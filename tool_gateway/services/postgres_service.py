import psycopg2
import json
from typing import Optional, List, Dict, Any

conn = psycopg2.connect(
    host="localhost",
    port=5434,
    database="goose_ai",
    user="goose",
    password="goosepass"
)


def insert_audit(action, payload):

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO audit_logs (action, payload)
        VALUES (%s, %s)
        """,
        (action, json.dumps(payload))
    )

    conn.commit()
    cur.close()


# ============================================================================
# JOB FUNCTIONS
# ============================================================================

def get_all_jobs() -> List[Dict[str, Any]]:
    """Récupère tous les jobs de la base."""
    cur = conn.cursor()
    
    cur.execute(
        """
        SELECT id, title, company, description, location, url, source, 
               status, ats_score, skills, created_at, updated_at
        FROM jobs
        ORDER BY created_at DESC
        """
    )
    
    columns = [desc[0] for desc in cur.description]
    jobs = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    return jobs


def create_job(title: str, company: str, description: str, 
                location: Optional[str] = None, url: Optional[str] = None,
                source: str = "manual", skills: Optional[List[str]] = None,
                ats_score: Optional[int] = None) -> str:
    """Crée un nouveau job et retourne son ID."""
    cur = conn.cursor()
    
    cur.execute(
        """
        INSERT INTO jobs (title, company, description, location, url, source, 
                         status, ats_score, skills)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (title, company, description, location, url, source, 
         "pending", ats_score, skills)
    )
    
    job_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    return str(job_id)


def update_job_ats_score(job_id: int, score: int, skills: List[str]) -> bool:
    """Met à jour le score ATS d'un job."""
    cur = conn.cursor()
    
    cur.execute(
        """
        UPDATE jobs
        SET ats_score = %s, skills = %s, status = 'scored', updated_at = NOW()
        WHERE id = %s
        RETURNING id
        """,
        (score, skills, job_id)
    )
    
    updated = cur.fetchone() is not None
    conn.commit()
    cur.close()
    
    return updated


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    """Récupère un job par son ID."""
    cur = conn.cursor()
    
    cur.execute(
        """
        SELECT id, title, company, description, location, url, source, 
               status, ats_score, skills, created_at, updated_at
        FROM jobs
        WHERE id = %s
        """,
        (job_id,)
    )
    
    columns = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    
    cur.close()
    
    if row:
        return dict(zip(columns, row))
    return None


def delete_job(job_id: int) -> bool:
    """Supprime un job."""
    cur = conn.cursor()
    
    cur.execute(
        """
        DELETE FROM jobs WHERE id = %s
        RETURNING id
        """,
        (job_id,)
    )
    
    deleted = cur.fetchone() is not None
    conn.commit()
    cur.close()
    
    return deleted

