"""Train a small Whisper ASR baseline on a manifest.

This is a deliberately explicit training loop so that every data and
optimization choice is visible in the experiment log. Audio is decoded with
the FFmpeg path bundled by faster-whisper because torchaudio backends are not
available in the current environment.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from faster_whisper.audio import decode_audio
from torch.utils.data import DataLoader, Dataset
from transformers import WhisperForConditionalGeneration, WhisperProcessor


def char_cer(reference: str, hypothesis: str) -> float:
    ref = list("".join(reference.split()))
    hyp = list("".join(hypothesis.split()))
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


class ManifestDataset(Dataset):
    def __init__(
        self,
        rows: list[dict],
        workspace: Path,
        processor: WhisperProcessor,
        text_field: str = "text",
    ):
        self.rows = rows
        self.workspace = workspace
        self.processor = processor
        self.text_field = text_field

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict:
        row = self.rows[index]
        audio = decode_audio(
            str(self.workspace / row["audio_path"]), sampling_rate=16000
        )
        features = self.processor.feature_extractor(
            audio, sampling_rate=16000, return_tensors="pt"
        ).input_features[0]
        labels = self.processor.tokenizer(row[self.text_field]).input_ids
        return {"features": features, "labels": labels, "row": row}


def collate(batch: list[dict], pad_token_id: int) -> dict:
    features = torch.stack([item["features"] for item in batch])
    max_len = max(len(item["labels"]) for item in batch)
    labels = torch.full(
        (len(batch), max_len), pad_token_id, dtype=torch.long
    )
    for index, item in enumerate(batch):
        values = torch.tensor(item["labels"], dtype=torch.long)
        labels[index, : values.numel()] = values
    labels[labels == pad_token_id] = -100
    return {"input_features": features, "labels": labels, "rows": [item["row"] for item in batch]}


def read_rows(path: Path, split: str, limit: int) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    rows = [row for row in rows if row["split"] == split]
    if limit > 0:
        rows = rows[:limit]
    return rows


@torch.no_grad()
def evaluate(
    model: WhisperForConditionalGeneration,
    loader: DataLoader,
    processor: WhisperProcessor,
    device: torch.device,
    max_decode_batches: int,
    text_field: str = "text",
) -> dict:
    model.eval()
    losses = []
    predictions = []
    for batch_index, batch in enumerate(loader):
        features = batch["input_features"].to(device)
        labels = batch["labels"].to(device)
        output = model(input_features=features, labels=labels)
        losses.append(float(output.loss.detach().cpu()))
        if batch_index < max_decode_batches:
            generated = model.generate(
                input_features=features,
                language="zh",
                task="transcribe",
                max_new_tokens=128,
            )
            texts = processor.batch_decode(generated, skip_special_tokens=True)
            for row, text in zip(batch["rows"], texts):
                predictions.append(
                    {
                        "utt_id": row["utt_id"],
                        "region": row.get("region", "unknown"),
                        "reference": row[text_field],
                        "hypothesis": text.strip(),
                        "cer": char_cer(row[text_field], text),
                    }
                )
    model.train()
    return {
        "loss": sum(losses) / max(1, len(losses)),
        "decoded_samples": len(predictions),
        "mean_decoded_cer": (
            sum(item["cer"] for item in predictions) / max(1, len(predictions))
        ),
        "predictions": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="openai/whisper-tiny")
    parser.add_argument("--train-limit", type=int, default=256)
    parser.add_argument("--dev-limit", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--text-field", default="text")
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the baseline training run")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda")

    processor = WhisperProcessor.from_pretrained(args.model)
    processor.tokenizer.set_prefix_tokens(language="zh", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(args.model).to(device)
    model.config.use_cache = False
    model.generation_config.language = "zh"
    model.generation_config.task = "transcribe"

    train_rows = read_rows(args.manifest, "train", args.train_limit)
    dev_rows = read_rows(args.manifest, "dev", args.dev_limit)
    if not train_rows or not dev_rows:
        raise RuntimeError("Both train and dev rows are required")

    train_loader = DataLoader(
        ManifestDataset(train_rows, args.workspace, processor, args.text_field),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        collate_fn=lambda batch: collate(batch, processor.tokenizer.pad_token_id),
    )
    dev_loader = DataLoader(
        ManifestDataset(dev_rows, args.workspace, processor, args.text_field),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        collate_fn=lambda batch: collate(batch, processor.tokenizer.pad_token_id),
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    history = []
    started = time.perf_counter()

    for epoch in range(args.epochs):
        model.train()
        train_losses = []
        for step, batch in enumerate(train_loader, 1):
            optimizer.zero_grad(set_to_none=True)
            features = batch["input_features"].to(device)
            labels = batch["labels"].to(device)
            output = model(input_features=features, labels=labels)
            output.loss.backward()
            optimizer.step()
            train_losses.append(float(output.loss.detach().cpu()))
            if step % 10 == 0 or step == len(train_loader):
                print(
                    f"epoch={epoch + 1}/{args.epochs} "
                    f"step={step}/{len(train_loader)} "
                    f"train_loss={train_losses[-1]:.5f}"
                )

        evaluation = evaluate(
            model,
            dev_loader,
            processor,
            device,
            max_decode_batches=8,
            text_field=args.text_field,
        )
        record = {
            "epoch": epoch + 1,
            "train_loss": sum(train_losses) / max(1, len(train_losses)),
            "dev_loss": evaluation["loss"],
            "dev_decoded_samples": evaluation["decoded_samples"],
            "dev_mean_decoded_cer": evaluation["mean_decoded_cer"],
            "elapsed_sec": time.perf_counter() - started,
        }
        history.append(record)
        print(json.dumps(record, ensure_ascii=False))
        checkpoint = args.output_dir / f"checkpoint_epoch_{epoch + 1}"
        model.save_pretrained(checkpoint)
        processor.save_pretrained(checkpoint)
        (args.output_dir / f"dev_predictions_epoch_{epoch + 1}.json").write_text(
            json.dumps(evaluation["predictions"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    summary = {
        "model": args.model,
        "train_samples": len(train_rows),
        "dev_samples": len(dev_rows),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "seed": args.seed,
        "history": history,
        "elapsed_sec": time.perf_counter() - started,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
