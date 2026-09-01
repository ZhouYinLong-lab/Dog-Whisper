# Personalized Predictive ASR for Latency Reduction in Voice Assistants

## 基本信息

- 作者：Andreas Schwarz, Di He, Maarten Van Segbroeck, Mohammed Hethnawi, Ariya Rastrow
- 会议：Interspeech 2023
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2023/schwarz23_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2023/schwarz23_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：中

## 初筛记录

论文不是直接改进 endpoint detector，而是利用 partial ASR hypothesis 预测完整 utterance，并提前预取响应，从而隐藏响应生成延迟。实验使用内部 voice assistant 数据和公开 SLURP 数据。

## 精读问题

- 预取错误的代价如何定义？
- 它如何处理用户继续说话导致的 partial hypothesis 改变？
- endpoint detection 在系统中具体位于哪个位置？
- latency 的起点和终点是什么？
- 公开 SLURP 部分是否足以复现核心结论？

## 对我们课题的启发

它提醒我们区分“更早判断用户说完”和“提前准备响应”两种降低延迟的方法。当前课题先聚焦 endpoint decision，不把 response prefetch 作为主实验。

