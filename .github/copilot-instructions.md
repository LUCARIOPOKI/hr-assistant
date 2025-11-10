---
applyTo: "**"
---

Each and every time there are any changes, new additions, or updates, you need to provide a plan and approach after that I give confirmation.

# HR Assistant - AI Coding Agent Instructions

## Project Overview

RAG-based HR assistant using **Semantic Kernel** for AI orchestration, **Azure OpenAI** for LLM/embeddings, **Pinecone** for vector search, and **FastAPI** for API layer. The system answers HR policy questions, retrieves documents, and maintains conversation context.

## Architecture & Core Components

### Layered Architecture

```
API Layer (FastAPI routes)
  ↓
Semantic Kernel + Plugins (orchestration)
  ↓
Services Layer (LLM, Embeddings, Vector Store, Memory)
  ↓
Database Layer (Pinecone, MongoDB optional)
```

### Key Entry Points

- **`src/main.py`**: FastAPI app with lifespan events for startup/shutdown. Initializes database → Pinecone → Semantic Kernel in sequence.
- **`src/core/semantic_kernel_setup.py`**: `SemanticKernelManager` singleton that loads Azure OpenAI services and auto-registers plugins from `src/plugins/__init__.py`.
- **`src/api/routes.py`**: All endpoints live here. Query endpoint implements RAG pattern: retrieve documents → get conversation history → build prompt → generate response.

### Plugin Architecture Pattern

Plugins are **Semantic Kernel functions** decorated with `@kernel_function`. Each plugin class is imported in `src/plugins/__init__.py` and auto-loaded by `SemanticKernelManager._load_hr_plugins()`.

**Plugin structure**:

- `retrieval_plugin/`: Single plugin file for document search and context retrieval
- `summarization_plugin/`: In same file as `RetrievalPlugin` (see `retrieval_plugin.py`)
- `company_plugin/`: Directory-based plugin with `__init__.py`
- `hr_policy_plugin.py`: Single file with 3 plugin classes (HRPolicyPlugin, EmployeeServicesPlugin, RecruitmentPlugin)

**Pattern**: Simple plugins use single `.py` file; complex plugins use directory with `__init__.py`.

### RAG Pipeline (Critical Flow)

Located in `src/api/routes.py::query()`:

1. Create/get session via `memory_service`
2. Call `retrieval_plugin.retrieve_and_answer()` to query Pinecone
3. Get formatted conversation history from `memory_service`
4. Build prompt using `CONVERSATION_CONTEXT_TEMPLATE` from `src/config/prompts.py`
5. Generate response via `llm_service.generate_response()`
6. Store assistant message in memory

**Critical**: Context template in `prompts.py` must include `{history}`, `{question}`, and `{context}` placeholders.

## Configuration & Environment

### Settings Pattern

Use **Pydantic Settings** (`src/config/settings.py`) with:

- `@lru_cache()` decorator on `get_settings()` for singleton
- `env_prefix="HR_"` - all env vars prefixed with `HR_`
- Multiple `.env` file locations: `(".env", "src/.env")`
- Optional fields use `str | None` type hints

### Configuration Workflow

1. Copy `.env.example` to `.env` (not committed)
2. Set `HR_AZURE_OPENAI_*` and `HR_PINECONE_*` variables
3. Optional: Set `HR_MONGO_DB_CONNECTION_STRING` for MongoDB

**Graceful degradation**: Services check if API keys exist; if not, log warning and return limited functionality (see `pinecone_client._ensure_client()`, `semantic_kernel_setup.py` warnings).

## Services Pattern

### Global Singleton Services

All services in `src/services/` follow this pattern:

```python
class SomeService:
    def __init__(self):
        self._client = None

    async def initialize(self):
        if self._client is None:
            # lazy init

# Global instance at module level
some_service = SomeService()
```

Import services directly: `from src.services.llm_service import llm_service` (lowercase singleton instance).

### Memory Service (In-Memory)

`memory_service` stores conversations in dict: `{session_id: [messages]}`. **Not persistent** - uses in-memory storage. For production, replace with Redis/PostgreSQL.

Methods:

- `create_session(session_id, user_id)`
- `add_message(session_id, role, content)` - role is "user" or "assistant"
- `get_formatted_history(session_id, limit)` - returns string formatted for prompts

