"""
Decision Trace Model
Maintains complete step-by-step decision and event traceability:
triage -> classification -> sensitivity -> sufficiency -> policy lookup -> answer/clarification/escalation -> assignment -> SLA start.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class DecisionTrace(Base):
    __tablename__ = "decision_traces"

    trace_id = Column(String(48), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(64), nullable=False, index=True)  # CLASSIFICATION, SENSITIVITY_CHECK, CONTEXT_EVALUATION, POLICY_LOOKUP, ROUTING, SLA_SCHEDULING, RESOLUTION
    input_context_json = Column(Text, nullable=True)
    output_decision = Column(String(120), nullable=False)
    rule_id_applied = Column(String(48), nullable=True)
    rationale = Column(Text, nullable=False)
    is_automated = Column(Boolean, default=True, nullable=False)
    actor_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    ticket = relationship("Ticket", back_populates="decision_traces")
    actor = relationship("Employee", foreign_keys=[actor_id])

