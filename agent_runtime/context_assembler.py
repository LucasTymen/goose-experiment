"""
Context Assembler for GOOSE Agent Runtime
=======================================

Transforms raw retrieval results into formatted context for LLM prompts.
Handles token budget management, deduplication, and prioritization.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryContext:
    """A single memory entry with formatting metadata"""
    content: str
    source: str
    collection: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    confidence: float = 1.0
    
    def to_string(self, template: Optional[str] = None) -> str:
        """Format the memory context as a string"""
        if template:
            return template.format(
                content=self.content,
                source=self.source,
                collection=self.collection,
                score=f"{self.score:.2f}",
                timestamp=self.timestamp.isoformat() if self.timestamp else "N/A"
            )
        
        timestamp_str = self.timestamp.isoformat() if self.timestamp else ""
        return f"[Memory: {self.collection} | Source: {self.source} | Score: {self.score:.2f} | {timestamp_str}]\n{self.content}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "source": self.source,
            "collection": self.collection,
            "score": self.score,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "confidence": self.confidence
        }


@dataclass
class AssembledContext:
    """Complete assembled context for LLM prompt"""
    memories: List[MemoryContext] = field(default_factory=list)
    total_tokens: int = 0
    collections_used: List[str] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    
    def to_string(self, separator: str = "\n\n---\n\n") -> str:
        """Join all memory contexts into a single string"""
        return separator.join(m.to_string() for m in self.memories)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "memories": [m.to_dict() for m in self.memories],
            "total_tokens": self.total_tokens,
            "collections_used": self.collections_used,
            "oldest_timestamp": min(self.timestamps).isoformat() if self.timestamps else None,
            "newest_timestamp": max(self.timestamps).isoformat() if self.timestamps else None,
        }


class ContextAssembler:
    """
    Assembles retrieval results into formatted context for LLM prompts.
    
    Features:
    - Token budget management
    - Deduplication
    - Prioritization by score/confidence
    - Chronological ordering options
    - Source attribution
    - Custom formatting templates
    """
    
    def __init__(
        self,
        token_budget: int = 2000,
        max_memories: int = 20,
        deduplication: bool = True,
        prioritize_recent: bool = True
    ):
        self.token_budget = token_budget
        self.max_memories = max_memories
        self.deduplication = deduplication
        self.prioritize_recent = prioritize_recent
        
        # Custom formatting templates
        self.formatting_templates = {
            "default": "[Memory: {collection} | Source: {source} | Score: {score}]\n{content}",
            "compact": "[{collection}] {content}",
            "detailed": "Memory Entry:\n- Collection: {collection}\n- Source: {source}\n- Score: {score}\n- Timestamp: {timestamp}\n\nContent:\n{content}",
            "minimal": "{content}",
        }
    
    def assemble(
        self,
        retrieval_results: List[Dict[str, Any]],
        template: str = "default",
        chronological: bool = False,
        include_metadata: bool = True
    ) -> AssembledContext:
        """
        Assemble retrieval results into formatted context.
        
        Args:
            retrieval_results: List of retrieval results from RetrievalEngine
            template: Formatting template name
            chronological: If True, sort by timestamp instead of score
            include_metadata: If True, include metadata in output
            
        Returns:
            AssembledContext with formatted memories
        """
        if not retrieval_results:
            return AssembledContext()
        
        # Convert to MemoryContext objects
        memory_contexts = []
        seen_content = set() if self.deduplication else None
        
        for result in retrieval_results:
            payload = result.get("payload", {})
            
            # Extract fields
            content = payload.get("content", "")
            source = payload.get("source", "unknown")
            collection = result.get("collection", "unknown")
            score = result.get("score", 0.0)
            timestamp_str = payload.get("timestamp")
            
            # Parse timestamp
            timestamp = None
            if timestamp_str:
                if isinstance(timestamp_str, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    except:
                        pass
                elif isinstance(timestamp_str, datetime):
                    timestamp = timestamp_str
            
            # Deduplication
            if seen_content is not None:
                content_hash = hash(f"{content[:100]}{collection}")
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)
            
            # Create MemoryContext
            context = MemoryContext(
                content=content,
                source=source,
                collection=collection,
                score=score,
                metadata=payload,
                timestamp=timestamp,
                confidence=score  # Use score as confidence proxy
            )
            memory_contexts.append(context)
        
        # Sort memories
        if chronological and any(m.timestamp for m in memory_contexts):
            # Sort by timestamp (oldest first)
            memory_contexts.sort(key=lambda m: m.timestamp or datetime.min)
        else:
            # Sort by score (highest first)
            memory_contexts.sort(key=lambda m: m.score, reverse=True)
        
        # Apply token budget
        current_token_count = 0
        final_memories = []
        
        for context in memory_contexts:
            # Estimate tokens for this memory
            memory_tokens = self._estimate_tokens(context.to_string(template))
            
            if current_token_count + memory_tokens > self.token_budget:
                logger.debug(f"Token budget exceeded, stopping at {len(final_memories)} memories")
                break
            
            if len(final_memories) >= self.max_memories:
                logger.debug(f"Max memories reached ({self.max_memories})")
                break
            
            final_memories.append(context)
            current_token_count += memory_tokens
        
        # Build AssembledContext
        assembled = AssembledContext(
            memories=final_memories,
            total_tokens=current_token_count,
            collections_used=list(set(m.collection for m in final_memories)),
            timestamps=[m.timestamp for m in final_memories if m.timestamp]
        )
        
        return assembled
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in text"""
        # Simple estimation: count words + punctuation
        # This is a rough approximation; for better accuracy, use a tokenizer
        if not text:
            return 0
        
        # Split on whitespace and punctuation
        tokens = re.findall(r"\b\w+\b|[.,;!?\-]", text)
        return len(tokens)
    
    def _estimate_tokens_accurate(self, text: str) -> int:
        """More accurate token estimation using a simple tokenizer"""
        # This is still approximate but better than word counting
        if not text:
            return 0
        
        # Count characters and divide by average token length
        char_count = len(text)
        # Average token length in English/French is ~5 characters
        return max(1, char_count // 5)
    
    def get_token_count(self, text: str) -> int:
        """Get token count for text (public method)"""
        return self._estimate_tokens_accurate(text)
    
    def format_memory(
        self,
        memory: MemoryContext,
        template: str = "default"
    ) -> str:
        """Format a single memory context"""
        if template in self.formatting_templates:
            return memory.to_string(self.formatting_templates[template])
        return memory.to_string()
    
    def set_formatting_template(
        self,
        name: str,
        template: str
    ) -> None:
        """Add or update a formatting template"""
        self.formatting_templates[name] = template
    
    def assemble_from_multiple_collections(
        self,
        collection_results: Dict[str, List[Dict[str, Any]]],
        template: str = "default",
        collection_order: Optional[List[str]] = None
    ) -> AssembledContext:
        """
        Assemble results from multiple collections.
        
        Args:
            collection_results: Dict mapping collection names to result lists
            template: Formatting template name
            collection_order: Optional order for collections
            
        Returns:
            AssembledContext with combined memories
        """
        # Flatten all results
        all_results = []
        for collection, results in collection_results.items():
            for result in results:
                result["collection"] = collection
                all_results.append(result)
        
        return self.assemble(all_results, template)
    
    def prioritize_by_collection(
        self,
        context: AssembledContext,
        collection_priority: Dict[str, int]
    ) -> AssembledContext:
        """
        Re-sort memories by collection priority.
        
        Args:
            context: The assembled context to reorder
            collection_priority: Dict mapping collection names to priority values
            
        Returns:
            New AssembledContext with reordered memories
        """
        # Sort memories by collection priority
        sorted_memories = sorted(
            context.memories,
            key=lambda m: collection_priority.get(m.collection, 0),
            reverse=True
        )
        
        return AssembledContext(
            memories=sorted_memories,
            total_tokens=context.total_tokens,
            collections_used=context.collections_used,
            timestamps=context.timestamps
        )
    
    def filter_by_confidence(
        self,
        context: AssembledContext,
        min_confidence: float = 0.5
    ) -> AssembledContext:
        """Filter memories by confidence score"""
        filtered = [m for m in context.memories if m.confidence >= min_confidence]
        
        return AssembledContext(
            memories=filtered,
            total_tokens=self._estimate_tokens_accurate("".join(m.content for m in filtered)),
            collections_used=context.collections_used,
            timestamps=context.timestamps
        )
    
    def chunk_context(
        self,
        context: AssembledContext,
        max_tokens: int = 1000
    ) -> List[AssembledContext]:
        """
        Split context into chunks that fit within token limits.
        
        Useful when the assembled context is too large for a single prompt.
        
        Args:
            context: The assembled context to chunk
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of AssembledContext chunks
        """
        if context.total_tokens <= max_tokens:
            return [context]
        
        chunks = []
        current_chunk = []
        current_token_count = 0
        
        for memory in context.memories:
            memory_tokens = self._estimate_tokens_accurate(
                self.format_memory(memory)
            )
            
            if current_token_count + memory_tokens > max_tokens and current_chunk:
                chunks.append(AssembledContext(
                    memories=current_chunk,
                    total_tokens=current_token_count,
                    collections_used=list(set(m.collection for m in current_chunk)),
                    timestamps=[m.timestamp for m in current_chunk if m.timestamp]
                ))
                current_chunk = []
                current_token_count = 0
            
            current_chunk.append(memory)
            current_token_count += memory_tokens
        
        # Add the last chunk
        if current_chunk:
            chunks.append(AssembledContext(
                memories=current_chunk,
                total_tokens=current_token_count,
                collections_used=list(set(m.collection for m in current_chunk)),
                timestamps=[m.timestamp for m in current_chunk if m.timestamp]
            ))
        
        return chunks
