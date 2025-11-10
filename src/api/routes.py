from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from pathlib import Path
from ..api.schemas import (
    HealthResponse, QueryRequest, QueryResponse,
)
from ..core.semantic_kernel_setup import sk_manager
from ..config.settings import get_settings
from ..config.prompts import HR_SYSTEM_PROMPT, CONVERSATION_CONTEXT_TEMPLATE
from ..services.llm_service import llm_service
from ..services.vector_store_service import vector_store_service
from ..services.memory_service import memory_service
from ..plugins.retrieval_plugin import RetrievalPlugin
from ..database.mongodb_client import mongodb_client
from ..database.pinecone_client import pinecone_client
from loguru import logger

router = APIRouter()
settings = get_settings()

# Initialize plugins
retrieval_plugin = RetrievalPlugin()

# In-memory storage for query status tracking
query_status_store: Dict[str, Dict[str, Any]] = {}


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Comprehensive health check endpoint.
    
    Checks:
    - API status
    - Azure OpenAI connection
    - Pinecone connection
    - MongoDB connection
    - Semantic Kernel initialization
    """
    checks = {
        "api": "ok",
        "azure_openai": "unknown",
        "pinecone": "unknown",
        "mongodb": "unknown",
        "semantic_kernel": "unknown"
    }
    
    errors = []
    
    try:
        # Check Azure OpenAI
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            try:
                await llm_service.initialize()
                checks["azure_openai"] = "ok"
            except Exception as e:
                checks["azure_openai"] = "error"
                errors.append(f"Azure OpenAI: {str(e)}")
        else:
            checks["azure_openai"] = "not_configured"
            errors.append("Azure OpenAI: credentials not configured")
        
        # Check Pinecone
        if settings.pinecone_api_key:
            try:
                index = pinecone_client.get_index()
                if index:
                    stats = index.describe_index_stats()
                    checks["pinecone"] = "ok"
                    checks["pinecone_vectors"] = stats.total_vector_count
                else:
                    checks["pinecone"] = "error"
                    errors.append("Pinecone: index not available")
            except Exception as e:
                checks["pinecone"] = "error"
                errors.append(f"Pinecone: {str(e)}")
        else:
            checks["pinecone"] = "not_configured"
            errors.append("Pinecone: API key not configured")
        
        # Check MongoDB
        try:
            if mongodb_client._client:
                mongodb_client._client.admin.command('ping')
                checks["mongodb"] = "ok"
                if mongodb_client._chunks_collection:
                    checks["mongodb_chunks"] = mongodb_client._chunks_collection.count_documents({})
            else:
                checks["mongodb"] = "not_configured"
        except Exception as e:
            checks["mongodb"] = "error"
            errors.append(f"MongoDB: {str(e)}")
        
        # Check Semantic Kernel
        try:
            kernel = sk_manager.get_kernel()
            if kernel:
                checks["semantic_kernel"] = "ok"
            else:
                checks["semantic_kernel"] = "error"
                errors.append("Semantic Kernel: not initialized")
        except Exception as e:
            checks["semantic_kernel"] = "error"
            errors.append(f"Semantic Kernel: {str(e)}")
        
        overall_status = "healthy" if not errors else "degraded"
        
        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            timestamp=datetime.utcnow(),
            checks=checks,
            errors=errors if errors else None
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="error",
            version=settings.app_version,
            timestamp=datetime.utcnow(),
            checks=checks,
            errors=[str(e)]
        )


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """
    Process a user query using RAG (Retrieval Augmented Generation).
    
    This endpoint:
    1. Creates a unique query ID for tracking
    2. Retrieves relevant HR policy documents
    3. Generates contextual responses using LLM
    4. Tracks all steps and status
    
    Returns query ID for status tracking via /status/{query_id}
    """
    query_id = str(uuid.uuid4())
    
    # Initialize status tracking
    query_status_store[query_id] = {
        "query_id": query_id,
        "status": "started",
        "query": req.query,
        "user_id": req.user_id,
        "started_at": datetime.utcnow().isoformat(),
        "steps": [],
        "current_step": "initializing"
    }
    
    def update_step(step_name: str, status: str = "in_progress", details: str = None):
        """Helper to update step status"""
        query_status_store[query_id]["current_step"] = step_name
        query_status_store[query_id]["steps"].append({
            "step": step_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        })
    
    try:
        # Step 1: Initialize session
        update_step("session_initialization", "in_progress", "Creating or retrieving session")
        session_id = req.session_id or str(uuid.uuid4())
        memory_service.create_session(session_id, req.user_id)
        memory_service.add_message(session_id, "user", req.query)
        update_step("session_initialization", "completed", f"Session ID: {session_id}")
        
        # Step 2: Document retrieval
        update_step("document_retrieval", "in_progress", f"Searching top {req.top_k} documents")
        logger.info(f"[{query_id}] Processing query: {req.query}")
        
        search_results = await vector_store_service.search(
            query=req.query,
            top_k=req.top_k,
            namespace="hr_policies"
        )
        
        retrieved_context = await retrieval_plugin.retrieve_and_answer(
            question=req.query,
            top_k=req.top_k
        )
        
        # Store retrieved documents in status
        retrieved_docs = []
        for result in search_results:
            retrieved_docs.append({
                "filename": result.get("metadata", {}).get("filename", "Unknown"),
                "title": result.get("metadata", {}).get("title", ""),
                "score": result.get("score", 0),
                "chunk_id": result.get("id", ""),
                "text_preview": result.get("metadata", {}).get("text", "")[:200] + "..." if result.get("metadata", {}).get("text") else ""
            })
        
        query_status_store[query_id]["retrieved_documents"] = retrieved_docs
        update_step("document_retrieval", "completed", f"Retrieved {len(search_results)} relevant documents")
        
        # Step 3: Context building
        update_step("context_building", "in_progress", "Building prompt with context and history")
        conversation_history = memory_service.get_formatted_history(session_id, limit=5)
        
        if conversation_history:
            full_prompt = CONVERSATION_CONTEXT_TEMPLATE.format(
                history=conversation_history,
                question=req.query,
                context=retrieved_context
            )
        else:
            full_prompt = f"{HR_SYSTEM_PROMPT}\n\n{retrieved_context}"
        update_step("context_building", "completed", "Prompt constructed successfully")
        
        # Step 4: LLM generation
        update_step("llm_generation", "in_progress", "Generating response using Azure OpenAI")
        await llm_service.initialize()
        answer = await llm_service.generate_response(
            prompt=full_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        update_step("llm_generation", "completed", f"Response generated ({len(answer)} chars)")
        
        # Step 5: Finalization
        update_step("finalization", "in_progress", "Saving response and preparing result")
        memory_service.add_message(session_id, "assistant", answer)
        
        # Extract sources
        sources = []
        for result in search_results:
            sources.append({
                "filename": result.get("metadata", {}).get("filename", "Unknown"),
                "score": result.get("score", 0),
                "title": result.get("metadata", {}).get("title", ""),
            })
        
        # Update final status
        query_status_store[query_id]["status"] = "completed"
        query_status_store[query_id]["current_step"] = "completed"
        query_status_store[query_id]["completed_at"] = datetime.utcnow().isoformat()
        query_status_store[query_id]["answer"] = answer
        query_status_store[query_id]["sources_count"] = len(sources)
        update_step("finalization", "completed", "Query processing complete")
        
        logger.info(f"[{query_id}] Query completed successfully")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            conversation_id=0,
            session_id=session_id,
            metadata={
                "query_id": query_id,
                "company_id": req.company_id,
                "top_k": req.top_k,
                "status_url": f"/api/v1/status/{query_id}"
            },
        )
        
    except Exception as e:
        logger.error(f"[{query_id}] Error processing query: {e}")
        
        # Update error status
        query_status_store[query_id]["status"] = "error"
        query_status_store[query_id]["error"] = str(e)
        query_status_store[query_id]["failed_at"] = datetime.utcnow().isoformat()
        update_step(query_status_store[query_id]["current_step"], "failed", str(e))
        
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/status/{query_id}")
async def get_query_status(query_id: str):
    """
    Get detailed status and all processing steps for a query.
    
    Returns:
    - Current status (started, in_progress, completed, error)
    - All processing steps with timestamps
    - Current step being executed
    - Final answer (if completed)
    - Error details (if failed)
    
    Example response:
    {
        "query_id": "abc-123",
        "status": "completed",
        "query": "What is the vacation policy?",
        "started_at": "2025-11-10T12:00:00",
        "completed_at": "2025-11-10T12:00:05",
        "current_step": "completed",
        "steps": [
            {
                "step": "session_initialization",
                "status": "completed",
                "timestamp": "2025-11-10T12:00:00",
                "details": "Session ID: xyz"
            },
            {
                "step": "document_retrieval",
                "status": "completed",
                "timestamp": "2025-11-10T12:00:01",
                "details": "Retrieved 5 relevant documents"
            },
            ...
        ],
        "answer": "According to the policy...",
        "sources_count": 5
    }
    """
    if query_id not in query_status_store:
        raise HTTPException(
            status_code=404,
            detail=f"Query ID '{query_id}' not found. It may have expired or never existed."
        )
    
    status_data = query_status_store[query_id]
    
    # Calculate duration if completed
    if status_data.get("completed_at"):
        started = datetime.fromisoformat(status_data["started_at"])
        completed = datetime.fromisoformat(status_data["completed_at"])
        status_data["duration_seconds"] = (completed - started).total_seconds()
    
    return status_data


# Cleanup endpoint (optional, for maintenance)
@router.delete("/status/{query_id}")
async def clear_query_status(query_id: str):
    """
    Clear status data for a specific query.
    
    Useful for cleanup after retrieving results.
    """
    if query_id not in query_status_store:
        raise HTTPException(status_code=404, detail=f"Query ID '{query_id}' not found")
    
    del query_status_store[query_id]
    return {"message": f"Status data for query '{query_id}' cleared successfully"}
