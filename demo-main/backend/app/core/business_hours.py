"""
Business Hours and SLA Calculation Engine
Calculates business-day hours (Mon-Fri 09:00 - 17:00), excluding weekends and holidays.
"""
from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Set
from app.core.config import settings

# Standard Corporate Holidays (Yearly fixed and standard observed dates)
STANDARD_HOLIDAYS: Set[Tuple[int, int]] = {
    (1, 1),   # New Year's Day
    (5, 1),   # Labor Day
    (7, 4),   # Independence Day
    (12, 25), # Christmas Day
    (12, 26), # Boxing Day
}

def is_work_day(dt: datetime) -> bool:
    """Check if date is a standard working day and not a recognized holiday."""
    if dt.weekday() not in settings.parsed_work_days:
        return False
    if (dt.month, dt.day) in STANDARD_HOLIDAYS:
        return False
    return True

def get_next_workday_start(dt: datetime) -> datetime:
    """Find the next valid working day at 09:00:00."""
    cur = dt + timedelta(days=1)
    while not is_work_day(cur):
        cur += timedelta(days=1)
    return cur.replace(
        hour=settings.BUSINESS_HOUR_START,
        minute=0,
        second=0,
        microsecond=0
    )

def snap_to_business_hours(dt: datetime) -> datetime:
    """
    If datetime falls outside business hours or on non-work days,
    roll forward to the next business hour window start.
    """
    cur = dt
    # If on a weekend or holiday, advance to next workday start
    while not is_work_day(cur):
        cur = get_next_workday_start(cur - timedelta(days=1))
    
    # If before opening
    if cur.hour < settings.BUSINESS_HOUR_START:
        return cur.replace(hour=settings.BUSINESS_HOUR_START, minute=0, second=0, microsecond=0)
    
    # If after closing, advance to next business day start
    if cur.hour >= settings.BUSINESS_HOUR_END:
        return get_next_workday_start(cur)
        
    return cur

def add_business_hours(start_dt: datetime, hours_to_add: float) -> datetime:
    """
    Accurately add business hours to a timestamp, skipping non-working hours,
    weekends, and corporate holidays.
    """
    cur = snap_to_business_hours(start_dt)
    remaining_minutes = int(round(hours_to_add * 60))
    daily_work_minutes = (settings.BUSINESS_HOUR_END - settings.BUSINESS_HOUR_START) * 60

    while remaining_minutes > 0:
        if not is_work_day(cur):
            cur = get_next_workday_start(cur - timedelta(days=1))
            continue
            
        day_end = cur.replace(
            hour=settings.BUSINESS_HOUR_END,
            minute=0,
            second=0,
            microsecond=0
        )
        minutes_left_today = int((day_end - cur).total_seconds() / 60)
        
        if minutes_left_today <= 0:
            cur = get_next_workday_start(cur)
            continue

        if remaining_minutes <= minutes_left_today:
            cur += timedelta(minutes=remaining_minutes)
            remaining_minutes = 0
        else:
            remaining_minutes -= minutes_left_today
            cur = get_next_workday_start(cur)
            
    return cur

def calculate_business_hours_between(start_dt: datetime, end_dt: datetime) -> float:
    """
    Calculate exact business hours elapsed between start_dt and end_dt.
    """
    if start_dt >= end_dt:
        return 0.0

    cur = snap_to_business_hours(start_dt)
    total_minutes = 0

    while cur < end_dt:
        if not is_work_day(cur):
            cur = get_next_workday_start(cur - timedelta(days=1))
            continue
            
        day_end = cur.replace(
            hour=settings.BUSINESS_HOUR_END,
            minute=0,
            second=0,
            microsecond=0
        )
        
        if end_dt <= day_end:
            if is_work_day(end_dt) and end_dt.hour >= settings.BUSINESS_HOUR_START:
                capped_end = min(end_dt, day_end)
                total_minutes += int((capped_end - cur).total_seconds() / 60)
            break
        else:
            total_minutes += int((day_end - cur).total_seconds() / 60)
            cur = get_next_workday_start(cur)

    return round(total_minutes / 60.0, 2)

def calculate_sla_deadlines(created_at: datetime, priority: str) -> Tuple[datetime, datetime, int]:
    """
    Return (response_due_at, resolution_due_at, business_hours_limit)
    based on priority tier.
    """
    p = priority.upper()
    if p == "URGENT":
        resp_hours = 1
        res_hours = 4
    elif p == "HIGH":
        resp_hours = 2
        res_hours = 8
    elif p == "LOW":
        resp_hours = 8
        res_hours = 48
    else:  # MEDIUM default
        resp_hours = 4
        res_hours = 24

    resp_due = add_business_hours(created_at, resp_hours)
    res_due = add_business_hours(created_at, res_hours)
    return resp_due, res_due, res_hours

