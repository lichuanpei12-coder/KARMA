# 中文 Prompt 审查与旧版英文对照

核查日期：2026年10月8日。依据：当前本地源码和用户指定的旧版源码。本次审查未修改源码、未调用模型、未做中英文效果实验。

同日后续更新：根据用户阅读修改需要，已将实体、关系Prompt从extraction_support移回各自Agent，仅调整存放位置和导入。8种实际请求的system/user/参数逐字一致，15项离线测试通过。以下审查和行号记录保留整理前状态；当前入口见 [Prompt阅读与修改入口](<E:/huawei after/KARMA/GPT执行/中文Prompt审查_20261008/Prompt合并整理/Prompt阅读与修改入口.md>)。主目录现在有三份源码的未提交整理改动；停用Agent设置保持用户原安排。

## 1. 后续工作的基础

已经确定采用中文 Prompt。此次对照的目的，是查找当前中文规则的缺口、矛盾和接口问题，吸收旧英文中仍适合当前任务的要求。

- 当前工作版本：[E:\huawei after\KARMA](<E:/huawei after/KARMA>)，源码在其 `karma` 目录中。
- 对照的旧英文版本：[E:\huawei after\KARMA\旧版\KARMA](<E:/huawei after/KARMA/旧版/KARMA>)。
- 当前本地 Git HEAD：`127f1a1`，提交时间为2026年9月9日16:48（北京时间）。本次核查时 `karma`、`main.py`、`evaluate.py` 相对 HEAD 没有未提交修改；工作区另有后续数据及脚本。本地提交时间不代表后续资料没有更新。
- 2026年10月8日追加线上核查：GitHub `lichuanpei12-coder/KARMA` 的默认分支 `main` 也是 `127f1a1399376fb5e9214cb656b045ca9a698a0b`，与本地HEAD相同。但远程另有 `codex/feedback-comparison-entity` 分支，领先main两个提交，最新为 `9d6883e2e56a008ecf70bb5ca695fead32a1abea`（2026年9月11日11:06:48，北京时间）。因此当前目录是最新main，不能称为整个仓库最新提交的检出目录。该分支只新增反馈对比实验文件及Evaluator结果目录参数，未改核心Prompt，本报告对Prompt的审查仍适用。
- 更新分支的本地副本已找到：[E:\huawei after\临时\KARMA](<E:/huawei after/临时/KARMA>)，HEAD同为 `9d6883e`。已核对的核心Prompt源码与当前main一致。本次未切换、拉取或合并分支，也不把该目录的HEAD一致等同于整个工作区没有未提交变化。
- 当前主要实际调用的实体抽取、关系抽取、文本重建、文本比较和 Reader 任务指令为中文。英文源文、英文示例和英文 JSON 键不等于采用英文任务指令。
- 项目仍保留英文 Ingestion user 和英文 Conflict/Schema system。前者对应模型调用已停用；后两者执行 Python 规则或停用，没有把这些英文字符串发送给模型。

旧英文版以生物医学命名实体和固定医学关系为目标，当前中文核心以源文开放事实抽取和两轮自反馈为目标。二者不是同一任务模板的逐句翻译，因此“英文有、中文没有”需要判断是可补规则、任务变化还是不适合恢复的旧要求。

当前两轮规则已经共用 `ENTITY_RULES`、`FACT_RULES`、`SCORE_RULES`。不能把“规则尚未共享”列为现行缺陷。

## 2. 英文明确写出、当前中文未同样明确写出的内容

