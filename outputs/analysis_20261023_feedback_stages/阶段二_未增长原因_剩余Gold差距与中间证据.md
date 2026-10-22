# 阶段二：反馈未带来增长的剩余问题与中间证据

对象：run1_5doc_1022。日期：2026-10-23。效果判断只以当前146条Gold为准。阶段一已单独展示反馈下降；本文检查反馈之后仍有哪些差距，以及重建和对比为何没有推动修复。

## 结论与范围

- 可从当前附件精确恢复的反馈后SPO为20条，全部141条中的其余121条只提供了自然语言重建。本文不会把重建文字重新抽成三元组并当作本轮实际输出。
- 6个源句可用实际SPO直接确认剩余差距：doc0/S7、S9，doc4/S7—S10。其中部分是第一阶段已说明的反馈退化，部分是反馈前已有、后续只补来源而未修复的问题。
- 对50个源句核对Gold行数与已有条目数后，19句的相关预测数少于本句Gold数。它说明本句一对一关系覆盖存在数量压力，不等于确认漏了19个事实，更不等于全文未匹配Gold清单。
- 重建主要检查文字内容是否完整，通常不能展示实际SPO边界。一个长条目能重建完整句子，仍可能对应多个Gold；因此比较为空也可能留下较大Gold差距。
- 当前反馈prompt明确将“内容已在长字段，仅缺独立表达”归为拆分问题。按这一职责划分，很多独立Gold差距不会由反馈补充；不能一边要求它跳过漏拆，一边期待反馈解决全部此类Gold差距。
- 对运行时究竟使用哪版prompt、某一条原SPO是否已含有关词、全文最终匹配了哪个Gold，没有原始文件时保留待核查结论。

## 能直接确认的重点

### doc0/S7：来源修好了，关系还没对上

Gold要求medium读取/执行关系和platform的目的关系；反馈只给以instructions为主体的三条旧SPO补来源。说明本轮至少有“把定位问题处理完，未继续检查Gold对应关系”的现象。模型输入没有Gold，which指代和目的表达的选择也可能与Gold不同。

### doc0/S9：有源文依据的额外关系不在Gold中

两个may refer条目已存在且只补来源，当前Gold未标这两条。按源文支持程度检查会选择保留，但Gold的P不会因补来源改善。两条负向关系的does/do也影响严格匹配。

### doc4/S7—S10：修订后仍有字段差距和关系数量不足

S7一部分关系修好了，另一部分被加长；S8/S10各只剩一条预测对应两个Gold；S9分别指向claims/equivalents的关系被合写。来源定位修好后，这些SPO问题仍然存在。

## 50句检查清单

“相关条目数”在已确认情况下补计原UNASSIGNED条目，并计入已发生增删；doc3/S7的#14仅根据同篇未定位重建人工关联，实际SPO尚未知。doc4#12在S2/S3同时出现，故全表行数不能简单相加当全文预测数。

| 文档/源句 | Gold行数 | 当前相关条目数 | 检查结果 |
| --- | ---: | ---: | --- |
| doc0/S1 | 3 | 6 | 未发现足以定性的证据；不等于全部正确 |
| doc0/S2 | 4 | 4 | 字段/关系组织候选，需原SPO核实 |
| doc0/S3 | 4 | 4 | 字段/关系组织候选，需原SPO核实 |
| doc0/S4 | 4 | 3 | 本句预测数不足，需原SPO定位缺项 |
| doc0/S5 | 2 | 3 | 字段/关系组织候选，需原SPO核实 |
| doc0/S6 | 1 | 4 | 字段/关系组织候选，需原SPO核实 |
| doc0/S7 | 4 | 5 | 实际SPO确认有差距 |
| doc0/S8 | 1 | 1 | 未发现足以定性的证据；不等于全部正确 |
| doc0/S9 | 2 | 4 | 实际SPO确认有差距 |
| doc0/S10 | 6 | 5 | 本句预测数不足，需原SPO定位缺项 |
| doc1/S1 | 3 | 3 | 未发现足以定性的证据；不等于全部正确 |
| doc1/S2 | 3 | 1 | 本句预测数不足，需原SPO定位缺项 |
| doc1/S3 | 4 | 4 | 字段/关系组织候选，需原SPO核实 |
| doc1/S4 | 2 | 3 | 未发现足以定性的证据；不等于全部正确 |
| doc1/S5 | 4 | 8 | 未发现足以定性的证据；不等于全部正确 |
| doc1/S6 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc1/S7 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc1/S8 | 3 | 3 | 未发现足以定性的证据；不等于全部正确 |
| doc1/S9 | 4 | 4 | 字段/关系组织候选，需原SPO核实 |
| doc1/S10 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc2/S1 | 3 | 1 | 本句预测数不足，需原SPO定位缺项 |
| doc2/S2 | 3 | 4 | 未发现足以定性的证据；不等于全部正确 |
| doc2/S3 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc2/S4 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc2/S5 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc2/S6 | 3 | 3 | 字段/关系组织候选，需原SPO核实 |
| doc2/S7 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc2/S8 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc2/S9 | 1 | 1 | 未发现足以定性的证据；不等于全部正确 |
| doc2/S10 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc3/S1 | 5 | 5 | 未发现足以定性的证据；不等于全部正确 |
| doc3/S2 | 2 | 1 | 本句预测数不足，需原SPO定位缺项 |
| doc3/S3 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc3/S4 | 7 | 7 | 未发现足以定性的证据；不等于全部正确 |
| doc3/S5 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc3/S6 | 4 | 3 | 本句预测数不足，需原SPO定位缺项 |
| doc3/S7 | 3 | 2 | 本句预测数不足，需原SPO定位缺项 |
| doc3/S8 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc3/S9 | 4 | 3 | 本句预测数不足，需原SPO定位缺项 |
| doc3/S10 | 4 | 3 | 本句预测数不足，需原SPO定位缺项 |
| doc4/S1 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc4/S2 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc4/S3 | 3 | 3 | 未发现足以定性的证据；不等于全部正确 |
| doc4/S4 | 1 | 1 | 未发现足以定性的证据；不等于全部正确 |
| doc4/S5 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc4/S6 | 2 | 2 | 未发现足以定性的证据；不等于全部正确 |
| doc4/S7 | 2 | 3 | 实际SPO确认有差距 |
| doc4/S8 | 2 | 1 | 实际SPO确认有差距 |
| doc4/S9 | 4 | 3 | 实际SPO确认有差距 |
| doc4/S10 | 2 | 1 | 实际SPO确认有差距 |