## Document Ingestion Pipeline

### Run Pipeline

```powershell
python scripts/ingest_documents.py
```

Places documents from `kb/` directory → chunks → embeddings → Pinecone + MongoDB.

### Pipeline Architecture

```
DocumentLoader → TextCleaner → TextSplitter → MetadataExtractor → EmbeddingService → Pinecone/MongoDB
```

**Key pattern**: `ingest_documents.py` creates `IngestionLogger` wrapper that logs to both console (loguru) and MongoDB audit trail (`audit_trail.logs` collection).

### Chunking Strategy

`TextSplitter` (in `src/data/ingestion/text_splitter.py`):

- Default: 1000 chars with 200 overlap
- Splits on semantic boundaries: `\n\n\n` → `\n\n` → `\n` → sentences → words
- Large chunks recursively split by words if needed

### MongoDB Integration (Optional)

If `HR_MONGO_DB_CONNECTION_STRING` set:

- Chunks stored in `{DATABASE_NAME}.{COLLECTION_NAME}`
- Audit logs in `{LOG_DATABASE_NAME}.{LOG_COLLECTION_NAME}`
- Documents include `document_id`, `chunk_index`, `text`, `metadata`, `ingestion_timestamp`

**Pattern**: MongoDB client checks connection before operations; silently skips if unavailable.

## Data Flow Patterns

### Query Flow (Detailed)

1. **Client** → POST `/api/v1/query` with `{query, user_id, session_id?, top_k?}`
2. **routes.py** → Initialize session → add user message to memory
3. **retrieval_plugin** → Embeds query → searches Pinecone namespace "hr_policies" → returns formatted context
4. **memory_service** → Retrieves last 5 messages
5. **prompts.py** → Template combines history + context + question
6. **llm_service** → Calls Azure OpenAI with full prompt
7. **routes.py** → Extracts sources from Pinecone results → returns response with sources, session_id

### Vector Storage Pattern

Pinecone vectors stored with:

- **id**: `{document_id}_chunk_{index}` (e.g., `doc_abc123_chunk_0`)
- **namespace**: `"hr_policies"` (default for all HR documents)
- **metadata**: `{document_id, chunk_index, total_chunks, text, filename, title, document_type}`

**Critical**: Metadata includes `text` field for retrieval display - don't remove.

## Development Workflows

### Running the Application

```powershell
# Activate environment
.\capestone_prj\Scripts\Activate.ps1

# Run directly
python src/main.py

# Or with uvicorn (hot reload)
uvicorn src.main:app --reload --port 8000
```

### Testing Workflow

```powershell
# Validate setup (no external dependencies needed)
python scripts/validate_setup.py

# Run all tests
pytest tests/ -v

# Specific test
pytest tests/test_health.py -v
```

### Adding New Plugin

1. Create plugin class in `src/plugins/your_plugin.py` or `src/plugins/your_plugin/`
2. Decorate methods with `@kernel_function(name="func_name", description="...")`
3. Import in `src/plugins/__init__.py`
4. Add to `SemanticKernelManager._load_hr_plugins()` in `semantic_kernel_setup.py`
5. Optional: Add API route in `routes.py` to expose functionality

### Adding New API Endpoint

Pattern in `routes.py`:

```python
@router.post("/endpoint", response_model=ResponseSchema)
async def endpoint_name(req: RequestSchema):
    try:
        # Call plugin/service
        result = await plugin_instance.method(...)
        return ResponseSchema(...)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

All endpoints follow: try/except with logger → HTTPException on error → return Pydantic response model.

## Project-Specific Conventions

### Naming Conventions

- **Services**: `snake_case_service.py` with singleton `snake_case_service` instance
- **Plugins**: `PluginNamePlugin` class, file is `plugin_name_plugin.py`
- **Models**: `CamelCase` in `src/models/`
- **API schemas**: `RequestName` and `ResponseName` in `schemas.py`
- **Environment variables**: All prefixed `HR_` (e.g., `HR_PINECONE_API_KEY`)

### Import Patterns

Use relative imports within `src/`:

```python
from ..services.llm_service import llm_service
from ..config.settings import get_settings
from ..plugins import HRPolicyPlugin
```

Scripts use absolute path manipulation:

```python
sys.path.append(str(Path(__file__).parent.parent))
from src.config.settings import get_settings
```

### Logging Pattern

Use **loguru** everywhere:

```python
from loguru import logger

