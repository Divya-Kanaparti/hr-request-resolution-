# Database Data Dictionary

Comprehensive schema documentation for all 11 core entities, audit logs, and anomaly detection records.

---

## 1. `departments`
Stores organizational departments.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `dept_id` | VARCHAR(32) | NO | PK | - | Deterministic department ID (e.g. `DEP-001`) |
| `name` | VARCHAR(120) | NO | UK | - | Department name (e.g. Engineering) |
| `code` | VARCHAR(32) | NO | UK | - | Short code (e.g. `ENG`) |
| `manager_id` | VARCHAR(32) | YES | FK | NULL | Foreign key to `employees.emp_id` |
| `location` | VARCHAR(120) | NO | - | 'Headquarters' | Facility or building location |
| `created_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Record creation timestamp |

---

## 2. `employees`
Stores employee profiles, hashed credentials, and system roles.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `emp_id` | VARCHAR(32) | NO | PK | - | Deterministic employee ID (e.g. `EMP-0001`) |
| `email` | VARCHAR(160) | NO | UK | - | Corporate email address |
| `password_hash` | VARCHAR(255) | NO | - | - | Bcrypt password hash |
| `full_name` | VARCHAR(120) | NO | - | - | Employee full legal name |
| `department_id` | VARCHAR(32) | NO | FK | - | Foreign key to `departments.dept_id` |
| `role` | ENUM | NO | - | 'EMPLOYEE' | `EMPLOYEE`, `HR_AGENT`, `HR_MANAGER`, `ADMIN`, `COMPLIANCE_OFFICER` |
| `employment_type` | ENUM | NO | - | 'FULL_TIME' | `FULL_TIME`, `PART_TIME`, `CONTRACT`, `INTERN` |
| `hire_date` | DATE | NO | - | - | Date employee joined company |
| `status` | ENUM | NO | - | 'ACTIVE' | `ACTIVE`, `ON_LEAVE`, `SUSPENDED`, `TERMINATED` |
| `is_active` | BOOLEAN | NO | - | TRUE | Whether login is enabled |
| `created_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Account creation timestamp |

---

## 3. `categories`
Intake categories for HR requests.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `category_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `CAT-001`) |
| `name` | VARCHAR(100) | NO | UK | - | Category title (e.g. Benefits) |
| `code` | VARCHAR(32) | NO | UK | - | Category code (e.g. `BEN`) |
| `description` | TEXT | YES | - | NULL | Scope and description |
| `default_priority`| ENUM | NO | - | 'MEDIUM' | Default priority (`LOW`, `MEDIUM`, `HIGH`, `URGENT`) |
| `is_sensitive_default`| BOOLEAN | NO | - | FALSE | Whether tickets in category default to confidential |
| `tier` | ENUM | NO | - | 'TIER_1' | Handling support tier (`TIER_1`, `TIER_2`, `TIER_3`) |
| `created_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Creation timestamp |

---

## 4. `policy_documents`
Master policy headers.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `policy_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `POL-001`) |
| `doc_code` | VARCHAR(40) | NO | UK | - | Document code (e.g. `POL-BEN-01`) |
| `title` | VARCHAR(200) | NO | - | - | Official policy title |
| `category_id` | VARCHAR(32) | NO | FK | - | Foreign key to `categories.category_id` |
| `department_id` | VARCHAR(32) | NO | FK | - | Foreign key to `departments.dept_id` |
| `audience` | ENUM | NO | - | 'ALL_EMPLOYEES'| `ALL_EMPLOYEES`, `MANAGERS_ONLY`, `FULL_TIME_ONLY`, `CONTRACTORS`, `HR_ONLY` |
| `owner_id` | VARCHAR(32) | NO | FK | - | Foreign key to `employees.emp_id` |
| `created_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Document record timestamp |

---

