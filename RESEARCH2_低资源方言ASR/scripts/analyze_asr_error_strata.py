"""Summarize an utterance-level ASR result by region, speaker, and text length."""

from __future__ import annotations

import argparse
import json
import statistics
import wave
from collections import defaultdict
from pathlib import Path


def mean(values: list[float]) -> float | None:
    return round(statistics.mean(values), 6) if values else None


def summarize(rows: list[dict], key_fn) -> list[dict]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[str(key_fn(row))].append(float(row["cer"]))
    return [
        {"group": key, "samples": len(values), "mean_cer": mean(values), "median_cer": round(statistics.median(values), 6)}
        for key, values in sorted(groups.items())
    ]


def length_bin(row: dict) -> str:
    length = len(str(row.get("reference", "")))
    if length <= 20:
        return "0-20"
    if length <= 40:
        return "21-40"
    if length <= 80:
        return "41-80"
    return "81+"


def duration_bin(row: dict) -> str:
    duration = row.get("audio_duration_sec")
    if duration is None:
        return "unknown"
    if duration < 2:
        return "<2s"
    if duration < 4:
        return "2-4s"
    if duration < 8:
        return "4-8s"
    return "8s+"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--audio-root", type=Path)
    parser.add_argument("--top-errors", type=int, default=20)
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8", newline="") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if not rows:
        parser.error("input has no rows")

    if args.manifest:
        if not args.audio_root:
            parser.error("--audio-root is required with --manifest")
        with args.manifest.open("r", encoding="utf-8", newline="") as handle:
            manifest = [json.loads(line) for line in handle if line.strip()]
        manifest_by_id = {row.get("utt_id"): row for row in manifest}
        for row in rows:
            manifest_row = manifest_by_id.get(row.get("utt_id"))
            if not manifest_row:
                row["audio_duration_sec"] = None
                continue
            audio_path = args.audio_root / str(manifest_row.get("audio_path", ""))
            try:
                with wave.open(str(audio_path), "rb") as audio:
                    rate = audio.getframerate()
                    row["audio_duration_sec"] = round(audio.getnframes() / rate, 4) if rate else None
            except (OSError, wave.Error):
                row["audio_duration_sec"] = None

    top = sorted(rows, key=lambda row: float(row["cer"]), reverse=True)[: args.top_errors]
    report = {
        "input": str(args.input),
        "samples": len(rows),
        "overall_mean_cer": mean([float(row["cer"]) for row in rows]),
        "overall_median_cer": round(statistics.median(float(row["cer"]) for row in rows), 6),
        "by_region": summarize(rows, lambda row: row.get("region", "unknown")),
        "by_speaker": summarize(rows, lambda row: row.get("speaker_id", "unknown")),
        "by_reference_length": summarize(rows, length_bin),
        "by_audio_duration": summarize(rows, duration_bin),
        "top_errors": [
            {
                "utt_id": row.get("utt_id"),
                "region": row.get("region"),
                "speaker_id": row.get("speaker_id"),
                "cer": row.get("cer"),
                "audio_duration_sec": row.get("audio_duration_sec"),
                "reference": row.get("reference"),
                "hypothesis": row.get("hypothesis"),
            }
            for row in top
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"samples": len(rows), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
