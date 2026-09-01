# 论文阅读路线

## 当前课题

流式语音对话中的端点检测与轮次预测：在用户持续输入时判断当前话轮是否结束，并研究响应延迟与误截断之间的权衡。

## 建议阅读顺序

### 第一组：先建立问题定义

1. [Maier et al. 2017 - Towards Deep End-of-Turn Prediction](01-Maier2017-End-of-Turn.md)
2. [Chang et al. 2022 - Turn-Taking Prediction for Natural Conversational Speech](02-Chang2022-Turn-Taking.md)
3. [Ekstedt & Skantze 2022 - Voice Activity Projection](03-Ekstedt2022-VAP.md)

### 第二组：理解不同的标签与建模方式

4. Hara et al. 2019 - TRP-based turn-taking prediction
5. Coman et al. 2019 - Incremental turn-taking model
6. Roddy et al. 2018 - Continuous turn-taking prediction

### 第三组：看扩展方向与评价问题

7. Fujie et al. 2021 - Timing Generating Networks
8. Ekstedt et al. 2023 - Automatic evaluation of turn-taking cues
9. Uro et al. 2024 - Terminality of speech-turn boundary
10. Schwarz et al. 2023 - Predictive ASR for latency reduction

## 每篇论文的阅读方式

第一次阅读不要马上记所有细节，按下面顺序完成：

1. 只看标题、摘要、图 1、结论，写出一句话总结；
2. 阅读引言，标出作者认为的困难和已有方法的不足；
3. 阅读任务定义和数据部分，确认是否真正是 streaming；
4. 阅读实验表格，记录 baseline、指标和最关键的对照；
5. 最后再看模型细节，判断哪些部分与你们的实验规模匹配。

## 阅读时必须特别检查

- 论文说的 endpoint、end-of-turn、turn-taking、TRP、VAD 是否是同一个概念；
- 模型是否使用了未来音频、完整转写或人工边界；
- latency 的起点和终点如何定义；
- cut-in、false endpoint、over-wait 是否被单独报告；
- 数据集是否公开，代码是否公开；
- 结果是否来自一次运行，是否报告随机性；
- 论文的创新到底是新模型、新标签、新数据，还是新的评价方式。

## 当前阅读任务

先精读 `01-Maier2017-End-of-Turn.md`，读完后再读 `02-Chang2022-Turn-Taking.md`。两篇读完，应该能回答：

1. 固定静音阈值为什么不够？
2. 增量文本相比声学信号多提供了什么信息？
3. 我们的评价是否必须同时包含 latency 和 cut-in？

