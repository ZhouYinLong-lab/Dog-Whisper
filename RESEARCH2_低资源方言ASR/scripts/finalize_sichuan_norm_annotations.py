"""Materialize explicitly reviewed normalization decisions into a new file.

Safety rules:
* the source annotation template is read-only;
* only rows explicitly marked accepted/edited are materialized;
* accepted may use the model candidate, while edited must provide
  human_norm_text;
* --require-complete refuses any remaining unreviewed/review rows;
* candidate-only metadata is not copied into the formal annotation file.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


ALLOWED_STATUSES = {"unreviewed", "accepted", "edited", "review"}


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--review-queue", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    template = read_jsonl(args.template)
    queue = read_jsonl(args.review_queue)
    template_by_id = {row.get("utt_id"): row for row in template}
    queue_by_id = {row.get("utt_id"): row for row in queue}
    errors: list[dict] = []
    output_rows: list[dict] = []
    status_counts = Counter()

    if len(template_by_id) != len(template):
        errors.append({"type": "duplicate_template_utt_id"})
    if len(queue_by_id) != len(queue):
        errors.append({"type": "duplicate_queue_utt_id"})
    missing_queue = sorted(set(template_by_id) - set(queue_by_id))
    unknown_queue = sorted(set(queue_by_id) - set(template_by_id))
    for utt_id in missing_queue[:10]:
        errors.append({"type": "missing_queue_row", "utt_id": utt_id})
    for utt_id in unknown_queue[:10]:
        errors.append({"type": "unknown_queue_row", "utt_id": utt_id})

    for template_row in template:
        utt_id = template_row.get("utt_id")
        review_row = queue_by_id.get(utt_id)
        if review_row is None:
            continue
        for immutable_field in ("dialect_text", "audio_path", "speaker_id", "region"):
            if review_row.get(immutable_field) != template_row.get(immutable_field):
                errors.append(
                    {
                        "type": "immutable_field_changed",
                        "utt_id": utt_id,
                        "field": immutable_field,
                    }
                )
                break
        status = str(review_row.get("human_review_status", "unreviewed")).strip().lower()
        status_counts[status] += 1
        if status not in ALLOWED_STATUSES:
            errors.append({"type": "invalid_review_status", "utt_id": utt_id, "status": status})
            continue

        human_text = str(review_row.get("human_norm_text", "")).strip()
        candidate = str(review_row.get("norm_text_candidate", "")).strip()
        if status == "accepted":
            final_text = human_text or candidate
            if not final_text:
                errors.append({"type": "accepted_without_text", "utt_id": utt_id})
                continue
        elif status == "edited":
            final_text = human_text
            if not final_text:
                errors.append({"type": "edited_without_human_text", "utt_id": utt_id})
                continue
        elif status == "review":
            final_text = human_text
            if args.require_complete or not final_text:
                errors.append({"type": "unresolved_review", "utt_id": utt_id})
                continue
        else:
            if args.require_complete:
                errors.append({"type": "unreviewed_row", "utt_id": utt_id})
                continue
            final_text = ""

        formal = dict(template_row)
        formal["norm_text"] = final_text
        formal["norm_status"] = "annotated" if status in {"accepted", "edited"} else "review"
        formal["annotation_note"] = (
            "人工审核接受本地模型候选；请按音频与原始方言文本复核。"
            if status == "accepted"
            else "人工审核后的普通话规范文本。"
            if status == "edited"
            else "人工审核未决，暂不用于训练。"
        )
        output_rows.append(formal)

    if args.require_complete and len(output_rows) != len(template):
        errors.append(
            {
                "type": "incomplete_output",
                "rows_written": len(output_rows),
                "rows_expected": len(template),
            }
        )

    summary = {
        "template_rows": len(template),
        "queue_rows": len(queue),
        "rows_written": len(output_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "error_count": len(errors),
        "error_examples": errors[:20],
        "ready_for_training": args.require_complete and not errors and len(output_rows) == len(template),
    }
    summary_path = args.summary or args.output.with_suffix(args.output.suffix + ".summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print(json.dumps(summary, ensure_ascii=False))
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in output_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
