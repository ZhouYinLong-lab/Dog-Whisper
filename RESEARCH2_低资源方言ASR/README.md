# RESEARCH2：低资源方言 ASR

这是与仓库主线分开的课程研究材料归档，记录截至 2026-09-29 的四川话基线和吴语双文本 pilot。

## 内容

- `docs/`：数据审计、相关工作、实验结果、运行说明和阶段汇报。
- `scripts/`：manifest 构造、训练、评估、误差分析与统计脚本。

## 主要结果快照

- 四川话 Whisper-tiny LoRA 单目标基线：说话人隔离测试集 CER 0.4925。
- 吴语双文本 pilot：严格测试集 68 条；共享任务控制 LoRA 方言/普通话 CER 0.8186/0.8445。
- 吴语本地 benchmark 没有 speaker ID；pilot 不能用于跨说话人泛化结论。
- 四川话规范文本尚未完成人工配对标注；本目录不声称已完成四川话双输出实验。

## 数据与大文件

本目录不含语音数据、Parquet、逐条预测、checkpoint 或打包 ZIP。公开仓库只保存文档和源代码；请按原数据集许可获取音频，并在本地生成 manifest 和训练产物。四川话语料的分发权利需由数据提供方确认。

## 阅读入口

1. [`docs/RESEARCH2_阶段汇报.md`](docs/RESEARCH2_阶段汇报.md)
2. [`docs/文献调研_双输出方言ASR_v0.1.md`](docs/文献调研_双输出方言ASR_v0.1.md)
3. [`docs/数据审计_v0.1.md`](docs/数据审计_v0.1.md)
4. [`docs/实验结果总表_v0.1.md`](docs/实验结果总表_v0.1.md)
5. [`docs/wu_paired_pilot_report_v0.3.md`](docs/wu_paired_pilot_report_v0.3.md)

训练依赖与参数以具体脚本和运行记录为准；没有随本目录发布的原始音频、完整环境或模型权重，因此不能仅凭此目录复现已有指标。
