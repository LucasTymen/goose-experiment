# Agent Runtime Layer for GOOSE

> **The "système nerveux" that connects GOOSE to its memory infrastructure**

---

## 🎯 The Problem We Solved

You had built:
- ✅ **Memory**: Qdrant vector database with embeddings
- ✅ **Retrieval**: FastAPI endpoints for semantic search
- ✅ **Audit**: PostgreSQL logging
- ✅ **Tools**: N8N workflows, FastAPI services
- ✅ **LLM**: Goose/Ollama integration

**BUT**: Goose had **NO COGNITIVE CONNECTION** to any of this.

- Goose didn't know the memory existed
- Goose didn't know when to retrieve
- Goose didn't know what to retrieve
- Goose didn't know how to use retrieved context
- Goose didn't store new memories

This layer **fixes all of that**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT RUNTIME LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  USER INPUT                                                       │
│       │                                                           │
│       ▼                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │ Intent       │───▶│ Memory       │───▶│ Qdrant              │ │
│  │ Classifier   │    │ Policy       │    │ Retrieval           │ │
│  └──────────────┘    │ Engine       │    │ Engine              │ │
│                      └──────────────┘    └──────────┬───────────┘ │
│                                                        │             │
│                                                        ▼             │
│                                                 ┌──────────────┐       │
│                                                 │ Context      │       │
│                                                 │ Assembler    │       │
│                                                 └──────────────┘       │
│                                                        │             │
│                                                        ▼             │
│                                                 ┌──────────────┐       │
│                                                 │ Prompt       │       │
│                                                 │ Augmenter    │       │
│                                                 └──────────────┘       │
│                                                        │             │
│                                                        ▼             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    GOOSE/OLLAMA (LLM)                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                        │             │
│                                                        ▼             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Tool Execution:                                            │ │
│  │  - N8N Workflows (scraping, automation)                    │ │
│  │  - FastAPI Tool Gateway (existing endpoints)               │ │
│  │  - Custom tool integration                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                        │             │
│                                                        ▼             │
│                                                 ┌──────────────┐       │
│                                                 │ Memory       │       │
│                                                 │ Writeback    │       │
│                                                 └──────────────┘       │
│                                                        │             │
│                                                        ▼             │
│                                                 ┌──────────────┐       │
│                                                 │ Audit        │       │
│                                                 │ Logging      │       │
│                                                 │ (PostgreSQL) │       │
│                                                 └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure

```
agent_runtime/
├── __init__.py              # Public API and exports
├── config.py               # Configuration management
├── memory_taxonomy.py      # Qdrant collection definitions
├── memory_policy.py        # Retrieval policy engine (WHEN to retrieve)
├── retrieval_engine.py     # Qdrant retrieval engine (HOW to retrieve)
├── context_assembler.py    # Context formatting for LLM
├── prompt_augmenter.py      # Prompt engineering with context
├── n8n_integrator.py       # N8N workflow integration
├── runtime.py              # Main orchestration layer (THE CORE)
│
└── examples/
    ├── __init__.py
    ├── demo_basic.py        # Basic demonstration scripts
    └── demo_advanced.py     # Advanced usage examples
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install qdrant-client aiohttp psycopg2-binary

# Development dependencies
pip install pytest black flake8 mypy
```

### 2. Configure Environment

Create a `.env` file or set environment variables:

```bash
# Qdrant (default: localhost:6334)
export QDRANT_HOST=localhost
export QDRANT_PORT=6334

# Ollama (default: localhost:11434)
export OLLAMA_HOST=localhost
export OLLAMA_PORT=11434
export EMBEDDING_MODEL=all-minilm:latest
export CHAT_MODEL=llama3:latest

# PostgreSQL (default: localhost:5434)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5434
export POSTGRES_DB=goose_ai
export POSTGRES_USER=goose
export POSTGRES_PASSWORD=goosepass

# N8N (default: localhost:5684)
export N8N_HOST=localhost
export N8N_PORT=5684
```

### 3. Initialize Collections

