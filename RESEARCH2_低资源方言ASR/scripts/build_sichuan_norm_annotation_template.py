"""Build a deterministic, speaker/region-stratified Sichuan normalization template."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def rank(seed: int, utt_id: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"{seed}:{utt_id}".encode("utf-8")).digest()[:8], "big"
    )


def proportional_quota(counts: dict[str, int], total: int) -> dict[str, int]:
    total_available = sum(counts.values())
    raw = {key: value * total / total_available for key, value in counts.items()}
    quota = {key: int(value) for key, value in raw.items()}
    remainder = total - sum(quota.values())
    for key, _ in sorted(raw.items(), key=lambda item: item[1] - quota[item[0]], reverse=True)[:remainder]:
        quota[key] += 1
    return quota


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()

    with args.manifest.open("r", encoding="utf-8", newline="") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    rows = [row for row in rows if row.get("split") == "train"]
    if args.count <= 0 or args.count > len(rows):
        raise ValueError(f"count must be in [1, {len(rows)}]")

    by_region = defaultdict(list)
    for row in rows:
        by_region[row["region"]].append(row)
    region_quota = proportional_quota({key: len(value) for key, value in by_region.items()}, args.count)
    selected = []
    for region, region_rows in sorted(by_region.items()):
        by_speaker = defaultdict(list)
        for row in region_rows:
            by_speaker[row["speaker_id"]].append(row)
        speaker_quota = proportional_quota(
            {key: len(value) for key, value in by_speaker.items()}, region_quota[region]
        )
        for speaker, speaker_rows in by_speaker.items():
            ranked = sorted(speaker_rows, key=lambda row: rank(args.seed, row["utt_id"]))
            selected.extend(ranked[: speaker_quota[speaker]])

    selected.sort(key=lambda row: (row["region"], row["speaker_id"], row["utt_id"]))
    records = []
    for row in selected:
        records.append({
            "utt_id": row["utt_id"],
            "region": row["region"],
            "speaker_id": row["speaker_id"],
            "gender": row.get("gender"),
            "age": row.get("age"),
            "audio_path": row["audio_path"],
            "dialect_text": row["text"],
            "norm_text": "",
            "norm_status": "unannotated",
            "source_split": "train",
            "annotation_note": "保留原意与数字/专名；只将方言词、口语形式和地区用字改为可读的普通话书面表达；无法确定时标记 review。",
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "sichuan_norm_annotation_500.jsonl"
    out.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")
    summary = {
        "source_manifest": str(args.manifest),
        "source_split": "train",
        "seed": args.seed,
        "requested": args.count,
        "selected": len(records),
        "regions": dict(sorted(Counter(record["region"] for record in records).items())),
        "speakers": dict(sorted(Counter(record["speaker_id"] for record in records).items())),
        "norm_text_status": "all blank; requires human annotation",
        "test_contamination_guard": "selection reads only source rows with split=train; Sichuan test speakers are not included",
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
