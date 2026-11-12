# Generated Data Validation Report

**Seed:** `20261022`  
**Generator:** `generator/generate_data.py`  
**Provenance:** Fully synthetic; no external or personal data sources used.  
**Validation commands:**

```powershell
python generator\validation.py starter
python generator\validation.py full --check-reproducibility
python generator\ground_truth.py --profile full
```

## Baseline volume and relationships

| Entity | Starter | Full |
|---|---:|---:|
| Departments | 6 | 6 |
| Employees | 50 | 500 |
| Categories | 7 | 7 |
| Policy documents | 30 | 30 |
| Policy versions | 60 | 60 |
| Knowledge articles | 150 | 150 |
| Tickets | 250 | 5,000 |
| Assignments | 250 | 5,000 |
| SLAs | 250 | 5,000 |
| Resolutions | 176 | 3,311 |
| Messages | 1,000 | 20,000 |
| Audit events | 945 | 18,737 |
| Anomaly records | 30 | 531 |

`data/{starter,full}/source_manifest.json` contains each profile's record counts,
SHA-256 checksums, seed, synthetic-only provenance, and ground-truth checksums.
Each profile includes CSV and MySQL seed exports. Labels are in the separate
`data/ground_truth/{starter,full}/` directory.

## Full-profile ground truth and coverage

| Case | Count | Rule |
|---|---:|---|
| Ambiguous requests | 417 (8.3%) | Missing required context; ticket enters `CLARIFICATION_NEEDED` and receives a prompt. |
| Sensitive requests | 416 (8.3%) | Sensitive ticket routed to a manager/compliance handler, except labelled misroutes. |
| Obsolete policy citations | 68 | Resolution references an expired/superseded policy version. |
| Sensitive general-queue routes | 208 | Sensitive case assigned to a general HR agent without confidential restriction. |
| Incorrect SLA deadlines | 167 | Injected calendar-time deadline differs from the computed business-hours deadline. |
| Unsupported policy claims | 88 | Resolution contains a claim not supported by an active policy citation. |
| **Total anomaly records** | **531** | Ground-truth labels are derived from the same deterministic rules. |

Ambiguity and sensitivity are separate classifications. A ticket may carry multiple
anomaly types; the separate per-ticket ground-truth files retain all labels and
expected decisions without mixing them into the operational feature CSVs.

## Validation outcomes

- **Keys and joins:** all required primary keys are present and unique; every required
  and optional foreign key was checked across the generated files.
- **Enums and schema:** required fields, allowed enum values, ID formats, and declared
  unique constraints passed.
- **Lifecycle and history:** resolved tickets have resolution records; ambiguous
  tickets have clarification prompts; routing, response, escalation, resolution and
  injected exceptions are retained as audit events.
- **Policy sources:** ordinary resolution and message citations point to published
  current versions and matching articles; obsolete citations are explicitly labelled.
- **Derived SLA values:** response and resolution deadlines, business-hour elapsed
  time, breach flags, and priority limits reconcile to source timestamps and the
  documented work calendar. The intentionally incorrect SLA cases are separately
  labelled and excluded from normal-deadline assertions.
- **Ground truth:** CSV and JSON labels cover every ticket, reconcile to anomaly
  records, and are checksummed in each source manifest.
- **Reproducibility:** two full-profile generations with seed `20261022` produced
  matching checksums for all 19 data, SQL, manifest, and ground-truth artifacts.
- **Backend behavior:** `28` automated tests passed, including form and JSON login,
  ticket routing, clarification, policy citations, anomaly detection, and SLA behavior.

The generated SQL seed was structurally emitted and checksum-validated. A live MySQL
import was not run in this environment because the MySQL CLI/server is unavailable.
Synthetic employee rows intentionally have blank password hashes; use
`database/seed.sql` for the separate demo login accounts.