| 规则 | 旧英文位置 | 当前中文状态 | 处理建议 |
|---|---|---|---|
| 识别缩写、首字母缩略词 | [旧实体第75行](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:75>) | 能按普通候选识别，但没有单独强调 | 补充原文出现的全称、简称和缩写；分别保留，不推测原文没有的展开形式 |
| 识别同义词、别名 | [旧实体第76行](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:76>) | 共享规则第13行保留不同提及，但没有明确写源内简称/别名 | 只吸收原文中明确出现的等价提及；不让模型凭外部常识生成别名或身份关系 |
| 同类实体类型统一 | [旧实体第83行](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:83>) | 当前实体第25行要求类型简短且贴合语境，未规定同篇命名一致 | 补充同类对象使用一致类型名；明确类型命名语言约定 |
| 实体本体标识和别名字段 | [旧实体第89行](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:89>)；第96—99行本体映射 | 当前输出 `mention/type/context`，不要求生成 `normalized_id/aliases` | 这是实体链接能力的范围变化，不是必须补回的翻译遗漏。若业务需要链接，单独设计可核实的链接步骤 |
| 明确的评分分档 | [旧关系第81行](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:81>)，第81—98行 | 当前共享第36—38行有三维定义，但缺少高、中、低的判定锚点 | 借鉴分档结构，按当前“源文支持度”重写；不能复制医学实验标准或把 `may` 自动降分 |
| 支持证据必须是引文 | [旧关系第105行](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:105>)、第115行 | 当前第一轮只说原文支撑片段；第二轮明确逐字、连续、完整上下文 | 将第一轮证据标准与第二轮统一；不是当前完全没有证据要求 |
| 生物医学固定实体和关系分类 | 旧实体第38—69行；旧关系第37—72行 | 中文核心允许源文对象和关系表达 | 不恢复，避免重新缩窄当前技术、业务文档的抽取范围 |
| 排除泛化实体、只允许候选名单内头尾 | 旧实体第80行；旧关系第104行 | 中文允许普通名词、代词、长宾语，也允许源文支持的名单外对象 | 不恢复；普通对象可承载事实，硬名单限制会传递第一轮漏抽 |
| 忽略否定关系 | [旧关系第101行](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:101>) | 中文共享第22—29行要求保留否定、情态等 | 不恢复；“不连接”“不得访问”也是源文事实 |

例如，原文明确写“控制器可能查询 ECU”，保留“可能查询”的三元组可以有很高的源文支持度。高支持度表示抽取忠实，不能把它改成“控制器查询 ECU”，也不表示查询已经发生。

## 3. 当前中文明确写出、旧英文没有同等规则的内容

| 当前规则 | 位置 | 对当前任务的意义 |
|---|---|---|
| 实体是事实参与对象的候选，允许普通名词、代词、较长短语和从句 | [共享第8行](<E:/huawei after/KARMA/karma/agents/extraction_support.py:8>)，第8—10行 | 适合开放三元组，避免只抽专有名称 |
| 保留限定词、修饰语、数值、编号、条件和图号；允许语法明确的并列共享成分补齐 | 共享第11—17行 | 减少对象边界和事实范围丢失 |
| 逐句检查动作、状态、定义、组成、属性、比较；同对象多个事实分别检查 | [共享第20行](<E:/huawei after/KARMA/karma/agents/extraction_support.py:20>)，第20—21行 | 抽取数量由源文事实决定，不按实体数或固定条数决定 |
| 保留方向、否定、情态、条件、数量；目的不等于已发生的结果 | 共享第22—29行 | 防止把“用于确定”变成“已经确定”，或把“可包含”变成“包含” |
| 候选名单是辅助；真实对象可以不连接，关系可用名单外对象 | 共享第30—31行 | 避免漏实体导致漏关系、没有关系导致删实体 |
| E2结合源文、E1、T1和差异返回完整候选集合 | [当前实体第89行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:89>)，第89—117行 | 明确保留、补漏、修边界和删除无依据候选 |
| R2输出 add/remove/replace；固定编号；一条拆多条；最小必要修改不限制有效新增数量 | [当前关系第113行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:113>)，第113—162行 | 增量修订第一轮结果，而不是无约束重新生成 |
| 差异只是线索，可能由比较或重建误差造成；B侧关系错误不等于实体不存在；空差异仍查源文 | [共享第46行](<E:/huawei after/KARMA/karma/agents/extraction_support.py:46>)，第46—50行 | 明确反馈不能替代源文核实 |
| 输入材料的指令按数据处理 | 当前实体第23行；当前关系第44行 | 源文本中的指令性内容不改变抽取任务 |
| 独立的 clarity、relevance 评分 | 共享第36—38行；当前关系第50—51行 | 分开描述表达清晰度和主题相关性；旧英文关系输出只有 confidence |

