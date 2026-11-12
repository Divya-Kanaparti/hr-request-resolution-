"""
Classification and Ambiguity Detection Service
Performs category inference, ambiguity checks, and sensitive-case detection.
"""
import re
from typing import Dict, List, Any, Optional
from app.schemas.ticket import ClassificationResult, AmbiguityCheckResult

# Category keywords mapping
CATEGORY_KEYWORDS = {
    "CAT-001": { # Benefits
        "name": "Benefits",
        "keywords": ["health", "medical", "dental", "vision", "401k", "pension", "retirement", "insurance", "fsa", "hsa", "wellness", "gym", "commuter", "perks"],
        "default_priority": "MEDIUM"
    },
    "CAT-002": { # Leave
        "name": "Leave",
        "keywords": ["pto", "vacation", "sick leave", "holiday", "parental", "maternity", "paternity", "fmla", "bereavement", "jury duty", "sabbatical", "time off", "absence"],
        "default_priority": "MEDIUM"
    },
    "CAT-003": { # Payroll
        "name": "Payroll",
        "keywords": ["salary", "paycheck", "bonus", "tax", "w-2", "direct deposit", "overtime", "payslip", "deduction", "compensation", "wage", "reimbursement", "expense"],
        "default_priority": "HIGH"
    },
    "CAT-004": { # Onboarding
        "name": "Onboarding",
        "keywords": ["new hire", "orientation", "first day", "badge", "laptop", "equipment", "i-9", "welcome", "relocation", "probation", "background check"],
        "default_priority": "MEDIUM"
    },
    "CAT-005": { # Workplace Relations
        "name": "Workplace Relations",
        "keywords": ["manager", "conflict", "performance review", "pip", "feedback", "promotion", "transfer", "team dispute", "resignation", "exit interview"],
        "default_priority": "HIGH"
    },
    "CAT-006": { # Health & Safety
        "name": "Health & Safety",
        "keywords": ["injury", "ergonomics", "safety hazard", "workplace accident", "osha", "first aid", "evacuation", "building emergency"],
        "default_priority": "HIGH"
    },
    "CAT-007": { # Compliance & Ethics (Sensitive by default)
        "name": "Compliance & Ethics",
        "keywords": ["harassment", "discrimination", "whistleblower", "misconduct", "fraud", "bribe", "retaliation", "code of conduct", "investigation", "hostile"],
        "default_priority": "URGENT"
    }
}

SENSITIVE_TRIGGERS = [
    "harassment", "sexual harassment", "discriminated", "discrimination",
    "whistleblower", "fraud", "hostile work environment", "retaliation",
    "bully", "bullying", "mental breakdown", "depression diagnosis",
    "confidential medical", "misconduct", "assault", "illegal practice",
    "ethics violation", "grievance against manager"
]

def classify_text(title: str, description: str) -> ClassificationResult:
    """Classify user query into category and detect sensitivity."""
    combined_text = f"{title.lower()} {description.lower()}"
    
    # 1. Sensitive Detection
    is_sensitive = False
    sensitivity_reason = None
    for trig in SENSITIVE_TRIGGERS:
        if trig in combined_text:
            is_sensitive = True
            sensitivity_reason = f"Detected sensitive trigger topic: '{trig}'"
            break

    # 2. Category Matching
    best_cat_id = "CAT-001"
    best_score = 0
    matched_keywords = []

    for cat_id, info in CATEGORY_KEYWORDS.items():
        score = 0
        current_matched = []
        for kw in info["keywords"]:
            if kw in combined_text:
                score += 1
                current_matched.append(kw)
        if score > best_score:
            best_score = score
            best_cat_id = cat_id
            matched_keywords = current_matched

    if is_sensitive and best_score == 0:
        best_cat_id = "CAT-007"
        matched_keywords = ["compliance", "ethics"]

    cat_info = CATEGORY_KEYWORDS.get(best_cat_id, CATEGORY_KEYWORDS["CAT-001"])
    confidence = min(0.95, 0.40 + (best_score * 0.15)) if best_score > 0 else 0.50
    priority = "URGENT" if is_sensitive else cat_info["default_priority"]

    return ClassificationResult(
        recommended_category_id=best_cat_id,
        category_name=cat_info["name"],
        confidence=round(confidence, 2),
        is_sensitive=is_sensitive,
        sensitivity_reason=sensitivity_reason,
        recommended_priority=priority,
        detected_keywords=matched_keywords
    )

def detect_ambiguity(title: str, description: str, category_name: str) -> AmbiguityCheckResult:
    """
    Detect missing crucial context or ambiguous requests:
    - Missing dates for leave requests
    - Missing pay period or specific amounts for payroll discrepancies
    - Missing plan type for benefits inquiries
    """
    text = f"{title.lower()} {description.lower()}".strip()
    reasons = []
    missing_fields = []
    is_ambiguous = False

    # Short or vague text
    if len(text.split()) < 5:
        is_ambiguous = True
        reasons.append("Request text is unusually brief and lacks operational detail.")

    # Leave category checks
    if "leave" in category_name.lower():
        # Check for dates
        has_date = bool(re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2}|next week|tomorrow|monday|friday)\b', text))
        has_leave_type = any(lt in text for lt in ["pto", "vacation", "sick", "parental", "maternity", "paternity", "bereavement", "fmla", "unpaid"])
        
        if not has_date:
            is_ambiguous = True
            reasons.append("No specific departure or return dates provided.")
            missing_fields.append("Requested Start Date and End Date")
        if not has_leave_type:
            is_ambiguous = True
            reasons.append("Leave category/type is unspecified (e.g., Vacation vs Sick vs Bereavement).")
            missing_fields.append("Leave Type")

    # Payroll category checks
    elif "payroll" in category_name.lower():
        has_period = any(p in text for p in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "pay period", "last month", "recent slip", "bonus", "w-2", "direct deposit"])
        if not has_period:
            is_ambiguous = True
            reasons.append("Specific pay period, pay date, or payment component is not mentioned.")
            missing_fields.append("Pay Period Date or Paycheck ID")

    # Benefits category checks
    elif "benefits" in category_name.lower():
        has_benefit_type = any(b in text for b in ["health", "dental", "vision", "401k", "hsa", "fsa", "commuter", "gym", "wellness"])
        if not has_benefit_type:
            is_ambiguous = True
            reasons.append("Benefit program or plan type is unclear.")
            missing_fields.append("Benefit Program (Medical, Dental, 401k, etc.)")

    clarification_prompt = None
    if is_ambiguous:
        clarification_prompt = (
            f"To help us resolve your request quickly, could you please clarify: "
            f"{', '.join(missing_fields) if missing_fields else 'more specific details regarding your inquiry'}?"
        )

    return AmbiguityCheckResult(
        is_ambiguous=is_ambiguous,
        ambiguity_reasons=reasons,
        missing_fields=missing_fields,
        clarification_prompt=clarification_prompt
    )