logger.info("Message")
logger.warning("Warning")
logger.error(f"Error: {e}")
logger.success("Success")
```

Logs written to:

- Console (with colors/formatting)
- File: `logs/app_{YYYY-MM-DD}.log` (rotated daily, 30-day retention)

### Error Handling Convention

Services return empty/default values on error (graceful degradation):

- `vector_store_service.search()` → returns `[]` on error
- `pinecone_client.get_index()` → returns `None` if unavailable
- Plugins return error message strings (not exceptions)

API layer converts exceptions to `HTTPException` with 500 status.

## Critical Implementation Details

### Async Everywhere

All plugin methods, service methods, and API endpoints are `async`. Even if not awaiting, maintain pattern for consistency (Semantic Kernel expects async).

### Semantic Kernel Version

Using `semantic-kernel==1.3.0` - syntax differs from 0.x versions. Current pattern:

```python
kernel.add_service(service_instance)
kernel.add_plugin(plugin_instance, "plugin_name")
```

Not: `kernel.import_semantic_skill_from_directory()` (deprecated).

### Pinecone Client Pattern

Pinecone v3+ uses `Pinecone(api_key=...)` → `.Index(name)`. Check if `ServerlessSpec` available for index creation (see `pinecone_client.py`).

### Prompt Engineering

System prompts in `src/config/prompts.py` emphasize:

1. Base answers on retrieved documents
2. Admit uncertainty if information missing
3. Professional, empathetic tone for HR context

Templates use f-string style: `{variable}` placeholders.

## Common Tasks

### Change Embedding Model

Update `HR_EMBEDDING_MODEL` in `.env` (default: `text-embedding-ada-002`). Must re-run `ingest_documents.py` if dimension changes.

### Change Chunk Size

Modify `chunk_size` and `chunk_overlap` parameters in `ingest_documents.py` call to `TextSplitter()`.

### Add New Document Source

1. Add loader method to `DocumentLoader` class
2. Update `load_document()` to recognize new extension
3. Test with `scripts/ingest_documents.py`

### Switch to OpenAI (non-Azure)

Services use `Azure*` classes. To switch, modify `semantic_kernel_setup.py` to use `OpenAIChatCompletion` and `OpenAITextEmbedding` instead.

## Testing Approach

### Test Files

- `tests/test_health.py` - Simple health endpoint test
- `tests/test_api.py` - API integration tests
- `scripts/validate_setup.py` - Pre-deployment validation without external dependencies

### Running Without Services

`validate_setup.py` tests plugins directly without Azure OpenAI/Pinecone - useful for CI or credential-free testing.

## Known Limitations & TODOs

- **Memory**: In-memory only; not persistent across restarts
- **Authentication**: No auth layer; add OAuth2/JWT for production
- **Rate Limiting**: Not implemented; consider adding for production
- **Multi-tenancy**: Single company; DB schema doesn't support multiple companies yet
- **Pinecone Index Creation**: Script uses hardcoded "us-east-1" region in ServerlessSpec

## Quick Reference

### Key Files to Read First

1. `readme.md` - Full setup instructions
2. `src/main.py` - Application lifecycle
3. `src/api/routes.py` - RAG query endpoint
4. `src/core/semantic_kernel_setup.py` - Plugin loading
5. `src/config/settings.py` - Configuration model

### Critical Environment Variables

- `HR_AZURE_OPENAI_ENDPOINT`, `HR_AZURE_OPENAI_API_KEY` - Required for LLM
- `HR_AZURE_OPENAI_DEPLOYMENT_NAME` - Chat model (e.g., "gpt-4")
- `HR_AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - Embedding model
- `HR_PINECONE_API_KEY`, `HR_PINECONE_INDEX_NAME` - Required for retrieval
- `HR_MONGO_DB_CONNECTION_STRING` - Optional for chunk storage

### Common Commands

```powershell
# Setup
.\capestone_prj\Scripts\Activate.ps1
pip install -r src/requirements.txt

# Ingest documents
python scripts/ingest_documents.py

# Run app
python src/main.py

# Test
pytest tests/ -v
python scripts/validate_setup.py

# Logs
Get-Content logs/app_*.log -Tail 50
```
