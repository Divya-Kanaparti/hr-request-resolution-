"""
Resolution Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ResolutionBase(BaseModel):
    resolution_type: str = "POLICY_EXPLANATION"
    resolution_notes: str
    root_cause: Optional[str] = None
    policy_version_used_id: Optional[str] = None

class ResolutionCreate(ResolutionBase):
    pass

class ResolutionResponse(ResolutionBase):
    resolution_id: str
    ticket_id: str
    resolved_by_id: str
    resolved_by_name: Optional[str] = None
    employee_rating: Optional[int] = None
    employee_feedback: Optional[str] = None
    resolved_at: datetime
    policy_doc_code: Optional[str] = None

    class Config:
        from_attributes = True

class SatisfactionRatingRequest(BaseModel):
    employee_rating: int = Field(..., ge=1, le=5)
    employee_feedback: Optional[str] = None