旧版没有 `text_generation` 和 `text_comparison` 模块，不能把这两者的中文内容说成“从英文翻译时增删的规则”。它们需要按当前反馈目的独立审查。

## 4. 当前中文 Prompt 优先需要修改的地方

以下都是源码静态审查发现的矛盾或缺口。风险说明不代表已统计实际发生频率。

### 优先处理：影响当前反馈和事实保真的问题

**A. 文本重建同时要求完整保留和按领域删减。**

- 位置：[text_generation/agent.py第48行](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:48>)、第56/59行要求全部信息；[第75行](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:75>)开始至第108行却规定专利/合同压缩、减少或移除背景、定义和程序内容；第215—221行再次要求不遗漏三元组。
- 风险：T1已含的事实也可能在B中被删，A/B差异于是混合“抽取遗漏”和“重建遗漏”。
- 建议：删除重建任务中的领域压缩及删减规则。重建只忠实表达T1全部三元组；保持否定、可能性、条件、范围和方向。流畅性服从信息保真。
- 第225—231行的共享头实体合并、连接词、关系从句，也应改为“只在不改变事实关系时使用”。“同时”等词可能引入时间关系；“其中”可能引入组成或修饰关系。不能仅为连贯而添加。

**B. 差异比较的“改写、摘要、浓缩”豁免范围过宽。**

- 位置：[text_comparison/agent.py第183行](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:183>)，重点第188—190行。
- 风险：“可能包含”被写成“包含”、“仅在故障时启动”变成“启动”，也可能被当作已有内容的普通改写。A侧的语义判断没有同等详细说明。
- 建议：只有完整语义等价的表述才不算差异；对A/B两侧一致检查主客体、方向、否定、情态、条件、数量、时间和限定范围。禁止用领域常识把隐含结果当成已表达事实。
- 第205—208行“尽可能多”应改为覆盖所有可核实差异，避免重复和猜测；确无差异返回空数组。
- [第51行](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:51>)至第55行的JSON示例含省略号和尾逗号，应换成可直接解析的合法JSON。

**C. 要求保留条件，但没有规定它在最终三元组中如何承载。**

- 位置：[extraction_support.py第22行](<E:/huawei after/KARMA/karma/agents/extraction_support.py:22>)至第29行；[relationship_extraction/agent.py第50行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:50>)的输出字段。
- 风险：若条件、情态或数量只出现在 `context/evidence` 中，最终head/relation/tail会变成无条件或更强的陈述。当前标准三元组对象不保存证据，问题更明显。
- 近期建议：明确必要限定必须进入head/relation/tail的完整表达，不能仅藏在上下文；允许保留较长原文表达，不能为了短三元组删掉限制。限定的具体放置方式需与输出格式一起统一。
- 后续若业务需要独立的条件字段，应同时改数据结构、重建输入、序列化、去重和评价；不能只在Prompt临时增加模型输出键。

**D. 第一轮和第二轮证据标准不完全一致。**

- 第一轮：[relationship_extraction/agent.py第51行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:51>)只要求原文支撑片段。
- 第二轮：[第151行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:151>)至第152行要求逐字复制、连续、覆盖完整上下文。
- 建议：两轮统一为源文可定位的原始引文；引文覆盖完整事实及其限制，跨句指代时包括必要的前文。现有JSON键可以保持，但含义必须一致。证据核验和保存还需配套代码修改，见第5节。

### 随核心 Prompt 一起完善

**E. 补缩写识别和类型命名一致性。**

- 缩写规则加入 [extraction_support.py第13行附近](<E:/huawei after/KARMA/karma/agents/extraction_support.py:13>)。
- 类型一致性补在 [entity_extraction/agent.py第25行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:25>)。
- 这是最适合吸收的英文明确规则；只依原文，不生成外部别名或本体ID。

