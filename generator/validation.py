"""
Synthetic Data Validation Engine
Validates:
1. Primary key uniqueness / duplicate checks
2. Foreign key referential integrity
3. Reproducibility checksums (SHA256)
4. Anomaly distribution statistics
Compatible with standard library (csv) or Pandas.
"""
import hashlib
import csv
from pathlib import Path
import json

def compute_file_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum for a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()

def read_csv_rows(filepath: Path):
    """Read CSV into list of dictionaries."""
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def validate_dataset(profile: str = "starter", base_dir: str = "data"):
    target_dir = Path(base_dir) / profile
    if not target_dir.exists():
        print(f"[-] Profile directory not found: {target_dir}")
        return False

    print("=" * 65)
    print(f"VALIDATING DATASET: {profile.upper()} ({target_dir})")
    print("=" * 65)

    errors = []
    checksums = {}
    tables = {}

    table_names = [
        "departments", "employees", "categories", "policy_documents",
        "policy_versions", "knowledge_articles", "tickets", "assignments",
        "slas", "resolutions", "messages", "anomalies"
    ]

    for filename in table_names:
        fpath = target_dir / f"{filename}.csv"
        if fpath.exists():
            tables[filename] = read_csv_rows(fpath)
            checksums[f"{filename}.csv"] = compute_file_sha256(fpath)
        else:
            errors.append(f"Missing required table file: {filename}.csv")

    if errors:
        for err in errors:
            print(f"[-] {err}")
        return False

    # 1. Primary Key Duplicates Check
    pk_map = {
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
        "anomalies": "anomaly_id"
    }

    print("\n[1/4] Running Primary Key Uniqueness Checks...")
    for tname, pk in pk_map.items():
        rows = tables[tname]
        seen = set()
        dupes = []
        for r in rows:
            val = r.get(pk)
            if val in seen:
                dupes.append(val)
            seen.add(val)
        if dupes:
            msg = f"Duplicate primary keys in {tname}.{pk}: {len(dupes)} occurrences"
            errors.append(msg)
            print(f"  [FAIL] {msg}")
        else:
            print(f"  [PASS] {tname:20s} PK {pk:15s} unique ({len(rows)} records)")

    # 2. Foreign Key Checks
    print("\n[2/4] Running Foreign Key Referential Integrity Checks...")
    fk_checks = [
        ("employees", "dept_id", "departments", "dept_id"),
        ("tickets", "employee_id", "employees", "emp_id"),
        ("tickets", "category_id", "categories", "category_id"),
        ("assignments", "ticket_id", "tickets", "ticket_id"),
        ("assignments", "assigned_to_id", "employees", "emp_id"),
        ("slas", "ticket_id", "tickets", "ticket_id"),
        ("messages", "ticket_id", "tickets", "ticket_id"),
        ("resolutions", "ticket_id", "tickets", "ticket_id"),
        ("anomalies", "ticket_id", "tickets", "ticket_id"),
        ("policy_versions", "policy_id", "policy_documents", "policy_id"),
        ("knowledge_articles", "policy_version_id", "policy_versions", "version_id")
    ]

    for child_t, child_col, parent_t, parent_col in fk_checks:
        parent_vals = {r[parent_col] for r in tables[parent_t] if r.get(parent_col)}
        child_vals = {r[child_col] for r in tables[child_t] if r.get(child_col)}
        orphans = child_vals - parent_vals
        if orphans:
            msg = f"Orphan foreign keys in {child_t}.{child_col} -> {parent_t}.{parent_col}: {len(orphans)} orphans"
            errors.append(msg)
            print(f"  [FAIL] {msg}")
        else:
            print(f"  [PASS] {child_t}.{child_col} -> {parent_t}.{parent_col} OK")

    # 3. Anomaly Summary
    print("\n[3/4] Anomaly & Ground Truth Distribution:")
    anom_rows = tables["anomalies"]
    type_counts = {}
    for r in anom_rows:
        t = r.get("anomaly_type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"  Total Anomalies Flagged: {len(anom_rows)}")
    for t, c in type_counts.items():
        print(f"    - {t:30s}: {c}")

    # 4. Checksums
    print("\n[4/4] Dataset SHA-256 Checksums (Reproducibility):")
    for fname, sha in checksums.items():
        print(f"  {fname:25s} : {sha}")

    print("\n" + "=" * 65)
    if not errors:
        print("[+] ALL VALIDATION CHECKS PASSED PERFECTLY!")
        return True
    else:
        print(f"[-] FAILED WITH {len(errors)} INTEGRITY ERRORS.")
        return False

if __name__ == "__main__":
    import sys
    prof = sys.argv[1] if len(sys.argv) > 1 else "starter"
    validate_dataset(prof)
