"""
Ground Truth Management Module
Provides utilities to inspect, query, and verify ground truth anomaly labels.
Compatible with standard library (csv, json) or Pandas.
"""
import json
import csv
from pathlib import Path

def load_ground_truth(base_dir: str = "data", profile: str = "full"):
    csv_path = Path(base_dir) / "ground_truth" / profile / "ground_truth.csv"
    json_path = Path(base_dir) / "ground_truth" / profile / "ground_truth.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Ground truth not found at {json_path}. Please run generate_data.py first.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data

def summarize_ground_truth(base_dir: str = "data", profile: str = "full"):
    data = load_ground_truth(base_dir, profile)
    total = len(data)
    ambiguous_count = sum(1 for r in data if r.get("is_ambiguous"))
    sensitive_count = sum(1 for r in data if r.get("is_sensitive"))
    anomaly_count = sum(1 for r in data if r.get("ground_truth_label") == "ANOMALOUS")

    type_counts = {}
    for r in data:
        for anomaly_type in filter(None, r.get("anomaly_types", "").split(";")):
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1

    print("=" * 60)
    print(f"GROUND TRUTH DATASET SUMMARY ({profile.upper()})")
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
    import argparse

    parser = argparse.ArgumentParser(description="Summarize synthetic ground-truth labels")
    parser.add_argument("--profile", choices=["starter", "full"], default="full")
    parser.add_argument("--base-dir", default="data")
    args = parser.parse_args()
    summarize_ground_truth(args.base_dir, args.profile)
