"""
Routing and Escalation Rules Models
Configurable, prioritized, and deterministic decision rules.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime
from app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class RoutingRule(Base):
    __tablename__ = "routing_rules"

    rule_id = Column(String(32), primary_key=True, index=True)
    rule_name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=100, nullable=False, index=True)  # Lower number = higher precedence
    condition_expression = Column(Text, nullable=False)  # JSON or expression criteria
    target_category_id = Column(String(32), nullable=True)
    target_tier = Column(String(32), default="TIER_1")
    target_queue = Column(String(64), nullable=False)
    is_confidential_route = Column(Boolean, default=False, nullable=False)
    auto_assign_role = Column(String(48), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    rule_id = Column(String(32), primary_key=True, index=True)
    rule_name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=100, nullable=False, index=True)
    trigger_condition = Column(String(64), nullable=False)  # e.g. "SLA_BREACH_IMMINENT", "SLA_BREACHED", "UNSUPPORTED_POLICY"
    threshold_percent = Column(Integer, default=75)  # e.g. 75% elapsed
    escalate_to_role = Column(String(48), nullable=False)
    escalate_to_queue = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

