"""
Agent Runtime - Main Orchestration Layer
========================================

This is the CORE of the Agent Runtime Layer.
It implements the complete memory loop:

    USER INPUT
       ↓
   Intent Classification
       ↓
   Memory Retrieval Policy  →  Should we retrieve? What? From where?
       ↓
   Qdrant Retrieval  →  Get relevant memories
       ↓
   Context Assembly  →  Format memories for LLM
       ↓
   Prompt Augmentation  →  Inject context into prompt
       ↓
   LLM Generation  →  Generate response (via Goose/Ollama)
       ↓
   Tool Execution  →  Call tools/workflows (N8N, FastAPI)
       ↓
   Memory Writeback  →  Store new memories
       ↓
   Audit Logging  →  Log everything to PostgreSQL

This connects ALL your existing infrastructure:
- Goose/Ollama (LLM)
- Qdrant (Memory)
- PostgreSQL (Audit)
- N8N (Workflow Automation)
- FastAPI Tool Gateway (Tool Execution)
"""

import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional, Union, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging
import aiohttp

from .config import AgentRuntimeConfig, load_config
from .memory_policy import MemoryPolicyEngine, RetrievalPolicy
from .retrieval_engine import RetrievalEngine, RetrievalResult
from .context_assembler import ContextAssembler, AssembledContext, MemoryContext
from .prompt_augmenter import PromptAugmenter
from .n8n_integrator import N8NIntegrator, N8NExecution
from .memory_taxonomy import MEMORY_COLLECTIONS, create_memory_payload

logger = logging.getLogger(__name__)


