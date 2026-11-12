# HR Request Resolution Data Dictionary

This dictionary describes the generated CSV fields (the SQL schema adds authentication
fields such as `employees.password_hash`; generated `seed.sql` uses a blank hash for
synthetic-only users, so they cannot log in). IDs are immutable strings. CSV booleans are
`True`/`False`; dates use ISO-8601; timestamps are generated in UTC-naive ISO format.
Empty strings represent optional values. No real employee information is used.

## Entities and fields

`Req.` is required/optional. `Unique` identifies a primary key or unique constraint.
Enum values are case-sensitive. An FK must reference a parent key in the same profile.

### Department (`departments`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `dept_id` | string | Yes | `DEP-###` | PK | Non-empty, immutable |
| `name` | string | Yes | Department name | Yes | Non-empty |
| `code` | string | Yes | Short code | Yes | Non-empty |
| `manager_id` | string | No | Employee ID | — | Nullable FK to `employees.emp_id` |
| `location` | string | Yes | Place name | — | Non-empty |
| `created_at` | timestamp | Yes | ISO-8601 | — | Valid timestamp |

### Employee (`employees`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `emp_id` | string | Yes | `EMP-####` | PK | Non-empty, immutable |
| `email` | string | Yes | Synthetic `@company.com` | Yes | Non-empty, valid-looking address |
| `full_name` | string | Yes | Synthetic name | — | Non-empty |
| `department_id` | string | Yes | Department ID | — | FK to `departments.dept_id` |
| `role` | enum | Yes | `EMPLOYEE`, `HR_AGENT`, `HR_MANAGER`, `ADMIN`, `COMPLIANCE_OFFICER` | — | Must be an enum member |
| `employment_type` | enum | Yes | `FULL_TIME`, `PART_TIME`, `CONTRACT`, `INTERN` | — | Must be an enum member |
| `hire_date` | date | Yes | ISO `YYYY-MM-DD` | — | Valid date |
| `status` | enum | Yes | `ACTIVE`, `ON_LEAVE`, `SUSPENDED`, `TERMINATED` | — | Must be an enum member |
| `is_active` | boolean | Yes | `True` / `False` | — | Boolean representation |

### Category (`categories`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `category_id` | string | Yes | `CAT-###` | PK | Non-empty |
| `name` | string | Yes | Category name | Yes | Non-empty |
| `code` | string | Yes | Short category code | Yes | Non-empty |
| `description` | string | Yes | Free text | — | Non-empty |
| `default_priority` | enum | Yes | `LOW`, `MEDIUM`, `HIGH`, `URGENT` | — | Must be an enum member |
| `is_sensitive_default` | boolean | Yes | `True` / `False` | — | Boolean representation |
| `tier` | enum | Yes | `TIER_1`, `TIER_2`, `TIER_3` | — | Must be an enum member |
| `created_at` | timestamp | Yes | ISO-8601 | — | Valid timestamp |

### PolicyDocument (`policy_documents`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `policy_id` | string | Yes | `POL-HR-2026-###` | PK | Matches document-code convention |
| `doc_code` | string | Yes | Same as policy ID | Yes | Must match `policy_id` |
| `title` | string | Yes | Policy title | — | Non-empty |
| `category_id` | string | Yes | Category ID | — | FK to `categories` |
| `department_id` | string | Yes | Department ID | — | FK to `departments` |
| `audience` | enum | Yes | `ALL_EMPLOYEES`, `MANAGERS_ONLY`, `FULL_TIME_ONLY`, `CONTRACTORS`, `HR_ONLY` | — | Must be an enum member |
| `owner_id` | string | Yes | Employee ID | — | FK to `employees` |
| `created_at` | timestamp | Yes | ISO-8601 | — | Valid timestamp |

### PolicyVersion (`policy_versions`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `version_id` | string | Yes | `VER-<policy_id>-##` | PK | References the same policy as `policy_id` |
| `policy_id` | string | Yes | Policy ID | Composite with `version_number` | FK to `policy_documents` |
| `version_number` | string | Yes | `1.0`, `2.0`, etc. | Composite with `policy_id` | Unique per policy |
| `status` | enum | Yes | `DRAFT`, `ACTIVE`, `ARCHIVED`, `SUPERSEDED` | — | Must be an enum member |
| `effective_from` | date | Yes | ISO `YYYY-MM-DD` | — | No later than `effective_to` |
| `effective_to` | date | No | ISO date or empty | — | Optional; if set, not before `effective_from` |
| `summary` | string | Yes | Free text | — | Non-empty |
| `content` | string | Yes | Policy text | — | Non-empty |
| `changelog` | string | No | Free text or empty | — | Optional |
| `approved_by` | string | Yes | Employee ID | — | FK to `employees` |
| `approved_at` | timestamp | Yes | ISO-8601 | — | Valid approval timestamp |

