"""
Memory Taxonomy for GOOSE Agent Runtime
=======================================

Defines all Qdrant collections and their metadata schemas for structured memory storage.
Each collection represents a different type of knowledge the agent can retrieve and use.
"""

from typing import Dict, Any, TypedDict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(Enum):
    """Types of memory entries"""
    PROFILE = "profile"           # User/candidate profile data
    PREFERENCE = "preference"     # User preferences (language, style, etc.)
    JOB = "job"                  # Job offers and applications
    ATS = "ats"                  # ATS patterns and keywords
    WORKFLOW = "workflow"        # Workflow execution history
    RECRUITER = "recruiter"      # Recruiter interactions
    INFRA = "infra"             # Infrastructure documentation
    CONVERSATION = "conversation"  # Conversation history
    DECISION = "decision"        # Agent decisions and reasoning


@dataclass
class MemoryCollection:
    """Definition of a Qdrant memory collection"""
    name: str
    description: str
    vector_size: int = 384  # Default for all-minilm (384), bge-small (384), nomic-embed-text (768)
    
    # Metadata schema definition
    metadata_schema: Dict[str, type] = field(default_factory=dict)
    required_metadata: list = field(default_factory=list)
    
    # Indexing configuration
    index_params: Dict[str, Any] = field(default_factory=dict)
    
    # Retrieval defaults
    default_limit: int = 5
    default_confidence_threshold: float = 0.7
    
    def __post_init__(self):
        # Set default index params if not provided
        if not self.index_params:
            self.index_params = {
                "M": 16,
                "ef_construct": 128,
                "ef_search": 128,
            }


# ============================================================================
# MEMORY COLLECTIONS DEFINITION
# ============================================================================

