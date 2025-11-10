"""Data models for the HR assistant."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company data model."""
    id: Optional[int] = None
    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Document(BaseModel):
    """Document data model."""
    id: Optional[int] = None
    company_id: Optional[int] = None
    title: str
    source: Optional[str] = None
    document_type: str = "policy"
    content: Optional[str] = None
    metadata: Optional[dict] = None
    status: str = "processed"
    chunk_count: int = 0
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentChunk(BaseModel):
    """Document chunk model for vector storage."""
    id: str
    document_id: Optional[int] = None
    text: str
    chunk_index: int
    embedding: Optional[list] = None
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
