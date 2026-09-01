# Turn-Taking Prediction Based on Detection of Transition Relevance Place

## 基本信息

- 作者：Kohei Hara, Koji Inoue, Katsuya Takanashi, Tatsuya Kawahara
- 会议：Interspeech 2019
- 论文：[ISCA 页面](https://www.isca-archive.org/interspeech_2019/hara19_interspeech.html) ｜ [PDF](https://www.isca-archive.org/interspeech_2019/hara19_interspeech.pdf)
- 阅读状态：待精读
- 与本课题的相关性：高

## 初筛记录

论文引入 Transition Relevance Place（TRP）：当前说话人的话轮在某个位置可以自然完成，其他人此时接话不会被视为打断。方法分两步，先检测 TRP，再判断是否发生 turn-taking。

作者在 human-robot dialogue corpus 上进行了 TRP 标注，并报告引入 TRP 后话轮预测准确率得到改善。

## 精读问题

- TRP 的标注标准是什么，标注者一致性如何？
- TRP 和简单 end-of-turn 标签的区别是什么？
- 两阶段方法是否出现误差级联？
- 评价是 frame-level、utterance-level 还是 event-level？
- 是否报告响应时延和误截断代价？

## 对我们课题的启发

如果后续发现“结束/未结束”标签过于粗糙，可以把 TRP 作为中间标签。但 TRP 标注成本较高，不适合作为第一版实验的必需部分。