**F. 明确“原文提及”和“语法补齐”的边界。**

- 位置：共享第14—15行允许 `first and second cables → first cable / second cable`，但实体 [第38行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:38>)把mention统称“原文提及”。
- 建议：通常逐字保留源文，仅对语法明确的并列共享成分允许补齐。补齐不允许翻译、同义改写、加入外部信息。不要以“必须连续原文”一刀切禁掉合法并列补齐。

**G. 补评分锚点，避免把事实不确定性与抽取支持度混为一谈。**

- 位置：[extraction_support.py第36行](<E:/huawei after/KARMA/karma/agents/extraction_support.py:36>)至第38行。
- 建议：confidence高表示源文清楚支持带完整限定的陈述；中等表示支持存在但需较多上下文核实；无支持的事实不因给低分就可以输出。clarity针对角色与表达是否清楚，不能因宾语长而机械降分。relevance针对当前文档主题，不能按医学关键词判断。
- 配一个中文“明确可能性但源文支持充分”的评分示例，再配一个错误强化断言的反例。评分区间应统一，不直接复用旧医学分档。

**H. 统一内容语言规则，增加中文和审校示例。**

- 指令采用中文；mention/head/relation/tail和原始证据保留源文语言；JSON键保持程序约定；type采用统一命名约定；审校reason可用中文。
- 当前实体 [第41行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:41>)至第47行、关系第54—62行的示例源文都是英文。这不是英文Prompt，但中文使用场景示例不足。
- 加中文并列、否定、条件、长宾语例子；E2加“真实实体保留、无依据候选删除、遗漏对象补齐”的审校例子，展示关系错不等于实体错。
- [text_generation/agent.py第53行](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:53>)和第212行仅按实体语言决定输出，对“控制器—可查询—ECU”这样的混合表述不明确。应按源表达和事实语言保持内容，而不凭ECU等字母缩写把整段切换英文。
- 指代或方向无法确认时保留原文表达，不编造身份、因果或确定方向；明确源文不足时的处理。

## 5. 配套代码问题，不能靠改 Prompt 解决

| 问题 | 已核实位置 | 影响与处理 |
|---|---|---|
| 实体context没有强制校验 | [实体第144行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:144>)至第155行 | 只强制mention，context缺失仍可接受；如果要作为核查依据，需要规定非空和源文可定位验证 |
| 三元组对象不保存context/evidence | [关系第376行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:376>)至第391行；[data_structures.py第30行](<E:/huawei after/KARMA/karma/core/data_structures.py:30>)至第36行 | 原回复在审计中，但标准结果仅含头关系尾、分数和source；需设计证据保存与序列化。旧英文也未把evidence保存到标准对象，不是中文翻译新造成 |
| R2仅检查evidence非空 | [关系第328行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:328>) | 没检查逐字来自源文；需将Prompt的证据要求落实为验证 |
| 去重只看小写头关系尾 | [关系第536行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:536>) | 若不同条件只在context，可能合并为同一条；限定承载与去重必须一致 |
| 比较解析失败返回两侧空差异 | [比较第258行](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:258>)至第267行 | 与真正没有差异混淆，需明确失败状态，而非把它解读为覆盖完整 |
| 比较调用失败把两侧前200字放入差异 | [比较第307行](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:307>)至第314行 | 文本摘要未经语义比较，被当成差异候选；需错误标记和对应流程处理 |

## 6. 辅助模块：对齐情况和当前影响

