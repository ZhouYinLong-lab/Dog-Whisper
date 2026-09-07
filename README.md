# Dog-Whisper

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Research status](https://img.shields.io/badge/status-literature%20survey-blue)](调研方向方案.md)
[![GitHub](https://img.shields.io/badge/GitHub-ZhouYinLong--lab%2FDog--Whisper-181717?logo=github)](https://github.com/ZhouYinLong-lab/Dog-Whisper)

流式语音对话中的端点检测与轮次预测调研仓库。

## 研究方向

**Streaming spoken dialogue: end-of-turn prediction under the latency–cut-in trade-off**

研究系统如何在用户持续说话时判断当前话轮是否结束，在降低响应延迟的同时避免误截断。重点关注：

- 固定静音阈值、VAD 与轻量因果声学模型的比较；
- 增量 ASR 文本对端点判断的作用；
- endpoint latency、false-positive/cut-in rate 与 over-wait rate 的权衡；
- TurnBench、EotBench 等公开资源上的可复现实验。

本方向不研究特殊/低资源语音、参数高效微调、语音伪造检测或音乐/音色任务。

## 仓库内容

| 文件/目录 | 内容 |
|---|---|
| [`调研方向方案.md`](调研方向方案.md) | 方向定义、研究问题与实验边界 |
| [`完整调研报告_v0.4.md`](完整调研报告_v0.4.md) | 按“调研结果与初步研究方案”结构整理的自洽版报告 |
| [`完整调研报告_v0.3.md`](完整调研报告_v0.3.md) | 七点结构的前一版正式初步调研报告 |
| [`完整调研报告_v0.2.md`](完整调研报告_v0.2.md) | 七点结构的前一版调研报告 |
| [`报告/`](报告/) | 七份独立分项报告与报告目录 |
| [`初步调研报告_v0.1.md`](初步调研报告_v0.1.md) | 第一轮文献调研、研究空缺与可行性判断 |
| [`调研过程与来源索引_v0.1.md`](调研过程与来源索引_v0.1.md) | 检索过程、公开来源和证据留痕 |
| [`阶段性研究结果_v0.1.md`](阶段性研究结果_v0.1.md) | 当前研究结论、基准与实验矩阵 |
| [`文献调研表_v0.1.md`](文献调研表_v0.1.md) | 文献和资源总表 |
| [`论文阅读/`](论文阅读/) | 分层阅读路线与逐篇阅读笔记 |

## 推荐入口

先阅读 [`论文阅读/00-分层阅读说明.md`](论文阅读/00-分层阅读说明.md)，再按“综述 → 理论奠基 → 计算轮次预测 → 连续模型 → 最新基准”的顺序阅读。

## 数据与许可证说明

本仓库目前只保存调研文档、阅读笔记和实验规划，不包含第三方语音数据。TurnBench、EotBench、Switchboard 等数据集及其衍生内容均需遵守各自的许可证、访问条件和使用限制；本仓库的 MIT 许可证不扩展第三方数据的授权范围。

## Citation

如果本仓库的调研材料对你的工作有帮助，可以引用仓库版本或引用其中列出的原始论文。仓库版本信息见 [`CITATION.cff`](CITATION.cff)。

## License

除第三方内容和外部链接所指向的材料外，本仓库内容以 [MIT License](LICENSE) 发布。
