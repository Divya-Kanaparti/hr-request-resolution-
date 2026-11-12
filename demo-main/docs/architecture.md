# HR Request Resolution System - Architectural Specification

## 1. System Architecture Overview

The HR Request Resolution System is an enterprise-tier web platform engineered to automate employee request intake, policy-backed question answering with exact citations, SLA management using business-hours logic, and compliance anomaly detection.

```
+-----------------------------------------------------------------------------------+
|                                 FRONTEND TIER                                     |
|  - HTML5, CSS3, Vanilla JavaScript (Single Page Architecture & Modular Pages)    |
|  - Role-Aware Routing, Interactive Tables, SLA Status Gauges, RAG AI Assistant    |
+-----------------------------------------------------------------------------------+
                                         │  HTTPS / REST JSON
                                         ▼
+-----------------------------------------------------------------------------------+
|                              BACKEND API TIER (FastAPI)                           |
|  ├── Core: Security (Bcrypt, JWT), RBAC Gatekeeper, Business Hours Engine         |
|  ├── Routes: Auth, Employees, Categories, Tickets, Policies, RAG, SLAs, Analytics|
|  └── Services: Classification, Ambiguity Detection, RAG Citations, Anomaly Radar  |
+-----------------------------------------------------------------------------------+
                     │                                         │
                     ▼                                         ▼
+------------------------------------+    +-----------------------------------------+
|          DATA & ORM TIER           |    |            AI & RAG PIPELINE            |
|  - MySQL 8.0 (InnoDB, utf8mb4)     |    |  - Configurable Gemini 1.5 Flash API    |
|  - SQLAlchemy 2.0 ORM Declarative  |    |  - Sentence-Transformers Local Vectors  |
|  - Immutable Event Audit Trail     |    |  - Active Policy Effective-Date Filtering|
+------------------------------------+    +-----------------------------------------+
```

---

## 2. Core Functional Modules

### 2.1 Role-Based Access Control (RBAC) Matrix

| Resource / Endpoint | `EMPLOYEE` | `HR_AGENT` | `HR_MANAGER` | `ADMIN` | `COMPLIANCE_OFFICER` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Submit Ticket** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **View Own Tickets** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **View General HR Queue** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **View Confidential/Sensitive Cases** | ❌ (Own only) | ❌ (Unless Assigned) | ✅ | ✅ | ✅ |
| **Assign / Escalate Tickets** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Resolve & Cite Policy** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Rate Resolution & Feedback** | ✅ (Submitter) | ❌ | ❌ | ❌ | ❌ |
| **Author Policy Versions** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Execute Anomaly Radar Scan** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Inspect Immutable Audit Logs** | ❌ | ❌ | ❌ | ✅ | ✅ |

### 2.2 Deterministic Business-Hours SLA Engine

Standard clock calculation fails to reflect true corporate working days (e.g. naive 24-hour additions improperly penalize HR teams over weekends or overnight).

The system implements a business hours algorithm:
- **Operating Hours**: 09:00:00 to 17:00:00 (8 business hours per day).
- **Working Days**: Monday (0) through Friday (4).
- **Holidays**: Corporate observed holidays skipped automatically.
- **Priority SLAs**:
  - `URGENT`: 1 business hour response, 4 business hours resolution.
  - `HIGH`: 2 business hours response, 8 business hours resolution (1 business day).
  - `MEDIUM`: 4 business hours response, 24 business hours resolution (3 business days).
  - `LOW`: 8 business hours response, 48 business hours resolution (6 business days).

```
Friday 15:00 (3 PM)  ───►  [2h Friday until 17:00]
                             ├── Saturday: Skipped
                             ├── Sunday: Skipped
                             └── Monday 09:00 + 2h remaining  ───►  Monday 11:00 AM (Resolution Due)
```

### 2.3 RAG Policy Engine with Verbatim Citations

To prevent hallucinations:
1. **Audience Filtering**: Employees only receive knowledge articles valid for their audience group (`ALL_EMPLOYEES` vs `MANAGERS_ONLY`).
2. **Effective Date Validation**: Only versions where `effective_from <= today <= effective_to` (or `effective_to` is NULL) and `status == 'ACTIVE'` are indexed.
3. **Exact Citation Formulation**: Every answer quotes the exact `doc_code`, `version_number`, `section_number`, and literal policy text.

### 2.4 Anomaly Detection System

Monitors four operational anomalies:
1. **`OBSOLETE_POLICY_CITATION`**: A resolution references a superseded or archived version.
2. **`SENSITIVE_GENERAL_QUEUE`**: A ticket with harassment/ethics triggers is left unassigned or placed in the public queue without confidential restriction.
3. **`INCORRECT_SLA_CALCULATION`**: An SLA deadline deviates from true business hours (e.g. calculated with naive calendar hours).
4. **`UNSUPPORTED_POLICY_CLAIM`**: An answer claims an unapproved benefit (e.g., "100% remote stipend unlimited") not present in any active policy document.

