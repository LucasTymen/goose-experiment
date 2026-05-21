# GOOSE Streamlit Utils
# =====================
# Package pour les utilitaires de l'application Streamlit

from .config import API_URL, QDRANT_URL, OLLAMA_URL
from .api_client import APIClient

__all__ = ["API_URL", "QDRANT_URL", "OLLAMA_URL", "APIClient"]