class RuntimeStatus(Enum):
    """Status of a runtime execution"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class RuntimeResult:
    """Result of a runtime execution"""
    status: RuntimeStatus
    input: str
    intent: str = ""
    policies_applied: List[str] = field(default_factory=list)
    retrieved_memories: List[Dict] = field(default_factory=list)
    assembled_context: Optional[AssembledContext] = None
    system_prompt: str = ""
    user_prompt: str = ""
    llm_response: Optional[str] = None
    tool_executions: List[Dict] = field(default_factory=list)
    memory_written: List[Dict] = field(default_factory=list)
    workflow_executions: List[Dict] = field(default_factory=list)
    audit_log: Optional[Dict] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        # Handle non-serializable objects
        result["assembled_context"] = self.assembled_context.to_dict() if self.assembled_context else None
        result["status"] = self.status.value
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


@dataclass
class ToolExecution:
    """Represents a tool execution"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentRuntime:
    """
    Main Agent Runtime class.
    
    Orchestrates the complete agent loop:
    1. Intent Classification
    2. Memory Retrieval Policy
    3. Context Assembly
    4. Prompt Augmentation
    5. LLM Generation
    6. Tool Execution
    7. Memory Writeback
    8. Audit Logging
    
    This is the "système nerveux" that connects Goose to your memory infrastructure.
    """
    
    def __init__(
        self,
        config: Optional[AgentRuntimeConfig] = None,
        retrieval_engine: Optional[RetrievalEngine] = None,
        policy_engine: Optional[MemoryPolicyEngine] = None,
        context_assembler: Optional[ContextAssembler] = None,
        prompt_augmenter: Optional[PromptAugmenter] = None,
        n8n_integrator: Optional[N8NIntegrator] = None
    ):
        # Configuration
        self.config = config or load_config()
        
        # Initialize components
        self.retrieval_engine = retrieval_engine or RetrievalEngine()
        self.policy_engine = policy_engine or MemoryPolicyEngine()
        self.context_assembler = context_assembler or ContextAssembler()
        self.prompt_augmenter = prompt_augmenter or PromptAugmenter()
        self.n8n_integrator = n8n_integrator or N8NIntegrator()
        
        # Conversation state
        self.conversation_history: List[Dict[str, str]] = []
        self.session_id: str = str(uuid.uuid4())
        
        # Load permanent memory (mémoireDure)
        self._load_permanent_memory()
        
        # Metrics
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_retrievals": 0,
            "total_memory_writes": 0,
            "total_tool_executions": 0,
            "avg_execution_time": 0.0,
            "last_execution_time": datetime.utcnow()
        }
        
        # Ensure collections exist
        try:
            self.retrieval_engine.ensure_collections_exist()
            logger.info("All Qdrant collections verified/existing")
        except Exception as e:
            logger.warning(f"Could not verify collections: {e}")
        
        logger.info("Agent Runtime initialized successfully")
    
    def _load_permanent_memory(self) -> None:
        """
        Charge les mémoires permanentes depuis le dossier mémoireDure.
        Ce dossier contient des éléments qui doivent être mémorisés et utilisés
        constamment par GOOSE.
        
        Affiche un message de confirmation: "Ça y est j'ai actualisé la mémoire - Yeepeekayee"
        """
        import os
        from pathlib import Path
        
        # Chemin vers le dossier mémoireDure (dans private/)
        memory_dir = Path("private/mémoireDure")
        
        # Vérifier si le dossier existe
        if not memory_dir.exists():
            logger.debug(f"Dossier mémoireDure non trouvé: {memory_dir.absolute()}")
            return
        
        # Lister tous les fichiers de mémoire
        memory_files = []
        for file_path in memory_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.md', '.json', '.txt']:
                memory_files.append(file_path)
        
        if not memory_files:
            logger.debug(f"Aucun fichier de mémoire trouvé dans {memory_dir}")
            return
        
        # Charger chaque fichier et stocker en mémoire
        loaded_count = 0
        for file_path in memory_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Créer un payload pour Qdrant
                payload = {
                    "content": content,
                    "source": str(file_path.relative_to(memory_dir)),
                    "type": "permanent_memory",
                    "category": "mémoireDure",
                    "priority": "high",
                    "user_id": "system",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Stocker dans Qdrant (collection mémoireDure_memory)
                try:
                    self.retrieval_engine.store_memory(
                        "mémoireDure_memory",
                        payload
                    )
                    loaded_count += 1
                    logger.info(f"Mémoire chargée: {file_path.relative_to(memory_dir)}")
                except Exception as e:
                    logger.warning(f"Erreur lors du stockage de {file_path}: {e}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de {file_path}: {e}")
        
        # Afficher le message de confirmation
        if loaded_count > 0:
            print("Ça y est j'ai actualisé la mémoire - Yeepeekayee")
            logger.info(f"{loaded_count} mémoires permanentes chargées depuis {memory_dir}")
    
    def refresh_permanent_memory(self) -> int:
        """
        Actualise manuellement les mémoires permanentes depuis mémoireDure.
        
        Returns:
            Nombre de mémoires chargées
        """
        self._load_permanent_memory()
        # Le message est déjà affiché dans _load_permanent_memory
        # Cette méthode permet de forcer un rechargement manuel
        return 0  # Le vrai count est géré dans _load_permanent_memory
    
    async def run(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        template: Optional[str] = None,
        enable_memory: Optional[bool] = None,
        enable_tools: Optional[bool] = None,
        enable_audit: Optional[bool] = None,
        **kwargs
    ) -> RuntimeResult:
        """
        Execute the complete agent runtime loop.
        
        This is the MAIN ENTRY POINT for the Agent Runtime.
        Call this method with user input to get an orchestrated response.
        
        Args:
            user_input: The raw user input text
            user_id: Optional user ID for personalization
            session_id: Optional session ID for conversation tracking
            template: Optional prompt template name
            enable_memory: Override memory enable setting
            enable_tools: Override tools enable setting
            enable_audit: Override audit enable setting
            **kwargs: Additional parameters for specific use cases
            
        Returns:
            RuntimeResult with complete execution details
        """
        import time
        
        start_time = time.time()
        user_id = user_id or self.config.user_id
        session_id = session_id or self.session_id
        
        # Initialize result
        result = RuntimeResult(
            status=RuntimeStatus.INITIALIZED,
            input=user_input,
            user_id=user_id,
            session_id=session_id
        )
        
        try:
            # Step 1: Intent Classification
            result.intent = self.policy_engine.extract_intent(user_input)
            logger.debug(f"Intent extracted: {result.intent}")
            
            # Step 2: Memory Retrieval Policy
            policies = self.policy_engine.get_policies_for_input(
                user_input, 
                intent=result.intent
            )
            result.policies_applied = [p.name for p in policies]
            logger.debug(f"Policies applied: {result.policies_applied}")
            
            # Step 3: Execute Retrieval if policies match
            if policies and (enable_memory if enable_memory is not None else self.config.enable_memory):
                await self._execute_retrieval(
                    user_input, 
                    user_id, 
                    policies, 
                    result
                )
            
            # Step 4: Context Assembly
            if result.retrieved_memories:
                result.assembled_context = self.context_assembler.assemble(
                    result.retrieved_memories,
                    template="default"
                )
                logger.debug(f"Context assembled: {result.assembled_context.total_tokens} tokens")
            
            # Step 5: Prompt Augmentation
            result.system_prompt, result.user_prompt = self.prompt_augmenter.augment(
                user_input=user_input,
                memory_context=result.assembled_context,
                intent=result.intent,
                template=template,
                conversation_history=self.conversation_history
            )
            logger.debug(f"Prompt augmented: system={len(result.system_prompt)} chars, user={len(result.user_prompt)} chars")
            
            # Step 6: LLM Generation (via Goose/Ollama)
            result.llm_response = await self._generate_with_llm(
                result.system_prompt,
                result.user_prompt
            )
            logger.debug(f"LLM response generated: {len(result.llm_response) if result.llm_response else 0} chars")
            
            # Step 7: Tool Execution (if needed)
            if enable_tools if enable_tools is not None else True:
                await self._execute_tools(
                    user_input,
                    result.llm_response,
                    result.intent,
                    result
                )
            
            # Step 8: Memory Writeback
            if enable_memory if enable_memory is not None else self.config.enable_memory:
                await self._writeback_memory(
                    user_input,
                    result.llm_response,
                    result.intent,
                    user_id,
                    session_id,
                    result
                )
            
            # Step 9: Audit Logging
            if enable_audit if enable_audit is not None else self.config.enable_audit:
                result.audit_log = await self._log_to_audit(
                    result,
                    start_time
                )
            
            # Update conversation history
            if self.config.enable_memory:
                self.prompt_augmenter.update_conversation_history(
                    user_input=user_input,
                    ai_response=result.llm_response or "",
                    intent=result.intent
                )
            
            # Update metrics
            result.execution_time = time.time() - start_time
            self.metrics["total_executions"] += 1
            self.metrics["successful_executions"] += 1
            self.metrics["last_execution_time"] = datetime.utcnow()
            self.metrics["avg_execution_time"] = (
                (self.metrics["avg_execution_time"] * (self.metrics["total_executions"] - 1) + result.execution_time) 
                / self.metrics["total_executions"]
            ) if self.metrics["total_executions"] > 0 else 0
            
            result.status = RuntimeStatus.COMPLETED
            
        except asyncio.TimeoutError:
            result.error = "Execution timed out"
            result.status = RuntimeStatus.TIMEOUT
            self.metrics["failed_executions"] += 1
        except Exception as e:
            result.error = str(e)
            result.status = RuntimeStatus.FAILED
            self.metrics["failed_executions"] += 1
            logger.error(f"Runtime execution failed: {e}", exc_info=True)
        
        return result
    
    async def _execute_retrieval(
        self,
        user_input: str,
        user_id: str,
        policies: List[RetrievalPolicy],
        result: RuntimeResult
    ) -> None:
        """Execute memory retrieval based on policies"""
        retrieval_tasks = []
        
        for policy in policies:
            try:
                retrieval_results = await self.retrieval_engine.retrieve(
                    query=user_input,
                    collection_name=policy.collection,
                    metadata_filters=policy.metadata_filters,
                    limit=policy.limit,
                    confidence_threshold=policy.confidence_threshold,
                    user_id=user_id
                )
                
                result.retrieved_memories.extend(
                    [r.to_dict() for r in retrieval_results]
                )
                
                self.metrics["total_retrievals"] += 1
                logger.debug(f"Retrieved {len(retrieval_results)} memories from {policy.collection}")
                
            except Exception as e:
                logger.error(f"Retrieval failed for policy {policy.name}: {e}")
        
        # Deduplicate results
        seen_ids = set()
        unique_results = []
        for r in result.retrieved_memories:
            r_id = r.get("id")
            if r_id and r_id in seen_ids:
                continue
            if r_id:
                seen_ids.add(r_id)
            unique_results.append(r)
        result.retrieved_memories = unique_results
    
    async def _generate_with_llm(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[str]:
        """
        Generate a response using Goose/Ollama.
        
        This connects to your existing Ollama setup.
        Can be extended to use Goose directly.
        """
        try:
            import aiohttp
            
            url = f"http://{self.config.ollama.host}:{self.config.ollama.port}/api/generate"
            
            payload = {
                "model": self.config.ollama.chat_model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 4096
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "")
                    else:
                        error = await response.text()
                        logger.error(f"LLM generation failed: {response.status} - {error}")
                        return None
                        
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None
    
    async def _execute_tools(
        self,
        user_input: str,
        llm_response: Optional[str],
        intent: str,
        result: RuntimeResult
    ) -> None:
        """
        Execute tools based on intent and LLM response.
        
        This is where we integrate with:
        - N8N workflows
        - FastAPI Tool Gateway
        - Custom tool executions
        """
        if not llm_response:
            return
        
        # Check for N8N workflow execution requests
        if intent in ["n8n_workflow", "web_scraping"]:
            await self._execute_n8n_tools(user_input, llm_response, result)
        
        # Check for scraping requests in the input
        if any(word in user_input.lower() for word in ["scrape", "scraper", "extraire", "url", "lien"]):
            await self._execute_scraping_tools(user_input, result)
        
        # Check for job matching
        if intent == "job_match" or "match" in user_input.lower():
            await self._execute_job_matching(result)
    
    async def _execute_n8n_tools(
        self,
        user_input: str,
        llm_response: str,
        result: RuntimeResult
    ) -> None:
        """Execute N8N workflows"""
        if not self.config.enable_n8n:
            logger.debug("N8N integration disabled")
            return
        
        try:
            # Try to extract URL from input
            url = self._extract_url(user_input)
            
            if url:
                # Create scraping parameters
                parameters = self.n8n_integrator.create_scraping_parameters(
                    url=url,
                    fields=["title", "description", "requirements", "company", "location"]
                )
                
                # Find or create a scraping workflow
                workflows = await self.n8n_integrator.find_workflows_by_tag("scraper")
                
                if workflows:
                    # Use existing workflow
                    workflow = workflows[0]
                    execution = await self.n8n_integrator.execute_workflow(
                        workflow.id,
                        parameters=parameters,
                        wait_for_completion=True,
                        timeout=60
                    )
                    
                    if execution:
                        result.workflow_executions.append({
                            "workflow_id": workflow.id,
                            "workflow_name": workflow.name,
                            "execution_id": execution.id,
                            "status": execution.status,
                            "result": execution.result
                        })
                        
                        # If execution succeeded, add result to memory
                        if execution.status == "success" and execution.result:
                            await self._store_scraping_result(
                                url,
                                execution.result,
                                result.user_id
                            )
                        
                        self.metrics["total_tool_executions"] += 1
                else:
                    # Create a new workflow
                    workflow_id = await self.n8n_integrator.create_scraping_workflow(
                        name=f"Scraper for {url}",
                        url=url,
                        extract_fields=["title", "description", "requirements", "company", "location"],
                        description=f"Auto-created scraper for: {user_input[:100]}"
                    )
                    
                    if workflow_id:
                        result.workflow_executions.append({
                            "workflow_id": workflow_id,
                            "workflow_name": f"Scraper for {url}",
                            "status": "created",
                            "message": "Workflow created, needs activation"
                        })
                        self.metrics["total_tool_executions"] += 1
            
        except Exception as e:
            logger.error(f"N8N tool execution failed: {e}")
            result.workflow_executions.append({
                "error": str(e)
            })
    
    async def _execute_scraping_tools(
        self,
        user_input: str,
        result: RuntimeResult
    ) -> None:
        """Execute scraping tools directly"""
        if not self.config.enable_n8n:
            logger.debug("N8N integration disabled")
            return
        
        try:
            # Extract URL and fields from input
            url = self._extract_url(user_input)
            fields = self._extract_fields(user_input)
            
            if url:
                # Create parameters
                parameters = self.n8n_integrator.create_scraping_parameters(
                    url=url,
                    fields=fields or ["title", "description", "requirements"]
                )
                
                # Execute via webhook (if configured)
                webhook_result = await self.n8n_integrator.execute_webhook(
                    webhook_path="job-scraper",  # Default webhook path
                    parameters=parameters
                )
                
                if webhook_result:
                    result.workflow_executions.append({
                        "webhook": "job-scraper",
                        "url": url,
                        "result": webhook_result
                    })
                    
                    # Store result in memory
                    await self._store_scraping_result(
                        url,
                        webhook_result,
                        result.user_id
                    )
                    self.metrics["total_tool_executions"] += 1
            
        except Exception as e:
            logger.error(f"Scraping tool execution failed: {e}")
            result.workflow_executions.append({
                "error": str(e)
            })
    
    async def _execute_job_matching(
        self,
        result: RuntimeResult
    ) -> None:
        """Execute job matching logic"""
        try:
            # This is a placeholder for actual job matching logic
            # In a real implementation, this would:
            # 1. Retrieve user profile from candidate_memory
            # 2. Retrieve job listings from jobs_memory
            # 3. Calculate match scores
            # 4. Return top matches
            
            # For now, just log that matching was attempted
            result.tool_executions.append({
                "tool": "job_matcher",
                "status": "not_implemented",
                "message": "Job matching logic needs implementation"
            })
            
        except Exception as e:
            logger.error(f"Job matching failed: {e}")
            result.tool_executions.append({
                "tool": "job_matcher",
                "status": "error",
                "error": str(e)
            })
    
    async def _writeback_memory(
        self,
        user_input: str,
        llm_response: Optional[str],
        intent: str,
        user_id: str,
        session_id: str,
        result: RuntimeResult
    ) -> None:
        """Write back to memory based on the interaction"""
        if not llm_response:
            return
        
        try:
            # Store conversation memory
            conversation_payload = create_memory_payload(
                collection_name="conversation_memory",
                content=user_input,
                user_id=user_id,
                session_id=session_id,
                turn=len(self.prompt_augmenter.conversation_history) // 2 + 1,
                role="user",
                intent=intent
            )
            self.retrieval_engine.store_memory(
                "conversation_memory",
                conversation_payload
            )
            self.metrics["total_memory_writes"] += 1
            result.memory_written.append({
                "collection": "conversation_memory",
                "type": "user_input",
                "content": user_input[:100] + "...",
                "id": conversation_payload.get("id")
            })
            
            # Store AI response
            ai_payload = create_memory_payload(
                collection_name="conversation_memory",
                content=llm_response,
                user_id=user_id,
                session_id=session_id,
                turn=len(self.prompt_augmenter.conversation_history) // 2 + 1,
                role="assistant",
                intent=intent
            )
            self.retrieval_engine.store_memory(
                "conversation_memory",
                ai_payload
            )
            self.metrics["total_memory_writes"] += 1
            result.memory_written.append({
                "collection": "conversation_memory",
                "type": "ai_response",
                "content": llm_response[:100] + "...",
                "id": ai_payload.get("id")
            })
            
            # Store preferences if detected
            if intent == "language_preference":
                language = self._extract_language(user_input)
                if language:
                    pref_payload = create_memory_payload(
                        collection_name="preferences_memory",
                        content=f"User prefers {language}",
                        user_id=user_id,
                        preference_type="language",
                        value=language,
                        priority=10,
                        source="agent"
                    )
                    self.retrieval_engine.store_memory(
                        "preferences_memory",
                        pref_payload
                    )
                    self.metrics["total_memory_writes"] += 1
                    result.memory_written.append({
                        "collection": "preferences_memory",
                        "type": "language_preference",
                        "value": language,
                        "id": pref_payload.get("id")
                    })
            
            # Store decision if relevant
            decision_payload = create_memory_payload(
                collection_name="decision_memory",
                content=f"Intent: {intent}, Policies: {', '.join(result.policies_applied)}",
                user_id=user_id,
                session_id=session_id,
                decision_type="intent_classification",
                context={
                    "input": user_input[:200],
                    "intent": intent,
                    "policies": result.policies_applied
                },
                choice=intent,
                reasoning=f"Classified as {intent} based on keyword matching",
                confidence=0.8,
                outcome="success" if llm_response else "failed"
            )
            self.retrieval_engine.store_memory(
                "decision_memory",
                decision_payload
            )
            self.metrics["total_memory_writes"] += 1
            
        except Exception as e:
            logger.error(f"Memory writeback failed: {e}")
    
    async def _store_scraping_result(
        self,
        url: str,
        result: Dict[str, Any],
        user_id: str
    ) -> None:
        """Store scraping result in memory"""
        try:
            # Extract job data from result
            title = result.get("title", "") or result.get("data", {}).get("title", "")
            description = result.get("description", "") or result.get("data", {}).get("description", "")
            company = result.get("company", "") or result.get("data", {}).get("company", "")
            location = result.get("location", "") or result.get("data", {}).get("location", "")
            requirements = result.get("requirements", "") or result.get("data", {}).get("requirements", "")
            
            # Create job payload
            job_payload = create_memory_payload(
                collection_name="jobs_memory",
                content=f"{title}\n\n{description}\n\nRequirements: {requirements}",
                user_id=user_id,
                job_id=f"job_{hash(url) % 1000000:06d}",
                title=title or "Untitled Job",
                company=company,
                location=location,
                source="scraped",
                url=url,
                status="saved"
            )
            
            self.retrieval_engine.store_memory(
                "jobs_memory",
                job_payload
            )
            self.metrics["total_memory_writes"] += 1
            
        except Exception as e:
            logger.error(f"Failed to store scraping result: {e}")
    
    async def _log_to_audit(
        self,
        result: RuntimeResult,
        start_time: float
    ) -> Dict[str, Any]:
        """Log execution to PostgreSQL audit"""
        try:
            import psycopg2
            from psycopg2 import sql
            
            conn = psycopg2.connect(
                host=self.config.postgres.host,
                port=self.config.postgres.port,
                dbname=self.config.postgres.database,
                user=self.config.postgres.user,
                password=self.config.postgres.password
            )
            
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_runtime_audit (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255),
                    user_id VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    input_text TEXT,
                    intent VARCHAR(255),
                    status VARCHAR(50),
                    execution_time FLOAT,
                    policies_applied JSONB,
                    memories_retrieved INTEGER,
                    memories_written INTEGER,
                    tools_executed INTEGER,
                    error TEXT,
                    result_summary JSONB
                )
            """)
            conn.commit()
            
            # Insert log entry
            cursor.execute("""
                INSERT INTO agent_runtime_audit (
                    session_id, user_id, input_text, intent, status, 
                    execution_time, policies_applied, memories_retrieved, 
                    memories_written, tools_executed, error, result_summary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                result.session_id,
                result.user_id,
                result.input[:1000],  # Truncate long inputs
                result.intent,
                result.status.value,
                result.execution_time,
                json.dumps(result.policies_applied),
                len(result.retrieved_memories),
                len(result.memory_written),
                len(result.tool_executions),
                result.error,
                json.dumps({
                    "llm_response_length": len(result.llm_response) if result.llm_response else 0,
                    "workflow_executions": len(result.workflow_executions),
                    "collections_used": result.assembled_context.collections_used if result.assembled_context else []
                })
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "message": "Logged to PostgreSQL audit"
            }
            
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from text"""
        import re
        url_pattern = re.compile(
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[\w./?=&-]*'
        )
        match = url_pattern.search(text)
        return match.group(0) if match else None
    
    def _extract_fields(self, text: str) -> List[str]:
        """Extract field names from text"""
        # Look for common field patterns
        field_patterns = [
            "title", "description", "company", "location", "salary",
            "requirements", "qualifications", "skills", "experience",
            "date", "contact", "email", "phone"
        ]
        
        text_lower = text.lower()
        extracted = []
        
        for field in field_patterns:
            if field in text_lower:
                extracted.append(field)
        
        return extracted if extracted else None
    
    def _extract_language(self, text: str) -> Optional[str]:
        """Extract language preference from text"""
        language_patterns = [
            ("français", "French"),
            ("english", "English"),
            ("spanish", "Spanish"),
            ("german", "German"),
            ("italian", "Italian"),
            ("dutch", "Dutch"),
        ]
        
        text_lower = text.lower()
        
        for pattern, language in language_patterns:
            if pattern in text_lower:
                return language
        
        # Check for direct language names
        direct_languages = ["french", "english", "spanish", "german", "italian", "dutch"]
        for lang in direct_languages:
            if lang in text_lower:
                return lang.capitalize()
        
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get runtime metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset runtime metrics"""
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_retrievals": 0,
            "total_memory_writes": 0,
            "total_tool_executions": 0,
            "avg_execution_time": 0.0,
            "last_execution_time": datetime.utcnow()
        }
    
    def clear_conversation(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
        self.prompt_augmenter.clear_conversation_history()
        self.session_id = str(uuid.uuid4())
    
    def set_session_id(self, session_id: str) -> None:
        """Set a custom session ID"""
        self.session_id = session_id
        self.prompt_augmenter.conversation_history = []


# Singleton instance
_runtime: Optional[AgentRuntime] = None


def get_agent_runtime(config: Optional[AgentRuntimeConfig] = None) -> AgentRuntime:
    """Get or create the global Agent Runtime instance"""
    global _runtime
    if _runtime is None:
        _runtime = AgentRuntime(config=config)
    return _runtime
