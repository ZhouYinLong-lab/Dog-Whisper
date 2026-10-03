# 双输出方言 ASR 文献调研 v0.1

更新时间：2026-09-26

## 初步结论

队友提出的方向可以落地，但论文问题不应表述成“训练两个 LoRA”本身。已有工作已经覆盖 LoRA-Whisper、AdapterFusion 和语音 Adapter 组合。更有研究价值的表述是：

> 方言保真识别知识与普通话规范化知识能否解耦，并通过可组合 Adapter 控制同一段方言语音的输出风格；这种组合能否迁移到未见过的方言。

我们现有四川话数据可以直接支持方言保真模块 `L_rec`，但还缺少同一语音对应的普通话规范文本，暂时不能直接训练 `L_norm`。

## 已核实的核心文献

| 优先级 | 文献 | 解决的问题 | 对 RESEARCH2 的直接启示 | 可复现性 |
|---|---|---|---|---|
| P0 | [WenetSpeech-Wu: Datasets, Benchmarks, and Models for a Unified Chinese Wu Dialect Speech Processing Ecosystem](https://aclanthology.org/2026.findings-acl.1395/)（ACL Findings 2026） | 全量语料约 8,000 小时，包含多维标注；官方 benchmark 约 9.75 小时吴语 ASR、4.4 小时吴语到普通话 AST，并覆盖说话人属性、情感、TTS 等任务 | 是最接近队友所说吴语路线的数据与评测平台；应区分“全量语料”和“公开 benchmark”，可借鉴方言 ASR/AST 任务定义 | [官方仓库](https://github.com/ASLP-lab/WenetSpeech-Wu-Repo) 和 [Hugging Face benchmark](https://huggingface.co/datasets/ASLP-lab/WenetSpeech-Wu-Bench) 已核实；完整数据仍需按仓库说明申请/下载 |
| P0 | [A Multi-Dialectal Dataset for German Dialect ASR and Dialect-to-Standard Speech Translation](https://www.isca-archive.org/interspeech_2025/blaschke25_interspeech.html)（Betthupferl，Interspeech 2025） | 4 小时、3 个德国方言组，同时提供方言转写和标准德语转写；分析 ASR 输出更接近方言还是标准语 | 这是“双版本文本”的直接先例。它证明了规范化输出应作为独立评测目标，而不是把方言 CER 和普通话 CER 混成一个指标 | 论文、数据形式和评测思路已核实；规模较小，适合作为方法先例，不适合作为主数据规模参考 |
| P0 | [LoRA-Whisper: Parameter-Efficient and Extensible Multilingual ASR](https://www.isca-archive.org/interspeech_2024/song24_interspeech.html)（Interspeech 2024） | 将 LoRA 加入 Whisper，缓解多语言干扰，并支持扩展新语言而不明显损害原有语言 | 支持我们使用 Whisper + LoRA 作为 `L_rec` 基线；也提醒我们报告语言/方言间干扰，而不只报告单一 CER | 论文和 ISCA 页面已核实；需进一步核对代码是否公开 |
| P0 | [AdapterFusion: Non-Destructive Task Composition for Transfer Learning](https://aclanthology.org/2021.eacl-main.39/)（EACL 2021） | 先分别抽取任务知识，再进行独立的知识组合，降低连续微调的灾难性遗忘 | “先训练 `L_rec`、`L_norm`，再组合”有成熟的概念来源；我们的创新不能只声称“两个 Adapter 叠加” | 论文和官方页面已核实，代码/AdapterHub 资源可作为实现参考 |
| P0 | [Parameter-efficient Dysarthric Speech Recognition Using Adapter Fusion and Householder Transformation](https://www.isca-archive.org/interspeech_2023/qi23b_interspeech.html)（Interspeech 2023） | 将 Adapter Fusion 用于语音识别和说话人适配，研究少量参数下的多 Adapter 知识转移 | 是目前找到的最接近“语音识别中的 Adapter Fusion”的先例；需要比较我们是简单堆叠、融合层，还是任务条件控制 | 论文和 ISCA 页面已核实；实现细节需读 PDF |
| P0 | [WenetSpeech-Chuan: A Large-Scale Sichuanese Corpus with Rich Annotation for Dialectal Speech Processing](https://arxiv.org/abs/2509.18004)（官方仓库/数据，2025 预印本；另有 ICASSP DOI） | 官方资料称约 10,000 小时川渝方言语音；metadata 含文本、speaker identity、地区、年龄、性别、质量分数和时间戳；WSC-Eval-ASR 有 Easy 8.55h + Hard 1.15h，并提供人工核验文本 | 这是比当前本地 13,068 条数据更强的四川话外部资源，可用于 speaker-aware 外部 ASR 基准；但官方 README/ASR `text` 仍是一套转写，没有发现同音频普通话规范文本，因此不能直接替代双文本标注 | [官方主页](https://aslp-lab.github.io/WenetSpeech-Chuan/)、[官方仓库](https://github.com/ASLP-lab/WenetSpeech-Chuan)、[WSC-Eval](https://huggingface.co/datasets/ASLP-lab/WSC-Eval) 已核实；预处理音频需按仓库说明联系获取，HF 训练元数据约 1.43GB，不下载 |
| P1 | [Leveraging Geographic Metadata for Dialect-Aware Speech Recognition](https://www.isca-archive.org/interspeech_2025/mehralian25_interspeech.html)（Interspeech 2025） | 将经纬度作为连续输入，让模型在已见和未见地区间插值 | 提供“地理条件控制”这一替代路线；可作为多 Adapter 方案的对照，而不是当前第一优先级 | 论文和 ISCA 页面已核实 |
| P1 | [Dialect-aware Semi-supervised Learning for End-to-End Multi-dialect Speech Recognition](https://doi.org/10.23919/apsipaasc55919.2022.9980139)（APSIPA 2022） | 多方言端到端识别中的方言感知与半监督学习 | 可作为低资源方言和跨方言泛化的背景方法，帮助设计无标注/伪标注扩展实验 | DOI 和题名已核实，需继续读取正文 |

## 2026 年新增方向核验

| 文献 | 已解决的问题 | 对 RESEARCH2 的影响 |
|---|---|---|
| [FormalASR: End-to-End Spoken Chinese to Formal Text](https://arxiv.org/abs/2605.19266) | 直接把口语中文语音识别为正式书面文本；构建 WenetSpeech-Formal 与 Speechio-Formal，并报告相对 verbatim baseline 的显著 CER、ROUGE-L、BERTScore 改善 | “端到端语音规范化”本身已是明确研究线，不能再把单一 `L_norm` 或普通话规范输出单独包装成主要创新；我们的实验必须保留方言保真 reference，并比较双输出控制 |
| [On-Policy Self-Distillation for Multi-Dialect ASR: Mastering Dialects, Retaining Mandarin](https://github.com/ASLP-lab/CN-MultiDialect-ASR) | 通过 CPT→方言 SFT→OPSD，在多方言识别增强的同时尽量不损害普通话；官方仓库报告四川话公开集上的方言 CER 改善 | “方言适配但保持普通话”也已有强先例；我们不能只声称 LoRA/Adapter 同时改善方言和普通话，需把问题限定为同一音频双 reference 的输出风格控制 |
| [Summary of the ChinaVoices Challenge 2026](https://arxiv.org/abs/2609.03471) | 统一 16 类方言、多数据轨道和公开/隐藏评测，分析归一化、增强、辅助 CTC 等方法 | 支持把地区、说话人、数据轨道和外部测试作为报告维度；不能用本地小规模数据直接宣称多方言泛化 |

### 更新后的创新性边界

截至 2026-09-26，以下命题都已有直接或高度相近先例：

- 单一模型将口语语音转为普通话正式文本；
- 方言适配同时尽量保持普通话性能；
- 用 LoRA/Adapter 做低资源方言适配；
- 用多系统或 LLM 做四川话转写纠错/规范化。

因此 RESEARCH2 必须把贡献收缩为一个可证伪的问题：

> 在同一段四川话语音和同一说话人隔离评测下，显式任务控制或 Adapter 路由能否在“方言保真文本”和“普通话规范文本”两个 reference 之间可靠切换；共享 task-control 是否比独立 Adapter、简单组合和级联规范化更有效或更省参数？

这个问题要求同音频双文本标注，正是当前四川话 500 条人工审核 gate 的必要性；模型候选不能替代该标注。

## 重要的创新性边界：WenetSpeech-Chuan 已覆盖单输出规范化

精读 [WenetSpeech-Chuan 论文](https://arxiv.org/abs/2509.18004) 后发现，其 Chuan-Pipeline 已包含 LLM-GER：用 FireRed-ASR、SenseVoice-Small 和 TeleASR 生成多个候选，再由 Qwen3 做 ROVER 式合并；论文明确描述该步骤会在保持语义和 token 长度的同时“normalize Sichuanese dialectal expressions”，并报告相对单个 ASR 系统约 15% 的转写准确率提升。

因此，以下表述不能作为 RESEARCH2 的独立创新：

- 用 LLM 对四川话 ASR 结果做普通话化/规范化；
- 用多 ASR 输出加 LLM 纠错提高四川话转写质量；
- 仅仅训练一个方言 LoRA 和一个规范化 LoRA。

当前仍有研究空间、且与已跑 pilot 对齐的表述是：

> 在同一段方言语音上保留“方言保真文本”和“普通话规范文本”两个可评测 reference，通过任务条件或 Adapter 组合控制输出风格；比较共享 task-control、独立 Adapter、级联规范化和融合路由，并检验方法能否迁移到未见说话人/方言。

WenetSpeech-Chuan 论文公开描述的是单一 corrected transcription 和单一 ASR benchmark reference，并未展示同音频双文本输出或 task-controlled Adapter 评测；这一点仍需通过未来正式数据审计持续确认。

## 截图中尚未核实的条目

以下名称暂时不作为论文依据写入研究结论，直到找到正式论文、DOI、官方仓库或数据主页：

| 名称 | 当前状态 | 处理方式 |
|---|---|---|
| MAS-LoRA | 未找到可确认的 ASR 论文记录 | 先不使用该名称；可能是队友的简称或内部方案名 |
| ChinaVoices Challenge 2026 | 未找到可确认的官方论文/赛事主页 | 需要队友提供链接或原始引用 |
| DASR-CPO, Interspeech 2026 | 未找到可确认的论文记录 | 先不写入 related work |
| ASR for Non-standardised Languages | 名称过于泛，未定位到唯一论文 | 需要作者、年份或链接 |

## 对我们当前工作的映射

| 组件 | 当前状态 | 下一步 |
|---|---|---|
| `L_rec`：方言保真识别 | 已有四川话数据、说话人独立划分和 Whisper-tiny LoRA 基线；最佳完整测试 CER 为 0.4925 | 补跑全测试集 zero-shot，作为严格对照；之后尝试 Whisper-base LoRA |
| `L_norm`：普通话规范化 | 当前数据没有配对规范文本 | 从四川话测试不泄漏的训练说话人中抽取 100–200 条，人工制作规范文本试标 |
| Adapter 组合 | 尚未实现 | 先比较独立 Adapter、任务 token、串联规范化和融合层；不能默认简单叠加有效 |
| 评测 | 目前只有方言保真 CER | 至少增加方言 CER、规范文本 CER，以及方言词保留/普通话规范化的人工检查 |
| 跨方言迁移 | 尚未开始 | 只有在四川话双版本小试验成立后，再考虑吴语或跨方言 Adapter 迁移 |

## 建议的最小实验

先不扩展到 8,000 小时数据，也不立即训练两个大模型。使用 500 条左右四川话样本，按说话人划分，建立：

1. Whisper zero-shot；
2. `L_rec`：方言保真 LoRA；
3. 单模型直接输出普通话规范文本；
4. `L_rec` 后接规范化模块；
5. 独立 `L_rec` + `L_norm`；
6. Adapter 组合/融合。

其中前 4 项先做，能够判断问题本身是否成立；如果级联或双 Adapter 没有超过单模型规范化，就不应把“可组合 LoRA”作为论文主贡献。

## 研究判断

当前最稳妥的论文切入点不是“我们提出了两个 LoRA”，而是：

> 在四川话低资源场景下，研究方言保真转写与普通话规范输出的可控解耦，并比较单模型、多任务、级联和 Adapter 组合四类方案。

这条路线既能利用已有四川话基线，也能吸收 WenetSpeech-Wu 和 Betthupferl 的数据/评测思想，同时避免把尚未核实的截图条目当作 SOTA 依据。
