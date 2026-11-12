"""
Enterprise Synthetic Data Generator
Generates realistic baseline HR datasets and injects labelled anomalies.
Fixed Seed: 20261022
Profiles: 'starter' and 'full' (5,000 tickets, 150 policy articles, 20,000 messages).
Works with standard Python library (csv, json) or Pandas/Faker when installed.
"""
import os
import sys
import argparse
import random
import csv
from datetime import datetime, date, timedelta
import json
from pathlib import Path

# Fixed Random Seed
RANDOM_SEED = 20261022

CATEGORIES_SPEC = [
    ("CAT-001", "Benefits", "BEN", "Health insurance, 401k, HSA/FSA, wellness perks", "MEDIUM", False, "TIER_1"),
    ("CAT-002", "Leave & Time Off", "LEV", "PTO, sick leave, maternity/paternity, bereavement", "MEDIUM", False, "TIER_1"),
    ("CAT-003", "Payroll & Compensation", "PAY", "Direct deposit, paycheck disputes, bonuses, tax withholding", "HIGH", False, "TIER_2"),
    ("CAT-004", "Onboarding & Offboarding", "ONB", "Equipment requisition, new hire paperwork, exit processing", "MEDIUM", False, "TIER_1"),
    ("CAT-005", "Workplace Relations", "REL", "Manager conflict, performance plans, team dynamics", "HIGH", False, "TIER_2"),
    ("CAT-006", "Health & Safety", "SAF", "Ergonomics, workplace injury, safety hazards", "HIGH", False, "TIER_2"),
    ("CAT-007", "Compliance & Ethics", "CMP", "Harassment, discrimination, whistleblowing, code of conduct", "URGENT", True, "TIER_3")
]

DEPARTMENTS_SPEC = [
    ("DEP-001", "Human Resources", "HR", "Corporate Tower A"),
    ("DEP-002", "Engineering", "ENG", "Building 4, Tech Campus"),
    ("DEP-003", "Sales & Marketing", "MKT", "Corporate Tower B"),
    ("DEP-004", "Finance & Accounting", "FIN", "Corporate Tower A"),
    ("DEP-005", "Legal & Compliance", "LGL", "Corporate Tower A"),
    ("DEP-006", "Operations & IT", "OPS", "Building 2, Tech Campus")
]

