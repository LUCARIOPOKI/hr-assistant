# HR Assistant

A RAG-based HR assistant chatbot built with Semantic Kernel, FastAPI, and Pinecone for semantic search over company policies, benefits, and HR documentation.

## Features

- **HR Policy Q&A**: Answer questions about company policies, benefits, leave, remote work
- **Employee Services**: Check leave balances, payroll info, and employee self-service
- **Recruitment**: Job openings, application status tracking
- **Document Retrieval**: Semantic search over indexed HR documents using Pinecone
- **Summarization**: Generate summaries and extract key points from documents
- **Conversation Memory**: Track multi-turn conversations with context

## Architecture

- **FastAPI**: RESTful API backend
- **Semantic Kernel**: AI orchestration with plugins for HR functions
- **Azure OpenAI**: Chat completion and embeddings (gpt-4, text-embedding-ada-002)
- **Pinecone**: Vector database for semantic document search
- **Loguru**: Structured logging

## Setup

### Prerequisites

- Python 3.12+
- Azure OpenAI API access
- Pinecone account (optional, for document retrieval)

### Installation

1. **Clone and activate environment**:
```bash
cd hr-assistant
.\capestone_prj\Scripts\Activate.ps1  # Windows
# or: source capestone_prj/bin/activate  # Linux/Mac
```

2. **Install dependencies** (if not already installed):
```bash
pip install -r src/requirements.txt
```

3. **Configure environment variables**:

Create `.env` file in project root:
```bash
# Azure OpenAI
HR_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
HR_AZURE_OPENAI_API_KEY=your-api-key
HR_AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
HR_AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
HR_AZURE_OPENAI_API_VERSION=2024-02-01

# Pinecone (optional)
HR_PINECONE_API_KEY=your-pinecone-key
HR_PINECONE_ENVIRONMENT=us-east-1
HR_PINECONE_INDEX_NAME=hr-assistant-index

# App
HR_DEBUG=true
HR_LOG_LEVEL=INFO
```

### Run the Application

```bash
python -m src.main
```

Or with uvicorn directly:
```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Query HR Assistant
```bash
POST /api/v1/query
{
  "query": "What is our remote work policy?",
  "user_id": "employee123",
  "top_k": 5
}
```

### Summarize Documents
```bash
POST /api/v1/summarize
{
  "company_id": 1,
  "summary_type": "executive",
  "audience": "leadership"
}
```

## Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_health.py -v
```

## Project Structure

```
hr-assistant/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── api/
│   │   ├── routes.py          # API endpoint handlers
│   │   └── schemas.py         # Pydantic request/response models
│   ├── config/
│   │   └── settings.py        # Application configuration
│   ├── core/
│   │   └── semantic_kernel_setup.py  # SK initialization & plugin loading
│   ├── database/
│   │   ├── base.py            # Database initialization
│   │   └── pinecone_client.py # Pinecone vector store client
│   ├── plugins/
│   │   ├── hr_policy_plugin.py      # HR policy Q&A functions
│   │   └── retrieval_plugin.py      # Document search & summarization
│   └── ...
├── tests/
│   └── test_health.py
├── capestone_prj/             # Python virtual environment
├── data/                      # Training data / documents
├── kb/                        # Knowledge base documents
└── README.md
```

## Usage Examples

### Ask about leave policy
```python
import httpx

response = httpx.post("http://localhost:8000/api/v1/query", json={
    "query": "How many vacation days do I get?",
    "user_id": "emp001"
})
print(response.json()["answer"])
```

### Check leave balance
```python
response = httpx.post("http://localhost:8000/api/v1/query", json={
    "query": "Check my leave balance for employee emp001"
})
print(response.json()["answer"])
```

### Search company documents
```python
response = httpx.post("http://localhost:8000/api/v1/query", json={
    "query": "What are the benefits for full-time employees?",
    "top_k": 3
})
print(response.json()["answer"])
```

## Plugin Architecture

The HR assistant uses Semantic Kernel plugins:

1. **HRPolicyPlugin**: Answers policy questions (leave, benefits, remote work)
2. **EmployeeServicesPlugin**: Self-service functions (leave balance, payroll)
3. **RecruitmentPlugin**: Job openings and application tracking
4. **RetrievalPlugin**: Semantic document search via Pinecone
5. **SummarizationPlugin**: Document summarization and key point extraction

Plugins are automatically loaded on application startup and available through the chat interface.

## Development

### Adding New Plugins

1. Create plugin class in `src/plugins/`
2. Decorate methods with `@kernel_function`
3. Import in `src/plugins/__init__.py`
4. Register in `semantic_kernel_setup.py`

### Indexing Documents

Use the Pinecone setup script:
```bash
python scripts/setup_pinecone.py --upload-docs data/hr_policies/
```

## Troubleshooting

**Azure OpenAI not configured**: App runs in limited mode without LLM. Set environment variables.

**Pinecone errors**: Document retrieval will be disabled. Check API key and index name.

**Import errors**: Ensure virtual environment is activated and dependencies installed.

## License

MIT

## Support

For issues or questions, contact the HR IT team or open an issue on the repository.