## 5. `policy_versions`
Versioned revisions with effective dates and approval tracking.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `version_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `VER-001`) |
| `policy_id` | VARCHAR(32) | NO | FK | - | Foreign key to `policy_documents.policy_id` |
| `version_number` | VARCHAR(16) | NO | - | - | Version string (e.g. '1.0', '2.0') |
| `status` | ENUM | NO | - | 'DRAFT' | `DRAFT`, `ACTIVE`, `ARCHIVED`, `SUPERSEDED` |
| `effective_from` | DATE | NO | - | - | Date policy takes legal effect |
| `effective_to` | DATE | YES | - | NULL | Expiration / sunset date |
| `summary` | TEXT | NO | - | - | Executive summary |
| `content` | MEDIUMTEXT | NO | - | - | Full legal policy text |
| `changelog` | TEXT | YES | - | NULL | Changes since prior version |
| `approved_by` | VARCHAR(32) | YES | FK | NULL | Foreign key to `employees.emp_id` |
| `approved_at` | TIMESTAMP | YES | - | NULL | Approval timestamp |

---

## 6. `knowledge_articles`
Indexed atomic sections for RAG semantic search.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `article_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `ART-0001`) |
| `policy_version_id`| VARCHAR(32)| NO | FK | - | Foreign key to `policy_versions.version_id` |
| `title` | VARCHAR(220) | NO | - | - | Section headline |
| `section_number` | VARCHAR(32) | NO | - | - | Formal section (e.g. 'Sec 2.1') |
| `content` | MEDIUMTEXT | NO | - | - | Article text content |
| `keywords` | VARCHAR(500) | YES | - | NULL | Comma-delimited keywords |
| `audience` | ENUM | NO | - | 'ALL_EMPLOYEES'| Target audience restriction |
| `is_published` | BOOLEAN | NO | - | TRUE | Whether available in Q&A |

---

## 7. `tickets`
The core HR request entity.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `ticket_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `TCK-00001`) |
| `tracking_number` | VARCHAR(48) | NO | UK | - | Tracking string (e.g. `REQ-2026-0001`) |
| `employee_id` | VARCHAR(32) | NO | FK | - | Submitter foreign key |
| `category_id` | VARCHAR(32) | NO | FK | - | Category foreign key |
| `title` | VARCHAR(220) | NO | - | - | Ticket title |
| `description` | MEDIUMTEXT | NO | - | - | Inquiry narrative |
| `status` | ENUM | NO | - | 'NEW' | `NEW`, `CLARIFICATION_NEEDED`, `IN_PROGRESS`, `ESCALATED`, `RESOLVED`, `CLOSED` |
| `priority` | ENUM | NO | - | 'MEDIUM' | `LOW`, `MEDIUM`, `HIGH`, `URGENT` |
| `is_sensitive` | BOOLEAN | NO | - | FALSE | Confidential flag |
| `confidential_assigned_to`| VARCHAR(32)| YES | FK | NULL | Restricted confidential HR assignee |
| `created_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Intake timestamp |
| `updated_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Last modified timestamp |
| `resolved_at` | TIMESTAMP | YES | - | NULL | Resolution completion timestamp |

---

## 8. `assignments`
Ticket routing and tier assignment log.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `assignment_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `ASG-00001`) |
| `ticket_id` | VARCHAR(32) | NO | FK | - | Ticket foreign key |
| `assigned_to_id` | VARCHAR(32) | NO | FK | - | Assigned agent employee ID |
| `assigned_by_id` | VARCHAR(32) | NO | FK | - | Assigning user employee ID |
| `tier` | ENUM | NO | - | 'TIER_1' | Handling tier (`TIER_1`, `TIER_2`, `TIER_3`) |
| `reason` | VARCHAR(255) | YES | - | NULL | Assignment / reassignment reason |
| `assigned_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Time assignment created |
| `unassigned_at` | TIMESTAMP | YES | - | NULL | Time assignment transitioned |
| `is_active` | BOOLEAN | NO | - | TRUE | Whether currently active |

---

## 9. `slas`
Business-hours Service Level Agreement monitoring.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `sla_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `SLA-00001`) |
| `ticket_id` | VARCHAR(32) | NO | FK, UK | - | Associated ticket |
| `priority` | ENUM | NO | - | 'MEDIUM' | SLA priority level |
| `business_hours_limit`| INT | NO | - | 24 | Maximum allowed business hours |
| `response_due_at` | TIMESTAMP | NO | - | - | Deadline for first response |
| `resolution_due_at`| TIMESTAMP | NO | - | - | Deadline for ticket resolution |
| `first_response_at` | TIMESTAMP | YES | - | NULL | Actual agent response timestamp |
| `is_response_breached`| BOOLEAN | NO | - | FALSE | Whether response was overdue |
| `is_resolution_breached`| BOOLEAN| NO | - | FALSE | Whether resolution was overdue |
| `calculated_business_hours`| DECIMAL(6,2)| NO | - | 0.00 | Exact business hours elapsed |