MEMORY_COLLECTIONS: Dict[str, MemoryCollection] = {
    
    # 1. Candidate Profile Memory
    "candidate_memory": MemoryCollection(
        name="candidate_memory",
        description="Profil, compétences, expériences et parcours du candidat",
        vector_size=384,
        metadata_schema={
            "user_id": str,
            "memory_type": str,  # MemoryType enum value
            "content": str,
            "timestamp": datetime,
            "confidence": float,
            "workflow_id": Optional[str],
            "source": str,  # "manual", "generated", "extracted"
            # Profile-specific
            "name": Optional[str],
            "title": Optional[str],
            "experience_years": Optional[int],
            "skills": Optional[list],
            "education": Optional[str],
            "location": Optional[str],
            "industry": Optional[str],
        },
        required_metadata=["user_id", "memory_type", "content", "timestamp"],
        default_limit=5,
        default_confidence_threshold=0.75,
    ),
    
    # 2. User Preferences Memory
    "preferences_memory": MemoryCollection(
        name="preferences_memory",
        description="Préférences utilisateur (langue, style, format, etc.)",
        vector_size=384,
        metadata_schema={
            "user_id": str,
            "preference_type": str,  # "language", "style", "format", "tone", etc.
            "value": str,
            "priority": int,  # 1-10
            "last_used": Optional[datetime],
            "created_at": datetime,
            "source": str,
        },
        required_metadata=["user_id", "preference_type", "value", "created_at"],
        default_limit=3,
        default_confidence_threshold=0.8,
    ),
    
    # 3. Jobs Memory
    "jobs_memory": MemoryCollection(
        name="jobs_memory",
        description="Offres d'emploi, candidatures et suivi",
        vector_size=384,
        metadata_schema={
            "user_id": str,
            "job_id": str,
            "title": str,
            "company": Optional[str],
            "location": Optional[str],
            "description": Optional[str],
            "status": str,  # "saved", "applied", "interview", "rejected", "offer"
            "application_date": Optional[datetime],
            "ats_score": Optional[float],
            "source": str,  # "linkedin", "indeed", "manual", etc.
            "url": Optional[str],
            "salary_range": Optional[str],
            "requirements": Optional[list],
            "timestamp": datetime,
        },
        required_metadata=["user_id", "job_id", "title", "status", "timestamp"],
        default_limit=10,
        default_confidence_threshold=0.7,
    ),
    
    # 4. ATS Patterns Memory
    "ats_memory": MemoryCollection(
        name="ats_memory",
        description="Patterns ATS, mots-clés, optimisations et bonnes pratiques",
        vector_size=384,
        metadata_schema={
            "category": str,  # "keywords", "format", "structure", "best_practice"
            "content": str,
            "relevance_score": float,
            "language": str,  # "fr", "en", etc.
            "industry": Optional[str],
            "last_used": Optional[datetime],
            "usage_count": int,
            "source": str,
            "timestamp": datetime,
        },
        required_metadata=["category", "content", "timestamp"],
        default_limit=8,
        default_confidence_threshold=0.75,
    ),
    
    # 5. Workflow Memory
    "workflow_memory": MemoryCollection(
        name="workflow_memory",
        description="Historique des workflows exécutés via N8N",
        vector_size=384,
        metadata_schema={
            "workflow_id": str,
            "user_id": str,
            "workflow_name": str,
            "status": str,  # "success", "failed", "running", "pending_approval"
            "parameters": dict,
            "result": Optional[dict],
            "execution_time": Optional[float],
            "started_at": datetime,
            "completed_at": Optional[datetime],
            "error_message": Optional[str],
            "n8n_execution_id": Optional[str],
        },
        required_metadata=["workflow_id", "user_id", "workflow_name", "status", "started_at"],
        default_limit=5,
        default_confidence_threshold=0.7,
    ),
    
    # 6. Recruiter Memory
    "recruiter_memory": MemoryCollection(
        name="recruiter_memory",
        description="Interactions avec les recruteurs et entreprises",
        vector_size=384,
        metadata_schema={
            "user_id": str,
            "recruiter_id": str,
            "recruiter_name": Optional[str],
            "company": str,
            "position": Optional[str],
            "conversation_history": list,
            "last_contact": Optional[datetime],
            "response_rate": Optional[float],
            "interview_count": int,
            "status": str,  # "active", "inactive", "hired", "rejected"
            "notes": Optional[str],
            "timestamp": datetime,
        },
        required_metadata=["user_id", "recruiter_id", "company", "timestamp"],
        default_limit=5,
        default_confidence_threshold=0.75,
    ),
    
    # 7. Infrastructure Memory
    "infra_memory": MemoryCollection(
        name="infra_memory",
        description="Documentation infrastructure, configurations et guides",
        vector_size=384,
        metadata_schema={
            "component": str,  # "api", "database", "docker", "network"
            "type": str,  # "doc", "config", "guide", "troubleshooting"
            "content": str,
            "severity": Optional[str],  # "info", "warning", "error"
            "last_accessed": Optional[datetime],
            "access_count": int,
            "tags": Optional[list],
            "timestamp": datetime,
        },
        required_metadata=["component", "type", "content", "timestamp"],
        default_limit=5,
        default_confidence_threshold=0.7,
    ),
    
    # 8. Conversation Memory (Short-term)
    "conversation_memory": MemoryCollection(
        name="conversation_memory",
        description="Historique des conversations récentes (court terme)",
        vector_size=384,
        metadata_schema={
            "session_id": str,
            "user_id": str,
            "turn": int,  # Turn number in conversation
            "role": str,  # "user" or "assistant"
            "content": str,
            "intent": Optional[str],
            "timestamp": datetime,
            "confidence": Optional[float],
        },
        required_metadata=["session_id", "user_id", "turn", "role", "content", "timestamp"],
        default_limit=10,
        default_confidence_threshold=0.6,
    ),
    
    # 9. Decision Memory (Agent Reasoning)
    "decision_memory": MemoryCollection(
        name="decision_memory",
        description="Historique des décisions de l'agent et raisonnements",
        vector_size=384,
        metadata_schema={
            "user_id": str,
            "session_id": str,
            "decision_type": str,
            "context": dict,
            "choice": str,
            "reasoning": str,
            "outcome": Optional[str],
            "confidence": float,
            "timestamp": datetime,
        },
        required_metadata=["user_id", "decision_type", "context", "choice", "reasoning", "timestamp"],
        default_limit=5,
        default_confidence_threshold=0.7,
    ),
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_collection(collection_name: str) -> Optional[MemoryCollection]:
    """Get a collection by name"""
    return MEMORY_COLLECTIONS.get(collection_name)


def list_collections() -> list:
    """List all available collection names"""
    return list(MEMORY_COLLECTIONS.keys())


def validate_memory_payload(collection_name: str, payload: Dict[str, Any]) -> bool:
    """Validate that a memory payload has required metadata"""
    collection = get_collection(collection_name)
    if not collection:
        return False
    
    for field in collection.required_metadata:
        if field not in payload:
            return False
    
    return True


def create_memory_payload(
    collection_name: str,
    content: str,
    user_id: str,
    **metadata
) -> Dict[str, Any]:
    """
    Create a properly structured memory payload for a collection.
    
    Args:
        collection_name: Name of the collection
        content: The main content to store
        user_id: The user ID
        **metadata: Additional metadata fields
        
    Returns:
        Dict with all required and optional metadata
    """
    collection = get_collection(collection_name)
    if not collection:
        raise ValueError(f"Unknown collection: {collection_name}")
    
    payload = {
        "content": content,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Add collection-specific defaults
    if collection_name == "preferences_memory":
        payload.update({
            "preference_type": metadata.get("preference_type", "general"),
            "value": metadata.get("value", content),
            "priority": metadata.get("priority", 5),
            "created_at": datetime.utcnow().isoformat(),
            "source": metadata.get("source", "agent"),
        })
    elif collection_name == "candidate_memory":
        payload.update({
            "memory_type": metadata.get("memory_type", "profile"),
            "confidence": metadata.get("confidence", 0.8),
            "source": metadata.get("source", "user"),
        })
    elif collection_name == "jobs_memory":
        payload.update({
            "job_id": metadata.get("job_id", f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "status": metadata.get("status", "saved"),
            "source": metadata.get("source", "user"),
        })
    elif collection_name == "workflow_memory":
        payload.update({
            "workflow_id": metadata.get("workflow_id", f"wf_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "workflow_name": metadata.get("workflow_name", "unknown"),
            "status": metadata.get("status", "running"),
            "started_at": datetime.utcnow().isoformat(),
            "parameters": metadata.get("parameters", {}),
        })
    
    # Add any additional metadata
    payload.update(metadata)
    
    return payload
