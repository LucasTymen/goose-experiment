"""
Configuration for Agent Runtime Layer
=====================================

Centralized configuration for all Agent Runtime components.
Loads from environment variables with sensible defaults.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration"""
    host: str = "localhost"
    port: int = 6334
    https: bool = False
    api_key: Optional[str] = None
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> "QdrantConfig":
        return cls(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            https=os.getenv("QDRANT_HTTPS", "false").lower() == "true",
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=int(os.getenv("QDRANT_TIMEOUT", "30")),
        )


@dataclass
class OllamaConfig:
    """Ollama LLM configuration"""
    host: str = "localhost"
    port: int = 11434
    embedding_model: str = "all-minilm:latest"
    chat_model: str = "llama3:latest"
    timeout: int = 120
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        return cls(
            host=os.getenv("OLLAMA_HOST", "localhost"),
            port=int(os.getenv("OLLAMA_PORT", "11434")),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-minilm:latest"),
            chat_model=os.getenv("CHAT_MODEL", "llama3:latest"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "120")),
        )


@dataclass
class PostgresConfig:
    """PostgreSQL configuration for audit logging"""
    host: str = "localhost"
    port: int = 5434
    database: str = "goose_ai"
    user: str = "goose"
    password: str = "goosepass"
    
    @classmethod
    def from_env(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5434")),
            database=os.getenv("POSTGRES_DB", "goose_ai"),
            user=os.getenv("POSTGRES_USER", "goose"),
            password=os.getenv("POSTGRES_PASSWORD", "goosepass"),
        )
    
    def get_connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class MemoryConfig:
    """Memory system configuration"""
    max_context_tokens: int = 2000
    retrieval_limit: int = 5
    confidence_threshold: float = 0.7
    
    # Collection specific settings
    collection_settings: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class N8NConfig:
    """N8N workflow engine configuration"""
    host: str = "localhost"
    port: int = 5684
    https: bool = False
    api_key: Optional[str] = None
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> "N8NConfig":
        return cls(
            host=os.getenv("N8N_HOST", "localhost"),
            port=int(os.getenv("N8N_PORT", "5684")),
            https=os.getenv("N8N_HTTPS", "false").lower() == "true",
            api_key=os.getenv("N8N_API_KEY"),
            timeout=int(os.getenv("N8N_TIMEOUT", "30")),
        )
    
    def get_base_url(self) -> str:
        protocol = "https" if self.https else "http"
        return f"{protocol}://{self.host}:{self.port}"


@dataclass
class AgentRuntimeConfig:
    """Main configuration for Agent Runtime"""
    # Component configs
    qdrant: QdrantConfig = field(default_factory=QdrantConfig.from_env)
    ollama: OllamaConfig = field(default_factory=OllamaConfig.from_env)
    postgres: PostgresConfig = field(default_factory=PostgresConfig.from_env)
    n8n: N8NConfig = field(default_factory=N8NConfig.from_env)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    
    # Runtime settings
    user_id: str = "default"
    session_id: Optional[str] = None
    enable_memory: bool = True
    enable_audit: bool = True
    enable_n8n: bool = True
    debug: bool = False
    
    @classmethod
    def from_env(cls, user_id: str = "default") -> "AgentRuntimeConfig":
        return cls(
            user_id=user_id,
            qdrant=QdrantConfig.from_env(),
            ollama=OllamaConfig.from_env(),
            postgres=PostgresConfig.from_env(),
            n8n=N8NConfig.from_env(),
            memory=MemoryConfig(),
            enable_memory=os.getenv("ENABLE_MEMORY", "true").lower() == "true",
            enable_audit=os.getenv("ENABLE_AUDIT", "true").lower() == "true",
            enable_n8n=os.getenv("ENABLE_N8N", "true").lower() == "true",
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )


def load_config(user_id: str = "default") -> AgentRuntimeConfig:
    """
    Load configuration from environment variables.
    
    Args:
        user_id: The current user ID for memory personalization
        
    Returns:
        AgentRuntimeConfig instance with all settings
    """
    return AgentRuntimeConfig.from_env(user_id=user_id)


# Default configuration instance
DEFAULT_CONFIG = load_config()

# Alias for backward compatibility and cleaner naming
RuntimeConfig = AgentRuntimeConfig
