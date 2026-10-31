# Agent Prompt总览与当前调用路线

更新日期：2026-11-01。源码版本：`40c4adf1e546bcd149155843f7297d0fc7b64107`。

## 当前运行的prompt是否唯一

每一次模型调用只采用一套确定的System和User；程序按调用入口选择分支，不会把所有分支prompt一起发给模型。实体与关系抽取有第一轮、第二轮之分，因此不同阶段有不同消息。重建文本与比较当前由pipeline传入sentence_groups，使用分组版本；“非分组User”只是未传该参数时保留的另一条入口。分组是同一请求内按S1、S2等组织材料，不等于每句分别调用一次模型。

## 各Agent文档与当前状态

| Agent | 完整Prompt文档 | 运行状态 |
| --- | --- | --- |
| ingestion | [摄入Agent_完整Prompt](<ingestion/摄入Agent_完整Prompt.md>) | 当前process只做文本规范化，_extract_metadata调用已注释，metadata=None；下面完整prompt属于保留但未由当前process调用的元数据入口。 |
| reader | [阅读Agent_完整Prompt](<reader/阅读Agent_完整Prompt.md>) | 普通文档准备阶段会分批调用相关性评分，每批最多5段；回放已保存基线时可能跳过准备阶段。每段送给评分的文本目前截取前500字符并加省略号。 |
| summarizer | [摘要Agent_完整Prompt](<summarizer/摘要Agent_完整Prompt.md>) | 当前pipeline默认跳过摘要；仅环境变量KARMA_USE_SUMMARIZER为非空值时启用。直接调用摘要方法且输入长度小于15字符时，也不调用模型。 |
| entity_extraction | [实体抽取Agent_完整Prompt](<entity_extraction/实体抽取Agent_完整Prompt.md>) | 当前pipeline第一轮执行实体抽取，第二轮执行实体反馈。两轮共用同一System，但User不同；每次调用只使用对应轮次的一套消息。 |
| relationship_extraction | [关系抽取Agent_完整Prompt](<relationship_extraction/关系抽取Agent_完整Prompt.md>) | 当前pipeline第一轮执行关系抽取，第二轮执行关系反馈。两轮System和User分别选择；反馈System覆盖第一轮System，不叠加FACT_RULES。 |
| triple_splitting | [拆分Agent_完整Prompt](<triple_splitting/拆分Agent_完整Prompt.md>) | 拆分阶段通过process调用专用System和User；只生成add/replace，remove固定为空。回放或跳过阶段时是否执行，以实际入口为准。 |
| text_generation | [重建文本Agent_完整Prompt](<text_generation/重建文本Agent_完整Prompt.md>) | 当前pipeline明确传入sentence_groups，因此采用generate_grouped的分组System和User。另一条generate_text路径只在不传分组或直接调用时使用，不会同时发送。 |
| text_comparison | [文本对比Agent_完整Prompt](<text_comparison/文本对比Agent_完整Prompt.md>) | 当前pipeline明确传入sentence_groups与reconstructions，因此采用compare_grouped。另一条compare路径只在不传分组或直接调用时使用，不会与当前版本叠加。 |
| conflict_resolution | [冲突处理Agent_完整Prompt](<conflict_resolution/冲突处理Agent_完整Prompt.md>) | 当前process执行Python矛盾关系和置信度比较规则，不调用模型。源码定义了System字符串，但当前没有实际发送的User或模型请求。 |
| evaluator | [评估Agent_完整Prompt](<evaluator/评估Agent_完整Prompt.md>) | 当前process执行Python加权评分和阈值筛选，不调用模型。源码System字符串不参与运行决策；实际逻辑以finalize_triples和_aggregate_scores为准，不能把字符串里的最低分条件当成已执行检查。 |
| schema_alignment | [模式对齐Agent_完整Prompt](<schema_alignment/模式对齐Agent_完整Prompt.md>) | 当前pipeline中初始化和调用均被注释。即使单独调用该类，现有process也是Python类型/关系映射，没有模型调用；定义的System不代表当前生效。 |

## 当前分组调用的源码证据

karma/core/pipeline.py 第385—401行；实体两轮选择：karma/core/pipeline.py 第419—426行；关系两轮选择：karma/core/pipeline.py 第450—460行。

## 阅读方式

每个文档按轮次/入口连续展示同一请求的System和User，每部分前仅用一行说明内容、相对文件路径和源码行号。固定内容全部展开，仅运行数据保留变量表达式。各Agent目录的Prompt完整模板.json保存不含阅读标注的角色结构。