### KnowledgeArticle (`knowledge_articles`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `article_id` | string | Yes | `KB-######` | PK | Non-empty, immutable |
| `policy_version_id` | string | Yes | Version ID | — | FK to `policy_versions` |
| `title` | string | Yes | Article title | — | Non-empty |
| `section_number` | string | Yes | `Sec n.n` | — | Non-empty |
| `content` | string | Yes | Verbatim policy snippet | — | Non-empty |
| `keywords` | string | Yes | Comma-separated words | — | Used for retrieval |
| `audience` | enum | Yes | Same values as `PolicyDocument.audience` | — | Must align with parent policy |
| `is_published` | boolean | Yes | `True` / `False` | — | Only published/current content is eligible for answers |
| `created_at` | timestamp | Yes | ISO-8601 | — | Valid timestamp |

### Ticket (`tickets`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `ticket_id` | string | Yes | `TKT-2026-######` | PK | Immutable and deterministic |
| `tracking_number` | string | Yes | Same as `ticket_id` | Yes | Exact match |
| `employee_id` | string | Yes | Employee ID | — | FK to submitter |
| `category_id` | string | Yes | Category ID | — | FK to category |
| `title` | string | Yes | Request title | — | Non-empty |
| `description` | string | Yes | Request details | — | Non-empty |
| `status` | enum | Yes | `NEW`, `CLARIFICATION_NEEDED`, `IN_PROGRESS`, `ESCALATED`, `RESOLVED`, `CLOSED` | — | Resolution timestamp and record required for resolved states |
| `priority` | enum | Yes | `LOW`, `MEDIUM`, `HIGH`, `URGENT` | — | Drives SLA targets |
| `is_sensitive` | boolean | Yes | `True` / `False` | — | Sensitive cases require restricted routing |
| `confidential_assigned_to` | string | No | Employee ID or empty | — | Nullable FK; eligible confidential handler unless labelled exception |
| `created_at` | timestamp | Yes | ISO-8601 | — | Valid creation time |
| `updated_at` | timestamp | Yes | ISO-8601 | — | At or after creation |
| `resolved_at` | timestamp | No | ISO-8601 or empty | — | At or after creation; required by resolved state |

### Assignment (`assignments`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `assignment_id` | string | Yes | `ASG-######` | PK | Non-empty |
| `ticket_id` | string | Yes | Ticket ID | — | FK to ticket |
| `assigned_to_id` | string | Yes | Employee ID | — | FK to assignee |
| `assigned_by_id` | string | Yes | Employee ID | — | FK to assigning actor |
| `tier` | enum | Yes | `TIER_1`, `TIER_2`, `TIER_3` | — | Must be an enum member |
| `reason` | string | Yes | Routing explanation | — | Non-empty |
| `assigned_at` | timestamp | Yes | ISO-8601 | — | At or after ticket creation |
| `unassigned_at` | timestamp | No | ISO-8601 or empty | — | At or after assignment |
| `is_active` | boolean | Yes | `True` / `False` | — | Exactly one active assignment per generated ticket |

### SLA (`slas`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `sla_id` | string | Yes | `SLA-######` | PK | Non-empty |
| `ticket_id` | string | Yes | Ticket ID | Yes | FK; one SLA per ticket |
| `priority` | enum | Yes | `LOW`, `MEDIUM`, `HIGH`, `URGENT` | — | Must match ticket |
| `business_hours_limit` | integer | Yes | Business hours | — | `4`, `8`, `24`, or `48` by priority |
| `response_due_at` | timestamp | Yes | ISO-8601 | — | Derived from priority response target and working calendar |
| `resolution_due_at` | timestamp | Yes | ISO-8601 | — | Derived from resolution target; exception cases explicitly labelled |
| `first_response_at` | timestamp | No | ISO-8601 or empty | — | Derived from first public agent reply |
| `is_response_breached` | boolean | Yes | `True` / `False` | — | Derived from response timestamp and deadline |
| `is_resolution_breached` | boolean | Yes | `True` / `False` | — | Derived from resolution/snapshot timestamp and deadline |
| `calculated_business_hours` | decimal | Yes | Hours | — | Derived from source timestamps, working hours and holidays |
| `created_at` | timestamp | Yes | ISO-8601 | — | Matches ticket creation |

### Message (`messages`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `message_id` | string | Yes | `MSG-<ticket_id>-###` | PK | Unique, sequential within ticket |
| `ticket_id` | string | Yes | Ticket ID | — | FK to ticket |
| `sender_id` | string | Yes | Employee ID | — | FK to sender |
| `message_type` | enum | Yes | `EMPLOYEE_NOTE`, `AGENT_REPLY`, `INTERNAL_NOTE`, `SYSTEM_EVENT`, `CLARIFICATION_PROMPT` | — | Must be an enum member |
| `content` | string | Yes | Text | — | Non-empty |
| `citations_json` | JSON string | Yes | Array of citation objects | — | Valid JSON; cited version/article must exist and be current |
| `is_internal` | boolean | Yes | `True` / `False` | — | Internal messages are not employee-visible |
| `created_at` | timestamp | Yes | ISO-8601 | — | At or after ticket creation |

