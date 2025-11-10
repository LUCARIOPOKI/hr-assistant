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
    Process a user query using Agentic RAG.
    
    The agent autonomously:
    1. Plans how to answer the question
    2. Calls appropriate tools (search, retrieve details, etc.)
    3. Reasons about the information
    4. Generates a comprehensive answer
    
    Returns query ID for status tracking via /status/{query_id}
    """
    query_id = str(uuid.uuid4())
    
    # Initialize status tracking with agent-specific fields
    query_status_store[query_id] = {
        "query_id": query_id,
        "status": "started",
        "query": req.query,
        "user_id": req.user_id,
        "started_at": datetime.utcnow().isoformat(),
        "steps": [],
        "current_step": "initializing",
        "agent_plan": None,
        "tool_calls": [],
        "iterations": 0
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
        
        # Step 2: Agent Planning & Execution
        update_step("agent_planning", "in_progress", "Agent analyzing query and planning approach")
        logger.info(f"[{query_id}] Starting agentic execution for: {req.query}")
        
        # Build agent system prompt with context
        conversation_history = memory_service.get_formatted_history(session_id, limit=5)
        
        agent_system_prompt = f"""{HR_SYSTEM_PROMPT}

You are an intelligent HR assistant with access to multiple tools to help answer questions.

Available tools:
- search_policy_documents: Search for specific policies by topic or keyword
- get_document_details: Get complete information from a specific document
- search_related_topics: Find connections between different policy areas
- list_available_policies: See what policy documents are available

Your task:
1. Analyze the user's question carefully
2. Plan which tools to use to gather comprehensive information
3. Call the tools as needed to collect relevant data
4. Synthesize the information into a clear, helpful answer
5. Be thorough - use multiple tools if needed to provide complete answers

Previous conversation:
{conversation_history if conversation_history else "No previous context"}

Remember: Base your answers only on the retrieved policy documents. If information is not available, say so clearly.
"""
        
        # Execute agent with auto tool calling
        await llm_service.initialize()
        agent_result = await llm_service.agent_execute(
            query=req.query,
            system_prompt=agent_system_prompt,
            max_iterations=5,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract agent results
        answer = agent_result["answer"]
        tool_calls = agent_result["tool_calls"]
        iterations = agent_result["iterations"]
        agent_plan = agent_result["agent_plan"]
        
        # Store agent metadata
        query_status_store[query_id]["agent_plan"] = agent_plan
        query_status_store[query_id]["tool_calls"] = tool_calls
        query_status_store[query_id]["iterations"] = iterations
        
        update_step("agent_planning", "completed", 
                   f"Agent completed in {iterations} iteration(s) with {len(tool_calls)} tool call(s)")
        
        # Step 3: Extract sources from tool calls
        update_step("source_extraction", "in_progress", "Extracting document sources from agent tools")
        sources = []
        
        # If agent used search tools, extract sources from those results
        # For now, do a quick search to get sources for metadata
        search_results = await vector_store_service.search(
            query=req.query,
            top_k=req.top_k,
            namespace="hr_policies"
        )
        
        retrieved_docs = []
        for result in search_results:
            doc_info = {
                "filename": result.get("metadata", {}).get("filename", "Unknown"),
                "title": result.get("metadata", {}).get("title", ""),
                "score": result.get("score", 0),
                "chunk_id": result.get("id", ""),
                "text_preview": result.get("metadata", {}).get("text", "")[:200] + "..." if result.get("metadata", {}).get("text") else ""
            }
            retrieved_docs.append(doc_info)
            sources.append({
                "filename": doc_info["filename"],
                "score": doc_info["score"],
                "title": doc_info["title"]
            })
        
        query_status_store[query_id]["retrieved_documents"] = retrieved_docs
        update_step("source_extraction", "completed", f"Extracted {len(sources)} source documents")
        
        # Step 4: Finalization
        update_step("finalization", "in_progress", "Saving response and preparing result")
        memory_service.add_message(session_id, "assistant", answer)
        
        # Update final status
        query_status_store[query_id]["status"] = "completed"
        query_status_store[query_id]["current_step"] = "completed"
        query_status_store[query_id]["completed_at"] = datetime.utcnow().isoformat()
        query_status_store[query_id]["answer"] = answer
        query_status_store[query_id]["sources_count"] = len(sources)
        update_step("finalization", "completed", "Query processing complete")
        
        logger.info(f"[{query_id}] Agentic query completed successfully")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            conversation_id=0,
            session_id=session_id,
            agent_plan=agent_plan,
            tool_calls=tool_calls,
            iterations=iterations,
            metadata={
                "query_id": query_id,
                "company_id": req.company_id,
                "top_k": req.top_k,
                "status_url": f"/api/v1/status/{query_id}",
                "mode": "agentic_rag"
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
    Get detailed status and all processing steps for an agentic query.
    
    Returns:
    - Current status (started, in_progress, completed, error)
    - All processing steps with timestamps
    - Agent planning information
    - Tool calls made by the agent
    - Iterations taken
    - Retrieved documents with scores
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
        "agent_plan": "Completed in 3 iteration(s) with 2 tool call(s)",
        "iterations": 3,
        "tool_calls": [
            {
                "tool_name": "search_policy_documents",
                "arguments": {"query": "vacation policy", "top_k": 3},
                "iteration": 1
            },
            {
                "tool_name": "get_document_details",
                "arguments": {"document_identifier": "HR Policy Manual"},
                "iteration": 2
            }
        ],
        "steps": [
            {
                "step": "session_initialization",
                "status": "completed",
                "timestamp": "2025-11-10T12:00:00",
                "details": "Session ID: xyz"
            },
            {
                "step": "agent_planning",
                "status": "completed",
                "timestamp": "2025-11-10T12:00:03",
                "details": "Agent completed in 3 iteration(s) with 2 tool call(s)"
            },
            ...
        ],
        "retrieved_documents": [
            {
                "filename": "HR Policy Manual 2023.pdf",
                "title": "Vacation Policy",
                "score": 0.95,
                "chunk_id": "doc_123_chunk_5",
                "text_preview": "Employees are entitled to..."
            }
        ],
        "answer": "According to the policy...",
        "sources_count": 5,
        "duration_seconds": 5.2
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
