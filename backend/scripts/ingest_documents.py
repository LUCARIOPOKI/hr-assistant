"""
Enhanced document ingestion script with MongoDB logging and storage.

This script:
1. Loads documents from kb/ directory
2. Chunks documents intelligently
3. Generates embeddings using Azure OpenAI (EMBEDDING_MODEL from env)
4. Uploads to Pinecone vector store
5. Stores chunks in MongoDB (DATABASE_NAME.COLLECTION_NAME)
6. Logs all operations to MongoDB audit trail (LOG_DATABASE_NAME.LOG_COLLECTION_NAME)
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger
import uuid
from typing import List, Dict, Any
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.ingestion.document_loader import DocumentLoader
from src.data.ingestion.text_splitter import TextSplitter
from src.data.ingestion.metadata_extractor import MetadataExtractor
from src.data.preprocessing.cleaner import TextCleaner
from src.services.embedding_service import embedding_service
from src.database.pinecone_client import pinecone_client
from src.database.mongodb_client import mongodb_client
from src.config.settings import get_settings

settings = get_settings()


class IngestionLogger:
    """Custom logger that writes to both console and MongoDB."""

    def __init__(self, mongodb_client):
        self.mongodb = mongodb_client

    def info(self, message: str, **kwargs):
        logger.info(message)
        self.mongodb.log_event('ingestion', message, 'INFO', kwargs)

    def warning(self, message: str, **kwargs):
        logger.warning(message)
        self.mongodb.log_event('ingestion', message, 'WARNING', kwargs)

    def error(self, message: str, **kwargs):
        logger.error(message)
        self.mongodb.log_event('ingestion', message, 'ERROR', kwargs)

    def success(self, message: str, **kwargs):
        logger.success(message)
        self.mongodb.log_event('ingestion', message, 'SUCCESS', kwargs)


async def generate_embeddings_batch(
    chunks: List[Dict[str, Any]],
    batch_size: int = 50
) -> List[Dict[str, Any]]:
    """
    Generate embeddings for chunks in batches using EMBEDDING_MODEL from env.

    Args:
        chunks: List of chunk dictionaries
        batch_size: Number of chunks to process at once

    Returns:
        Chunks with embeddings added
    """
    await embedding_service.initialize()
    
    chunks_with_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [chunk['text'] for chunk in batch]
        
        logger.info(f"Generating embeddings for batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
        
        try:
            embeddings = await embedding_service.generate_embeddings_batch(texts)
            
            for chunk, embedding in zip(batch, embeddings):
                chunk['embedding'] = embedding
                chunks_with_embeddings.append(chunk)
                
        except Exception as e:
            logger.error(f"Error generating embeddings for batch: {e}")
            # Add chunks without embeddings to preserve data
            chunks_with_embeddings.extend(batch)
    
    return chunks_with_embeddings


async def ingest_documents(
    directory_path: str,
    namespace: str = "hr_policies",
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """
    Ingest documents from a directory into Pinecone and MongoDB.

    Args:
        directory_path: Path to directory containing documents
        namespace: Pinecone namespace to use
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
    """
    # Initialize MongoDB
    mongodb_client.connect()
    db_logger = IngestionLogger(mongodb_client)
    
    ingestion_start = datetime.utcnow()
    db_logger.info(f"Starting document ingestion from: {directory_path}")
    
    # Initialize Pinecone
    db_logger.info("Initializing Pinecone vector store...")
    pinecone_client.initialize_index()
    
    # Load documents
    db_logger.info("Loading documents from kb/ directory...")
    loader = DocumentLoader()
    
    try:
        documents = loader.load_directory(directory_path, recursive=True)
        db_logger.info(f"Loaded {len(documents)} documents", document_count=len(documents))
    except Exception as e:
        db_logger.error(f"Error loading documents: {e}")
        return
    
    if not documents:
        db_logger.warning("No documents found to ingest")
        return
    
    # Process each document
    cleaner = TextCleaner()
    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    metadata_extractor = MetadataExtractor()
    
    all_chunks = []
    document_stats = []
    
    for doc_idx, doc in enumerate(documents, 1):
        doc_start = datetime.utcnow()
        filename = doc['metadata']['filename']
        db_logger.info(f"Processing document {doc_idx}/{len(documents)}: {filename}")
        
        try:
            # Clean text
            cleaned_text = cleaner.clean(
                doc['content'],
                remove_urls=True,
                remove_emails=False,
                fix_encoding=True
            )
            
            # Extract metadata
            extracted_metadata = metadata_extractor.extract_all(
                cleaned_text,
                filename=filename
            )
            
            # Merge metadata
            combined_metadata = {**doc['metadata'], **extracted_metadata}
            
            # Generate document ID
            document_id = f"doc_{uuid.uuid4().hex[:12]}"
            combined_metadata['document_id'] = document_id
            
            # Split into chunks
            chunks = splitter.split_text(cleaned_text)
            db_logger.info(f"Split into {len(chunks)} chunks", 
                          filename=filename, 
                          chunk_count=len(chunks))
            
            # Prepare chunks for processing
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                all_chunks.append({
                    'id': chunk_id,
                    'document_id': document_id,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'text': chunk_text,
                    'metadata': {
                        **combined_metadata,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'text': chunk_text,  # Store text in metadata for retrieval
                    }
                })
            
            doc_duration = (datetime.utcnow() - doc_start).total_seconds()
            document_stats.append({
                'document_id': document_id,
                'filename': filename,
                'chunk_count': len(chunks),
                'processing_time': doc_duration
            })
            
        except Exception as e:
            db_logger.error(f"Error processing document {filename}: {e}", filename=filename)
            continue
    
    db_logger.info(f"Total chunks prepared: {len(all_chunks)}", total_chunks=len(all_chunks))
    
    # Generate embeddings using EMBEDDING_MODEL from env
    db_logger.info("Generating embeddings using Azure OpenAI...")
    db_logger.info(f"Embedding model: {settings.embedding_model}")
    
    try:
        chunks_with_embeddings = await generate_embeddings_batch(all_chunks)
        db_logger.success(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")
    except Exception as e:
        db_logger.error(f"Error generating embeddings: {e}")
        return
    
    # Store in MongoDB (DATABASE_NAME.COLLECTION_NAME)
    if mongodb_client._chunks_collection is not None:
        db_logger.info(f"Storing chunks in MongoDB: {settings.database_name}.{settings.collection_name}")
        try:
            # Prepare chunks for MongoDB (without embeddings to save space)
            mongo_chunks = []
            for chunk in chunks_with_embeddings:
                mongo_chunk = {
                    'chunk_id': chunk['id'],
                    'document_id': chunk['document_id'],
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks'],
                    'text': chunk['text'],
                    'metadata': chunk['metadata'],
                    'has_embedding': 'embedding' in chunk and chunk['embedding'] is not None,
                    'ingestion_timestamp': datetime.utcnow()
                }
                mongo_chunks.append(mongo_chunk)
            
            inserted_count = mongodb_client.insert_chunks_batch(mongo_chunks)
            db_logger.success(f"Stored {inserted_count} chunks in MongoDB",
                            database=settings.database_name,
                            collection=settings.collection_name)
        except Exception as e:
            db_logger.error(f"Error storing chunks in MongoDB: {e}")
    else:
        db_logger.warning("MongoDB not connected - skipping chunk storage")
        inserted_count = 0
    
    # Upload to Pinecone
    db_logger.info("Uploading vectors to Pinecone...")
    
    # Prepare vectors for Pinecone
    pinecone_vectors = []
    target_dimension = settings.pinecone_dimension
    
    for chunk in chunks_with_embeddings:
        if 'embedding' in chunk and chunk['embedding']:
            # Truncate embedding to match index dimension
            embedding = chunk['embedding'][:target_dimension]
            
            pinecone_vectors.append({
                'id': chunk['id'],
                'values': embedding,
                'metadata': {
                    'document_id': chunk['document_id'],
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks'],
                    'text': chunk['text'],
                    'filename': chunk['metadata'].get('filename', ''),
                    'title': chunk['metadata'].get('title', ''),
                    'document_type': chunk['metadata'].get('document_type', ''),
                }
            })
    
    # Upload to Pinecone in batches
    batch_size = 100
    index = pinecone_client.get_index()
    
    if index:
        for i in range(0, len(pinecone_vectors), batch_size):
            batch = pinecone_vectors[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(pinecone_vectors) + batch_size - 1) // batch_size
            
            db_logger.info(f"Uploading batch {batch_num}/{total_batches} to Pinecone")
            
            try:
                index.upsert(vectors=batch, namespace=namespace)
                db_logger.success(f"Uploaded batch {batch_num}: {len(batch)} vectors")
            except Exception as e:
                db_logger.error(f"Error uploading batch {batch_num}: {e}")
                continue
    else:
        db_logger.error("Pinecone index not available")
    
    # Final summary
    ingestion_duration = (datetime.utcnow() - ingestion_start).total_seconds()
    
    summary = {
        'total_documents': len(documents),
        'total_chunks': len(all_chunks),
        'chunks_with_embeddings': len([c for c in chunks_with_embeddings if 'embedding' in c]),
        'vectors_uploaded_to_pinecone': len(pinecone_vectors),
        'chunks_stored_in_mongodb': inserted_count,
        'processing_time_seconds': ingestion_duration,
        'embedding_model': settings.embedding_model,
        'pinecone_namespace': namespace,
        'pinecone_index': settings.pinecone_index_name,
        'mongodb_database': settings.database_name,
        'mongodb_collection': settings.collection_name,
        'log_database': settings.log_database_name,
        'log_collection': settings.log_collection_name,
        'document_stats': document_stats
    }
    
    db_logger.success("=" * 60)
    db_logger.success("Document Ingestion Complete!")
    db_logger.success("=" * 60)
    db_logger.info(f"Documents processed: {summary['total_documents']}")
    db_logger.info(f"Total chunks: {summary['total_chunks']}")
    db_logger.info(f"Embeddings generated: {summary['chunks_with_embeddings']}")
    db_logger.info(f"Pinecone vectors: {summary['vectors_uploaded_to_pinecone']}")
    db_logger.info(f"MongoDB chunks: {summary['chunks_stored_in_mongodb']}")
    db_logger.info(f"Processing time: {ingestion_duration:.2f}s")
    db_logger.success("=" * 60)
    
    # Log final summary to MongoDB audit trail
    mongodb_client.log_event(
        'ingestion_complete',
        'Document ingestion pipeline completed successfully',
        'SUCCESS',
        summary
    )
    
    # Close MongoDB connection
    mongodb_client.close()


async def main():
    """Main entry point."""
    # Default to kb/ directory
    kb_dir = Path(__file__).parent.parent / "kb"
    
    if not kb_dir.exists():
        logger.error(f"Directory not found: {kb_dir}")
        logger.error("Please create a kb/ directory and add your HR policy documents")
        return
    
    # Check configuration
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        logger.error("Azure OpenAI credentials not configured!")
        logger.error("Please set HR_AZURE_OPENAI_ENDPOINT and HR_AZURE_OPENAI_API_KEY in .env")
        return
    
    if not settings.pinecone_api_key:
        logger.error("Pinecone API key not configured!")
        logger.error("Please set HR_PINECONE_API_KEY in .env")
        return
    
    logger.info(f"Ingesting documents from: {kb_dir}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"Pinecone index: {settings.pinecone_index_name}")
    logger.info(f"MongoDB database: {settings.database_name}.{settings.collection_name}")
    logger.info(f"MongoDB logs: {settings.log_database_name}.{settings.log_collection_name}")
    logger.info("")
    
    await ingest_documents(str(kb_dir))


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    asyncio.run(main())
