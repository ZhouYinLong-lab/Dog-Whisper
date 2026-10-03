"""Create a risk-ranked, review-only queue for normalization candidates.

The input files contain model suggestions. This script never writes to the
formal annotation template and never treats a candidate as a training label.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


# Restrict this hard flag to Arabic numerals. Chinese numeral wording often
# changes during harmless normalization (for example "俩" -> "两"), so
# treating every Chinese number character as a mismatch creates false flags.
DIGIT_PATTERN = re.compile(r"[0-9０-９]+")
ENGLISH_PATTERN = re.compile(r"[A-Za-z]{3,}")


def digits(text: str) -> list[str]:
    return DIGIT_PATTERN.findall(text)


def audit(row: dict) -> dict:
    source = str(row.get("dialect_text", "")).strip()
    candidate = str(row.get("norm_text_candidate", "")).strip()
    flags: list[str] = []
    if row.get("candidate_status") != "model_suggested" or not candidate:
        flags.append("candidate_unavailable")
    if row.get("candidate_error"):
        flags.append("model_error")
    if candidate and ENGLISH_PATTERN.search(candidate):
        flags.append("english_output")
    if source and candidate:
        ratio = len(candidate) / len(source)
        if ratio < 0.50:
            flags.append("too_short")
        elif ratio > 1.80:
            flags.append("too_long")
        if digits(source) != digits(candidate):
            flags.append("digit_mismatch")
        similarity = SequenceMatcher(None, source, candidate).ratio()
        if similarity < 0.55:
            flags.append("large_edit")
    else:
        ratio = None
        similarity = None

    changed = bool(candidate and candidate != source)
    if not changed and candidate:
        flags.append("unchanged_candidate")
    if any(flag in flags for flag in ("candidate_unavailable", "model_error", "english_output", "digit_mismatch", "too_short", "too_long", "large_edit")):
        priority = "high"
    elif changed:
        priority = "medium"
    else:
        priority = "low"

    result = dict(row)
    result.update(
        {
            "candidate_changed": changed,
            "candidate_length_ratio": round(ratio, 4) if ratio is not None else None,
            "candidate_similarity": round(similarity, 4) if similarity is not None else None,
            "candidate_flags": flags,
            "review_priority": priority,
            "human_norm_text": "",
            "human_review_status": "unreviewed",
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows: list[dict] = []
    for path in args.input:
        if not path.is_file():
            parser.error(f"input not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())

    audited = [audit(row) for row in rows]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in audited:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    priority_counts = Counter(row["review_priority"] for row in audited)
    flag_counts = Counter(flag for row in audited for flag in row["candidate_flags"])
    summary = {
        "rows": len(audited),
        "priority_counts": dict(sorted(priority_counts.items())),
        "flag_counts": dict(sorted(flag_counts.items())),
        "formal_fields_preserved": True,
        "training_ready": False,
        "note": "review-only queue; human_norm_text remains blank",
    }
    summary_path = args.output.with_suffix(args.output.suffix + ".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
