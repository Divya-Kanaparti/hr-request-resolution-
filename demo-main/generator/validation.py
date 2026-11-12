"""Schema, relationship, lifecycle, calculation, label and reproducibility checks."""
import argparse
import csv
import hashlib
import json
import re
import tempfile
from datetime import date, datetime
from pathlib import Path

try:
    from .data_factory import add_business_hours, business_hours_between, generate_dataset
except ImportError:
    from data_factory import add_business_hours, business_hours_between, generate_dataset


TABLE_KEYS = {
    "departments": "dept_id",
    "employees": "emp_id",
    "categories": "category_id",
    "policy_documents": "policy_id",
    "policy_versions": "version_id",
    "knowledge_articles": "article_id",
    "tickets": "ticket_id",
    "assignments": "assignment_id",
    "slas": "sla_id",
    "resolutions": "resolution_id",
    "messages": "message_id",
    "anomalies": "anomaly_id",
    "audit_logs": "audit_id",
}

FOREIGN_KEYS = (
    ("departments", "manager_id", "employees", "emp_id", True),
    ("employees", "department_id", "departments", "dept_id", False),
    ("policy_documents", "category_id", "categories", "category_id", False),
    ("policy_documents", "department_id", "departments", "dept_id", False),
    ("policy_documents", "owner_id", "employees", "emp_id", False),
    ("policy_versions", "policy_id", "policy_documents", "policy_id", False),
    ("policy_versions", "approved_by", "employees", "emp_id", True),
    ("knowledge_articles", "policy_version_id", "policy_versions", "version_id", False),
    ("tickets", "employee_id", "employees", "emp_id", False),
    ("tickets", "category_id", "categories", "category_id", False),
    ("tickets", "confidential_assigned_to", "employees", "emp_id", True),
    ("assignments", "ticket_id", "tickets", "ticket_id", False),
    ("assignments", "assigned_to_id", "employees", "emp_id", False),
    ("assignments", "assigned_by_id", "employees", "emp_id", False),
    ("slas", "ticket_id", "tickets", "ticket_id", False),
    ("messages", "ticket_id", "tickets", "ticket_id", False),
    ("messages", "sender_id", "employees", "emp_id", False),
    ("resolutions", "ticket_id", "tickets", "ticket_id", False),
    ("resolutions", "resolved_by_id", "employees", "emp_id", False),
    ("resolutions", "policy_version_used_id", "policy_versions", "version_id", True),
    ("anomalies", "ticket_id", "tickets", "ticket_id", False),
    ("audit_logs", "actor_id", "employees", "emp_id", True),
)

