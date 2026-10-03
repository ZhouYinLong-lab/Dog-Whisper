"""Export/import a human-friendly TSV review sheet without changing labels silently."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "utt_id",
    "region",
    "speaker_id",
    "dialect_text",
    "norm_text_candidate",
    "candidate_flags",
    "review_priority",
    "human_norm_text",
    "human_review_status",
    "reviewer_note",
]


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def export_tsv(queue_path: Path, output_path: Path, priorities: set[str] | None, limit: int, offset: int) -> int:
    rows = read_jsonl(queue_path)
    if priorities:
        rows = [row for row in rows if row.get("review_priority") in priorities]
    rows = rows[offset : offset + limit if limit > 0 else None]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            values = dict(row)
            values["candidate_flags"] = ",".join(row.get("candidate_flags", []))
            values["reviewer_note"] = row.get("reviewer_note", "")
            writer.writerow({field: values.get(field, "") for field in FIELDS})
    print(json.dumps({"mode": "export", "rows": len(rows), "output": str(output_path), "priorities": sorted(priorities or [])}, ensure_ascii=False))
    return 0


def import_tsv(queue_path: Path, tsv_path: Path, output_path: Path, allow_partial: bool) -> int:
    queue = read_jsonl(queue_path)
    by_id = {row.get("utt_id"): row for row in queue}
    errors: list[dict] = []
    updates: dict[str, dict] = {}
    with tsv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing_fields = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing_fields:
            errors.append({"type": "missing_fields", "fields": missing_fields})
        for line_number, row in enumerate(reader, 2):
            utt_id = (row.get("utt_id") or "").strip()
            if not utt_id:
                errors.append({"type": "blank_utt_id", "line": line_number})
                continue
            if utt_id not in by_id:
                errors.append({"type": "unknown_utt_id", "line": line_number, "utt_id": utt_id})
                continue
            if utt_id in updates:
                errors.append({"type": "duplicate_utt_id", "line": line_number, "utt_id": utt_id})
                continue
            if row.get("dialect_text", "") != by_id[utt_id].get("dialect_text", ""):
                errors.append({"type": "dialect_text_changed", "line": line_number, "utt_id": utt_id})
                continue
            status = (row.get("human_review_status") or "unreviewed").strip().lower()
            if status not in {"unreviewed", "accepted", "edited", "review"}:
                errors.append({"type": "invalid_review_status", "line": line_number, "utt_id": utt_id, "status": status})
                continue
            updates[utt_id] = {
                "human_norm_text": (row.get("human_norm_text") or "").strip(),
                "human_review_status": status,
                "reviewer_note": row.get("reviewer_note", "").strip(),
            }

    if not updates:
        errors.append({"type": "empty_sheet"})
    if not allow_partial and len(updates) != len(queue):
        errors.append({"type": "incomplete_sheet", "queue_rows": len(queue), "sheet_rows": len(updates)})
    if errors:
        summary = {"mode": "import", "rows_updated": 0, "allow_partial": allow_partial, "error_count": len(errors), "error_examples": errors[:20]}
        print(json.dumps(summary, ensure_ascii=False))
        return 1

    output_rows = []
    for row in queue:
        updated = dict(row)
        if row["utt_id"] in updates:
            updated.update(updates[row["utt_id"]])
        output_rows.append(updated)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in output_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"mode": "import", "rows_updated": len(updates), "queue_rows": len(output_rows), "allow_partial": allow_partial, "output": str(output_path)}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--queue", required=True, type=Path)
    export_parser.add_argument("--output", required=True, type=Path)
    export_parser.add_argument("--priority", action="append", choices=["high", "medium", "low"])
    export_parser.add_argument("--limit", type=int, default=-1)
    export_parser.add_argument("--offset", type=int, default=0)
    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--queue", required=True, type=Path)
    import_parser.add_argument("--tsv", required=True, type=Path)
    import_parser.add_argument("--output", required=True, type=Path)
    import_parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    if args.mode == "export":
        if args.offset < 0 or args.limit == 0:
            parser.error("--offset must be non-negative and --limit must be -1 or positive")
        return export_tsv(args.queue, args.output, set(args.priority or []), args.limit, args.offset)
    return import_tsv(args.queue, args.tsv, args.output, args.allow_partial)


if __name__ == "__main__":
    raise SystemExit(main())
