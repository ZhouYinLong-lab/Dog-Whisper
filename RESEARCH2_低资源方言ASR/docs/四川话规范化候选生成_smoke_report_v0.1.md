# 四川话规范化候选生成 smoke report v0.1

日期：2026-09-24

## 目的

为 500 条四川话人工规范化模板提供“仅供审核的草稿”，降低人工起标成本。模型候选不写入正式 `norm_text`，不改变 `norm_status`，也不直接用于训练。

## 模型与协议

- 本地 Ollama：`minicpm5-2b-local:latest`，约 2.5B、Q4_K_M；
- 生成脚本：`scripts/generate_norm_candidates_ollama.py`；
- 输出字段：`norm_text_candidate`、`candidate_status`、`candidate_model`、`candidate_prompt_version`、`human_norm_text`、`human_review_status`；
- 当前提示版本：`sichuan-norm-candidate-v2-zh-only`；显式要求只输出简体中文 JSON，并提供四川话→普通话示例。

## 结果

| 轮次 | 样本 | 成功解析 | 发生改写 | 保持原文 | 失败 |
|---|---:|---:|---:|---:|---:|
| v1，未限定中文 | 20 | 20 | 不统计 | 不统计 | 0 |
| v2，限定中文+示例 | 20 | 20 | 结果抽查可用 | 结果抽查可用 | 0 |
| v2，扩大 smoke | 100 | 99 | 62 | 37 | 1 |

对完整 500 条模板采用分段调用后：495 条成功解析、319 条发生改写、176 条保持原文、5 条 JSON 截断失败；成功结果中未检测到英文片段。这里的“发生改写”只表示字符串发生变化，不表示改写一定正确。

v1 的主要失败模式是输出英文，因此已废弃。v2 的 100 条结果中，1 条因 JSON 截断失败；该条仍保留在候选文件中，但 `candidate_status` 不是 `model_suggested`，不会被误用。

## 文件

- 20 条复测：`sichuan_norm_annotation_template/norm_candidates_ollama_smoke20_v2.jsonl`；
- 100 条候选：`sichuan_norm_annotation_template/norm_candidates_ollama_100.jsonl`；
- 100 条摘要：`sichuan_norm_annotation_template/norm_candidates_ollama_100.jsonl.summary.json`。
- 其余 400 条候选：`sichuan_norm_annotation_template/norm_candidates_ollama_remaining400.jsonl`；
- 其余 400 条摘要：`sichuan_norm_annotation_template/norm_candidates_ollama_remaining400.jsonl.summary.json`。
- 审核队列：`sichuan_norm_annotation_template/norm_review_queue_500.jsonl`；
- 审核队列摘要：`sichuan_norm_annotation_template/norm_review_queue_500.jsonl.summary.json`。

## 审核队列分级

审核审计按“候选不可用/模型错误、英文、阿拉伯数字变化、长度异常、较大改写”标记高风险。修正数字规则后，500 条中：高优先级 12 条、中优先级 312 条、低优先级 176 条；高优先级包括 5 条模型错误、1 条数字格式变化、6 条较大改写。数字检查只对阿拉伯数字生效，避免把“俩/两”“一篇”等正常汉字规范化误报为数字错误。

## 结论与下一步

本地模型可以作为人工标注的候选生成器，但不能替代人工审核。下一步只允许人工把候选复制/修改到 `human_norm_text`，并将 `human_review_status` 改为 `accepted` 或 `edited`；完成后再由硬校验脚本生成训练 manifest。当前正式标注模板仍为 500 条空白 `norm_text`，训练 gate 仍应保持 `ready_for_training: false`。
