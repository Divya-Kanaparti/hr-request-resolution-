"""
Assignment Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.models.category import TierEnum

class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(String(32), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_by_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="RESTRICT"), nullable=False)
    tier = Column(SQLEnum(TierEnum), nullable=False, default=TierEnum.TIER_1)
    reason = Column(String(255), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    unassigned_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="assignments")
    assigned_to = relationship("Employee", back_populates="assignments_received", foreign_keys=[assigned_to_id])
    assigned_by = relationship("Employee", back_populates="assignments_created", foreign_keys=[assigned_by_id])

