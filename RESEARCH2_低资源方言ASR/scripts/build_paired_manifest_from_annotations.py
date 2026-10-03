"""Convert completed dialect/normalised annotation JSONL to a trainable manifest."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument(
        "--dev-speakers",
        default="",
        help="comma-separated speaker IDs assigned wholly to dev; keeps speaker-disjoint train/dev",
    )
    args = parser.parse_args()

    dev_speakers = {value.strip() for value in args.dev_speakers.split(",") if value.strip()}

    with args.annotation.open("r", encoding="utf-8", newline="") as handle:
        source_rows = [json.loads(line) for line in handle if line.strip()]
    errors = []
    rows = []
    seen = set()
    for row in source_rows:
        utt_id = row.get("utt_id")
        if not utt_id or utt_id in seen:
            errors.append({"type": "duplicate_or_missing_utt_id", "utt_id": utt_id})
        seen.add(utt_id)
        dialect = row.get("dialect_text", "").strip()
        norm = row.get("norm_text", "").strip()
        status = row.get("norm_status", "unannotated")
        if not dialect:
            errors.append({"type": "missing_dialect_text", "utt_id": utt_id})
        if not norm or status != "annotated":
            errors.append({"type": "incomplete_norm_text", "utt_id": utt_id, "status": status})
        if norm and status == "annotated":
            rows.append({
                "utt_id": utt_id,
                "region": row.get("region", "unknown"),
                "speaker_id": row.get("speaker_id", "unknown"),
                "audio_path": row["audio_path"],
                "text": dialect,
                "dialect_text": dialect,
                "norm_text": norm,
                "split": "dev" if row.get("speaker_id") in dev_speakers else row.get("source_split", "train"),
                "split_group": utt_id,
                "source": "Sichuan Dialect Scripted Speech Corpus + human normalization",
                "annotation_status": status,
            })

    error_counts = Counter(error["type"] for error in errors)
    result = {
        "source": str(args.annotation),
        "rows_read": len(source_rows),
        "rows_written": len(rows),
        "error_count": len(errors),
        "error_counts": dict(sorted(error_counts.items())),
        "error_examples": errors[:10],
        "dev_speakers": sorted(dev_speakers),
        "split_counts": dict(sorted(Counter(row["split"] for row in rows).items())),
        "ready_for_training": not errors and bool(rows),
    }
    if args.require_complete and errors:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.with_suffix(".summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    args.output.with_suffix(".summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
