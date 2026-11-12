"""
Resolution Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

class ResolutionTypeEnum(str, enum.Enum):
    POLICY_EXPLANATION = "POLICY_EXPLANATION"
    MANUAL_CORRECTION = "MANUAL_CORRECTION"
    ESCALATION_RESOLVED = "ESCALATION_RESOLVED"
    POLICY_EXCEPTION = "POLICY_EXCEPTION"
    DUPLICATE = "DUPLICATE"
    WITHDRAWN = "WITHDRAWN"

class Resolution(Base):
    __tablename__ = "resolutions"

    resolution_id = Column(String(32), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    resolved_by_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="RESTRICT"), nullable=False, index=True)
    resolution_type = Column(SQLEnum(ResolutionTypeEnum), nullable=False, default=ResolutionTypeEnum.POLICY_EXPLANATION)
    resolution_notes = Column(Text, nullable=False)
    root_cause = Column(String(255), nullable=True)
    policy_version_used_id = Column(String(32), ForeignKey("policy_versions.version_id", ondelete="SET NULL"), nullable=True)
    employee_rating = Column(Integer, nullable=True)
    employee_feedback = Column(Text, nullable=True)
    resolved_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="resolution")
    resolver = relationship("Employee", back_populates="resolutions", foreign_keys=[resolved_by_id])
    policy_version_used = relationship("PolicyVersion", back_populates="resolutions", foreign_keys=[policy_version_used_id])

