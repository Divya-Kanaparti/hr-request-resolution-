"""CLI and synthetic domain fixtures for the HR request data generator."""
import argparse
import csv
import random
from pathlib import Path

RANDOM_SEED = 20261022

CATEGORIES_SPEC = [
    ("CAT-001", "Benefits", "BEN", "Health insurance, 401k, HSA/FSA, wellness perks", "MEDIUM", False, "TIER_1"),
    ("CAT-002", "Leave & Time Off", "LEV", "PTO, sick leave, parental and bereavement leave", "MEDIUM", False, "TIER_1"),
    ("CAT-003", "Payroll & Compensation", "PAY", "Direct deposit, paycheck disputes, bonuses, tax withholding", "HIGH", False, "TIER_2"),
    ("CAT-004", "Onboarding & Offboarding", "ONB", "Equipment requisition, new hire paperwork, exit processing", "MEDIUM", False, "TIER_1"),
    ("CAT-005", "Workplace Relations", "REL", "Manager conflict, performance plans, team dynamics", "HIGH", False, "TIER_2"),
    ("CAT-006", "Health & Safety", "SAF", "Ergonomics, workplace injury, safety hazards", "HIGH", False, "TIER_2"),
    ("CAT-007", "Compliance & Ethics", "CMP", "Harassment, discrimination, whistleblowing, code of conduct", "URGENT", True, "TIER_3"),
]

DEPARTMENTS_SPEC = [
    ("DEP-001", "Human Resources", "HR", "Corporate Tower A"),
    ("DEP-002", "Engineering", "ENG", "Building 4, Tech Campus"),
    ("DEP-003", "Sales & Marketing", "MKT", "Corporate Tower B"),
    ("DEP-004", "Finance & Accounting", "FIN", "Corporate Tower A"),
    ("DEP-005", "Legal & Compliance", "LGL", "Corporate Tower A"),
    ("DEP-006", "Operations & IT", "OPS", "Building 2, Tech Campus"),
]

SAMPLE_TOPICS = {
    "CAT-001": [
        ("Dental enrollment after a life event", "I married recently and want to add my spouse to dental and vision coverage."),
        ("401(k) company match", "Can you confirm the company match percentage and vesting schedule?"),
        ("HSA contribution limits", "What is the maximum HSA payroll deduction for an individual plan?"),
        ("Wellness reimbursement", "Where do I submit my annual fitness membership receipts?"),
        ("Vision eyewear allowance", "Does vision insurance cover prescription sunglasses or contact lenses?"),
        ("Disability enrollment eligibility", "I would like to know whether disability coverage is automatic."),
    ],
    "CAT-002": [
        ("PTO accrual balance discrepancy", "My payslip shows 12 accrued PTO days instead of 15 based on my tenure."),
        ("Parental leave request", "I am expecting a child in June and would like to understand paid parental leave."),
        ("Bereavement leave policy", "I need to take bereavement leave after a family member passed away."),
        ("Jury duty wage continuation", "I received a court summons for jury service starting next Monday."),
        ("Unused PTO rollover", "How many unused hours can I carry into next year before they expire?"),
        ("Sick leave documentation", "Do I need to attach a physician note after three consecutive sick days?"),
    ],
    "CAT-003": [
        ("Missing overtime compensation", "My paycheck did not include overtime hours approved by my supervisor."),
        ("Change direct deposit account", "I need to update my direct deposit account before the next cutoff."),
        ("W-2 form request", "Could you provide an electronic copy of my previous year W-2?"),
        ("Tax withholding adjustment", "My tax withholding has not changed after I submitted a new W-4."),
        ("Performance bonus timing", "When will the departmental performance bonus be disbursed?"),
        ("Commuter deduction", "How do I increase my monthly pre-tax transit deduction?"),
    ],
    "CAT-004": [
        ("New hire equipment delivery", "I start Monday and have not received tracking information for my workstation."),
        ("Security badge activation", "My building badge fails to open the engineering laboratory doors."),
        ("I-9 verification appointment", "I need to schedule an appointment to verify Section 2 of my I-9."),
        ("Ergonomic equipment request", "I am requesting an ergonomic chair and monitor arm assessment."),
        ("Offboarding asset return", "I submitted notice and need the equipment return shipping label."),
    ],
    "CAT-005": [
        ("Conflict resolution guidance", "I am experiencing ongoing communication friction about team deliverables."),
        ("Performance plan timeline", "Please clarify the evaluation milestones in my 60-day performance plan."),
        ("Department transfer request", "I would like to initiate an internal transfer to another team."),
    ],
    "CAT-006": [
        ("Ergonomic desk assessment", "I am requesting an ergonomic evaluation due to wrist and neck strain."),
        ("Spill hazard report", "There is a water leak near an electrical panel in the breakroom."),
        ("First aid kit restocking", "The first aid kit in the engineering wing needs restocking."),
    ],
    "CAT-007": [
        ("Confidential harassment report", "I am reporting repeated offensive remarks and hostile comments by a colleague."),
        ("Whistleblower compliance report", "I am submitting confidential evidence about unauthorized accounting practices."),
        ("Retaliation concern", "I am facing exclusion after raising safety concerns."),
        ("Discrimination grievance", "I am raising a confidential grievance about discriminatory comments during review."),
    ],
}

AMBIGUOUS_QUERIES = [
    ("I need time off", "Can I take some days off soon?"),
    ("My pay is wrong", "My recent paycheck is missing money; please fix it."),
    ("Need benefits information", "What benefits do I get here?"),
    ("Equipment problem", "My work equipment is broken."),
]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
]


def write_csv(filepath: Path, records: list):
    if not records:
        raise ValueError(f"Cannot write a CSV without a header: {filepath}")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic HR data")
    parser.add_argument("--profile", choices=["starter", "full", "both"], default="starter")
    parser.add_argument("--outdir", default="data")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--tickets", type=int)
    parser.add_argument("--messages", type=int)
    parser.add_argument("--articles", type=int, default=150)
    args = parser.parse_args()

    try:
        from .data_factory import generate_dataset
    except ImportError:
        from data_factory import generate_dataset

    profiles = ("starter", "full") if args.profile == "both" else (args.profile,)
    for profile in profiles:
        generate_dataset(
            profile=profile,
            output_dir=args.outdir,
            seed=args.seed,
            ticket_count=args.tickets,
            message_count=args.messages,
            article_count=args.articles,
        )


if __name__ == "__main__":
    main()