## 逐项证据与原因分析

每节给出完整源句、对应Gold、能拿到的反馈后SPO、重建和差异。未提供SPO的情况明确写出，不用重建代替。Gold编号采用本文档内从0开始的全局Gold编号。

### doc0/S7：已确认：读/执行的主体与目的关系未对齐Gold

**证据等级：实际SPO已确认。**

**实际运行源句**

```text
They may be implemented as instructions stored on a machine-readable medium, which may be read and executed by a computing platform to perform the operations described herein.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G18 | they | may be implemented as | instructions |
| G19 | instructions | are stored on | a machine-readable medium |
| G20 | a machine-readable medium | may be read and executed by | a computing platform |
| G21 | a computing platform | is to perform | the operations |

**附件可恢复的反馈后SPO**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| 0 | They | may be implemented as | instructions |
| 1 | the instructions | may be read by | a computing platform |
| 2 | instructions | are stored on | a machine-readable medium |
| 3 | the instructions | may be executed by | a computing platform |
| 4 | the instructions | perform | the operations described herein |

**对应重建 text_b（反馈前生成）**

```text
They may be implemented as instructions. Instructions are stored on a machine-readable medium.
```

**相关UNASSIGNED重建全文**

```text
The instructions may be read by a computing platform. Repeated use of the phrase "in one embodiment," may refer to the same embodiment. The instructions may be executed by a computing platform. The instructions perform the operations described herein. Repeated use of the phrase "in an exemplary embodiment," may refer to the same embodiment.
```

**导出的文本对比结果**

- A侧：
  - [S7] The original includes that the instructions may be read and executed by a computing platform to perform the operations described herein. The reconstruction omits this information entirely.
- B侧：
  - [UNASSIGNED] The instructions may be read by a computing platform.
  - [UNASSIGNED] The instructions may be executed by a computing platform.
  - [UNASSIGNED] The instructions perform the operations described herein.
  - [UNASSIGNED] Repeated use of the phrase "in one embodiment" may refer to the same embodiment.
  - [UNASSIGNED] Repeated use of the phrase "in an exemplary embodiment" may refer to the same embodiment.

**本轮反馈动作**：replace #11；replace #31；replace #32。

**为什么没有发现或没有修好**

相关五条SPO全部可恢复。Gold要求medium may be read and executed by platform，以及platform is to perform operations；已有条目却以instructions为主体表达read、execute和perform。这里不是仅缺来源：补来源后字段仍不对应目标Gold，两个目标Gold与本句五条预测的局部配对仍未建立。差异将读/执行在本句缺失与UNASSIGNED重复列出，模型只补来源，没有改关系。不能将“在全文能找到这些文字”当作Gold三元组已经抽对。

### doc0/S9：已确认：4条预测对应2条Gold，may refer为额外条目

**证据等级：实际SPO已确认。**

**实际运行源句**

```text
Further, repeated use of the phrase "in one embodiment," or "in an exemplary embodiment," do not necessarily refer to the same embodiment, although they may.
```

**Gold文件中的源句（与实际运行有版本差别）**

```text
Further, repeated use of the phrase "in one embodiment," or "in an exemplary embodiment," do not necessarily refer to the same embodiment.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G23 | repeated use of the phrase "in one embodiment," | do not necessarily refer to | the same embodiment |
| G24 | repeated use of the phrase  "in an exemplary embodiment," | do not necessarily refer to | the same embodiment |

