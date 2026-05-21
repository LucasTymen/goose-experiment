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
    COLLECTION_NAME
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

