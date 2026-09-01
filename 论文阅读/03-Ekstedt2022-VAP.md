# Voice Activity Projection: Self-supervised Learning of Turn-taking Events

## 基本信息

- 作者：Erik Ekstedt, Gabriel Skantze
- 会议：Interspeech 2022
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2022/ekstedt22_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2022/ekstedt22_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：中高

## 初筛记录（基于摘要，阅读全文后核对）

### 一句话总结

论文提出 Voice Activity Projection（VAP），通过自监督方式预测对话双方未来的语音活动状态，用统一的未来语音活动建模来支持话轮切换、backchannel 和下一位说话人预测。

### 问题定义

传统 turn-taking 模型往往需要人工标注“何时结束”或“何时接话”。VAP 将任务重新定义为预测未来时间窗口内双方是否发声，从而减少对人工轮次标签的依赖。

### 方法线索

- 自监督训练目标；
- 输入是对话双方的语音活动序列；
- 输出是未来语音活动状态的概率分布；
- 任务覆盖 turn shift、turn hold、backchannel 等多个现象。

### 初步结论

摘要显示，VAP 可以作为较通用的 turn-taking 表征和预测工具，并在多个 zero-shot 任务上优于已有方法。

## 精读时重点记录

- 未来时间窗口如何划分；
- 输出状态与 `HOLD/SHIFT` 如何对应；
- 为什么要建模双方语音活动的联合依赖；
- 训练数据是否需要对话双方的独立音轨；
- VAP 与单用户端点检测的关系；
- 评价指标是否能直接转化为 endpoint latency/cut-in；
- 该方法在重叠语音和麦克风串音下如何处理。

## 对我们课题的启发

VAP 不应直接被当作我们的最终 endpoint detector，因为它预测的是未来双方 voice activity，而不是简单的“用户是否说完”。但它可以作为扩展方向，或帮助我们理解为什么自然轮次预测比单通道 VAD 更接近真实对话。

## 阅读后填写

- VAP 的预测目标具体是：
- 它与 endpoint detection 的相同点是：
- 它与 endpoint detection 的不同点是：
- 我们是否需要使用 VAP：
- 我还不理解的地方：

