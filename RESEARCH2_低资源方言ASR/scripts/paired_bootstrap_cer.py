"""Reproduce paired CER improvements from two JSONL prediction files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_cer(path: Path) -> dict[str, float]:
    values = {}
    # Iterate over physical newline characters. str.splitlines() also splits
    # on Unicode line separators such as U+2028, which may legitimately occur
    # inside a JSON-escaped prediction string and would corrupt JSONL parsing.
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                values[row["utt_id"]] = float(row["cer"])
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description="reference CER minus candidate CER")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260924)
    parser.add_argument("--bootstrap", type=int, default=10000)
    args = parser.parse_args()

    reference = load_cer(args.reference)
    candidate = load_cer(args.candidate)
    ids = sorted(set(reference) & set(candidate))
    if not ids:
        raise RuntimeError("No common utt_id values")
    delta = np.asarray([reference[key] - candidate[key] for key in ids], dtype=float)
    rng = np.random.default_rng(args.seed)
    samples = delta[rng.integers(0, len(delta), size=(args.bootstrap, len(delta)))].mean(axis=1)
    result = {
        "reference": str(args.reference),
        "candidate": str(args.candidate),
        "n": len(delta),
        "bootstrap": args.bootstrap,
        "seed": args.seed,
        "definition": "reference CER - candidate CER; positive means candidate improves",
        "mean_improvement": float(delta.mean()),
        "wins": int((delta > 0).sum()),
        "ties": int((delta == 0).sum()),
        "losses": int((delta < 0).sum()),
        "bootstrap95ci": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
