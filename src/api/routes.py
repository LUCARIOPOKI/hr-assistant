from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional
import uuid
from ..api.schemas import (
    HealthResponse, QueryRequest, QueryResponse,
    SummarizationRequest, SummarizationResponse,
)
from ..core.semantic_kernel_setup import sk_manager
from ..config.settings import get_settings
from ..config.prompts import HR_SYSTEM_PROMPT, CONVERSATION_CONTEXT_TEMPLATE
from ..services.llm_service import llm_service
from ..services.vector_store_service import vector_store_service
from ..services.memory_service import memory_service
from ..plugins.retrieval_plugin import RetrievalPlugin
from ..plugins.summarization_plugin import SummarizationPlugin
from ..plugins.company_plugin import CompanyPlugin
from ..plugins.hr_policy_plugin import HRPolicyPlugin, EmployeeServicesPlugin, RecruitmentPlugin
from loguru import logger

router = APIRouter()
settings = get_settings()

# Initialize plugins
retrieval_plugin = RetrievalPlugin()
summarization_plugin = SummarizationPlugin()
company_plugin = CompanyPlugin()
hr_policy_plugin = HRPolicyPlugin()
employee_services_plugin = EmployeeServicesPlugin()
recruitment_plugin = RecruitmentPlugin()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version=settings.app_version, timestamp=datetime.utcnow())


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """
    Process a user query using RAG (Retrieval Augmented Generation).
    
    This endpoint:
    1. Retrieves relevant HR policy documents
    2. Maintains conversation history
    3. Generates contextual responses using LLM
    """
    try:
        # Initialize session if needed
        session_id = req.session_id or str(uuid.uuid4())
        memory_service.create_session(session_id, req.user_id)
        
        # Add user message to history
        memory_service.add_message(session_id, "user", req.query)
        
        # Retrieve relevant documents
        logger.info(f"Processing query: {req.query}")
        retrieved_context = await retrieval_plugin.retrieve_and_answer(
            question=req.query,
            top_k=req.top_k
        )
        
        # Get conversation history
        conversation_history = memory_service.get_formatted_history(session_id, limit=5)
        
        # Build full prompt with context and history
        if conversation_history:
            full_prompt = CONVERSATION_CONTEXT_TEMPLATE.format(
                history=conversation_history,
                question=req.query,
                context=retrieved_context
            )
        else:
            full_prompt = f"{HR_SYSTEM_PROMPT}\n\n{retrieved_context}"
        
        # Generate response
        await llm_service.initialize()
        answer = await llm_service.generate_response(
            prompt=full_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Add assistant response to history
        memory_service.add_message(session_id, "assistant", answer)
        
        # Extract sources from retrieval
        sources = []
        search_results = await vector_store_service.search(
            query=req.query,
            top_k=req.top_k,
            namespace="hr_policies"
        )
        
        for result in search_results:
            sources.append({
                "filename": result.get("metadata", {}).get("filename", "Unknown"),
                "score": result.get("score", 0),
                "title": result.get("metadata", {}).get("title", ""),
            })
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            conversation_id=0,  # Can be enhanced with DB storage
            session_id=session_id,
            metadata={"company_id": req.company_id, "top_k": req.top_k},
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/summarize", response_model=SummarizationResponse)
async def summarize(req: SummarizationRequest):
    """
    Generate a summary of HR documents for a specific audience.
    
    This can summarize policies, handbooks, or retrieved documents.
    """
    try:
        # In a real implementation, retrieve company documents
        # For now, we'll use a sample document retrieval
        logger.info(f"Generating {req.summary_type} summary for audience: {req.audience}")
        
        # Search for relevant documents
        search_query = "HR policies procedures company handbook"
        results = await vector_store_service.search(
            query=search_query,
            top_k=10,
            namespace="hr_policies"
        )
        
        # Combine retrieved documents
        if results:
            document_text = "\n\n".join([r.get("text", "") for r in results[:5]])
        else:
            document_text = "No HR documents found in the system."
        
        # Generate summary
        summary = await summarization_plugin.summarize_for_audience(
            document=document_text,
            audience=req.audience
        )
        
        return SummarizationResponse(
            company_name=f"Company {req.company_id}",
            summary=summary,
            summary_type=req.summary_type,
            audience=req.audience,
            generated_at=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.get("/company/info")
async def get_company_info(info_type: str = "overview"):
    """Get company information."""
    try:
        info = await company_plugin.get_company_info(info_type=info_type)
        return {"info_type": info_type, "content": info}
    except Exception as e:
        logger.error(f"Error getting company info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hr/policy")
async def get_hr_policy(question: str):
    """Ask HR policy questions."""
    try:
        answer = await hr_policy_plugin.answer_policy_question(question=question)
        return {"question": question, "answer": answer}
    except Exception as e:
        logger.error(f"Error answering policy question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hr/leave-balance/{employee_id}")
async def get_leave_balance(employee_id: str):
    """Check employee leave balance."""
    try:
        balance = await employee_services_plugin.check_leave_balance(employee_id=employee_id)
        return {"employee_id": employee_id, "balance": balance}
    except Exception as e:
        logger.error(f"Error checking leave balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recruitment/openings")
async def get_job_openings(department: str = "all"):
    """Get current job openings."""
    try:
        openings = await recruitment_plugin.get_job_openings(department=department)
        return {"department": department, "openings": openings}
    except Exception as e:
        logger.error(f"Error getting job openings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
