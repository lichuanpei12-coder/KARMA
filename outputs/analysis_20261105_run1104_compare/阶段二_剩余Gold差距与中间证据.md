# 阶段二：未增长原因——剩余Gold差距与中间证据

分析日期：2026-11-05。运行：run1_5doc_1104_1 与 run1_5doc_1104_3。以用户确认的修改后 Gold 为准，全文采用宽松匹配。本文仅分析结果，不修改程序、Prompt 或 Gold。

关联报告：[阶段一_两次反馈变化_逐句完整对照](阶段一_两次反馈变化_逐句完整对照.md) · [阶段二_剩余Gold差距与中间证据](阶段二_剩余Gold差距与中间证据.md) · [反馈问题总结与修改建议_含三元组证据](反馈问题总结与修改建议_含三元组证据.md)。同名 HTML 提供固定侧边目录与目录搜索。

## 证据范围与评价口径

用户提供每次运行的拆分后三元组、流程最终三元组、文档差异各一份，共六份文本。Gold 为 `10月底数据集修改/DocOIE_transportation_eval_gold.json`，5篇共153条；50个源句均与运行文本对齐。完整输入路径、SHA256、匹配明细、逐句指标与检查结果见 [核对与宽松评估证据.json](核对与宽松评估证据.json)。

“反馈后”附件实际来源是 `_run_manifest.json` 的 `rounds.2`。按用户指定的 d401c9c（11.4 简化prompt）代码，该字段在冲突处理、评分筛选后保存；本文称“最终结果”。因此拆分→最终的变化可评价整个反馈流程的净效果，但不能仅据最终条目反推真实 add/replace/remove 操作，或确定具体由哪个 Agent/后处理删除。缺少实际阶段回复、操作接受/拒绝记录、after_add、after_replace、after_revision（后处理前）和冲突审计。

宽松匹配沿用仓库 `lexical-one-to-one-v1`：各字段小写化后按空白切词，多重集词元重合；三个对应字段均须有交集，才可配对。按配对F1最大化选一对一匹配，P、R分别累计配对P、R后除以预测数、Gold数，最后算F1。它不做词形还原，不以源句编号限制配对；不是“配上即正确”，配对数也不是软指标的TP。指标按整篇匹配、五篇微平均为主，逐句指标只用于定位。

编号说明：B#是附件拆分列表原编号，F#是对应运行最终列表编号，G#是该篇修改Gold从0起的编号。句子之间可能共享来源条目，分句展示会重复出现，整篇评价只计一次。S6/S7等共享条目不能按单句条数相加算贡献。所有指标差值以百分点（pp）表示。

## 未配对数量与原因分类

| 主要诊断 | 1104_1 未配Gold | 1104_3 未配Gold |
|---|---|---|
| Gold重复或边界变体 | 4 | 4 |
| 一对一容量或目标粒度 | 4 | 2 |
| 主体层级及字段边界 | 11 | 11 |
| 主体或指代不对齐 | 3 | 3 |
| 字段内部关系未独立 | 22 | 22 |
| 定义边界或Gold待裁决 | 1 | 1 |
| 并列主体未按Gold分别表达 | 2 | 2 |
| 独立事实被合并或污染 | 13 | 0 |
| 词形与Gold规则冲突 | 4 | 4 |
| 合计 | 64 | 49 |

分类是逐条人工核对后的主要原因，每条只归一类用于计数；主体错误、词形政策和Gold粒度可能同时存在，具体解释保留次要因素。此表不是模型执行日志推断。64/49条未配Gold不等于64/49条完全缺失的源文事实。

## 解释宽松分数时必须区分的现象

1. **未配对**：全篇最优一对一分配没有选中某Gold。可能没有对应事实，也可能候选被另一Gold占用。
2. **已配但不满分**：不在64/49条中，仍有词形、主体、边界或多余限定差距，例如doc3/S7。
3. **弱配对**：词面够配不等于事实正确；源句编号不限制本评估。两次输入doc2/G6与S5/B17得到F1约0.2069的跨句配对；1104_1最终G6仍与S5/F5弱配对（约0.1882），并非风险关系已补齐。1104_3的G6才与本句F15满分配对。
4. **预测更少而P提高**：删除不配对项可改善P，即使该句Gold仍全未覆盖，doc0/S10、doc3/S9都是例子。
5. **目标重复或等价边界**：Gold同一事实多次标注时，预测只出现一次会有未配Gold；是否改目标由用户决定。

## 1104_1：全部未配Gold逐项解释

### 1104_1 doc0/S1：1条未配Gold

> Because such elements and operations are well known in the art, and because they do not facilitate a better understanding of the present disclosure.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | such elements | are well known in | the art | S1 | G0，配对F1=1.0000 |
| F1 | such elements | do not facilitate | a better understanding of the present disclosure | S1 | 未配对 |
| F13 | such operations | are well known in | the art | S1 | G1，配对F1=1.0000 |
| F14 | such operations | do not facilitate | a better understanding of the present disclosure | S1 | 未配对 |

重建文本：

> Such elements and such operations are well known in the art and do not facilitate a better understanding of the present disclosure.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G2：they / do not facilitate / a better understanding of the present disclosure**

- 匹配状态：输入也未配对。
- 主要原因：主体或指代不对齐。Gold以they为主语，当前否定条目以elements/operations为主语，head词元无交集。
- 现有证据：仅作定位的相似片段F1：such elements / do not facilitate / a better understanding of the present disclosure；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：两次均保留4条。Gold对否定关系只用 they 作主语，当前分成 elements/operations 后没有词面重合，G2不配对。语义能否接受指代展开与评分是否配对是两件事。源句只剩 Because 从句，没有给出结果对象，不能按比较中的“隐含结果”补造因果三元组。

### 1104_1 doc0/S2：1条未配Gold

> As the ECUs may include PUF components, the controller may query the ECU to identify which PUF component is compromised, in order to determine where in the sub-system the compromise is located.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F2 | the ECUs | may include | PUF components | S2 | G3，配对F1=1.0000 |
| F3 | the controller | may query the ECU to identify | which PUF component is compromised | S2 | G5，配对F1=1.0000 |
| F4 | the controller | may identify which PUF component is compromised in order to determine | where in the sub-system the compromise is located | S2 | G6，配对F1=0.7692 |

重建文本：

> The ECUs may include PUF components. The controller may query the ECU, may identify which PUF component is compromised, and may determine where in the sub-system the compromise is located.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G4：the controller / may query / the ECU**

- 匹配状态：输入配B3，配对F1=1.0000；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将独立query并入长目的关系；query的独立对象the ECU不再有单独条目。
- 现有证据：本句最接近的可配候选F4：the controller / may identify which PUF component is compromised in order to determine / where in the sub-system the compromise is located；候选配对F1=0.2963。全篇已配给G6。

反馈环节与对比的关系：1104_1把4条变3条：得到 query→identify 的目的表达，却丢失独立 query 条目；末条又以 identify 为目的链起点，与修改Gold要求 query→determine 不同。独立 query 对应G4失配。

### 1104_1 doc0/S7：4条未配Gold

> They may be implemented as instructions stored on a machine-readable medium, which may be read and executed by a computing platform to perform the operations described herein.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F9 | They | may be implemented as | instructions stored on a machine-readable medium | S7 | G17，配对F1=0.7059 |
| F25 | instructions | may be read and executed by a computing platform to perform | the operations described herein | S7 | 未配对 |

重建文本：

> They may be implemented as instructions stored on a machine-readable medium. Instructions may be read by a computing platform and executed by a computing platform. A computing platform performs the operations described herein.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G18：instructions / are stored on / a machine-readable medium**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。instructions stored on...仍在实现条目的tail里，缺独立存储关系。
- 现有证据：仅作定位的相似片段F25：instructions / may be read and executed by a computing platform to perform / the operations described herein；无法配对的零交集字段：relation, tail。这不是有效配对。

**G19：a machine-readable medium / may be read by / a computing platform**

- 匹配状态：输入也未配对。
- 主要原因：主体或指代不对齐。预测以instructions为读取/执行主体，Gold以machine-readable medium为主语；1104_1又将两动作并入长relation。which指代另待裁决。
- 现有证据：仅作定位的相似片段F9：They / may be implemented as / instructions stored on a machine-readable medium；无法配对的零交集字段：head。这不是有效配对。

**G20：a machine-readable medium / may be executed by / a computing platform**

- 匹配状态：输入也未配对。
- 主要原因：主体或指代不对齐。预测以instructions为读取/执行主体，Gold以machine-readable medium为主语；1104_1又将两动作并入长relation。which指代另待裁决。
- 现有证据：仅作定位的相似片段F9：They / may be implemented as / instructions stored on a machine-readable medium；无法配对的零交集字段：head。这不是有效配对。

**G21：a computing platform / is to perform / the operations**

- 匹配状态：输入也未配对。
- 主要原因：独立事实被合并或污染。1104_1将平台目的并入instructions长relation，缺以a computing platform为head的独立目的条目。
- 现有证据：仅作定位的相似片段F25：instructions / may be read and executed by a computing platform to perform / the operations described herein；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：1104_1把读取、执行、平台目的3条压成 instructions / may be read and executed by a computing platform to perform / operations，一条同时承担多个关系，Gold的三个相应主客体不再对齐，独立stored仍埋在tail。

### 1104_1 doc0/S8：1条未配Gold

> While specific exemplary embodiments have been discussed, it should be understood that this is done for illustration purposes only.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F10 | this, while specific exemplary embodiments have been discussed | is done for | illustration purposes only | S8 | 未配对 |

重建文本：

> This is done for illustration purposes only.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G22：this / is done for / illustration purposes**

- 匹配状态：输入配B9，配对F1=0.9231；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1把让步从句并入this主语，原核心条目被背景污染。
- 现有证据：仅作定位的相似片段F10：this, while specific exemplary embodiments have been discussed / is done for / illustration purposes only；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：1104_1将 this 改为 this, while specific exemplary embodiments have been discussed，核心主语附加了整段背景，原本较好的G22配对丢失。这个句首背景不构成要塞入head的实体身份限定。

### 1104_1 doc0/S9：1条未配Gold

> Further, repeated use of the phrase "in one embodiment," or "in an exemplary embodiment," do not necessarily refer to the same embodiment.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F11 | repeated use of the phrase "in one embodiment," or "in an exemplary embodiment," | do not necessarily refer to | the same embodiment | S9 | G24，配对F1=0.8947 |