**附件可恢复的反馈后SPO**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| 0 | repeated use of the phrase "in one embodiment," | does not necessarily refer to | the same embodiment |
| 1 | repeated use of the phrase "in one embodiment," | may refer to | the same embodiment |
| 2 | repeated use of the phrase "in an exemplary embodiment," | does not necessarily refer to | the same embodiment |
| 3 | repeated use of the phrase "in an exemplary embodiment," | may refer to | the same embodiment |

**对应重建 text_b（反馈前生成）**

```text
Repeated use of the phrase "in one embodiment," does not necessarily refer to the same embodiment. Repeated use of the phrase "in an exemplary embodiment," does not necessarily refer to the same embodiment.
```

**相关UNASSIGNED重建全文**

```text
The instructions may be read by a computing platform. Repeated use of the phrase "in one embodiment," may refer to the same embodiment. The instructions may be executed by a computing platform. The instructions perform the operations described herein. Repeated use of the phrase "in an exemplary embodiment," may refer to the same embodiment.
```

**导出的文本对比结果**

- A侧：
  - [S9] The original includes 'although they may', indicating that repeated uses of the phrases may refer to the same embodiment. The reconstruction omits this concession.
- B侧：
  - [UNASSIGNED] The instructions may be read by a computing platform.
  - [UNASSIGNED] The instructions may be executed by a computing platform.
  - [UNASSIGNED] The instructions perform the operations described herein.
  - [UNASSIGNED] Repeated use of the phrase "in one embodiment" may refer to the same embodiment.
  - [UNASSIGNED] Repeated use of the phrase "in an exemplary embodiment" may refer to the same embodiment.

**本轮反馈动作**：replace #14；replace #34。

**为什么没有发现或没有修好**

Gold只保留两种phrase的do not necessarily refer to；本句同时有两条may refer，反馈只给它们补来源。额外两条在运行源文although they may中有文字依据，但本评测Gold未标。两条否定关系还使用does而Gold为do，严格不相等。模型以源文支持为保留标准，无法知道Gold选择性省略正向关系，因此没有删除或改成Gold形式。此处不是让步内容漏抽，而是Gold对齐和额外预测问题。

### doc0/S4：优先核查：能力关系与本句数量不足

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
Further, the term computer readable medium is meant to refer to any machine-readable medium (automated data medium) capable of storing data in a format readable by a mechanical device.
```

**Gold文件中的源句（与实际运行有版本差别）**

```text
Further, the term computer readable medium is meant to refer to any machine-readable medium capable of storing data in a format readable by a mechanical device.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G11 | the term computer readable medium | is meant to refer to | any machine-readable medium |
| G12 | machine-readable medium | is capable of | storing data |
| G13 | machine-readable medium | is capable of storing data in | a format |
| G14 | a format | is readable by | a mechanical device |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [7, 23, 24]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The term computer readable medium is meant to refer to any machine-readable medium (automated data medium). Any machine-readable medium (automated data medium) stores data in a format. The format is readable by a mechanical device.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold有is capable of storing data和is capable of storing data in a format两项；重建只写medium stores data in a format。本句只有3条预测，对4条Gold存在局部配对数量不足；同时capable与stores差异未被对比提示指出。可能是三元组缺能力表达，也可能重建将能力丢失。反馈未改本句，须查#7、#23、#24才能确定具体漏项和失误环节。

### doc1/S2：一个长关系对应三条Gold，差异为空

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G3 | a congestion | may be detected based on | said congestion value |
| G4 | said minimum bandwidth demand | exceeds | the measured traffic per time |
| G5 | the measured traffic per time | is over | a given time span |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [2]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

本句只有#2一条，Gold有检测依据、带宽需求exceeds流量、流量over时间跨度三条。重建几乎还原源句，比较没有提示。即使全部文字都在一条SPO中，仍不能在本句一对一对应三条Gold。这是独立关系展开候选，按当前反馈prompt被视作拆分问题而不补新事实。

### doc1/S10：两条预测对应三条Gold的原因结构

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G27 | this | may lead to | inaccuracy |
| G28 | inaccuracy | is due to | the varying nature of instantaneous traffic patterns |
| G29 | inaccuracy | is due to | dependence on medium- to long-term congestion situations |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [17, 30]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and due to dependence on medium- to long-term congestion situations for reporting.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold分别列出lead to inaccuracy与两个inaccuracy is due to。重建把两个due to并入一条This may lead to长句，差异为空；本句两个预测最多覆盖两个本句Gold。未提供#17、#30字段，不能断定具体缺哪条，但结构数量不足与文本内容已覆盖可以同时成立。

