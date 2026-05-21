from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime
import json
from tool_gateway.services.postgres_service import insert_audit
from tool_gateway.services.embedding_service import create_embedding
from tool_gateway.services.qdrant_service import (
    client,
    init_collection,
    init_all_collections,
    get_all_collections,
    search_memory,
    COLLECTION_NAME,
    COLLECTIONS
)

from qdrant_client.models import PointStruct
import uuid

app = FastAPI(title="GOOSE TOOL GATEWAY")

AUDIT_LOG = "/home/lucas/GOOSE/tool_gateway/logs/audit.log"


def write_audit(event: dict):
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")


class CVRequest(BaseModel):
    candidate: str
    role: str
    company: str


class ATSRequest(BaseModel):
    job_description: str
    skills: List[str]


class MemoryRequest(BaseModel):
    content: str


class SearchRequest(BaseModel):
    query: str
    collection: str = "candidate_memory"
    limit: int = 5


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "GOOSE_TOOL_GATEWAY",
        "timestamp": str(datetime.utcnow())
    }


@app.post("/generate-cv")
def generate_cv(req: CVRequest):

    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "generate_cv",
        "candidate": req.candidate,
        "role": req.role,
        "company": req.company
    }

    insert_audit("generate_cv", event)

    return {
        "status": "accepted",
        "message": "CV generation task created",
        "payload": event
    }


@app.post("/ats-score")
def ats_score(req: ATSRequest):

    score = 0

    for skill in req.skills:
        if skill.lower() in req.job_description.lower():
            score += 10

    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "ats_score",
        "score": score
    }

    insert_audit("ats_score", event)

    return {
        "status": "completed",
        "score": score
    }



@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/memory/store")
def memory_store(req: MemoryRequest):

    init_collection()

    embedding = create_embedding(req.content)

    point_id = str(uuid.uuid4())

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "content": req.content
                }
            )
        ]
    )

    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "memory_store",
        "point_id": point_id
    }

    insert_audit("memory_store", event)

    return {
        "status": "stored",
        "point_id": point_id
    }


@app.get("/memory/collections")
def list_collections():
    """Liste toutes les collections Qdrant existantes."""
    collections = get_all_collections()
    
    result = {
        "collections": collections,
        "count": len(collections)
    }
    
    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "list_collections"
    }
    
    insert_audit("list_collections", event)
    
    return result


@app.post("/memory/collections/init")
def init_collections():
    """Initialise toutes les collections Qdrant définies dans la taxonomy."""
    result = init_all_collections()
    
    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "init_collections",
        "created": result["created"],
        "existed": result["existed"]
    }
    
    insert_audit("init_collections", event)
    
    return {
        "status": "initialized",
        **result
    }


@app.post("/memory/search")
def memory_search(req: SearchRequest):
    """
    Recherche sémantique dans une collection Qdrant.
    
    Args:
        query: Texte à rechercher
        collection: Nom de la collection (défaut: candidate_memory)
        limit: Nombre de résultats (défaut: 5)
    
    Returns:
        Liste de résultats avec scores et payloads
    """
    # Créer l'embedding de la requête
    embedding = create_embedding(req.query)
    
    # Rechercher dans Qdrant
    results = search_memory(
        collection_name=req.collection,
        query_vector=embedding,
        limit=req.limit
    )
    
    # Audit
    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "memory_search",
        "query": req.query[:50],  # Truncated for audit
        "collection": req.collection,
        "results_count": len(results)
    }
    
    insert_audit("memory_search", event)
    
    return {
        "status": "completed",
        "query": req.query,
        "collection": req.collection,
        "results": results
    }