重建文本：

> Repeated use of the phrase "in one embodiment," and "in an exemplary embodiment," do not necessarily refer to the same embodiment.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G23：repeated use of the phrase "in one embodiment," / do not necessarily refer to / the same embodiment**

- 匹配状态：输入配B10，配对F1=1.0000；最终丢配。
- 主要原因：一对一容量或目标粒度。两个短语原有独立预测合成一个or主语，一个预测最多配一个Gold。
- 现有证据：本句最接近的可配候选F11：repeated use of the phrase "in one embodiment," or "in an exemplary embodiment," / do not necessarily refer to / the same embodiment；候选配对F1=0.8649。全篇已配给G24。

反馈环节与对比的关系：1104_1的重建确实把or写成and；最终将两个原本各配一条Gold的三元组合成一个or长主语，一对一匹配只能覆盖其中一个Gold，G23丢配。

### 1104_1 doc0/S10：6条未配Gold

> This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F12 | This method | may be integrated in a variety of systems including | connected cars, car sharing, rental car services, maintenance and factory services | S10 | 未配对 |

重建文本：

> This method may be integrated in connected cars, car sharing, rental car services, maintenance, and factory services.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G25：this method / may be integrated in / a variety of systems**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F12：This method / may be integrated in a variety of systems including / connected cars, car sharing, rental car services, maintenance and factory services；无法配对的零交集字段：tail。这不是有效配对。

**G26：a variety of systems / include / connected cars**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F12：This method / may be integrated in a variety of systems including / connected cars, car sharing, rental car services, maintenance and factory services；无法配对的零交集字段：head, relation。这不是有效配对。

**G27：a variety of systems / include / car sharing**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F12：This method / may be integrated in a variety of systems including / connected cars, car sharing, rental car services, maintenance and factory services；无法配对的零交集字段：head, relation。这不是有效配对。

**G28：a variety of systems / include / rental car services**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F12：This method / may be integrated in a variety of systems including / connected cars, car sharing, rental car services, maintenance and factory services；无法配对的零交集字段：head, relation。这不是有效配对。

**G29：a variety of systems / include / maintenance**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F12：This method / may be integrated in a variety of systems including / connected cars, car sharing, rental car services, maintenance and factory services；无法配对的零交集字段：head, relation。这不是有效配对。

**G30：a variety of systems / include / factory services**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F12：This method / may be integrated in a variety of systems including / connected cars, car sharing, rental car services, maintenance and factory services；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：1104_1把5条合成一条长relation和列表tail，虽恢复 a variety of systems including 的文字，6条Gold仍全未配对。条数减少可提高全篇P，不能称为本句Gold补齐。

### 1104_1 doc1/S1：1条未配Gold

> A further aspect provides a meaningful capture of the congestion level information enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | A further aspect | provides | a meaningful capture of the congestion level information | S1 | G0，配对F1=1.0000 |
| F12 | a meaningful capture of the congestion level information | enables | appropriate congestion mitigation measures, for example according to the severeness of the congestion | S1 | G1，配对F1=0.6857 |

重建文本：

> A further aspect provides a meaningful capture of the congestion level information, which enables appropriate congestion mitigation measures, for example according to the severeness of the congestion.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G2：congestion mitigation measures / are for example according to / the severeness of the congestion**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F12：a meaningful capture of the congestion level information / enables / appropriate congestion mitigation measures, for example according to the severeness of the congestion；无法配对的零交集字段：relation。这不是有效配对。

反馈环节与对比的关系：两次保留 capture / enables / measures, for example according to severeness 的长tail，G2的措施→严重程度仍未独立。

### 1104_1 doc1/S2：2条未配Gold

> A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F1 | A congestion | may be detected based on said congestion value when | said minimum bandwidth demand exceeds the measured traffic per time over a given time span | S2 | G3，配对F1=0.4444 |

重建文本：

> A congestion may be detected based on said congestion value. A congestion may be detected when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G4：said minimum bandwidth demand / exceeds / the measured traffic per time**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F1：A congestion / may be detected based on said congestion value when / said minimum bandwidth demand exceeds the measured traffic per time over a given time span；无法配对的零交集字段：head, relation。这不是有效配对。

**G5：the measured traffic per time / is over / a given time span**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F1：A congestion / may be detected based on said congestion value when / said minimum bandwidth demand exceeds the measured traffic per time over a given time span；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：两次把两条检测关系压成一条，只是“based on”在relation或tail中的分配不同。Gold的 demand / exceeds / traffic 和 traffic / is over / time span 依然埋在长字段中。

### 1104_1 doc1/S3：1条未配Gold

> The term "part" in connection with the term "network" is to be understood in a broad sense, meaning that part of the network can be any real or imaginary fraction, portion or component of the network.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F2 | The term "part" in connection with the term "network" | is to be understood | in a broad sense | S3 | G6，配对F1=0.9412 |
| F13 | part of the network | can be | any real or imaginary fraction of the network | S3 | G8，配对F1=1.0000 |
| F14 | part of the network | can be | any real or imaginary portion of the network | S3 | G9，配对F1=1.0000 |
| F15 | part of the network | can be | any real or imaginary component of the network | S3 | G10，配对F1=1.0000 |

重建文本：

> The term "part" in connection with the term "network" is to be understood in a broad sense. Part of the network can be any real or imaginary fraction, portion, or component of the network.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G7：the term "part" in connection with the term "network" / means that / part of the network**

- 匹配状态：输入也未配对。
- 主要原因：定义边界或Gold待裁决。Gold将meaning that切出一条并截短对象；当前没有独立定义连接，且means/meaning词形口径需确认。
- 现有证据：仅作定位的相似片段F2：The term "part" in connection with the term "network" / is to be understood / in a broad sense；无法配对的零交集字段：relation, tail。这不是有效配对。

反馈环节与对比的关系：两次4条均保持，三个 fraction/portion/component 对象已按修改Gold拆开；G7 means that / part of the network 没有独立表达。

### 1104_1 doc1/S4：1条未配Gold

> Most eNBs use variants of proportional-fair scheduling, where cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F3 | Most eNBs | use | variants of proportional-fair scheduling | S4 | G11，配对F1=1.0000 |
| F4 | cell capacity | fluctuates depending on | time-variant radio conditions and scheduling assignments | S4 | G12，配对F1=0.8421 |

重建文本：

> Most eNBs use variants of proportional-fair scheduling. Cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G13：cell capacity / fluctuates depending on / scheduling assignments**

- 匹配状态：输入配B21，配对F1=0.7143；最终丢配。
- 主要原因：一对一容量或目标粒度。原两个因素/分类条目被合成一条，已配给另一条Gold，无法再覆盖此Gold。
- 现有证据：本句最接近的可配候选F4：cell capacity / fluctuates depending on / time-variant radio conditions and scheduling assignments；候选配对F1=0.7778。全篇已配给G12。

反馈环节与对比的关系：两个最终结果一致：原两条 cell capacity / fluctuates / depending on具体因素 变为一条 cell capacity / fluctuates depending on / 两个因素and。relation边界更接近Gold，但独立预测数量从2变1，G13失去配对。

### 1104_1 doc1/S5：8条未配Gold

> While the invention has been illustrated and described in detail in the drawings and foregoing description, such illustration and description are to be considered illustrative or exemplary and not restrictive.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F19 | such illustration and description | are to be considered illustrative or exemplary and not restrictive, while | the invention has been illustrated and described in detail in the drawings and foregoing description | S5 | 未配对 |

重建文本：

> Such illustration and description are to be considered illustrative or exemplary and not restrictive. The invention has been illustrated and described in detail in the drawings and the foregoing description.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G14：the invention / has been illustrated in detail in / the drawings**

- 匹配状态：输入配B6，配对F1=0.7000；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：head, relation。这不是有效配对。

**G15：the invention / has been illustrated in detail in / the foregoing description**

- 匹配状态：输入配B23，配对F1=0.7273；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：head, relation。这不是有效配对。

**G16：the invention / has been described in detail in / the drawings**

- 匹配状态：输入配B24，配对F1=0.7000；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：head, relation。这不是有效配对。

**G17：the invention / has been described in detail in / the foregoing description**

- 匹配状态：输入配B25，配对F1=0.7273；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：head, relation。这不是有效配对。

**G18：such illustration / are to be considered / illustrative or exemplary**

- 匹配状态：输入配B5，配对F1=0.9000；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：tail。这不是有效配对。

**G19：such description / are to be considered / illustrative or exemplary**

- 匹配状态：输入也未配对。
- 主要原因：并列主体未按Gold分别表达。illustration and description仍用集合主语；Gold分别给两主体相同评价，一个预测不能覆盖两个Gold。1104_1还整体重合并。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：tail。这不是有效配对。

**G20：such illustration / are to be considered not / restrictive**

- 匹配状态：输入配B22，配对F1=0.7778；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：tail。这不是有效配对。

**G21：such description / are to be considered not / restrictive**

- 匹配状态：输入也未配对。
- 主要原因：并列主体未按Gold分别表达。illustration and description仍用集合主语；Gold分别给两主体相同评价，一个预测不能覆盖两个Gold。1104_1还整体重合并。
- 现有证据：仅作定位的相似片段F19：such illustration and description / are to be considered illustrative or exemplary and not restrictive, while / the invention has been illustrated and described in detail in the drawings and foregoing description；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：1104_1把6条压成一个超长条目，头尾分别装入整段描述；8条Gold全未配对。原来 illustrated/described×drawings/description 的4条可用关系均消失，是主要下降来源。

### 1104_1 doc1/S8：3条未配Gold

> Although specific terms are employed herein, they are used in a generic and descriptive sense only and not for purposes of limitation.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F20 | they | are used in a generic and descriptive sense only and not for purposes of limitation, although | specific terms are employed herein | S8 | 未配对 |

重建文本：

> Specific terms are employed herein; they are used in a generic and descriptive sense only and not for purposes of limitation.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G26：they / are used in / a generic and descriptive sense**

- 匹配状态：输入配B11，配对F1=0.8421；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F20：they / are used in a generic and descriptive sense only and not for purposes of limitation, although / specific terms are employed herein；无法配对的零交集字段：tail。这不是有效配对。

**G27：they / are not for purposes of / limitation**

- 匹配状态：输入配B29，配对F1=0.6667；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F20：they / are used in a generic and descriptive sense only and not for purposes of limitation, although / specific terms are employed herein；无法配对的零交集字段：tail。这不是有效配对。

