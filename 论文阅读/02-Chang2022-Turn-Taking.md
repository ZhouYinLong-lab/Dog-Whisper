# Turn-Taking Prediction for Natural Conversational Speech

## 基本信息

- 作者：Shuo-Yiin Chang, Bo Li, Tara Sainath, Chao Zhang, Trevor Strohman, Qiao Liang, Yanzhang He
- 会议：Interspeech 2022
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2022/chang22_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2022/chang22_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：高

## 初筛记录（基于摘要，阅读全文后核对）

### 一句话总结

论文研究自然对话中的流式轮次预测，重点区分用户的思考停顿、犹豫、填充词和真正结束，并在端到端 ASR 模型上联合优化识别与轮次判断。

### 问题定义

许多语音助手假设用户一次只说一个完整查询，但自然对话中经常出现停顿、重复、填充词和多个连续问题。系统必须判断用户是要继续说，还是已经完成当前请求。

### 方法线索

- 基于端到端 ASR recognizer；
- 联合优化 ASR task、pausing detection 和 finished-speaking detection；
- 比较 acoustic-based、text-based 和 E2E 方法；
- 关注自然对话而不是单轮、无犹豫的语音查询。

### 初步结论

论文强调，端点检测不能把所有静音都视为结束。声学和增量文本的联合建模可能更适合自然对话场景，但阅读全文时必须确认各设置的公平性和数据可得性。

## 精读时重点记录

- 公开数据集和内部数据集分别承担什么作用；
- ASR partial hypothesis 如何生成；
- pausing 与 finished-speaking 的标签如何区分；
- 模型是否使用了未来上下文；
- 论文是否报告 endpoint latency、cut-in 或只报告分类指标；
- ASR 和 turn-taking 联合训练时，是否存在任务权重敏感性；
- 哪个结果可以在课程项目中复现，哪个需要工业数据。

## 对我们课题的启发

这篇论文可以帮助我们把“用户停顿”和“用户结束”分成不同决策状态，也提醒我们不能只用静音长度作为唯一特征。我们的可行版本可以先使用公开数据进行离线流式模拟，再决定是否接入真实增量 ASR。

## 阅读后填写

- 作者的主要创新是：
- 与 Maier 2017 的最大区别是：
- 数据和标签是否足以支撑结论：
- 我们能复现的 baseline 是：
- 我还不理解的地方：

