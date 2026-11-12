"""
Anomaly Record Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

class AnomalyTypeEnum(str, enum.Enum):
    OBSOLETE_POLICY_CITATION = "OBSOLETE_POLICY_CITATION"
    SENSITIVE_GENERAL_QUEUE = "SENSITIVE_GENERAL_QUEUE"
    INCORRECT_SLA_CALCULATION = "INCORRECT_SLA_CALCULATION"
    UNSUPPORTED_POLICY_CLAIM = "UNSUPPORTED_POLICY_CLAIM"

class AnomalySeverityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AnomalyStatusEnum(str, enum.Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"

class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    anomaly_id = Column(String(32), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    anomaly_type = Column(SQLEnum(AnomalyTypeEnum), nullable=False, index=True)
    severity = Column(SQLEnum(AnomalySeverityEnum), nullable=False, default=AnomalySeverityEnum.HIGH)
    detected_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(AnomalyStatusEnum), nullable=False, default=AnomalyStatusEnum.DETECTED, index=True)
    ground_truth_label = Column(Boolean, nullable=False, default=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="anomalies")

