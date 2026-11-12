"""
Ground Truth Management Module
Provides utilities to inspect, query, and verify ground truth anomaly labels.
Compatible with standard library (csv, json) or Pandas.
"""
import json
import csv
from pathlib import Path

def load_ground_truth(base_dir: str = "data"):
    csv_path = Path(base_dir) / "ground_truth" / "ground_truth.csv"
    json_path = Path(base_dir) / "ground_truth" / "ground_truth.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Ground truth not found at {json_path}. Please run generate_data.py first.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data

def summarize_ground_truth(base_dir: str = "data"):
    data = load_ground_truth(base_dir)
    total = len(data)
    ambiguous_count = sum(1 for r in data if r.get("is_ambiguous"))
    sensitive_count = sum(1 for r in data if r.get("is_sensitive"))
    anomaly_count = sum(1 for r in data if r.get("has_anomaly"))

    type_counts = {}
    for r in data:
        if r.get("has_anomaly"):
            atype = r.get("anomaly_type", "NONE")
            type_counts[atype] = type_counts.get(atype, 0) + 1

    print("=" * 60)
    print("GROUND TRUTH DATASET SUMMARY")
    print("=" * 60)
    print(f"Total labeled tickets: {total}")
    print(f"Ambiguous tickets:     {ambiguous_count} ({round(ambiguous_count / total * 100, 1)}%)")
    print(f"Sensitive tickets:     {sensitive_count} ({round(sensitive_count / total * 100, 1)}%)")
    print(f"Total Anomalies:       {anomaly_count} ({round(anomaly_count / total * 100, 1)}%)")
    print("\nAnomaly Breakdown:")
    for atype, cnt in type_counts.items():
        print(f"  - {atype:30s}: {cnt}")
    print("=" * 60)

if __name__ == "__main__":
    summarize_ground_truth()
