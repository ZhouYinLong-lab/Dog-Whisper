# Timing Generating Networks: Neural Network Based Precise Turn-Taking Timing Prediction in Multiparty Conversation

## 基本信息

- 作者：Shinya Fujie, Hayato Katayama, Jin Sakuma, Tetsunori Kobayashi
- 会议：Interspeech 2021
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2021/fujie21_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2021/fujie21_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：中高

## 初筛记录

论文关注的不只是“是否结束”，还关注系统应该在什么精确时刻开始说话。Timing Generating Network 将响应时机建模为可微的 timing generation 问题，试图减少 VAD 和固定响应时间等硬模块造成的误差传播。

作者报告该方法优于基于 VAD 硬决策和固定响应时间估计的传统系统。

## 精读问题

- 目标 timing label 如何获得？
- 多方对话中系统与多个用户的角色如何定义？
- 模型输出是一个时刻、概率分布还是连续时间值？
- latency 和 interruption/cut-in 如何定义？
- 该方法对本科项目来说是否可以只作为相关工作，而不是复现对象？

## 对我们课题的启发

它说明端点检测和响应 timing 可以被分开讨论。我们当前课题先研究用户端 `HOLD/SHIFT`，不把 TGN 的完整生成式 timing 建模作为主线。

