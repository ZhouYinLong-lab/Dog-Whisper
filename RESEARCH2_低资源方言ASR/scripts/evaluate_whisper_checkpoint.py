"""Evaluate a Hugging Face Whisper checkpoint on a manifest split."""

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--processor-model", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--text-field", default="text")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for checkpoint evaluation")
    device = torch.device("cuda")
    processor_source = args.processor_model or args.checkpoint
    processor = WhisperProcessor.from_pretrained(
        processor_source,
        local_files_only=processor_source.exists(),
    )
    adapter_config = args.checkpoint / "adapter_config.json"
    if adapter_config.exists():
        peft_config = PeftConfig.from_pretrained(args.checkpoint)
        base_model = WhisperForConditionalGeneration.from_pretrained(
            peft_config.base_model_name_or_path
        )
        model = PeftModel.from_pretrained(base_model, args.checkpoint).to(device)
    else:
        model = WhisperForConditionalGeneration.from_pretrained(args.checkpoint).to(device)
    model.eval()
    rows = read_rows(args.manifest, args.split, args.limit)
    loader = DataLoader(
        ManifestDataset(rows, args.workspace, processor, args.text_field),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        collate_fn=lambda batch: collate(batch, processor.tokenizer.pad_token_id),
    )

    predictions = []
    with torch.no_grad():
        for batch in loader:
            features = batch["input_features"].to(device)
            generated = model.generate(
                input_features=features,
                language="zh",
                task="transcribe",
                max_new_tokens=args.max_new_tokens,
                num_beams=1,
                do_sample=False,
                no_repeat_ngram_size=3,
                repetition_penalty=1.05,
            )
            texts = processor.batch_decode(generated, skip_special_tokens=True)
            for row, text in zip(batch["rows"], texts):
                text = text.strip()
                predictions.append(
                    {
                        "utt_id": row["utt_id"],
                        "region": row.get("region", "unknown"),
                        "speaker_id": row.get("speaker_id", "unknown"),
                        "reference": row[args.text_field],
                        "hypothesis": text,
                        "cer": char_cer(row[args.text_field], text),
                    }
                )

    by_region = defaultdict(list)
    for item in predictions:
        by_region[item["region"]].append(item["cer"])
    summary = {
        "checkpoint": str(args.checkpoint),
        "split": args.split,
        "samples": len(predictions),
        "mean_cer": sum(item["cer"] for item in predictions) / max(1, len(predictions)),
        "by_region": {
            region: sum(values) / len(values) for region, values in sorted(by_region.items())
        },
        "max_new_tokens": args.max_new_tokens,
        "no_repeat_ngram_size": 3,
        "repetition_penalty": 1.05,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".jsonl").write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in predictions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for item in predictions[:5]:
        print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
