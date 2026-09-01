# An Incremental Turn-Taking Model for Task-Oriented Dialog Systems

## 基本信息

- 作者：Andrei C. Coman, Koichiro Yoshino, Yukitoshi Murase, Satoshi Nakamura, Giuseppe Riccardi
- 会议：Interspeech 2019
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2019/coman19_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2019/coman19_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：高

## 初筛记录

论文从增量转写中逐 token 更新对话状态，提出 incremental Dialog State Tracker（iDST）和 incremental Turn Taking Decider（iTTD）。作者重新标注 DSTC2，为每个 token 分配二元标签，用于表示是否已经到达适合系统接话的位置。

摘要报告 iTTD 优于确定性的手工轮次决策算法。

## 精读问题

- token-level 标签如何定义，是否只依赖对话系统的语义状态？
- DSTC2 的原始数据是否包含足够时间信息？
- 增量文本来自真实 streaming ASR 还是由参考文本模拟？
- “better performance”具体指什么指标？
- 是否评估错误提前接话和延迟接话的代价？

## 对我们课题的启发

这篇论文可帮助我们区分“文本已经足够理解”与“用户已经结束”两个概念。若使用增量文本，必须明确文本是当前 partial hypothesis，而不是完整参考句子。