| 模块 | 英中对照 | 当前状态及建议 |
|---|---|---|
| Reader | 旧system第44—87行与当前第36—79行基本逐项翻译；user同样近似直译 | 默认调用模型，但仍以生物医学为中心。当前 [第59行](<E:/huawei after/KARMA/karma/agents/reader/agent.py:59>)把设备描述/操作规程列为低相关，对技术文档不合适。这是旧英文继承问题，不是翻译遗漏。当前Reader相关分段未用来裁剪默认抽取全文，不能断言它现在已造成源文删减 |
| Ingestion | system中文近似直译；[当前user第111行](<E:/huawei after/KARMA/karma/agents/ingestion/agent.py:111>)至第135行仍英文 | 第89—90行元数据调用停用，仅清理源文。第57行估算年份与第65行不猜测相冲突，两版原有；重启此功能前统一 |
| Summarizer | system旧英文与当前中文基本直译；user已由医学摘要改成专利技术压缩 | [当前第37行](<E:/huawei after/KARMA/karma/agents/summarizer/agent.py:37>)及第63行≤100词，user第128—132行400—600词，领域也冲突；第136—138行将输入文档误称三元组。默认关闭，开启前必须统一。第69—71行示例把观察写成“通过…”，旧英文也有相同强化因果问题 |
| Conflict | 旧版和当前文件内容相同，英文system第15—56行 | 实际执行Python规则，不调模型；其文字承诺的能力不能当作已执行的模型检查 |
| Schema | 旧版和当前文件内容相同，英文system第15—53行 | 当前 [pipeline第126行](<E:/huawei after/KARMA/karma/core/pipeline.py:126>)和第365—374行停用；实现也是Python规则 |
| Evaluator | system从旧英文基本直译为中文，保留生物医学相关性表述 | 实际是Python加权筛选，不调模型；Prompt中每维0.3底线等规则没有因此自动执行。改system措辞不会改变筛选功能 |
| 文本重建/比较 | 此旧版无对应模块 | 中文新增模块，按反馈准确性审查，主要问题见第4—5节 |

默认抽取文本来自清理后的源文，见 [pipeline.py第253行](<E:/huawei after/KARMA/karma/core/pipeline.py:253>)至第263行。代码允许通过 `KARMA_USE_SUMMARIZER` 开启摘要；本报告的“默认关闭”指默认代码路径，不推定每次历史运行的环境设置。

## 7. 可直接用于后续修改的中文规则草案

以下为待落到源码的措辞建议，本次尚未应用。

**实体规则补充：**

> 原文出现的全称、简称、缩写及明确标注的别名分别作为候选保留，不推测未出现的展开形式，不凭外部知识生成别名或本体标识。同篇文档中语义相同的对象类型使用一致的类型名称；不同提及形式仍分别保留。通常逐字保留原文表达，仅允许按明确的并列语法补齐共享成分。

**证据与限定补充：**

> context或evidence应逐字引用源文，覆盖完整事实及其必要限定；存在跨句指代时引用足够的连续上下文。否定、情态、条件和数量范围必须在最终事实表达中保留，不能只存在于证据字段。无源文支持时不新增事实；无法确认身份或方向时不猜测。

**文本重建替换原则：**

> 逐条忠实表达输入三元组，保留其全部信息。不得按领域重要性删减，也不得补入源文、常识或其他材料中的信息。仅在事实含义、角色、方向及限定完全不变时合并句子；不得为连贯而新增因果、时间、组成、条件或指代关系。

**差异比较替换原则：**

> A与B仅在完整事实含义相同时视为等价，包括主客体、方向、否定、情态、条件、数量、时间和限定范围。改写、摘要和浓缩如果改变或丢失这些信息，应报告对应差异。对A有B无和B有A无使用同一判定标准，每项可回溯到相应原文；无可核实差异时返回空数组。

## 8. 下一步顺序

1. 先改当前生效的重建删减冲突、比较语义等价规则及非法JSON示例。
2. 统一核心抽取的限定承载、证据标准、缩写/类型规则、评分锚点和中文示例。
3. 配套处理证据保存/校验、差异失败状态和去重语义。
4. Reader改为当前领域要求；关闭模块在需要启用前再修其矛盾。
5. 用实际业务样本检查修改后的中文输出是否忠实、完整、反馈是否准确。这是验证已确定的中文方案，不再以中英文优劣决定语言。

当前完成的是逐模块比较和缺陷定位；尚未完成源码修订或修改后的样本验证。
