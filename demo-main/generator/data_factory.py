"""Reproducible, source-derived synthetic HR dataset generation."""
import hashlib
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from .generate_data import (
        CATEGORIES_SPEC,
        DEPARTMENTS_SPEC,
        FIRST_NAMES,
        LAST_NAMES,
        RANDOM_SEED,
        SAMPLE_TOPICS,
        AMBIGUOUS_QUERIES,
        write_csv,
    )
except ImportError:
    from generate_data import (
        CATEGORIES_SPEC,
        DEPARTMENTS_SPEC,
        FIRST_NAMES,
        LAST_NAMES,
        RANDOM_SEED,
        SAMPLE_TOPICS,
        AMBIGUOUS_QUERIES,
        write_csv,
    )


PRIORITY_SLA = {
    "URGENT": (1, 4),
    "HIGH": (2, 8),
    "MEDIUM": (4, 24),
    "LOW": (8, 48),
}
HOLIDAYS = {(1, 1), (5, 1), (7, 4), (12, 25), (12, 26)}
ANOMALY_TYPES = (
    "OBSOLETE_POLICY_CITATION",
    "SENSITIVE_GENERAL_QUEUE",
    "INCORRECT_SLA_CALCULATION",
    "UNSUPPORTED_POLICY_CLAIM",
)


def _is_workday(timestamp):
    return timestamp.weekday() < 5 and (timestamp.month, timestamp.day) not in HOLIDAYS


def add_business_hours(start, hours):
    current = start
    while not _is_workday(current):
        current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    if current.hour < 9:
        current = current.replace(hour=9, minute=0, second=0, microsecond=0)
    elif current.hour >= 17:
        current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        while not _is_workday(current):
            current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    remaining = round(hours * 60)
    while remaining > 0:
        end_of_day = current.replace(hour=17, minute=0, second=0, microsecond=0)
        minutes_today = int((end_of_day - current).total_seconds() / 60)
        if minutes_today <= 0:
            current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            while not _is_workday(current):
                current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        elif remaining <= minutes_today:
            current += timedelta(minutes=remaining)
            remaining = 0
        else:
            remaining -= minutes_today
            current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            while not _is_workday(current):
                current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    return current


