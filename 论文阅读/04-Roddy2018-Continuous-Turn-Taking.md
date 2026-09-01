# Investigating Speech Features for Continuous Turn-Taking Prediction Using LSTMs

## 基本信息

- 作者：Matthew Roddy, Gabriel Skantze, Naomi Harte
- 会议：Interspeech 2018
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2018/roddy18_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2018/roddy18_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：高

## 初筛记录

论文把轮次预测从“在 utterance 末端做一次决定”改成连续预测：模型在每个时间点预测未来时间窗内的语音活动概率。重点比较传统声学特征、词特征和 POS 特征，并分析暂停和重叠处的预测表现。

摘要给出的结论是：传统声学特征表现较好，词特征通常优于 POS 特征，模型整体优于已有 baseline。

## 精读问题

- 未来时间窗具体多长？
- 连续预测的标签如何从对话时间戳生成？
- 模型输出如何转换为真正的 HOLD/SHIFT 决策？
- latency、cut-in 或 overlap 是否被直接评价？
- 词特征是否依赖人工转写，若依赖，怎样模拟 streaming ASR？

## 对我们课题的启发

可以借鉴“连续预测”而不是只做句末二分类，但我们的最小实验仍可先输出 `HOLD/SHIFT`，避免一开始复现完整连续状态空间。

