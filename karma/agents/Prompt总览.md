# Agent Prompt总览与当前调用路线

更新日期：2026-11-04。导出时 Git HEAD：`c3aa35473680505bd66fab4694eb73630ddb8cb9`；文档内容取自当前工作区源码，包含本次未提交修改，精确文件哈希见导出核验 JSON。

## 当前运行的prompt是否唯一

每一次模型调用只采用一套确定的System和User；程序按调用入口选择分支，不会把所有分支prompt一起发给模型。实体抽取仍分两轮；关系抽取只负责基线，反馈由 Add → Replace → Remove 三个 Agent 执行。每个阶段独立核查并接收前一步实际输出；各 Agent 内部采用核对问题、生成操作、复核输出三个阶段。问题由程序传递，模型只输出本阶段操作与 handoff。新事实按单句依据抽取。重建文本与比较当前由pipeline传入sentence_groups，使用分组版本；“非分组User”只是未传该参数时保留的另一条入口。默认 text_scope=sentence，每个分组单独调用重建和对比；feedback_scope=sentence，每句独立完成 Add→Replace→Remove。两个配置均可选 document，恢复整篇调用。逐句反馈遇到历史多来源或无法分组的条目时显式回退整篇并记录。所有请求顺序执行；原 Chat Completions 的 429/5xx/网络重试取消次数上限，等待最多30秒；Responses 保持原接口处理。

运行范围、限流重试及回放命令见 [逐句运行与API重试说明](逐句运行与API重试说明.md)。

## 各Agent文档与当前状态

| Agent | 完整Prompt文档 | 运行状态 |
| --- | --- | --- |
| ingestion | [摄入Agent_完整Prompt](<ingestion/摄入Agent_完整Prompt.md>) | 当前process只做文本规范化，_extract_metadata调用已注释，metadata=None；下面完整prompt属于保留但未由当前process调用的元数据入口。 |
| reader | [阅读Agent_完整Prompt](<reader/阅读Agent_完整Prompt.md>) | 普通文档准备阶段会分批调用相关性评分，每批最多5段；回放已保存基线时可能跳过准备阶段。每段送给评分的文本目前截取前500字符并加省略号。 |
| summarizer | [摘要Agent_完整Prompt](<summarizer/摘要Agent_完整Prompt.md>) | 当前pipeline默认跳过摘要；仅环境变量KARMA_USE_SUMMARIZER为非空值时启用。直接调用摘要方法且输入长度小于15字符时，也不调用模型。 |
| entity_extraction | [实体抽取Agent_完整Prompt](<entity_extraction/实体抽取Agent_完整Prompt.md>) | 当前pipeline第一轮执行实体抽取，第二轮执行实体反馈。两轮共用同一System，但User不同；每次调用只使用对应轮次的一套消息。 |
| relationship_extraction | [关系抽取Agent_完整Prompt](<relationship_extraction/关系抽取Agent_完整Prompt.md>) | 当前仅执行第一轮基线关系抽取。第二轮关系反馈已移到 feedback_add、feedback_replace、feedback_remove，由 FeedbackPipeline 依次调用。三元组分数由程序固定填入0.8，模型只输出事实和证据。 |
| triple_splitting | [拆分Agent_完整Prompt](<triple_splitting/拆分Agent_完整Prompt.md>) | 拆分阶段通过process调用专用System和User；只生成add/replace；程序兼容旧响应中的空remove。回放或跳过阶段时是否执行，以实际入口为准。 |
| text_generation | [重建文本Agent_完整Prompt](<text_generation/重建文本Agent_完整Prompt.md>) | 当前pipeline默认text_scope=sentence，由generate_sentences逐句调用generate_grouped，每次只传一个分组。text_scope=document时一次传入全部分组；两种模式固定System和User相同，仅输入范围不同。另一条generate_text路径只在不传分组或直接调用时使用，不会同时发送。 |
| text_comparison | [文本对比Agent_完整Prompt](<text_comparison/文本对比Agent_完整Prompt.md>) | 当前pipeline默认text_scope=sentence，由compare_sentences逐句调用compare_grouped，每次只传对应源句及重建文本；全文标签也仅包含本句。text_scope=document时一次传入全部分组。两种模式固定提示相同，仅输入范围不同。另一条compare路径只在不传分组或直接调用时使用，不会与当前版本叠加。 |
| conflict_resolution | [冲突处理Agent_完整Prompt](<conflict_resolution/冲突处理Agent_完整Prompt.md>) | 当前process执行Python矛盾关系和置信度比较规则，不调用模型。源码定义了System字符串，但当前没有实际发送的User或模型请求。 |
| evaluator | [评估Agent_完整Prompt](<evaluator/评估Agent_完整Prompt.md>) | 当前process执行Python加权评分和阈值筛选，不调用模型。源码System字符串不参与运行决策；实际逻辑以finalize_triples和_aggregate_scores为准，不能把字符串里的最低分条件当成已执行检查。 |
| schema_alignment | [模式对齐Agent_完整Prompt](<schema_alignment/模式对齐Agent_完整Prompt.md>) | 当前pipeline中初始化和调用均被注释。即使单独调用该类，现有process也是Python类型/关系映射，没有模型调用；定义的System不代表当前生效。 |
| feedback_add | [AddAgent_完整Prompt](<feedback_add/AddAgent_完整Prompt.md>) | 当前反馈阶段调用：遗漏补充。默认每句独立执行 Add → Replace → Remove，再汇总整篇；feedback_scope=document 为整篇调用，固定提示相同。历史共享来源条目无法安全分组时显式回退整篇。每句有尚未投递到 Add/Replace 的问题时最多再执行一轮相关阶段。投递成功不代表语义问题已解决。 |
| feedback_replace | [ReplaceAgent_完整Prompt](<feedback_replace/ReplaceAgent_完整Prompt.md>) | 当前反馈阶段调用：已有表达修正与拆分。默认每句独立执行 Add → Replace → Remove，再汇总整篇；feedback_scope=document 为整篇调用，固定提示相同。历史共享来源条目无法安全分组时显式回退整篇。每句有尚未投递到 Add/Replace 的问题时最多再执行一轮相关阶段。投递成功不代表语义问题已解决。 |
| feedback_remove | [RemoveAgent_完整Prompt](<feedback_remove/RemoveAgent_完整Prompt.md>) | 当前反馈阶段调用：重复清理。默认每句独立执行 Add → Replace → Remove，再汇总整篇；feedback_scope=document 为整篇调用，固定提示相同。历史共享来源条目无法安全分组时显式回退整篇。每句有尚未投递到 Add/Replace 的问题时最多再执行一轮相关阶段。投递成功不代表语义问题已解决。 |

## 当前分组调用的源码证据

karma/core/pipeline.py 第413—415行；文本对比：karma/core/pipeline.py 第428—431行；实体：karma/core/pipeline.py 第452行；基线关系：karma/core/pipeline.py 第484—486行；三步反馈：karma/core/pipeline.py 第491—494行。

## 阅读方式

每个文档按轮次/入口连续展示同一请求的System和User，每部分前仅用一行说明内容、相对文件路径和源码行号。固定内容全部展开，仅运行数据保留变量表达式。各Agent目录的Prompt完整模板.json保存不含阅读标注的角色结构。