def business_hours_between(start, end):
    if start >= end:
        return 0.0
    current = start
    total_minutes = 0
    while current < end:
        if not _is_workday(current):
            current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            continue
        if current.hour < 9:
            current = current.replace(hour=9, minute=0, second=0, microsecond=0)
        elif current.hour >= 17:
            current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            continue
        day_end = current.replace(hour=17, minute=0, second=0, microsecond=0)
        total_minutes += max(0, int((min(end, day_end) - current).total_seconds() / 60))
        current = (current + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    return round(total_minutes / 60, 2)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    escaped = str(value).replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("'", "''")
    return f"'{escaped}'"


def _write_sql_seed(output, exports):
    table_order = (
        "departments", "employees", "categories", "policy_documents",
        "policy_versions", "knowledge_articles", "tickets", "assignments",
        "slas", "messages", "resolutions", "anomalies", "audit_logs",
    )
    table_names = {"anomalies": "anomaly_records"}
    bool_fields = {
        "is_active", "is_sensitive_default", "is_sensitive", "is_published",
        "is_internal", "is_response_breached", "is_resolution_breached",
        "ground_truth_label",
    }
    nullable_fields = {
        "manager_id", "effective_to", "changelog", "confidential_assigned_to",
        "resolved_at", "unassigned_at", "first_response_at",
        "policy_version_used_id", "employee_feedback", "actor_id",
    }
    sql_path = output / "seed.sql"
    with sql_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(
            "-- Deterministic generated dataset seed. Synthetic employee accounts have "
            "blank password hashes; apply database/seed.sql for demo logins.\n"
            "USE hr_request_resolution;\n"
        )
        for table in table_order:
            rows = exports[table]
            db_table = table_names.get(table, table)
            columns = list(rows[0])
            if table == "employees":
                columns.append("password_hash")
            for start in range(0, len(rows), 250):
                batch = rows[start:start + 250]
                stream.write(
                    f"\nINSERT IGNORE INTO `{db_table}` "
                    f"({', '.join(f'`{name}`' for name in columns)}) VALUES\n"
                )
                for row_index, row in enumerate(batch):
                    values = []
                    for column in columns:
                        if column == "password_hash":
                            values.append("''")
                        elif row.get(column, "") == "" and column in nullable_fields:
                            values.append("NULL")
                        elif column in bool_fields:
                            values.append("1" if str(row.get(column, "")).lower() == "true" else "0")
                        else:
                            values.append(_sql_literal(row.get(column, "")))
                    delimiter = "," if row_index < len(batch) - 1 else ";"
                    stream.write(f"({', '.join(values)}){delimiter}\n")
    return sql_path


def generate_dataset(
    profile="starter",
    output_dir="data",
    seed=RANDOM_SEED,
    ticket_count=None,
    message_count=None,
    article_count=150,
):
    if profile not in ("starter", "full"):
        raise ValueError(f"Unknown profile: {profile}")
    full = profile == "full"
    ticket_count = ticket_count if ticket_count is not None else (5000 if full else 250)
    message_count = message_count if message_count is not None else (20000 if full else 1000)
    employee_count = 500 if full else 50
    if ticket_count < 1 or article_count < 1 or message_count < ticket_count:
        raise ValueError("Counts must be positive and message_count must cover every ticket")

    random.seed(seed)
    output = Path(output_dir) / profile
    truth_dir = Path(output_dir) / "ground_truth" / profile
    output.mkdir(parents=True, exist_ok=True)
    truth_dir.mkdir(parents=True, exist_ok=True)

    departments = [
        {
            "dept_id": dept_id,
            "name": name,
            "code": code,
            "manager_id": "",
            "location": location,
            "created_at": "2023-01-01T00:00:00",
        }
        for dept_id, name, code, location in DEPARTMENTS_SPEC
    ]

    employees = [
        {
            "emp_id": "EMP-0001", "email": "admin@company.com",
            "full_name": "System Administrator", "department_id": "DEP-006",
            "role": "ADMIN", "employment_type": "FULL_TIME",
            "hire_date": "2021-01-10", "status": "ACTIVE", "is_active": True,
        },
        {
            "emp_id": "EMP-0002", "email": "emily.manager@company.com",
            "full_name": "Emily Watson", "department_id": "DEP-001",
            "role": "HR_MANAGER", "employment_type": "FULL_TIME",
            "hire_date": "2021-03-15", "status": "ACTIVE", "is_active": True,
        },
        {
            "emp_id": "EMP-0003", "email": "sarah.agent@company.com",
            "full_name": "Sarah Jenkins", "department_id": "DEP-001",
            "role": "HR_AGENT", "employment_type": "FULL_TIME",
            "hire_date": "2022-02-01", "status": "ACTIVE", "is_active": True,
        },
        {
            "emp_id": "EMP-0004", "email": "rachel.compliance@company.com",
            "full_name": "Rachel Vance", "department_id": "DEP-005",
            "role": "COMPLIANCE_OFFICER", "employment_type": "FULL_TIME",
            "hire_date": "2021-06-10", "status": "ACTIVE", "is_active": True,
        },
        {
            "emp_id": "EMP-0005", "email": "john.doe@company.com",
            "full_name": "John Doe", "department_id": "DEP-002",
            "role": "EMPLOYEE", "employment_type": "FULL_TIME",
            "hire_date": "2022-05-18", "status": "ACTIVE", "is_active": True,
        },
        {
            "emp_id": "EMP-0006", "email": "it.partner@company.com",
            "full_name": "IT Operations Partner", "department_id": "DEP-006",
            "role": "IT_OPERATIONS_PARTNER", "employment_type": "FULL_TIME",
            "hire_date": "2022-06-01", "status": "ACTIVE", "is_active": True,
        },
    ]
    roles = (
        ["EMPLOYEE"] * 85 + ["HR_AGENT"] * 8 + ["HR_MANAGER"] * 4
        + ["ADMIN"] * 2 + ["COMPLIANCE_OFFICER", "IT_OPERATIONS_PARTNER"]
    )
    employment_types = ["FULL_TIME"] * 3 + ["CONTRACT", "PART_TIME"]
    for index in range(7, employee_count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        employees.append({
            "emp_id": f"EMP-{index:04d}",
            "email": f"{first.lower()}.{last.lower()}{index}@company.com",
            "full_name": f"{first} {last}",
            "department_id": random.choice(DEPARTMENTS_SPEC)[0],
            "role": random.choice(roles),
            "employment_type": random.choice(employment_types),
            "hire_date": (date(2022, 1, 1) + timedelta(days=random.randint(0, 1000))).isoformat(),
            "status": "ACTIVE",
            "is_active": True,
        })

    categories = [
        {
            "category_id": category_id, "name": name, "code": code,
            "description": description, "default_priority": priority,
            "is_sensitive_default": sensitive, "tier": tier,
            "created_at": "2023-01-01T00:00:00",
        }
        for category_id, name, code, description, priority, sensitive, tier in CATEGORIES_SPEC
    ]

    policy_documents = []
    policy_versions = []
    version_by_category = {}
    version_by_id = {}
    documents_by_id = {}
    for index in range(1, 31):
        category_id = list(SAMPLE_TOPICS)[(index - 1) % len(SAMPLE_TOPICS)]
        category_code = next(item[2] for item in CATEGORIES_SPEC if item[0] == category_id)
        policy_id = f"POL-HR-2026-{index:03d}"
        audience = "ALL_EMPLOYEES" if not version_by_category.get(category_id) else random.choices(
            ["ALL_EMPLOYEES", "MANAGERS_ONLY", "FULL_TIME_ONLY", "CONTRACTORS", "HR_ONLY"],
            weights=[70, 10, 10, 5, 5],
        )[0]
        title = f"Corporate Policy on {SAMPLE_TOPICS[category_id][(index - 1) % len(SAMPLE_TOPICS[category_id])][0]}"
        document = {
            "policy_id": policy_id, "doc_code": policy_id, "title": title,
            "category_id": category_id, "department_id": "DEP-001",
            "audience": audience, "owner_id": "EMP-0002",
            "created_at": "2023-01-01T00:00:00",
        }
        policy_documents.append(document)
        documents_by_id[policy_id] = document
        for version_no, status, effective_from, effective_to in (
            ("01", "SUPERSEDED", "2023-01-01", "2024-12-31"),
            ("02", "ACTIVE", "2025-01-01", ""),
        ):
            version_id = f"VER-{policy_id}-{version_no}"
            version = {
                "version_id": version_id, "policy_id": policy_id,
                "version_number": "1.0" if version_no == "01" else "2.0", "status": status,
                "effective_from": effective_from, "effective_to": effective_to,
                "summary": f"{'Legacy' if version_no == '01' else 'Active'} policy for {title}.",
                "content": (
                    f"Historical guidelines regarding {title}; superseded on 2025-01-01."
                    if version_no == "01"
                    else f"Current approved guidelines governing {title}. "
                         "For eligibility, contact Human Resources through the HR portal."
                ),
                "changelog": "Updated policy guidance." if version_no == "02" else "",
                "approved_by": "EMP-0002",
                "approved_at": f"{effective_from}T00:00:00",
            }
            policy_versions.append(version)
            version_by_id[version_id] = version
            if version_no == "02":
                version_by_category.setdefault(category_id, []).append(version_id)

    knowledge_articles = []
    articles_by_version = {}
    active_version_ids = [
        version_id
        for versions in version_by_category.values()
        for version_id in versions
    ]
    for index in range(1, article_count + 1):
        version_id = active_version_ids[(index - 1) % len(active_version_ids)]
        version = version_by_id[version_id]
        document = next(doc for doc in policy_documents if doc["policy_id"] == version["policy_id"])
        section = f"Sec {(index % 8) + 1}.{(index % 5) + 1}"
        article = {
            "article_id": f"KB-{index:06d}",
            "policy_version_id": version_id,
            "title": f"{document['title']} - Operational Guidelines {section}",
            "section_number": section,
            "content": (
                f"Under {document['title']} ({document['doc_code']}), submit the request through the HR portal. "
                "Human Resources verifies eligibility and processes complete requests within 2 to 5 business days."
            ),
            "keywords": f"{document['doc_code']}, eligibility, request, process",
            "audience": document["audience"],
            "is_published": True,
            "created_at": "2025-01-01T00:00:00",
        }
        knowledge_articles.append(article)
        articles_by_version.setdefault(version_id, []).append(article)

    tickets = []
    assignments = []
    slas = []
    resolutions = []
    messages = []
    anomalies = []
    audit_logs = []
    ground_truth = []
    message_counts = {}
    hr_agents = [employee for employee in employees if employee["role"] in ("HR_AGENT", "HR_MANAGER")]
    general_agents = [employee for employee in employees if employee["role"] == "HR_AGENT"]
    confidential_agents = [employee for employee in employees if employee["role"] in ("HR_MANAGER", "COMPLIANCE_OFFICER")]
    operations_agents = [employee for employee in employees if employee["role"] == "IT_OPERATIONS_PARTNER"]
    regular_employees = [employee for employee in employees if employee["role"] == "EMPLOYEE"]
    if not regular_employees or not hr_agents or not general_agents or not confidential_agents or not operations_agents:
        raise ValueError("The selected employee volume did not generate all required actor roles")

    def add_message(ticket_id, sender_id, message_type, content, created_at, citations=None, internal=False):
        sequence = message_counts.get(ticket_id, 0) + 1
        message_counts[ticket_id] = sequence
        messages.append({
            "message_id": f"MSG-{ticket_id}-{sequence:03d}",
            "ticket_id": ticket_id,
            "sender_id": sender_id,
            "message_type": message_type,
            "content": content,
            "citations_json": json.dumps(citations or [], separators=(",", ":")),
            "is_internal": internal,
            "created_at": created_at.isoformat(),
        })

    def add_audit(entity_id, action, actor_id, created_at, details):
        audit_logs.append({
            "audit_id": f"AUD-{len(audit_logs) + 1:07d}",
            "entity_type": "TICKET",
            "entity_id": entity_id,
            "action": action,
            "actor_id": actor_id,
            "details_json": json.dumps(details, sort_keys=True, separators=(",", ":")),
            "created_at": created_at.isoformat(),
        })

    base_time = datetime(2026, 1, 5, 9)
    snapshot_time = datetime(2026, 6, 30, 17)
    for index in range(1, ticket_count + 1):
        ticket_id = f"TKT-2026-{index:06d}"
        is_sensitive = index % 12 == 0
        is_ambiguous = index % 10 == 0 and not is_sensitive
        employee = random.choice(regular_employees)
        if is_sensitive:
            category_id = "CAT-007"
            title, description = random.choice(SAMPLE_TOPICS[category_id])
            priority = "URGENT"
        elif is_ambiguous:
            category_id = random.choice(["CAT-001", "CAT-002", "CAT-003"])
            title, description = random.choice(AMBIGUOUS_QUERIES)
            priority = "MEDIUM"
        else:
            category_id = random.choice(list(SAMPLE_TOPICS)[:-1])
            title, description = random.choice(SAMPLE_TOPICS[category_id])
            priority = next(item[4] for item in CATEGORIES_SPEC if item[0] == category_id)

        created_at = base_time + timedelta(minutes=index * 25)
        if is_ambiguous:
            status = "CLARIFICATION_NEEDED"
        else:
            status = random.choices(
                ["RESOLVED", "IN_PROGRESS", "NEW", "ESCALATED"],
                weights=[70, 18, 7, 5],
            )[0]

        wrong_sensitive_route = is_sensitive and index % 24 == 0
        if is_sensitive and not wrong_sensitive_route:
            assigned_agent = confidential_agents[(index // 12) % len(confidential_agents)]
        elif wrong_sensitive_route:
            assigned_agent = general_agents[(index // 24) % len(general_agents)]
        elif category_id == "CAT-004" and status != "ESCALATED":
            assigned_agent = operations_agents[index % len(operations_agents)]
        elif status == "ESCALATED":
            assigned_agent = next(
                employee for employee in employees if employee["role"] == "HR_MANAGER"
            )
        else:
            assigned_agent = hr_agents[index % len(hr_agents)]
        confidential_assignee = assigned_agent["emp_id"] if is_sensitive and not wrong_sensitive_route else ""

        employee_visible_versions = [
            version_id for version_id in version_by_category[category_id]
            if documents_by_id[version_by_id[version_id]["policy_id"]]["audience"] == "ALL_EMPLOYEES"
        ]
        active_version_id = random.choice(employee_visible_versions)
        policy_id = version_by_id[active_version_id]["policy_id"]
        current_article = (articles_by_version.get(active_version_id) or [None])[0]
        anomaly_types = []
        if wrong_sensitive_route:
            anomaly_types.append("SENSITIVE_GENERAL_QUEUE")
        if index % 30 == 3:
            anomaly_types.append("INCORRECT_SLA_CALCULATION")
        if status == "RESOLVED" and index % 50 == 1:
            anomaly_types.append("OBSOLETE_POLICY_CITATION")
        if status == "RESOLVED" and index % 40 == 4:
            anomaly_types.append("UNSUPPORTED_POLICY_CLAIM")

        resolved_at = add_business_hours(created_at, random.randint(4, 20)) if status == "RESOLVED" else None
        ticket = {
            "ticket_id": ticket_id,
            "tracking_number": ticket_id,
            "employee_id": employee["emp_id"],
            "category_id": category_id,
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "is_sensitive": is_sensitive,
            "confidential_assigned_to": confidential_assignee,
            "created_at": created_at.isoformat(),
            "updated_at": (resolved_at or created_at).isoformat(),
            "resolved_at": resolved_at.isoformat() if resolved_at else "",
        }
        tickets.append(ticket)

        assignments.append({
            "assignment_id": f"ASG-{index:06d}",
            "ticket_id": ticket_id,
            "assigned_to_id": assigned_agent["emp_id"],
            "assigned_by_id": "EMP-0002",
            "tier": "TIER_3" if is_sensitive else (
                "TIER_2" if priority == "HIGH" or status == "ESCALATED" else "TIER_1"
            ),
            "reason": "Sensitive case routing" if is_sensitive else "Category and priority triage",
            "assigned_at": created_at.isoformat(),
            "unassigned_at": "",
            "is_active": True,
        })

        response_hours, resolution_hours = PRIORITY_SLA[priority]
        response_due = add_business_hours(created_at, response_hours)
        expected_resolution_due = add_business_hours(created_at, resolution_hours)
        incorrect_sla = "INCORRECT_SLA_CALCULATION" in anomaly_types
        resolution_due = (
            created_at + timedelta(hours=resolution_hours)
            if incorrect_sla else expected_resolution_due
        )
        first_response_at = (
            add_business_hours(created_at, 0.75)
            if status in ("IN_PROGRESS", "RESOLVED", "ESCALATED") else None
        )
        elapsed_end = resolved_at or snapshot_time
        slas.append({
            "sla_id": f"SLA-{index:06d}",
            "ticket_id": ticket_id,
            "priority": priority,
            "business_hours_limit": resolution_hours,
            "response_due_at": response_due.isoformat(),
            "resolution_due_at": resolution_due.isoformat(),
            "first_response_at": first_response_at.isoformat() if first_response_at else "",
            "is_response_breached": (first_response_at or snapshot_time) > response_due,
            "is_resolution_breached": elapsed_end > resolution_due,
            "calculated_business_hours": business_hours_between(created_at, elapsed_end),
            "created_at": created_at.isoformat(),
        })

        add_message(ticket_id, employee["emp_id"], "EMPLOYEE_NOTE", description, created_at)
        add_audit(ticket_id, "CREATE_TICKET", employee["emp_id"], created_at, {"status": status})
        add_audit(ticket_id, "ASSIGN_TICKET", "EMP-0002", created_at, {
            "assigned_to_id": assigned_agent["emp_id"],
            "tier": assignments[-1]["tier"],
        })
        if status == "ESCALATED":
            add_message(
                ticket_id, assigned_agent["emp_id"], "SYSTEM_EVENT",
                "Ticket escalated to Tier 2 for specialist review.",
                created_at, internal=True,
            )
            add_audit(ticket_id, "ESCALATE_TICKET", "EMP-0002", created_at, {
                "target_tier": "TIER_2",
                "reason": "Specialist review required",
            })
        if is_ambiguous:
            prompt_time = add_business_hours(created_at, 0.1)
            add_message(
                ticket_id, "EMP-0001", "CLARIFICATION_PROMPT",
                "Please provide the missing date, amount, or request details so HR can review your case.",
                prompt_time,
            )
            add_audit(ticket_id, "CLARIFICATION_REQUESTED", "EMP-0001", prompt_time, {
                "reason": "Required request context is missing",
            })

        citation = []
        if current_article:
            citation = [{
                "policy_version_id": active_version_id,
                "policy_id": policy_id,
                "article_id": current_article["article_id"],
                "doc_code": policy_id,
                "version_number": "2.0",
                "section_number": current_article["section_number"],
                "quote": current_article["content"],
            }]
        if first_response_at:
            add_message(
                ticket_id, assigned_agent["emp_id"], "AGENT_REPLY",
                "Your request is under review. HR will confirm the applicable policy and next steps.",
                first_response_at, citation,
            )
            add_audit(ticket_id, "FIRST_RESPONSE", assigned_agent["emp_id"], first_response_at, {})

        if resolved_at:
            if "OBSOLETE_POLICY_CITATION" in anomaly_types:
                used_version_id = f"VER-{policy_id}-01"
                notes = "Resolved using the superseded Policy Version 1.0; this citation is intentionally obsolete."
            elif "UNSUPPORTED_POLICY_CLAIM" in anomaly_types:
                used_version_id = ""
                notes = "Approved request citing an unsupported unlimited remote-work stipend."
            else:
                used_version_id = active_version_id
                notes = (
                    f"Resolved using current policy {policy_id}, version 2.0. "
                    "The employee was given the applicable policy section and next steps."
                )
            resolution = {
                "resolution_id": f"RES-{index:06d}",
                "ticket_id": ticket_id,
                "resolved_by_id": assigned_agent["emp_id"],
                "resolution_type": "POLICY_EXPLANATION",
                "resolution_notes": notes,
                "root_cause": "Routine policy clarification",
                "policy_version_used_id": used_version_id,
                "employee_rating": random.choice([3, 4, 4, 5, 5]),
                "employee_feedback": "Thank you for the response.",
                "resolved_at": resolved_at.isoformat(),
            }
            resolutions.append(resolution)
            add_message(
                ticket_id, assigned_agent["emp_id"], "AGENT_REPLY",
                f"Resolution: {notes}", resolved_at, citation if used_version_id == active_version_id else [],
            )
            add_audit(ticket_id, "RESOLVE_TICKET", assigned_agent["emp_id"], resolved_at, {
                "resolution_id": resolution["resolution_id"],
                "policy_version_used_id": used_version_id,
            })

        for anomaly_type in anomaly_types:
            anomalies.append({
                "anomaly_id": f"ANOM-{len(anomalies) + 1:06d}",
                "ticket_id": ticket_id,
                "anomaly_type": anomaly_type,
                "severity": "CRITICAL" if anomaly_type == "SENSITIVE_GENERAL_QUEUE" else "HIGH",
                "description": f"Intentional synthetic exception: {anomaly_type}",
                "status": "DETECTED",
                "ground_truth_label": True,
                "detected_at": created_at.isoformat(),
            })
            add_audit(ticket_id, "ANOMALY_INJECTED", "EMP-0001", created_at, {
                "issue_type": anomaly_type,
            })

        ground_truth.append({
            "ticket_id": ticket_id,
            "ground_truth_label": "ANOMALOUS" if anomaly_types else "NORMAL",
            "issue_type": "SENSITIVE" if is_sensitive else ("AMBIGUOUS" if is_ambiguous else "ROUTINE"),
            "expected_decision": (
                "CONFIDENTIAL_QUEUE" if is_sensitive
                else ("REQUEST_CLARIFICATION" if is_ambiguous else "GENERAL_HR_QUEUE")
            ),
            "is_sensitive": is_sensitive,
            "is_ambiguous": is_ambiguous,
            "anomaly_types": ";".join(anomaly_types),
            "sla_business_hours_limit": resolution_hours,
            "expected_response_due_at": response_due.isoformat(),
            "expected_resolution_due_at": expected_resolution_due.isoformat(),
        })

    if len(messages) > message_count:
        raise ValueError(
            f"message_count={message_count} is too small for generated workflow events ({len(messages)} required)"
        )

    followup_templates = (
        "I have added the requested supporting details to my request.",
        "HR confirmed receipt and is checking the information provided.",
        "A follow-up was recorded while the request is being reviewed.",
    )
    index = 0
    while len(messages) < message_count:
        ticket = tickets[index % len(tickets)]
        employee = next(person for person in employees if person["emp_id"] == ticket["employee_id"])
        assignment = assignments[index % len(assignments)]
        sequence = message_counts.get(ticket["ticket_id"], 0)
        created_at = datetime.fromisoformat(ticket["created_at"])
        event_time = add_business_hours(created_at, min(6, 1 + sequence * 0.25))
        if sequence % 4 == 3:
            sender_id = assignment["assigned_to_id"]
            message_type = "INTERNAL_NOTE"
            internal = True
        elif sequence % 2:
            sender_id = employee["emp_id"]
            message_type = "EMPLOYEE_NOTE"
            internal = False
        else:
            sender_id = assignment["assigned_to_id"]
            message_type = "AGENT_REPLY"
            internal = False
        add_message(
            ticket["ticket_id"], sender_id, message_type,
            followup_templates[index % len(followup_templates)], event_time, internal=internal,
        )
        index += 1

    exports = {
        "departments": departments,
        "employees": employees,
        "categories": categories,
        "policy_documents": policy_documents,
        "policy_versions": policy_versions,
        "knowledge_articles": knowledge_articles,
        "tickets": tickets,
        "assignments": assignments,
        "slas": slas,
        "resolutions": resolutions,
        "messages": messages,
        "anomalies": anomalies,
        "audit_logs": audit_logs,
    }
    for table, rows in exports.items():
        write_csv(output / f"{table}.csv", rows)
    sql_seed = _write_sql_seed(output, exports)
    write_csv(truth_dir / "ground_truth.csv", ground_truth)
    with (truth_dir / "ground_truth.json").open("w", encoding="utf-8") as stream:
        json.dump(ground_truth, stream, indent=2)
    if profile == "full":
        compatibility_truth_dir = Path(output_dir) / "ground_truth"
        write_csv(compatibility_truth_dir / "ground_truth.csv", ground_truth)
        with (compatibility_truth_dir / "ground_truth.json").open("w", encoding="utf-8") as stream:
            json.dump(ground_truth, stream, indent=2)

    manifest = {
        "profile": profile,
        "seed": seed,
        "baseline_volume": (
            ticket_count == (5000 if full else 250)
            and message_count == (20000 if full else 1000)
            and article_count == 150
        ),
        "synthetic_only": True,
        "external_sources": [],
        "provenance": "Generated in-repository; no real employee or external source data used.",
        "generator": "generator/generate_data.py",
        "record_counts": {table: len(rows) for table, rows in exports.items()},
        "ground_truth": {
            "record_count": len(ground_truth),
            "csv_sha256": _sha256(truth_dir / "ground_truth.csv"),
            "json_sha256": _sha256(truth_dir / "ground_truth.json"),
        },
        "checksums_sha256": {
            **{f"{table}.csv": _sha256(output / f"{table}.csv") for table in exports},
            "seed.sql": _sha256(sql_seed),
        },
    }
    with (output / "source_manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)

    print(
        f"Generated {profile}: {len(tickets)} tickets, {len(messages)} messages, "
        f"{len(knowledge_articles)} knowledge articles, {len(anomalies)} labelled anomalies."
    )