### doc2/S1：一个预测对应三个Gold，且Even有明确差异

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
Even a small open area can present a danger when loose items are being transported in high-traffic areas.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G0 | even a small open area | can present | a danger |
| G1 | a danger | is when | loose items are being transported in high-traffic areas |
| G2 | loose items | are being transported in | high-traffic areas |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [0]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
A small open area can present a danger when loose items are being transported in high-traffic areas.
```

**导出的文本对比结果**

- A侧：
  - [S1] 缺少'Even'，弱化了强调语气
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold包含danger关系、danger的发生条件、loose items transported三条，本句只有#0一条。重建完整长句但省Even；对比仅提示Even，没有检查独立关系数量，反馈未改。Even是当前Gold已有词，属于可核查的细小字段差异；另外两项独立展开是主要结构候选。须看#0才能区分三元组本身省Even还是仅重建省略。

### doc0/S2：目的链组织差异；尚不能判断错在三元组还是重建

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
As the ECUs may include PUF components, the controller may query the ECU to identify which PUF component is compromised, in order to determine where in the sub-system the compromise is located.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G3 | the ECUs | may include | PUF components |
| G4 | the controller | may query | the ECU |
| G5 | the controller | may query the ECU to identify | which PUF component is compromised |
| G6 | the controller | may query the ECU in order to determine | where in the sub-system the compromise is located |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [3, 4, 19, 20]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The ECUs may include PUF components. The controller may query the ECU, identify which PUF component is compromised, and determine where in the sub-system the compromise is located.
```

**导出的文本对比结果**

- A侧：
  - [S2] The original sentence indicates a purpose chain: query the ECU to identify the compromised PUF component in order to determine where the compromise is located. The reconstruction lists query, identify, and determine as parallel actions, losing the purpose relationship.
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold将query、query to identify、query in order to determine分别表达。重建却列为query、identify、determine并列动作；差异A侧已经明确指出这一点，反馈未改内容。缺少这四条原SPO，不能确定模型忽略了真实三元组错误，还是判断只是重建错误。先查#3、#4、#19、#20的实际字段。

### doc0/S3：字段边界、主被动组织及Gold拼写差异

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
In this manner, validation of the vehicle identity ensures the integrity of all of the components that make up the vehicle as well as information generated by any of the components that make up the vehicle.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G7 | vlidation of the vehicle identity | ensures | the integrity of all of the components |
| G8 | the components | make up | the vehicle |
| G9 | vlidation of the vehicle identity | ensures | information generated by any of the components that make up the vehicle |
| G10 | information | is generated by | any of the components that make up the vehicle |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [5, 6, 21, 22]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
Validation of the vehicle identity ensures the integrity of all of the components and ensures information generated by any of the components. The components make up the vehicle. Any of the components generate information.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold包含information is generated by…，重建为components generate information；此外Gold的ensures information条目保留较长生成修饰。语义重建可能认为这些内容已覆盖，因而未产生差异。Gold还写vlidation，实际重建写validation。未拿到本句四条SPO，不能要求模型人为拼错，也不能仅因重建主动表达就认定原SPO没有被动关系。

### doc0/S5：目的被写成动作结果的候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
It is to be understood that each specific element includes all technical equivalents that operate in a similar manner to accomplish a similar purpose.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G15 | each specific element | includes | all technical equivalents |
| G16 | technical equivalents | operate in a similar manner to accomplish | a similar purpose |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [8, 25, 26]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
Each specific element includes all technical equivalents. All technical equivalents operate in a similar manner and accomplish a similar purpose.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold是operate in a similar manner to accomplish，重建写operate… and accomplish。差异未提示。若原SPO也将accomplish独立断言，应修关系；若SPO保留to而重建改成and，应修重建。本句3条对2条Gold，增加数量不能自动解决字段及目的组织问题。

### doc0/S6：可能存在拆分过多：4条对应1条Gold

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
Embodiments of the invention may also be implemented in one or a combination of hardware, firmware, and software.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G17 | embodiments of the invention | may be implemented in | one or a combination of hardware, firmware, and software |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [9, 27, 28, 29]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
Embodiments of the invention may also be implemented in hardware, firmware, software, or a combination of hardware, firmware, and software.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold把one or a combination of hardware, firmware, and software保留为一条。该句有4个预测index，重建又合成自然语言中的“单项或组合”，掩盖四条预测与一条Gold的数量差异。未提供四条SPO，不判定其中哪条多余；但按语义覆盖检查通常不会认为需修改，Gold P却可能受额外条目影响。

