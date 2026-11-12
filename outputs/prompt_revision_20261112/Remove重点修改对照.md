# Remove 重点修改对照

2026-11-12。本稿只列本轮修改，左栏为开始本轮实施时的工作区内容，右栏为当前实际代码。此前移除 evidence 等修改已包含在左栏。代码尚未提交 Git。

## 先看这四项

| 重点 | 当前实现 | 源码 |
| --- | --- | --- |
| 当次解决重复和冗余 | Remove 同时返回 replace、remove；每项替换形成一条保留表达，两个数组按同一输入编号整组执行 | [删除与替换执行](../../karma/agents/feedback_operations.py#L54) |
| 两个独立排名 | 全部三元组对各出现一次，分别记录整体重合排名和包含排名，零重合项同样保留 | [词重合计算](../../karma/core/triple_overlap.py#L6) |
| 限定词归属 | 回查限定词修饰哪个对象或关系，再确定当前条目的完整表达 | [Remove Prompt](../../karma/agents/feedback_remove/agent.py#L9) |
| 工作站示例 | 将 all/any 两条位置关系统一成 the workstations，外层检查范围和发送者范围保留 | [完整 Prompt](../../karma/agents/feedback_remove/RemoveAgent_完整Prompt.md) |

## 词重合与评估的关系

两者均使用 lower().split() 分词及 Counter 词频计数，保留重复词次数。这里合并 head、relation、tail 后两两比较；评估则在对应字段中计数，再将预测结果与 Gold 一对一配对。当前算法保留原标点形式，沿用评估的空白分词口径。

两条词数为 A、B，共有词数为 C：整体重合 F1=2C/(A+B)，左包含率=C/A，右包含率=C/B。整体排名按 F1 降序，包含排名按两侧包含率的较大值降序；同分同排名。空分母对应分数0。表格按编号排列，两个排名字段表达各自的检查优先级。模型重点检查任一排名靠前的条目对，随后检查其余条目。

每次 Remove 及返修调用前，用最新集合重新计算；basis_version、条目编号均与该次 current_collection 对齐。排序用于安排检查顺序，删除和替换依据源句中的事实、角色与限定归属。

## 职责

karma/agents/feedback_remove/agent.py：原第 4—7 行，现 [4—6 行](../../karma/agents/feedback_remove/agent.py#L4)。

| 左栏 · 本轮修改前 | 右栏 · 当前实际内容 |
| --- | --- |
| <pre>你负责依据源句自主查找重复三元组，选择保留项并删除完整重复项。<br>结合当前完整集合比较事实及必要限定；文本差异和前序提示用于帮助定位问题。<br>删除后，原条目的全部事实与必要限定应由保留项表达；不同事实保留，部分重叠交给 replace 调整。<br>输出 remove 和 handoff 两个数组，具体步骤与格式见本次任务说明。</pre> | <pre>你负责依据源句处理当前三元组中的重复和冗余。<br>发现重复或冗余时，依据源句确定应保留的完整表达，在本次处理中完成必要的替换和删除。<br>输出 replace、remove、handoff，具体步骤与格式见本次任务说明。</pre> |

## 执行步骤

karma/agents/feedback_remove/agent.py：原第 9—22 行，现 [8—25 行](../../karma/agents/feedback_remove/agent.py#L8)。

| 左栏 · 本轮修改前 | 右栏 · 当前实际内容 |
| --- | --- |
| <pre># 阶段一：核对并确定问题<br>1. 阅读源句与当前完整集合，自主查找表达同一事实的条目。<br>2. 比较主体、关系、客体，以及否定、可能性、条件、数量、时间和范围。<br>3. 回查文本差异和收到的 handoff 提示，依据源句区分完整重复、部分重叠和不同事实。<br><br># 阶段二：生成本阶段操作<br>1. 对完整重复选择保留项：优先保留主体、关系、原文用词及必要限定正确的条目；同样正确且等价时保留编号较小的一条。<br>2. 为每项删除填写 index、keep_index、reason，说明重复依据和保留理由。<br>3. 保留不同事实。部分重叠或两条都需要修正时交给 replace；依据不足时保留当前结果并记录 review。<br><br># 阶段三：复核并输出<br>1. 确认待删除条目的全部事实与必要限定均由保留项表达，保留仍含独有内容的条目。<br>2. 确认每个 keep_index 指向本轮最终保留的条目。<br>3. 输出 remove、handoff。收到的问题为空时，仍独立检查完整集合。</pre> | <pre># 阶段一：确定问题<br>1. 阅读源句和当前集合，了解每条关系表达的事实。<br>2. lexical_overlap.pairs 列出当前集合的全部三元组对。重点检查 overall_rank 或 containment_rank 靠前的条目对，随后检查其余条目；每对条目形成一次完整判断。<br>   overlap_f1 表示整体词重合程度，left_containment、right_containment 分别表示左、右条目的词被另一条包含的比例。overall_rank 按整体重合程度排名，containment_rank 按两侧较高的包含率排名，同分同排名。<br>   数值由程序提供，用于安排检查顺序。结合原条目核对主体、关系方向、字段归属，以及 left_only_words、right_only_words 列出的不同词。<br>3. 比较两条的主体、关系、客体及必要限定。遇到数量、条件、范围等限定时，回查源句，确定限定词修饰哪个对象或关系，再判断当前两条表达的是同一事实还是不同事实。<br>4. 遇到词包含关系时，分别确定外层关系和字段内部关系，保留各项独立事实。<br>5. 结合文本差异和收到的 handoff 核实问题在当前集合中的位置。<br><br># 阶段二：确定保留表达并处理<br>1. 依据源句确定应保留的主体、关系、客体和必要限定；限定属于其他关系时，在对应关系中保留其范围。<br>2. 表达同一事实的条目选择一项保留，必要时替换为统一的完整表达，并删除重复项；同样正确且等价时保留编号较小的一条。<br>3. 字段部分重叠时，直接调整需要修改的字段，并保留各项独立关系。<br>4. 依据尚待核实的条目保留当前表达，在 handoff 中记录 review 及待核实内容。<br><br># 阶段三：整理输出<br>1. index 和 keep_index 均使用本次输入编号。keep_index 指向本轮保留的条目，也可以指向本轮替换后的保留项。<br>2. 将同一条目的修改合为一次操作，为每项操作填写具体理由，输出 replace、remove、handoff。</pre> |

## 输出协议

karma/agents/feedback_remove/agent.py：原第 24—28 行，现 [27—33 行](../../karma/agents/feedback_remove/agent.py#L27)。

| 左栏 · 本轮修改前 | 右栏 · 当前实际内容 |
| --- | --- |
| <pre># 输出格式<br>返回 JSON 对象，包含 remove、handoff 两个数组；无内容的数组写 []。<br>remove 每项写 index、keep_index、reason；reason 简述重复依据与保留理由。<br>handoff 每项写 target、source_sentence_ids、indices、problem：target 指处理阶段；indices 填当前相关条目编号，缺少条目时填 []；problem 简述具体位置与问题。<br>target 使用 add、replace、remove、text_generation、text_comparison 或 review；源句与三元组正确而重建文本或对比判断有误时，分别记录 text_generation 或 text_comparison。</pre> | <pre># 输出格式<br>返回 JSON 对象，包含 replace、remove、handoff 三个数组；空数组写 []。<br>replace 每项写 index、reason、new_triples；new_triples 包含一条完整三元组，字段为 head、relation、tail、source_sentence_ids，用它替换原 index 的条目。<br>remove 每项写 index、keep_index、reason；reason 说明重复依据与保留理由。<br>每个输入 index 对应一次替换或删除；保留项与删除项使用各自的编号。程序将本次替换和删除作为一组执行。<br>handoff 每项写 target、source_sentence_ids、indices、problem；indices 填当前相关编号，缺少对应条目填 []，problem 说明具体问题。<br>target 使用 add、replace、remove、text_generation、text_comparison 或 review；当前重复和冗余问题由本 Agent 在 replace、remove 中处理。</pre> |

## 新增的工作站示例

来源：[karma/agents/feedback_remove/agent.py 第 35 行](../../karma/agents/feedback_remove/agent.py#L35)。此示例为改写构造，使用实验室工作站场景与不同句式。

| 左栏 · 本轮修改前 | 右栏 · 当前实际内容 |
| --- | --- |
| <pre>此前没有该示例。</pre> | <pre>输入：{&quot;source_sentences&quot;:[{&quot;sentence_id&quot;:&quot;S1&quot;,&quot;text&quot;:&quot;The supervisor inspects all of the workstations located in the lab and records messages sent by any of the workstations located in the lab.&quot;}],&quot;current_collection&quot;:{&quot;triples&quot;:[{&quot;index&quot;:0,&quot;head&quot;:&quot;all of the workstations&quot;,&quot;relation&quot;:&quot;are located in&quot;,&quot;tail&quot;:&quot;the lab&quot;,&quot;source_sentence_ids&quot;:[&quot;S1&quot;]},{&quot;index&quot;:1,&quot;head&quot;:&quot;any of the workstations&quot;,&quot;relation&quot;:&quot;are located in&quot;,&quot;tail&quot;:&quot;the lab&quot;,&quot;source_sentence_ids&quot;:[&quot;S1&quot;]},{&quot;index&quot;:2,&quot;head&quot;:&quot;The supervisor&quot;,&quot;relation&quot;:&quot;inspects&quot;,&quot;tail&quot;:&quot;all of the workstations located in the lab&quot;,&quot;source_sentence_ids&quot;:[&quot;S1&quot;]},{&quot;index&quot;:3,&quot;head&quot;:&quot;The supervisor&quot;,&quot;relation&quot;:&quot;records&quot;,&quot;tail&quot;:&quot;messages sent by any of the workstations located in the lab&quot;,&quot;source_sentence_ids&quot;:[&quot;S1&quot;]},{&quot;index&quot;:4,&quot;head&quot;:&quot;messages&quot;,&quot;relation&quot;:&quot;are sent by&quot;,&quot;tail&quot;:&quot;any of the workstations located in the lab&quot;,&quot;source_sentence_ids&quot;:[&quot;S1&quot;]}]}}<br>输出：{&quot;replace&quot;:[{&quot;index&quot;:0,&quot;reason&quot;:&quot;两条位置关系指向同一组工作站，统一为 the workstations。all 表达检查范围，any 表达发送者范围，分别保留在第2条和第3、4条。&quot;,&quot;new_triples&quot;:[{&quot;head&quot;:&quot;the workstations&quot;,&quot;relation&quot;:&quot;are located in&quot;,&quot;tail&quot;:&quot;the lab&quot;,&quot;source_sentence_ids&quot;:[&quot;S1&quot;]}]}],&quot;remove&quot;:[{&quot;index&quot;:1,&quot;keep_index&quot;:0,&quot;reason&quot;:&quot;第1条的位置关系由替换后的第0条表达。&quot;}],&quot;handoff&quot;:[]}</pre> |

## 同时更新的原有示例

完整重复例输出增加空 replace 数组。长字段重叠例改为由 Remove 直接替换外层字段并保留内部独立关系。

## 执行与校验

replace 和 remove 共用当前输入编号。keep_index 可指向本轮替换后的保留项。同一条目被同时替换和删除、保留项也被删除、来源编号无效等情况会使整组操作回滚。日志按实际操作记录 replace/remove，并保留它们发生在 Remove 阶段的信息。兼容旧回复省略 replace 数组。

106 项离线测试通过；10 个当前反馈示例通过格式和操作执行校验。已同步 Prompt Markdown、HTML、JSON、总览和来源行号。未调用在线模型，实际重复识别率和误删变化仍需后续运行评估。