The Agent Runtime will automatically create all required Qdrant collections on first run.

### 4. Run the Demo

```bash
# Run basic demo
python agent_runtime/examples/demo_basic.py

# Or run individual demos
python -c "
import asyncio
from agent_runtime import get_agent_runtime

async def test():
    runtime = get_agent_runtime()
    result = await runtime.run('Parlons français')
    print(result.to_json())

asyncio.run(test())
"
```

---

## 🎯 Usage Examples

### Basic Usage

```python
import asyncio
from agent_runtime import AgentRuntime, RuntimeConfig

async def main():
    # Create runtime with user ID
    runtime = AgentRuntime(config=RuntimeConfig(user_id="user_123"))
    
    # Run with user input
    result = await runtime.run("Parlons français")
    
    # Access results
    print(f"Intent: {result.intent}")
    print(f"Response: {result.llm_response}")
    print(f"Policies: {result.policies_applied}")
    print(f"Memories Retrieved: {len(result.retrieved_memories)}")
    
asyncio.run(main())
```

### With Custom Configuration

```python
from agent_runtime import AgentRuntime, RuntimeConfig, QdrantConfig, OllamaConfig

config = RuntimeConfig(
    user_id="lucas",
    qdrant=QdrantConfig(host="localhost", port=6334),
    ollama=OllamaConfig(host="localhost", port=11434, chat_model="mistral:latest"),
    enable_memory=True,
    enable_audit=True
)

runtime = AgentRuntime(config=config)
```

### Session Management

```python
# Start a new session
runtime = AgentRuntime(config=RuntimeConfig(user_id="user_123"))

# Run multiple interactions in the same session
result1 = await runtime.run("Parlons français")
result2 = await runtime.run("Génère mon CV")  # Remembers language preference

# Clear session
runtime.clear_conversation()
```

---

## 🧠 Memory Taxonomy

The system defines 9 types of memory collections:

| Collection | Purpose | Example Use Case |
|------------|---------|------------------|
| `candidate_memory` | User profile, skills, experience | Storing CV data, skills, work history |
| `preferences_memory` | User preferences | Language, style, format preferences |
| `jobs_memory` | Job listings and applications | Storing scraped job postings |
| `ats_memory` | ATS optimization patterns | Keywords, best practices, scoring |
| `workflow_memory` | N8N workflow executions | Scraping history, automation results |
| `recruiter_memory` | Recruiter interactions | Contact history, company info |
| `infra_memory` | Infrastructure documentation | System docs, configurations |
| `conversation_memory` | Conversation history | Short-term conversation context |
| `decision_memory` | Agent decisions | Intent classification, reasoning |

Each collection has:
- Defined metadata schema
- Required fields
- Default retrieval parameters
- Indexing configuration

---

## 🎛️ Memory Policy Engine

The **core innovation** that solves your problem.

This engine **decides WHEN and WHAT to retrieve** based on:

### Policy Types

1. **Intent-Based**: Triggered by classified intent
   - Example: `cv_generation` intent → retrieve from `candidate_memory`

2. **Keyword-Based**: Triggered by keywords in input
   - Example: "scraper" or "url" → retrieve scraping workflows

3. **Contextual**: Triggered by conversation state
   - Example: If previous turn was about CV → continue CV context

4. **Temporal**: Triggered by time-based rules
   - Example: "What did we do yesterday?" → retrieve recent memories

### Example Policies

```python
# Language preference policy
policy = RetrievalPolicy(
    name="language_preference",
    intents=["language", "langue"],
    keywords=["parlons", "français", "in english"],
    collection="preferences_memory",
    metadata_filters={"preference_type": "language"},
    limit=3,
    priority=10  # High priority
)
```

### Adding Custom Policies

```python
from agent_runtime import get_agent_runtime, RetrievalPolicy

runtime = get_agent_runtime()

# Add a custom policy
custom_policy = RetrievalPolicy(
    name="my_custom_policy",
    keywords=["custom", "special"],
    collection="candidate_memory",
    limit=5
)

runtime.policy_engine.add_policy(custom_policy)
```

