"""
SLA Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.models.category import PriorityEnum

class SLA(Base):
    __tablename__ = "slas"

    sla_id = Column(String(32), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, unique=True)
    priority = Column(SQLEnum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM)
    business_hours_limit = Column(Integer, nullable=False, default=24)
    response_due_at = Column(DateTime, nullable=False)
    resolution_due_at = Column(DateTime, nullable=False, index=True)
    first_response_at = Column(DateTime, nullable=True)
    is_response_breached = Column(Boolean, nullable=False, default=False)
    is_resolution_breached = Column(Boolean, nullable=False, default=False, index=True)
    calculated_business_hours = Column(Numeric(6, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="sla")