---

## 10. `messages`
Conversation thread and internal notes.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `message_id` | VARCHAR(32) | NO | PK | - | Message ID (e.g. `MSG-00001`) |
| `ticket_id` | VARCHAR(32) | NO | FK | - | Ticket foreign key |
| `sender_id` | VARCHAR(32) | NO | FK | - | Sender employee ID |
| `message_type` | ENUM | NO | - | - | `EMPLOYEE_NOTE`, `AGENT_REPLY`, `INTERNAL_NOTE`, `SYSTEM_EVENT`, `CLARIFICATION_PROMPT` |
| `content` | MEDIUMTEXT | NO | - | - | Message content |
| `citations_json` | JSON | YES | - | NULL | Policy citation objects |
| `is_internal` | BOOLEAN | NO | - | FALSE | If TRUE, hidden from standard employees |
| `created_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Message timestamp |

---

## 11. `resolutions`
Formal resolution record and employee feedback.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `resolution_id` | VARCHAR(32) | NO | PK | - | Resolution ID (e.g. `RES-00001`) |
| `ticket_id` | VARCHAR(32) | NO | FK, UK | - | Resolved ticket |
| `resolved_by_id` | VARCHAR(32) | NO | FK | - | Resolving agent employee ID |
| `resolution_type`| ENUM | NO | - | 'POLICY_EXPLANATION'| Resolution classification |
| `resolution_notes`| MEDIUMTEXT | NO | - | - | Detailed resolution findings |
| `root_cause` | VARCHAR(255) | YES | - | NULL | Root cause categorization |
| `policy_version_used_id`| VARCHAR(32)| YES | FK | NULL | Policy version cited |
| `employee_rating`| TINYINT | YES | - | NULL | Employee rating (1 to 5) |
| `employee_feedback`| TEXT | YES | - | NULL | Written feedback from submitter |
| `resolved_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Resolution timestamp |

---

## 12. `audit_logs`
Immutable event tracking for system mutations.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `audit_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `AUD-00001`) |
| `entity_type` | VARCHAR(64) | NO | - | - | Entity modified (e.g. `TICKET`, `POLICY`) |
| `entity_id` | VARCHAR(32) | NO | - | - | ID of affected entity |
| `action` | VARCHAR(64) | NO | - | - | Action name (e.g. `CREATE_TICKET`, `RESOLVE_TICKET`) |
| `actor_id` | VARCHAR(32) | YES | FK | NULL | Operating user ID |
| `details_json` | JSON | YES | - | NULL | Mutation payload metadata |
| `created_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Audit log timestamp |

---

## 13. `anomaly_records`
Detected and injected compliance anomalies.

| Column | Type | Nullable | Key | Default | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `anomaly_id` | VARCHAR(32) | NO | PK | - | Deterministic ID (e.g. `ANOM-00001`) |
| `ticket_id` | VARCHAR(32) | NO | FK | - | Associated ticket ID |
| `anomaly_type` | ENUM | NO | - | - | `OBSOLETE_POLICY_CITATION`, `SENSITIVE_GENERAL_QUEUE`, `INCORRECT_SLA_CALCULATION`, `UNSUPPORTED_POLICY_CLAIM` |
| `severity` | ENUM | NO | - | 'HIGH' | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `detected_at` | TIMESTAMP | YES | - | CURRENT_TIMESTAMP | Detection timestamp |
| `description` | TEXT | NO | - | - | Diagnostic description |
| `status` | ENUM | NO | - | 'DETECTED' | `DETECTED`, `INVESTIGATING`, `RESOLVED`, `FALSE_POSITIVE` |
| `ground_truth_label`| BOOLEAN | NO | - | TRUE | Whether verified ground truth anomaly |

