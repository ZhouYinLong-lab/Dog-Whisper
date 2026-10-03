"""Evaluate both task-control outputs from one LoRA checkpoint."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import torch
from peft import PeftConfig, PeftModel
from torch.utils.data import DataLoader
from transformers import WhisperForConditionalGeneration, WhisperProcessor

sys.path.insert(0, str(Path(__file__).parent))
from train_whisper_baseline import ManifestDataset, char_cer, collate, read_rows  # noqa: E402
from train_whisper_task_control_lora import TARGET_FIELDS, add_control_tokens  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--processor-model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for checkpoint evaluation")
    device = torch.device("cuda")
    processor = WhisperProcessor.from_pretrained(args.processor_model, local_files_only=True)
    processor.tokenizer.set_prefix_tokens(language="zh", task="transcribe")
    control_ids = add_control_tokens(processor)
    config = PeftConfig.from_pretrained(args.checkpoint)
    base = WhisperForConditionalGeneration.from_pretrained(config.base_model_name_or_path, local_files_only=Path(config.base_model_name_or_path).exists())
    model = PeftModel.from_pretrained(base, args.checkpoint).to(device).eval()
    rows = read_rows(args.manifest, args.split, args.limit)
    results = {}
    for control, field in TARGET_FIELDS.items():
        loader = DataLoader(
            ManifestDataset(rows, args.workspace, processor, field), batch_size=args.batch_size,
            shuffle=False, num_workers=0,
            collate_fn=lambda batch: collate(batch, processor.tokenizer.pad_token_id),
        )
        predictions = []
        # Whisper supplies decoder_start_token_id (SOT) internally.  Forced
        # decoder ids therefore start at position 1; forcing SOT at position 0
        # makes generation collapse to a one-token sequence.
        forced = [
            [position, token]
            for position, token in enumerate(processor.tokenizer.prefix_tokens[1:], 1)
        ]
        forced.extend([
            [len(processor.tokenizer.prefix_tokens) + offset, token]
            for offset, token in enumerate(control_ids[control])
        ])
        with torch.no_grad():
            for batch in loader:
                generated = model.generate(
                    input_features=batch["input_features"].to(device),
                    forced_decoder_ids=forced, max_new_tokens=64, num_beams=1,
                    do_sample=False, no_repeat_ngram_size=3, repetition_penalty=1.05,
                )
                texts = processor.batch_decode(generated, skip_special_tokens=True)
                for row, text in zip(batch["rows"], texts):
                    predictions.append({
                        "utt_id": row["utt_id"], "control": control, "reference": row[field],
                        "hypothesis": text.strip(), "cer": char_cer(row[field], text),
                    })
        results[control] = {
            "samples": len(predictions),
            "mean_cer": sum(x["cer"] for x in predictions) / max(1, len(predictions)),
            "predictions": predictions,
        }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"checkpoint": str(args.checkpoint), "split": args.split, "samples": len(rows), "results": {
        key: {"samples": val["samples"], "mean_cer": val["mean_cer"]} for key, val in results.items()
    }}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, val in results.items():
        (args.output_dir / f"predictions_{key}.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in val["predictions"]) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
