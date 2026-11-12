"""
Ticket Model
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base
from app.models.category import PriorityEnum

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class TicketStatusEnum(str, enum.Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_EMPLOYEE = "WAITING_FOR_EMPLOYEE"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"  # Alias for WAITING_FOR_EMPLOYEE
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    CANCELLED = "CANCELLED"

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String(32), primary_key=True, index=True)
    tracking_number = Column(String(48), unique=True, nullable=False, index=True)
    employee_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = Column(String(32), ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(220), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TicketStatusEnum, native_enum=False), nullable=False, default=TicketStatusEnum.NEW, index=True)
    priority = Column(SQLEnum(PriorityEnum, native_enum=False), nullable=False, default=PriorityEnum.MEDIUM, index=True)
    is_sensitive = Column(Boolean, nullable=False, default=False, index=True)
    confidential_assigned_to = Column(String(32), ForeignKey("employees.emp_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Core Relationships
    employee = relationship("Employee", back_populates="submitted_tickets", foreign_keys=[employee_id])
    category = relationship("Category", back_populates="tickets")
    confidential_agent = relationship("Employee", back_populates="confidential_tickets", foreign_keys=[confidential_assigned_to])
    assignments = relationship("Assignment", back_populates="ticket", cascade="all, delete-orphan", order_by="desc(Assignment.assigned_at)")
    sla = relationship("SLA", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan", order_by="Message.created_at")
    resolution = relationship("Resolution", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    anomalies = relationship("AnomalyRecord", back_populates="ticket", cascade="all, delete-orphan")

    # Traceability & Event Relationships
    events = relationship("TicketEvent", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketEvent.created_at")
    citations = relationship("PolicyCitation", back_populates="ticket", cascade="all, delete-orphan", order_by="PolicyCitation.created_at")
    decision_traces = relationship("DecisionTrace", back_populates="ticket", cascade="all, delete-orphan", order_by="DecisionTrace.created_at")
    participants = relationship("TicketParticipant", back_populates="ticket", cascade="all, delete-orphan")