SAMPLE_TOPICS = {
    "CAT-001": [
        ("How do I enroll in dental insurance for my spouse?", "I got married last week and would like to add my spouse to our dental and vision plan."),
        ("401(k) company match contribution percentage", "Can you confirm what the company 401(k) matching percentage is and when it vests?"),
        ("HSA contribution limits for this calendar year", "What is the maximum HSA payroll deduction allowed for an individual HDHP plan?"),
        ("Wellness gym reimbursement claim submission", "Where do I submit my annual $500 fitness and wellness gym membership receipts?"),
        ("Vision eyewear allowance details", "Does our vision insurance cover prescription sunglasses or contact lenses?"),
        ("Short-term disability enrollment eligibility", "I would like to know if short-term disability coverage is automatically enrolled.")
    ],
    "CAT-002": [
        ("PTO accrual balance discrepancy", "My latest payslip shows 12 days accrued PTO instead of 15 days according to my tenure."),
        ("Parental leave request for upcoming child birth", "Expecting our second child in June, requesting 16 weeks of paid parental leave."),
        ("Bereavement leave policy clarification", "Need to take bereavement leave following the passing of my grandfather."),
        ("Jury duty summons wage continuation", "I have received a court summons for jury service starting next Monday."),
        ("Unused PTO rollover into next calendar year", "How many hours of unused PTO can I carry over into next year before they expire?"),
        ("Sick leave documentation requirement", "If I am out sick for 3 consecutive days, do I need to attach a physician note?")
    ],
    "CAT-003": [
        ("Missing overtime compensation on pay stub", "My paycheck dated March 15 did not include the 12 overtime hours approved by my supervisor."),
        ("Change direct deposit checking account", "I need to update my bank account for direct deposit before the upcoming cutoff."),
        ("W-2 tax form copy request", "Could you provide an electronic copy of my previous year W-2 for tax filing?"),
        ("Federal tax withholding adjustment W-4", "I submitted a new W-4 form two weeks ago but my tax withholdings remain unchanged."),
        ("Performance bonus payout timing", "When will the Q3 departmental performance bonus be disbursed to eligible staff?"),
        ("Commuter pre-tax transit deduction", "How do I increase my monthly pre-tax transit pass deduction to $200?")
    ],
    "CAT-004": [
        ("New hire laptop and monitor delivery status", "Starting on Monday, haven't received tracking information for my workstation equipment."),
        ("Security building access badge activation", "My building badge fails to open the 4th floor engineering laboratory doors."),
        ("I-9 form verification appointment", "I need to schedule an in-person appointment to verify Section 2 of my I-9 documentation."),
        ("Office ergonomic chair request", "Requesting an ergonomic chair and monitor arm evaluation for my designated desk."),
        ("Offboarding process and asset return checklist", "I have submitted my 2-week notice and need the equipment return shipping label.")
    ],
    "CAT-005": [
        ("Conflict resolution guidance with team lead", "Experiencing ongoing communication friction regarding sprint deliverables."),
        ("Performance improvement plan timeline clarification", "Requesting clarification on the evaluation milestones outlined in my 60-day PIP."),
        ("Departmental transfer request to DevOps team", "I would like to initiate an internal transfer request to the Cloud Infrastructure team.")
    ],
    "CAT-006": [
        ("Ergonomic desk assessment request", "Requesting an ergonomic evaluation due to persistent wrist and neck strain."),
        ("Spill hazard in 2nd floor breakroom", "Water leak noticed near the electrical panel on the second floor breakroom."),
        ("First aid kit restocking in Engineering wing", "The wall-mounted first aid kit in Building 4 needs restocking of antiseptic supplies.")
    ],
    "CAT-007": [
        ("Confidential report of workplace harassment", "Reporting repeated offensive remarks and hostile comments made by a senior colleague."),
        ("Whistleblower report regarding billing compliance", "Submitting confidential documentation regarding unauthorized accounting practices."),
        ("Report of retaliatory treatment after reporting misconduct", "Facing exclusionary behavior and project removal after raising safety concerns."),
        ("Discrimination in promotional opportunities", "Raising a confidential grievance regarding discriminatory comments during review.")
    ]
}

AMBIGUOUS_QUERIES = [
    ("I need time off", "Can I take some days off soon?"),
    ("My pay is wrong", "My recent paycheck is missing money, please fix."),
    ("Need benefits info", "What benefits do I get here?"),
    ("Equipment problem", "My stuff is broken.")
]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
]

