# Synthetic Data Validation Report

**HR Request Resolution System**  
**Seed**: `20261022`  
**Generated Date**: 2026-11-12  
**Validation Status**: **PASSED (100% Integrity)**

---

## 1. Executive Summary

The synthetic dataset generation suite was executed using deterministic seed `20261022`. Both `starter` and `full` profiles were synthesized and comprehensively verified against schema constraints, referential integrity rules, business-hours SLA calculations, and labeled anomaly injections.

| Metric | Starter Profile | Full Enterprise Profile | Target Requirement | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tickets** | 250 | **5,000** | 5,000 | **MATCHED** |
| **Messages** | 1,000 | **20,000** | 20,000 | **MATCHED** |
| **Policy Articles** | 150 | **150** | 150 | **MATCHED** |
| **Employees** | 50 | 500 | 500+ | **MATCHED** |
| **Departments** | 6 | 6 | 6 | **MATCHED** |
| **Categories** | 7 | 7 | 7 | **MATCHED** |
| **Total Injected Anomalies** | 28 | **533** | Labelled | **MATCHED** |

---

## 2. Injected Anomalies and Ground Truth Distribution

Four core operational enterprise anomalies were systematically synthesized and recorded in `data/ground_truth/ground_truth.csv` and `data/ground_truth/ground_truth.json`:

| Anomaly Type | Injected Count (Full) | Share of Total | Primary Detection Vector |
| :--- | :--- | :--- | :--- |
| **`OBSOLETE_POLICY_CITATION`** | 67 | 12.6% | Resolution quotes a superseded/archived version whose `effective_to` has expired. |
| **`SENSITIVE_GENERAL_QUEUE`** | 208 | 39.0% | Harassment, whistleblowing, or ethics grievance unassigned or exposed in general agent queue without confidential restriction. |
| **`INCORRECT_SLA_CALCULATION`** | 167 | 31.3% | SLA deadline computed using calendar hours (adding 24h directly), improperly counting weekend or after-hours time. |
| **`UNSUPPORTED_POLICY_CLAIM`** | 91 | 17.1% | Agent resolution asserts a benefit or term not corroborated by any active knowledge article. |
| **Total Anomalies** | **533** | **100%** | Comprehensive Multi-Vector Evaluation |

---

## 3. Ambiguity and Context Analysis

- **Ambiguous Tickets**: 500 tickets (10.0%) were injected with missing parameters (missing start/end dates for leave, missing pay period for payroll discrepancy, or vague benefit inquiries).
- **Proactive Clarification**: Each ambiguous ticket is assigned status `CLARIFICATION_NEEDED` and triggers an automated clarification prompt.

---

## 4. Referential Integrity & Foreign Key Audit

All 11 entity relationships and foreign keys were audited with zero orphan records:

| Child Table | Foreign Key Column | Parent Table | Parent Key | Orphan Count | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `employees` | `dept_id` | `departments` | `dept_id` | 0 | **PASS** |
| `tickets` | `employee_id` | `employees` | `emp_id` | 0 | **PASS** |
| `tickets` | `category_id` | `categories` | `category_id` | 0 | **PASS** |
| `assignments` | `ticket_id` | `tickets` | `ticket_id` | 0 | **PASS** |
| `assignments` | `assigned_to_id` | `employees` | `emp_id` | 0 | **PASS** |
| `slas` | `ticket_id` | `tickets` | `ticket_id` | 0 | **PASS** |
| `messages` | `ticket_id` | `tickets` | `ticket_id` | 0 | **PASS** |
| `resolutions` | `ticket_id` | `tickets` | `ticket_id` | 0 | **PASS** |
| `anomalies` | `ticket_id` | `tickets` | `ticket_id` | 0 | **PASS** |
| `policy_versions` | `policy_id` | `policy_documents` | `policy_id` | 0 | **PASS** |
| `knowledge_articles` | `policy_version_id` | `policy_versions` | `version_id` | 0 | **PASS** |

---

## 5. File Checksums (SHA-256 Reproducibility)

### Full Profile Artifacts (`data/full/`)
- `departments.csv`: `406c095d63af4ed0202df64dfa2d40ed9b3b0968008f12afd8e4a452cdf18e7c`
- `employees.csv`: `acceec357be0a82fda7038322885fe88129289ebf5902e29defe96ab349d625a`
- `categories.csv`: `79239cccbad3333d13bf7857376f2a7132f6ebc2f0fb392a94531bf2ccc1c7cc`
- `policy_documents.csv`: `7d23516750d0f45e176b3741b0e2d5a1d49ea246199fdd61f2ca94457a4c819e`
- `policy_versions.csv`: `236b7012d64f74fc61d360405e318cea54cb28f1706d29e2a453f72c53d87604`
- `knowledge_articles.csv`: `f732ca6958eb02cb4d4faa3188604cb904c5f829ee2ad157ff70389cde6fae49`
- `tickets.csv`: `2cf190543859260184c69bbeec5cc3147008aab0fb99e6ca8593b1b7a07f34a8`
- `assignments.csv`: `2ac7e9000f65c20e08bcfe647841daf036b1f421495cbe4dcb2046766ad31930`
- `slas.csv`: `f4e52c4ffafaf85ab5ce42c654e463a5193cdf0554d352d589846449919f9b34`
- `resolutions.csv`: `f076863d327c331869f4884b7c7a80da8c1a9a0b38a9f1da4bc08dd37b9d10c5`
- `messages.csv`: `162fc4dd83a40693a0bdb9b0ab60fdf990439255111425a751c0b8f09d0afc2e`
- `anomalies.csv`: `79dc7e38f800170fd04242d7afa5265749ef7cde1ea1dfa3ed4be48ec344b3a8`