---

## 🔍 Retrieval Engine

Handles all Qdrant operations:

```python
from agent_runtime import get_agent_runtime

runtime = get_agent_runtime()

# Retrieve from a specific collection
results = await runtime.retrieval_engine.retrieve(
    query="Data Scientist",
    collection_name="jobs_memory",
    metadata_filters={"status": "applied"},
    limit=5,
    user_id="user_123"
)

# Store a memory
memory_id = runtime.retrieval_engine.store_memory(
    collection_name="preferences_memory",
    payload={
        "user_id": "user_123",
        "preference_type": "language",
        "value": "French",
        "content": "User prefers French",
        "timestamp": "2026-05-22T10:00:00Z",
        "priority": 10
    }
)

# Batch retrieve from multiple collections
operations = [
    RetrievalOperation(
        collection="candidate_memory",
        query="Data Scientist",
        limit=5
    ),
    RetrievalOperation(
        collection="jobs_memory",
        query="Data Scientist",
        limit=10
    )
]
results = await runtime.retrieval_engine.batch_retrieve(operations)
```

---

## 🧩 Context Assembly

Transforms raw retrieval results into LLM-ready context:

```python
from agent_runtime import get_agent_runtime

runtime = get_agent_runtime()

# Assemble context from retrieval results
assembled = runtime.context_assembler.assemble(
    retrieval_results=results,
    template="default",  # or "compact", "detailed", "minimal"
    chronological=False,  # Sort by score (True = sort by timestamp)
    include_metadata=True
)

print(f"Total tokens: {assembled.total_tokens}")
print(f"Collections used: {assembled.collections_used}")
print(assembled.to_string())
```

### Templates

- **default**: `[Memory: {collection} | Source: {source} | Score: {score}]
  {content}`
- **compact**: `[{collection}] {content}`
- **detailed**: Full metadata with formatting
- **minimal**: Just the content

### Token Budget Management

```python
# Context assembler with 1000 token budget
assembler = ContextAssembler(
    token_budget=1000,
    max_memories=10,
    deduplication=True
)

# Chunk large contexts
chunks = assembler.chunk_context(context, max_tokens=500)
```

---

## ✨ Prompt Augmentation

Injects memory context into LLM prompts:

```python
from agent_runtime import get_agent_runtime

runtime = get_agent_runtime()

# Augment a simple user input
system_prompt, user_prompt = runtime.prompt_augmenter.augment(
    user_input="Génère mon CV",
    memory_context=assembled_context,
    intent="cv_generation",
    template="cv_generation"  # Use a specific template
)

print(f"System Prompt:\n{system_prompt}")
print(f"\nUser Prompt:\n{user_prompt}")
```

### Built-in Templates

- **default**: General-purpose with memory context
- **language_preference**: Language-adaptive responses
- **cv_generation**: CV-specific prompts
- **job_match**: Job matching prompts
- **ats_optimization**: ATS optimization prompts
- **web_scraping**: Scraping workflow prompts
- **conversation**: Multi-turn conversation
- **minimal**: Just the context

### Custom Templates

```python
from agent_runtime.prompt_augmenter import PromptTemplate

# Create a custom template
custom_template = PromptTemplate(
    name="my_template",
    system_prompt="You are a helpful assistant.\n\n{memory_context}",
    user_prompt="{user_input}"
)

runtime.prompt_augmenter.add_template(custom_template)
```

---

## 🤖 N8N Integration

Connects to your N8N workflow engine:

```python
from agent_runtime import get_agent_runtime

runtime = get_agent_runtime()

# List available workflows
workflows = await runtime.n8n_integrator.get_workflows()

# Find workflows by tag
scraping_workflows = await runtime.n8n_integrator.find_workflows_by_tag("scraper")

# Execute a workflow
execution = await runtime.n8n_integrator.execute_workflow_by_name(
    workflow_name="job-scraper",
    parameters={
        "url": "https://example.com/jobs/123",
        "fields": ["title", "description", "company"]
    },
    wait_for_completion=True,
    timeout=60
)

# Execute via webhook
webhook_result = await runtime.n8n_integrator.execute_webhook(
    webhook_path="job-scraper",
    parameters={"url": "https://example.com/jobs/123"}
)

# Create a new scraping workflow
workflow_id = await runtime.n8n_integrator.create_scraping_workflow(
    name="My Custom Scraper",
    url="https://example.com/jobs/123",
    extract_fields=["title", "description", "company", "location"],
    description="Auto-created by GOOSE"
)
```

