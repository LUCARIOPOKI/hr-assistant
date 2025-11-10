"""Company data model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Company(BaseModel):
    """Company data model."""
    id: Optional[int] = None
    name: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    headquarters: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