### doc0/S10：系统包含列表的关系层级候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G25 | this method | may be integrated in | a variety of systems |
| G26 | a variety of systems | include | connected cars |
| G27 | a variety of systems | include | car sharing |
| G28 | a variety of systems | include | rental car services |
| G29 | a variety of systems | include | maintenance |
| G30 | a variety of systems | include | factory services |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [15, 35, 36, 37, 38]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance, and factory services.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold有method may be integrated in systems及systems include五个对象，共6条；本句只有5个预测index，重建将全部列表写在including长句里。差异为空，无法显示缺哪条独立Gold或是否误用method作所有条目的主体。前面其他运行确有该主体问题，但不能据此直接套用到本轮，须取本轮#15、#35—#38。

### doc1/S3：释义连接关系means that可能没有独立表达

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
The term "part" in connection with the term "network" is to be understood in a broad sense, meaning that part of the network can be any real or imaginary fraction, portion or component of the network.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G6 | the term "part" in connection with the term "network" | is to be understood in | a broad sense |
| G7 | the term "part" in connection with the term "network" | means that | part of the network |
| G8 | part of the network | can be | any  real or imaginary fraction of the network |
| G9 | part of the network | can be | any portion or component of the network |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [3, 4, 18, 19]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The term "part" in connection with the term "network" is to be understood in a broad sense. Part of the network can be any real or imaginary fraction, portion, or component of the network.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

重建表达term is understood in broad sense与part can be各成分，却没有显式means that连接。Gold将这个连接另列。四条SPO未提供，不能仅据重建没说means that判为漏抽。语义相近的定义改写容易被比较阶段视为覆盖，因而不给具体Gold结构线索。

### doc1/S9：feedback profiles depend on operator的内部关系候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
This enhances the flexibility of the congestion value, since different operators can use different transformation functions or profiles such that the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G23 | this | enhances | the flexibility of the congestion value |
| G24 | different operators | can use | different transformation functions or profiles |
| G25 | the congestion level | may be based | per cell and per link with different feedback profiles |
| G26 | different feedback profiles | depend on | the need of an operator |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [14, 15, 16, 29]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
This enhances the flexibility of the congestion value. Different operators can use different transformation functions or profiles. The congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.
```

**导出的文本对比结果**

- A侧：
  - [S9] since (expressing cause)
  - [S9] such that (expressing result/purpose)
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold将profiles depend on operator另列，重建仍放在per-cell/per-link长句里，只有since与such that被比较提示。差异指向句间衔接，未明确指出内部依赖关系是否独立存在。当前四条SPO未知，不能确认漏项；即使依赖文字已有，按当前反馈规则也可能被归为拆分而不新增。

### doc2/S3：hazards内容、enact laws和laws against的展开候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
Further, the hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G6 | the hazards | is of loose items flying out of | the open-top of cargo trailers |
| G7 | the hazards of loose items flying out of the open-top of cargo trailers | has led many governing bodies to enact | strict laws |
| G8 | strict laws | is against | such open transport |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [2, 14]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold三条，预测两条。重建基本复述长句，差异为空，无法显露hazards of和laws against是否独立抽出。至少本句预测数不足以逐项对应Gold；具体缺哪条仍须原SPO确认。

### doc2/S5：matter所在位置嵌在长主体中

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not as a limitation.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G11 | the matter set forth | is in | the foregoing description and accompanying drawings |
| G12 | the matter set forth | is offered by | way of illustration |
| G13 | the matter set forth | is offered not as | a limitation |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [4, 16]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not by way of a limitation.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold另列matter is in description/drawings，本句两个预测对三个Gold。重建保留该长主语以及illustration/not limitation，比较仅可见语法改写而没有遗漏提示。缺少独立位置关系的候选会被语义覆盖检查忽略。

### doc2/S6：claims/viewed/perspective的主体连接候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G14 | the actual scope of the protection sought | is intended to be defined in | the following claims |
| G15 | the following claims | are viewed in | their proper perspective |
| G16 | their proper perspective | is based on | the prior art |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [5, 17, 18]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The actual scope of the protection sought is intended to be defined in the following claims, which are viewed in their proper perspective based on the prior art.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold主体是claims are viewed in perspective和perspective based on prior art；重建写claims, which are viewed…，比历史运行清楚，但实际三个SPO未提供。条目数与Gold相同不能保证字段正确；需检查#5、#17、#18。差异为空既可能真覆盖，也可能遗漏了关系主体错误，不能确定归因。

### doc2/S7：conditions of being atop的内部关系候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
Preferably, most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G17 | most of these components | are made of | strong materials |
| G18 | most of these components made of strong materials | is to withstand | the conditions |
| G19 | the conditions | are of being atop | an open cargo area of a vehicle during transportation of goods |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [6, 19]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
Most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.
```

**导出的文本对比结果**

- A侧：
  - [S7] 缺少'Preferably'，弱化了优选条件
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold三条，预测两条；重建把材料、承受条件和conditions of being atop放在一个长句里。差异只报告Preferably，而该词不在当前Gold中。反馈即使补Preferably，也不能解决三个Gold对两个预测的结构差距。

