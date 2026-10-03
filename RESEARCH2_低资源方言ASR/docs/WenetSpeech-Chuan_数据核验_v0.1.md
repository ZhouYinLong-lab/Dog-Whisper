# WenetSpeech-Chuan 数据核验 v0.1

核验日期：2026-09-24

## 核验对象

- [官方主页](https://aslp-lab.github.io/WenetSpeech-Chuan/)
- [官方 GitHub 仓库](https://github.com/ASLP-lab/WenetSpeech-Chuan)
- [WSC-Eval Hugging Face 数据集](https://huggingface.co/datasets/ASLP-lab/WSC-Eval)
- [WSC-Train Hugging Face 数据集](https://huggingface.co/datasets/ASLP-lab/WSC-Train)

## 已确认内容

官方资料称 WenetSpeech-Chuan 约 10,000 小时，metadata 包含文本、speaker identity、地区、年龄、性别、质量分数和时间戳。官方 ASR benchmark WSC-Eval-ASR 分为 Easy 8.55 小时和 Hard 1.15 小时，并提供人工核验文本；这使它适合做 speaker-aware 的四川话 ASR 外部评测。

Hugging Face 文件结构中，WSC-Eval-ASR 明确包含：

- `Easy/text`、`Easy/key.txt`、`Easy/wav.scp` 与对应音频；
- `Hard/text`、`Hard/key.txt`、`Hard/wav.scp` 与对应音频；
- 其他 Long/Short 目录及 TTS 评测文件。

WSC-Train 的官方 README 说明训练 metadata 以单一 JSONL 保存，核心转写字段包括 `text` / `text_punc` 或 `rover_result`，同时有 speaker、质量和时间戳信息。HF 文件列表显示训练 metadata 约 1.43 GB，数据 viewer 当前还存在 schema cast 错误，因此本轮不下载完整文件。

## 与双输出目标的关系

本轮逐项检查了官方 README 和 WSC-Eval 非音频文件列表，没有发现同一音频对应的第二个“普通话规范文本”字段或独立 norm/translation 标注文件。这里的结论是对公开文件结构的核验，不表示数据永远不存在隐藏或申请制标注。

论文还显示，Chuan-Pipeline 已通过 LLM-GER 对多 ASR 输出做四川话表达规范化，并报告约 15% 的转写准确率提升；因此本项目不能把“LLM 规范化”本身当作创新。我们的差异应限定为双 reference、可控输出风格和 Adapter 组合/迁移评测。

因此当前决策是：

1. WenetSpeech-Chuan 用作四川话 ASR 的外部 speaker-aware benchmark 候选；
2. 不把 WSC-Chuan 单文本 `text` 当成双输出训练数据；
3. 四川话双输出主线仍需要人工补齐 `norm_text`，当前 500 条模板继续保留；
4. 若联系作者获得预处理音频或隐藏标注，再单独做配对字段审计，不改变当前结论。
