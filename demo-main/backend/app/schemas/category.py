"""
Category Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    default_priority: str = "MEDIUM"
    is_sensitive_default: bool = False
    tier: str = "TIER_1"

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: str
    created_at: datetime

    class Config:
        from_attributes = True