---

## 📊 Complete Runtime Example

```python
import asyncio
from agent_runtime import AgentRuntime, RuntimeConfig

async def complete_example():
    # Initialize runtime
    runtime = AgentRuntime(
        config=RuntimeConfig(
            user_id="lucas",
            enable_memory=True,
            enable_audit=True,
            enable_n8n=True
        )
    )
    
    # Run the complete loop
    result = await runtime.run(
        user_input="Scrape cette annonce: https://example.com/jobs/123 et génère mon CV",
        template="default"
    )
    
    # Inspect results
    print("=== Runtime Result ===")
    print(f"Status: {result.status}")
    print(f"Intent: {result.intent}")
    print(f"Policies Applied: {result.policies_applied}")
    print(f"Memories Retrieved: {len(result.retrieved_memories)}")
    print(f"LLM Response Length: {len(result.llm_response) if result.llm_response else 0}")
    print(f"Memories Written: {len(result.memory_written)}")
    print(f"Workflow Executions: {len(result.workflow_executions)}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    
    # Get metrics
    metrics = runtime.get_metrics()
    print("\n=== Metrics ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

asyncio.run(complete_example())
```

---

## 📈 Metrics & Monitoring

The runtime tracks comprehensive metrics:

```python
runtime = get_agent_runtime()

# Get current metrics
metrics = runtime.get_metrics()
# {
#     'total_executions': 15,
#     'successful_executions': 14,
#     'failed_executions': 1,
#     'total_retrievals': 45,
#     'total_memory_writes': 30,
#     'total_tool_executions': 5,
#     'avg_execution_time': 2.34,
#     'last_execution_time': datetime
# }

# Reset metrics
runtime.reset_metrics()
```

---

## 🔧 Audit Logging

All executions are logged to PostgreSQL:

```sql
-- Table created automatically
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
);
```

Query audit logs:

```sql
-- Get recent executions
SELECT * FROM agent_runtime_audit 
ORDER BY timestamp DESC 
LIMIT 10;

-- Get executions for a specific user
SELECT * FROM agent_runtime_audit 
WHERE user_id = 'lucas'
ORDER BY timestamp DESC;

-- Get statistics
SELECT 
    intent,
    COUNT(*) as count,
    AVG(execution_time) as avg_time,
    SUM(memories_retrieved) as total_retrievals
FROM agent_runtime_audit 
GROUP BY intent;
```

---

## 🛡️ Error Handling

The runtime handles errors gracefully:

```python
result = await runtime.run("Some input that might fail")

if result.status == RuntimeStatus.FAILED:
    print(f"Error: {result.error}")
elif result.status == RuntimeStatus.TIMEOUT:
    print("Request timed out")
else:
    print(f"Success: {result.llm_response}")
```

---

## 🎓 Advanced Usage

### Custom Components

You can override any component:

```python
from agent_runtime import AgentRuntime
from agent_runtime.memory_policy import MemoryPolicyEngine

class CustomPolicyEngine(MemoryPolicyEngine):
    def extract_intent(self, user_input: str) -> str:
        # Your custom intent classification
        return "custom_intent"

runtime = AgentRuntime(
    config=RuntimeConfig(user_id="user_123"),
    policy_engine=CustomPolicyEngine()
)
```

### Middleware Integration

Integrate with FastAPI:

```python
from fastapi import FastAPI, Request
from agent_runtime import get_agent_runtime
import asyncio

app = FastAPI()
runtime = get_agent_runtime()

@app.post("/api/agent")
async def agent_endpoint(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    user_id = data.get("user_id", "default")
    
    result = await runtime.run(
        user_input=user_input,
        user_id=user_id
    )
    
    return result.to_dict()

@app.get("/api/agent/metrics")
async def get_metrics():
    return runtime.get_metrics()
```

