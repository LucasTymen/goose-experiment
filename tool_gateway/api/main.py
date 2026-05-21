from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
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


class JobRequest(BaseModel):
    title: str
    company: str
    description: str
    location: Optional[str] = None
    url: Optional[str] = None
    source: str = "manual"
    skills: Optional[List[str]] = None


class JobScoreRequest(BaseModel):
    skills: List[str]


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


def calculate_ats_score(job_description: str, skills: List[str]) -> int:
    """Calcule le score ATS (logique partagée)."""
    score = 0
    for skill in skills:
        if skill.lower() in job_description.lower():
            score += 10
    return score


@app.post("/ats-score")
def ats_score(req: ATSRequest):

    score = calculate_ats_score(req.job_description, req.skills)

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


# ============================================================================
# JOB ENDPOINTS
# ============================================================================

@app.get("/jobs")
def list_jobs():
    """Liste tous les jobs stockés en base de données."""
    from tool_gateway.services.postgres_service import get_all_jobs
    
    jobs = get_all_jobs()
    
    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "list_jobs",
        "count": len(jobs)
    }
    
    insert_audit("list_jobs", event)
    
    return {
        "status": "completed",
        "jobs": jobs,
        "count": len(jobs)
    }


@app.post("/jobs")
def create_job(req: JobRequest):
    """Crée un nouveau job et calcule son score ATS."""
    from tool_gateway.services.postgres_service import create_job as db_create_job
    
    # Debug: vérifier req.skills
    import sys
    print(f"[DEBUG] req.skills = {req.skills}, type = {type(req.skills)}", file=sys.stderr)
    
    # Calculer le score ATS si des skills sont fournies
    job_ats_score = None
    if req.skills:
        # Utiliser la fonction utilitaire de calcul de score
        job_ats_score = calculate_ats_score(req.description, req.skills)
    
    # Créer le job en base
    job_id = db_create_job(
        title=req.title,
        company=req.company,
        description=req.description,
        location=req.location,
        url=req.url,
        source=req.source,
        skills=req.skills,
        ats_score=job_ats_score
    )
    
    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "create_job",
        "job_id": job_id,
        "ats_score": job_ats_score
    }
    
    insert_audit("create_job", event)
    
    return {
        "status": "created",
        "job_id": job_id,
        "ats_score": job_ats_score
    }


@app.post("/jobs/{job_id}/score")
def score_job(job_id: str, req: JobScoreRequest):
    """Calcule/recalcule le score ATS pour un job existant."""
    from tool_gateway.services.postgres_service import update_job_ats_score, get_job_by_id
    
    # Récupérer le job pour avoir la description
    job = get_job_by_id(job_id)
    if not job:
        return {"status": "error", "message": "Job not found"}
    
    # Calculer le score
    score = calculate_ats_score(job.get("description", ""), req.skills)
    
    # Mettre à jour en base
    updated = update_job_ats_score(job_id, score, req.skills)
    
    event = {
        "timestamp": str(datetime.utcnow()),
        "action": "score_job",
        "job_id": job_id,
        "score": score
    }
    
    insert_audit("score_job", event)
    
    return {
        "status": "scored",
        "job_id": job_id,
        "score": score
    }

