# TurnBench: A Multi-Domain Benchmark for Turn-Taking Dynamics in Spoken Dialogue

## 基本信息

- 作者：Freeman Jiang et al.
- 年份：2026
- 论文：[arXiv](https://arxiv.org/abs/2608.25218)
- 项目：[GitHub](https://github.com/SesameAILabs/turnbench)
- 基准：[官方页面](https://turnbench.sesame.com/)
- 阅读状态：待精读
- 与本课题的相关性：极高

## 初筛记录

这是一个面向 EOT 和 interruption detection 的多领域 benchmark。数据是双通道双人对话，包含 154 段对话、约 30 小时音频、106 位说话人和 6 种对话类型。每段对话由三名标注者标注，最终使用 2/3 共识。

模型必须输出事件发生的时间点，并满足严格的 causal 规则：时刻 `t` 的预测只能依赖截至 `t` 的音频。评分包含 recall、false-positive rate 和 detection latency。

## 官方 benchmark 的重要观察

- VAP 在官方榜单上同时取得较强的 EOT/INT 表现；
- RMS Energy VAD 触发很早，但 FPR 很高；
- 没有模型同时达到高 recall、低 FPR 和低 latency；
- interruption 的误报与 backchannel 较多的对话类型有关；
- 人类的 floor transfer 也可能发生在当前话轮结束前，因此“结束点”不是单一静音阈值问题。

## 精读问题

- EOT/INT 标注的具体时间容忍窗口是什么？
- recall、FPR 和 latency 的匹配算法如何定义？
- 六种对话类型的样本是否平衡？
- 训练集与 dev/test 的说话人是否严格隔离？
- 官方榜单中的模型是否全部满足同样的 causal 约束？
- RMS-VAD baseline 的阈值如何选择？
- 论文是否讨论数据许可证和模型许可证对复现的影响？

## 对我们课题的启发

TurnBench 适合作为主 benchmark。我们的贡献不应是再造一个榜单模型，而可以是：在公开 scorer 上比较固定阈值、RMS-VAD 和轻量声学模型，并按对话类型和停顿事件分析 latency/FPR 权衡。

## 必须记录的复现信息

- Hugging Face 是否能获得访问权限；
- 下载的 dataset revision；
- scorer commit/version；
- 运行设备和实时因子；
- 预测文件格式；
- 不同阈值 sweep 是否只使用 dev 集。

