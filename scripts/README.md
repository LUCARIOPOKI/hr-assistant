# HR Assistant - Document Ingestion Script

## Overview

The `ingest_documents.py` script processes documents from the `kb/` folder and uploads them to Pinecone with MongoDB logging.

## Features

✅ **Document Loading**: Supports PDF, DOCX, TXT, MD files  
✅ **Intelligent Chunking**: Splits documents into optimal chunks (1000 chars, 200 overlap)  
✅ **Embeddings**: Generates embeddings using Azure OpenAI (configurable via `EMBEDDING_MODEL`)  
✅ **Pinecone Upload**: Stores vectors with metadata in Pinecone  
✅ **MongoDB Storage**: Saves chunks to `DATABASE_NAME.COLLECTION_NAME`  
✅ **Audit Trail**: Logs all operations to `LOG_DATABASE_NAME.LOG_COLLECTION_NAME`  

## Configuration

### Required Environment Variables

```bash
# Azure OpenAI (for embeddings)
HR_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
HR_AZURE_OPENAI_API_KEY=your-api-key
HR_AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
HR_EMBEDDING_MODEL=text-embedding-ada-002

# Pinecone
HR_PINECONE_API_KEY=your-pinecone-key
HR_PINECONE_INDEX_NAME=hr-assistant-index

# MongoDB (optional, for chunk storage and logging)
HR_MONGO_DB_CONNECTION_STRING=mongodb://localhost:27017/
HR_DATABASE_NAME=company_information_chunks
HR_COLLECTION_NAME=chunks
HR_LOG_DATABASE_NAME=audit_trail
HR_LOG_COLLECTION_NAME=logs
```

### Configuration Files

The script reads from `.env` file in the project root. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### 1. Add Documents to kb/ Folder

Place your HR policy documents in the `kb/` directory:

```
kb/
├── HR Policy Manual 2023 (8).pdf
├── Employee Handbook.docx
├── Benefits Guide.pdf
└── Code of Conduct.md
```

### 2. Activate Virtual Environment

```bash
# Windows
capestone_prj\Scripts\activate

# Linux/Mac
source capestone_prj/bin/activate
```

### 3. Install Dependencies

```bash
pip install pymongo  # Optional, for MongoDB features
```

### 4. Run Ingestion Script

```bash
python scripts/ingest_documents.py
```

## What Happens During Ingestion

### Step 1: Document Loading
```
Loading documents from kb/ directory...
Loaded 4 documents
```

### Step 2: Document Processing
For each document:
- Cleans text (removes extra whitespace, fixes encoding)
- Extracts metadata (title, document type, word count)
- Chunks text into 1000-character segments with 200-char overlap

```
Processing document 1/4: HR Policy Manual 2023 (8).pdf
Split into 45 chunks
```

### Step 3: Embedding Generation
Uses Azure OpenAI to generate embeddings:

```
Generating embeddings using Azure OpenAI...
Embedding model: text-embedding-ada-002
Generating embeddings for batch 1/1
Generated embeddings for 45 chunks
```

### Step 4: MongoDB Storage
Stores chunks in MongoDB (if configured):

```
Storing chunks in MongoDB: company_information_chunks.chunks
Stored 45 chunks in MongoDB
```

### Step 5: Pinecone Upload
Uploads vectors to Pinecone:

```
Uploading vectors to Pinecone...
Uploading batch 1/1 to Pinecone
Uploaded batch 1: 45 vectors
```

### Step 6: Summary
```
============================================================
Document Ingestion Complete!
============================================================
Documents processed: 4
Total chunks: 180
Embeddings generated: 180
Pinecone vectors: 180
MongoDB chunks: 180
Processing time: 45.23s
============================================================
```

## Output

### Pinecone Index
- **Namespace**: `hr_policies` (default)
- **Vectors**: One per chunk with embeddings
- **Metadata**: Contains document ID, chunk index, text, filename, etc.

### MongoDB Collections

#### Chunks Collection (`company_information_chunks.chunks`)
```json
{
  "chunk_id": "doc_a1b2c3d4e5f6_chunk_0",
  "document_id": "doc_a1b2c3d4e5f6",
  "chunk_index": 0,
  "total_chunks": 45,
  "text": "Employee Handbook 2023...",
  "metadata": {
    "filename": "HR Policy Manual 2023 (8).pdf",
    "document_type": "pdf",
    "title": "HR Policy Manual",
    "word_count": 1523
  },
  "has_embedding": true,
  "ingestion_timestamp": "2025-11-10T10:30:00Z",
  "created_at": "2025-11-10T10:30:00Z"
}
```

#### Logs Collection (`audit_trail.logs`)
```json
{
  "timestamp": "2025-11-10T10:30:00Z",
  "event_type": "ingestion",
  "level": "INFO",
  "message": "Starting document ingestion from: kb/",
  "metadata": {}
}
```

## Troubleshooting

### Error: "Azure OpenAI credentials not configured"

**Solution**: Set environment variables in `.env`:
```bash
HR_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
HR_AZURE_OPENAI_API_KEY=your-key
```

### Error: "Pinecone API key not configured"

**Solution**: Add Pinecone credentials:
```bash
HR_PINECONE_API_KEY=your-pinecone-key
```

### Warning: "MongoDB not connected"

**Effect**: Chunks won't be stored in MongoDB, only in Pinecone  
**Solution**: Install pymongo and configure connection string:
```bash
pip install pymongo
# Add to .env:
HR_MONGO_DB_CONNECTION_STRING=mongodb://localhost:27017/
```

### No documents found

**Solution**: Check that documents exist in `kb/` directory:
```bash
ls kb/  # Should show your PDF/DOCX files
```

## Advanced Usage

### Custom Chunk Size

Edit the script to change chunking parameters:
```python
await ingest_documents(
    str(kb_dir),
    chunk_size=1500,      # Larger chunks
    chunk_overlap=300     # More overlap
)
```

### Different Namespace

Use a different Pinecone namespace:
```python
await ingest_documents(str(kb_dir), namespace="company_policies")
```

### Re-ingesting Documents

To re-ingest after updates:
1. Delete vectors from Pinecone namespace
2. Clear MongoDB chunks collection (optional)
3. Run script again

## Performance

- **Speed**: ~2-5 seconds per document (depends on size)
- **Batch Size**: Processes embeddings in batches of 50 chunks
- **Pinecone Upload**: Batches of 100 vectors at a time

## Next Steps

After ingestion:
1. Start the FastAPI server: `python src/main.py`
2. Test queries at: `http://localhost:8000/docs`
3. Query your documents via the `/query` endpoint

## Support

For issues, check:
- Logs in console output
- MongoDB `audit_trail.logs` collection for detailed event history
- Pinecone dashboard to verify vector uploads
