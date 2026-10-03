"""Run a small Whisper zero-shot baseline on a manifest split."""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

from faster_whisper import WhisperModel


def cer(reference: str, hypothesis: str) -> float:
    ref = list(reference)
    hyp = list(hypothesis)
    previous = list(range(len(hyp) + 1))
    for i, ref_char in enumerate(ref, 1):
        current = [i]
        for j, hyp_char in enumerate(hyp, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (ref_char != hyp_char),
                )
            )
        previous = current
    return previous[-1] / max(1, len(ref))


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="small")
    parser.add_argument("--split", default="test")
    parser.add_argument("--max-samples", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()

    with args.manifest.open("r", encoding="utf-8", newline="") as handle:
        records = [json.loads(line) for line in handle if line.strip()]
    if args.split != "all":
        records = [record for record in records if record["split"] == args.split]
    records.sort(key=lambda record: (record["region"], record["speaker_id"], record["utt_id"]))
    if args.max_samples > 0:
        grouped = {}
        for record in records:
            grouped.setdefault(record["region"], []).append(record)
        selected = []
        regions = sorted(grouped)
        index = 0
        while len(selected) < args.max_samples and regions:
            added = False
            for region in regions:
                items = grouped[region]
                if index < len(items):
                    selected.append(items[index])
                    added = True
                    if len(selected) >= args.max_samples:
                        break
            if not added:
                break
            index += 1
        records = selected

    model = WhisperModel(args.model, device="cuda", compute_type="float16")
    results = []
    for index, record in enumerate(records, 1):
        audio_path = args.workspace / record["audio_path"]
        start = time.perf_counter()
        segments, info = model.transcribe(
            str(audio_path), language="zh", beam_size=5, vad_filter=False
        )
        hypothesis = "".join(segment.text.strip() for segment in segments)
        elapsed = time.perf_counter() - start
        reference = str(record["text"])
        result = {
            **record,
            "model": args.model,
            "reference": reference,
            "hypothesis": hypothesis,
            "cer": cer(normalize(reference), normalize(hypothesis)),
            "audio_duration_sec": round(float(info.duration), 3),
            "inference_sec": round(elapsed, 3),
        }
        results.append(result)
        print(
            f"[{index}/{len(records)}] {record['utt_id']} "
            f"CER={result['cer']:.4f} time={elapsed:.2f}s"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pred_path = args.output.with_suffix(".jsonl")
    with pred_path.open("w", encoding="utf-8", newline="\n") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    mean_cer = sum(result["cer"] for result in results) / max(1, len(results))
    total_ref_chars = sum(len(normalize(result["reference"])) for result in results)
    weighted_cer = sum(
        result["cer"] * len(normalize(result["reference"])) for result in results
    ) / max(1, total_ref_chars)
    summary = {
        "model": args.model,
        "split": args.split,
        "samples": len(results),
        "mean_utterance_cer": mean_cer,
        "weighted_cer": weighted_cer,
        "mean_inference_sec": sum(result["inference_sec"] for result in results)
        / max(1, len(results)),
        "regions": dict(Counter(result["region"] for result in results)),
        "speakers": sorted({result["speaker_id"] for result in results}),
        "note": "Preliminary zero-shot sample, not a full test-set result.",
    }
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