**G28：specific terms / are employed / herein**

- 匹配状态：输入配B10，配对F1=1.0000；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F20：they / are used in a generic and descriptive sense only and not for purposes of limitation, although / specific terms are employed herein；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：1104_1将 specific terms→employed、they→generic descriptive、they→not limitation 三条合为“they | ...although | specific terms are employed herein”，3条Gold全部失配。

### 1104_1 doc1/S9：3条未配Gold

> This enhances the flexibility of the congestion value, since different operators can use different transformation functions or profiles such that the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | This | enhances the flexibility of the congestion value because | different operators can use different transformation functions or profiles | S9 | 未配对 |
| F9 | different operators | can use | different transformation functions or profiles | S9 | G30，配对F1=1.0000 |
| F10 | the congestion level | may be based | per cell and per link with different feedback profiles depending on the need of an operator | S9 | G31，配对F1=0.7059 |
| F21 | different operators can use different transformation functions or profiles | is such that | the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator | S9 | 未配对 |

重建文本：

> This enhances the flexibility of the congestion value. Different operators can use different transformation functions and different profiles. The congestion level may be based per cell or per link with different feedback profiles depending on the need of an operator.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G29：this / enhances / the flexibility of the congestion value**

- 匹配状态：输入配B12，配对F1=1.0000；最终丢配。
- 主要原因：独立事实被合并或污染。1104_1将原可配对的独立主体/动作/客体并入让步、原因或条件长条目，字段无法再对齐。
- 现有证据：仅作定位的相似片段F8：This / enhances the flexibility of the congestion value because / different operators can use different transformation functions or profiles；无法配对的零交集字段：tail。这不是有效配对。

**G32：the congestion level / may be based / per link with different feedback profiles**

- 匹配状态：输入配B31，配对F1=0.7742；最终丢配。
- 主要原因：一对一容量或目标粒度。原两个因素/分类条目被合成一条，已配给另一条Gold，无法再覆盖此Gold。
- 现有证据：本句最接近的可配候选F10：the congestion level / may be based / per cell and per link with different feedback profiles depending on the need of an operator；候选配对F1=0.7059。全篇已配给G31。

**G33：different feedback profiles / depending on / the need of an operator**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F21：different operators can use different transformation functions or profiles / is such that / the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator；无法配对的零交集字段：relation。这不是有效配对。

反馈环节与对比的关系：1104_1用原文没有的because替换since，并把 This / enhances / flexibility 塞进长relation；cell/link两条也合一，G29与G32丢配。新增such that长条目，depending on仍没独立。

### 1104_1 doc1/S10：2条未配Gold

> This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F11 | This | may lead to | inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting | S10 | G34，配对F1=0.3448 |

重建文本：

> This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and due to the dependence on medium- to long-term congestion situations for reporting.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G35：inaccuracy / is due to / the varying nature of instantaneous traffic patterns**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F11：This / may lead to / inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting；无法配对的零交集字段：head。这不是有效配对。

**G36：inaccuracy / is due to / dependence on medium- to long-term congestion situations**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F11：This / may lead to / inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：1104_1将两个长tail条目合成一条and长tail，1104_3保持原两条。G35、G36两条inaccuracy / is due to / 原因都未独立。

### 1104_1 doc2/S1：2条未配Gold

> Even a small open area can present a danger when loose items are being transported in high-traffic areas.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | a small open area | can present | a danger when loose items are being transported in high-traffic areas | S1 | G0，配对F1=0.6154 |

重建文本：

> A small open area can present a danger when loose items are being transported in high-traffic areas.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G1：a danger / is when / loose items are being transported in high-traffic areas**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F0：a small open area / can present / a danger when loose items are being transported in high-traffic areas；无法配对的零交集字段：relation。这不是有效配对。

**G2：loose items / are being transported in / high-traffic areas**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F0：a small open area / can present / a danger when loose items are being transported in high-traffic areas；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：两次都只有 small open area / can present / danger when...。Gold的 danger→when条件和 loose items→are being transported in 均未配对。

### 1104_1 doc2/S3：1条未配Gold

> Further, the hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F2 | the hazards of loose items flying out of the open-top of cargo trailers | has led | many governing bodies to enact strict laws against such open transport | S3 | G7，配对F1=0.3243 |
| F16 | loose items | fly out of | the open-top of cargo trailers | S3 | 未配对 |

重建文本：

> Loose items fly out of the open-top of cargo trailers. The hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G8：strict laws / is against / such open transport**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F2：the hazards of loose items flying out of the open-top of cargo trailers / has led / many governing bodies to enact strict laws against such open transport；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：1104_1保持 hazards长主语/has led长tail与 loose items/fly out of，既丢风险层级，又把flying改成fly。比较1其实指出了“独立飞出断言”问题，结果没有体现修正。

### 1104_1 doc2/S5：1条未配Gold

> The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not as a limitation.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F5 | The matter set forth in the foregoing description and accompanying drawings | is offered | by way of illustration only | S5 | G6，配对F1=0.1875 |
| F6 | The matter set forth in the foregoing description and accompanying drawings | is not offered | as a limitation | S5 | 未配对 |
| F17 | The matter set forth in the foregoing description | is not offered | as a limitation | S5 | G13，配对F1=0.7500 |
| F18 | The matter set forth in the accompanying drawings | is offered | by way of illustration only | S5 | G12，配对F1=0.7200 |
| F19 | The matter set forth in the accompanying drawings | is not offered | as a limitation | S5 | 未配对 |

重建文本：

> The matter set forth in the foregoing description is offered by way of illustration only and is not offered as a limitation. The matter set forth in the accompanying drawings is offered by way of illustration only and is not offered as a limitation.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G11：the matter set forth / is in / the foregoing description and accompanying drawings**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F18：The matter set forth in the accompanying drawings / is offered / by way of illustration only；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：1104_1新增合并description and drawings的两个head表达，却只替换掉一个旧条目，最终5条，同时保留集合作用与部分作用，存在明显重叠。不是完整清理。

### 1104_1 doc2/S6：2条未配Gold

> The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F7 | The actual scope of the protection sought | is intended to be defined | in the following claims when viewed in their proper perspective based on the prior art | S6 | G14，配对F1=0.6977 |

重建文本：

> The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G15：the following claims / are viewed in / their proper perspective**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F7：The actual scope of the protection sought / is intended to be defined / in the following claims when viewed in their proper perspective based on the prior art；无法配对的零交集字段：relation。这不是有效配对。

**G16：their proper perspective / is based on / the prior art**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F7：The actual scope of the protection sought / is intended to be defined / in the following claims when viewed in their proper perspective based on the prior art；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：两次各保留一条 scope / intended to be defined / claims when viewed...based on...。

### 1104_1 doc2/S7：1条未配Gold

> Preferably, most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | most of these components | are made of | strong materials | S7 | G17，配对F1=1.0000 |
| F20 | most of these components | are to withstand | the conditions of being atop an open cargo area of a vehicle during transportation of goods | S7 | G18，配对F1=0.4444 |

重建文本：

> Most of these components are made of strong materials and are intended to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G19：the conditions / are of being atop / an open cargo area of a vehicle during transportation of goods**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F20：most of these components / are to withstand / the conditions of being atop an open cargo area of a vehicle during transportation of goods；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：1104_1将 are intended to withstand 改为 are to withstand；1104_3改为 to withstand，均去掉原文没有的intended。

### 1104_1 doc2/S8：1条未配Gold

> Later, a series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F9 | a series of bows | was brought into use to keep | the tarpaulin from lying in direct contact with goods in the truck trailer | S8 | G21，配对F1=0.6087 |
| F10 | a series of bows | was brought into use to prevent | water accumulation | S8 | G22，配对F1=0.6667 |

重建文本：

> A series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G20：a series of bows / was brought into / use**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。brought into use被包含在目的relation中，Gold要求独立brought into/use以及不同目的主体边界。
- 现有证据：仅作定位的相似片段F9：a series of bows / was brought into use to keep / the tarpaulin from lying in direct contact with goods in the truck trailer；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：两次保持两个 bows / was brought into use to keep或prevent 条目，均没有独立 bows / was brought into / use。

### 1104_1 doc3/S1：3条未配Gold

> The present invention relates to a rubber composite comprising rubber, oil and a combination of powdered additives, as well as a process for manufacturing same.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | The present invention | relates to | a rubber composite | S1 | G0，配对F1=1.0000 |
| F1 | The present invention | relates to | a process for manufacturing same | S1 | G4，配对F1=1.0000 |
| F14 | a rubber composite | comprising | rubber | S1 | 未配对 |
| F15 | a rubber composite | comprising | oil | S1 | 未配对 |
| F16 | a rubber composite | comprising | a combination of powdered additives | S1 | 未配对 |

重建文本：

> The present invention relates to a rubber composite and a process for manufacturing same. The rubber composite comprises rubber, oil, and a combination of powdered additives.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G1：a rubber composite / comprises / rubber**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。已抽出的组成关系用源句comprising，Gold为comprises；宽松匹配不词形还原，relation零交集。
- 现有证据：仅作定位的相似片段F14：a rubber composite / comprising / rubber；无法配对的零交集字段：relation。这不是有效配对。

**G2：a rubber composite / comprises / oil**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。已抽出的组成关系用源句comprising，Gold为comprises；宽松匹配不词形还原，relation零交集。
- 现有证据：仅作定位的相似片段F15：a rubber composite / comprising / oil；无法配对的零交集字段：relation。这不是有效配对。

**G3：a rubber composite / comprises / a combination of powdered additives**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。已抽出的组成关系用源句comprising，Gold为comprises；宽松匹配不词形还原，relation零交集。
- 现有证据：仅作定位的相似片段F16：a rubber composite / comprising / a combination of powdered additives；无法配对的零交集字段：relation。这不是有效配对。

反馈环节与对比的关系：两次5条原样保留，rubber/oil/additives三条已独立抽出，不能再说缺少组成关系。

### 1104_1 doc3/S2：1条未配Gold

> The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F2 | The incorporation of granulated recycled tire rubber into bitumen | aimed to improve | the mechanical behavior of bituminous mixtures | S2 | G5，配对F1=1.0000 |

重建文本：

> The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G6：granulated recycled tire rubber / is incorporated into / bitumen**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。incorporation名词化内部事实未独立；Gold要求incorporated，按实义词原词形政策能否生成需用户裁决。
- 现有证据：仅作定位的相似片段F2：The incorporation of granulated recycled tire rubber into bitumen / aimed to improve / the mechanical behavior of bituminous mixtures；无法配对的零交集字段：relation, tail。这不是有效配对。

反馈环节与对比的关系：两次仅保留 incorporation... / aimed to improve / behavior。

### 1104_1 doc3/S3：2条未配Gold

> In this connection, the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F3 | the properties of the asphalt bitumen-based binders in high and low temperature conditions | are of | a decisive importance | S3 | G7，配对F1=1.0000 |

重建文本：

> The properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G8：the asphalt bitumen-based binders / are in / high temperature conditions**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F3：the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance；无法配对的零交集字段：tail。这不是有效配对。

**G9：the asphalt bitumen-based binders / are in / low temperature conditions**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F3：the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：两次都只保留 properties of binders in high and low... / are of / decisive importance，主关系与Gold一致。

### 1104_1 doc3/S5：1条未配Gold

> The term oil-dry thus stands to mean that the external surface, namely the out-most layer of the rubber composite, is substantially, or completely, free of oil.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | The term oil-dry | stands to mean that | the external surface is substantially, or completely, free of oil | S5 | G17，配对F1=0.9412 |
| F20 | the external surface | is namely | the out-most layer of the rubber composite | S5 | G18，配对F1=1.0000 |

重建文本：

> The term oil-dry stands to mean that the external surface is substantially, or completely, free of oil. The external surface is namely the out-most layer of the rubber composite.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G19：the external surface / is substantially, or completely, free of / oil**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F20：the external surface / is namely / the out-most layer of the rubber composite；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：两次均只有 oil-dry定义与外表面别名两条。

### 1104_1 doc3/S6：1条未配Gold

> When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle, namely the diameter of an equivalent spherical particle based on the longest dimension of the particle.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F9 | When the particles are of non-spheroid shape, the term | refers to | the average equivalent diameter of the particle | S6 | G21，配对F1=0.7586 |
| F21 | When the particles are of non-spheroid shape, the average equivalent diameter of the particle | is namely | the diameter of an equivalent spherical particle | S6 | G22，配对F1=0.8205 |
| F22 | When the particles are of non-spheroid shape, the diameter of an equivalent spherical particle | is based on | the longest dimension of the particle | S6 | G23，配对F1=0.8205 |

重建文本：

> When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle. The average equivalent diameter of the particle is namely the diameter of an equivalent spherical particle, which is based on the longest dimension of the particle.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G20：the particles / are of / non-spheroid shape**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F9：When the particles are of non-spheroid shape, the term / refers to / the average equivalent diameter of the particle；无法配对的零交集字段：relation, tail。这不是有效配对。

反馈环节与对比的关系：两次均将 When particles... 前缀复制到3个head。Gold三条主体无前缀，另外有 particles / are of / non-spheroid shape。

### 1104_1 doc3/S9：4条未配Gold

> It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even compared with traditional SMA mixtures with highly modified bitumen and fibres.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F12 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres | S9 | 未配对 |

重建文本：

> It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) and traditional SMA mixtures with highly modified bitumen and fibres.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G29：it / is clearly / the lowest value**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。lowest value留在relation中、比较对象留在长tail，Gold要求lowest value核心断言及以它为主体的比较关系。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：tail。这不是有效配对。

**G30：the lowest value / is compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR)**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。lowest value留在relation中、比较对象留在长tail，Gold要求lowest value核心断言及以它为主体的比较关系。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：head。这不是有效配对。

**G31：the lowest value / is even compared with / traditional SMA mixtures with highly modified bitumen and fibres**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。lowest value留在relation中、比较对象留在长tail，Gold要求lowest value核心断言及以它为主体的比较关系。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：head。这不是有效配对。

**G32：traditional SMA mixtures / are with highly modified / bitumen and fibres**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：两次最终都把2条比较合成1条or even长tail。恢复了源句or，却没有抽 lowest value核心断言、以lowest value为主语的两条比较，以及SMA的修饰关系；4条Gold全部未配对。

### 1104_1 doc3/S10：2条未配Gold

> It should be noted that the range is given as such merely for convenience and brevity and should not be construed as an inflexible limitation on the scope of the invention.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F13 | the range | is given as such merely for | convenience and brevity | S10 | G33，配对F1=0.9000 |
| F26 | the range | should not be construed as | an inflexible limitation on the scope of the invention | S10 | G35，配对F1=1.0000 |

重建文本：

> The range is given as such merely for convenience and brevity and should not be construed as an inflexible limitation on the scope of the invention.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G34：the range / is given as such merely for / brevity**

- 匹配状态：输入也未配对。
- 主要原因：一对一容量或目标粒度。convenience and brevity共一个预测，已配给convenience，无法再次配brevity。
- 现有证据：本句最接近的可配候选F13：the range / is given as such merely for / convenience and brevity；候选配对F1=0.9000。全篇已配给G33。

**G36：the range / should not be construed as an inflexible limitation on / the scope of the invention**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。Gold还以另一字段切法再标一次not limitation；一条预测已配G35，不能重复使用。
- 现有证据：本句最接近的可配候选F26：the range / should not be construed as / an inflexible limitation on the scope of the invention；候选配对F1=0.7500。全篇已配给G35。

反馈环节与对比的关系：两次均保留 convenience and brevity 一条，以及 not limitation 一条，未作修改。

### 1104_1 doc4/S3：2条未配Gold

> The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F3 | The selecting unit | is for selecting | at least one of the communication paths for the vehicle according to the evaluation items | S3 | G4，配对F1=0.8649 |
| F12 | the evaluation items | are based on | the item importance information | S2,S3 | G3，配对F1=1.0000 |

重建文本：

> The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items, which are based on the item importance information.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G5：selecting at least one of the communication paths for the vehicle / is according to / the evaluation items**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。according to、of或with连接未独立；其中with目标是否合理需单列Gold审查。
- 现有证据：本句最接近的可配候选F3：The selecting unit / is for selecting / at least one of the communication paths for the vehicle according to the evaluation items；候选配对F1=0.3158。全篇已配给G4。

**G6：the evaluation items / are based on / the item importance information**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。与S2/G3完全相同的based-on事实，当前一个共享来源预测已配G3；非完全没有抽取。
- 现有证据：本句最接近的可配候选F12：the evaluation items / are based on / the item importance information；候选配对F1=1.0000。全篇已配给G3。

反馈环节与对比的关系：两次 selecting unit / is for selecting / paths according to items 的长tail都未缩短，Gold要求 selecting paths / is according to / items 未独立。

### 1104_1 doc4/S7：1条未配Gold

> All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F7 | All of the evaluation items EV of each of the communication paths PH in the third group G3 | is worse than | the standard thresholds E0 | S7 | G12，配对F1=0.6842 |

重建文本：

> All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G13：all of the evaluation items EV / is of / each of the communication paths PH in the third group G3**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。according to、of或with连接未独立；其中with目标是否合理需单列Gold审查。
- 现有证据：本句最接近的可配候选F7：All of the evaluation items EV of each of the communication paths PH in the third group G3 / is worse than / the standard thresholds E0；候选配对F1=0.3636。全篇已配给G12。

反馈环节与对比的关系：两次都保留 All evaluation items of paths in G3 / is worse than / thresholds。

### 1104_1 doc4/S8：1条未配Gold

> In the good category of the available bandwidth, the value of the routing path latency is equal to or lower than 500 kbps.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | the value of the routing path latency | in the good category of the available bandwidth, is equal to or lower than | 500 kbps | S8 | G14，配对F1=0.7895 |

重建文本：

> The value of the routing path latency in the good category of the available bandwidth is equal to or lower than 500 kbps.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G15：the value of the routing path latency / is equal to or lower than 500 kbps in / the good category of the available bandwidth**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。同一阈值在Gold中分别以数值和分类两种边界给出，单条预测只可配一次。
- 现有证据：仅作定位的相似片段F8：the value of the routing path latency / in the good category of the available bandwidth, is equal to or lower than / 500 kbps；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：两次同一条阈值条目保留，限定放在relation前部，与Gold第一条有配对。

### 1104_1 doc4/S9：2条未配Gold

> It is intended that the specification and examples be considered as exemplary only, with a true scope of the disclosure being indicated by the following claims and their equivalents.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F9 | the specification | is intended to be considered as | exemplary only | S9 | 未配对 |
| F10 | a true scope of the disclosure | is indicated by | the following claims and their equivalents | S9 | G18，配对F1=0.6667 |
| F15 | examples | are intended to be considered as | exemplary only | S9 | G16，配对F1=0.5882 |

重建文本：

> The specification and examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims and their equivalents.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G17：the specification and examples / are considered as exemplary only with / a true scope of the disclosure**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。according to、of或with连接未独立；其中with目标是否合理需单列Gold审查。
- 现有证据：仅作定位的相似片段F9：the specification / is intended to be considered as / exemplary only；无法配对的零交集字段：tail。这不是有效配对。

**G19：the disclosure / is being indicated by / their equivalents**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。预测主体scope且claims/equivalents同放tail；Gold主体disclosure并拆对象，属于主体、粒度及Gold指代争议。
- 现有证据：本句最接近的可配候选F10：a true scope of the disclosure / is indicated by / the following claims and their equivalents；候选配对F1=0.6087。全篇已配给G18。

反馈环节与对比的关系：两次均保留specification、examples分别表达的两条及scope→claims/equivalents条目，没有重演旧运行把它们全部合成一条的现象。

### 1104_1 doc4/S10：1条未配Gold

> In the good category of the routing path latency, the value of the routing path latency is equal to or lower than 50 ms.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F11 | the value of the routing path latency | in the good category of the routing path latency, is equal to or lower than | 50 ms | S10 | G20，配对F1=0.7692 |

重建文本：

> The value of the routing path latency in the good category of the routing path latency is equal to or lower than 50 ms.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G21：the value of the routing path latency / is equal to or lower than 50 ms in / the good category of the routing path latency**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。同一阈值在Gold中分别以数值和分类两种边界给出，单条预测只可配一次。
- 现有证据：仅作定位的相似片段F11：the value of the routing path latency / in the good category of the routing path latency, is equal to or lower than / 50 ms；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：两次都保留50 ms且分类仍在relation，主阈值事实没有被破坏。

## 1104_3：全部未配Gold逐项解释

### 1104_3 doc0/S1：1条未配Gold

