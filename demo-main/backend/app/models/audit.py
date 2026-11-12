"""
Audit Log Model (Immutable Event History)
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(32), primary_key=True, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(32), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="SET NULL"), nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    actor = relationship("Employee", foreign_keys=[actor_id])

