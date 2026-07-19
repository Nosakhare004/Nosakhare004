#!/usr/bin/env python3
"""
Merge a reviewed candidates JSON (produced by extract.py, then checked by
a human) into seed_financials.csv.

Rules enforced:
  - Only fills cells that are currently blank for the matching
    (ticker, period_end) row. Never overwrites an existing value.
  - Writes monetary values as full Naira integers: no commas, no naira
    sign, no abbreviations.
  - Leaves fields blank ("") where not applicable.
  - Preserves the existing column order and every existing row.

Usage:
    python merge_into_csv.py --csv ../data/seed_financials.csv --candidates candidates_GTCO_2025.json
"""
import argparse
import csv
import json
import sys
from pathlib import Path

from config import EXTRACTABLE_COLUMNS, PER_SHARE_COLUMNS


def format_value(column, value):
    if value is None:
        return ""
    if column in PER_SHARE_COLUMNS:
        return f"{float(value):.2f}"
    return str(int(round(float(value))))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", required=True, help="Path to seed_financials.csv")
    parser.add_argument("--candidates", required=True, help="Path to the reviewed candidates JSON")
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Also overwrite cells that already have a value (default: only fill blanks)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    candidates_path = Path(args.candidates)
    if not csv_path.exists():
        sys.exit(f"CSV not found: {csv_path}")
    if not candidates_path.exists():
        sys.exit(f"Candidates file not found: {candidates_path}")

    data = json.loads(candidates_path.read_text())
    ticker = data["ticker"]
    period_end = data["period_end"]

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    match_index = None
    for i, row in enumerate(rows):
        if row["ticker"] == ticker and row["period_end"] == period_end:
            match_index = i
            break
    if match_index is None:
        sys.exit(
            f"No row found for ticker={ticker} period_end={period_end} in {csv_path}. "
            "Add the row to the CSV first (preserving existing columns)."
        )

    row = rows[match_index]
    updated = []
    skipped_existing = []
    left_blank = []

    for column in EXTRACTABLE_COLUMNS:
        field = data["fields"].get(column, {})
        if field.get("not_applicable"):
            continue
        value = field.get("value")
        current = row.get(column, "")
        if value is None:
            left_blank.append(column)
            continue
        if current.strip() != "" and not args.allow_overwrite:
            skipped_existing.append(column)
            continue
        row[column] = format_value(column, value)
        updated.append(column)

    if data.get("source_doc") and not row.get("source_doc", "").strip():
        row["source_doc"] = data["source_doc"]
    if not row.get("extracted_by", "").strip() or row.get("extracted_by") == "manual":
        pass  # leave provenance columns as-is unless explicitly blank

    rows[match_index] = row

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {csv_path} row {ticker} {period_end}:")
    print(f"  filled:  {updated or '(none)'}")
    print(f"  blank (not found in PDF): {left_blank or '(none)'}")
    if skipped_existing:
        print(f"  skipped (already had a value, use --allow-overwrite to replace): {skipped_existing}")


if __name__ == "__main__":
    main()
