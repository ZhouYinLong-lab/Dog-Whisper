"""Audit the data and experiment invariants for the RESEARCH2 workspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def duplicate_ids(rows: list[dict]) -> list[str]:
    ids = [row.get("utt_id") for row in rows]
    return sorted({utt_id for utt_id in ids if ids.count(utt_id) > 1})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--require-paired", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifests = {
        split: read_jsonl(args.root / "manifests" / f"sichuan_{split}.jsonl")
        for split in ("train", "dev", "test")
    }
    speakers = {split: {row.get("speaker_id") for row in rows} for split, rows in manifests.items()}
    split_intersections = {
        f"{left}_{right}": sorted(speakers[left] & speakers[right])
        for left, right in (("train", "dev"), ("train", "test"), ("dev", "test"))
    }

    template_path = args.root / "sichuan_norm_annotation_template" / "sichuan_norm_annotation_500.jsonl"
    queue_path = args.root / "sichuan_norm_annotation_template" / "norm_review_queue_500.jsonl"
    template = read_jsonl(template_path)
    queue = read_jsonl(queue_path) if queue_path.is_file() else []
    template_ids = {row.get("utt_id") for row in template}
    queue_ids = {row.get("utt_id") for row in queue}
    test_speakers = speakers["test"]
    template_speakers = {row.get("speaker_id") for row in template}
    nonblank_norm = sum(bool(str(row.get("norm_text", "")).strip()) for row in template)
    annotated = sum(row.get("norm_status") == "annotated" for row in template)

    errors: list[dict] = []
    for split, rows in manifests.items():
        duplicates = duplicate_ids(rows)
        if duplicates:
            errors.append({"type": "duplicate_manifest_ids", "split": split, "examples": duplicates[:10]})
    for name, overlap in split_intersections.items():
        if overlap:
            errors.append({"type": "speaker_overlap", "splits": name, "speakers": overlap})
    if template_speakers & test_speakers:
        errors.append({"type": "annotation_test_speaker_overlap", "speakers": sorted(template_speakers & test_speakers)})
    if template_ids != queue_ids:
        errors.append({"type": "template_queue_id_mismatch", "missing": sorted(template_ids - queue_ids)[:10], "unknown": sorted(queue_ids - template_ids)[:10]})
    if len(template) != 500:
        errors.append({"type": "unexpected_template_size", "rows": len(template)})
    if args.require_paired and (nonblank_norm != len(template) or annotated != len(template)):
        errors.append({"type": "paired_training_gate_not_ready", "rows": len(template), "nonblank_norm": nonblank_norm, "annotated": annotated})

    result = {
        "manifest_rows": {split: len(rows) for split, rows in manifests.items()},
        "manifest_speakers": {split: len(value) for split, value in speakers.items()},
        "split_speaker_intersections": split_intersections,
        "annotation_template_rows": len(template),
        "annotation_template_speakers": len(template_speakers),
        "annotation_test_speaker_overlap": sorted(template_speakers & test_speakers),
        "annotation_nonblank_norm": nonblank_norm,
        "annotation_annotated": annotated,
        "review_queue_rows": len(queue),
        "error_count": len(errors),
        "error_examples": errors[:20],
        "ready_for_paired_training": not errors and nonblank_norm == len(template) and annotated == len(template),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
