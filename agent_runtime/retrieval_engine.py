"""
Retrieval Engine for GOOSE Agent Runtime
======================================

Handles all vector search operations against Qdrant.
Provides a unified interface for memory retrieval.
"""

import asyncio
import aiohttp
import json
import uuid
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .config import QdrantConfig, OllamaConfig
from .memory_taxonomy import MEMORY_COLLECTIONS, get_collection, create_memory_payload

logger = logging.getLogger(__name__)

# Import qdrant models for type definitions
try:
    from qdrant_client import models
except ImportError:
    models = None  # Will be imported lazily in methods


@dataclass
class RetrievalResult:
    """A single retrieval result from Qdrant"""
    id: Union[str, int]
    score: float
    payload: Dict[str, Any]
    collection: str
    vector: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "score": self.score,
            "payload": self.payload,
            "collection": self.collection,
        }


@dataclass
class RetrievalOperation:
    """Definition of a single retrieval operation"""
    collection: str
    query: str
    query_vector: Optional[List[float]] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 5
    confidence_threshold: float = 0.7
    
    def to_search_params(self) -> Dict[str, Any]:
        """Convert to Qdrant search parameters"""
        # Build filter from metadata
        filter_dict = None
        if self.metadata_filters:
            filter_dict = self._build_qdrant_filter(self.metadata_filters)
        
        return {
            "collection_name": self.collection,
            "query_vector": self.query_vector,
            "query": self.query,
            "filter": filter_dict,
            "limit": self.limit,
            "with_payload": True,
            "with_vectors": False,
            "score_threshold": self.confidence_threshold,
        }
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Qdrant filter from metadata filters"""
        qdrant_filters = []
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # Handle special operators like $contains
                if "$contains" in value:
                    qdrant_filters.append({
                        "key": key,
                        "match": {"text": value["$contains"]}
                    })
                else:
                    qdrant_filters.append({
                        "key": key,
                        "match": {"value": value}
                    })
            else:
                qdrant_filters.append({
                    "key": key,
                    "match": {"value": value}
                })
        
        if len(qdrant_filters) == 1:
            return qdrant_filters[0]
        elif len(qdrant_filters) > 1:
            return {"must": qdrant_filters}
        else:
            return {}


class RetrievalEngine:
    """
    Main engine for retrieving memories from Qdrant.
    
    Features:
    - Vector search with metadata filtering
    - Multiple collection support
    - Embedding generation via Ollama
    - Async operations for performance
    - Result post-processing
    """
    
    def __init__(
        self,
        qdrant_config: Optional[QdrantConfig] = None,
        ollama_config: Optional[OllamaConfig] = None
    ):
        self.qdrant_config = qdrant_config or QdrantConfig.from_env()
        self.ollama_config = ollama_config or OllamaConfig.from_env()
        self.session = None
        self._initialize_qdrant_client()
    
    def _initialize_qdrant_client(self):
        """Initialize Qdrant client"""
        try:
            from qdrant_client import QdrantClient, models
            
            # Use async client
            self.client = QdrantClient(
                host=self.qdrant_config.host,
                port=self.qdrant_config.port,
                https=self.qdrant_config.https,
                api_key=self.qdrant_config.api_key,
                timeout=self.qdrant_config.timeout,
            )
            
            # Test connection
            self.client.get_collections()
            logger.info(f"Connected to Qdrant at {self.qdrant_config.host}:{self.qdrant_config.port}")
            
        except ImportError as e:
            logger.error(f"Qdrant client not installed: {e}")
            raise RuntimeError("Please install qdrant-client: pip install qdrant-client")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def ensure_collections_exist(self) -> None:
        """Create all required collections if they don't exist"""
        from qdrant_client import models
        
        existing_collections = [c.name for c in self.client.get_collections().collections]
        
        for collection_name, collection_config in MEMORY_COLLECTIONS.items():
            if collection_name not in existing_collections:
                self._create_collection(collection_name, collection_config)
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.debug(f"Collection exists: {collection_name}")
    
    def _create_collection(self, name: str, config: Any) -> None:
        """Create a new Qdrant collection"""
        from qdrant_client import models
        
        self.client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=config.vector_size,
                distance=models.Distance.COSINE
            ),
            # Enable dynamic schema for flexible metadata
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=0  # Index all vectors immediately
            )
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Truncate very long text to avoid context length errors
        # all-minilm has a context length of ~128 tokens (varies by implementation)
        # Be conservative and limit to 512 characters
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        url = f"http://{self.ollama_config.host}:{self.ollama_config.port}/api/embeddings"
        
        payload = {
            "model": self.ollama_config.embedding_model,
            "prompt": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error(f"Ollama embedding error: {error}")
                    # Fallback: return zero vector (will match nothing)
                    collection = get_collection("preferences_memory")
                    return [0.0] * (collection.vector_size if collection else 384)
                
                data = await response.json()
                return data["embedding"]
    
    def generate_embedding_sync(self, text: str) -> List[float]:
        """Synchronous version of generate_embedding"""
        import requests
        
        # Truncate very long text to avoid context length errors
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        url = f"http://{self.ollama_config.host}:{self.ollama_config.port}/api/embeddings"
        
        payload = {
            "model": self.ollama_config.embedding_model,
            "prompt": text
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code != 200:
                logger.error(f"Ollama embedding error: {response.text}")
                collection = get_collection("preferences_memory")
                return [0.0] * (collection.vector_size if collection else 384)
            
            data = response.json()
            return data["embedding"]
        except Exception as e:
            logger.error(f"Ollama embedding sync error: {e}")
            collection = get_collection("preferences_memory")
            return [0.0] * (collection.vector_size if collection else 384)
    
    async def retrieve(
        self,
        query: str,
        collection_name: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        confidence_threshold: float = 0.7,
        user_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve memories from a specific collection.
        
        Args:
            query: The search query text
            collection_name: Name of the Qdrant collection
            metadata_filters: Optional metadata filters
            limit: Maximum number of results
            confidence_threshold: Minimum score threshold
            user_id: Optional user ID for filtering
            
        Returns:
            List of RetrievalResult objects
        """
        # Validate collection
        if collection_name not in MEMORY_COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        # Add user_id filter if provided
        if user_id:
            metadata_filters = metadata_filters or {}
            metadata_filters["user_id"] = user_id
        
        # Generate embedding
        query_embedding = await self.generate_embedding(query)
        
        # Build search parameters
        search_params = {
            "collection_name": collection_name,
            "query_vector": query_embedding,
            "limit": limit,
            "with_payload": True,
            "with_vectors": False,
            "score_threshold": confidence_threshold,
        }
        
        # Add filter if provided
        if metadata_filters:
            search_params["query_filter"] = self._build_qdrant_filter(metadata_filters)
        
        # Execute search - use query_points for Qdrant 1.x+ API
        try:
            # Extract parameters for the new API
            collection = search_params.pop("collection_name")
            query_vector = search_params.pop("query_vector")
            
            # Remap remaining parameters
            query_params = {
                "limit": search_params.pop("limit", 10),
                "with_payload": search_params.pop("with_payload", True),
                "with_vectors": search_params.pop("with_vectors", False),
                "score_threshold": search_params.pop("score_threshold", None),
            }
            
            if "query_filter" in search_params:
                query_params["query_filter"] = search_params.pop("query_filter")
            
            results = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                **query_params
            )
            
            return [
                RetrievalResult(
                    id=hit.id,
                    score=hit.score,
                    payload=hit.payload,
                    collection=collection_name
                )
                for hit in results.points
            ]
        except Exception as e:
            logger.error(f"Search error in {collection_name}: {e}")
            return []
    
    def retrieve_sync(
        self,
        query: str,
        collection_name: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        confidence_threshold: float = 0.7,
        user_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Synchronous version of retrieve"""
        import requests
        
        # Validate collection
        if collection_name not in MEMORY_COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        # Add user_id filter if provided
        if user_id:
            metadata_filters = metadata_filters or {}
            metadata_filters["user_id"] = user_id
        
        # Generate embedding
        query_embedding = self.generate_embedding_sync(query)
        
        # Build search payload
        payload = {
            "collection_name": collection_name,
            "vector": query_embedding,
            "limit": limit,
            "with_payload": True,
            "with_vectors": False,
            "score_threshold": confidence_threshold,
        }
        
        # Add filter if provided
        if metadata_filters:
            payload["filter"] = self._build_qdrant_filter(metadata_filters)
        
        # Execute search
        url = f"http://{self.qdrant_config.host}:{self.qdrant_config.port}/collections/{collection_name}/points/search"
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code != 200:
                logger.error(f"Qdrant search error: {response.text}")
                return []
            
            data = response.json()
            return [
                RetrievalResult(
                    id=hit["id"],
                    score=hit["score"],
                    payload=hit["payload"],
                    collection=collection_name
                )
                for hit in data.get("result", [])
            ]
        except Exception as e:
            logger.error(f"Sync search error: {e}")
            return []
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Any:
        """Build Qdrant filter from metadata filters for Qdrant 1.x+ API"""
        from qdrant_client import models
        
        qdrant_filters = []
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # Handle special operators
                if "$contains" in value:
                    qdrant_filters.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchText(text=value["$contains"])
                        )
                    )
                elif "$in" in value:
                    qdrant_filters.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value["$in"])
                        )
                    )
                else:
                    qdrant_filters.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            else:
                qdrant_filters.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
        
        if len(qdrant_filters) == 1:
            return models.Filter(must=[qdrant_filters[0]])
        elif len(qdrant_filters) > 1:
            return models.Filter(must=qdrant_filters)
        else:
            return None
    
    async def batch_retrieve(
        self,
        operations: List[RetrievalOperation]
    ) -> Dict[str, List[RetrievalResult]]:
        """
        Execute multiple retrieval operations in parallel.
        
        Args:
            operations: List of RetrievalOperation objects
            
        Returns:
            Dict mapping collection names to lists of results
        """
        results = {}
        
        # Group by collection for efficiency
        by_collection = {}
        for op in operations:
            if op.collection not in by_collection:
                by_collection[op.collection] = []
            by_collection[op.collection].append(op)
        
        # Execute in parallel
        tasks = []
        for collection, ops in by_collection.items():
            for op in ops:
                task = asyncio.create_task(
                    self.retrieve(
                        query=op.query,
                        collection_name=op.collection,
                        metadata_filters=op.metadata_filters,
                        limit=op.limit,
                        confidence_threshold=op.confidence_threshold
                    )
                )
                tasks.append((collection, task))
        
        # Wait for all tasks
        for collection, task in tasks:
            collection_results = await task
            if collection not in results:
                results[collection] = []
            results[collection].extend(collection_results)
        
        return results
    
    def store_memory(
        self,
        collection_name: str,
        payload: Dict[str, Any],
        vector: Optional[List[float]] = None
    ) -> Optional[str]:
        """
        Store a memory entry in Qdrant.
        
        Args:
            collection_name: Name of the collection
            payload: Metadata payload
            vector: Optional pre-computed vector (will be generated if not provided)
            
        Returns:
            The ID of the stored point, or None if failed
        """
        # Validate collection
        if collection_name not in MEMORY_COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        collection = MEMORY_COLLECTIONS[collection_name]
        
        # Validate payload
        if not all(field in payload for field in collection.required_metadata):
            missing = [f for f in collection.required_metadata if f not in payload]
            raise ValueError(f"Missing required fields: {missing}")
        
        # Generate vector if not provided
        if vector is None:
            # Use 'content' field for embedding
            content = payload.get("content", "")
            if isinstance(content, list):
                content = " ".join(content)
            vector = self.generate_embedding_sync(content)
        
        # Generate point ID - Qdrant requires UUID or unsigned int
        point_id = payload.get("id") or str(uuid.uuid4())
        
        # Store in Qdrant
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            logger.debug(f"Stored memory {point_id} in {collection_name}")
            return point_id
        except Exception as e:
            logger.error(f"Failed to store memory in {collection_name}: {e}")
            return None
    
    def delete_memory(self, collection_name: str, point_id: Union[str, int]) -> bool:
        """Delete a memory entry from Qdrant"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[point_id]
                )
            )
            logger.debug(f"Deleted memory {point_id} from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {point_id} from {collection_name}: {e}")
            return False
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all points from a collection"""
        try:
            self.client.clear(
                collection_name=collection_name
            )
            logger.info(f"Cleared collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection {collection_name}: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a collection"""
        try:
            collection = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": collection.points_count,
                "config": collection.config
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None
    
    def list_collections(self) -> List[str]:
        """List all available collections"""
        try:
            collections = self.client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []


# Singleton instance for convenience
_retrieval_engine: Optional[RetrievalEngine] = None


def get_retrieval_engine() -> RetrievalEngine:
    """Get or create the global retrieval engine instance"""
    global _retrieval_engine
    if _retrieval_engine is None:
        _retrieval_engine = RetrievalEngine()
    return _retrieval_engine
