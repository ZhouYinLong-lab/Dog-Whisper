"""Compose two compatible LoRA adapters by concatenating their low-rank updates.

For each target linear layer, the new adapter represents

    delta = delta_rec + delta_norm

exactly (up to floating-point precision) by concatenating the two rank-r
factors into a rank-2r factor.  This is different from averaging A/B matrices,
which is not equivalent to adding the two LoRA updates.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import torch
from peft import PeftConfig, PeftModel
from transformers import WhisperForConditionalGeneration, WhisperProcessor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--rec-adapter", type=Path, required=True)
    parser.add_argument("--norm-adapter", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    base_model = WhisperForConditionalGeneration.from_pretrained(
        args.base_model, local_files_only=True
    )
    model = PeftModel.from_pretrained(
        base_model, args.rec_adapter, local_files_only=True
    )
    model.load_adapter(
        args.norm_adapter,
        adapter_name="norm",
        is_trainable=False,
        local_files_only=True,
    )

    rec_config = PeftConfig.from_pretrained(args.rec_adapter)
    norm_config = PeftConfig.from_pretrained(args.norm_adapter)
    if rec_config.r != norm_config.r:
        raise ValueError("Adapters must have the same LoRA rank")
    if rec_config.lora_alpha != norm_config.lora_alpha:
        raise ValueError("Adapters must have the same LoRA alpha")
    composed_config = copy.deepcopy(rec_config)
    composed_config.r = rec_config.r + norm_config.r
    composed_config.lora_alpha = rec_config.r + norm_config.r
    composed_config.base_model_name_or_path = str(args.base_model)
    model.add_adapter("composed", composed_config)

    scale_rec = rec_config.lora_alpha / rec_config.r
    scale_norm = norm_config.lora_alpha / norm_config.r
    layer_count = 0
    with torch.no_grad():
        for module in model.modules():
            if not hasattr(module, "lora_A") or "composed" not in module.lora_A:
                continue
            if not {"default", "norm"}.issubset(module.lora_A.keys()):
                continue
            rec_a = module.lora_A["default"].weight
            rec_b = module.lora_B["default"].weight
            norm_a = module.lora_A["norm"].weight
            norm_b = module.lora_B["norm"].weight
            module.lora_A["composed"].weight.copy_(torch.cat([rec_a, norm_a], dim=0))
            module.lora_B["composed"].weight.copy_(
                torch.cat([scale_rec * rec_b, scale_norm * norm_b], dim=1)
            )
            layer_count += 1

    if layer_count == 0:
        raise RuntimeError("No compatible LoRA layers were found")
    model.set_adapter("composed", inference_mode=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output_dir, selected_adapters=["composed"])
    processor = WhisperProcessor.from_pretrained(args.rec_adapter, local_files_only=True)
    processor.save_pretrained(args.output_dir)
    summary = {
        "base_model": str(args.base_model),
        "rec_adapter": str(args.rec_adapter),
        "norm_adapter": str(args.norm_adapter),
        "composition": "exact_delta_sum_by_rank_concatenation",
        "rec_weight": 1.0,
        "norm_weight": 1.0,
        "rec_rank": rec_config.r,
        "norm_rank": norm_config.r,
        "composed_rank": composed_config.r,
        "layers": layer_count,
    }
    (args.output_dir / "composition_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
