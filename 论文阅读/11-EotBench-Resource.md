# eot-bench：带文本上下文的 End-of-Turn Benchmark

## 基本信息

- 项目：[GitHub](https://github.com/livekit/eot-bench)
- 数据集：[Hugging Face 数据集入口](https://huggingface.co/datasets/livekit/eot-bench-data)
- 阅读状态：待核验
- 与本课题的相关性：高

## 初筛记录

eot-bench 面向真实 human-agent 用户话轮，覆盖 14 种语言，并同时提供音频和文本上下文。每个完整用户话轮中的停顿都被记录：最终停顿作为真实结束，中间停顿作为系统应该继续等待的 hesitation。

它的优势是直接支持 audio-only 与 audio+text 的对照，并以真实暂停和 false-cutoff budget 评价端点检测，而不是把孤立语音片段做普通分类。

## 与 TurnBench 的区别

| 维度 | TurnBench | eot-bench |
| --- | --- | --- |
| 对话关系 | human-human | human-agent |
| 语言 | 英语为主 | 14 种语言 |
| 音频 | 双通道 | 需核对具体格式 |
| 文本 | 主要用于评测事件 | 对齐文本上下文明确提供 |
| 主要事件 | EOT + interruption | EOT 和中间停顿 |
| 适合问题 | 音频端点和中断 | audio/text 融合、false cutoff |

## 精读/核验问题

- 文本上下文是否为真实在线 partial transcript；
- 数据集每种语言和每种场景的规模；
- 许可证是否允许课程项目训练和发布预测结果；
- false-cutoff 和 latency 的具体匹配规则；
- 是否存在说话人、任务或会话级数据泄漏；
- 是否可以在本地完全运行 scorer。

## 对我们课题的使用建议

把 eot-bench 作为第二阶段的 text-fusion 数据源，不要在第一阶段同时处理 14 种语言。优先选择英语或中文，先完成 audio-only baseline，再加入文本上下文。

