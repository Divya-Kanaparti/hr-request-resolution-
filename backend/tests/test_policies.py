"""
Policy Management and Version Control Test Suite
"""
import pytest
import re

def test_list_policies(client, employee_token):
    res = client.get("/api/v1/policies", headers={"Authorization": f"Bearer {employee_token}"})
    assert res.status_code == 200
    policies = res.json()
    assert len(policies) >= 1
    p = policies[0]
    assert p["doc_code"] == "POL-BEN-01"
    assert len(p["versions"]) >= 1

def test_get_policy_details_with_articles(client, employee_token):
    res = client.get("/api/v1/policies/POL-HR-2026-001", headers={"Authorization": f"Bearer {employee_token}"})
    assert res.status_code == 200
    p = res.json()
    assert p["policy_id"] == "POL-HR-2026-001"
    assert len(p["versions"]) == 2 # v2.0 active and v1.0 superseded

def test_create_new_policy_version_supersedes_old(client, manager_token):
    res = client.post(
        "/api/v1/policies/POL-HR-2026-001/versions",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "version_number": "3.0",
            "status": "ACTIVE",
            "effective_from": "2026-06-01",
            "summary": "Updated dental benefits with orthotics coverage",
            "content": "Expanded dental coverage includes 50% orthodontics up to $2,000 lifetime maximum.",
            "changelog": "Added orthodontics tier",
            "articles": [
                {
                    "title": "Orthodontic Treatment Guidelines",
                    "section_number": "Sec 2.5",
                    "content": "Orthodontic benefits apply to dependent children under 19 years of age.",
                    "keywords": "orthodontics, braces, dental",
                    "audience": "ALL_EMPLOYEES",
                    "is_published": True
                }
            ]
        }
    )
    assert res.status_code == 201
    new_v = res.json()
    assert new_v["version_number"] == "3.0"
    assert new_v["version_id"] == "VER-POL-HR-2026-001-03"
    assert new_v["status"] == "ACTIVE"
    assert len(new_v["articles"]) == 1
    assert new_v["articles"][0]["article_id"] == "KB-000002"

    # Verify previous version v2.0 is now SUPERSEDED
    p_check = client.get("/api/v1/policies/POL-HR-2026-001", headers={"Authorization": f"Bearer {manager_token}"}).json()
    v2 = next(v for v in p_check["versions"] if v["version_number"] == "2.0")
    assert v2["status"] == "SUPERSEDED"


def test_create_policy_uses_standard_ids(client, manager_token):
    res = client.post(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "doc_code": "POL-BEN-NEW",
            "title": "New Benefits Policy",
            "category_id": "CAT-001",
            "department_id": "DEP-001",
            "audience": "ALL_EMPLOYEES",
            "initial_version": {
                "version_number": "1.0",
                "status": "ACTIVE",
                "effective_from": "2026-01-01",
                "summary": "Initial version",
                "content": "Policy content",
                "articles": [
                    {
                        "title": "New Benefits Article",
                        "section_number": "1.1",
                        "content": "Article content",
                    }
                ],
            },
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert re.fullmatch(r"POL-HR-\d{4}-\d{3}", data["policy_id"])
    assert data["versions"][0]["version_id"] == f"VER-{data['policy_id']}-01"
    assert data["versions"][0]["articles"][0]["article_id"] == "KB-000002"