> Because such elements and operations are well known in the art, and because they do not facilitate a better understanding of the present disclosure.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | such elements | are well known in | the art | S1 | G0，配对F1=1.0000 |
| F1 | such elements | do not facilitate | a better understanding of the present disclosure | S1 | 未配对 |
| F12 | such operations | are well known in | the art | S1 | G1，配对F1=1.0000 |
| F13 | such operations | do not facilitate | a better understanding of the present disclosure | S1 | 未配对 |

重建文本：

> Such elements and such operations are well known in the art and do not facilitate a better understanding of the present disclosure.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G2：they / do not facilitate / a better understanding of the present disclosure**

- 匹配状态：输入也未配对。
- 主要原因：主体或指代不对齐。Gold以they为主语，当前否定条目以elements/operations为主语，head词元无交集。
- 现有证据：仅作定位的相似片段F1：such elements / do not facilitate / a better understanding of the present disclosure；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：比较两次都强调 Because 丢失；这没有指出 Gold 的 they 主语口径，也不能提供一个源文未出现的因果结果。此处没有发生可见的负面改动。

### 1104_3 doc0/S7：3条未配Gold

> They may be implemented as instructions stored on a machine-readable medium, which may be read and executed by a computing platform to perform the operations described herein.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | They | may be implemented as | instructions stored on a machine-readable medium | S7 | G17，配对F1=0.7059 |
| F27 | instructions | may be read by | a computing platform | S6,S7 | 未配对 |
| F28 | instructions | may be executed by | a computing platform | S6,S7 | 未配对 |
| F29 | a computing platform | may read and execute the instructions to perform | the operations described herein | S7 | G21，配对F1=0.6087 |

重建文本：

> They may be implemented as instructions stored on a machine-readable medium. Instructions may be read and executed by a computing platform. A computing platform performs the operations described herein.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G18：instructions / are stored on / a machine-readable medium**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。instructions stored on...仍在实现条目的tail里，缺独立存储关系。
- 现有证据：仅作定位的相似片段F27：instructions / may be read by / a computing platform；无法配对的零交集字段：relation。这不是有效配对。

**G19：a machine-readable medium / may be read by / a computing platform**

- 匹配状态：输入也未配对。
- 主要原因：主体或指代不对齐。预测以instructions为读取/执行主体，Gold以machine-readable medium为主语；1104_1又将两动作并入长relation。which指代另待裁决。
- 现有证据：仅作定位的相似片段F27：instructions / may be read by / a computing platform；无法配对的零交集字段：head。这不是有效配对。

**G20：a machine-readable medium / may be executed by / a computing platform**

- 匹配状态：输入也未配对。
- 主要原因：主体或指代不对齐。预测以instructions为读取/执行主体，Gold以machine-readable medium为主语；1104_1又将两动作并入长relation。which指代另待裁决。
- 现有证据：仅作定位的相似片段F28：instructions / may be executed by / a computing platform；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：1104_3保留读取/执行两条，并将平台条目改为 platform / may read and execute the instructions to perform / operations；恢复目的后G21得到配对，但may/read/execute与instructions再度塞进relation，仍非Gold的 is to perform。两个读取条目的主体instructions与Gold的machine-readable medium不同，需用户裁决which指代，不能自动认定模型或Gold正确。

### 1104_3 doc0/S10：6条未配Gold

> This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F11 | This method | may be integrated in | connected cars | S10 | 未配对 |
| F31 | This method | may be integrated in | car sharing | S10 | 未配对 |
| F32 | This method | may be integrated in | rental car services | S10 | 未配对 |
| F33 | This method | may be integrated in | maintenance | S10 | 未配对 |
| F34 | This method | may be integrated in | factory services | S10 | 未配对 |

重建文本：

> This method may be integrated in connected cars, car sharing, rental car services, maintenance, and factory services.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G25：this method / may be integrated in / a variety of systems**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F11：This method / may be integrated in / connected cars；无法配对的零交集字段：tail。这不是有效配对。

**G26：a variety of systems / include / connected cars**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F11：This method / may be integrated in / connected cars；无法配对的零交集字段：head, relation。这不是有效配对。

**G27：a variety of systems / include / car sharing**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F31：This method / may be integrated in / car sharing；无法配对的零交集字段：head, relation。这不是有效配对。

**G28：a variety of systems / include / rental car services**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F32：This method / may be integrated in / rental car services；无法配对的零交集字段：head, relation。这不是有效配对。

**G29：a variety of systems / include / maintenance**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F33：This method / may be integrated in / maintenance；无法配对的零交集字段：head, relation。这不是有效配对。

**G30：a variety of systems / include / factory services**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。缺method→a variety of systems的中间层及systems→成员的5条；已有method→成员不具备对应head/relation/tail。include/including政策待决。
- 现有证据：仅作定位的相似片段F34：This method / may be integrated in / factory services；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：1104_3保留原5条 method→具体系统，也仍全未配对。两次比较都发现中间层systems缺失，但结果没有重建 Gold 的 method→a variety of systems 以及 systems→五个成员。including与Gold include存在词形规则冲突，列入待决。

### 1104_3 doc1/S1：1条未配Gold

> A further aspect provides a meaningful capture of the congestion level information enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | A further aspect | provides | a meaningful capture of the congestion level information | S1 | G0，配对F1=1.0000 |
| F16 | a meaningful capture of the congestion level information | enables | appropriate congestion mitigation measures, for example according to the severeness of the congestion | S1 | G1，配对F1=0.6857 |

重建文本：

> A further aspect provides a meaningful capture of the congestion level information. A meaningful capture of the congestion level information enables appropriate congestion mitigation measures, for example according to the severeness of the congestion.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G2：congestion mitigation measures / are for example according to / the severeness of the congestion**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F16：a meaningful capture of the congestion level information / enables / appropriate congestion mitigation measures, for example according to the severeness of the congestion；无法配对的零交集字段：relation。这不是有效配对。

反馈环节与对比的关系：重建文本完整覆盖原句，因此两次差异都为空。这种空差异是文本层面的结果，Replace仍应从长字段识别关系，不能由Add按完全遗漏补一份又让长字段保持不变。

### 1104_3 doc1/S2：2条未配Gold

> A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F1 | A congestion | may be detected | based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span | S2 | G3，配对F1=0.4444 |

重建文本：

> A congestion may be detected based on said congestion value, and may be detected when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G4：said minimum bandwidth demand / exceeds / the measured traffic per time**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F1：A congestion / may be detected / based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span；无法配对的零交集字段：head, relation。这不是有效配对。

**G5：the measured traffic per time / is over / a given time span**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F1：A congestion / may be detected / based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：比较认为两条表达将联合条件变成两个独立条件，提示有语义依据，但不能推导成只保留一个长三元组。字段边界和条件语义需同时处理；本句全篇指标可能因条数减少而微升，不等于遗漏已修复。

### 1104_3 doc1/S3：1条未配Gold

> The term "part" in connection with the term "network" is to be understood in a broad sense, meaning that part of the network can be any real or imaginary fraction, portion or component of the network.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F2 | The term "part" in connection with the term "network" | is to be understood | in a broad sense | S3 | G6，配对F1=0.9412 |
| F17 | part of the network | can be | any real or imaginary fraction of the network | S3 | G8，配对F1=1.0000 |
| F18 | part of the network | can be | any real or imaginary portion of the network | S3 | G9，配对F1=1.0000 |
| F19 | part of the network | can be | any real or imaginary component of the network | S3 | G10，配对F1=1.0000 |

重建文本：

> The term "part" in connection with the term "network" is to be understood in a broad sense. Part of the network can be any real or imaginary fraction of the network, any real or imaginary portion of the network, or any real or imaginary component of the network.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G7：the term "part" in connection with the term "network" / means that / part of the network**

- 匹配状态：输入也未配对。
- 主要原因：定义边界或Gold待裁决。Gold将meaning that切出一条并截短对象；当前没有独立定义连接，且means/meaning词形口径需确认。
- 现有证据：仅作定位的相似片段F2：The term "part" in connection with the term "network" / is to be understood / in a broad sense；无法配对的零交集字段：relation, tail。这不是有效配对。

反馈环节与对比的关系：两次比较为空，因为文字已足够重建。Gold将meaning that单独切出且对象截在 part of the network，是否是可接受独立事实需用户确认；同时meaning→means与实义词原形要求相冲突，不能盲目照搬至Prompt。

### 1104_3 doc1/S4：1条未配Gold

> Most eNBs use variants of proportional-fair scheduling, where cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F3 | Most eNBs | use | variants of proportional-fair scheduling | S4 | G11，配对F1=1.0000 |
| F4 | cell capacity | fluctuates depending on | time-variant radio conditions and scheduling assignments | S4 | G12，配对F1=0.8421 |

重建文本：

> Most eNBs use variants of proportional-fair scheduling. Cell capacity fluctuates depending on time-variant radio conditions and depending on scheduling assignments.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G13：cell capacity / fluctuates depending on / scheduling assignments**

- 匹配状态：输入配B21，配对F1=0.7143；最终丢配。
- 主要原因：一对一容量或目标粒度。原两个因素/分类条目被合成一条，已配给另一条Gold，无法再覆盖此Gold。
- 现有证据：本句最接近的可配候选F4：cell capacity / fluctuates depending on / time-variant radio conditions and scheduling assignments；候选配对F1=0.7778。全篇已配给G12。

反馈环节与对比的关系：两次比较都为空，可见问题不只由错误差异驱动：反馈或后续处理也会自主过度合并。应同时保留两个独立因素条目，只修relation/tail边界。

### 1104_3 doc1/S5：2条未配Gold

> While the invention has been illustrated and described in detail in the drawings and foregoing description, such illustration and description are to be considered illustrative or exemplary and not restrictive.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F5 | such illustration and description | are to be considered | illustrative or exemplary | S5 | G18，配对F1=0.9000 |
| F6 | the invention | has been illustrated | in detail in the drawings | S5 | G14，配对F1=0.7000 |
| F20 | such illustration and description | are to be considered | not restrictive | S5 | G20，配对F1=0.7778 |
| F21 | the invention | has been illustrated | in detail in the foregoing description | S5 | G15，配对F1=0.7273 |
| F22 | the invention | has been described | in detail in the drawings | S5 | G16，配对F1=0.7000 |
| F23 | the invention | has been described | in detail in the foregoing description | S5 | G17，配对F1=0.7273 |
| F32 | the invention has been illustrated and described in detail in the drawings and foregoing description | while | such illustration and description are to be considered illustrative or exemplary and not restrictive | S5 | 未配对 |

重建文本：

> Such illustration and description are to be considered illustrative or exemplary and not restrictive. The invention has been illustrated in detail in the drawings and in the foregoing description, and has been described in detail in the drawings and in the foregoing description.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G19：such description / are to be considered / illustrative or exemplary**

- 匹配状态：输入也未配对。
- 主要原因：并列主体未按Gold分别表达。illustration and description仍用集合主语；Gold分别给两主体相同评价，一个预测不能覆盖两个Gold。1104_1还整体重合并。
- 现有证据：本句最接近的可配候选F5：such illustration and description / are to be considered / illustrative or exemplary；候选配对F1=0.9000。全篇已配给G18。

**G21：such description / are to be considered not / restrictive**

- 匹配状态：输入也未配对。
- 主要原因：并列主体未按Gold分别表达。illustration and description仍用集合主语；Gold分别给两主体相同评价，一个预测不能覆盖两个Gold。1104_1还整体重合并。
- 现有证据：本句最接近的可配候选F20：such illustration and description / are to be considered / not restrictive；候选配对F1=0.7778。全篇已配给G20。

反馈环节与对比的关系：1104_3保留原6条又加“整句 | while | 整句”，原illustration/description未按Gold拆成两个主语，新增让步条目也不属于Gold目标。两次比较都报告While丢失；这种话语连接被当作目标关系，比独立主体/动作覆盖得到更多关注。

### 1104_3 doc1/S9：1条未配Gold

> This enhances the flexibility of the congestion value, since different operators can use different transformation functions or profiles such that the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F12 | This | enhances | the flexibility of the congestion value | S9 | G29，配对F1=1.0000 |
| F13 | different operators | can use | different transformation functions or profiles | S9 | G30，配对F1=1.0000 |
| F14 | the congestion level | may be based | per cell with different feedback profiles depending on the need of an operator | S9 | G31，配对F1=0.7742 |
| F28 | the congestion level | may be based | per link with different feedback profiles depending on the need of an operator | S9 | G32，配对F1=0.7742 |
| F30 | the flexibility of the congestion value | is enhanced because | different operators can use different transformation functions or profiles | S9 | 未配对 |
| F31 | different operators can use different transformation functions or profiles | such that | the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator | S9 | 未配对 |

重建文本：

> This enhances the flexibility of the congestion value. Different operators can use different transformation functions and different profiles. The congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G33：different feedback profiles / depending on / the need of an operator**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F31：different operators can use different transformation functions or profiles / such that / the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator；无法配对的零交集字段：relation。这不是有效配对。

反馈环节与对比的关系：1104_3保留 This→enhances，functions/profiles合成or，修复了选择范围；但又新增 is enhanced because（enhanced词形和because均非原文）及整句such that连接。没有出现causes不代表实义词和核心连接词约束已满足。源句确有since因果，比较此处不是凭空发明因果；问题在反馈的用词和目标关系选择。

### 1104_3 doc1/S10：2条未配Gold

> This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F15 | This | may lead to | inaccuracy due to the varying nature of instantaneous traffic patterns | S10 | G34，配对F1=0.5263 |
| F29 | This | may lead to | inaccuracy due to the dependence on medium- to long-term congestion situations for reporting | S10 | 未配对 |

重建文本：

> This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and due to the dependence on medium- to long-term congestion situations for reporting.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G35：inaccuracy / is due to / the varying nature of instantaneous traffic patterns**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F15：This / may lead to / inaccuracy due to the varying nature of instantaneous traffic patterns；无法配对的零交集字段：head。这不是有效配对。

**G36：inaccuracy / is due to / dependence on medium- to long-term congestion situations**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。目标关系仍包含在长tail中，没有对应的独立主体和关系字段。
- 现有证据：仅作定位的相似片段F29：This / may lead to / inaccuracy due to the dependence on medium- to long-term congestion situations for reporting；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：两次重建完整复述句子且差异为空，Replace未体现逐字段关系检查。第一种合并可能减少冗余条数但仍未补Gold关系；第二种保留也不是已解决。

### 1104_3 doc2/S1：2条未配Gold

> Even a small open area can present a danger when loose items are being transported in high-traffic areas.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | a small open area | can present | a danger when loose items are being transported in high-traffic areas | S1 | G0，配对F1=0.6154 |

重建文本：

> A small open area can present a danger when loose items are being transported in high-traffic areas.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G1：a danger / is when / loose items are being transported in high-traffic areas**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F0：a small open area / can present / a danger when loose items are being transported in high-traffic areas；无法配对的零交集字段：relation。这不是有效配对。

**G2：loose items / are being transported in / high-traffic areas**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F0：a small open area / can present / a danger when loose items are being transported in high-traffic areas；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：比较1只指出Even省略；比较3为空。应从源句中的when和被动动作识别内部关系，同时保留其处于危险条件的语义，不把运输条件错误扩成无条件事实。

### 1104_3 doc2/S3：1条未配Gold

> Further, the hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F2 | the hazards | has led | many governing bodies to enact strict laws against such open transport | S3 | G7，配对F1=0.4615 |
| F15 | the hazards | is of loose items flying out of | the open-top of cargo trailers | S3 | G6，配对F1=1.0000 |

重建文本：

> The hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport. Loose items fly out of the open-top of cargo trailers.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G8：strict laws / is against / such open transport**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F2：the hazards / has led / many governing bodies to enact strict laws against such open transport；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：1104_3将错误飞出条目改为 hazards / is of loose items flying out of / open-top...，与G6完全一致；外层head也缩为hazards。G7的 has led many governing bodies to enact 与G8的 laws→against 仍在长tail中。比较3反而为空，说明空差异不等于反馈没有自主修正能力。

### 1104_3 doc2/S5：1条未配Gold

> The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not as a limitation.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F5 | The matter set forth in the foregoing description | is offered | by way of illustration only | S5 | G12，配对F1=0.7200 |
| F16 | The matter set forth in the foregoing description | is not offered | as a limitation | S5 | G13，配对F1=0.7500 |
| F17 | The matter set forth in the accompanying drawings | is offered | by way of illustration only | S5 | 未配对 |
| F18 | The matter set forth in the accompanying drawings | is not offered | as a limitation | S5 | 未配对 |

重建文本：

> The matter set forth in the foregoing description is offered by way of illustration only and is not offered as a limitation. The matter set forth in the accompanying drawings is offered by way of illustration only and is not offered as a limitation.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G11：the matter set forth / is in / the foregoing description and accompanying drawings**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F5：The matter set forth in the foregoing description / is offered / by way of illustration only；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：1104_3原4条不变。两次都未补 the matter set forth / is in / description and drawings，也没统一Gold的核心主体边界。对比都为空，需Replace处理长head，Remove只能在独有事实已保住时删。

### 1104_3 doc2/S6：2条未配Gold

> The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F6 | The actual scope of the protection sought | is intended to be defined | in the following claims when viewed in their proper perspective based on the prior art | S6 | G14，配对F1=0.6977 |

重建文本：

> The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G15：the following claims / are viewed in / their proper perspective**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F6：The actual scope of the protection sought / is intended to be defined / in the following claims when viewed in their proper perspective based on the prior art；无法配对的零交集字段：relation。这不是有效配对。

**G16：their proper perspective / is based on / the prior art**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F6：The actual scope of the protection sought / is intended to be defined / in the following claims when viewed in their proper perspective based on the prior art；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：G15 claims→viewed in→perspective、G16 perspective→based on→prior art 均未配对；重建直接复现整句，对比为空。当前样本没有多条重复scope条目，之前“doc2/S6重复”的现象不适用于这份输入。

### 1104_3 doc2/S7：1条未配Gold

> Preferably, most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F7 | most of these components | are made of | strong materials | S7 | G17，配对F1=1.0000 |
| F19 | most of these components | to withstand | the conditions of being atop an open cargo area of a vehicle during transportation of goods | S7 | G18，配对F1=0.4571 |

重建文本：

> Most of these components are made of strong materials and are intended to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G19：the conditions / are of being atop / an open cargo area of a vehicle during transportation of goods**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。when条件、运输、法规against、matter位置、viewed/based、conditions归属等仍在长字段，没有独立条目。
- 现有证据：仅作定位的相似片段F19：most of these components / to withstand / the conditions of being atop an open cargo area of a vehicle during transportation of goods；无法配对的零交集字段：head, relation。这不是有效配对。

反馈环节与对比的关系：Gold主体含 most of these components made of strong materials，现主体仍过短；conditions→are of being atop 未独立。比较对intended的新增意图定位有效；Preferably省略不应抢占主要修改目标。

### 1104_3 doc2/S8：1条未配Gold

> Later, a series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | a series of bows | was brought into use to keep | the tarpaulin from lying in direct contact with goods in the truck trailer | S8 | G21，配对F1=0.6087 |
| F9 | a series of bows | was brought into use to prevent | water accumulation | S8 | G22，配对F1=0.6667 |

重建文本：

> A series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G20：a series of bows / was brought into / use**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。brought into use被包含在目的relation中，Gold要求独立brought into/use以及不同目的主体边界。
- 现有证据：仅作定位的相似片段F8：a series of bows / was brought into use to keep / the tarpaulin from lying in direct contact with goods in the truck trailer；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：Gold将 brought into use 放在两个目的关系的主体中，当前放在relation里，导致边界差异和预测数不足。比较1关注Later省略，比较3为空，均没提示Gold独立层级。Later可能有时间语义，是否保留需有明确上下文依据，不应一概删全部背景词。

### 1104_3 doc3/S1：3条未配Gold

> The present invention relates to a rubber composite comprising rubber, oil and a combination of powdered additives, as well as a process for manufacturing same.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F0 | The present invention | relates to | a rubber composite | S1 | G0，配对F1=1.0000 |
| F1 | The present invention | relates to | a process for manufacturing same | S1 | G4，配对F1=1.0000 |
| F14 | a rubber composite | comprising | rubber | S1 | 未配对 |
| F15 | a rubber composite | comprising | oil | S1 | 未配对 |
| F16 | a rubber composite | comprising | a combination of powdered additives | S1 | 未配对 |

重建文本：

> The present invention relates to a rubber composite and a process for manufacturing same. The rubber composite comprises rubber, oil, and a combination of powdered additives.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G1：a rubber composite / comprises / rubber**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。已抽出的组成关系用源句comprising，Gold为comprises；宽松匹配不词形还原，relation零交集。
- 现有证据：仅作定位的相似片段F14：a rubber composite / comprising / rubber；无法配对的零交集字段：relation。这不是有效配对。

**G2：a rubber composite / comprises / oil**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。已抽出的组成关系用源句comprising，Gold为comprises；宽松匹配不词形还原，relation零交集。
- 现有证据：仅作定位的相似片段F15：a rubber composite / comprising / oil；无法配对的零交集字段：relation。这不是有效配对。

**G3：a rubber composite / comprises / a combination of powdered additives**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。已抽出的组成关系用源句comprising，Gold为comprises；宽松匹配不词形还原，relation零交集。
- 现有证据：仅作定位的相似片段F16：a rubber composite / comprising / a combination of powdered additives；无法配对的零交集字段：relation。这不是有效配对。

反馈环节与对比的关系：源句comprising、预测comprising，Gold为comprises；现宽松匹配只按空白词元重合，不做词形还原，三个relation零交集，所以均未配对。需用户决定Gold或词形政策，不应为得分擅自要求改词。

### 1104_3 doc3/S2：1条未配Gold

> The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F2 | The incorporation of granulated recycled tire rubber into bitumen | aimed to improve | the mechanical behavior of bituminous mixtures | S2 | G5，配对F1=1.0000 |

重建文本：

> The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G6：granulated recycled tire rubber / is incorporated into / bitumen**

- 匹配状态：输入也未配对。
- 主要原因：词形与Gold规则冲突。incorporation名词化内部事实未独立；Gold要求incorporated，按实义词原词形政策能否生成需用户裁决。
- 现有证据：仅作定位的相似片段F2：The incorporation of granulated recycled tire rubber into bitumen / aimed to improve / the mechanical behavior of bituminous mixtures；无法配对的零交集字段：relation, tail。这不是有效配对。

反馈环节与对比的关系：Gold要求 granulated recycled tire rubber / is incorporated into / bitumen，内部事实仍藏在名词化head；但原句只有incorporation，没有incorporated，直接补Gold会触及原词形政策，作为待决项单列。对比为空只能说明复述文字足够。

### 1104_3 doc3/S3：2条未配Gold

> In this connection, the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F3 | the properties of the asphalt bitumen-based binders in high and low temperature conditions | are of | a decisive importance | S3 | G7，配对F1=1.0000 |

重建文本：

> The properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G8：the asphalt bitumen-based binders / are in / high temperature conditions**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F3：the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance；无法配对的零交集字段：tail。这不是有效配对。

**G9：the asphalt bitumen-based binders / are in / low temperature conditions**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F3：the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：Gold另外要求 binders→are in→high/low conditions 两条，当前没有独立条目。对比为空。是否将条件独立后仍完整限定主关系，需在Replace中同时检查。

### 1104_3 doc3/S5：1条未配Gold

> The term oil-dry thus stands to mean that the external surface, namely the out-most layer of the rubber composite, is substantially, or completely, free of oil.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | The term oil-dry | stands to mean that | the external surface is substantially, or completely, free of oil | S5 | G17，配对F1=0.9412 |
| F20 | the external surface | is namely | the out-most layer of the rubber composite | S5 | G18，配对F1=1.0000 |

重建文本：

> The term oil-dry stands to mean that the external surface, which is namely the out-most layer of the rubber composite, is substantially, or completely, free of oil.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G19：the external surface / is substantially, or completely, free of / oil**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F20：the external surface / is namely / the out-most layer of the rubber composite；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：Gold的 external surface / is substantially, or completely, free of / oil 未独立，是典型定义tail中关系漏拆；对比为空不能当作结构完成。

### 1104_3 doc3/S6：1条未配Gold

> When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle, namely the diameter of an equivalent spherical particle based on the longest dimension of the particle.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F9 | When the particles are of non-spheroid shape, the term | refers to | the average equivalent diameter of the particle | S6 | G21，配对F1=0.7586 |
| F21 | When the particles are of non-spheroid shape, the average equivalent diameter of the particle | is namely | the diameter of an equivalent spherical particle | S6 | G22，配对F1=0.8205 |
| F22 | When the particles are of non-spheroid shape, the diameter of an equivalent spherical particle | is based on | the longest dimension of the particle | S6 | G23，配对F1=0.8205 |

重建文本：

> When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle. The average equivalent diameter is namely the diameter of an equivalent spherical particle, and the diameter of an equivalent spherical particle is based on the longest dimension of the particle.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G20：the particles / are of / non-spheroid shape**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F9：When the particles are of non-spheroid shape, the term / refers to / the average equivalent diameter of the particle；无法配对的零交集字段：relation, tail。这不是有效配对。

反馈环节与对比的关系：当前既没有独立条件事实，又有主语冗长导致的宽松折损。把条件从head拿走后仍要保留其限定范围，不能为了Gold丢掉when的成立条件。对比为空。

### 1104_3 doc3/S9：4条未配Gold

> It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even compared with traditional SMA mixtures with highly modified bitumen and fibres.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F12 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres | S9 | 未配对 |

重建文本：

> It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) and traditional SMA mixtures with highly modified bitumen and fibres.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G29：it / is clearly / the lowest value**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。lowest value留在relation中、比较对象留在长tail，Gold要求lowest value核心断言及以它为主体的比较关系。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：tail。这不是有效配对。

**G30：the lowest value / is compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR)**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。lowest value留在relation中、比较对象留在长tail，Gold要求lowest value核心断言及以它为主体的比较关系。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：head。这不是有效配对。

**G31：the lowest value / is even compared with / traditional SMA mixtures with highly modified bitumen and fibres**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。lowest value留在relation中、比较对象留在长tail，Gold要求lowest value核心断言及以它为主体的比较关系。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：head。这不是有效配对。

**G32：traditional SMA mixtures / are with highly modified / bitumen and fibres**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。位置条件、free of、when条件或SMA修饰关系未形成独立三元组。
- 现有证据：仅作定位的相似片段F12：It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres；无法配对的零交集字段：head。这不是有效配对。

反馈环节与对比的关系：宽松全篇P可能仅因删除一条不配对预测而升高，属于条数效应，不是Gold覆盖改善。对比两次都发现and替代or，是重建错误与三元组结构问题并存的例子。

### 1104_3 doc3/S10：2条未配Gold

> It should be noted that the range is given as such merely for convenience and brevity and should not be construed as an inflexible limitation on the scope of the invention.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F13 | the range | is given as such merely for | convenience and brevity | S10 | G33，配对F1=0.9000 |
| F26 | the range | should not be construed as | an inflexible limitation on the scope of the invention | S10 | G35，配对F1=1.0000 |

重建文本：

> The range is given as such merely for convenience and brevity, and should not be construed as an inflexible limitation on the scope of the invention.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G34：the range / is given as such merely for / brevity**

- 匹配状态：输入也未配对。
- 主要原因：一对一容量或目标粒度。convenience and brevity共一个预测，已配给convenience，无法再次配brevity。
- 现有证据：本句最接近的可配候选F13：the range / is given as such merely for / convenience and brevity；候选配对F1=0.9000。全篇已配给G33。

**G36：the range / should not be construed as an inflexible limitation on / the scope of the invention**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。Gold还以另一字段切法再标一次not limitation；一条预测已配G35，不能重复使用。
- 现有证据：本句最接近的可配候选F26：the range / should not be construed as / an inflexible limitation on the scope of the invention；候选配对F1=0.7500。全篇已配给G35。

反馈环节与对比的关系：Gold将convenience/brevity拆成两条，且又用两种边界写出not limitation，4条Gold竞争2条预测，G34与G36未配对。第一个是并列粒度差异，第二个更像Gold重复/边界口径，需用户决定是否保留两种目标，不能统一称为新增两个源文事实。

### 1104_3 doc4/S3：2条未配Gold

> The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F3 | The selecting unit | is for selecting | at least one of the communication paths for the vehicle according to the evaluation items | S3 | G4，配对F1=0.8649 |
| F12 | the evaluation items | are based on | the item importance information | S2,S3 | G3，配对F1=1.0000 |

重建文本：

> The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items, which are based on the item importance information.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G5：selecting at least one of the communication paths for the vehicle / is according to / the evaluation items**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。according to、of或with连接未独立；其中with目标是否合理需单列Gold审查。
- 现有证据：本句最接近的可配候选F3：The selecting unit / is for selecting / at least one of the communication paths for the vehicle according to the evaluation items；候选配对F1=0.3158。全篇已配给G4。

**G6：the evaluation items / are based on / the item importance information**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。与S2/G3完全相同的based-on事实，当前一个共享来源预测已配G3；非完全没有抽取。
- 现有证据：本句最接近的可配候选F12：the evaluation items / are based on / the item importance information；候选配对F1=1.0000。全篇已配给G3。

反馈环节与对比的关系：另一个未配对G6与S2的G3完全相同，当前共享条目已配给G3，不能说模型完全没抽based-on。按句单独评分会让同一预测重复计分，因此主报告保持全篇评价。

### 1104_3 doc4/S7：1条未配Gold

> All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F7 | All of the evaluation items EV of each of the communication paths PH in the third group G3 | is worse than | the standard thresholds E0 | S7 | G12，配对F1=0.6842 |

重建文本：

> All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.

对比提示：两侧均为 `[]`，文本层面没有报告差异。

**G13：all of the evaluation items EV / is of / each of the communication paths PH in the third group G3**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。according to、of或with连接未独立；其中with目标是否合理需单列Gold审查。
- 现有证据：本句最接近的可配候选F7：All of the evaluation items EV of each of the communication paths PH in the third group G3 / is worse than / the standard thresholds E0；候选配对F1=0.3636。全篇已配给G12。

反馈环节与对比的关系：Gold另有 evaluation items / is of / paths in G3，当前未独立；对比为空，因为整句可直接重建。主语缩短与内部归属同时处理，不能只新增再让长主语保持原样。

### 1104_3 doc4/S8：1条未配Gold

> In the good category of the available bandwidth, the value of the routing path latency is equal to or lower than 500 kbps.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F8 | the value of the routing path latency | in the good category of the available bandwidth, is equal to or lower than | 500 kbps | S8 | G14，配对F1=0.7895 |

重建文本：

