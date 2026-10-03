"""Train one LoRA with an explicit dialect/normalised-output control token."""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader, Dataset
from transformers import WhisperForConditionalGeneration, WhisperProcessor

from train_whisper_baseline import ManifestDataset, collate, read_rows


CONTROL_PHRASES = {"dialect": "方言输出", "norm": "普通话输出"}
TARGET_FIELDS = {"dialect": "dialect_text", "norm": "norm_text"}


class ControlledDataset(Dataset):
    def __init__(self, rows, workspace, processor, control_ids):
        self.rows = [(row, control) for row in rows for control in CONTROL_PHRASES]
        self.workspace = workspace
        self.processor = processor
        self.control_ids = control_ids

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row, control = self.rows[index]
        base = ManifestDataset([row], self.workspace, self.processor, TARGET_FIELDS[control])[0]
        labels = base["labels"]
        prefix_len = len(self.processor.tokenizer.prefix_tokens)
        labels = labels[:prefix_len] + self.control_ids[control] + labels[prefix_len:]
        return {"features": base["features"], "labels": labels, "row": row, "control": control}


def collate_control(batch, pad_token_id):
    out = collate(batch, pad_token_id)
    out["controls"] = [item["control"] for item in batch]
    return out


def add_control_tokens(processor):
    ids = {
        name: processor.tokenizer(phrase, add_special_tokens=False).input_ids
        for name, phrase in CONTROL_PHRASES.items()
    }
    return ids


@torch.no_grad()
def evaluate_control_loss(model, loader, device):
    model.eval()
    losses = []
    for batch in loader:
        output = model(
            input_features=batch["input_features"].to(device),
            labels=batch["labels"].to(device),
        )
        losses.append(float(output.loss.detach().cpu()))
    model.train()
    return sum(losses) / max(1, len(losses))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--processor-model", type=Path, required=True)
    parser.add_argument("--train-limit", type=int, default=-1)
    parser.add_argument("--dev-limit", type=int, default=-1)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the LoRA training run")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda")

    processor = WhisperProcessor.from_pretrained(args.processor_model, local_files_only=True)
    processor.tokenizer.set_prefix_tokens(language="zh", task="transcribe")
    control_ids = add_control_tokens(processor)
    model = WhisperForConditionalGeneration.from_pretrained(
        args.model, local_files_only=Path(args.model).exists()
    )
    model = model.to(device)
    model.config.use_cache = False
    model.generation_config.language = "zh"
    model.generation_config.task = "transcribe"
    model = get_peft_model(
        model,
        LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=["q_proj", "v_proj"],
            bias="none",
        ),
    )
    model.print_trainable_parameters()

    train_rows = read_rows(args.manifest, "train", args.train_limit)
    dev_rows = read_rows(args.manifest, "dev", args.dev_limit)
    train_loader = DataLoader(
        ControlledDataset(train_rows, args.workspace, processor, control_ids),
        batch_size=args.batch_size, shuffle=True, num_workers=0,
        collate_fn=lambda batch: collate_control(batch, processor.tokenizer.pad_token_id),
    )
    dev_loader = DataLoader(
        ControlledDataset(dev_rows, args.workspace, processor, control_ids),
        batch_size=args.batch_size, shuffle=False, num_workers=0,
        collate_fn=lambda batch: collate_control(batch, processor.tokenizer.pad_token_id),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    history = []

    for epoch in range(args.epochs):
        model.train()
        losses = []
        for step, batch in enumerate(train_loader, 1):
            optimizer.zero_grad(set_to_none=True)
            output = model(input_features=batch["input_features"].to(device), labels=batch["labels"].to(device))
            output.loss.backward()
            optimizer.step()
            losses.append(float(output.loss.detach().cpu()))
            if step % 20 == 0 or step == len(train_loader):
                print(f"epoch={epoch + 1}/{args.epochs} step={step}/{len(train_loader)} train_loss={losses[-1]:.5f}")
        dev_loss = evaluate_control_loss(model, dev_loader, device)
        record = {
            "epoch": epoch + 1,
            "train_loss": sum(losses) / max(1, len(losses)),
            "dev_loss": dev_loss,
            "elapsed_sec": time.perf_counter() - started,
        }
        history.append(record)
        print(json.dumps(record, ensure_ascii=False))
        checkpoint = args.output_dir / f"checkpoint_epoch_{epoch + 1}"
        model.save_pretrained(checkpoint)
        processor.save_pretrained(checkpoint)

    (args.output_dir / "summary.json").write_text(json.dumps({
        "model": args.model, "train_source_rows": len(train_rows), "dev_source_rows": len(dev_rows),
        "effective_train_rows": len(train_rows) * 2, "effective_dev_rows": len(dev_rows) * 2,
        "control_phrases": CONTROL_PHRASES, "control_ids": control_ids, "added_tokens": 0,
        "epochs": args.epochs, "batch_size": args.batch_size, "learning_rate": args.learning_rate,
        "seed": args.seed, "history": history, "elapsed_sec": time.perf_counter() - started,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
