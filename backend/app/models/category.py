"""
Category Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

class PriorityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class TierEnum(str, enum.Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(32), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    default_priority = Column(SQLEnum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM)
    is_sensitive_default = Column(Boolean, nullable=False, default=False)
    tier = Column(SQLEnum(TierEnum), nullable=False, default=TierEnum.TIER_1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tickets = relationship("Ticket", back_populates="category")
    policies = relationship("PolicyDocument", back_populates="category")

