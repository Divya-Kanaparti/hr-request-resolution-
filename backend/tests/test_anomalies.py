"""
Anomaly Detection Engine Test Suite
"""
import pytest
from datetime import datetime, timedelta
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.resolution import Resolution, ResolutionTypeEnum
from app.models.sla import SLA
from app.models.category import PriorityEnum
from app.services.anomaly_service import run_full_anomaly_scan

def test_detect_obsolete_policy_citation(db, client, compliance_token):
    # Create ticket resolved with superseded policy version VER-001-1
    t = Ticket(
        ticket_id="TCK-ANOM-01",
        tracking_number="REQ-2026-9001",
        employee_id="EMP-TEST-01",
        category_id="CAT-001",
        title="Dental inquiry with obsolete citation",
        description="Inquiry about dental benefits",
        status=TicketStatusEnum.RESOLVED,
        priority=PriorityEnum.MEDIUM,
        is_sensitive=False
    )
    db.add(t)
    db.commit()

    res = Resolution(
        resolution_id="RES-ANOM-01",
        ticket_id=t.ticket_id,
        resolved_by_id="EMP-TEST-02",
        resolution_type=ResolutionTypeEnum.POLICY_EXPLANATION,
        resolution_notes="Resolved using older guidelines",
        policy_version_used_id="VER-001-1" # Superseded version
    )
    db.add(res)
    db.commit()

    # Trigger scan
    scan_res = client.post("/api/v1/anomalies/scan", headers={"Authorization": f"Bearer {compliance_token}"})
    assert scan_res.status_code == 200
    anomalies = scan_res.json()
    types = [a["anomaly_type"] for a in anomalies]
    assert "OBSOLETE_POLICY_CITATION" in types

def test_detect_sensitive_case_in_general_queue(db, client, compliance_token):
    # Create ticket with sensitive harassment trigger, but NO confidential_assigned_to
    t = Ticket(
        ticket_id="TCK-ANOM-02",
        tracking_number="REQ-2026-9002",
        employee_id="EMP-TEST-01",
        category_id="CAT-007",
        title="Harassment grievance against senior manager",
        description="Reporting severe workplace harassment",
        status=TicketStatusEnum.NEW,
        priority=PriorityEnum.URGENT,
        is_sensitive=True,
        confidential_assigned_to=None # Exposed!
    )
    db.add(t)
    db.commit()

    scan_res = client.post("/api/v1/anomalies/scan", headers={"Authorization": f"Bearer {compliance_token}"})
    assert scan_res.status_code == 200
    anomalies = scan_res.json()
    types = [a["anomaly_type"] for a in anomalies]
    assert "SENSITIVE_GENERAL_QUEUE" in types

def test_resolve_anomaly(client, compliance_token, db):
    # Run scan to create anomalies
    test_detect_obsolete_policy_citation(db, client, compliance_token)

    anom_list = client.get("/api/v1/anomalies", headers={"Authorization": f"Bearer {compliance_token}"}).json()
    assert len(anom_list) > 0
    target_id = anom_list[0]["anomaly_id"]

    # Resolve anomaly
    res = client.put(
        f"/api/v1/anomalies/{target_id}/resolve",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={"status": "RESOLVED", "resolution_comment": "Case re-opened and cited against v2.0."}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "RESOLVED"

