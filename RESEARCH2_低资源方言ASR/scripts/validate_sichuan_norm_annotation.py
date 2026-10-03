"""Validate the manually filled Sichuan dialect/normalised-text template."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation", type=Path, required=True)
    parser.add_argument("--sichuan-root", type=Path, required=True)
    parser.add_argument("--test-manifest", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.annotation.open("r", encoding="utf-8", newline="") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    with args.test_manifest.open("r", encoding="utf-8", newline="") as handle:
        test_rows = [json.loads(line) for line in handle if line.strip()]
    errors = []
    seen = set()
    test_speakers = {row["speaker_id"] for row in test_rows}
    for row in rows:
        utt_id = row.get("utt_id")
        if not utt_id or utt_id in seen:
            errors.append({"type": "duplicate_or_missing_utt_id", "utt_id": utt_id})
        seen.add(utt_id)
        if not row.get("dialect_text", "").strip():
            errors.append({"type": "missing_dialect_text", "utt_id": utt_id})
        if row.get("speaker_id") in test_speakers:
            errors.append({"type": "test_speaker_overlap", "utt_id": utt_id, "speaker_id": row.get("speaker_id")})
        audio = args.sichuan_root / row.get("audio_path", "")
        if not audio.exists():
            errors.append({"type": "missing_audio", "utt_id": utt_id, "audio_path": row.get("audio_path")})

    blank = sum(not row.get("norm_text", "").strip() for row in rows)
    review = sum(row.get("norm_status") == "review" for row in rows)
    annotated = sum(row.get("norm_status") == "annotated" and row.get("norm_text", "").strip() for row in rows)
    if args.require_complete and blank:
        errors.append({"type": "blank_norm_text", "count": blank})
    result = {
        "rows": len(rows),
        "blank_norm_text": blank,
        "review_rows": review,
        "annotated_rows": annotated,
        "regions": dict(sorted(Counter(row.get("region", "unknown") for row in rows).items())),
        "speakers": len({row.get("speaker_id") for row in rows}),
        "errors": errors,
        "valid_structure": not errors,
        "ready_for_training": not errors and blank == 0 and review == 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