### Streamlit Integration

```python
import streamlit as st
import asyncio
from agent_runtime import get_agent_runtime

runtime = get_agent_runtime()

st.title("GOOSE with Agent Runtime")

if user_input := st.chat_input("Talk to GOOSE..."):
    with st.spinner("Thinking..."):
        result = await runtime.run(user_input, user_id="streamlit_user")
    
    st.chat_message("assistant").write(result.llm_response)
```

---

## 📚 API Reference

### AgentRuntime

**Main class that orchestrates everything.**

#### Methods

- `run(user_input, user_id, session_id, ...)` → RuntimeResult
- `get_metrics()` → Dict[str, Any]
- `reset_metrics()`
- `clear_conversation()`
- `set_session_id(session_id)`

#### Configuration

```python
RuntimeConfig(
    user_id: str = "default"
    session_id: Optional[str] = None
    enable_memory: bool = True
    enable_audit: bool = True
    enable_n8n: bool = True
    debug: bool = False
    qdrant: QdrantConfig = QdrantConfig.from_env()
    ollama: OllamaConfig = OllamaConfig.from_env()
    postgres: PostgresConfig = PostgresConfig.from_env()
    n8n: N8NConfig = N8NConfig.from_env()
    memory: MemoryConfig = MemoryConfig()
)
```

### RuntimeResult

**Complete result of a runtime execution.**

#### Attributes

- `status`: RuntimeStatus (INITIALIZED, RUNNING, COMPLETED, FAILED, TIMEOUT)
- `input`: str (original user input)
- `intent`: str (extracted intent)
- `policies_applied`: List[str] (names of applied policies)
- `retrieved_memories`: List[Dict] (retrieved memory entries)
- `assembled_context`: AssembledContext (formatted context)
- `system_prompt`: str (generated system prompt)
- `user_prompt`: str (generated user prompt)
- `llm_response`: Optional[str] (LLM response)
- `tool_executions`: List[Dict] (executed tools)
- `memory_written`: List[Dict] (written memories)
- `workflow_executions`: List[Dict] (N8N executions)
- `audit_log`: Optional[Dict] (audit logging result)
- `error`: Optional[str] (error message)
- `execution_time`: float (seconds)
- `timestamp`: str (ISO timestamp)
- `session_id`: str (session identifier)
- `user_id`: str (user identifier)

#### Methods

- `to_dict()` → Dict[str, Any]
- `to_json(indent=2)` → str

---

## 🚀 What's Next

1. **Test the demos**: Run `python agent_runtime/examples/demo_basic.py`
2. **Integrate with Streamlit**: Connect to your existing UI
3. **Integrate with FastAPI**: Add as middleware to your API
4. **Add custom policies**: Extend the Memory Policy Engine
5. **Create workflows**: Set up N8N workflows for scraping
6. **Monitor performance**: Use the audit logging and metrics
7. **Tune parameters**: Adjust token budgets, confidence thresholds, etc.

---

## 📖 Glossary

| Term | Definition |
|------|------------|
| Agent Runtime | The orchestration layer that connects Goose to memory |
| Memory Policy | Rules that decide WHEN and WHAT to retrieve |
| Retrieval Engine | Component that executes Qdrant searches |
| Context Assembly | Formatting memories for LLM prompts |
| Prompt Augmentation | Injecting context into prompts |
| Memory Writeback | Storing new memories from interactions |
| Audit Logging | Logging all executions to PostgreSQL |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Submit a pull request

---

## 📄 License

MIT License - Feel free to use, modify, and distribute.

---

## 🙏 Acknowledgments

- Inspired by the "memory loop" concept in modern AI agents
- Built on top of your existing GOOSE infrastructure
- Designed to be modular, extensible, and production-ready

---

**GOOSE is now COGNITIVELY CONNECTED to its memory! 🎉**
