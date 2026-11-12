"""
Ticket Event Model
Immutable audit log for lifecycle state changes and operational events.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

class TicketEventTypeEnum(str, enum.Enum):
    CREATED = "CREATED"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    REASSIGNED = "REASSIGNED"
    STATUS_CHANGED = "STATUS_CHANGED"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    CLARIFICATION_RECEIVED = "CLARIFICATION_RECEIVED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"
    CLOSED = "CLOSED"
    NOTE_ADDED = "NOTE_ADDED"
    CITATION_LINKED = "CITATION_LINKED"
    ANOMALY_FLAGGED = "ANOMALY_FLAGGED"

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class TicketEvent(Base):
    __tablename__ = "ticket_events"

    event_id = Column(String(48), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(SQLEnum(TicketEventTypeEnum, native_enum=False), nullable=False, index=True)
    previous_state = Column(String(48), nullable=True)
    new_state = Column(String(48), nullable=False)
    actor_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="SET NULL"), nullable=True, index=True)
    actor_role = Column(String(48), nullable=True)
    reason = Column(Text, nullable=True)
    correlation_id = Column(String(64), nullable=True, index=True)
    related_policy_id = Column(String(48), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="events")
    actor = relationship("Employee", foreign_keys=[actor_id])