### doc2/S8：基础brought into use与两个目的的字段组织

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
Later, a series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G20 | a series of bows | was brought into | use |
| G21 | a series of bows brought into use | is to keep the tarpaulin from lying in | direct contact with goods in the truck trailer |
| G22 | a series of bows brought into use | is to prevent | water accumulation |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [7, 20]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
A series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.
```

**导出的文本对比结果**

- A侧：
  - [S8] 缺少时间状语'Later'
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold有brought into use基础关系和两个is to目的，共三条；预测只有两条，重建流畅合并两个目的。对比只提示Later，当前Gold没有Later。真正应核查的是基础关系是否独立、两个目的的head/relation是否与Gold一致；当前没有具体提示。

### doc3/S2：incorporation事件内部的被动关系候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G5 | the incorporation of granulated recycled tire rubber into bitumen | aimed to improve | the mechanical behavior of bituminous mixtures |
| G6 | granulated recycled tire rubber | is incorporated into | bitumen |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [3]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold将rubber is incorporated into bitumen单列；本句只有一个预测。重建与源句基本相同，故差异为空。若全部内容在事件主语中，按当前反馈职责它被视为已有内容，不会为了独立对应Gold而add。

### doc3/S3：温度条件内部关系数量不足

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
In this connection, the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G7 | the properties of the asphalt bitumen-based binders in high and low temperature conditions | are of | a decisive importance |
| G8 | the asphalt bitumen-based binders | are in | high temperature conditions |
| G9 | the asphalt bitumen-based binders | are in | low temperature conditions |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [4, 21]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The properties of the asphalt bitumen-based binders in high temperature conditions and in low temperature conditions are of a decisive importance.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold为properties的重要性及binders in high/low temperature三条，本句只有两个预测；重建展开高低温文字但没有反映实际三元组边界，差异为空。无法从重建判断两条预测分别对应哪条Gold，需#4、#21。

### doc3/S5：oil-dry定义、同位解释与free of关系候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
The term oil-dry thus stands to mean that the external surface, namely the out-most layer of the rubber composite, is substantially, or completely, free of oil.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G17 | the term oil-dry | stands to mean that | the external surface is substantially, or completely, free of oil. |
| G18 | the external surface | is namely | the out-most layer of the rubber composite |
| G19 | the external surface | is substantially, or completely, free of | oil |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [11, 23]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The term oil-dry stands to mean that the external surface is substantially, or completely, free of oil. The external surface is namely the out-most layer of the rubber composite.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold三条，本句两个预测。重建把oil-dry定义与free of合写，另有namely解释，全文内容看似完整。比较忽略独立关系数量，反馈未改。需核实#11、#23是否缺独立free of或只是字段划分不同。

### doc3/S6：Gold条件前提条目与当前抽取政策冲突

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle, namely the diameter of an equivalent spherical particle based on the longest dimension of the particle.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G20 | the particles | are of | non-spheroid shape |
| G21 | the term | refers to | the average equivalent diameter of the particle |
| G22 | the average equivalent diameter of the particle | is namely | the diameter of an equivalent spherical particle |
| G23 | the diameter of an equivalent spherical particle | is based on | the longest dimension of the particle |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [12, 24, 25]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle. The average equivalent diameter of the particle is namely the diameter of an equivalent spherical particle. The diameter of an equivalent spherical particle is based on the longest dimension of the particle.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold把particles are of non-spheroid shape另列为一条；当前重建把它放在When条件中，本句仅三个预测。对比不会把保留条件视为遗漏。按当前Gold可能缺一个独立配对机会，但不能从重建确定三条实际SPO。当前拆分prompt明确保留When条件，可能在源文表达与Gold形式之间形成持续差距。评价仍以Gold为准，此处记录政策冲突，不以源文准确替代Gold分数。

### doc3/S7：目的在UNASSIGNED，另需检查prior to独立关系

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
In some embodiments, the process further comprises a pre-step of grinding the rubber prior to employing the process of this invention to reduce the particles to a desired size.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G24 | the process | comprises | a pre-step of grinding the rubber |
| G25 | a pre-step of grinding the rubber | is prior to | employing the process of this invention |
| G26 | a pre-step of grinding the rubber prior to employing the process of this invention | is to reduce the particles to | a desired size |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [13]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The process further comprises a pre-step of grinding the rubber prior to employing the process of this invention.
```

**相关UNASSIGNED重建全文**

```text
A pre-step of grinding the rubber prior to employing the process of this invention aims to reduce the particles to a desired size.
```

**导出的文本对比结果**

- A侧：
  - [S7] In some embodiments
  - [S7] to reduce the particles to a desired size
- B侧：
  - [UNASSIGNED] A pre-step of grinding the rubber prior to employing the process of this invention aims to reduce the particles to a desired size.

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