ENUMS = {
    ("employees", "role"): {"EMPLOYEE", "HR_AGENT", "HR_MANAGER", "ADMIN", "COMPLIANCE_OFFICER", "IT_OPERATIONS_PARTNER"},
    ("employees", "employment_type"): {"FULL_TIME", "PART_TIME", "CONTRACT", "INTERN"},
    ("employees", "status"): {"ACTIVE", "ON_LEAVE", "SUSPENDED", "TERMINATED"},
    ("categories", "default_priority"): {"LOW", "MEDIUM", "HIGH", "URGENT"},
    ("categories", "tier"): {"TIER_1", "TIER_2", "TIER_3"},
    ("policy_documents", "audience"): {"ALL_EMPLOYEES", "MANAGERS_ONLY", "FULL_TIME_ONLY", "CONTRACTORS", "HR_ONLY"},
    ("policy_versions", "status"): {"DRAFT", "ACTIVE", "ARCHIVED", "SUPERSEDED"},
    ("knowledge_articles", "audience"): {"ALL_EMPLOYEES", "MANAGERS_ONLY", "FULL_TIME_ONLY", "CONTRACTORS", "HR_ONLY"},
    ("tickets", "status"): {"NEW", "CLARIFICATION_NEEDED", "IN_PROGRESS", "ESCALATED", "RESOLVED", "CLOSED"},
    ("tickets", "priority"): {"LOW", "MEDIUM", "HIGH", "URGENT"},
    ("assignments", "tier"): {"TIER_1", "TIER_2", "TIER_3"},
    ("slas", "priority"): {"LOW", "MEDIUM", "HIGH", "URGENT"},
    ("messages", "message_type"): {"EMPLOYEE_NOTE", "AGENT_REPLY", "INTERNAL_NOTE", "SYSTEM_EVENT", "CLARIFICATION_PROMPT"},
    ("resolutions", "resolution_type"): {"POLICY_EXPLANATION", "MANUAL_CORRECTION", "ESCALATION_RESOLVED", "POLICY_EXCEPTION", "DUPLICATE", "WITHDRAWN"},
    ("anomalies", "anomaly_type"): {"OBSOLETE_POLICY_CITATION", "SENSITIVE_GENERAL_QUEUE", "INCORRECT_SLA_CALCULATION", "UNSUPPORTED_POLICY_CLAIM"},
    ("anomalies", "severity"): {"LOW", "MEDIUM", "HIGH", "CRITICAL"},
    ("anomalies", "status"): {"DETECTED", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"},
}

REQUIRED_FIELDS = {
    "departments": ("dept_id", "name", "code", "location"),
    "employees": ("emp_id", "email", "full_name", "department_id", "role", "employment_type", "hire_date", "status"),
    "categories": ("category_id", "name", "code", "default_priority", "tier"),
    "policy_documents": ("policy_id", "doc_code", "title", "category_id", "department_id", "audience", "owner_id"),
    "policy_versions": ("version_id", "policy_id", "version_number", "status", "effective_from", "summary", "content"),
    "knowledge_articles": ("article_id", "policy_version_id", "title", "section_number", "content", "audience"),
    "tickets": ("ticket_id", "tracking_number", "employee_id", "category_id", "title", "description", "status", "priority"),
    "assignments": ("assignment_id", "ticket_id", "assigned_to_id", "assigned_by_id", "tier", "assigned_at"),
    "slas": ("sla_id", "ticket_id", "priority", "business_hours_limit", "response_due_at", "resolution_due_at"),
    "resolutions": ("resolution_id", "ticket_id", "resolved_by_id", "resolution_type", "resolution_notes", "resolved_at"),
    "messages": ("message_id", "ticket_id", "sender_id", "message_type", "content", "created_at"),
    "anomalies": ("anomaly_id", "ticket_id", "anomaly_type", "severity", "description", "status"),
    "audit_logs": ("audit_id", "entity_type", "entity_id", "action", "created_at"),
}

PRIORITY_SLA = {"URGENT": (1, 4), "HIGH": (2, 8), "MEDIUM": (4, 24), "LOW": (8, 48)}
SNAPSHOT = datetime(2026, 6, 30, 17)


def _read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_datetime(value):
    return datetime.fromisoformat(value) if value else None


def _is_true(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def _reproducibility_check(seed, profile):
    with tempfile.TemporaryDirectory(prefix="hr-data-repro-") as temp:
        root = Path(temp)
        first = root / "first"
        second = root / "second"
        generate_dataset(profile, first, seed)
        generate_dataset(profile, second, seed)
        file_paths = sorted(
            path.relative_to(first).as_posix()
            for path in first.rglob("*")
            if path.is_file()
        )
        for relative in file_paths:
            left = first / Path(relative)
            right = second / Path(relative)
            if not right.exists() or _sha256(left) != _sha256(right):
                raise ValueError(f"Reproducibility check failed for {relative}")
        return len(file_paths)


def validate_dataset(profile="starter", base_dir="data", check_reproducibility=False, seed=20261022):
    root = Path(base_dir)
    target = root / profile
    truth_dir = root / "ground_truth" / profile
    errors = []
    tables = {}

    for table in TABLE_KEYS:
        path = target / f"{table}.csv"
        if not path.exists():
            errors.append(f"Missing required file {path}")
        else:
            tables[table] = _read_csv(path)
    manifest_path = target / "source_manifest.json"
    if not manifest_path.exists():
        errors.append(f"Missing source manifest: {manifest_path}")
        manifest = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    truth_csv = truth_dir / "ground_truth.csv"
    truth_json = truth_dir / "ground_truth.json"
    if not truth_csv.exists() or not truth_json.exists():
        errors.append(f"Missing profile-specific ground truth under {truth_dir}")
        truth_rows = []
        truth_json_rows = []
    else:
        truth_rows = _read_csv(truth_csv)
        truth_json_rows = json.loads(truth_json.read_text(encoding="utf-8"))

    if errors:
        print("\n".join(f"[FAIL] {error}" for error in errors))
        return False

    for table, rows in tables.items():
        key = TABLE_KEYS[table]
        identifiers = [row.get(key, "") for row in rows]
        if not all(identifiers) or len(identifiers) != len(set(identifiers)):
            errors.append(f"{table}.{key} contains missing or duplicate primary keys")
        if rows:
            for field in REQUIRED_FIELDS[table]:
                missing = sum(not row.get(field, "").strip() for row in rows)
                if missing:
                    errors.append(f"{table}.{field} has {missing} missing required values")
        for row_number, row in enumerate(rows, start=2):
            for (enum_table, field), allowed in ENUMS.items():
                if enum_table == table and row.get(field) not in allowed:
                    errors.append(f"{table} row {row_number}: {field}={row.get(field)!r} is not allowed")

    for version in tables["policy_versions"]:
        effective_from = date.fromisoformat(version["effective_from"])
        effective_to = date.fromisoformat(version["effective_to"]) if version["effective_to"] else None
        if effective_to and effective_to < effective_from:
            errors.append(f"{version['version_id']} expires before it becomes effective")
        if version["approved_at"] and datetime.fromisoformat(version["approved_at"]).date() < effective_from:
            errors.append(f"{version['version_id']} was approved before its effective date")

    for child, child_field, parent, parent_field, optional in FOREIGN_KEYS:
        parent_ids = {row[parent_field] for row in tables[parent] if row.get(parent_field)}
        invalid = [
            row.get(child_field, "")
            for row in tables[child]
            if (not row.get(child_field) and not optional)
            or (row.get(child_field) and row[child_field] not in parent_ids)
        ]
        if invalid:
            errors.append(f"{child}.{child_field} has {len(invalid)} missing/orphan references to {parent}.{parent_field}")

    unique_constraints = (
        ("employees", ("email",)),
        ("categories", ("name",)),
        ("categories", ("code",)),
        ("policy_documents", ("doc_code",)),
        ("tickets", ("tracking_number",)),
        ("policy_versions", ("policy_id", "version_number")),
        ("slas", ("ticket_id",)),
        ("resolutions", ("ticket_id",)),
    )
    for table, columns in unique_constraints:
        keys = [tuple(row.get(column, "") for column in columns) for row in tables[table]]
        if len(keys) != len(set(keys)):
            errors.append(f"{table} unique constraint {columns} has duplicates")

    expected_patterns = {
        "policy_id": re.compile(r"^POL-HR-2026-\d{3}$"),
        "version_id": re.compile(r"^VER-POL-HR-2026-\d{3}-\d{2}$"),
        "article_id": re.compile(r"^KB-\d{6}$"),
        "ticket_id": re.compile(r"^TKT-2026-\d{6}$"),
    }
    for table, field, pattern in (
        ("policy_documents", "policy_id", expected_patterns["policy_id"]),
        ("policy_documents", "doc_code", expected_patterns["policy_id"]),
        ("policy_versions", "version_id", expected_patterns["version_id"]),
        ("knowledge_articles", "article_id", expected_patterns["article_id"]),
        ("tickets", "ticket_id", expected_patterns["ticket_id"]),
        ("tickets", "tracking_number", expected_patterns["ticket_id"]),
    ):
        if any(not pattern.fullmatch(row[field]) for row in tables[table]):
            errors.append(f"{table}.{field} violates the required ID convention")

    ticket_by_id = {row["ticket_id"]: row for row in tables["tickets"]}
    version_by_id = {row["version_id"]: row for row in tables["policy_versions"]}
    document_by_id = {row["policy_id"]: row for row in tables["policy_documents"]}
    employee_by_id = {row["emp_id"]: row for row in tables["employees"]}
    assignments_by_ticket = {row["ticket_id"]: row for row in tables["assignments"]}
    slas_by_ticket = {row["ticket_id"]: row for row in tables["slas"]}
    resolutions_by_ticket = {row["ticket_id"]: row for row in tables["resolutions"]}
    anomalies_by_ticket = {}
    for row in tables["anomalies"]:
        anomalies_by_ticket.setdefault(row["ticket_id"], set()).add(row["anomaly_type"])
        if not _is_true(row.get("ground_truth_label", "")):
            errors.append(f"Anomaly {row['anomaly_id']} is missing its ground-truth label")

    truth_by_ticket = {row["ticket_id"]: row for row in truth_rows}
    if len(truth_by_ticket) != len(truth_rows) or set(truth_by_ticket) != set(ticket_by_id):
        errors.append("Ground truth rows do not map one-to-one to all generated tickets")
    if {row.get("ticket_id") for row in truth_json_rows} != set(truth_by_ticket):
        errors.append("Ground-truth JSON does not contain the same ticket IDs as ground_truth.csv")
    truth_manifest = manifest.get("ground_truth", {})
    if truth_manifest.get("record_count") != len(truth_rows):
        errors.append("Ground-truth manifest count does not match the CSV")
    if truth_manifest.get("csv_sha256") != _sha256(truth_csv):
        errors.append("Ground-truth CSV checksum mismatch")
    if truth_manifest.get("json_sha256") != _sha256(truth_json):
        errors.append("Ground-truth JSON checksum mismatch")

    audit_actions = {}
    for row in tables["audit_logs"]:
        audit_actions.setdefault(row["entity_id"], set()).add(row["action"])
    for ticket_id, ticket in ticket_by_id.items():
        actions = audit_actions.get(ticket_id, set())
        required_actions = {"CREATE_TICKET", "ASSIGN_TICKET"}
        if ticket["status"] == "CLARIFICATION_NEEDED":
            required_actions.add("CLARIFICATION_REQUESTED")
        if ticket["status"] == "ESCALATED":
            required_actions.add("ESCALATE_TICKET")
        if ticket["status"] in {"RESOLVED", "CLOSED"}:
            required_actions.add("RESOLVE_TICKET")
        if not required_actions.issubset(actions):
            errors.append(f"{ticket_id} is missing lifecycle audit events: {required_actions - actions}")

    for ticket_id, ticket in ticket_by_id.items():
        ticket_anomalies = anomalies_by_ticket.get(ticket_id, set())
        truth = truth_by_ticket.get(ticket_id)
        if truth:
            labeled_types = set(filter(None, truth["anomaly_types"].split(";")))
            if labeled_types != ticket_anomalies:
                errors.append(f"{ticket_id} anomaly records disagree with ground truth")
            if (truth["ground_truth_label"] == "ANOMALOUS") != bool(ticket_anomalies):
                errors.append(f"{ticket_id} ground-truth class disagrees with anomaly records")
            if _is_true(truth["is_sensitive"]) != _is_true(ticket["is_sensitive"]):
                errors.append(f"{ticket_id} sensitivity label disagrees with ticket source")
            if truth["expected_decision"] == "REQUEST_CLARIFICATION" and ticket["status"] != "CLARIFICATION_NEEDED":
                errors.append(f"{ticket_id} ambiguous request did not enter clarification state")

        created_at = _parse_datetime(ticket["created_at"])
        resolved_at = _parse_datetime(ticket["resolved_at"])
        if resolved_at and resolved_at < created_at:
            errors.append(f"{ticket_id} resolves before it was created")
        if (ticket["status"] in {"RESOLVED", "CLOSED"}) != bool(resolved_at):
            errors.append(f"{ticket_id} status and resolved_at lifecycle state disagree")
        if ticket["status"] in {"RESOLVED", "CLOSED"} and ticket_id not in resolutions_by_ticket:
            errors.append(f"{ticket_id} is resolved without a resolution record")
        if ticket["status"] == "ESCALATED" and assignments_by_ticket[ticket_id]["tier"] == "TIER_1":
            errors.append(f"{ticket_id} is escalated but remains assigned at Tier 1")
        if ticket["status"] == "CLARIFICATION_NEEDED":
            if not any(
                row["ticket_id"] == ticket_id and row["message_type"] == "CLARIFICATION_PROMPT"
                for row in tables["messages"]
            ):
                errors.append(f"{ticket_id} needs clarification but has no clarification message")

        if _is_true(ticket["is_sensitive"]):
            assignment = assignments_by_ticket[ticket_id]
            assignee = employee_by_id[assignment["assigned_to_id"]]
            if "SENSITIVE_GENERAL_QUEUE" in ticket_anomalies:
                if ticket["confidential_assigned_to"] or assignee["role"] != "HR_AGENT":
                    errors.append(f"{ticket_id} sensitive routing anomaly is not represented in source records")
            elif ticket["confidential_assigned_to"] != assignment["assigned_to_id"] or assignee["role"] not in {
                "HR_MANAGER", "COMPLIANCE_OFFICER"
            }:
                errors.append(f"{ticket_id} sensitive ticket is not restricted to an eligible confidential assignee")

        sla = slas_by_ticket[ticket_id]
        response_hours, resolution_hours = PRIORITY_SLA[ticket["priority"]]
        expected_response = add_business_hours(created_at, response_hours)
        expected_resolution = add_business_hours(created_at, resolution_hours)
        if int(sla["business_hours_limit"]) != resolution_hours:
            errors.append(f"{ticket_id} SLA limit does not match priority")
        if _parse_datetime(sla["response_due_at"]) != expected_response:
            errors.append(f"{ticket_id} response deadline is not business-hours derived")
        due = _parse_datetime(sla["resolution_due_at"])
        response_due = _parse_datetime(sla["response_due_at"])
        response_observed = _parse_datetime(sla["first_response_at"]) or SNAPSHOT
        if _is_true(sla["is_response_breached"]) != (response_observed > response_due):
            errors.append(f"{ticket_id} response breach flag does not reconcile to its deadline")
        if "INCORRECT_SLA_CALCULATION" in ticket_anomalies:
            if due == expected_resolution:
                errors.append(f"{ticket_id} labelled SLA exception has a correct deadline")
        elif due != expected_resolution:
            errors.append(f"{ticket_id} resolution deadline is not business-hours derived")
        elapsed_end = resolved_at or SNAPSHOT
        if float(sla["calculated_business_hours"]) != business_hours_between(created_at, elapsed_end):
            errors.append(f"{ticket_id} elapsed business hours do not reconcile to source dates")
        if _is_true(sla["is_resolution_breached"]) != (elapsed_end > due):
            errors.append(f"{ticket_id} resolution breach flag does not reconcile to its deadline")

        resolution = resolutions_by_ticket.get(ticket_id)
        if resolution:
            used_version = resolution["policy_version_used_id"]
            if "OBSOLETE_POLICY_CITATION" in ticket_anomalies:
                if not used_version or version_by_id[used_version]["status"] not in {"SUPERSEDED", "ARCHIVED"}:
                    errors.append(f"{ticket_id} obsolete citation label lacks an outdated policy version")
            elif "UNSUPPORTED_POLICY_CLAIM" in ticket_anomalies:
                if used_version or "unsupported" not in resolution["resolution_notes"].lower():
                    errors.append(f"{ticket_id} unsupported-claim label is not backed by its resolution")
            elif used_version:
                version = version_by_id[used_version]
                document = document_by_id[version["policy_id"]]
                effective_from = date.fromisoformat(version["effective_from"])
                effective_to = date.fromisoformat(version["effective_to"]) if version["effective_to"] else None
                if (
                    version["status"] != "ACTIVE"
                    or effective_from > resolved_at.date()
                    or (effective_to and effective_to < resolved_at.date())
                    or document["category_id"] != ticket["category_id"]
                ):
                    errors.append(f"{ticket_id} resolution does not cite its current effective category policy")

    messages_by_ticket = {}
    for row in tables["messages"]:
        messages_by_ticket.setdefault(row["ticket_id"], []).append(row)
        if _parse_datetime(row["created_at"]) < _parse_datetime(ticket_by_id[row["ticket_id"]]["created_at"]):
            errors.append(f"{row['message_id']} predates its ticket")
        expected_prefix = f"MSG-{row['ticket_id']}-"
        if not row["message_id"].startswith(expected_prefix):
            errors.append(f"{row['message_id']} does not follow the ticket-scoped message ID convention")
        try:
            citations = json.loads(row["citations_json"] or "[]")
        except json.JSONDecodeError:
            errors.append(f"{row['message_id']} has invalid citations_json")
            continue
        for citation in citations:
            cited_version = version_by_id.get(citation.get("policy_version_id"))
            if not cited_version or cited_version["status"] != "ACTIVE":
                errors.append(f"{row['message_id']} cites a missing or inactive policy version")
            elif citation.get("article_id") not in {article["article_id"] for article in tables["knowledge_articles"]}:
                errors.append(f"{row['message_id']} cites a missing knowledge article")
            else:
                article = next(
                    item for item in tables["knowledge_articles"]
                    if item["article_id"] == citation["article_id"]
                )
                if article["policy_version_id"] != cited_version["version_id"]:
                    errors.append(f"{row['message_id']} article and policy-version citation disagree")
                document = document_by_id[cited_version["policy_id"]]
                message_date = _parse_datetime(row["created_at"]).date()
                effective_from = date.fromisoformat(cited_version["effective_from"])
                effective_to = date.fromisoformat(cited_version["effective_to"]) if cited_version["effective_to"] else None
                if (
                    not _is_true(article["is_published"])
                    or effective_from > message_date
                    or (effective_to and effective_to < message_date)
                    or document["audience"] != "ALL_EMPLOYEES"
                    or article["audience"] != document["audience"]
                    or citation.get("doc_code") != document["doc_code"]
                    or citation.get("version_number") != cited_version["version_number"]
                ):
                    errors.append(f"{row['message_id']} cites a source outside its effective audience or version")
    for ticket_id, ticket_messages in messages_by_ticket.items():
        sequences = sorted(int(row["message_id"].rsplit("-", 1)[1]) for row in ticket_messages)
        if sequences != list(range(1, len(sequences) + 1)):
            errors.append(f"{ticket_id} message sequence contains gaps or duplicates")

    if len(tables["tickets"]) != len(tables["assignments"]) or len(tables["tickets"]) != len(tables["slas"]):
        errors.append("Every ticket must have exactly one active assignment and one SLA")
    if len(tables["knowledge_articles"]) != 150 and manifest.get("baseline_volume"):
        errors.append("Baseline profile must contain exactly 150 knowledge articles")
    if manifest.get("profile") != profile:
        errors.append("Source manifest profile does not match the selected dataset")
    if manifest.get("synthetic_only") is not True or manifest.get("external_sources") != []:
        errors.append("Source manifest must state synthetic-only provenance and no external sources")
    if manifest.get("record_counts") != {table: len(rows) for table, rows in tables.items()}:
        errors.append("Source manifest record counts do not match exported CSV files")
    for table in TABLE_KEYS:
        expected_hash = manifest.get("checksums_sha256", {}).get(f"{table}.csv")
        if expected_hash != _sha256(target / f"{table}.csv"):
            errors.append(f"Manifest checksum mismatch for {table}.csv")
    if manifest.get("checksums_sha256", {}).get("seed.sql") != _sha256(target / "seed.sql"):
        errors.append("Manifest checksum mismatch for seed.sql")

    if manifest.get("baseline_volume"):
        expected = ({"tickets": 5000, "messages": 20000} if profile == "full"
                    else {"tickets": 250, "messages": 1000})
        for table, count in expected.items():
            if len(tables[table]) != count:
                errors.append(f"Baseline {profile} profile expects {count} {table}, found {len(tables[table])}")
        if {row["anomaly_type"] for row in tables["anomalies"]} != {
            "OBSOLETE_POLICY_CITATION",
            "SENSITIVE_GENERAL_QUEUE",
            "INCORRECT_SLA_CALCULATION",
            "UNSUPPORTED_POLICY_CLAIM",
        }:
            errors.append("Baseline profile is missing one or more required anomaly types")

    reproduced_files = None
    if check_reproducibility:
        reproduced_files = _reproducibility_check(seed, profile)

    print(f"Profile: {profile}; seed: {manifest.get('seed')}")
    print(f"CSV row counts: {', '.join(f'{name}={len(rows)}' for name, rows in tables.items())}")
    anomaly_counts = {}
    for row in tables["anomalies"]:
        anomaly_counts[row["anomaly_type"]] = anomaly_counts.get(row["anomaly_type"], 0) + 1
    print(f"Anomaly labels: {json.dumps(anomaly_counts, sort_keys=True)}")
    if reproduced_files is not None:
        print(f"Reproducibility: PASS ({reproduced_files} files match across two generations)")
    if errors:
        print(f"Validation: FAIL ({len(errors)} issue(s))")
        for error in errors[:100]:
            print(f"  - {error}")
        return False
    print("Validation: PASS (keys, joins, enums, dates, lifecycle, labels, SLAs and checksums)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate generated HR datasets")
    parser.add_argument("profile", choices=["starter", "full"], nargs="?", default="starter")
    parser.add_argument("--base-dir", default="data")
    parser.add_argument("--check-reproducibility", action="store_true")
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    raise SystemExit(0 if validate_dataset(
        args.profile, args.base_dir, args.check_reproducibility, args.seed
    ) else 1)
