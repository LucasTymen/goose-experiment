# GOOSE API Client
# ================
# Client HTTP pour interagir avec FastAPI Tool Gateway

import requests
import json
from typing import Optional, Dict, List, Any
from .config import API_URL, REQUEST_TIMEOUT


class APIClient:
    """Client pour interagir avec FastAPI Tool Gateway."""
    
    def __init__(self, base_url: str = API_URL, timeout: int = REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                 params: Optional[Dict] = None) -> Dict:
        """Exécute une requête HTTP générique."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=self.timeout
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Méthode {method} non supportée")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status": "error",
                "endpoint": endpoint
            }
    
    # === HEALTH === 
    def health(self) -> Dict:
        """Vérifie que FastAPI est opérationnel."""
        return self._request("GET", "/health")
    
    # === ATS SCORING === 
    def ats_score(self, job_description: str, skills: List[str]) -> Dict:
        """Calcule le score ATS pour une offre et des compétences."""
        return self._request("POST", "/ats-score", data={
            "job_description": job_description,
            "skills": skills
        })
    
    # === CV GENERATION === 
    def generate_cv(self, candidate: str, role: str, company: str) -> Dict:
        """Génère un CV (placeholder pour l'instant)."""
        return self._request("POST", "/generate-cv", data={
            "candidate": candidate,
            "role": role,
            "company": company
        })
    
    # === MEMORY STORE === 
    def store_memory(self, content: str) -> Dict:
        """Stocke un contenu en mémoire Qdrant."""
        return self._request("POST", "/memory/store", data={
            "content": content
        })
    
    # === MEMORY SEARCH === 
    def search_memory(self, query: str, collection: str = "candidate_memory", 
                      limit: int = 5) -> Dict:
        """Recherche sémantique dans Qdrant."""
        return self._request("POST", "/memory/search", data={
            "query": query,
            "collection": collection,
            "limit": limit
        })
    
    # === MEMORY COLLECTIONS === 
    def list_collections(self) -> Dict:
        """Liste toutes les collections Qdrant."""
        return self._request("GET", "/memory/collections")
    
    def init_collections(self) -> Dict:
        """Initialise toutes les collections Qdrant."""
        return self._request("POST", "/memory/collections/init")
    
    # === ROOT === 
    def root(self) -> Dict:
        """Récupère les infos de base."""
        return self._request("GET", "/")
    
    # === JOBS ===
    def list_jobs(self) -> Dict:
        """Liste tous les jobs."""
        return self._request("GET", "/jobs")
    
    def create_job(self, title: str, company: str, description: str, 
                  location: Optional[str] = None, url: Optional[str] = None,
                  source: str = "manual", skills: Optional[List[str]] = None) -> Dict:
        """Crée un nouveau job avec calcul ATS automatique."""
        data = {
            "title": title,
            "company": company,
            "description": description,
            "location": location,
            "url": url,
            "source": source,
            "skills": skills or []
        }
        return self._request("POST", "/jobs", data=data)
    
    def score_job(self, job_id: str, skills: List[str]) -> Dict:
        """Recalcule le score ATS pour un job existant."""
        return self._request("POST", f"/jobs/{job_id}/score", data={"skills": skills})


# Instance globale
api_client = APIClient()
