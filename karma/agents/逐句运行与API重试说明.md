# 逐句运行与 API 重试说明

2026-11-04。实施计划：[逐句反馈实施计划](逐句反馈实施计划.md)。

## 默认调用范围

主程序默认使用 `--feedback-scope sentence --text-scope sentence`。重建文本、文本对比以及 Add、Replace、Remove 每次处理一个源句对应的数据。基线抽取、拆分和实体反馈仍按原入口运行。

程序先逐句生成重建文本，汇总后逐句对比，再逐句完成 Add → Replace → Remove。各步骤顺序执行，当前不启用并发。10 句且各句均有三元组时，这五个环节正常共约 50 次调用，不含实体等其他环节、有限返修和 API 重试。

只比较反馈范围时可用 `--feedback-scope sentence --text-scope document`；恢复整篇调用用 `--feedback-scope document --text-scope document`。控制变量实验优先使用下方固定输入回放工具，因为重新跑上游即使参数相同也可能产生不同内容。

源码入口：[主流程](../core/pipeline.py)、[逐句反馈调度](../core/sentence_feedback_pipeline.py)、[三阶段执行](../core/feedback_pipeline.py)、[重建文本](text_generation/agent.py)、[文本对比](text_comparison/agent.py)。

## 请求间隔与持续重试

按用户最新要求，只对原 Chat Completions 重试机制做两项行为修改：取消重试次数上限；每次等待最长 30 秒。

- 原有重试条件保留：HTTP 429、5xx，以及 httpx 网络错误和超时。
- 无有效 Retry-After 时等待序列为 2、4、8、16、30、30……秒，持续重试同一请求。
- 原有数字形式 Retry-After 继续支持，但同样限制在 30 秒以内；没有新增 HTTP 日期或 retry-after-ms 解析。
- 其他 HTTP 错误保持原来的异常与各 Agent 失败处理。408、409 没有新增重试；429 中的账户额度错误没有特别分支。
- Ctrl+C 沿用原有 Python 中断行为。
- Responses 恢复原 SDK 调用及错误处理，不额外加入无限重试；SDK 客户端的重试和超时配置恢复原设置。
- 已撤销额外的统一请求间隔、随机抖动、分段等待及两接口共用重试模块。逐句处理仍顺序执行。

请求及回复记录用于逐句审计，保留消息、结果和重试记录，不改变上述重试条件。JSON 解析错误继续按既有失败策略处理。

源码：[原有接口调用与重试](../core/base_agent.py)。

## 输出与来源检查

- `_dump_doc0_generation_S3.json`、`_dump_doc0_comparison_S3.json`：本句请求、原始回复和重试记录。空三元组不调用重建模型，其状态保留在重建结果中。
- `_dump_doc0_feedback_S3_2_replace.json`：S3 的 Replace 输入输出、实际修改、来源与当前编号。
- `revision_result.json` 中的 after_add、after_replace、after_revision：各句对应阶段的汇总，不仅是最后一句。
- revision_audit 包含 sentence_runs、snapshot_index_maps 和带句编号的 stages。编号须结合源句及版本解释。
- 抽取、拆分和去重保留每条三元组的源句编号；不同源句中的相同三元组不合并来源。逐句反馈遇到来源编号缺失、多值或无效的旧条目时明确报错，不自动切换到整篇调用；需恢复原始逐句归属后再运行。显式设置 feedback_scope=document 仍使用整篇入口。
- 逐句 Remove 检查本句重复。汇总不增加新的跨句语义去重；既有冲突处理沿用原流程。

## 固定输入对照

工具：[compare_feedback_scopes.py](../../tools/evaluation/compare_feedback_scopes.py)。直接读取一篇文章保存的拆分后三元组、源句、重建文本、差异及候选实体，分别运行整篇反馈与逐句反馈；不重新调用拆分、重建或对比。

```powershell
python tools/evaluation/compare_feedback_scopes.py --revision-result <revision_result.json路径> --feedback-input <feedback.json路径> --entities <候选实体数组JSON路径> --output-dir <新输出目录> --base-url <接口地址> --model <模型名> --gold <修改后Gold路径> --gold-key <该篇Gold键>
```

密钥从 `KARMA_API_KEY` 环境变量读取。候选实体文件应采用该次反馈实际使用的数据，支持 name 或 mention 字段；真实候选为空时提供 `[]`，缺失材料不要用虚构内容代替。Responses 模式追加 `--api-mode responses`。

输出 document.json、sentence.json，均含相同输入的 SHA256 和实际运行配置。提供 Gold 时生成 lenient_metrics.json，按仓库既有宽松匹配规则给出拆分后、Add 后、Replace 后、反馈后的 P/R/F1，以及 feedback_delta；逐句输入须具有有效的单句来源编号。

## 验证范围

离线测试和反馈示例用于核对格式、来源传递及操作执行；模型抽取质量需另行运行评估。测试覆盖超过旧上限仍继续重试、2/4/8/16/30 秒等待与持续封顶、Retry-After 封顶、原 Responses 行为、网络错误、主动中断、原有 Agent 回退、逐句隔离、空句补抽、编号映射、有限返修、失败隔离、主流程文件汇总和固定输入回放。

尚未使用真实 API 运行本次改动，没有新的反馈质量或费用结论。实际效果应采用用户指定的修改后 Gold 和同一批输入核对。
