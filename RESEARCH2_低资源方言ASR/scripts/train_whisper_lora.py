"""Train a parameter-efficient Whisper LoRA baseline on a manifest."""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader
from transformers import WhisperForConditionalGeneration, WhisperProcessor

from train_whisper_baseline import ManifestDataset, collate, evaluate, read_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="openai/whisper-tiny")
    parser.add_argument("--processor-model", default=None)
    parser.add_argument("--train-limit", type=int, default=-1)
    parser.add_argument("--dev-limit", type=int, default=-1)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--text-field", default="text")
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the LoRA training run")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda")

    processor_source = args.processor_model or args.model
    processor = WhisperProcessor.from_pretrained(
        processor_source,
        local_files_only=Path(processor_source).exists(),
    )
    processor.tokenizer.set_prefix_tokens(language="zh", task="transcribe")
    base_model = WhisperForConditionalGeneration.from_pretrained(
        args.model,
        local_files_only=Path(args.model).exists(),
    ).to(device)
    base_model.config.use_cache = False
    base_model.generation_config.language = "zh"
    base_model.generation_config.task = "transcribe"
    model = get_peft_model(
        base_model,
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
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
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
