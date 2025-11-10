from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Request Schemas

class CompanyCreate(BaseModel):
    """Schema for creating a company."""
    name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    headquarters: Optional[str] = Field(None, max_length=255)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)


class DocumentUpload(BaseModel):
    """Schema for document upload."""
    company_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=500)
    source: Optional[str] = Field(None, max_length=1000)


class QueryRequest(BaseModel):
    """Schema for query request."""
    query: str = Field(..., min_length=1)
    company_id: Optional[int] = Field(None, gt=0)
    session_id: Optional[str] = None
    user_id: str = Field(default="default_user")
    top_k: Optional[int] = Field(5, ge=1, le=20)


class SummarizationRequest(BaseModel):
    """Schema for summarization request."""
    company_id: int = Field(..., gt=0)
    summary_type: str = Field(default="comprehensive")
    audience: str = Field(default="general")


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""
    user_id: str = Field(..., min_length=1)
    company_id: Optional[int] = Field(None, gt=0)
    title: Optional[str] = Field(None, max_length=255)


# Response Schemas

class CompanyResponse(BaseModel):
    """Schema for company response."""
    id: int
    name: str
    industry: Optional[str]
    sector: Optional[str]
    description: Optional[str]
    website: Optional[str]
    headquarters: Optional[str]
    founded_year: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    company_id: int
    title: str
    source: Optional[str]
    document_type: str
    status: str
    chunk_count: int
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: int
    user_id: str
    session_id: str
    company_id: Optional[int]
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class QueryResponse(BaseModel):
    """Schema for query response with agentic RAG metadata."""
    answer: str
    sources: List[Dict[str, Any]] = []
    conversation_id: int
    session_id: str
    metadata: Optional[Dict[str, Any]] = None
    # Agentic RAG fields
    agent_plan: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = []
    iterations: Optional[int] = 0


class SummarizationResponse(BaseModel):
    """Schema for summarization response."""
    company_name: str
    summary: str
    summary_type: str
    audience: str
    generated_at: datetime


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
    timestamp: datetime
    checks: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime