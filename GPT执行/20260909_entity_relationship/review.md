# Entity / Relationship 修改说明与复审

本次修改日期：2026-09-09。修改已在本地完成，未提交或推送 Git。

## 之前讨论中确认的约定

- 使用“源文本”，保持 pipeline 的 summaries 数据源；Summarizer 关闭时使用清理后的源文本。
- 使用“当前实体集合 / 当前三元组集合”，模型无需理解“第一轮”的程序流程。
- diff 的 A 是源文本，B 是三元组重建文本。两组差异都是比较模型的候选线索。
- 以完整 head/relation/tail 判断语义，主动被动、头尾调换必须结合完整事实核实。
- 采用正向输出要求“完整回复采用 JSON 数组/对象”，没有加入“不要输出 Markdown 或说明文字”。
- evidence 保留原文片段要求，Python 暂不检查是否匹配原文。
- confidence/clarity/relevance 分开判断；没有新增置信度硬阈值。既有综合分数阈值保持可配置。
- Schema Alignment 仍停用，原始实现和注释调用保留。

## 最终数据流

源文本 → E1 → 三元组抽取 → 冲突处理/评分 → T1 → 文本重建和比较 → diff。

源文本 + E1 + T1 + diff → 实体审校 → 完整 E2。

源文本 + E2 + T1 + diff → 三元组审校 → add/remove/replace → Python 执行 → 冲突处理/评分 → T2。

每篇文章 T2 的头尾生成该文档最终实体；加入全局图谱，不删除其他文章的节点。

## 本次改动

1. Entity：保留两轮 LLM，第二轮返回完整审校候选集合，替换原先的 E1/E2 并集。
2. Relationship：第一轮取消空实体和至少两个实体的门槛；第二轮重新输入 E2，作为候选提示。
3. 共享规则：extraction_support.py 集中维护实体边界、事实判断、评分、diff 定义和结构解析。
4. 关系覆盖：同时检查动作、状态、定义、组成、属性、比较；同一对象的多个关系分别检查。
5. 语义保护：保留否定、情态、条件与数量；目的表述不升级成已经发生的结果。
6. 解析：普通 JSON、Markdown JSON 代码块、简单说明包裹均可解析；错误顶层类型不误取内部数组。
7. 单条非法三元组单独拒收；非法/缺失分数回退 0.5，合法零分保留；布尔编号、小数编号、空/null 头尾拒收。
8. 同一编号的多次 remove/replace 全部拒绝并保留原条目；其余有效操作正常执行。
9. E2 格式不完整时整体保留 E1；R2 调用/顶层解析失败时保留 T1。有效空数组与失败区分。
10. 失败记录保留原始模型回复，便于区分“模型没有抽取”和“程序没有解析成功”。
11. 最终 entities 现在表示最终三元组使用的节点，初始/审校候选单独保存。
12. 修复两个 legacy 抽取方法遗漏 diff 参数造成的调用错误，保留直接调用方式。
13. Evaluator 的数字前缀文件现在写入实际保留结果；筛选前候选另存审计文件。
14. 修复最终 CSV 阶段标签：当前 relationships 是 after_revision，不再称 initial_extraction。

## 输出位置与兼容性

正式运行结果仍位于 data/result/<时间戳>/，不改输入与 gold 路径。

- NNN_HHMMSS.json：各文档两轮实际保留三元组。空结果也写文件，保持 2i/2i+1 对齐。
- _evaluation_NNN_candidates.json：该轮进入 Evaluator 的候选，筛选前记录。
- _dump_docI_r0_entities.json：E1。
- _dump_docI_r1_entities.json：E2，或审校失败时回退的 E1。
- _dump_docI_rT_entity_audit.json：实体抽取/审校记录及失败原因。
- _dump_docI_r0_relationship_audit.json：第一轮解析明细、非法条目、默认分数和模型条目。
- _dump_docI_r1_revision.json：三元组操作及拒收原因。
- _dump_docI_feedback.json：实际文本 A、B 与 diff。
- _dump_docI_final_entities.json：T2 的头尾节点。

中间结果新增 initial_entities、revised_entities、initial_relationships、baseline_triples。
entities 是最终节点；relationships 仍是末轮候选；integrated_triples 是末轮保留三元组。
JSON 集合多文档运行时，原有 IntermediateOutput 仍代表最后一篇；各篇结果看文档编号文件，全局图谱包含全部文档。主程序已增加这条提示。

历史结果与新结果在非零集成阈值下可能有评估口径差异：旧数字前缀文件保存筛选前候选，新文件保存实际保留结果。进行前后对比时应统一阈值和数据口径。

## 提示词复审

- 消除了“实体最小化”与“完整头尾边界”的冲突。
- 移除了只强调动作、商业领域及生物医学回退造成的偏向。
- E2 的 B 侧差异不会直接认定相关实体无效；对象可以正确而关系错误。
- E2 候选增删不会触发程序自动增删关系；关系仍完整审校。
- 第一轮和第二轮事实规则共享，避免以后只修改其中一处。
- 输出模板中 remove/replace 使用不同示例编号，避免示例自身冲突。
- “分开评分”不要求三个分数人为不同。
- E2 回退时关系 prompt 不再错误宣称名单已经成功审校。
- 完整 before/after system 与 user 内容见 prompt_comparison.md，可运行 export_prompts.py 重新导出。

复审方法参考 OpenAI 官方的输入分区、示例和清晰输出约定，但这不构成对当前 DeepSeek 配置抽取质量的保证：
https://developers.openai.com/api/docs/guides/prompt-engineering

## 验证

离线测试位于 test_feedback.py，运行命令：

```powershell
python -B "GPT执行/20260909_entity_relationship/test_feedback.py"
```

15 项测试覆盖：

- JSON 包裹、错误顶层、结构异常、有效空结果与失败区分；
- 0/1 个候选时仍进行关系抽取；
- 单条错误隔离、分数默认、合法零分、非法数字；
- E2 替换、失败回退、提及形式保留；
- add/remove/replace、冲突保留原条目、非法编号、evidence 不做原文匹配；
- 两个 legacy 入口；
- 最终节点和数据结构序列化回读；
- 两文档两轮完整流程与 main.py 真实命令行执行路径，分别设置两种 API 模式；
- 非零阈值时文件与返回值一致、每篇两个数字前缀文件、候选孤立节点不进入图谱；
- Schema 不被初始化/执行；上下文未串到下一文档。

模型回复在 BaseAgent 边界模拟，并阻止外部 HTTP 请求。通过表示程序数据流、导出和回退可运行，不能当作真实 API 可用性或召回率提升的证据。
额外检查覆盖项目 Python 语法、main/karma.cli 帮助入口与 git diff --check。

## 仍需实验判断的取舍

| 当前选择 | 优点 | 局限 | 后续方案 |
|---|---|---|---|
| E2 返回完整数组 | 易读、流程简单，可删除旧错误候选 | 模型可能意外漏掉旧候选 | 对 E1/E2 做人工抽样；若漏项明显再考虑实体增量操作 |
| 候选名单作为软提示 | 关系模型可以补充漏掉的对象 | 不会强制证明每个候选都被检查 | 对比“用 E1 / 用 E2”的固定条件实验 |
| 保留大小写和不同边界提及 | 保留原文信息，避免粗糙合并语义不同的缩写 | 候选数可能变多，身份仍未消歧 | 后续单独设计实体身份层，不用它改写 gold 所需原文 |
| evidence 只检查非空字符串 | 无格式匹配误杀，代码简单 | 不能识别伪造或无关证据 | 后续再评估宽松文本匹配或独立审校 |
| 当前 summaries 整篇输入 | 保留跨句上下文，与既有流程一致 | 长文可能遗漏，E2 增加 token | 用长文样本评估分段+全文复核，考虑跨句事实损失 |
| 同编号冲突操作全部回退 | 结果不由操作顺序偶然决定 | 可能放弃其中一条正确修正 | 观察冲突频率，必要时只重试冲突项 |

上游 Reader/Summarizer 和文本生成/比较的旧提示词没有在本次重写。默认 Summarizer 关闭；Reader 评分不决定当前抽取文本；重建文本仍可能有压缩或改写误差，所以 diff 被明确降为辅助线索。

现有 gold 评估仍为嵌入相似度匹配，分数提升不能替代人工检查否定、情态、条件和方向。下一次真实实验建议先使用固定小样本，检查新增正确率和误删率，再扩大运行。
