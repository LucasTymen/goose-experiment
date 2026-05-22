"""
Agent Runtime Layer for GOOSE
================================

This module provides the cognitive orchestration layer that connects:
- User inputs (via Streamlit/FastAPI/CLI)
- Memory infrastructure (Qdrant, PostgreSQL)
- Tool execution (FastAPI endpoints, N8N workflows)
- LLM reasoning (Goose/Ollama)

The Agent Runtime implements the "memory loop" that was missing:
1. Intent Classification
2. Memory Retrieval Policy
3. Context Assembly
4. Prompt Augmentation
5. Tool Selection & Execution
6. Memory Writeback
7. Audit Logging

Usage:
    from agent_runtime import AgentRuntime, RuntimeConfig
    
    runtime = AgentRuntime(config=RuntimeConfig(user_id="user_123"))
    result = await runtime.run("Parlons français")
"""

from .config import AgentRuntimeConfig, RuntimeConfig, load_config, QdrantConfig, OllamaConfig, PostgresConfig, N8NConfig, MemoryConfig
from .runtime import AgentRuntime, RuntimeResult, RuntimeStatus, ToolExecution, get_agent_runtime
from .memory_taxonomy import MEMORY_COLLECTIONS, MemoryCollection, MemoryType, create_memory_payload
from .memory_policy import MemoryPolicyEngine, RetrievalPolicy, PolicyType
from .retrieval_engine import RetrievalEngine, RetrievalResult, RetrievalOperation
from .context_assembler import ContextAssembler, MemoryContext, AssembledContext
from .prompt_augmenter import PromptAugmenter, PromptTemplate
from .n8n_integrator import N8NIntegrator, N8NWorkflow, N8NExecution

__all__ = [
    # Main runtime
    "AgentRuntime",
    "RuntimeConfig",
    "RuntimeResult",
    "RuntimeStatus",
    "get_agent_runtime",
    
    # Configuration
    "load_config",
    "QdrantConfig",
    "OllamaConfig", 
    "PostgresConfig",
    "N8NConfig",
    "MemoryConfig",
    
    # Memory Taxonomy
    "MEMORY_COLLECTIONS",
    "MemoryCollection",
    "MemoryType",
    "create_memory_payload",
    
    # Memory Policy
    "MemoryPolicyEngine",
    "RetrievalPolicy",
    "PolicyType",
    
    # Retrieval Engine
    "RetrievalEngine",
    "RetrievalResult",
    "RetrievalOperation",
    
    # Context Assembly
    "ContextAssembler",
    "MemoryContext",
    "AssembledContext",
    
    # Prompt Augmentation
    "PromptAugmenter",
    "PromptTemplate",
    
    # N8N Integration
    "N8NIntegrator",
    "N8NWorkflow",
    "N8NExecution",
]

__version__ = "1.0.0"
