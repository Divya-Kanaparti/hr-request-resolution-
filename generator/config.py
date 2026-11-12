"""
Synthetic Data Generator Configuration
Deterministic Seed: 20261022
Synthetic Reference Horizon: 2026-01-05 to 2026-12-31
"""
from datetime import datetime, date

DEFAULT_SEED = 20261022

# Calendar Reference Bounds (Consistent 2026 baseline scenario)
START_DATE = datetime(2026, 1, 5, 9, 0, 0)
END_DATE = datetime(2026, 12, 31, 17, 0, 0)

# Corporate Working Hours
BUSINESS_HOUR_START = 9   # 09:00
BUSINESS_HOUR_END = 17    # 17:00
WORK_DAYS = [0, 1, 2, 3, 4]  # Monday through Friday

# 2026 Official Corporate Public Holidays
HOLIDAYS_2026 = [
    ("HOL-2026-001", "New Year's Day (Observed)", date(2026, 1, 1)),
    ("HOL-2026-002", "Martin Luther King Jr. Day", date(2026, 1, 19)),
    ("HOL-2026-003", "Presidents' Day", date(2026, 2, 16)),
    ("HOL-2026-004", "Memorial Day", date(2026, 5, 25)),
    ("HOL-2026-005", "Juneteenth National Independence Day", date(2026, 6, 19)),
    ("HOL-2026-006", "Independence Day (Observed)", date(2026, 7, 3)),
    ("HOL-2026-007", "Labor Day", date(2026, 9, 7)),
    ("HOL-2026-008", "Thanksgiving Day", date(2026, 11, 26)),
    ("HOL-2026-009", "Day After Thanksgiving", date(2026, 11, 27)),
    ("HOL-2026-010", "Christmas Day", date(2026, 12, 25))
]

# Standard Corporate Departments
DEPARTMENTS_SPEC = [
    ("DEP-001", "Human Resources", "HR", "Corporate Tower A"),
    ("DEP-002", "Engineering", "ENG", "Building 4, Tech Campus"),
    ("DEP-003", "Sales & Marketing", "MKT", "Corporate Tower B"),
    ("DEP-004", "Finance & Accounting", "FIN", "Corporate Tower A"),
    ("DEP-005", "Legal & Compliance", "LGL", "Corporate Tower A"),
    ("DEP-006", "Operations & IT", "OPS", "Building 2, Tech Campus")
]

# Standard Ticket Categories
CATEGORIES_SPEC = [
    ("CAT-001", "Benefits", "BEN", "Health insurance, 401k, HSA/FSA, wellness perks", "MEDIUM", False, "TIER_1"),
    ("CAT-002", "Leave & Time Off", "LEV", "PTO, sick leave, parental, bereavement, jury duty", "MEDIUM", False, "TIER_1"),
    ("CAT-003", "Payroll & Compensation", "PAY", "Direct deposit, paycheck disputes, bonuses, tax withholding", "HIGH", False, "TIER_2"),
    ("CAT-004", "Onboarding & Access", "ONB", "Equipment requisition, new hire paperwork, IT provisioning", "MEDIUM", False, "TIER_1"),
    ("CAT-005", "Workplace Relations", "REL", "Manager friction, performance plans, team dynamics", "HIGH", False, "TIER_2"),
    ("CAT-006", "Health & Safety", "SAF", "Ergonomics, workplace injury, safety hazards", "HIGH", False, "TIER_2"),
    ("CAT-007", "Confidential Employee Relations", "CMP", "Harassment, discrimination, whistleblowing, retaliation grievances", "URGENT", True, "TIER_3")
]

# SLA Plans Specification (Category / Priority -> Response / Resolution hours)
SLA_PLANS_SPEC = [
    ("SLA-PLAN-001", "Standard Tier 1 Plan", "CAT-001", "LOW", 8.0, 32.0, True),
    ("SLA-PLAN-002", "Benefits Standard Plan", "CAT-001", "MEDIUM", 4.0, 24.0, True),
    ("SLA-PLAN-003", "Leave Operations Plan", "CAT-002", "MEDIUM", 4.0, 24.0, True),
    ("SLA-PLAN-004", "Payroll Expedited Plan", "CAT-003", "HIGH", 2.0, 8.0, True),
    ("SLA-PLAN-005", "Onboarding Priority Plan", "CAT-004", "MEDIUM", 4.0, 16.0, True),
    ("SLA-PLAN-006", "Workplace Relations Plan", "CAT-005", "HIGH", 2.0, 12.0, True),
    ("SLA-PLAN-007", "Confidential Investigation Plan", "CAT-007", "URGENT", 1.0, 4.0, False)
]

# Routing Rules (Prioritized condition -> target queue & role)
ROUTING_RULES_SPEC = [
    ("RR-001", "Confidential Harassment & Whistleblower Rule", 10, "category == 'CAT-007' or is_sensitive == True", "CAT-007", "TIER_3", "RESTRICTED_CONFIDENTIAL_QUEUE", True, "COMPLIANCE_OFFICER"),
    ("RR-002", "Payroll Discrepancy Expedited Rule", 20, "category == 'CAT-003' and priority in ['HIGH', 'URGENT']", "CAT-003", "TIER_2", "PAYROLL_OPERATIONS_QUEUE", False, "HR_AGENT"),
    ("RR-003", "Onboarding Hardware & Access Rule", 30, "category == 'CAT-004'", "CAT-004", "TIER_1", "IT_ONBOARDING_QUEUE", False, "HR_AGENT"),
    ("RR-004", "Statutory Leave Interpretation Rule", 40, "category == 'CAT-002'", "CAT-002", "TIER_1", "LEAVE_ADMIN_QUEUE", False, "HR_AGENT"),
    ("RR-005", "Benefits Self-Service Eligible Rule", 50, "category == 'CAT-001'", "CAT-001", "TIER_1", "BENEFITS_OPERATIONS_QUEUE", False, "HR_AGENT"),
    ("RR-006", "Workplace Relations Mediation Rule", 60, "category == 'CAT-005'", "CAT-005", "TIER_2", "EMPLOYEE_RELATIONS_QUEUE", False, "HR_MANAGER"),
    ("RR-007", "Health and Ergonomic Safety Rule", 70, "category == 'CAT-006'", "CAT-006", "TIER_1", "SAFETY_FACILITIES_QUEUE", False, "HR_AGENT"),
    ("RR-008", "Default General Triage Fallback", 99, "True", None, "TIER_1", "GENERAL_HR_QUEUE", False, "HR_AGENT")
]

# Escalation Rules (Trigger -> Target Queue & Role)
ESCALATION_RULES_SPEC = [
    ("ER-001", "SLA Critical Breach Imminent Escalation", 10, "SLA_BREACH_IMMINENT", 80, "HR_MANAGER", "MANAGEMENT_ESCALATION_QUEUE"),
    ("ER-002", "SLA Definite Breach Escalation", 20, "SLA_BREACHED", 100, "HR_MANAGER", "DIRECTOR_ESCALATION_QUEUE"),
    ("ER-003", "Unsupported Policy Claim Review Escalation", 30, "UNSUPPORTED_POLICY", 0, "COMPLIANCE_OFFICER", "COMPLIANCE_REVIEW_QUEUE"),
    ("ER-004", "Sensitive Case Misroute Remediation", 5, "SENSITIVE_MISROUTE", 0, "COMPLIANCE_OFFICER", "RESTRICTED_CONFIDENTIAL_QUEUE")
]

