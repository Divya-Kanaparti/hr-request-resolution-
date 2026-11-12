"""
Audit Schemas
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    audit_id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    details_json: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True

