"""
Authentication and Authorization Test Suite
"""
import pytest

def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "employee@company.com",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "employee@company.com"
    assert data["user"]["role"] == "EMPLOYEE"

def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "employee@company.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_login_swagger_form(client):
    res = client.post("/api/v1/auth/login", data={
        "username": "manager@company.com",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "HR_MANAGER"

def test_register_employee_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "new.hire@company.com",
        "password": "Password123!",
        "full_name": "New Hire",
        "department_id": "DEP-002",
        "role": "EMPLOYEE"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == "new.hire@company.com"

def test_register_duplicate_email(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "employee@company.com",
        "password": "Password123!",
        "full_name": "Duplicate User",
        "department_id": "DEP-001"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

def test_get_current_user_profile(client, employee_token):
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {employee_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["emp_id"] == "EMP-TEST-01"
    assert data["role"] == "EMPLOYEE"

def test_unauthenticated_request_rejected(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

