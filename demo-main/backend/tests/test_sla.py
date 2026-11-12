"""
Business Hours Engine and SLA Calculation Test Suite
"""
import pytest
from datetime import datetime
from app.core.business_hours import (
    add_business_hours,
    calculate_business_hours_between,
    calculate_sla_deadlines,
    snap_to_business_hours
)

def test_business_hours_same_day():
    # Monday 10:00 AM + 3 business hours -> Monday 1:00 PM (13:00)
    start = datetime(2026, 1, 5, 10, 0, 0)
    result = add_business_hours(start, 3.0)
    assert result == datetime(2026, 1, 5, 13, 0, 0)

def test_business_hours_spans_overnight():
    # Monday 15:00 (3 PM) + 4 business hours -> 2h Monday (until 17:00) + 2h Tuesday -> Tuesday 11:00 AM
    start = datetime(2026, 1, 5, 15, 0, 0)
    result = add_business_hours(start, 4.0)
    assert result == datetime(2026, 1, 6, 11, 0, 0)

def test_business_hours_skips_weekend():
    # Friday 15:00 (3 PM) + 4 business hours -> 2h Friday + skips Sat/Sun -> Monday 11:00 AM
    friday_start = datetime(2026, 1, 9, 15, 0, 0) # Friday
    result = add_business_hours(friday_start, 4.0)
    assert result == datetime(2026, 1, 12, 11, 0, 0) # Monday

def test_start_on_weekend_snaps_to_monday():
    # Saturday 14:00 + 2 business hours -> Monday 09:00 + 2h -> Monday 11:00
    saturday_start = datetime(2026, 1, 10, 14, 0, 0)
    result = add_business_hours(saturday_start, 2.0)
    assert result == datetime(2026, 1, 12, 11, 0, 0)

def test_calculate_elapsed_business_hours():
    # Monday 09:00 to Tuesday 17:00 = 2 full days of 8 hours = 16 hours
    start = datetime(2026, 1, 5, 9, 0, 0)
    end = datetime(2026, 1, 6, 17, 0, 0)
    elapsed = calculate_business_hours_between(start, end)
    assert elapsed == 16.0

def test_priority_sla_thresholds():
    created = datetime(2026, 1, 5, 9, 0, 0)
    _, _, limit_urgent = calculate_sla_deadlines(created, "URGENT")
    assert limit_urgent == 4

    _, _, limit_high = calculate_sla_deadlines(created, "HIGH")
    assert limit_high == 8

    _, _, limit_med = calculate_sla_deadlines(created, "MEDIUM")
    assert limit_med == 24

    _, _, limit_low = calculate_sla_deadlines(created, "LOW")
    assert limit_low == 48

