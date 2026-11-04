# 逐句运行与 API 重试说明

2026-11-04。实施计划：[逐句反馈实施计划](逐句反馈实施计划.md)。

## 默认调用范围

主程序默认使用 `--feedback-scope sentence --text-scope sentence`。重建文本、文本对比以及 Add、Replace、Remove 每次处理一个源句对应的数据。基线抽取、拆分和实体反馈仍按原入口运行。

程序先逐句生成重建文本，汇总后逐句对比，再逐句完成 Add → Replace → Remove。各步骤顺序执行，当前不启用并发。10 句且各句均有三元组时，这五个环节正常共约 50 次调用，不含实体等其他环节、有限返修和 API 重试。

只比较反馈范围时可用 `--feedback-scope sentence --text-scope document`；恢复整篇调用用 `--feedback-scope document --text-scope document`。控制变量实验优先使用下方固定输入回放工具，因为重新跑上游即使参数相同也可能产生不同内容。

源码入口：[主流程](../core/pipeline.py)、[逐句反馈调度](../core/sentence_feedback_pipeline.py)、[三阶段执行](../core/feedback_pipeline.py)、[重建文本](text_generation/agent.py)、[文本对比](text_comparison/agent.py)。

## 请求间隔与持续重试

所有 Agent 共用请求间隔控制，默认两次请求起始时间至少间隔 1 秒。可通过 `--api-min-interval 3` 改为至少 3 秒；它控制请求频率，不代表预先知道服务商的 token 额度。

| 情况 | 行为 |
| --- | --- |
| HTTP 429 限流 | 无限次等待并重试同一请求，不跳过 Agent |
| HTTP 408、409、5xx，连接错误和超时 | 按同一持续退避策略重试 |
| Retry-After / retry-after-ms | 优先遵循服务端等待要求；支持秒数、毫秒和 HTTP 日期 |
| 没有有效等待头 | 指数退避加抖动，等待增长到约 60 秒后保持该级别 |
| 401/403、参数错误等其他 HTTP 错误 | 停止并报告，避免跳过后继续生成不完整结果 |
| 明确的 insufficient_quota / billing_hard_limit_reached | 停止并报告账户额度耗尽，不当作瞬时限流 |
| 用户 Ctrl+C | 中断请求或等待，不进入 Agent 的失败兜底继续执行 |

没有“连续失败五次后跳过”的 API 重试上限。长等待分段进行并打印进度；同一 Prompt 保持不变。Chat Completions 与 Responses 共用上述机制，Responses SDK 的内置有限重试在主流程中关闭。

成功获得回复之后的 JSON 解析错误仍属于格式错误，按现有规则记录并回退；无限重试专用于可恢复的 API 请求错误，不代表所有错误都会无限重试。程序格式验证也不能判断语义一定正确。

源码：[统一请求与记录](../core/base_agent.py)、[重试和请求间隔](../core/api_retry.py)。退避设计参考 [OpenAI 官方限流说明](https://developers.openai.com/api/docs/guides/rate-limits)；无限次重试是本项目根据用户要求采用的策略。

## 输出与回退

- `_dump_doc0_generation_S3.json`、`_dump_doc0_comparison_S3.json`：本句请求、原始回复和重试记录。空三元组不调用重建模型，其状态保留在重建结果中。
- `_dump_doc0_feedback_S3_2_replace.json`：S3 的 Replace 输入输出、实际修改、来源与当前编号。
- `revision_result.json` 中的 after_add、after_replace、after_revision：各句对应阶段的汇总，不仅是最后一句。
- revision_audit 包含 sentence_runs、snapshot_index_maps 和带句编号的 stages。编号须结合源句及版本解释。
- 历史条目同时关联多个源句或不能安全分组时，反馈显式回退整篇，记录 `requested_scope=sentence`、`scope=document`、fallback_reason 和 fallback_indices。重建与对比的 text_scope 独立保持所选模式。实验报告应将回退文章单列。
- 逐句 Remove 检查本句重复。汇总不增加新的跨句语义去重；既有冲突处理沿用原流程。

## 固定输入对照

工具：[compare_feedback_scopes.py](../../tools/evaluation/compare_feedback_scopes.py)。直接读取一篇文章保存的拆分后三元组、源句、重建文本、差异及候选实体，分别运行整篇反馈与逐句反馈；不重新调用拆分、重建或对比。

```powershell
python tools/evaluation/compare_feedback_scopes.py --revision-result <revision_result.json路径> --feedback-input <feedback.json路径> --entities <候选实体数组JSON路径> --output-dir <新输出目录> --base-url <接口地址> --model <模型名> --gold <修改后Gold路径> --gold-key <该篇Gold键>
```

密钥从 `KARMA_API_KEY` 环境变量读取。候选实体文件应采用该次反馈实际使用的数据，支持 name 或 mention 字段；真实候选为空时提供 `[]`，缺失材料不要用虚构内容代替。Responses 模式追加 `--api-mode responses`。

输出 document.json、sentence.json，均含相同输入的 SHA256 和实际运行配置。提供 Gold 时生成 lenient_metrics.json，按仓库既有宽松匹配规则给出拆分后、Add 后、Replace 后、反馈后的 P/R/F1，以及 feedback_delta；实际是否回退整篇也明确标记。

## 验证范围

已通过 92 项离线测试；9 个反馈示例通过格式和操作执行校验。测试覆盖超过旧上限仍继续重试、两种接口、服务器和网络错误、等待头、主动中断、不可恢复错误传播、逐句隔离、空句补抽、编号映射、有限返修、失败隔离、主流程文件汇总和固定输入回放。

尚未使用真实 API 运行本次改动，没有新的反馈质量或费用结论。实际效果应采用用户指定的修改后 Gold 和同一批输入核对。
