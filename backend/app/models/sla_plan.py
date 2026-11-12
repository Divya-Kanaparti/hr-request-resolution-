"""
SLA Plan, Business Calendar, and Holiday Models
Supports enterprise business-hours SLA calculations, public holidays, and weekend exclusions.
"""
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class BusinessCalendar(Base):
    __tablename__ = "business_calendars"

    calendar_id = Column(String(32), primary_key=True, index=True)
    calendar_name = Column(String(120), nullable=False)
    timezone = Column(String(64), default="UTC", nullable=False)
    business_hour_start = Column(Integer, default=9, nullable=False)  # 09:00
    business_hour_end = Column(Integer, default=17, nullable=False)    # 17:00
    work_days = Column(String(32), default="0,1,2,3,4", nullable=False)  # Mon-Fri
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    holidays = relationship("Holiday", back_populates="calendar", cascade="all, delete-orphan")

class Holiday(Base):
    __tablename__ = "holidays"

    holiday_id = Column(String(32), primary_key=True, index=True)
    calendar_id = Column(String(32), ForeignKey("business_calendars.calendar_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    holiday_date = Column(Date, nullable=False, index=True)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    calendar = relationship("BusinessCalendar", back_populates="holidays")

class SLAPlan(Base):
    __tablename__ = "sla_plans"

    plan_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    category_id = Column(String(32), ForeignKey("categories.category_id", ondelete="CASCADE"), nullable=True, index=True)
    priority = Column(String(32), nullable=False, index=True)  # LOW, MEDIUM, HIGH, URGENT
    response_hours = Column(Float, nullable=False)
    resolution_hours = Column(Float, nullable=False)
    calendar_id = Column(String(32), ForeignKey("business_calendars.calendar_id", ondelete="RESTRICT"), nullable=False)
    allow_clarification_pause = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

