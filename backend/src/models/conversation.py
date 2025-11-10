"""Conversation data models."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class Message(BaseModel):
    """Message model."""
    id: Optional[int] = None
    conversation_id: int
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Conversation(BaseModel):
    """Conversation model."""
    id: Optional[int] = None
    user_id: str
    session_id: str
    title: Optional[str] = None
    company_id: Optional[int] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: List[Message] = []
    
    class Config:
        from_attributes = True
