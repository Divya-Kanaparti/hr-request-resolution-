"""
Message Schemas
"""
from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel

class MessageBase(BaseModel):
    content: str
    message_type: str = "EMPLOYEE_NOTE"
    is_internal: bool = False
    citations_json: Optional[Any] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    message_id: str
    ticket_id: str
    sender_id: str
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

