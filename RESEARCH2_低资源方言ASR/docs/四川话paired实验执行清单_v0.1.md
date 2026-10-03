# 四川话 paired 实验执行清单 v0.1

前置条件：

- `norm_text` 已由人工审核确认；
- `validate_research2_state.py --require-paired` 通过；
- `manifests/sichuan_paired_500.jsonl` summary 显示 train/dev 均非空且 speaker-disjoint；
- 不覆盖原始模板和已有 checkpoint。

以下命令从项目根目录执行。示例 dev 说话人 `G0008,G0019` 只是当前模板的候选，正式运行前按已完成标注的说话人覆盖量确认。

## 1. 独立方言 LoRA

```powershell
python "RESEARCH 2/scripts/train_whisper_lora.py" `
  --manifest "RESEARCH 2/manifests/sichuan_paired_500.jsonl" `
  --workspace "RESEARCH 2" `
  --output-dir "RESEARCH 2/results/sichuan_paired_lrec" `
  --model "openai/whisper-tiny" `
  --processor-model "openai/whisper-tiny" `
  --text-field dialect_text `
  --epochs 1 --batch-size 4 --learning-rate 1e-4
```

## 2. 独立规范 LoRA

使用相同命令，将 `--text-field dialect_text` 改为 `--text-field norm_text`，输出目录改为 `sichuan_paired_lnorm`。

## 3. 共享 task-control LoRA

```powershell
python "RESEARCH 2/scripts/train_whisper_task_control_lora.py" `
  --manifest "RESEARCH 2/manifests/sichuan_paired_500.jsonl" `
  --workspace "RESEARCH 2" `
  --output-dir "RESEARCH 2/results/sichuan_paired_task_control" `
  --model "openai/whisper-tiny" `
  --processor-model "openai/whisper-tiny" `
  --epochs 1 --batch-size 4 --learning-rate 1e-4
```

## 4. 统一评测

独立 LoRA 使用 `evaluate_whisper_checkpoint.py`，分别传 `--text-field dialect_text` 和 `--text-field norm_text`；task-control 使用 `evaluate_whisper_task_control.py`，同一 checkpoint 输出两路结果。所有方法固定同一 test、`max_new_tokens=64`、重复抑制参数，并保存逐条 JSONL。

## 5. 比较与报告

- 报告方言 CER、规范 CER、方言特征词召回、输出分离率；
- 对同一 utt_id 做 paired bootstrap，不只比较平均 CER；
- 组合 Adapter 作为负结果/干扰对照，不预设它优于 task-control；
- 若 500 条样本不足以稳定 dev，先报告 pilot，不升级为正式结论。
- 由于 FormalASR 等工作已覆盖单一 spoken-to-formal，结果分析必须同时报告方言保真和规范化两路 reference；单独的规范 CER 改善不能作为主要贡献。