### Resolution (`resolutions`)

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `resolution_id` | string | Yes | `RES-######` | PK | Non-empty |
| `ticket_id` | string | Yes | Ticket ID | Yes | FK; one resolution per resolved ticket |
| `resolved_by_id` | string | Yes | Employee ID | — | FK to resolver |
| `resolution_type` | enum | Yes | `POLICY_EXPLANATION`, `MANUAL_CORRECTION`, `ESCALATION_RESOLVED`, `POLICY_EXCEPTION`, `DUPLICATE`, `WITHDRAWN` | — | Must be an enum member |
| `resolution_notes` | string | Yes | Text | — | Non-empty; unsupported-claim exceptions state the claim |
| `root_cause` | string | Yes | Text | — | Non-empty |
| `policy_version_used_id` | string | No | Version ID or empty | — | Nullable FK; must be effective unless labelled obsolete |
| `employee_rating` | integer | Yes | Stars 1-5 | — | Inclusive range 1 through 5 |
| `employee_feedback` | string | Yes | Text | — | Non-empty |
| `resolved_at` | timestamp | Yes | ISO-8601 | — | At or after creation |

### Anomaly (`anomalies`) and ground truth

| Field | Type | Req. | Allowed values / units | Unique | Validation |
|---|---|---:|---|---|---|
| `anomaly_id` | string | Yes | `ANOM-######` | PK | Non-empty |
| `ticket_id` | string | Yes | Ticket ID | — | FK to ticket |
| `anomaly_type` | enum | Yes | `OBSOLETE_POLICY_CITATION`, `SENSITIVE_GENERAL_QUEUE`, `INCORRECT_SLA_CALCULATION`, `UNSUPPORTED_POLICY_CLAIM` | — | Must correspond to the represented exception |
| `severity` | enum | Yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | — | Must be an enum member |
| `description` | string | Yes | Text | — | States the injected issue |
| `status` | enum | Yes | `DETECTED`, `INVESTIGATING`, `RESOLVED`, `FALSE_POSITIVE` | — | Must be an enum member |
| `ground_truth_label` | boolean | Yes | `True` / `False` | — | True for deliberately injected anomaly rows |
| `detected_at` | timestamp | Yes | ISO-8601 | — | At or after ticket creation |
| `ground_truth.csv/json` | separate files | Yes | One row per ticket | — | Never join into operational input features |
| `ground_truth_label` | enum | Yes | `NORMAL`, `ANOMALOUS` | — | Derived from linked anomaly rows |
| `issue_type` | enum | Yes | `ROUTINE`, `AMBIGUOUS`, `SENSITIVE` | — | Derived from source text and routing rules |
| `expected_decision` | enum | Yes | `GENERAL_HR_QUEUE`, `REQUEST_CLARIFICATION`, `CONFIDENTIAL_QUEUE` | — | Deterministic business-rule outcome |
| `anomaly_types` | delimited enum list | Yes | Zero or more anomaly enums | — | Must exactly reconcile to `anomalies.csv` |

`audit_logs.csv` is the append-only event history. It records actor, entity, action,
timestamp and JSON details for ticket creation, routing, clarification, response,
resolution and intentional anomaly injection. It does not overwrite ticket history.

## Relationships, cardinality and lifecycle

| Relationship | Cardinality | Optionality / rule |
|---|---|---|
| Department → Employee | 1:N | Employee requires one department; department may have zero or one manager. |
| Department → PolicyDocument | 1:N | Each policy document belongs to one department. |
| Category → Ticket | 1:N | Each ticket has one category. |
| Category → PolicyDocument | 1:N | Each policy document has one category. |
| Employee → Ticket submitter | 1:N | Each ticket has one submitter. |
| Employee ↔ Ticket assignee | N:M | `assignments` is the bridge and retains reassignment history. |
| Ticket → Assignment | 1:N | Generated baseline has one active assignment; past assignments may remain. |
| Ticket → SLA | 1:1 | SLA is required for every ticket. |
| Ticket → Message | 1:N | Messages retain the conversation in time order. |
| Ticket → Resolution | 1:0..1 | Resolution is optional until terminal resolved/closed state. |
| PolicyDocument → PolicyVersion | 1:N | Effective intervals on a document must not be rewritten; old versions remain. |
| PolicyVersion → KnowledgeArticle | 1:N | Articles cite one immutable version; current answers use effective published versions. |
| PolicyVersion → Resolution | 1:N | Resolution citation is optional and must be effective unless anomaly-labelled. |
| Ticket → Anomaly / AuditLog | 1:N | Exceptions and state events are explicit records. |

Lifecycle rules: tickets begin `NEW` or `CLARIFICATION_NEEDED`; clarification emits a
prompt event; first public agent reply records response timing; resolution requires a
resolution record and `resolved_at`. Sensitive tickets must route to a manager or
compliance officer with a restricted assignment. Policy versions are immutable once
published and selected by effective date and audience. SLA clocks are 09:00-17:00,
Monday-Friday, excluding the configured fixed holidays.

The `assignments` bridge implements the ticket/employee many-to-many relation; other
generated relations are one-to-many or optional one-to-one, so no additional bridge
table is required.
