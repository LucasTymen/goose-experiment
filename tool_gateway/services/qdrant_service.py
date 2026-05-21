from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(
    host="localhost",
    port=6334
)

COLLECTION_NAME = "candidate_memory"


def init_collection():

    collections = client.get_collections().collections

    exists = any(
        c.name == COLLECTION_NAME
        for c in collections
    )

    if not exists:

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )
