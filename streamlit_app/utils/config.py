# GOOSE Streamlit Configuration
# =================================

# FastAPI Tool Gateway
API_URL = "http://localhost:8044"

# Qdrant
QDRANT_URL = "http://localhost:6334"

# Ollama
OLLAMA_URL = "http://localhost:11434"

# PostgreSQL (pour référence)
PG_HOST = "localhost"
PG_PORT = 5434
PG_DB = "goose_ai"
PG_USER = "goose"

# Streamlit
STREAMLIT_PORT = 8501
STREAMLIT_THEME = "dark"

# Collections Qdrant
QDRANT_COLLECTIONS = [
    "candidate_memory",
    "jobs_memory", 
    "ats_keywords_memory",
    "prompts_memory",
    "workflow_memory"
]

# Timeout pour les requêtes (secondes)
REQUEST_TIMEOUT = 30
