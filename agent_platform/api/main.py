from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="GOOSE Agent Platform")

class CVRequest(BaseModel):
    candidate: str
    target_role: str
    company: str

@app.get("/")
def root():
    return {"status": "GOOSE_AGENT_PLATFORM_RUNNING"}

@app.post("/generate-cv")
def generate_cv(req: CVRequest):
    return {
        "status": "accepted",
        "candidate": req.candidate,
        "target_role": req.target_role,
        "company": req.company
    }
