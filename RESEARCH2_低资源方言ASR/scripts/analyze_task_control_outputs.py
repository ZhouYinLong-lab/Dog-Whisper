"""Measure whether two task-control decoding modes actually diverge."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def compact(value: str) -> str:
    return "".join(value.split())


def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for i, char in enumerate(left, 1):
        current = [i]
        for j, other in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (char != other)))
        previous = current
    return previous[-1]


def load(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["utt_id"]: row for row in (json.loads(line) for line in handle if line.strip())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dialect", type=Path, required=True)
    parser.add_argument("--norm", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    dialect = load(args.dialect)
    norm = load(args.norm)
    ids = sorted(set(dialect) & set(norm))
    rows = []
    for utt_id in ids:
        d = compact(dialect[utt_id]["hypothesis"])
        n = compact(norm[utt_id]["hypothesis"])
        distance = edit_distance(d, n)
        denominator = max(1, len(d), len(n))
        rows.append({
            "utt_id": utt_id,
            "dialect_cer": dialect[utt_id]["cer"],
            "norm_cer": norm[utt_id]["cer"],
            "dialect_hypothesis": dialect[utt_id]["hypothesis"],
            "norm_hypothesis": norm[utt_id]["hypothesis"],
            "exact_same": d == n,
            "dialect_length": len(d),
            "norm_length": len(n),
            "hypothesis_edit_distance": distance,
            "relative_divergence": distance / denominator,
        })
    exact = sum(row["exact_same"] for row in rows)
    result = {
        "samples": len(rows),
        "exact_same_hypothesis": exact,
        "exact_same_rate": exact / max(1, len(rows)),
        "different_hypothesis": len(rows) - exact,
        "mean_dialect_length": sum(row["dialect_length"] for row in rows) / max(1, len(rows)),
        "mean_norm_length": sum(row["norm_length"] for row in rows) / max(1, len(rows)),
        "mean_hypothesis_edit_distance": sum(row["hypothesis_edit_distance"] for row in rows) / max(1, len(rows)),
        "mean_relative_divergence": sum(row["relative_divergence"] for row in rows) / max(1, len(rows)),
        "dialect_cer_mean": sum(row["dialect_cer"] for row in rows) / max(1, len(rows)),
        "norm_cer_mean": sum(row["norm_cer"] for row in rows) / max(1, len(rows)),
        "most_divergent_examples": sorted(rows, key=lambda row: row["relative_divergence"], reverse=True)[:10],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
