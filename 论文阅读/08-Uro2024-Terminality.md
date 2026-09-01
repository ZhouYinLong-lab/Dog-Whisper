# Detecting the Terminality of Speech-Turn Boundary for Spoken Interactions in French TV and Radio Content

## 基本信息

- 作者：Rémi Uro, Marie Tahon, David Doukhan, Antoine Laurent, Albert Rilliard
- 会议：Interspeech 2024
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2024/uro24_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2024/uro24_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：高

## 初筛记录

论文将说话边界分类为 Terminal 或 Non-Terminal，并研究音频、文本以及二者融合对 terminality 判断的影响。数据来自法语 TV 和 Radio 多说话人内容，边界处带有 turn-terminality 标注。

作者使用预训练自监督表征，比较不同融合方式和上下文长度，同时分析多次随机初始化导致的性能变化。

## 精读问题

- terminality 标签是否等同于用户端 endpoint？
- TV/Radio 场景和人机对话的分布差异有多大？
- 文本特征是参考文本还是增量文本？
- 多次运行的方差有多大，作者如何报告？
- 为什么选择 accuracy，是否有 latency/cut-in 评价？

## 对我们课题的启发

这篇较新的工作可以用来避免过时的创新表述。我们的差异应放在在线决策代价和公开数据上的统一评价，而不是简单重复 audio/text fusion。

