"""
Message Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

class MessageTypeEnum(str, enum.Enum):
    EMPLOYEE_NOTE = "EMPLOYEE_NOTE"
    AGENT_REPLY = "AGENT_REPLY"
    INTERNAL_NOTE = "INTERNAL_NOTE"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    CLARIFICATION_PROMPT = "CLARIFICATION_PROMPT"

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String(32), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="RESTRICT"), nullable=False, index=True)
    message_type = Column(SQLEnum(MessageTypeEnum), nullable=False, index=True)
    content = Column(Text, nullable=False)
    citations_json = Column(JSON, nullable=True)
    is_internal = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
    sender = relationship("Employee", back_populates="messages", foreign_keys=[sender_id])

