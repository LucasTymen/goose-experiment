import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"

MODEL = "nomic-embed-text"


def create_embedding(text: str):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": text
        }
    )

    data = response.json()

    return data["embedding"]
