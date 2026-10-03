# WenetSpeech-Chuan 外部 ASR smoke v0.1

日期：2026-09-24

## 目的

验证官方 WSC-Eval-ASR Easy 的文本、音频命名和本地 Whisper 评测脚本能否接通。该 smoke 不是正式 benchmark，也不包含普通话规范化目标。

## 数据

- 来源：[ASLP-lab/WSC-Eval](https://huggingface.co/datasets/ASLP-lab/WSC-Eval)
- 子集：`WSC-Eval-ASR/Easy`
- 下载样本：8 条
- 音频总大小：1,047,392 bytes
- 本地 manifest：`_external/wsc_chuan_eval_smoke/manifest.jsonl`
- 目标字段：官方单一 `text`

## 结果

模型：缓存的 `openai/whisper-tiny`，zero-shot，沿用项目解码设置（`max_new_tokens=64`、`no_repeat_ngram_size=3`、`repetition_penalty=1.05`）。

- 样本数：8
- 平均 utterance CER：**0.7232**
- 结果文件：`results/wsc_chuan_tiny_zero_shot_smoke/eval.json`

作为迁移 smoke，同一 8 条样本再使用本地四川话 `whisper_tiny_lora_epoch3`：

- 平均 utterance CER：**0.5696**；
- 相对 zero-shot 的逐样本 CER 改善：0.1535；胜出/持平/变差 = 6 / 1 / 1；bootstrap 95% CI `[0.0615, 0.2383]`；
- 结果文件：`results/wsc_chuan_tiny_sichuan_lora_smoke/eval.json`；统计：`paired_vs_zero_shot.json`。

这提示本地四川话 LoRA 可能具有跨来源迁移能力，但样本只有 8 条，不能据此宣称外部泛化成立。

## 边界

1. 8 条样本不足以报告 WSC-Eval 性能，也不能和官方 leaderboard 比较；
2. 当前样本没有 speaker 字段，不能验证 speaker-disjoint 性能；
3. WSC-Eval 公开文件结构中没有同音频普通话规范文本，因此本 smoke 只验证单目标四川话 ASR 接入；
4. 四川话双输出主线仍以人工补齐 `sichuan_norm_annotation_template` 为准。
