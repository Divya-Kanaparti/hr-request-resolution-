"""
Ticket Submission, Classification, Triage, and RBAC Test Suite
"""
import pytest
import re

def test_ticket_creation_and_auto_classification(client, employee_token):
    res = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "category_id": "CAT-001",
            "title": "Dental insurance coverage inquiry for crown",
            "description": "How much does the company insurance cover for major dental procedures like crowns and root canals?",
            "priority": "MEDIUM",
            "is_sensitive": False
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert re.fullmatch(r"TKT-\d{4}-\d{6}", data["ticket_id"])
    assert data["tracking_number"].startswith("REQ-2026-")
    assert data["status"] in ["NEW", "IN_PROGRESS"]
    assert data["category_name"] == "Benefits"

def test_ambiguous_ticket_triggers_clarification(client, employee_token):
    # Short and vague request lacking dates and leave type
    res = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "category_id": "CAT-002",
            "title": "I need off",
            "description": "Can I take some time off next week?",
            "priority": "MEDIUM",
            "is_sensitive": False
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "CLARIFICATION_NEEDED"

def test_sensitive_case_confidential_routing(client, employee_token, agent_token, manager_token):
    # Submit sensitive harassment ticket
    res = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "category_id": "CAT-007",
            "title": "Confidential report of workplace harassment by supervisor",
            "description": "I am experiencing repeated hostile remarks and discriminatory treatment from my lead.",
            "priority": "URGENT",
            "is_sensitive": True
        }
    )
    assert res.status_code == 201
    ticket = res.json()
    assert ticket["is_sensitive"] is True
    assert ticket["confidential_assigned_to"] is not None
    ticket_id = ticket["ticket_id"]

    # 1. Employee who submitted can see it
    emp_view = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {employee_token}"})
    assert emp_view.status_code == 200

    # 2. General HR Agent CANNOT access sensitive ticket
    agent_view = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {agent_token}"})
    assert agent_view.status_code == 403

    # 3. HR Manager CAN access sensitive ticket
    mgr_view = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert mgr_view.status_code == 200

def test_ticket_assignment_and_escalation(client, agent_token, manager_token, employee_token):
    # Create ticket
    create_res = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "category_id": "CAT-001",
            "title": "HSA contribution limits inquiry",
            "description": "What is the maximum pre-tax deduction for HSA this calendar year?",
            "priority": "LOW",
            "is_sensitive": False
        }
    )
    ticket_id = create_res.json()["ticket_id"]

    # Assign ticket
    asg_res = client.post(
        f"/api/v1/tickets/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "assigned_to_id": "EMP-TEST-02",
            "tier": "TIER_1",
            "reason": "Direct triage assignment"
        }
    )
    assert asg_res.status_code == 200

    # Escalate ticket
    esc_res = client.post(
        f"/api/v1/tickets/{ticket_id}/escalate",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "target_tier": "TIER_2",
            "escalation_reason": "Complex benefits exception requested"
        }
    )
    assert esc_res.status_code == 200
    assert esc_res.json()["status"] == "ESCALATED"

def test_ticket_messaging_internal_note_privacy(client, employee_token, agent_token):
    # Create ticket
    create_res = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "category_id": "CAT-003",
            "title": "Paycheck dispute for March 15",
            "description": "My paycheck was short 8 hours of regular pay.",
            "priority": "HIGH"
        }
    )
    ticket_id = create_res.json()["ticket_id"]

    # Agent posts internal note
    client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "content": "CONFIDENTIAL: Internal payroll audit indicates timesheet was submitted late by supervisor.",
            "message_type": "INTERNAL_NOTE",
            "is_internal": True
        }
    )
    reply_res = client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "content": "The review is underway.",
            "message_type": "AGENT_REPLY",
            "is_internal": False
        }
    )
    assert reply_res.status_code == 201
    assert reply_res.json()["message_id"] == f"MSG-{ticket_id}-002"

    # Employee views ticket -> internal note MUST BE FILTERED OUT
    emp_view = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {employee_token}"})
    messages = emp_view.json()["messages"]
    internal_msgs = [m for m in messages if m.get("is_internal") is True]
    assert len(internal_msgs) == 0

    # Agent views ticket -> internal note IS VISIBLE
    agent_view = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {agent_token}"})
    agent_messages = agent_view.json()["messages"]
    agent_internal_msgs = [m for m in agent_messages if m.get("is_internal") is True]
    assert len(agent_internal_msgs) == 1
    assert agent_internal_msgs[0]["message_id"] == f"MSG-{ticket_id}-001"

