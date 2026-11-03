# 反馈 Prompt 分配与案例核查

状态：2026-11-03 第 2 版设计稿。Replace 直接将一条旧三元组换成一条或多条，新三元组写在 new_triples 数组中。现有运行代码仍是单次反馈调用；本稿分配现有规则并给出拟新增文本，不代表已实现三个 Agent，不代表历史运行实际请求。Gold、运行三元组和正式 Prompt 文档均未修改。

## 1. 确定的职责

顺序：Add 遗漏补充 → Replace 已有表达修正与拆分（一条可直接换成多条）→ Remove 重复清理。
每个 Agent 先核实交接事项，再独立检查其职责范围内的完整源句或集合，输出自己的问题清单和操作。前序清单不构成检查范围上限，判断可被后续依据源句更正。没有单独的问题核对 Agent。

- [Add 完整草案](AddAgent_Prompt草案.md)
- [Replace 完整草案](ReplaceAgent_Prompt草案.md)
- [Remove 完整草案](RemoveAgent_Prompt草案.md)
- [三份拟发送消息 JSON](Prompt草案模板.json)

## 2. 原有 Prompt 如何分配

| 原有内容 | 当前来源 | 分配方式 |
|---|---|---|
| 源句、对象、方向、词形、限定、目的和风险 | [karma/agents/relationship_extraction/agent.py 第197—208行](../../karma/agents/relationship_extraction/agent.py#L197) | 三者共享判断标准；Add 核实新增事实，Replace 修正表达，Remove 判断是否等价 |
| 源文、分组、当前集合、候选实体、差异 | [karma/agents/relationship_extraction/agent.py 第217—248行](../../karma/agents/relationship_extraction/agent.py#L217) | 每阶段更新当前集合；源文不变；差异标明对应反馈前 V0 |
| add 定义与内部关系 | [karma/agents/relationship_extraction/agent.py 第251—256行](../../karma/agents/relationship_extraction/agent.py#L251) | 完全遗漏交 Add；已有长字段的拆分交 Replace，由其将原条目换成多条 |
| replace 定义 | [karma/agents/relationship_extraction/agent.py 第257—259行](../../karma/agents/relationship_extraction/agent.py#L257) | Replace，保留拆分能力，但输出改成 replace 的 new_triples 数组，不再单独输出 add |
| remove 的完整重复与局部重叠 | [karma/agents/relationship_extraction/agent.py 第262—264行](../../karma/agents/relationship_extraction/agent.py#L262) | Remove 自主搜索、判断并选择保留项 |
| 无依据且无法修正的删除 | [karma/agents/relationship_extraction/agent.py 第260—261行](../../karma/agents/relationship_extraction/agent.py#L260) | 当前草案先列 review，保留原有能力缺口的显式记录；正式实现前需决定由谁执行，不能静默忽略 |
| 原文证据、来源、编号和 reason | [karma/agents/relationship_extraction/agent.py 第268—276行](../../karma/agents/relationship_extraction/agent.py#L268) | 所有操作沿用；增加问题 ID、前序事项状态、替换结果数组及 keep_index |
| confidence/clarity/relevance | [karma/agents/relationship_extraction/agent.py 第57—68行](../../karma/agents/relationship_extraction/agent.py#L57) | Add、Replace 生成新表达时沿用；Remove 不用分数替代重复判断 |
| 定位源句、找到关系和主体、限定 | [karma/agents/relationship_extraction/agent.py 第281—295行](../../karma/agents/relationship_extraction/agent.py#L281) | Add 从源句查覆盖；Replace 从已有表达查错误；Remove 回查候选是否等价 |
| 查找已有表达 | [karma/agents/relationship_extraction/agent.py 第297—300行](../../karma/agents/relationship_extraction/agent.py#L297) | Add 分流已有错误或长字段内容；Replace 查找内部关系已有条目；Remove 查找保留项 |
| 定位字段错误 | [karma/agents/relationship_extraction/agent.py 第302—306行](../../karma/agents/relationship_extraction/agent.py#L302) | Replace；Add/Remove 也能发现并交接 |
| 差异核实与自主检查 | [karma/agents/relationship_extraction/agent.py 第308—311行](../../karma/agents/relationship_extraction/agent.py#L308) | 三者共享；Add 重点查遗漏，Replace 查已有表达，Remove 不依赖差异发起检查 |
| 修正和拆分 | [karma/agents/relationship_extraction/agent.py 第313—316行](../../karma/agents/relationship_extraction/agent.py#L313) | Replace；拆分结果全部放入同一 replace 的 new_triples |
| 生成 add | [karma/agents/relationship_extraction/agent.py 第318—320行](../../karma/agents/relationship_extraction/agent.py#L318) | Add 补遗漏；Replace 在替换结果数组中完成拆分，两者都检查是否重复 |
| 去重 | [karma/agents/relationship_extraction/agent.py 第322—325行](../../karma/agents/relationship_extraction/agent.py#L322) | Remove 对完整候选集合独立检查；自身不能处理的字段错误返修 |
| 词形、覆盖与输出 | [karma/agents/relationship_extraction/agent.py 第327—333行](../../karma/agents/relationship_extraction/agent.py#L327) | Add/Replace 核对生成项；各阶段输出检查范围、问题与操作 |
| 读取/存储缺失示例 | [karma/agents/relationship_extraction/agent.py 第335—339行](../../karma/agents/relationship_extraction/agent.py#L335) | Add |
| 选择范围错误示例 | [karma/agents/relationship_extraction/agent.py 第340—343行](../../karma/agents/relationship_extraction/agent.py#L340) | Replace 修复选择范围；冗余条目交 Remove；两步关联需要程序记录 |
| 内部关系及错误主体示例 | [karma/agents/relationship_extraction/agent.py 第345—357行](../../karma/agents/relationship_extraction/agent.py#L345) | Replace，草案保留已有正确/已有错误/没有独立条目三种分支 |
| 用途与词形示例 | [karma/agents/relationship_extraction/agent.py 第359—365行](../../karma/agents/relationship_extraction/agent.py#L359) | Replace；完全缺失的 includes 属 Add 检查责任，Replace 自主发现时仍可交接 |
| 重复与共同主语示例 | [karma/agents/relationship_extraction/agent.py 第367—371行](../../karma/agents/relationship_extraction/agent.py#L367) | Remove，补充保留项判断和局部重叠分支 |
| 重建文本错误示例 | [karma/agents/relationship_extraction/agent.py 第373—378行](../../karma/agents/relationship_extraction/agent.py#L373) | Add、Replace 明确使用；公共规则供 Remove 核查 |
| 根据严重程度的缺失关系示例 | [karma/agents/relationship_extraction/agent.py 第380—391行](../../karma/agents/relationship_extraction/agent.py#L380) | 若当前字段完全没有该关系由 Add 补；若嵌入长字段则由 Replace 拆分 |
| 混合操作 JSON 示例、输出与调用 | [karma/agents/relationship_extraction/agent.py 第393—505行](../../karma/agents/relationship_extraction/agent.py#L393) | 重新按职责组织输出。新问题清单协议尚未被当前调用流程实现，不能直接把模板替换进去就当成完成重构 |

## 3. 具体案例：已有什么，缺什么，归谁

以下依据已提供的 10301 汇总及当前源码。当前规则存在不等于能证明远端某次实际请求完整加载了它，也不足以证明失败发生在解析或应用代码。

| 案例 | 已有要求 | 本次缺口和拟补内容 | 负责者 |
|---|---|---|---|
| doc0/S2 盲目补目的关系 | [karma/agents/relationship_extraction/agent.py 第254—259行](../../karma/agents/relationship_extraction/agent.py#L254) 优先修正已有条目；[karma/agents/relationship_extraction/agent.py 第359—365行](../../karma/agents/relationship_extraction/agent.py#L359) 用途例子 | Add 明确把已有动作缺少目的连接交 Replace；Replace 用现有 index 补全 query→identify 等连接，再检查是否仍缺独立关系 | Add 分流；Replace 修正 |
| doc0/S3 两条 make up | [karma/agents/relationship_extraction/agent.py 第263—264行](../../karma/agents/relationship_extraction/agent.py#L263) 按完整含义判断重复 | Remove 自主搜索，并说明 all/any 是不同限定还是在具体上下文中重复表达；不能形成“all/any 一律合并”的规则。当前 Gold 取一条，仍须源句依据 | Remove，主体边界需改则返修 Replace |
| doc0/S3 长字段再次扩长 | [karma/agents/relationship_extraction/agent.py 第258—259行](../../karma/agents/relationship_extraction/agent.py#L258) 与 [karma/agents/relationship_extraction/agent.py 第315—316行](../../karma/agents/relationship_extraction/agent.py#L315) 可收短外层字段 | Replace 明确原文词形一致不要求把整个从句写回字段；独立关系另列后逐项判断实体身份和必要限定。Gold 的 #19 仍保留从句，不能统一删除 | Replace |
| doc1/S9 and/or | [karma/agents/relationship_extraction/agent.py 第373—378行](../../karma/agents/relationship_extraction/agent.py#L373) 已有非常接近的重建错误示例 | Add/Replace 自主核实错误阶段；重建 Agent 另需细化“无明确连接用短句”。原 functions/profiles 输入已经丢失 or，Replace 合回；cell/link 输入并非因重建 or 而需合并 | 上游重建＋Replace；Add 不补重建错误 |
| doc1/S9 since 与排他解释 | [karma/agents/relationship_extraction/agent.py 第308—311行](../../karma/agents/relationship_extraction/agent.py#L308) 核实差异；源文确有 since | 比较指出 since 丢失有依据；把 or 一律解释排他过强，属上游比较问题。当前 Gold 未单列因果，不将这一事实写成运行 prompt 的特例 | 对比 Agent 改进；反馈各阶段核实 |
| doc1/S9 depending on 未拆 | [karma/agents/relationship_extraction/agent.py 第252—255行](../../karma/agents/relationship_extraction/agent.py#L252) 与 [karma/agents/relationship_extraction/agent.py 第315—316行](../../karma/agents/relationship_extraction/agent.py#L315) 已覆盖 | Replace 独立查长字段，拆分时将原条目换成多条，检查主体和边界；Add 从全文覆盖检查发现后交接，不忽略。源文 depending on 与 Gold depend on 的词形冲突单列 | Replace 主责，Add 补查 |
| doc2/S2 mounting 主体错误 | [karma/agents/relationship_extraction/agent.py 第303—305行](../../karma/agents/relationship_extraction/agent.py#L303) 主体检查；[karma/agents/relationship_extraction/agent.py 第359—365行](../../karma/agents/relationship_extraction/agent.py#L359) 用途词形 | 新例子同时展示系统主体、安装修饰与 to provide，修复主体和关系两字段 | Replace |
| doc2/S3 风险内动作脱离联系 | [karma/agents/relationship_extraction/agent.py 第207—208行](../../karma/agents/relationship_extraction/agent.py#L207) 已要求风险联系 | 先确认 loose items 是内部动作主体，再检查 hazards 外层联系；不能简化为主体一律错误，或只将 fly 改回 flying | Replace |
| doc2/S3 法律关系遗漏与长字段 | [karma/agents/relationship_extraction/agent.py 第285—300行](../../karma/agents/relationship_extraction/agent.py#L285) 内部关系和覆盖检查 | 检查长 head 和 tail，将法律针对运输等关系写入拆分后的三元组数组 | Replace，Add 独立发现并交接 |
| doc3/S7 目的重建错误、主体扩展 | [karma/agents/relationship_extraction/agent.py 第310—311行](../../karma/agents/relationship_extraction/agent.py#L310) 和 [karma/agents/relationship_extraction/agent.py 第373—378行](../../karma/agents/relationship_extraction/agent.py#L373) 保留正确三元组 | 新例子明确输入 is to reduce、重建 reduces，不据此改动正确条目。a pre-step of 有原文语义依据但不因重建错误强制补长 | Add/Replace |
| doc3/S7 Gold 主体 | 不属于运行 prompt 规则缺失 | 上下文支持研磨预处理作为目的主体；建议 Gold 使用 a pre-step of grinding the rubber，需由用户决定；本稿不修改 Gold，不把 Gold 当 Agent 输入 | 标注核查 |

## 4. 需要新增的通用文字

三份草案已分别展开以下内容，不只是列建议：

1. 自主性：核实前序事项后，独立扫描本阶段职责范围；空清单和空差异同样检查；前序错误可依据源句更正。
2. 问题清单：先列 issue_id、相关 index、源句证据、具体问题和处理结论，操作关联到问题。
3. Add 边界：完全遗漏可新增；已有错误表达与嵌套未拆交 Replace。发现问题后必须交接，不能只因不属本职跳过。
4. Replace 拆出的新条目：先查内部关系是否已有独立条目；没有时，一项 replace 的 new_triples 写入多条；已有时只修正需要修改的条目。
5. Remove 自主保留选择：完整扫描候选集合，按原文正确性和限定完整性选保留项，每项删除写 keep_index。
6. 历史差异：差异属于 V0，结合实际变更判定当前是否仍存在；前序计划不等于已执行结果。
7. 上游错误：三元组正确而重建或比较出错时保留，记录到对应环节。

## 5. 输入、输出及程序交接

| 阶段 | 输入 | Agent 处理 | 输出给下一步 |
|---|---|---|---|
| 程序准备 | 带来源三元组、源句、重建/差异、实体 | 固定输入版本 V0；生成现有 index 和分组引用 | 源句全文、完整 V0、版本化重建/差异、空交接 |
| Add | 上述数据 | 逐句独立查遗漏＋核对差异，形成清单；新增完全遗漏；交接已有错误和嵌套 | add、issues、handoff、checked 范围 |
| 程序应用 Add | V0＋Add 回复 | 校验格式/来源/证据引用、应用有效项、保存失败，形成 V1；维护编号映射 | 完整 V1、实际变更摘要、未解决事项 |
| Replace | 原文、完整 V1、历史差异及实际变更、前序问题 | 自己检查所有条目，修正主体、词形、修饰和拆分问题 | replace（每项包含 new_triples）、问题清单、前序问题处理结果 |
| 程序应用 Replace | V1＋替换结果 | 检查全部替换结果后在临时副本上应用；同一批替换全部有效才确认，失败则保留该批输入并记录原因，形成 V2 | 完整 V2、实际变更或失败、待处理事项 |
| Remove | 原文、完整 V2、变更及依赖、前序提示 | 独立查重复，判断保留哪条；检查局部重叠与必要限定 | remove＋keep_index、问题清单、返修及未决事项 |
| 程序确认 | V2＋删除输出 | 校验目标与保留项、依赖，候选应用；具体问题可有一轮定向返修并重查受影响集合 | 最终集合、全部实际操作、问题生命周期与未解决事项 |

输入变量具体内容：

- source_sentences_json：原文顺序的 sentence_id＋text，一篇完整传入；无需再重复一份 source_text。
- current_collection_json：version、triples；每项 index、SPO、source_sentence_ids。版本内 index 唯一。
- sentence_index_json：sentence_id 到 index 的引用表，不重复整条 SPO。
- comparison_bundle_json：basis_version、每句 text_a/text_b、A/B 差异及状态。第一次为 V0；后续传原始完整差异并明确历史版本。
- candidate_entities_json：候选 mention；为空也直接依据源文。
- applied_change_log_json：已实际应用的修改前后对照、失败和版本/编号映射，保留相关记录即可。
- handoff_json：尚未解决的问题、前序处理结果、替换前后关系保留情况。每项有来源阶段、问题 ID、相关版本和编号、证据。

当前每篇十句、几十条三元组，三者都接收完整当前集合；不只看前序点名的几条。后序不必再接收完整 V0 三元组，但历史差异所引用且发生变化的旧条目在变更摘要中保留。完整原始回复和历史快照保存日志，不全部重复塞进 prompt。

## 6. 连续示例（演示数据，不是历史请求）

源句 S1：The system includes a module that processes data. S2：The module stores records.
输入 T0=(The system, includes, a module that processes data)，T1/T2 均为 (The module, stores, records)。

1. Add 自主扫描：processes 已在长字段中，交 Replace；records 已覆盖；发现重复可提示 Remove，但不代其决策。add 为空。
2. Replace 自主扫描：将 T0 替换为两条：(The system, includes, a module) 和 (a module, processes, data)；都放在同一 new_triples 数组中。
3. Remove 自主扫描：确认 T1/T2 完整重复，按同样正确时保留较早项的规则保留 T1、删除 T2。即使没有前序提示也须发现。
4. 最终三项：system includes module；module processes data；module stores records。

## 7. 当前缺口与实施边界

本次只交付 Prompt 分配及完整草案。新 Agent 类、编排入口、一条换多条的解析和应用、状态交接和测试尚未实现；当前 exporter 也不认识这些拟新增消息。正式接入时需要一起实现并同步各 Agent 的正式 *_完整Prompt.md、HTML、Prompt完整模板.json 与总览。

拟新增 issues、handoff、replace.new_triples 等字段不是当前 _apply_revision 自动提供的能力。程序检查格式、ID、引用与替换数组完整性；语义是否成立仍由 Agent 判断和外部评估核验。失败不等于没有问题，必须记录；同一批替换中有条目失败时保留该批输入并记录原因，避免只收短外层字段却没有保留内部关系。

Remove 的用户指定核心职责是重复清理；旧代码还允许删除无依据且无法修复的事实。本草案将它显式交给 review，不静默删除、不冒称已完全迁移该能力；接入前需确定责任出口。最后阶段发现需要 Replace/Add 的新问题可定向返修一次，之后检查被影响的重复和依赖；仍不确定则记录，避免无限循环。

运行外验证：固定 10301 反馈前集合，对比旧流程与新流程的错误修复、误改、P/R/F1 增量和调用成本。先处理 Gold 歧义，不用当前有争议的匹配结果迫使模型采用错误主体。当前拆分输入是旧结果，反馈实验不证明新版拆分 Agent 的效果。

## 8. 验证记录

本版根据源码重新表述规则，源码位置表示原规则来源，不表示草案逐字复制原文。模板 JSON 与各 Markdown 的代码块逐段拼合核对，并检查所有 few-shot 的 JSON、编号、证据和一条换多条结构。源码链接及行号、HTML 目录与锚点检查记录在同目录验证文件。这些检查只验证草案完整和格式可用，未调用模型，未证明语义效果提升。

## 9. 第 2 版：用词和 few-shot 的具体调整

- “核实前序待处理事项，再独立扫描”改成“先看前一步发现的问题，再自己检查全部源句或三元组”。
- “原子操作组”从 Agent 输出中移除。一条 replace 自带 new_triples 数组；程序检查后用整个数组替换旧条目。多项替换相互依赖时，程序先检查整批结果，再一起确认。
- “完整重复与局部重叠”在示例里具体展示为：相同事实删一条；includes 和 processes 两项关系都保留。
- 三份草案共有 13 个 few-shot：Add 4 个、Replace 6 个、Remove 3 个。每个示例都有源句、当前三元组、核查结论及完整 JSON 回复。
- few-shot 紧接输出格式，均属于拟发送给 LLM 的 User 消息。实际数据仍用变量表示；示例明确为演示数据。
- Replace 例子覆盖一条换多条、已有内部关系、主体和用途、目的连接、危险联系、重建文本错误。
- 本次修改只是让规则和输出更具体，是否提高模型表现仍需真实运行验证。