def write_csv(filepath: Path, records: list):
    """Write list of dicts to CSV using standard csv module."""
    if not records:
        return
    keys = list(records[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

def is_work_day(dt: datetime) -> bool:
    return dt.weekday() < 5

def add_business_hours_sim(start_dt: datetime, hours: float) -> datetime:
    """Pure Python simulation of business-hours addition (09:00 - 17:00, Mon-Fri)."""
    cur = start_dt
    while cur.weekday() >= 5:
        cur += timedelta(days=1)
        cur = cur.replace(hour=9, minute=0, second=0)

    if cur.hour < 9:
        cur = cur.replace(hour=9, minute=0, second=0)
    elif cur.hour >= 17:
        cur += timedelta(days=1)
        while cur.weekday() >= 5:
            cur += timedelta(days=1)
        cur = cur.replace(hour=9, minute=0, second=0)

    remaining_minutes = int(hours * 60)
    while remaining_minutes > 0:
        if cur.weekday() >= 5:
            cur += timedelta(days=1)
            continue
        day_end = cur.replace(hour=17, minute=0, second=0)
        minutes_left = int((day_end - cur).total_seconds() / 60)
        if minutes_left <= 0:
            cur += timedelta(days=1)
            cur = cur.replace(hour=9, minute=0, second=0)
            continue
        if remaining_minutes <= minutes_left:
            cur += timedelta(minutes=remaining_minutes)
            remaining_minutes = 0
        else:
            remaining_minutes -= minutes_left
            cur += timedelta(days=1)
            cur = cur.replace(hour=9, minute=0, second=0)
    return cur

def generate_dataset(profile: str = "starter", output_dir: str = "data"):
    random.seed(RANDOM_SEED)

    is_full = (profile == "full")
    num_employees = 500 if is_full else 50
    num_articles = 150  # Required: exactly 150 policy articles
    num_tickets = 5000 if is_full else 250
    num_messages = 20000 if is_full else 1000

    print(f"[*] Generating '{profile}' dataset: {num_employees} employees, {num_articles} policy articles, {num_tickets} tickets, {num_messages} messages...")

    out_path = Path(output_dir) / profile
    out_path.mkdir(parents=True, exist_ok=True)
    gt_path = Path(output_dir) / "ground_truth"
    gt_path.mkdir(parents=True, exist_ok=True)

    # 1. Departments
    dept_records = []
    for d_id, name, code, loc in DEPARTMENTS_SPEC:
        dept_records.append({
            "dept_id": d_id,
            "name": name,
            "code": code,
            "location": loc,
            "created_at": "2023-01-01T00:00:00"
        })
    write_csv(out_path / "departments.csv", dept_records)

    # 2. Employees
    roles_pool = ["EMPLOYEE"] * 85 + ["HR_AGENT"] * 8 + ["HR_MANAGER"] * 4 + ["ADMIN"] * 2 + ["COMPLIANCE_OFFICER"] * 1
    employees = [
        {"emp_id": "EMP-0001", "email": "admin@company.com", "full_name": "System Administrator", "dept_id": "DEP-006", "role": "ADMIN", "employment_type": "FULL_TIME", "hire_date": "2021-01-10", "status": "ACTIVE"},
        {"emp_id": "EMP-0002", "email": "emily.manager@company.com", "full_name": "Emily Watson", "dept_id": "DEP-001", "role": "HR_MANAGER", "employment_type": "FULL_TIME", "hire_date": "2021-03-15", "status": "ACTIVE"},
        {"emp_id": "EMP-0003", "email": "sarah.agent@company.com", "full_name": "Sarah Jenkins", "dept_id": "DEP-001", "role": "HR_AGENT", "employment_type": "FULL_TIME", "hire_date": "2022-02-01", "status": "ACTIVE"},
        {"emp_id": "EMP-0004", "email": "rachel.compliance@company.com", "full_name": "Rachel Vance", "dept_id": "DEP-005", "role": "COMPLIANCE_OFFICER", "employment_type": "FULL_TIME", "hire_date": "2021-06-10", "status": "ACTIVE"},
        {"emp_id": "EMP-0005", "email": "john.doe@company.com", "full_name": "John Doe", "dept_id": "DEP-002", "role": "EMPLOYEE", "employment_type": "FULL_TIME", "hire_date": "2022-05-18", "status": "ACTIVE"}
    ]

    for i in range(6, num_employees + 1):
        emp_id = f"EMP-{i:04d}"
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        email = f"{fn.lower()}.{ln.lower()}{i}@company.com"
        role = random.choice(roles_pool)
        dept = random.choice(DEPARTMENTS_SPEC)[0]
        emp_type = random.choice(["FULL_TIME", "FULL_TIME", "FULL_TIME", "CONTRACT", "PART_TIME"])
        employees.append({
            "emp_id": emp_id,
            "email": email,
            "full_name": f"{fn} {ln}",
            "dept_id": dept,
            "role": role,
            "employment_type": emp_type,
            "hire_date": (date(2022, 1, 1) + timedelta(days=random.randint(0, 1000))).isoformat(),
            "status": "ACTIVE"
        })
    write_csv(out_path / "employees.csv", employees)

    # 3. Categories
    cat_records = []
    for c_id, name, code, desc, prio, sens, tier in CATEGORIES_SPEC:
        cat_records.append({
            "category_id": c_id,
            "name": name,
            "code": code,
            "description": desc,
            "default_priority": prio,
            "is_sensitive_default": sens,
            "tier": tier,
            "created_at": "2023-01-01T00:00:00"
        })
    write_csv(out_path / "categories.csv", cat_records)

    # 4. Policy Documents, Versions & 150 Knowledge Articles
    policy_docs = []
    policy_versions = []
    knowledge_articles = []

    categories_keys = list(SAMPLE_TOPICS.keys())
    for p_idx in range(1, 31):
        p_id = f"POL-{p_idx:03d}"
        cat_id = categories_keys[(p_idx - 1) % len(categories_keys)]
        cat_code = next(c[2] for c in CATEGORIES_SPEC if c[0] == cat_id)
        doc_code = f"POL-{cat_code}-{p_idx:02d}"
        title = f"Corporate Policy on {SAMPLE_TOPICS[cat_id][(p_idx-1) % len(SAMPLE_TOPICS[cat_id])][0]}"
        policy_docs.append({
            "policy_id": p_id,
            "doc_code": doc_code,
            "title": title,
            "category_id": cat_id,
            "department_id": "DEP-001",
            "audience": "ALL_EMPLOYEES",
            "owner_id": "EMP-0002",
            "created_at": "2023-01-01T00:00:00"
        })

        # Add 2 versions: v1.0 (SUPERSEDED/ARCHIVED), v2.0 (ACTIVE)
        v1_id = f"VER-{p_idx:03d}-1"
        v2_id = f"VER-{p_idx:03d}-2"

        policy_versions.append({
            "version_id": v1_id,
            "policy_id": p_id,
            "version_number": "1.0",
            "status": "SUPERSEDED",
            "effective_from": "2023-01-01",
            "effective_to": "2024-12-31",
            "summary": f"Legacy initial version of {title}.",
            "content": f"Historical guidelines regarding {title}. Superseded on 2025-01-01.",
            "approved_by": "EMP-0002"
        })

        policy_versions.append({
            "version_id": v2_id,
            "policy_id": p_id,
            "version_number": "2.0",
            "status": "ACTIVE",
            "effective_from": "2025-01-01",
            "effective_to": "",
            "summary": f"Active standard version of {title}.",
            "content": f"Official active guidelines governing {title}. Mandatory adherence for all employees.",
            "approved_by": "EMP-0002"
        })

    # Exactly 150 knowledge articles distributed across active versions
    for art_idx in range(1, num_articles + 1):
        assigned_pver = policy_versions[(art_idx * 2 - 1) % len(policy_versions)]
        sec_num = f"Sec {(art_idx % 8) + 1}.{(art_idx % 5) + 1}"
        p_obj = next(p for p in policy_docs if p["policy_id"] == assigned_pver["policy_id"])
        art_title = f"{p_obj['title']} - Operational Guidelines {sec_num}"
        content = (
            f"Under {p_obj['title']} ({p_obj['doc_code']}), employees must adhere strictly to these operational parameters. "
            f"Formal submission through the HR portal is required within 30 business days. "
            f"Standard processing time is 2 to 5 business days, verified and administered by Human Resources."
        )
        knowledge_articles.append({
            "article_id": f"ART-{art_idx:04d}",
            "policy_version_id": assigned_pver["version_id"],
            "title": art_title,
            "section_number": sec_num,
            "content": content,
            "keywords": f"{p_obj['doc_code']}, guidelines, eligibility, compliance, process",
            "audience": "ALL_EMPLOYEES",
            "is_published": True,
            "created_at": "2025-01-01T00:00:00"
        })

    write_csv(out_path / "policy_documents.csv", policy_docs)
    write_csv(out_path / "policy_versions.csv", policy_versions)
    write_csv(out_path / "knowledge_articles.csv", knowledge_articles)

    # 5. Tickets, Assignments, SLAs, Resolutions, Messages, Anomalies
    tickets = []
    assignments = []
    slas = []
    resolutions = []
    messages = []
    anomalies = []
    ground_truth = []

    hr_agents = [e for e in employees if e["role"] in ["HR_AGENT", "HR_MANAGER"]]
    regular_employees = [e for e in employees if e["role"] == "EMPLOYEE"]

    base_date = datetime(2026, 1, 5, 9, 0, 0)

    for t_idx in range(1, num_tickets + 1):
        t_id = f"TCK-{t_idx:05d}"
        tracking_num = f"REQ-2026-{t_idx:05d}"
        emp = random.choice(regular_employees)

        # 10% Ambiguous tickets
        is_ambiguous = (t_idx % 10 == 0)
        # 8% Sensitive tickets
        is_sensitive = (t_idx % 12 == 0)

        if is_sensitive:
            cat_id = "CAT-007"
            p_topic = random.choice(SAMPLE_TOPICS["CAT-007"])
            title, desc = p_topic[0], p_topic[1]
            priority = "URGENT"
        elif is_ambiguous:
            cat_id = random.choice(["CAT-001", "CAT-002", "CAT-003"])
            title, desc = random.choice(AMBIGUOUS_QUERIES)
            priority = "MEDIUM"
        else:
            cat_id = random.choice(categories_keys)
            p_topic = random.choice(SAMPLE_TOPICS[cat_id])
            title, desc = p_topic[0], p_topic[1]
            cat_prio = next(c[4] for c in CATEGORIES_SPEC if c[0] == cat_id)
            priority = cat_prio

        created_at = base_date + timedelta(minutes=(t_idx * 25))

        if is_ambiguous:
            status = random.choice(["CLARIFICATION_NEEDED", "IN_PROGRESS", "RESOLVED"])
        else:
            status = random.choices(["RESOLVED", "IN_PROGRESS", "NEW", "ESCALATED"], weights=[70, 18, 7, 5])[0]

        has_anomaly = False
        anomaly_type = None

        confidential_assigned = None
        if is_sensitive:
            confidential_assigned = "EMP-0002" if t_idx % 24 != 0 else None
            if not confidential_assigned:
                has_anomaly = True
                anomaly_type = "SENSITIVE_GENERAL_QUEUE"

        resolved_at = None
        if status in ["RESOLVED", "CLOSED"]:
            resolved_at = add_business_hours_sim(created_at, random.randint(4, 20))

        tickets.append({
            "ticket_id": t_id,
            "tracking_number": tracking_num,
            "employee_id": emp["emp_id"],
            "category_id": cat_id,
            "title": title,
            "description": desc,
            "status": status,
            "priority": priority,
            "is_sensitive": is_sensitive,
            "confidential_assigned_to": confidential_assigned or "",
            "created_at": created_at.isoformat(),
            "updated_at": (resolved_at or created_at).isoformat(),
            "resolved_at": resolved_at.isoformat() if resolved_at else ""
        })

        assigned_agent = random.choice(hr_agents)
        assignments.append({
            "assignment_id": f"ASG-{t_idx:05d}",
            "ticket_id": t_id,
            "assigned_to_id": confidential_assigned or assigned_agent["emp_id"],
            "assigned_by_id": "EMP-0002",
            "tier": "TIER_2" if is_sensitive else "TIER_1",
            "reason": "Automated system triage",
            "assigned_at": created_at.isoformat(),
            "unassigned_at": "",
            "is_active": True
        })

        limit_hours = 4 if priority == "URGENT" else (8 if priority == "HIGH" else 24)
        correct_resp_due = add_business_hours_sim(created_at, 2 if priority == "URGENT" else 4)
        correct_res_due = add_business_hours_sim(created_at, limit_hours)

        sla_is_incorrect = (t_idx % 30 == 3)
        if sla_is_incorrect:
            has_anomaly = True
            anomaly_type = "INCORRECT_SLA_CALCULATION"
            res_due = created_at + timedelta(hours=limit_hours)
        else:
            res_due = correct_res_due

        is_breached = bool(resolved_at and resolved_at > res_due)

        slas.append({
            "sla_id": f"SLA-{t_idx:05d}",
            "ticket_id": t_id,
            "priority": priority,
            "business_hours_limit": limit_hours,
            "response_due_at": correct_resp_due.isoformat(),
            "resolution_due_at": res_due.isoformat(),
            "first_response_at": (created_at + timedelta(minutes=45)).isoformat(),
            "is_response_breached": False,
            "is_resolution_breached": is_breached,
            "calculated_business_hours": 8.0,
            "created_at": created_at.isoformat()
        })

        messages.append({
            "message_id": f"MSG-{len(messages) + 1:06d}",
            "ticket_id": t_id,
            "sender_id": emp["emp_id"],
            "message_type": "EMPLOYEE_NOTE",
            "content": desc,
            "citations_json": "[]",
            "is_internal": False,
            "created_at": created_at.isoformat()
        })

        if status in ["IN_PROGRESS", "RESOLVED"]:
            messages.append({
                "message_id": f"MSG-{len(messages) + 1:06d}",
                "ticket_id": t_id,
                "sender_id": assigned_agent["emp_id"],
                "message_type": "AGENT_REPLY",
                "content": "Thank you for reaching out to HR. Your request is being reviewed under company policy standards.",
                "citations_json": "[]",
                "is_internal": False,
                "created_at": (created_at + timedelta(minutes=45)).isoformat()
            })

        if status in ["RESOLVED", "CLOSED"]:
            policy_used = "VER-001-2"
            is_obsolete = (t_idx % 50 == 1)
            is_unsupported = (t_idx % 40 == 4)

            if is_obsolete:
                has_anomaly = True
                anomaly_type = "OBSOLETE_POLICY_CITATION"
                policy_used = "VER-001-1"
                res_notes = "Resolved using archived Policy Version 1.0 guidelines (superseded in 2025)."
            elif is_unsupported:
                has_anomaly = True
                anomaly_type = "UNSUPPORTED_POLICY_CLAIM"
                policy_used = ""
                res_notes = "Approved request citing 100% remote stipend unlimited and executive dental allowance."
            else:
                res_notes = "Inquiry fully investigated and confirmed compliant with active corporate policy standards."

            resolutions.append({
                "resolution_id": f"RES-{t_idx:05d}",
                "ticket_id": t_id,
                "resolved_by_id": assigned_agent["emp_id"],
                "resolution_type": "POLICY_EXPLANATION",
                "resolution_notes": res_notes,
                "root_cause": "Routine policy clarification",
                "policy_version_used_id": policy_used,
                "employee_rating": random.choice([4, 5, 5, 3, 4]),
                "employee_feedback": "Thank you for the prompt resolution.",
                "resolved_at": resolved_at.isoformat()
            })

        if has_anomaly and anomaly_type:
            anomalies.append({
                "anomaly_id": f"ANOM-{len(anomalies) + 1:05d}",
                "ticket_id": t_id,
                "anomaly_type": anomaly_type,
                "severity": "CRITICAL" if anomaly_type == "SENSITIVE_GENERAL_QUEUE" else "HIGH",
                "description": f"Injected synthetic ground truth anomaly: {anomaly_type}",
                "status": "DETECTED",
                "ground_truth_label": True,
                "detected_at": created_at.isoformat()
            })

        ground_truth.append({
            "ticket_id": t_id,
            "tracking_number": tracking_num,
            "category_id": cat_id,
            "is_sensitive": is_sensitive,
            "is_ambiguous": is_ambiguous,
            "has_anomaly": has_anomaly,
            "anomaly_type": anomaly_type or "NONE",
            "sla_business_hours_limit": limit_hours,
            "expected_resolution_due": correct_res_due.isoformat()
        })

    # Fill extra messages to target count
    target_msg_count = num_messages
    current_msg_count = len(messages)
    for extra in range(current_msg_count + 1, target_msg_count + 1):
        rand_ticket = tickets[(extra - 1) % len(tickets)]
        is_internal = (extra % 5 == 0)
        messages.append({
            "message_id": f"MSG-{extra:06d}",
            "ticket_id": rand_ticket["ticket_id"],
            "sender_id": rand_ticket["employee_id"] if extra % 2 == 0 else "EMP-0003",
            "message_type": "INTERNAL_NOTE" if is_internal else ("EMPLOYEE_NOTE" if extra % 2 == 0 else "AGENT_REPLY"),
            "content": f"Update message on ticket {rand_ticket['tracking_number']}: Follow-up verification details recorded.",
            "citations_json": "[]",
            "is_internal": is_internal,
            "created_at": rand_ticket["created_at"]
        })

    write_csv(out_path / "tickets.csv", tickets)
    write_csv(out_path / "assignments.csv", assignments)
    write_csv(out_path / "slas.csv", slas)
    write_csv(out_path / "resolutions.csv", resolutions)
    write_csv(out_path / "messages.csv", messages)
    write_csv(out_path / "anomalies.csv", anomalies)

    write_csv(gt_path / "ground_truth.csv", ground_truth)
    with open(gt_path / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"[+] Successfully generated dataset '{profile}':")
    print(f"    - Tickets: {len(tickets)}")
    print(f"    - Messages: {len(messages)}")
    print(f"    - Policy Articles: {len(knowledge_articles)}")
    print(f"    - Anomalies Injected: {len(anomalies)}")
    print(f"    - Ground Truth records: {len(ground_truth)}")

def main():
    parser = argparse.ArgumentParser(description="Synthetic HR Data Generator")
    parser.add_argument("--profile", choices=["starter", "full", "both"], default="starter")
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    if args.profile == "both":
        generate_dataset("starter", args.outdir)
        generate_dataset("full", args.outdir)
    else:
        generate_dataset(args.profile, args.outdir)

if __name__ == "__main__":
    main()