本句组只有#13，UNASSIGNED另有#14目的，人工关联后共两个，对三个Gold。差异提示In some embodiments和to reduce，但目的文字本已在UNASSIGNED，不能算全新事实遗漏；独立prior to及目的字段是否对应Gold才是候选。反馈零操作可能在避免重复补目的，不能单凭零操作判漏执行。

### doc3/S9：比较对象中的材料修饰候选

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even compared with traditional SMA mixtures with highly modified bitumen and fibres.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G29 | it | is clearly | the lowest value |
| G30 | the lowest value | is compared with | tradition Asphalt Rubber gap graded mixtures (with and without RAR) |
| G31 | the lowest value | is even compared with | traditional SMA mixtures with highly modified bitumen and fibres |
| G32 | traditional SMA mixtures | are with highly modified | bitumen and fibres |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [16, 27, 28]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures with RAR, tradition Asphalt Rubber gap graded mixtures without RAR, and traditional SMA mixtures with highly modified bitumen and fibres.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold四条，包括SMA mixtures are with highly modified bitumen and fibres；本句三个预测。重建列出了完整比较对象，内部with文字也在，但没有暴露是否独立关系。差异为空，按当前反馈规则容易归到拆分。

### doc3/S10：Gold对同一范围限制采用两种字段划分

**证据等级：候选：需原SPO确认具体缺项或错误层。**

**实际运行源句**

```text
It should be noted that the range is given as such merely for convenience and brevity and should not be construed as an inflexible limitation on the scope of the invention.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G33 | the range | is given as such merely for | convenience |
| G34 | the range | is given as such merely for | brevity |
| G35 | the range | should not be construed as | an inflexible limitation on the scope of the invention |
| G36 | the range | should not be construed as an inflexible limitation on | the scope of the invention |

**反馈后SPO：附件未提供完整字段。** 本句没有内容操作，重建输入原index为 [17, 18, 29]；只能确认条目仍在，不能从自然语言判断原字段。

**对应重建 text_b（反馈前生成）**

```text
The range is given as such merely for convenience and brevity, and should not be construed as an inflexible limitation on the scope of the invention.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：无操作。

**为什么没有发现或没有修好**

Gold四条，其中后两条以不同字段划分表达相近的范围限制；本句三个预测。不能简单说漏了第四项新事实。语义去重与当前Gold逐行匹配存在冲突，反馈认为内容完整时不会额外生成一个近重复表达。

### doc4/S7：已确认：一条改好但未完全对齐，一条被加长

**证据等级：实际SPO已确认。**

**实际运行源句**

```text
All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G12 | all of the evaluation items EV | is worse than | the standard thresholds E0 |
| G13 | all of the evaluation items EV | is of | each of the communication paths PH in the third group G3 |

**附件可恢复的反馈后SPO**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| 0 | All of the evaluation items EV of each of the communication paths PH in the third group G3 | is worse than | the standard thresholds E0 |
| 1 | the evaluation items EV | are of | each of the communication paths PH in the third group G3 |
| 2 | each of the communication paths PH | is in | the third group G3 |

**对应重建 text_b（反馈前生成）**

```text
All of the evaluation items EV is worse than the standard thresholds E0. The evaluation items EV are associated with each of the communication paths PH in the third group G3. Each of the communication paths PH is in the third group G3.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：replace #6；replace #16。

**为什么没有发现或没有修好**

反馈后#16与目标Goldis of的直接F1为0.8889，仍有all/the与is/are差别；#6加长主语后与目标Gold只有0.6842。原#17仍在，本句预测数足够却字段组织不一致。两侧差异为空，反馈对are associated with做了修复，但同时作了反向的主语回填。

### doc4/S8：已确认：反馈后只剩一条，对应两个Gold

**证据等级：实际SPO已确认。**

**实际运行源句**

```text
In the good category of the available bandwidth, the value of the routing path latency is equal to or lower than 500 kbps.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G14 | the value of the routing path latency | is equal to or lower than | 500 kbps |
| G15 | the value of the routing path latency | is equal to or lower than 500 kbps in | the good category of the available bandwidth |

**附件可恢复的反馈后SPO**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| 0 | the value of the routing path latency in the good category of the available bandwidth | is equal to or lower than | 500 kbps |

**对应重建 text_b（反馈前生成）**

```text
（空）
```

**相关UNASSIGNED重建全文**

```text
The value of the routing path latency is equal to or lower than 500 kbps. The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims. The value of the routing path latency is equal to or lower than 50 ms. The value of the routing path latency is in the good category of the available bandwidth. The examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by their equivalents. The value of the routing path latency is in the good category of the routing path latency.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：remove #18；replace #7。

**为什么没有发现或没有修好**

原#7加长主体并删除#18，第二个Gold独立配对机会消失。全文重建已有阈值与类别，无法靠“内容缺没缺”提示出两个Gold需要分别表达。该问题由反馈制造，下降原因见阶段一。

