# REST API Reference Documentation

**Base URL**: `http://localhost:8000/api/v1`  
**Interactive Swagger UI**: `http://localhost:8000/docs`  
**Authentication**: Bearer JWT Token (`Authorization: Bearer <token>`)

---

## 1. Authentication Endpoints

### 1.1 Login
- **URL**: `POST /auth/login`
- **Description**: Authenticate with corporate email and password. Compatible with standard JSON body or OAuth2 form-data for Swagger Authorize.
- **Request Body**:
```json
{
  "email": "sarah.agent@company.com",
  "password": "Password123!"
}
```
- **Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "user": {
    "emp_id": "EMP-0003",
    "email": "sarah.agent@company.com",
    "full_name": "Sarah Jenkins",
    "department_id": "DEP-001",
    "role": "HR_AGENT",
    "employment_type": "FULL_TIME",
    "status": "ACTIVE"
  }
}
```

### 1.2 Get Current User
- **URL**: `GET /auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**: Current user profile.

---

## 2. Tickets & Workflow Endpoints

### 2.1 List Tickets
- **URL**: `GET /tickets`
- **Query Parameters**:
  - `status`: Optional filter (`NEW`, `CLARIFICATION_NEEDED`, `IN_PROGRESS`, `ESCALATED`, `RESOLVED`, `CLOSED`)
  - `category_id`: Optional filter
  - `priority`: Optional filter (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
  - `is_sensitive`: Optional boolean filter
  - `search`: Search query string
- **Access**: Employees only see tickets they authored; HR agents see general queue; Managers & Compliance see all.

### 2.2 Submit HR Request
- **URL**: `POST /tickets`
- **Description**: Submits ticket. Triggers AI classification, ambiguity heuristics, priority assignment, SLA deadline calculation, and confidential routing if triggers detected.
- **Request Body**:
```json
{
  "title": "PTO rollover into 2026 calendar year",
  "description": "How many hours of accrued unused vacation can I carry over into next year before forfeiting?",
  "category_id": "CAT-002",
  "priority": "MEDIUM",
  "is_sensitive": false
}
```
- **Response `201 Created`**: Returns created `TicketResponse` with tracking number.

### 2.3 Get Ticket Details
- **URL**: `GET /tickets/{ticket_id}`
- **Description**: Retrieves ticket details, conversation thread, SLA deadline, and assignment history. Internal notes are hidden from standard employees.

### 2.4 Assign Ticket
- **URL**: `POST /tickets/{ticket_id}/assign`
- **Roles**: `HR_AGENT`, `HR_MANAGER`, `ADMIN`, `COMPLIANCE_OFFICER`
- **Request Body**:
```json
{
  "assigned_to_id": "EMP-0003",
  "tier": "TIER_1",
  "reason": "Direct triage assignment"
}
```

### 2.5 Escalate Ticket
- **URL**: `POST /tickets/{ticket_id}/escalate`
- **Roles**: `HR_AGENT`, `HR_MANAGER`, `ADMIN`
- **Request Body**:
```json
{
  "target_tier": "TIER_2",
  "escalation_reason": "Complex exception requiring benefits specialist review"
}
```

### 2.6 Resolve Ticket
- **URL**: `POST /tickets/{ticket_id}/resolve`
- **Roles**: `HR_AGENT`, `HR_MANAGER`, `ADMIN`
- **Request Body**:
```json
{
  "resolution_type": "POLICY_EXPLANATION",
  "resolution_notes": "Employee informed that maximum 40 hours of unused PTO rolls over per Section 1.3.",
  "root_cause": "Policy rollover question",
  "policy_version_used_id": "VER-002-2"
}
```

### 2.7 Post Message / Reply
- **URL**: `POST /tickets/{ticket_id}/messages`
- **Request Body**:
```json
{
  "content": "Thank you. I have confirmed your PTO balance.",
  "message_type": "AGENT_REPLY",
  "is_internal": false
}
```

### 2.8 Rate Resolution
- **URL**: `POST /tickets/{ticket_id}/rate`
- **Access**: Ticket author only
- **Request Body**:
```json
{
  "employee_rating": 5,
  "employee_feedback": "Fast and helpful response!"
}
```

---

## 3. RAG and Policy Intelligence

### 3.1 Ask Policy Question
- **URL**: `POST /rag/ask`
- **Request Body**:
```json
{
  "query": "How many hours of PTO can I roll over into next year?",
  "top_k": 3
}
```
- **Response `200 OK`**:
```json
{
  "query": "How many hours of PTO can I roll over into next year?",
  "answer": "According to policy Paid Time Off and Leave Administration Policy (POL-LEV-01, Version 2.0, Section Sec 1.3):\n\nRollover is capped at 40 hours as of December 31st each year...",
  "citations": [
    {
      "policy_doc_code": "POL-LEV-01",
      "policy_title": "Paid Time Off and Leave Administration Policy",
      "version_number": "2.0",
      "section_number": "Sec 1.3",
      "article_title": "PTO Accrual Schedule and Maximum Rollover",
      "quote": "Rollover is capped at 40 hours as of December 31st each year.",
      "relevance_score": 0.88
    }
  ],
  "confidence_score": 0.95,
  "model_used": "DeterministicPolicyEngine"
}
```

---

## 4. Anomaly Radar & Compliance

### 4.1 List Anomalies
- **URL**: `GET /anomalies`
- **Roles**: `ADMIN`, `COMPLIANCE_OFFICER`

### 4.2 Trigger Comprehensive Scan
- **URL**: `POST /anomalies/scan`
- **Description**: Scans all tickets for Obsolete Policy Citations, Sensitive Cases in General Queue, Incorrect Business-Hours SLAs, and Unsupported Claims.

### 4.3 Resolve Anomaly
- **URL**: `PUT /anomalies/{anomaly_id}/resolve`
- **Request Body**:
```json
{
  "status": "RESOLVED",
  "resolution_comment": "Re-opened ticket and cited active Policy Version 2.0."
}
```

---

## 5. Analytics & SLA Monitoring

- `GET /analytics/summary`: Dashboard KPI card metrics.
- `GET /analytics/category-trends`: Ticket distribution by category.
- `GET /analytics/agent-workload`: Agent active workloads and satisfaction ratings.
- `POST /sla/check-breaches`: Batch check for SLA breaches.
- `GET /audit`: Immutable audit log query.
- `GET /health`: System health and MySQL database connection status.

