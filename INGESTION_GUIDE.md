# Quick Start: Upload KB Files to Pinecone

## Step 1: Setup Environment

1. **Copy environment template:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   # Required: Azure OpenAI
   HR_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   HR_AZURE_OPENAI_API_KEY=your-key-here
   HR_EMBEDDING_MODEL=text-embedding-ada-002

   # Required: Pinecone
   HR_PINECONE_API_KEY=your-pinecone-key
   HR_PINECONE_INDEX_NAME=hr-assistant-index

   # Optional: MongoDB (for chunk storage and audit logs)
   HR_MONGO_DB_CONNECTION_STRING=mongodb://localhost:27017/
   HR_DATABASE_NAME=company_information_chunks
   HR_COLLECTION_NAME=chunks
   HR_LOG_DATABASE_NAME=audit_trail
   HR_LOG_COLLECTION_NAME=logs
   ```

## Step 2: Install Dependencies

```bash
# Activate virtual environment
capestone_prj\Scripts\activate

# Install MongoDB support (optional)
pip install pymongo
```

## Step 3: Run Ingestion

```bash
python scripts/ingest_documents.py
```

## What It Does

✅ **Chunks** documents from `kb/` folder  
✅ **Embeds** using `EMBEDDING_MODEL` from env (Azure OpenAI)  
✅ **Uploads** vectors to Pinecone  
✅ **Stores** chunks in MongoDB `DATABASE_NAME.COLLECTION_NAME`  
✅ **Logs** operations to MongoDB `LOG_DATABASE_NAME.LOG_COLLECTION_NAME`  

## Output

```
Loading documents from kb/ directory...
Loaded 1 documents

Processing document 1/1: HR Policy Manual 2023 (8).pdf
Split into 45 chunks

Generating embeddings using Azure OpenAI...
Embedding model: text-embedding-ada-002
Generated embeddings for 45 chunks

Storing chunks in MongoDB: company_information_chunks.chunks
Stored 45 chunks in MongoDB

Uploading vectors to Pinecone...
Uploaded batch 1: 45 vectors

============================================================
Document Ingestion Complete!
============================================================
Documents processed: 1
Total chunks: 45
Embeddings generated: 45
Pinecone vectors: 45
MongoDB chunks: 45
Processing time: 12.34s
============================================================
```

## Verify Upload

### Pinecone Dashboard
- Go to your Pinecone console
- Check index: `hr-assistant-index`
- Namespace: `hr_policies`
- Should see vectors equal to chunk count

### MongoDB (if configured)
```javascript
// Connect to MongoDB
use company_information_chunks
db.chunks.count()  // Should match chunk count

use audit_trail
db.logs.find().sort({timestamp: -1}).limit(10)  // View recent logs
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Azure OpenAI credentials not configured" | Set `HR_AZURE_OPENAI_ENDPOINT` and `HR_AZURE_OPENAI_API_KEY` in `.env` |
| "Pinecone API key not configured" | Set `HR_PINECONE_API_KEY` in `.env` |
| "No documents found" | Add PDF/DOCX files to `kb/` folder |
| "MongoDB not connected" | Install `pymongo` or ignore (MongoDB is optional) |

## Next Steps

After successful ingestion:

1. **Start API server:**
   ```bash
   python src/main.py
   ```

2. **Test queries:**
   - Open: http://localhost:8000/docs
   - Try POST `/query` endpoint with your questions

3. **Query example:**
   ```json
   {
     "query": "What is the vacation policy?",
     "conversation_id": "test-123"
   }
   ```
