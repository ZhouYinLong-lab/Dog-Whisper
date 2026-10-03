"""Build a conservative Wu dialect/standard-Mandarin paired pilot.

The benchmark stores dialect ASR rows under a parent utterance id and AST rows
under the same id with a ``_segXX`` suffix.  This script only keeps parents
with exactly one AST segment and a close audio-duration match, avoiding
concatenating uncertain segment boundaries.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import wave
from pathlib import Path

import pandas as pd


SEGMENT_SUFFIX = re.compile(r"_seg(?:\d+)?(?:_seg\d+)?$")


def base_utt_id(value: str) -> str:
    return SEGMENT_SUFFIX.sub("", value)


def wav_duration(audio: bytes) -> float:
    with wave.open(io.BytesIO(audio)) as handle:
        return handle.getnframes() / handle.getframerate()


def split_for(base_id: str, seed: int) -> str:
    digest = hashlib.sha256(f"{seed}:{base_id}".encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "dev"
    return "test"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-duration-ratio", type=float, default=0.95)
    parser.add_argument("--max-duration-ratio", type=float, default=1.05)
    parser.add_argument("--split-seed", type=int, default=20260924)
    args = parser.parse_args()

    asr = pd.read_parquet(args.input_dir / "asr.parquet")
    ast = pd.read_parquet(args.input_dir / "ast.parquet")
    ast = ast.copy()
    ast["base_utt_id"] = ast["utt_id"].map(base_utt_id)
    ast_counts = ast["base_utt_id"].value_counts()
    asr_rows = {row.utt_id: row for row in asr.itertuples(index=False)}

    audio_dir = args.output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    manifests = {"train": [], "dev": [], "test": []}
    rejected = {"multiple_ast_segments": 0, "no_asr_parent": 0, "duration_mismatch": 0}

    for row in ast.itertuples(index=False):
        base_id = row.base_utt_id
        if ast_counts[base_id] != 1:
            rejected["multiple_ast_segments"] += 1
            continue
        if base_id not in asr_rows:
            rejected["no_asr_parent"] += 1
            continue

        parent = asr_rows[base_id]
        parent_duration = wav_duration(parent.audio)
        ast_duration = wav_duration(row.audio)
        ratio = ast_duration / parent_duration if parent_duration else 0.0
        if not (args.min_duration_ratio <= ratio <= args.max_duration_ratio):
            rejected["duration_mismatch"] += 1
            continue

        split = split_for(base_id, args.split_seed)
        audio_name = f"{base_id}.wav"
        (audio_dir / audio_name).write_bytes(row.audio)
        record = {
            "utt_id": base_id,
            "asr_utt_id": base_id,
            "ast_utt_id": row.utt_id,
            "audio_path": f"audio/{audio_name}",
            "text": parent.label,
            "dialect_text": parent.label,
            "norm_text": row.label,
            "region": "wu",
            "speaker_id": "unknown",
            "duration_ratio": ratio,
            "split_group": base_id,
            "split": split,
            "source": "ASLP-lab/WenetSpeech-Wu-Bench",
            "license": "apache-2.0",
        }
        manifests[split].append(record)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for split, records in manifests.items():
        records.sort(key=lambda item: item["utt_id"])
        with (args.output_dir / f"wu_paired_{split}.jsonl").open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    all_records = [record for records in manifests.values() for record in records]
    all_records.sort(key=lambda item: item["utt_id"])
    with (args.output_dir / "wu_paired_all.jsonl").open("w", encoding="utf-8") as handle:
        for record in all_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "source": "ASLP-lab/WenetSpeech-Wu-Bench",
        "license": "apache-2.0",
        "min_duration_ratio": args.min_duration_ratio,
        "max_duration_ratio": args.max_duration_ratio,
        "split_seed": args.split_seed,
        "counts": {split: len(records) for split, records in manifests.items()},
        "total": sum(len(records) for records in manifests.values()),
        "rejected": rejected,
        "warning": "No speaker metadata is available in these parquet rows; splits are parent-utterance-disjoint, not speaker-disjoint.",
    }
    (args.output_dir / "wu_paired_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