> The value of the routing path latency in the good category of the available bandwidth is equal to or lower than 500 kbps.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G15：the value of the routing path latency / is equal to or lower than 500 kbps in / the good category of the available bandwidth**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。同一阈值在Gold中分别以数值和分类两种边界给出，单条预测只可配一次。
- 现有证据：仅作定位的相似片段F8：the value of the routing path latency / in the good category of the available bandwidth, is equal to or lower than / 500 kbps；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：Gold还要求阈值/分类关系的另一种切法，单条预测不能同时配两条，因此G15未配对。源文kbps与latency组合虽可疑，Gold同样如此；应由用户决定是否纠正数据，模型不能凭领域常识改数字或单位。比较3列纯语序变化而自认无事实差异。

### 1104_3 doc4/S9：2条未配Gold

> It is intended that the specification and examples be considered as exemplary only, with a true scope of the disclosure being indicated by the following claims and their equivalents.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F9 | the specification | is intended to be considered as | exemplary only | S9 | 未配对 |
| F10 | a true scope of the disclosure | is indicated by | the following claims and their equivalents | S9 | G18，配对F1=0.6667 |
| F15 | examples | are intended to be considered as | exemplary only | S9 | G16，配对F1=0.5882 |

重建文本：

> The specification and examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims and their equivalents.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G17：the specification and examples / are considered as exemplary only with / a true scope of the disclosure**

- 匹配状态：输入也未配对。
- 主要原因：字段内部关系未独立。according to、of或with连接未独立；其中with目标是否合理需单列Gold审查。
- 现有证据：仅作定位的相似片段F9：the specification / is intended to be considered as / exemplary only；无法配对的零交集字段：tail。这不是有效配对。

**G19：the disclosure / is being indicated by / their equivalents**

- 匹配状态：输入也未配对。
- 主要原因：主体层级及字段边界。预测主体scope且claims/equivalents同放tail；Gold主体disclosure并拆对象，属于主体、粒度及Gold指代争议。
- 现有证据：本句最接近的可配候选F10：a true scope of the disclosure / is indicated by / the following claims and their equivalents；候选配对F1=0.6087。全篇已配给G18。

反馈环节与对比的关系：当前Gold包含集合主语、with范围连接、以disclosure为主语的indicated by及拆分claims/equivalents。模型结果与其不完全一致；源句直接被指明的是a true scope，Gold却用disclosure，单列待用户决策。比较把intended that改成 intended to也说成丢语气，部分是等价改写噪声。

### 1104_3 doc4/S10：1条未配Gold

> In the good category of the routing path latency, the value of the routing path latency is equal to or lower than 50 ms.

当前本句预测：

| 编号 | head | relation | tail | 来源 | 整篇配对 |
|---|---|---|---|---|---|
| F11 | the value of the routing path latency | in the good category of the routing path latency, is equal to or lower than | 50 ms | S10 | G20，配对F1=0.7692 |

重建文本：

> The value of the routing path latency in the good category of the routing path latency is equal to or lower than 50 ms.

对比提示：完整A/B差异见阶段一同句；下列为该句诊断。

**G21：the value of the routing path latency / is equal to or lower than 50 ms in / the good category of the routing path latency**

- 匹配状态：输入也未配对。
- 主要原因：Gold重复或边界变体。同一阈值在Gold中分别以数值和分类两种边界给出，单条预测只可配一次。
- 现有证据：仅作定位的相似片段F11：the value of the routing path latency / in the good category of the routing path latency, is equal to or lower than / 50 ms；无法配对的零交集字段：tail。这不是有效配对。

反馈环节与对比的关系：Gold另一条将分类放到tail的表达没有独立预测，G21未配对。比较1为空，比较3仅报告语序变化；两者均不能直接指导是否需要双重Gold条目。

## 两次都已配对、但仍明显偏离Gold的重点

| 位置 | 问题 | 为何未出现在未配Gold列表 |
|---|---|---|
| doc0/S3 | 长head/tail反复包含make up，两个components条目重叠，Gold还有vlidation拼写 | 有词元重合可软配，不代表层级清楚 |
| doc0/S4 | 能力恢复但定义tail继续扩长；data in字段边界不一致 | 各项仍可软配 |
| doc1/S7 | at least one of选择列表拆3条，Gold只1条 | 一条可配，其他预测损P |
| doc2/S7 | withstand主体缺made of strong materials，conditions未独立 | 目的条目仍可软配，条件条目另属未配 |
| doc3/S4 | external surface / is / outmost surface of particles的边界 | 仍有三个字段交集 |
| doc3/S7 | grinding the rubber与Gold的a pre-step of grinding the rubber；to a desired size边界 | 目标有配对但非满分 |
| doc3/S8 | Gold为all the possible individual numerical values，预测没有all the possible | 软配可选但R折损 |
| doc4/S5 | Gold belongs外层head包含located短语，预测为shaded area | 软配但head覆盖下降 |
| doc4/S9 | scope与disclosure、集合主体与单体、claims与equivalents粒度 | 部分可配不等于全部目标满足 |

## 全部最终未配预测条目

这些条目在主评价中未被选中；不能一律称为错误或重复。可能是Gold未标、粒度不同、词形冲突或词面错位。

### 1104_1 未配预测

| 位置 | 来源 | head | relation | tail |
|---|---|---|---|---|
| doc0/F1 | S1 | such elements | do not facilitate | a better understanding of the present disclosure |
| doc0/F8 | S6 | Embodiments of the invention | may also be implemented in | hardware |
| doc0/F10 | S8 | this, while specific exemplary embodiments have been discussed | is done for | illustration purposes only |
| doc0/F12 | S10 | This method | may be integrated in a variety of systems including | connected cars, car sharing, rental car services, maintenance and factory services |
| doc0/F14 | S1 | such operations | do not facilitate | a better understanding of the present disclosure |
| doc0/F17 | S3 | any of the components of the vehicle | make up | the vehicle |
| doc0/F22 | S6 | Embodiments of the invention | may also be implemented in | firmware |
| doc0/F23 | S6 | Embodiments of the invention | may also be implemented in | software |
| doc0/F25 | S7 | instructions | may be read and executed by a computing platform to perform | the operations described herein |
| doc1/F7 | S7 | said transformation function | amends at least one of | a number of congestion levels |
| doc1/F8 | S9 | This | enhances the flexibility of the congestion value because | different operators can use different transformation functions or profiles |
| doc1/F18 | S7 | said transformation function | amends at least one of | a shape of a congestion level curve |
| doc1/F19 | S5 | such illustration and description | are to be considered illustrative or exemplary and not restrictive, while | the invention has been illustrated and described in detail in the drawings and foregoing description |
| doc1/F20 | S8 | they | are used in a generic and descriptive sense only and not for purposes of limitation, although | specific terms are employed herein |
| doc1/F21 | S9 | different operators can use different transformation functions or profiles | is such that | the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator |
| doc2/F6 | S5 | The matter set forth in the foregoing description and accompanying drawings | is not offered | as a limitation |
| doc2/F12 | S10 | A first set of left pulleys | are attached at | the front |
| doc2/F13 | S10 | a second set of left pulleys | are attached at | the rear of the cargo hold |
| doc2/F16 | S3 | loose items | fly out of | the open-top of cargo trailers |
| doc2/F19 | S5 | The matter set forth in the accompanying drawings | is not offered | as a limitation |
| doc2/F21 | S10 | A first set of right pulleys | are attached at | the front |
| doc2/F22 | S10 | a second set of right pulleys | are attached at | the rear of the cargo hold |
| doc3/F12 | S9 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres |
| doc3/F14 | S1 | a rubber composite | comprising | rubber |
| doc3/F15 | S1 | a rubber composite | comprising | oil |
| doc3/F16 | S1 | a rubber composite | comprising | a combination of powdered additives |
| doc4/F9 | S9 | the specification | is intended to be considered as | exemplary only |

### 1104_3 未配预测

| 位置 | 来源 | head | relation | tail |
|---|---|---|---|---|
| doc0/F1 | S1 | such elements | do not facilitate | a better understanding of the present disclosure |
| doc0/F7 | S6 | Embodiments of the invention | may also be implemented in | hardware |
| doc0/F11 | S10 | This method | may be integrated in | connected cars |
| doc0/F13 | S1 | such operations | do not facilitate | a better understanding of the present disclosure |
| doc0/F14 | S2 | the controller | may identify | which PUF component is compromised |
| doc0/F15 | S2 | the controller | may determine | where in the sub-system the compromise is located |
| doc0/F18 | S3 | any of the components that make up the vehicle | make up | the vehicle |
| doc0/F22 | S5 | all technical equivalents | operate in | a similar manner |
| doc0/F24 | S6 | Embodiments of the invention | may also be implemented in | firmware |
| doc0/F25 | S6 | Embodiments of the invention | may also be implemented in | software |
| doc0/F27 | S6,S7 | instructions | may be read by | a computing platform |
| doc0/F28 | S6,S7 | instructions | may be executed by | a computing platform |
| doc0/F31 | S10 | This method | may be integrated in | car sharing |
| doc0/F32 | S10 | This method | may be integrated in | rental car services |
| doc0/F33 | S10 | This method | may be integrated in | maintenance |
| doc0/F34 | S10 | This method | may be integrated in | factory services |
| doc1/F9 | S7 | said transformation function | amends at least one of | a number of congestion levels |
| doc1/F26 | S7 | said transformation function | amends at least one of | a shape of a congestion level curve |
| doc1/F29 | S10 | This | may lead to | inaccuracy due to the dependence on medium- to long-term congestion situations for reporting |
| doc1/F30 | S9 | the flexibility of the congestion value | is enhanced because | different operators can use different transformation functions or profiles |
| doc1/F31 | S9 | different operators can use different transformation functions or profiles | such that | the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator |
| doc1/F32 | S5 | the invention has been illustrated and described in detail in the drawings and foregoing description | while | such illustration and description are to be considered illustrative or exemplary and not restrictive |
| doc1/F33 | S8 | specific terms are employed herein | although | they are used in a generic and descriptive sense only and not for purposes of limitation |
| doc2/F17 | S5 | The matter set forth in the accompanying drawings | is offered | by way of illustration only |
| doc2/F18 | S5 | The matter set forth in the accompanying drawings | is not offered | as a limitation |
| doc3/F12 | S9 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even traditional SMA mixtures with highly modified bitumen and fibres |
| doc3/F14 | S1 | a rubber composite | comprising | rubber |
| doc3/F15 | S1 | a rubber composite | comprising | oil |
| doc3/F16 | S1 | a rubber composite | comprising | a combination of powdered additives |
| doc4/F9 | S9 | the specification | is intended to be considered as | exemplary only |
