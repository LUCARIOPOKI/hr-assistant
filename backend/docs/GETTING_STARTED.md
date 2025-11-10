# Getting Started with HR Assistant Bot

## Overview

You now have a fully functional HR assistant bot with:
- ✅ RAG-powered document retrieval
- ✅ Conversation memory
- ✅ HR policy Q&A
- ✅ Document summarization
- ✅ Employee services
- ✅ Company information

## Current Status

The system has been validated and is ready for:
1. Azure OpenAI configuration
2. Pinecone integration
3. Document ingestion
4. Production deployment

## Configuration Required

### 1. Azure OpenAI Setup

Get your credentials from Azure Portal:
1. Create an Azure OpenAI resource
2. Deploy these models:
   - `gpt-4` (or `gpt-35-turbo`) for chat
   - `text-embedding-ada-002` for embeddings
3. Note your endpoint and API key

### 2. Pinecone Setup

Get your credentials from Pinecone dashboard:
1. Create a free account at pinecone.io
2. Create an index named `hr-assistant-index`
   - Dimensions: 1536
   - Metric: cosine
3. Note your API key

### 3. Create .env File

```bash
# Copy the example
cp .env.example .env

# Edit with your credentials
notepad .env  # or use your preferred editor
```

Add:
```
HR_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
HR_AZURE_OPENAI_API_KEY=your-key-here
HR_AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
HR_AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

HR_PINECONE_API_KEY=your-pinecone-key
HR_PINECONE_INDEX_NAME=hr-assistant-index
```

## Running the System

### Step 1: Ingest Documents

The `kb/` folder contains your HR Policy Manual. Ingest it:

```powershell
# Activate environment
.\capestone_prj\Scripts\Activate.ps1

# Run ingestion
python scripts/ingest_documents.py
```

Expected output:
```
Loading documents...
Loaded 1 documents
Processing: HR Policy Manual 2023 (8).pdf
Split into X chunks
Uploading to Pinecone...
✓ Document ingestion complete!
```

### Step 2: Start the Server

```powershell
python src/main.py
```

You should see:
```
INFO: Starting Company Information Assistant
INFO: Database initialized successfully
INFO: Pinecone initialized successfully
INFO: Semantic Kernel initialized successfully
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test the API

Visit http://localhost:8000/docs to see interactive API documentation.

#### Test Query Endpoint

```powershell
# Using curl
curl -X POST "http://localhost:8000/api/v1/query" `
  -H "Content-Type: application/json" `
  -d '{
    "query": "What is the leave policy?",
    "user_id": "test_user",
    "top_k": 3
  }'
```

#### Test Health Endpoint

```powershell
curl http://localhost:8000/api/v1/health
```

## Usage Examples

### Python Client

```python
import httpx

# Initialize client
client = httpx.Client(base_url="http://localhost:8000")

# Ask about leave policy
response = client.post("/api/v1/query", json={
    "query": "How many vacation days do employees get?",
    "user_id": "emp123"
})
print(response.json()["answer"])

# Check leave balance
response = client.get("/api/v1/hr/leave-balance/EMP001")
print(response.json())

# Get job openings
response = client.get("/api/v1/recruitment/openings?department=engineering")
print(response.json())

# Get company info
response = client.get("/api/v1/company/info?info_type=values")
print(response.json())
```

### JavaScript/TypeScript

```javascript
// Using fetch
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What are the benefits for new employees?',
    user_id: 'user123',
    top_k: 5
  })
});

const data = await response.json();
console.log(data.answer);
```

## Available Endpoints

### HR Queries
- `POST /api/v1/query` - RAG-powered Q&A
- `GET /api/v1/hr/policy?question={question}` - Direct policy questions
- `GET /api/v1/hr/leave-balance/{employee_id}` - Leave balance

### Company Information
- `GET /api/v1/company/info?info_type=overview` - Company overview
- `GET /api/v1/company/info?info_type=values` - Company values
- `GET /api/v1/company/info?info_type=history` - Company history
- `GET /api/v1/company/info?info_type=contact` - Contact information

### Recruitment
- `GET /api/v1/recruitment/openings?department={dept}` - Job openings

### Utilities
- `GET /api/v1/health` - Health check
- `POST /api/v1/summarize` - Document summarization

## Development Workflow

### Adding Documents

1. Place new documents in `kb/` folder (PDF, DOCX, TXT, MD)
2. Run ingestion script: `python scripts/ingest_documents.py`
3. Documents are chunked, embedded, and stored in Pinecone

### Testing Changes

```powershell
# Run validation
python scripts/validate_setup.py

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=src tests/
```

### Monitoring

Logs are saved to `logs/app_YYYY-MM-DD.log`

```powershell
# View logs
Get-Content logs/app_*.log -Tail 50
```

## Conversation Features

### Session Management

Each conversation has a session ID that maintains context:

```python
# First question
response1 = client.post("/api/v1/query", json={
    "query": "What is the leave policy?",
    "user_id": "emp123",
    "session_id": "session_abc"
})

# Follow-up question (same session)
response2 = client.post("/api/v1/query", json={
    "query": "How do I apply for it?",  # "it" refers to leave
    "user_id": "emp123",
    "session_id": "session_abc"  # Same session
})
```

The assistant maintains context across questions in the same session.

## Performance Tips

### Optimize Retrieval
- Adjust `top_k` parameter (3-10 recommended)
- Higher values provide more context but slower responses

### Conversation History
- Sessions are stored in memory by default
- Clear old sessions periodically
- Implement Redis for production persistence

### Caching
- Consider caching frequent queries
- Use Redis for distributed caching

## Troubleshooting

### "Chat service not configured"
→ Add Azure OpenAI credentials to `.env`

### "No relevant documents found"
→ Run ingestion script to load documents

### "Pinecone index not available"
→ Check Pinecone API key and index name

### Import errors
→ Activate venv: `.\capestone_prj\Scripts\Activate.ps1`

## Production Checklist

Before deploying to production:

- [ ] Set `HR_DEBUG=false`
- [ ] Use secrets manager (Azure Key Vault)
- [ ] Configure proper CORS origins
- [ ] Add authentication middleware
- [ ] Enable rate limiting
- [ ] Set up monitoring (Application Insights)
- [ ] Configure log aggregation
- [ ] Add database for conversation persistence
- [ ] Set up backup for Pinecone
- [ ] Document API for end users

## Support

### Files to Reference
- `README.md` - Full documentation
- `docs/IMPLEMENTATION_SUMMARY.md` - Architecture details
- `.env.example` - Configuration template
- `src/config/prompts.py` - Customize system behavior

### Quick Commands

```powershell
# Validate setup
python scripts/validate_setup.py

# Ingest documents
python scripts/ingest_documents.py

# Run app
python src/main.py

# Run tests
pytest tests/ -v

# Check logs
Get-Content logs/app_*.log -Tail 50
```

## Next Steps

1. **Configure credentials** in `.env`
2. **Ingest HR documents** with ingestion script
3. **Start the server** and test endpoints
4. **Integrate frontend** or chat interface
5. **Deploy to production** (Azure App Service, Docker, etc.)

Your HR assistant is ready to help employees with policies, benefits, and company information! 🎉
