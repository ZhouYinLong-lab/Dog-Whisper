"""Tiny overfit smoke test for the Whisper fine-tuning path.

This is intentionally not a production training script. It verifies that the
manifest, FFmpeg decoding, Whisper feature extraction, labels, GPU forward,
backward, and checkpoint saving all work together before full training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from faster_whisper.audio import decode_audio
from transformers import WhisperForConditionalGeneration, WhisperProcessor


def load_examples(manifest: Path, workspace: Path, count: int) -> list[dict]:
    with manifest.open("r", encoding="utf-8", newline="") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    rows = [row for row in rows if row["split"] == "train"][:count]
    for row in rows:
        audio = decode_audio(str(workspace / row["audio_path"]), sampling_rate=16000)
        row["audio"] = audio
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="openai/whisper-tiny")
    parser.add_argument("--examples", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-5)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this smoke test")

    processor = WhisperProcessor.from_pretrained(args.model)
    model = WhisperForConditionalGeneration.from_pretrained(args.model).cuda()
    model.config.use_cache = False
    model.generation_config.language = "zh"
    model.generation_config.task = "transcribe"
    model.train()

    examples = load_examples(args.manifest, args.workspace, args.examples)
    if not examples:
        raise RuntimeError("No training examples were found")

    features = []
    labels = []
    for row in examples:
        features.append(
            processor.feature_extractor(
                row["audio"], sampling_rate=16000, return_tensors="pt"
            ).input_features[0]
        )
        token_ids = processor.tokenizer(row["text"]).input_ids
        labels.append(torch.tensor(token_ids, dtype=torch.long))

    input_features = torch.stack(features).cuda()
    max_length = max(label.numel() for label in labels)
    padded_labels = torch.full(
        (len(labels), max_length), processor.tokenizer.pad_token_id, dtype=torch.long
    )
    for index, label in enumerate(labels):
        padded_labels[index, : label.numel()] = label
    padded_labels[padded_labels == processor.tokenizer.pad_token_id] = -100
    padded_labels = padded_labels.cuda()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    losses = []
    for epoch in range(args.epochs):
        optimizer.zero_grad(set_to_none=True)
        output = model(input_features=input_features, labels=padded_labels)
        loss = output.loss
        loss.backward()
        optimizer.step()
        value = float(loss.detach().cpu())
        losses.append(value)
        print(f"epoch={epoch + 1}/{args.epochs} loss={value:.6f}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output_dir / "checkpoint")
    processor.save_pretrained(args.output_dir / "checkpoint")
    summary = {
        "model": args.model,
        "examples": len(examples),
        "epochs": args.epochs,
        "losses": losses,
        "loss_decreased": losses[-1] < losses[0],
        "device": "cuda",
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
