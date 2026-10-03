# WenetSpeech-Wu 双文本 pilot v0.3

日期：2026-09-24

## 本轮新增问题

在两个独立 LoRA 之外，测试一个共享 LoRA、由输出控制前缀选择目标的方案：

- 方言目标：在 Whisper 标准前缀后加入已有词表中的“方言输出”；
- 规范目标：在 Whisper 标准前缀后加入已有词表中的“普通话输出”；
- 同一音频在训练集中复制两份，分别对应两种目标；
- 推理时通过 `forced_decoder_ids` 强制标准前缀与目标控制短语。

控制短语使用已有词表，不扩展 tokenizer，因此没有随机新 embedding。推理协议额外遵循 Whisper 约定：`decoder_start_token_id` 由模型内部提供，强制 token 从 position 1 开始。

## 数据与训练

使用扩展候选集 1,449 条（train 1,003 / dev 226），所有最终指标仍在严格候选集的 68 条 test 上计算。模型为 Whisper-tiny，LoRA `r=8`、`alpha=16`、dropout 0.05，学习率 `1e-4`，batch size 4，1 epoch。

checkpoint：`results/wu_tiny_task_control_text90_epoch1/checkpoint_epoch_1/`

训练有效样本数为 2,006，train loss 2.8631，dev loss 2.3763。当前 parquet 没有 speaker 字段，因此仍然只是父 utterance 隔离，不是 speaker-disjoint 评测。

2026-09-24 对本地 parquet schema 做了复核：`asr.parquet` 与 `ast.parquet` 的字段均只有 `task / utt_id / audio / label`，Parquet pandas metadata 也没有隐藏 speaker 列。因此当前本地资源不能升级为 speaker-disjoint benchmark，只能保持 pilot 定位。

## 严格 test 结果

| 方法 | 方言 reference CER | 普通话 reference CER |
|---|---:|---:|
| tiny zero-shot | 0.9080 | 0.9109 |
| 独立 `L_rec` / `L_norm` | 0.8245 | 0.8493 |
| 共享 LoRA + task-control | **0.8186** | **0.8445** |
| `L_rec + L_norm` 等权直接相加 | 1.0799 | 1.0827 |

共享 task-control 相对 zero-shot 的逐样本 paired bootstrap（10,000 次）结果：

- 方言：绝对改善 0.0894；胜出/持平/变差 = 55 / 4 / 9；95% CI `[0.0563, 0.1207]`；
- 普通话：绝对改善 0.0664；胜出/持平/变差 = 52 / 4 / 12；95% CI `[0.0384, 0.0931]`。

与对应独立 LoRA 的 paired bootstrap：

- 方言：task-control 额外改善 0.0059；胜出/持平/变差 = 32 / 10 / 26；95% CI `[-0.0206, 0.0319]`；
- 普通话：task-control 额外改善 0.0049；胜出/持平/变差 = 34 / 7 / 27；95% CI `[-0.0156, 0.0251]`。

因此，task-control 已经证明“一个 adapter 可以按任务条件输出两种目标”在这个 pilot 上可运行，并且点估计略优于独立 adapter；但相对独立 adapter 的置信区间跨 0，暂不能宣称统计显著优于独立方案。

## 输出是否真的受到控制

对同一 68 条 test 的两路 hypothesis 做了额外分离度分析，结果保存在 `results/wu_tiny_task_control_text90_epoch1/eval_strict_v2/output_divergence.json`：

- 两路输出完全相同：5 / 68，完全相同率 `7.35%`；
- 发生差异：63 / 68；
- 平均 hypothesis edit distance：15.21 个字符；
- 平均相对字符 divergence：`0.3375`。

这说明控制短语确实改变了输出序列，而不是被模型完全忽略。但 divergence 本身不等于“方言/普通话风格正确”，因为当前 test 上两路仍有不少识别错误；后续必须用人工标注的四川话 paired test 检查风格方向是否正确。

## 工程失败记录

第一版使用新增 special token `<|dialect_output|>` / `<|norm_output|>`，但这些 token 的 embedding 是随机初始化且不在 q/v LoRA 的可训练参数中；结果在严格 test 上 CER 为 2.1887 / 2.2300，并出现大量英文幻觉。该运行已标记为无效工程试验，不纳入方法比较。随后发现 evaluator 在 position 0 重复强制 SOT，也会使生成退化为单 token；修复为从 position 1 强制后，才得到上面的有效结果。

## 方向判断

当前证据支持：

1. 双文本目标可在同一 adapter 中通过显式任务条件进行控制；
2. 任务条件比简单 LoRA delta 相加可靠；
3. task-control 与独立 adapter 的性能在当前 pilot 上相当，且部署上只需保存一个 adapter。

当前证据不支持：

1. 在无 speaker-disjoint split 的 benchmark 子集上宣称最终泛化或 SOTA；
2. 声称 task-control 已显著优于独立 adapter；
3. 直接把 Wu pilot 的规范文本结果外推为四川话结果。

## 下一步

1. 优先获得或构造 speaker-disjoint 的双文本评测；
2. 对四川话人工补标 300–500 条同音频规范文本，保留方言原文与规范文本配对；
3. 在四川话上复用同一 task-control 训练/评测脚本；
4. 若新数据验证有效，再迁移到 Whisper-base，并比较 task-control、adapter routing、级联规范化。
