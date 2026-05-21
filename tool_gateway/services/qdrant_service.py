from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(
    host="localhost",
    port=6334
)

# Memory Taxonomy: Collections dédiées pour chaque type de mémoire
COLLECTIONS = {
    "candidate_memory": {
        "vector_size": 768,
        "distance": Distance.COSINE,
        "description": "Mémoire des profils candidats et CVs"
    },
    "jobs_memory": {
        "vector_size": 768,
        "distance": Distance.COSINE,
        "description": "Mémoire des offres d'emploi et descriptions de poste"
    },
    "ats_keywords_memory": {
        "vector_size": 768,
        "distance": Distance.COSINE,
        "description": "Mémoire des keywords ATS et compétences"
    },
    "prompts_memory": {
        "vector_size": 768,
        "distance": Distance.COSINE,
        "description": "Mémoire des prompts validés et optimisés"
    },
    "workflow_memory": {
        "vector_size": 768,
        "distance": Distance.COSINE,
        "description": "Mémoire des workflows et historiques d'exécution"
    }
}

# Backward compatibility
COLLECTION_NAME = "candidate_memory"


def get_all_collections():
    """Récupère la liste de toutes les collections existantes."""
    try:
        response = client.get_collections()
        return [c.name for c in response.collections]
    except Exception as e:
        print(f"Erreur lors de la récupération des collections: {e}")
        return []


def collection_exists(collection_name: str) -> bool:
    """Vérifie si une collection existe."""
    existing = get_all_collections()
    return collection_name in existing


def create_collection_if_not_exists(collection_name: str, vector_size: int = 768, distance: Distance = Distance.COSINE):
    """Crée une collection si elle n'existe pas."""
    if not collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance
            )
        )
        print(f"Collection '{collection_name}' créée avec succès.")
        return True
    else:
        print(f"Collection '{collection_name}' existe déjà.")
        return False


def init_collection():
    """Initialise la collection candidate_memory (backward compatibility)."""
    create_collection_if_not_exists(
        collection_name=COLLECTION_NAME,
        vector_size=COLLECTIONS[COLLECTION_NAME]["vector_size"],
        distance=COLLECTIONS[COLLECTION_NAME]["distance"]
    )


def init_all_collections():
    """Initialise TOUTES les collections définies dans COLLECTIONS."""
    created = []
    existed = []
    
    for name, config in COLLECTIONS.items():
        if create_collection_if_not_exists(
            collection_name=name,
            vector_size=config["vector_size"],
            distance=config["distance"]
        ):
            created.append(name)
        else:
            existed.append(name)
    
    return {
        "created": created,
        "existed": existed,
        "all_collections": get_all_collections()
    }


def delete_collection(collection_name: str):
    """Supprime une collection (ATTENTION: destruction de données)."""
    if collection_exists(collection_name):
        client.delete_collection(collection_name=collection_name)
        print(f"Collection '{collection_name}' supprimée.")
        return True
    else:
        print(f"Collection '{collection_name}' n'existe pas.")
        return False


def search_memory(collection_name: str, query_vector: list, limit: int = 5):
    """
    Recherche sémantique dans une collection Qdrant.
    
    Args:
        collection_name: Nom de la collection
        query_vector: Vecteur de recherche (liste de floats)
        limit: Nombre de résultats à retourner
        
    Returns:
        Liste de points avec scores et payloads
    """
    if not collection_exists(collection_name):
        raise ValueError(f"Collection '{collection_name}' n'existe pas.")
    
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    
    return [
        {
            "id": str(point.id),
            "score": float(point.score),
            "payload": point.payload
        }
        for point in results.points
    ]
