"""
Ticket Resolution and Employee Feedback Test Suite
"""
import pytest

def test_resolve_ticket_and_submit_rating(client, employee_token, agent_token):
    # 1. Create ticket
    create_res = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "category_id": "CAT-001",
            "title": "Dental in-network doctor verification",
            "description": "How do I check if my provider is in the dental network?",
            "priority": "MEDIUM"
        }
    )
    ticket_id = create_res.json()["ticket_id"]

    # 2. Agent resolves ticket
    resolve_res = client.post(
        f"/api/v1/tickets/{ticket_id}/resolve",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "resolution_type": "POLICY_EXPLANATION",
            "resolution_notes": "Directed employee to the Delta Dental network portal using member ID. Verified coverage is 100% preventive.",
            "root_cause": "Provider directory lookup",
            "policy_version_used_id": "VER-POL-HR-2026-001-02"
        }
    )
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["resolution_id"].startswith("RES-")
    assert res_data["ticket_id"] == ticket_id

    # Verify ticket status is now RESOLVED
    t_check = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {employee_token}"}).json()
    assert t_check["status"] == "RESOLVED"
    assert t_check["resolved_at"] is not None

    # 3. Employee rates resolution
    rate_res = client.post(
        f"/api/v1/tickets/{ticket_id}/rate",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "employee_rating": 5,
            "employee_feedback": "Fast and crystal clear response!"
        }
    )
    assert rate_res.status_code == 200
    assert rate_res.json()["employee_rating"] == 5
    assert rate_res.json()["employee_feedback"] == "Fast and crystal clear response!"

