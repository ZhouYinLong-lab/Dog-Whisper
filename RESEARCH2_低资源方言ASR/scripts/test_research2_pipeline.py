"""Small positive-path regression test for annotation -> paired manifest.

The fixture is created in a temporary directory and never enters the formal
dataset. No model or GPU is used.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def run(script: Path, args: list[str]) -> None:
    completed = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)
    if completed.returncode != 0:
        raise AssertionError(f"{script.name} failed:\n{completed.stdout}\n{completed.stderr}")


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    finalizer = script_dir / "finalize_sichuan_norm_annotations.py"
    builder = script_dir / "build_paired_manifest_from_annotations.py"
    with tempfile.TemporaryDirectory(prefix="research2_pipeline_") as temp:
        root = Path(temp)
        template = root / "template.jsonl"
        queue = root / "queue.jsonl"
        final = root / "final.jsonl"
        manifest = root / "paired.jsonl"
        rows = [
            {"utt_id": "u1", "region": "成都", "speaker_id": "G0001", "audio_path": "a1.wav", "dialect_text": "甲嘛", "norm_text": "", "norm_status": "unannotated", "source_split": "train"},
            {"utt_id": "u2", "region": "成都", "speaker_id": "G0001", "audio_path": "a2.wav", "dialect_text": "乙嘛", "norm_text": "", "norm_status": "unannotated", "source_split": "train"},
            {"utt_id": "u3", "region": "泸州", "speaker_id": "G0002", "audio_path": "a3.wav", "dialect_text": "丙嘛", "norm_text": "", "norm_status": "unannotated", "source_split": "train"},
            {"utt_id": "u4", "region": "泸州", "speaker_id": "G0002", "audio_path": "a4.wav", "dialect_text": "丁嘛", "norm_text": "", "norm_status": "unannotated", "source_split": "train"},
        ]
        reviewed = []
        for index, row in enumerate(rows, 1):
            item = dict(row)
            item.update(
                {
                    "norm_text_candidate": f"规范文本{index}",
                    "human_norm_text": "" if index == 1 else f"人工文本{index}",
                    "human_review_status": "accepted" if index == 1 else "edited",
                    "reviewer_note": "fixture",
                }
            )
            reviewed.append(item)
        write_jsonl(template, rows)
        write_jsonl(queue, reviewed)

        run(finalizer, ["--template", str(template), "--review-queue", str(queue), "--output", str(final), "--require-complete"])
        run(builder, ["--annotation", str(final), "--output", str(manifest), "--dev-speakers", "G0002", "--require-complete"])

        final_rows = [json.loads(line) for line in final.read_text(encoding="utf-8").splitlines() if line.strip()]
        manifest_rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(final_rows) == 4
        assert all(row["norm_status"] == "annotated" and row["norm_text"] for row in final_rows)
        assert {row["split"] for row in manifest_rows} == {"train", "dev"}
        assert {row["speaker_id"] for row in manifest_rows if row["split"] == "dev"} == {"G0002"}
        assert {row["speaker_id"] for row in manifest_rows if row["split"] == "train"} == {"G0001"}
        assert all(set(("utt_id", "audio_path", "text", "dialect_text", "norm_text", "split")) <= row.keys() for row in manifest_rows)
    print(json.dumps({"status": "passed", "fixture_rows": 4, "dev_speakers": ["G0002"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