### doc4/S9：已确认：scope主体与Gold不同，两个客体被合并

**证据等级：实际SPO已确认。**

**实际运行源句**

```text
It is intended that the specification and examples be considered as exemplary only, with a true scope of the disclosure being indicated by the following claims and their equivalents.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G16 | the specification and examples | are considered as | exemplary |
| G17 | the specification and examples | are considered as exemplary only with | a true scope of the disclosure |
| G18 | the disclosure | is being indicated by | the following claims |
| G19 | the disclosure | is being indicated by | their equivalents |

**附件可恢复的反馈后SPO**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| 0 | The specification | is intended to be considered as | exemplary only |
| 1 | a true scope of the disclosure | is indicated by | the following claims and their equivalents |
| 2 | The examples | are intended to be considered as | exemplary only |

**对应重建 text_b（反馈前生成）**

```text
（空）
```

**相关UNASSIGNED重建全文**

```text
The value of the routing path latency is equal to or lower than 500 kbps. The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims. The value of the routing path latency is equal to or lower than 50 ms. The value of the routing path latency is in the good category of the available bandwidth. The examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by their equivalents. The value of the routing path latency is in the good category of the routing path latency.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：remove #20；replace #8；replace #9；replace #19。

**为什么没有发现或没有修好**

反馈后只留scope indicated by claims and equivalents一条，而Gold用disclosure作为主体并分别标claims、equivalents；另两条specification/examples也与Gold合并主语的表达不同。这里既有反馈造成的合并退化，也有原本的字段差距。差异为空，模型仍认为and应整体表达，未以Gold粒度组织结果。

### doc4/S10：已确认：与S8同样的单条覆盖双Gold问题

**证据等级：实际SPO已确认。**

**实际运行源句**

```text
In the good category of the routing path latency, the value of the routing path latency is equal to or lower than 50 ms.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G20 | the value of the routing path latency | is equal to or lower than | 50 ms |
| G21 | the value of the routing path latency | is equal to or lower than 50 ms in | the good category of the routing path latency |

**附件可恢复的反馈后SPO**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| 0 | the value of the routing path latency in the good category of the routing path latency | is equal to or lower than | 50 ms |

**对应重建 text_b（反馈前生成）**

```text
（空）
```

**相关UNASSIGNED重建全文**

```text
The value of the routing path latency is equal to or lower than 500 kbps. The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims. The value of the routing path latency is equal to or lower than 50 ms. The value of the routing path latency is in the good category of the available bandwidth. The examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by their equivalents. The value of the routing path latency is in the good category of the routing path latency.
```

**导出的文本对比结果**

- A侧：
  - 未导出本句提示。
- B侧：
  - 未导出本句提示。

**本轮反馈动作**：remove #21；replace #10。

**为什么没有发现或没有修好**

反馈后只剩加长主体的50 ms关系，对应本句两个Gold；文字仍在但独立配对不足。下降原因见阶段一。

## 原因归纳：哪些已确认，哪些仍是推测

| 环节 | 有依据的观察 | 还不能确定的部分 |
| --- | --- | --- |
| 来源定位 | 15条原未定位；部分差异实际由分组错位造成 | 本次父子来源何时变空，需要splitting原始审计 |
| 重建 | 将多条或长字段组织成完整自然语言，掩盖SPO边界；有capable/to等关系组织差别 | 错词来自原SPO还是重建，需要完整预测 |
| 对比 | 主要提示内容/衔接词差异，未显示独立Gold数量；有已提示但未改的案例 | 本文依据导出MD，不能排除导出遗漏嵌套差异 |
| 反馈决策 | 部分只补来源；部分把独立关系合并；当前prompt跳过已有长字段的纯拆分问题 | 这次实际加载的prompt及每个未修改决定的内部理由不可见 |
| Gold形式 | 有源文支持但Gold未标的额外关系、主体选择与字段划分冲突 | 没有Gold输入，模型不能自动知道每项标注取舍 |

## 下一步需要的原始数据

要将19句数量候选逐条落实为“哪条Gold未匹配、哪条预测差在哪里”，还需本轮各篇完整after_split、after_revision和matches。优先读取运行目录中的run_manifest或revision_result、splitting及feedback JSON；原始输出应保留sentence_differences和实际prompt。

这些文件目前未在工作区找到。本报告已经完成现有证据下的逐句筛查和候选原因分析，但没有声称穷尽全文所有漏抽，也没有虚构121条未提供的SPO。

## 对后续修改的影响

先固定来源定位与分组，减少假遗漏；再明确反馈是否应处理“内容已有但缺Gold独立关系”的范围。若继续全部交给拆分，反馈增长目标就应限于真内容遗漏和已有关系纠错；若希望反馈弥补独立Gold差距，需要有针对性地调整这条边界，并在固定输入上看Gold分数。当前不修改程序。
