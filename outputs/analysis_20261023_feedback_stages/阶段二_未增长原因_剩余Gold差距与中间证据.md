# 阶段二：完整三元组下的剩余Gold差距与中间证据

对象：run1_5doc_1022。依据新补充的完整143/141条三元组更新。效果只以当前146条Gold判断。

## 本次修订：以实际反馈输入为准

用户补充了附件3bbba618中的`grouped_difference_context(diff)`输出，即反馈prompt的输入四。此前报告把原始字段转成了逐句说明，并把相关UNASSIGNED差异按内容放到源句下；这种分析排版不等于agent实际收到的结构，容易造成误解，本次已更正。

核对结果：五篇文档的54个对象（50个源句、4个UNASSIGNED）中，原先引用的text_a、text_b、triple_indices、generation_status及两侧差异内容均与新附件一致；此前主要问题在于重新组织了展示结构，并省略了完整输入的字段和提示语。正文现在使用对象原文摘录，文末保留每篇输入四的完整原文。

**需要区分的四件事**

- 顶层`unique_to_text_a/b`是整篇汇总，带`[Sx]`或`[UNASSIGNED]`标记；`sentence_differences`对象内部的差异属于该对象自身。这两层在实际输入中同时存在，汇总不是另一次比较。
- UNASSIGNED是单独对象。本报告可以指出它的内容可能属于哪句，但不把这个人工判断改写成原始输入中的来源归属。
- `generation_status`与`comparison_status`都保留原值。`compared`只表示导出的比较状态，不能证明内容比较正确；`[]`也不能证明没有Gold差距。
- 以前补充材料中的“反馈后重建展示”不是本轮输入四的一部分。本次从逐句输入证据区移除这些展示，避免误认为它们触发了本轮反馈；反馈后三元组和Gold对照仍然保留。

**对原因判断的补充**

实际输入前导语已经说明：“差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。”因此，对比未报错会减少定位线索，但不能把反馈未修复直接解释为没有要求它检查空差异。doc0/S2属于提示已经指出真实问题却未执行修复；doc0/S4等属于比较未指出问题，反馈的额外检查也未修复。为什么没有执行，需要更多调用证据，不能仅凭最终结果推测模型内部过程。

这份输入四仍保留了相关三元组全局索引和逐句文本，所以“重建文字会掩盖字段边界”不能理解为反馈agent完全看不到三元组结构；它还有其他输入。报告观察的是这一路重建/差异提示没有显示具体SPO差距，而最终反馈也没有利用实际SPO修复。

doc4/S8、S9、S10实际输入的text_b为空、generation_status为empty_triples，但A/B差异均为空、comparison_status均为compared。不能把这里写成“比较已明确判定内容齐全”，也不能写成“比较已经报告这些句子遗漏全部事实”。相关已有内容在独立UNASSIGNED对象中。

新增附件只涵盖输入四及它的前导语，不是整份反馈prompt或全部输入，也不包含模型内部判断过程。Gold匹配和PRF1不受此次展示修订影响。

附件SHA-256：`67b52b84be3a9d56bc3bd038865e97c3d0bf508c3767616b2999e8ac6385c4e5`。

## 完整阶段数据补齐后的核验

本次新增附件951395ee（after_split）和3c261745（after_revision）。逐篇条数为拆分后39/31/21/30/22，反馈后39/32/21/30/19，合计143→141；Gold为31/30/26/37/22，合计146。

已核对：此前17项操作全部可在完整列表中复现，按原索引应用后与反馈后141条SPO逐条一致；之前重建分组的所有索引与拆分来源编号一致。此前缺少121条反馈后SPO的问题已经解除。

采用仓库evaluation_common.py的lexical-one-to-one-v1评测，严格和宽松匹配按整篇文章计算；来源编号用于诊断，不限制当前评分配对。重算保存了全部匹配、未匹配、词元证据及反事实结果，未调用模型，也未修改程序或prompt。附件是用户导出的数据，重算核实的是导出内容，不能替代原始调用日志真实性核验。

逐句证据区现在只展示实际输入四的原始对象。真正触发本轮反馈的是拆分后的重建和对比；反馈后重建展示不属于这次输入。模型内部为什么选择某一操作不能由结果文件直接读取。

## 现在可以明确的结论

- 反馈后40条Gold未获得宽松一对一配对，35条预测未配对；另外6条已配对Gold的配对F1≤0.5。0.5只用于列出优先人工复核对象，不是修改评测阈值。
- 40条未配对不能全部称为“新事实漏抽”：其中混有内部关系未展开、主体/方向错误、字段边界差别、Gold重复标注及反馈误删。106条已配对也不等于106条语义正确，至少有两处跨源句的无关弱配对。
- doc0/S2目的链、doc0/S4能力语义、doc2/S7目的主体、doc3/S4的being关系等，已由真实SPO确认存在差距，并非只有拆分问题。
- doc1/S2、S9、S10，doc2/S1，doc3/S2、S3、S5等确有文字已在长字段、缺独立Gold关系的问题。重建能还原这些文字，文本差异常为空，无法可靠检查关系是否独立抽出。
- doc0/S6、doc1/S4/S5还存在预测比Gold拆得更细的问题；“把所有长信息都再拆开”不能保证解决全部Gold差距。
- doc0/S2的真实目的关系错误已进入差异提示，却仍未修改；doc2/S1的Even也已被提示却未修。说明除了发现问题，反馈执行也有遗漏。输出足以确认未落实，不能证明模型内部为何跳过。
- 当前仓库prompt把“内容已在长字段，仅缺独立表达”归给拆分阶段，这与有限增长相符；但本轮实际加载哪个prompt仍需运行日志验证，不能仅凭当前代码断言。

## 完整未配对清单

这里采用现有整篇评分的真实未配对结果，不将数量差直接当成漏抽数。编号为文档内Gold的0起始编号；详细三元组与中间证据见后面的对应源句。

| 文档 | 未配对Gold编号 | 数量 |
| --- | --- | ---: |
| doc0 | G2, G10, G12, G20, G21, G26, G27, G28, G29, G30 | 10 |
| doc1 | G4, G5, G7, G26, G28, G29 | 6 |
| doc2 | G1, G2, G5, G7, G8, G11, G19, G20 | 8 |
| doc3 | G6, G8, G9, G16, G19, G20, G25, G29, G30, G31, G32, G36 | 12 |
| doc4 | G6, G17, G19, G21 | 4 |

## 配对存在不代表关系抽对

- doc2/S3 G6（hazards of loose items…）配到doc2/S2 #13（structure / is for / attachment of a tarp），配对F1=0.272727，是无关的词语重合。
- doc4/S8 G15（阈值类别关系）配到doc4/S7 #17（communication paths / is in / third group G3），配对F1=0.285714，也不应视为关系正确。
- doc3/S7 G26配到仍无source_sentence_ids的#14；这条内容确实来自S7，属于来源缺失而非无关误配。
- doc4/S2 G3与S3 G6是完全相同的Gold条目；预测#12只有一个实例、关联S2和S3，全文一对一只能覆盖其中一行。这是同一事实在两句出现，不是跨句事实。

## 50句逐句核查

每句列出完整Gold、反馈前后实际三元组、全文真实配对、重建与差异。原始source_sentence_ids保留；仅用于分析的UNASSIGNED归属会明确标出。由于#12关联两个源句、未定位条目被人工关联，逐句展示行数不可直接求和当作去重总数。

### doc0/S1：主体替换及Gold未收录条目

**源句（本轮实际输入）**

```text
Because such elements and operations are well known in the art, and because they do not facilitate a better understanding of the present disclosure, a discussion of such elements and operations may not be provided herein.
```

**Gold版本中的源句（存在差别）**

```text
Because such elements and operations are well known in the art, and because they do not facilitate a better understanding of the present disclosure.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G0 | such elements | are well known in | the art |
| G1 | such operations | are well known in | the art |
| G2 | they | do not facilitate | a better understanding of the present disclosure |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | such elements | are well known in | the art |
| #1 / 原来源=S1 | such elements | do not facilitate | a better understanding of the present disclosure |
| #2 / 原来源=S1 | a discussion of such elements | may not be provided | herein |
| #16 / 原来源=S1 | such operations | are well known in | the art |
| #17 / 原来源=S1 | such operations | do not facilitate | a better understanding of the present disclosure |
| #18 / 原来源=S1 | a discussion of such operations | may not be provided | herein |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | such elements | are well known in | the art |
| #1 / 原来源=S1 | such elements | do not facilitate | a better understanding of the present disclosure |
| #2 / 原来源=S1 | a discussion of such elements | may not be provided | herein |
| #16 / 原来源=S1 | such operations | are well known in | the art |
| #17 / 原来源=S1 | such operations | do not facilitate | a better understanding of the present disclosure |
| #18 / 原来源=S1 | a discussion of such operations | may not be provided | herein |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G0 | #0 / 1.000000 | #0 / 1.000000 |
| G1 | #16 / 1.000000 | #16 / 1.000000 |
| G2 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S1"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S1",
      "triple_indices": [
        0,
        1,
        2,
        16,
        17,
        18
      ],
      "text_b": "Such elements are well known in the art and do not facilitate a better understanding of the present disclosure, and a discussion of such elements may not be provided herein. Such operations are well known in the art and do not facilitate a better understanding of the present disclosure, and a discussion of such operations may not be provided herein.",
      "generation_status": "generated",
      "text_a": "Because such elements and operations are well known in the art, and because they do not facilitate a better understanding of the present disclosure, a discussion of such elements and operations may not be provided herein.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

Gold G2用they作主体；现有#1/#17分别用such elements/operations，语义能还原，但不能直接匹配该Gold主体。#2/#18的discussion未列入当前Gold，运行源句与Gold源句存在版本差别。对比没有指出这种标注形式差距；按源文支持检查也不会主动删去这些条目。

### doc0/S2：已提示的目的关系错误没有修复

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S2 | the ECUs | may include | PUF components |
| #4 / 原来源=S2 | the controller | may query | the ECU |
| #19 / 原来源=S2 | the controller | may identify | which PUF component is compromised |
| #20 / 原来源=S2 | the controller | may determine | where in the sub-system the compromise is located |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S2 | the ECUs | may include | PUF components |
| #4 / 原来源=S2 | the controller | may query | the ECU |
| #19 / 原来源=S2 | the controller | may identify | which PUF component is compromised |
| #20 / 原来源=S2 | the controller | may determine | where in the sub-system the compromise is located |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G3 | #3 / 1.000000 | #3 / 1.000000 |
| G4 | #4 / 1.000000 | #4 / 1.000000 |
| G5 | #19 / 0.818182 | #19 / 0.818182 |
| G6 | #20 / 0.800000 | #20 / 0.800000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S2"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S2",
      "triple_indices": [
        3,
        4,
        19,
        20
      ],
      "text_b": "The ECUs may include PUF components. The controller may query the ECU, identify which PUF component is compromised, and determine where in the sub-system the compromise is located.",
      "generation_status": "generated",
      "text_a": "As the ECUs may include PUF components, the controller may query the ECU to identify which PUF component is compromised, in order to determine where in the sub-system the compromise is located.",
      "unique_to_text_a": [
        "The original sentence indicates a purpose chain: query the ECU to identify the compromised PUF component in order to determine where the compromise is located. The reconstruction lists query, identify, and determine as parallel actions, losing the purpose relationship."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际#19/#20确实是may identify/may determine，缺Gold关系字段中的query the ECU to/in order to，并非只是重建改写。重建也将它们列为并行动作；A侧明确提示目的链丢失，但反馈零操作。现在可确认：真实SPO问题已被差异提示，却没有落实修复；为何未执行仍无法从输出推知模型内部原因。

### doc0/S3：主客体方向、字段长度及Gold拼写

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S3 | validation of the vehicle identity | ensures | the integrity of all of the components |
| #6 / 原来源=S3 | validation of the vehicle identity | ensures | information generated by any of the components |
| #21 / 原来源=S3 | the components | make up | the vehicle |
| #22 / 原来源=S3 | any of the components | generate | information |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S3 | validation of the vehicle identity | ensures | the integrity of all of the components |
| #6 / 原来源=S3 | validation of the vehicle identity | ensures | information generated by any of the components |
| #21 / 原来源=S3 | the components | make up | the vehicle |
| #22 / 原来源=S3 | any of the components | generate | information |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G7 | #5 / 0.923077 | #5 / 0.923077 |
| G8 | #21 / 1.000000 | #21 / 1.000000 |
| G9 | #6 / 0.774194 | #6 / 0.774194 |
| G10 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S3"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S3",
      "triple_indices": [
        5,
        6,
        21,
        22
      ],
      "text_b": "Validation of the vehicle identity ensures the integrity of all of the components and ensures information generated by any of the components. The components make up the vehicle. Any of the components generate information.",
      "generation_status": "generated",
      "text_a": "In this manner, validation of the vehicle identity ensures the integrity of all of the components that make up the vehicle as well as information generated by any of the components that make up the vehicle.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#22是components generate information，Gold G10是information is generated by components，方向不同；#6还缺Gold尾部that make up the vehicle。重建表达了近似内容，对比为空，因此没有提示按Gold方向调整。Gold的vlidation拼写与预测validation不同，影响严格匹配；记录评分差距，不建议让模型故意制造拼写错误。

### doc0/S4：能力语义在实际三元组中已丢失

**源句（本轮实际输入）**

```text
Further, the term computer readable medium is meant to refer to any machine-readable medium (automated data medium) capable of storing data in a format readable by a mechanical device.
```

**Gold版本中的源句（存在差别）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=S4 | the term computer readable medium | is meant to refer to | any machine-readable medium (automated data medium) |
| #23 / 原来源=S4 | any machine-readable medium (automated data medium) | stores data in | a format |
| #24 / 原来源=S4 | the format | is readable by | a mechanical device |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=S4 | the term computer readable medium | is meant to refer to | any machine-readable medium (automated data medium) |
| #23 / 原来源=S4 | any machine-readable medium (automated data medium) | stores data in | a format |
| #24 / 原来源=S4 | the format | is readable by | a mechanical device |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G11 | #7 / 0.896552 | #7 / 0.896552 |
| G12 | 未配对 | 未配对 |
| G13 | #23 / 0.571429 | #23 / 0.571429 |
| G14 | #24 / 0.875000 | #24 / 0.875000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S4"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S4",
      "triple_indices": [
        7,
        23,
        24
      ],
      "text_b": "The term computer readable medium is meant to refer to any machine-readable medium (automated data medium). Any machine-readable medium (automated data medium) stores data in a format. The format is readable by a mechanical device.",
      "generation_status": "generated",
      "text_a": "Further, the term computer readable medium is meant to refer to any machine-readable medium (automated data medium) capable of storing data in a format readable by a mechanical device.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#23是medium / stores data in / a format；Gold G12要求is capable of / storing data，G13也保留is capable of。确认问题已在SPO中，不只是重建丢词。三个预测对应四条Gold，缺独立能力关系；重建沿用stores，对比仍未提示能力与实际存储的差别，反馈未改。

### doc0/S5：目的关系被拆成两个动作

**源句（本轮实际输入）**

```text
It is to be understood that each specific element includes all technical equivalents that operate in a similar manner to accomplish a similar purpose.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G15 | each specific element | includes | all technical equivalents |
| G16 | technical equivalents | operate in a similar manner to accomplish | a similar purpose |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #8 / 原来源=S5 | each specific element | includes | all technical equivalents |
| #25 / 原来源=S5 | all technical equivalents | operate in | a similar manner |
| #26 / 原来源=S5 | all technical equivalents | accomplish | a similar purpose |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #8 / 原来源=S5 | each specific element | includes | all technical equivalents |
| #25 / 原来源=S5 | all technical equivalents | operate in | a similar manner |
| #26 / 原来源=S5 | all technical equivalents | accomplish | a similar purpose |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G15 | #8 / 1.000000 | #8 / 1.000000 |
| G16 | #26 / 0.631579 | #26 / 0.631579 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S5"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S5",
      "triple_indices": [
        8,
        25,
        26
      ],
      "text_b": "Each specific element includes all technical equivalents. All technical equivalents operate in a similar manner and accomplish a similar purpose.",
      "generation_status": "generated",
      "text_a": "It is to be understood that each specific element includes all technical equivalents that operate in a similar manner to accomplish a similar purpose.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#25写operate in a similar manner，#26写accomplish a similar purpose；Gold G16把operate…to accomplish作为一个目的关系。重建使用and串联两条事实，对比为空。这里需要修复关系表达和Gold粒度，继续增加三元组数量不一定有用。

### doc0/S6：拆分粒度比Gold更细

**源句（本轮实际输入）**

```text
Embodiments of the invention may also be implemented in one or a combination of hardware, firmware, and software.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G17 | embodiments of the invention | may be implemented in | one or a combination of hardware, firmware, and software |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #9 / 原来源=S6 | Embodiments of the invention | may also be implemented in | hardware |
| #27 / 原来源=S6 | Embodiments of the invention | may also be implemented in | firmware |
| #28 / 原来源=S6 | Embodiments of the invention | may also be implemented in | software |
| #29 / 原来源=S6 | Embodiments of the invention | may also be implemented in | a combination of hardware, firmware, and software |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #9 / 原来源=S6 | Embodiments of the invention | may also be implemented in | hardware |
| #27 / 原来源=S6 | Embodiments of the invention | may also be implemented in | firmware |
| #28 / 原来源=S6 | Embodiments of the invention | may also be implemented in | software |
| #29 / 原来源=S6 | Embodiments of the invention | may also be implemented in | a combination of hardware, firmware, and software |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G17 | #29 / 0.909091 | #29 / 0.909091 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S6"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S6",
      "triple_indices": [
        9,
        27,
        28,
        29
      ],
      "text_b": "Embodiments of the invention may also be implemented in hardware, firmware, software, or a combination of hardware, firmware, and software.",
      "generation_status": "generated",
      "text_a": "Embodiments of the invention may also be implemented in one or a combination of hardware, firmware, and software.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际四条分别列hardware、firmware、software及combination；Gold只保留一条one or a combination…。重建重新合成完整列表后，看不出四对一的冗余匹配问题；差异为空。说明与Gold的差距并非全部来自拆得不够，也存在拆得比Gold更细。

### doc0/S7：来源修好了，Gold主体与目的仍未修正

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #10 / 原来源=S7 | They | may be implemented as | instructions |
| #11 / 原来源=空（本报告关联到S7） | the instructions | may be read by | a computing platform |
| #30 / 原来源=S7 | instructions | are stored on | a machine-readable medium |
| #31 / 原来源=空（本报告关联到S7） | the instructions | may be executed by | a computing platform |
| #32 / 原来源=空（本报告关联到S7） | the instructions | perform | the operations described herein |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #10 / 原来源=S7 | They | may be implemented as | instructions |
| #11 / 原来源=S7 | the instructions | may be read by | a computing platform |
| #30 / 原来源=S7 | instructions | are stored on | a machine-readable medium |
| #31 / 原来源=S7 | the instructions | may be executed by | a computing platform |
| #32 / 原来源=S7 | the instructions | perform | the operations described herein |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G18 | #10 / 1.000000 | #10 / 1.000000 |
| G19 | #30 / 1.000000 | #30 / 1.000000 |
| G20 | 未配对 | 未配对 |
| G21 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S7"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S7",
      "triple_indices": [
        10,
        30
      ],
      "text_b": "They may be implemented as instructions. Instructions are stored on a machine-readable medium.",
      "generation_status": "generated",
      "text_a": "They may be implemented as instructions stored on a machine-readable medium, which may be read and executed by a computing platform to perform the operations described herein.",
      "unique_to_text_a": [
        "The original includes that the instructions may be read and executed by a computing platform to perform the operations described herein. The reconstruction omits this information entirely."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**同一次输入中的 UNASSIGNED 对象（完整原文，独立于本句）**

以下对象在实际JSON中是同级的独立分组；把它放在这里便于人工核查，不表示反馈agent输入时已将它归入本句。内容可能涉及其他源句，保留全部差异，不筛选或改挂到本句。

```json
{
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        11,
        14,
        31,
        32,
        34
      ],
      "text_b": "The instructions may be read by a computing platform. Repeated use of the phrase \"in one embodiment,\" may refer to the same embodiment. The instructions may be executed by a computing platform. The instructions perform the operations described herein. Repeated use of the phrase \"in an exemplary embodiment,\" may refer to the same embodiment.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [
        "The instructions may be read by a computing platform.",
        "The instructions may be executed by a computing platform.",
        "The instructions perform the operations described herein.",
        "Repeated use of the phrase \"in one embodiment\" may refer to the same embodiment.",
        "Repeated use of the phrase \"in an exemplary embodiment\" may refer to the same embodiment."
      ],
      "comparison_status": "compared"
    }
```

doc0/S7和S9对象自身的`unique_to_text_b`均为`[]`；五条B侧差异在UNASSIGNED对象内，并同时出现在顶层B侧汇总数组（带`[UNASSIGNED]`前缀）。其中instructions相关三条与S7有关，may refer相关两条与S9有关；这是本报告的人工解释，不是原始分组。

**本轮反馈动作**：replace 原#11；replace 原#31；replace 原#32。

**Gold差距及反馈未发现/未修好的原因**

五条实际SPO已齐。读/执行以instructions为主体，而Gold G20用medium；perform也以instructions为主体，而G21用platform。A/B差异由UNASSIGNED错位产生，三次replace只补来源。即使文字内容能在全文找到，也未形成Gold要求的关系；这里属于主体选择、目的关系差距。

### doc0/S8：差异提示的让步内容不属于当前Gold缺项

**源句（本轮实际输入）**

```text
While specific exemplary embodiments have been discussed, it should be understood that this is done for illustration purposes only.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G22 | this | is done for | illustration purposes |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #12 / 原来源=S8 | this | is done for | illustration purposes only |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #12 / 原来源=S8 | this | is done for | illustration purposes only |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G22 | #12 / 0.923077 | #12 / 0.923077 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S8"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S8",
      "triple_indices": [
        12
      ],
      "text_b": "This is done for illustration purposes only.",
      "generation_status": "generated",
      "text_a": "While specific exemplary embodiments have been discussed, it should be understood that this is done for illustration purposes only.",
      "unique_to_text_a": [
        "The original includes the concessive clause 'While specific exemplary embodiments have been discussed', which is completely absent in the reconstruction."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

本句唯一Gold是this / is done for / illustration purposes，预测只多only，宽松接近。A侧指出While…被省略，但当前Gold没有该让步事实。反馈不补这一提示不能据此算漏补Gold；提示有文字依据也未必有评分收益。

### doc0/S9：Gold未标的正向关系及does/do差别

**源句（本轮实际输入）**

```text
Further, repeated use of the phrase "in one embodiment," or "in an exemplary embodiment," do not necessarily refer to the same embodiment, although they may.
```

**Gold版本中的源句（存在差别）**

```text
Further, repeated use of the phrase "in one embodiment," or "in an exemplary embodiment," do not necessarily refer to the same embodiment.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G23 | repeated use of the phrase "in one embodiment," | do not necessarily refer to | the same embodiment |
| G24 | repeated use of the phrase  "in an exemplary embodiment," | do not necessarily refer to | the same embodiment |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #13 / 原来源=S9 | repeated use of the phrase "in one embodiment," | does not necessarily refer to | the same embodiment |
| #14 / 原来源=空（本报告关联到S9） | repeated use of the phrase "in one embodiment," | may refer to | the same embodiment |
| #33 / 原来源=S9 | repeated use of the phrase "in an exemplary embodiment," | does not necessarily refer to | the same embodiment |
| #34 / 原来源=空（本报告关联到S9） | repeated use of the phrase "in an exemplary embodiment," | may refer to | the same embodiment |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #13 / 原来源=S9 | repeated use of the phrase "in one embodiment," | does not necessarily refer to | the same embodiment |
| #14 / 原来源=S9 | repeated use of the phrase "in one embodiment," | may refer to | the same embodiment |
| #33 / 原来源=S9 | repeated use of the phrase "in an exemplary embodiment," | does not necessarily refer to | the same embodiment |
| #34 / 原来源=S9 | repeated use of the phrase "in an exemplary embodiment," | may refer to | the same embodiment |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G23 | #13 / 0.937500 | #13 / 0.937500 |
| G24 | #33 / 0.941176 | #33 / 0.941176 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S9"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S9",
      "triple_indices": [
        13,
        33
      ],
      "text_b": "Repeated use of the phrase \"in one embodiment,\" does not necessarily refer to the same embodiment. Repeated use of the phrase \"in an exemplary embodiment,\" does not necessarily refer to the same embodiment.",
      "generation_status": "generated",
      "text_a": "Further, repeated use of the phrase \"in one embodiment,\" or \"in an exemplary embodiment,\" do not necessarily refer to the same embodiment, although they may.",
      "unique_to_text_a": [
        "The original includes 'although they may', indicating that repeated uses of the phrases may refer to the same embodiment. The reconstruction omits this concession."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**同一次输入中的 UNASSIGNED 对象（完整原文，独立于本句）**

以下对象在实际JSON中是同级的独立分组；把它放在这里便于人工核查，不表示反馈agent输入时已将它归入本句。内容可能涉及其他源句，保留全部差异，不筛选或改挂到本句。

```json
{
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        11,
        14,
        31,
        32,
        34
      ],
      "text_b": "The instructions may be read by a computing platform. Repeated use of the phrase \"in one embodiment,\" may refer to the same embodiment. The instructions may be executed by a computing platform. The instructions perform the operations described herein. Repeated use of the phrase \"in an exemplary embodiment,\" may refer to the same embodiment.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [
        "The instructions may be read by a computing platform.",
        "The instructions may be executed by a computing platform.",
        "The instructions perform the operations described herein.",
        "Repeated use of the phrase \"in one embodiment\" may refer to the same embodiment.",
        "Repeated use of the phrase \"in an exemplary embodiment\" may refer to the same embodiment."
      ],
      "comparison_status": "compared"
    }
```

doc0/S7和S9对象自身的`unique_to_text_b`均为`[]`；五条B侧差异在UNASSIGNED对象内，并同时出现在顶层B侧汇总数组（带`[UNASSIGNED]`前缀）。其中instructions相关三条与S7有关，may refer相关两条与S9有关；这是本报告的人工解释，不是原始分组。

**本轮反馈动作**：replace 原#14；replace 原#34。

**Gold差距及反馈未发现/未修好的原因**

实际四条中两条may refer未被Gold收录；另两条does not…与Gold do not…不同。两次replace仅修来源。重建/对比围绕although they may提示内容遗漏，实际上会推动保留Gold未标的关系，不能帮助解决当前Gold粒度和用词差异。

### doc0/S10：系统包含关系全部放进了method的长尾

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #15 / 原来源=S10 | This method | may be integrated in | a variety of systems including connected cars |
| #35 / 原来源=S10 | This method | may be integrated in | a variety of systems including car sharing |
| #36 / 原来源=S10 | This method | may be integrated in | a variety of systems including rental car services |
| #37 / 原来源=S10 | This method | may be integrated in | a variety of systems including maintenance |
| #38 / 原来源=S10 | This method | may be integrated in | a variety of systems including factory services |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #15 / 原来源=S10 | This method | may be integrated in | a variety of systems including connected cars |
| #35 / 原来源=S10 | This method | may be integrated in | a variety of systems including car sharing |
| #36 / 原来源=S10 | This method | may be integrated in | a variety of systems including rental car services |
| #37 / 原来源=S10 | This method | may be integrated in | a variety of systems including maintenance |
| #38 / 原来源=S10 | This method | may be integrated in | a variety of systems including factory services |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G25 | #37 / 0.909091 | #37 / 0.909091 |
| G26 | 未配对 | 未配对 |
| G27 | 未配对 | 未配对 |
| G28 | 未配对 | 未配对 |
| G29 | 未配对 | 未配对 |
| G30 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc0 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S10"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S10",
      "triple_indices": [
        15,
        35,
        36,
        37,
        38
      ],
      "text_b": "This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance, and factory services.",
      "generation_status": "generated",
      "text_a": "This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

五条实际SPO全部以This method为主体，尾部分别是systems including某一系统。Gold要求一条method integrated in systems及五条systems include对象。重建可以完整列出五个对象，对比为空；这确认存在嵌套关系未独立抽取，且当前五条主体层级不符，不能仅机械增加一个三元组解决。

### doc1/S1：唯一真正新增的Gold关系

**源句（本轮实际输入）**

```text
A further aspect provides a meaningful capture of the congestion level information enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G0 | a further aspect | provides | a meaningful capture of the congestion level information |
| G1 | a meaningful capture of the congestion level information | enables | appropriate congestion mitigation measures |
| G2 | congestion mitigation measures | are for example according to | the severeness of the congestion |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | A further aspect | provides | a meaningful capture of the congestion level information |
| #1 / 原来源=空（本报告关联到S1） | a meaningful capture of the congestion level information | enables | appropriate congestion mitigation measures |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | A further aspect | provides | a meaningful capture of the congestion level information |
| #1 / 原来源=S1 | a meaningful capture of the congestion level information | enables | appropriate congestion mitigation measures |
| #31 / 原来源=S1 | appropriate congestion mitigation measures | are for example according to | the severeness of the congestion |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G0 | #0 / 1.000000 | #0 / 1.000000 |
| G1 | #1 / 1.000000；来源为空 | #1 / 1.000000 |
| G2 | 未配对 | #31 / 0.962963 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S1"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S1",
      "triple_indices": [
        0
      ],
      "text_b": "A further aspect provides a meaningful capture of the congestion level information.",
      "generation_status": "generated",
      "text_a": "A further aspect provides a meaningful capture of the congestion level information enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion.",
      "unique_to_text_a": [
        "enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**同一次输入中的 UNASSIGNED 对象（完整原文，独立于本句）**

以下对象在实际JSON中是同级的独立分组；把它放在这里便于人工核查，不表示反馈agent输入时已将它归入本句。内容可能涉及其他源句，保留全部差异，不筛选或改挂到本句。

```json
{
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        1
      ],
      "text_b": "A meaningful capture of the congestion level information enables appropriate congestion mitigation measures.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：add 原#新增；replace 原#1。

**Gold差距及反馈未发现/未修好的原因**

新增#31严重程度关系实际匹配G2，配对F1=0.962963；appropriate使其仍非严格匹配。#1仅修来源。该句说明差异包含真正未表达的关系时，反馈能够补充；这次成功没有推广到其他结构性遗漏。

### doc1/S2：一个长尾中保留了三个Gold关系

**源句（本轮实际输入）**

```text
A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G3 | a congestion | may be detected based on | said congestion value |
| G4 | said minimum bandwidth demand | exceeds | the measured traffic per time |
| G5 | the measured traffic per time | is over | a given time span |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #2 / 原来源=S2 | A congestion | may be detected | based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #2 / 原来源=S2 | A congestion | may be detected | based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G3 | #2 / 0.444444 | #2 / 0.444444 |
| G4 | 未配对 | 未配对 |
| G5 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S2"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S2",
      "triple_indices": [
        2
      ],
      "text_b": "A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.",
      "generation_status": "generated",
      "text_a": "A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际只有#2，长尾包含检测依据、需求exceeds流量及流量over时间。Gold G4/G5没有独立三元组。重建能接近原句，对比为空；“文字覆盖”不会暴露独立关系缺口，当前反馈prompt又把已有字段内的关系展开归给拆分阶段。

### doc1/S3：缺少Gold的means that连接

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S3 | The term "part" in connection with the term "network" | is to be understood | in a broad sense |
| #4 / 原来源=S3 | part of the network | can be | any real or imaginary fraction of the network |
| #18 / 原来源=S3 | part of the network | can be | any real or imaginary portion of the network |
| #19 / 原来源=S3 | part of the network | can be | any real or imaginary component of the network |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S3 | The term "part" in connection with the term "network" | is to be understood | in a broad sense |
| #4 / 原来源=S3 | part of the network | can be | any real or imaginary fraction of the network |
| #18 / 原来源=S3 | part of the network | can be | any real or imaginary portion of the network |
| #19 / 原来源=S3 | part of the network | can be | any real or imaginary component of the network |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G6 | #3 / 0.941176 | #3 / 0.941176 |
| G7 | 未配对 | 未配对 |
| G8 | #4 / 1.000000 | #4 / 1.000000 |
| G9 | #18 / 0.888889 | #18 / 0.888889 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S3"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S3",
      "triple_indices": [
        3,
        4,
        18,
        19
      ],
      "text_b": "The term \"part\" in connection with the term \"network\" is to be understood in a broad sense. Part of the network can be any real or imaginary fraction, portion, or component of the network.",
      "generation_status": "generated",
      "text_a": "The term \"part\" in connection with the term \"network\" is to be understood in a broad sense, meaning that part of the network can be any real or imaginary fraction, portion or component of the network.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际四条包括broad sense及fraction/portion/component，但没有G7的term / means that / part of the network。重建保留定义含义，比较为空，因而没有提示缺少Gold单列的释义连接。这里不是看条目数就能发现的问题：预测数与Gold数相同，关系仍不同。

### doc1/S4：并列客体拆得比Gold更细

**源句（本轮实际输入）**

```text
Most eNBs use variants of proportional-fair scheduling, where cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G10 | most eNBs | use | variants of proportional-fair scheduling |
| G11 | cell capacity | fluctuates depending on | time-variant radio conditions and scheduling assignments |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S4 | Most eNBs | use | variants of proportional-fair scheduling |
| #6 / 原来源=S4 | cell capacity | fluctuates depending on | time-variant radio conditions |
| #20 / 原来源=S4 | cell capacity | fluctuates depending on | scheduling assignments |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S4 | Most eNBs | use | variants of proportional-fair scheduling |
| #6 / 原来源=S4 | cell capacity | fluctuates depending on | time-variant radio conditions |
| #20 / 原来源=S4 | cell capacity | fluctuates depending on | scheduling assignments |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G10 | #5 / 1.000000 | #5 / 1.000000 |
| G11 | #6 / 0.842105 | #6 / 0.842105 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S4"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S4",
      "triple_indices": [
        5,
        6,
        20
      ],
      "text_b": "Most eNBs use variants of proportional-fair scheduling. Cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.",
      "generation_status": "generated",
      "text_a": "Most eNBs use variants of proportional-fair scheduling, where cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

cell capacity的两条分别指向radio conditions和scheduling assignments，Gold把它们放在同一尾实体。重建把两项合回一句，差异为空；三条预测对应两条Gold，多出的粒度影响精确率，新增不会解决。

### doc1/S5：多重并列被展开成八条，Gold只有四条

**源句（本轮实际输入）**

```text
While the invention has been illustrated and described in detail in the drawings and foregoing description, such illustration and description are to be considered illustrative or exemplary and not restrictive.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G12 | the invention | has been illustrated in detail in | the drawings and foregoing description |
| G13 | the invention | has been described in detail in | the drawings and foregoing description |
| G14 | such illustration and description | are to be considered | illustrative or exemplary |
| G15 | such illustration and description | are to be considered not | restrictive |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=S5 | the invention | has been illustrated | in detail in the drawings |
| #8 / 原来源=S5 | such illustration | is to be considered | illustrative or exemplary |
| #21 / 原来源=S5 | the invention | has been illustrated | in detail in the foregoing description |
| #22 / 原来源=S5 | the invention | has been described | in detail in the drawings |
| #23 / 原来源=S5 | the invention | has been described | in detail in the foregoing description |
| #24 / 原来源=S5 | such illustration | is to be considered | not restrictive |
| #25 / 原来源=S5 | such description | is to be considered | illustrative or exemplary |
| #26 / 原来源=S5 | such description | is to be considered | not restrictive |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=S5 | the invention | has been illustrated | in detail in the drawings |
| #8 / 原来源=S5 | such illustration | is to be considered | illustrative or exemplary |
| #21 / 原来源=S5 | the invention | has been illustrated | in detail in the foregoing description |
| #22 / 原来源=S5 | the invention | has been described | in detail in the drawings |
| #23 / 原来源=S5 | the invention | has been described | in detail in the foregoing description |
| #24 / 原来源=S5 | such illustration | is to be considered | not restrictive |
| #25 / 原来源=S5 | such description | is to be considered | illustrative or exemplary |
| #26 / 原来源=S5 | such description | is to be considered | not restrictive |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G12 | #21 / 0.666667 | #21 / 0.666667 |
| G13 | #23 / 0.666667 | #23 / 0.666667 |
| G14 | #8 / 0.800000 | #8 / 0.800000 |
| G15 | #24 / 0.666667 | #24 / 0.666667 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S5"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S5",
      "triple_indices": [
        7,
        8,
        21,
        22,
        23,
        24,
        25,
        26
      ],
      "text_b": "The invention has been illustrated and described in detail in the drawings and in the foregoing description. Such illustration is to be considered illustrative or exemplary and not restrictive. Such description is to be considered illustrative or exemplary and not restrictive.",
      "generation_status": "generated",
      "text_a": "While the invention has been illustrated and described in detail in the drawings and foregoing description, such illustration and description are to be considered illustrative or exemplary and not restrictive.",
      "unique_to_text_a": [
        "While (expressing contrast)"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

illustrated/described与drawings/description展开成四条，illustration/description又分别展开评价，共八条；Gold采用四条更长的字段组合。重建可还原全部内容，差异仅指While。实际问题是Gold粒度及否定词字段位置，不能将While提示当成核心漏抽。

### doc1/S6：主要是冠词和大小写

**源句（本轮实际输入）**

```text
At least one embodiment has the advantage of capturing of congestion levels in such a way that congestion mitigation measures can be reliably performed.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G16 | at least one embodiment | has the advantage of | capturing of congestion levels |
| G17 | capturing of congestion levels | is in such a way that | congestion mitigation measures can be reliably performed |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #9 / 原来源=S6 | At least one embodiment | has the advantage of | capturing of congestion levels |
| #27 / 原来源=S6 | the capturing of congestion levels | is in such a way that | congestion mitigation measures can be reliably performed |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #9 / 原来源=S6 | At least one embodiment | has the advantage of | capturing of congestion levels |
| #27 / 原来源=S6 | the capturing of congestion levels | is in such a way that | congestion mitigation measures can be reliably performed |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G16 | #9 / 1.000000 | #9 / 1.000000 |
| G17 | #27 / 0.971429 | #27 / 0.971429 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S6"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S6",
      "triple_indices": [
        9,
        27
      ],
      "text_b": "At least one embodiment has the advantage of capturing of congestion levels. The capturing of congestion levels is in such a way that congestion mitigation measures can be reliably performed.",
      "generation_status": "generated",
      "text_a": "At least one embodiment has the advantage of capturing of congestion levels in such a way that congestion mitigation measures can be reliably performed.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条关系都已表达。#9的At least与Gold at least、#27主体多the影响严格匹配，宽松接近；重建和比较不报告这些同义形式差别。此处没有证据表明还缺独立事实。

### doc1/S7：主要是句首大小写

**源句（本轮实际输入）**

```text
Said congestion value may be adapted via a transformation function, wherein said transformation function amends at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G18 | said congestion value | may be adapted via | a transformation function |
| G19 | said transformation function | amends | at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #10 / 原来源=S7 | Said congestion value | may be adapted via | a transformation function |
| #11 / 原来源=S7 | said transformation function | amends | at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #10 / 原来源=S7 | Said congestion value | may be adapted via | a transformation function |
| #11 / 原来源=S7 | said transformation function | amends | at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G18 | #10 / 1.000000 | #10 / 1.000000 |
| G19 | #11 / 1.000000 | #11 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S7"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S7",
      "triple_indices": [
        10,
        11
      ],
      "text_b": "Said congestion value may be adapted via a transformation function. Said transformation function amends at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve.",
      "generation_status": "generated",
      "text_a": "Said congestion value may be adapted via a transformation function, wherein said transformation function amends at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条Gold均有对应关系，#10 Said与Gold said影响严格匹配，#11内容一致。没有文本差异及反馈操作符合语义覆盖情况；这类严格差距需要输出规范化目标，不是补事实。

### doc1/S8：否定关系和介词的字段位置不同

**源句（本轮实际输入）**

```text
Although specific terms are employed herein, they are used in a generic and descriptive sense only and not for purposes of limitation.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G20 | they | are used in | a generic and descriptive sense |
| G21 | they | are not for purposes of | limitation |
| G22 | specific terms | are employed | herein |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #12 / 原来源=S8 | specific terms | are employed | herein |
| #13 / 原来源=S8 | they | are used | in a generic and descriptive sense only |
| #28 / 原来源=S8 | they | are used | not for purposes of limitation |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #12 / 原来源=S8 | specific terms | are employed | herein |
| #13 / 原来源=S8 | they | are used | in a generic and descriptive sense only |
| #28 / 原来源=S8 | they | are used | not for purposes of limitation |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G20 | #13 / 0.842105 | #13 / 0.842105 |
| G21 | #28 / 0.400000 | #28 / 0.400000 |
| G22 | #12 / 1.000000 | #12 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S8"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S8",
      "triple_indices": [
        12,
        13,
        28
      ],
      "text_b": "Specific terms are employed herein. They are used in a generic and descriptive sense only and not for purposes of limitation.",
      "generation_status": "generated",
      "text_a": "Although specific terms are employed herein, they are used in a generic and descriptive sense only and not for purposes of limitation.",
      "unique_to_text_a": [
        "Although (expressing concession)"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#28写they / are used / not for purposes of limitation，Gold G21写they / are not for purposes of / limitation；#13也把in留在tail。重建文字自然，但不能显示SPO边界，比较只提示Although而没有指出Gold所需否定关系字段。即使没有缺词，仍有明确可修的关系形式差距。

### doc1/S9：profiles依赖operator的关系未独立表达

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #14 / 原来源=S9 | This | enhances | the flexibility of the congestion value |
| #15 / 原来源=S9 | different operators | can use | different transformation functions or profiles |
| #16 / 原来源=S9 | the congestion level | may be based | per cell with different feedback profiles depending on the need of an operator |
| #29 / 原来源=S9 | the congestion level | may be based | per link with different feedback profiles depending on the need of an operator |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #14 / 原来源=S9 | This | enhances | the flexibility of the congestion value |
| #15 / 原来源=S9 | different operators | can use | different transformation functions or profiles |
| #16 / 原来源=S9 | the congestion level | may be based | per cell with different feedback profiles depending on the need of an operator |
| #29 / 原来源=S9 | the congestion level | may be based | per link with different feedback profiles depending on the need of an operator |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G23 | #14 / 1.000000 | #14 / 1.000000 |
| G24 | #15 / 1.000000 | #15 / 1.000000 |
| G25 | #16 / 0.705882 | #16 / 0.705882 |
| G26 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S9"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S9",
      "triple_indices": [
        14,
        15,
        16,
        29
      ],
      "text_b": "This enhances the flexibility of the congestion value. Different operators can use different transformation functions or profiles. The congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.",
      "generation_status": "generated",
      "text_a": "This enhances the flexibility of the congestion value, since different operators can use different transformation functions or profiles such that the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.",
      "unique_to_text_a": [
        "since (expressing cause)",
        "such that (expressing result/purpose)"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#16/#29长尾含profiles depending on operator，却没有G26独立关系；同时将per cell/per link拆成两条。比较只提示since/such that，没有指出内部depend on关系。反馈没有将词语已出现与独立关系已抽取区分开。

### doc1/S10：原因关系错误地保留在This的长尾

**源句（本轮实际输入）**

```text
This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G27 | this | may lead to | inaccuracy |
| G28 | inaccuracy | is due to | the varying nature of instantaneous traffic patterns |
| G29 | inaccuracy | is due to | dependence on medium- to long-term congestion situations |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #17 / 原来源=S10 | This | may lead to | inaccuracy due to the varying nature of instantaneous traffic patterns |
| #30 / 原来源=S10 | This | may lead to | inaccuracy due to dependence on medium- to long-term congestion situations for reporting |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #17 / 原来源=S10 | This | may lead to | inaccuracy due to the varying nature of instantaneous traffic patterns |
| #30 / 原来源=S10 | This | may lead to | inaccuracy due to dependence on medium- to long-term congestion situations for reporting |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G27 | #17 / 0.526316 | #17 / 0.526316 |
| G28 | 未配对 | 未配对 |
| G29 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc1 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S10"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S10",
      "triple_indices": [
        17,
        30
      ],
      "text_b": "This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and due to dependence on medium- to long-term congestion situations for reporting.",
      "generation_status": "generated",
      "text_a": "This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际两条均为This may lead to inaccuracy due to某原因。Gold要求this lead to inaccuracy及inaccuracy due to两种原因。重建内容完整、比较为空，但G28/G29没有独立对应。属于关系层级与主体切换问题，和前面的嵌套关系展开直接相关。

### doc2/S1：Even被提示，但另外两个内部关系没有被提示

**源句（本轮实际输入）**

```text
Even a small open area can present a danger when loose items are being transported in high-traffic areas.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G0 | even a small open area | can present | a danger |
| G1 | a danger | is when | loose items are being transported in high-traffic areas |
| G2 | loose items | are being transported in | high-traffic areas |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | a small open area | can present | a danger when loose items are being transported in high-traffic areas |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | a small open area | can present | a danger when loose items are being transported in high-traffic areas |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G0 | #0 / 0.615385 | #0 / 0.615385 |
| G1 | 未配对 | 未配对 |
| G2 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S1"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S1",
      "triple_indices": [
        0
      ],
      "text_b": "A small open area can present a danger when loose items are being transported in high-traffic areas.",
      "generation_status": "generated",
      "text_a": "Even a small open area can present a danger when loose items are being transported in high-traffic areas.",
      "unique_to_text_a": [
        "缺少'Even'，弱化了强调语气"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际只有一条small open area / can present / danger when…；Gold G1的danger when和G2的items transported未独立表达，G0还少Even。A侧确实指出Even，反馈未修；但更大的两个独立关系缺口未进入差异提示。这里只补Even不能解决主要召回差距。

### doc2/S2：目的关系被改成提供结果并再次拆开

**源句（本轮实际输入）**

```text
Particularly, the application relates to a tarpaulin bracket system for mounting to a vehicle to provide a structure for attachment of a tarp.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G3 | the application | relates to | a tarpaulin bracket system |
| G4 | a tarpaulin bracket system | is for mounting to | a vehicle |
| G5 | a tarpaulin bracket system for mounting to a vehicle | is to provide | a structure for attachment of a tarp |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #1 / 原来源=S2 | the application | relates to | a tarpaulin bracket system |
| #11 / 原来源=S2 | a tarpaulin bracket system | is for mounting to | a vehicle |
| #12 / 原来源=S2 | a tarpaulin bracket system | provides | a structure |
| #13 / 原来源=S2 | the structure | is for | attachment of a tarp |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #1 / 原来源=S2 | the application | relates to | a tarpaulin bracket system |
| #11 / 原来源=S2 | a tarpaulin bracket system | is for mounting to | a vehicle |
| #12 / 原来源=S2 | a tarpaulin bracket system | provides | a structure |
| #13 / 原来源=S2 | the structure | is for | attachment of a tarp |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G3 | #1 / 1.000000 | #1 / 1.000000 |
| G4 | #11 / 1.000000 | #11 / 1.000000 |
| G5 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S2"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S2",
      "triple_indices": [
        1,
        11,
        12,
        13
      ],
      "text_b": "The application relates to a tarpaulin bracket system that is for mounting to a vehicle and provides a structure for attachment of a tarp.",
      "generation_status": "generated",
      "text_a": "Particularly, the application relates to a tarpaulin bracket system for mounting to a vehicle to provide a structure for attachment of a tarp.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#12是bracket system / provides / a structure，#13是structure / is for / attachment of a tarp；Gold G5是一条完整的system… / is to provide / structure for attachment。内容在四条中均出现，但目的谓词和字段组合不对应。重建与对比没有推动修复。这也说明条目多于Gold仍可漏掉Gold匹配。

### doc2/S3：因果链与内部修饰未形成Gold关系

**源句（本轮实际输入）**

```text
Further, the hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G6 | the hazards | is of loose items flying out of | the open-top of cargo trailers |
| G7 | the hazards of loose items flying out of the open-top of cargo trailers | has led many governing bodies to enact | strict laws |
| G8 | strict laws | is against | such open transport |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #2 / 原来源=S3 | the hazards of loose items flying out of the open-top of cargo trailers | has led | many governing bodies |
| #14 / 原来源=S3 | many governing bodies | enact | strict laws against such open transport |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #2 / 原来源=S3 | the hazards of loose items flying out of the open-top of cargo trailers | has led | many governing bodies |
| #14 / 原来源=S3 | many governing bodies | enact | strict laws against such open transport |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G6 | #13 / 0.272727；来源S2，与本句不同 | #13 / 0.272727；来源S2，与本句不同 |
| G7 | 未配对 | 未配对 |
| G8 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S3"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S3",
      "triple_indices": [
        2,
        14
      ],
      "text_b": "The hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.",
      "generation_status": "generated",
      "text_a": "Further, the hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#2把has led接到many governing bodies；#14再写bodies enact laws against…。Gold另列hazards of…、完整has led…to enact laws及laws against transport。三条Gold中两条未配对，另一条被全文评分错误地配到S2的structure is for attachment。该词面配对不能证明本句抽对；重建内容近似完整，对比为空。

### doc2/S4：主要是句首大小写

**源句（本轮实际输入）**

```text
The plurality of connectors is detachably connected to one of either the first and second cables and to each end of every bow.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G9 | the plurality of connectors | is detachably connected to | one of either the first and second cables |
| G10 | the plurality of connectors | is detachably connected to | each end of every bow |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S4 | The plurality of connectors | is detachably connected to | one of either the first and second cables |
| #15 / 原来源=S4 | The plurality of connectors | is detachably connected to | each end of every bow |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S4 | The plurality of connectors | is detachably connected to | one of either the first and second cables |
| #15 / 原来源=S4 | The plurality of connectors | is detachably connected to | each end of every bow |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G9 | #3 / 1.000000 | #3 / 1.000000 |
| G10 | #15 / 1.000000 | #15 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S4"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S4",
      "triple_indices": [
        3,
        15
      ],
      "text_b": "The plurality of connectors is detachably connected to one of either the first and second cables and to each end of every bow.",
      "generation_status": "generated",
      "text_a": "The plurality of connectors is detachably connected to one of either the first and second cables and to each end of every bow.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条连接关系完整，预测The与Gold the不同，严格匹配受影响；对比没有提示这类形式差距。无需据此添加新事实。

### doc2/S5：源位置关系藏在长主语中

**源句（本轮实际输入）**

```text
The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not as a limitation.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G11 | the matter set forth | is in | the foregoing description and accompanying drawings |
| G12 | the matter set forth | is offered by | way of illustration |
| G13 | the matter set forth | is offered not as | a limitation |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #4 / 原来源=S5 | The matter set forth in the foregoing description and accompanying drawings | is offered by way of | illustration only |
| #16 / 原来源=S5 | The matter set forth in the foregoing description and accompanying drawings | is not offered by way of | a limitation |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #4 / 原来源=S5 | The matter set forth in the foregoing description and accompanying drawings | is offered by way of | illustration only |
| #16 / 原来源=S5 | The matter set forth in the foregoing description and accompanying drawings | is not offered by way of | a limitation |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G11 | 未配对 | 未配对 |
| G12 | #4 / 0.571429 | #4 / 0.571429 |
| G13 | #16 / 0.620690 | #16 / 0.620690 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S5"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S5",
      "triple_indices": [
        4,
        16
      ],
      "text_b": "The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not by way of a limitation.",
      "generation_status": "generated",
      "text_a": "The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not as a limitation.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条都以matter set forth in description and drawings作长主语；Gold G11将matter / is in / description and drawings独立列出，预测没有该关系。其余两条的by way of与not字段边界也不同。重建保留原句文字、比较为空，未揭示内部关系及字段组织差距。

### doc2/S6：关系已拆出，但长尾仍重复限定

**源句（本轮实际输入）**

```text
The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G14 | the actual scope of the protection sought | is intended to be defined in | the following claims |
| G15 | the following claims | are viewed in | their proper perspective |
| G16 | their proper perspective | is based on | the prior art |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S6 | The actual scope of the protection sought | is intended to be defined in | the following claims |
| #17 / 原来源=S6 | the following claims | are viewed in | their proper perspective based on the prior art |
| #18 / 原来源=S6 | their proper perspective | is based on | the prior art |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S6 | The actual scope of the protection sought | is intended to be defined in | the following claims |
| #17 / 原来源=S6 | the following claims | are viewed in | their proper perspective based on the prior art |
| #18 / 原来源=S6 | their proper perspective | is based on | the prior art |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G14 | #5 / 1.000000 | #5 / 1.000000 |
| G15 | #17 / 0.782609 | #17 / 0.782609 |
| G16 | #18 / 1.000000 | #18 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S6"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S6",
      "triple_indices": [
        5,
        17,
        18
      ],
      "text_b": "The actual scope of the protection sought is intended to be defined in the following claims, which are viewed in their proper perspective based on the prior art.",
      "generation_status": "generated",
      "text_a": "The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#17把based on prior art仍放进perspective尾部，同时#18已独立表示该关系；Gold G15的尾实体更短。并非缺少based on关系，原候选应排除“漏抽”解释，主要是字段长度。比较为空、反馈未修的是表达边界，不是补漏。

### doc2/S7：目的主体和条件内部关系存在差距

**源句（本轮实际输入）**

```text
Preferably, most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G17 | most of these components | are made of | strong materials |
| G18 | most of these components made of strong materials | is to withstand | the conditions |
| G19 | the conditions | are of being atop | an open cargo area of a vehicle during transportation of goods |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #6 / 原来源=S7 | most of these components | are made of | strong materials |
| #19 / 原来源=S7 | strong materials | are to withstand | the conditions of being atop an open cargo area of a vehicle during transportation of goods |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #6 / 原来源=S7 | most of these components | are made of | strong materials |
| #19 / 原来源=S7 | strong materials | are to withstand | the conditions of being atop an open cargo area of a vehicle during transportation of goods |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G17 | #6 / 1.000000 | #6 / 1.000000 |
| G18 | #19 / 0.352941 | #19 / 0.352941 |
| G19 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S7"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S7",
      "triple_indices": [
        6,
        19
      ],
      "text_b": "Most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.",
      "generation_status": "generated",
      "text_a": "Preferably, most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.",
      "unique_to_text_a": [
        "缺少'Preferably'，弱化了优选条件"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#19以strong materials为主体表达are to withstand，Gold G18以components made of materials为主体；G19的conditions of being atop未独立抽取。比较只提示Preferably，Gold并未将该词作为独立事实；因此提示没有覆盖主要主体及嵌套结构问题。

### doc2/S8：两个目的条目没有独立的基础使用关系

**源句（本轮实际输入）**

```text
Later, a series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G20 | a series of bows | was brought into | use |
| G21 | a series of bows brought into use | is to keep the tarpaulin from lying in | direct contact with goods in the truck trailer |
| G22 | a series of bows brought into use | is to prevent | water accumulation |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=S8 | a series of bows | was brought into use to keep | the tarpaulin from lying in direct contact with goods in the truck trailer |
| #20 / 原来源=S8 | a series of bows | was brought into use to prevent | water accumulation |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=S8 | a series of bows | was brought into use to keep | the tarpaulin from lying in direct contact with goods in the truck trailer |
| #20 / 原来源=S8 | a series of bows | was brought into use to prevent | water accumulation |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G20 | 未配对 | 未配对 |
| G21 | #7 / 0.608696 | #7 / 0.608696 |
| G22 | #20 / 0.666667 | #20 / 0.666667 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S8"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S8",
      "triple_indices": [
        7,
        20
      ],
      "text_b": "A series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.",
      "generation_status": "generated",
      "text_a": "Later, a series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.",
      "unique_to_text_a": [
        "缺少时间状语'Later'"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际两条都是bows / was brought into use to keep或prevent / …。Gold另有bows brought into use基础关系，并以完整bows brought into use作目的主体。比较只提示Later，Gold不要求单列Later；主要差距是基础关系缺少独立条目及字段边界。

### doc2/S9：本句已严格匹配

**源句（本轮实际输入）**

```text
Additionally, the motorized system doesn't always extend far enough to cover the entire open-top cargo hold.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G23 | the motorized system | doesn't always extend far enough to cover | the entire open-top cargo hold |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #8 / 原来源=S9 | the motorized system | doesn't always extend far enough to cover | the entire open-top cargo hold |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #8 / 原来源=S9 | the motorized system | doesn't always extend far enough to cover | the entire open-top cargo hold |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G23 | #8 / 1.000000 | #8 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S9"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S9",
      "triple_indices": [
        8
      ],
      "text_b": "The motorized system doesn't always extend far enough to cover the entire open-top cargo hold.",
      "generation_status": "generated",
      "text_a": "Additionally, the motorized system doesn't always extend far enough to cover the entire open-top cargo hold.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

唯一预测与Gold一致，比较没有提示、反馈没有修改，无需作为反馈未增长的问题。

### doc2/S10：第二条谓词缺少are

**源句（本轮实际输入）**

```text
A first set of left and right pulleys are attached at the front with a second set of left and right pulleys attached at the rear of the cargo hold.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G24 | a first set of left and right pulleys | are attached at | the front |
| G25 | a second set of left and right pulleys | are attached at | the rear of the cargo hold |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #9 / 原来源=S10 | A first set of left and right pulleys | are attached at | the front |
| #10 / 原来源=S10 | a second set of left and right pulleys | attached at | the rear of the cargo hold |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #9 / 原来源=S10 | A first set of left and right pulleys | are attached at | the front |
| #10 / 原来源=S10 | a second set of left and right pulleys | attached at | the rear of the cargo hold |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G24 | #9 / 1.000000 | #9 / 1.000000 |
| G25 | #10 / 0.969697 | #10 / 0.969697 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc2 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S10"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S10",
      "triple_indices": [
        9,
        10
      ],
      "text_b": "A first set of left and right pulleys are attached at the front, and a second set of left and right pulleys are attached at the rear of the cargo hold.",
      "generation_status": "generated",
      "text_a": "A first set of left and right pulleys are attached at the front with a second set of left and right pulleys attached at the rear of the cargo hold.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

第一条只有A/a大小写差别，第二条attached at相对Gold are attached at缺are。重建会把谓词组织成自然句，比较没有提示SPO中的语法缺项，因此没有修正。属于已有三元组修复空间，不是拆分问题。

### doc3/S1：主要是句首大小写

**源句（本轮实际输入）**

```text
The present invention relates to a rubber composite comprising rubber, oil and a combination of powdered additives, as well as a process for manufacturing same.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G0 | the present invention | relates to | a rubber composite |
| G1 | a rubber composite | comprises | rubber |
| G2 | a rubber composite | comprises | oil |
| G3 | a rubber composite | comprises | a combination of powdered additives |
| G4 | the present invention | relates to | a process for manufacturing same |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | The present invention | relates to | a rubber composite |
| #1 / 原来源=S1 | The present invention | relates to | a process for manufacturing same |
| #2 / 原来源=S1 | a rubber composite | comprises | rubber |
| #19 / 原来源=S1 | a rubber composite | comprises | oil |
| #20 / 原来源=S1 | a rubber composite | comprises | a combination of powdered additives |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | The present invention | relates to | a rubber composite |
| #1 / 原来源=S1 | The present invention | relates to | a process for manufacturing same |
| #2 / 原来源=S1 | a rubber composite | comprises | rubber |
| #19 / 原来源=S1 | a rubber composite | comprises | oil |
| #20 / 原来源=S1 | a rubber composite | comprises | a combination of powdered additives |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G0 | #0 / 1.000000 | #0 / 1.000000 |
| G1 | #2 / 1.000000 | #2 / 1.000000 |
| G2 | #19 / 1.000000 | #19 / 1.000000 |
| G3 | #20 / 1.000000 | #20 / 1.000000 |
| G4 | #1 / 1.000000 | #1 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S1"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S1",
      "triple_indices": [
        0,
        1,
        2,
        19,
        20
      ],
      "text_b": "The present invention relates to a rubber composite and a process for manufacturing same. The rubber composite comprises rubber, oil, and a combination of powdered additives.",
      "generation_status": "generated",
      "text_a": "The present invention relates to a rubber composite comprising rubber, oil and a combination of powdered additives, as well as a process for manufacturing same.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

五条关系都已抽取；两个The present invention与Gold the present invention大小写不同，其他成分关系完整。比较没有指出此类严格格式差别。

### doc3/S2：名词化事件内部的incorporated into没有拆出

**源句（本轮实际输入）**

```text
The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G5 | the incorporation of granulated recycled tire rubber into bitumen | aimed to improve | the mechanical behavior of bituminous mixtures |
| G6 | granulated recycled tire rubber | is incorporated into | bitumen |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S2 | The incorporation of granulated recycled tire rubber into bitumen | aimed to improve | the mechanical behavior of bituminous mixtures |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S2 | The incorporation of granulated recycled tire rubber into bitumen | aimed to improve | the mechanical behavior of bituminous mixtures |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G5 | #3 / 1.000000 | #3 / 1.000000 |
| G6 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S2"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S2",
      "triple_indices": [
        3
      ],
      "text_b": "The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.",
      "generation_status": "generated",
      "text_a": "The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

只有#3整句aimed to improve；Gold G6 rubber / is incorporated into / bitumen埋在主语incorporation of…into…里。重建和源文接近、差异为空，反馈未发现独立关系缺口。

### doc3/S3：拆了高低温修饰，却没有抽出binders in条件

**源句（本轮实际输入）**

```text
In this connection, the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G7 | the properties of the asphalt bitumen-based binders in high and low temperature conditions | are of | a decisive importance |
| G8 | the asphalt bitumen-based binders | are in | high temperature conditions |
| G9 | the asphalt bitumen-based binders | are in | low temperature conditions |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #4 / 原来源=S3 | the properties of the asphalt bitumen-based binders in high temperature conditions | are of | a decisive importance |
| #21 / 原来源=S3 | the properties of the asphalt bitumen-based binders in low temperature conditions | are of | a decisive importance |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #4 / 原来源=S3 | the properties of the asphalt bitumen-based binders in high temperature conditions | are of | a decisive importance |
| #21 / 原来源=S3 | the properties of the asphalt bitumen-based binders in low temperature conditions | are of | a decisive importance |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G7 | #4 / 0.941176 | #4 / 0.941176 |
| G8 | 未配对 | 未配对 |
| G9 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S3"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S3",
      "triple_indices": [
        4,
        21
      ],
      "text_b": "The properties of the asphalt bitumen-based binders in high temperature conditions and in low temperature conditions are of a decisive importance.",
      "generation_status": "generated",
      "text_a": "In this connection, the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条预测均是properties…high/low temperature / are of / importance。Gold还要binders / are in / high及low conditions。两个内部关系都未形成独立三元组，且重要性关系被重复拆开；重建合回完整表达，对比为空。

### doc3/S4：being形式与Gold关系字段不同

**源句（本轮实际输入）**

```text
The rubber has an internal structure, being characterized by open cellular structure containing pores that are connected to one another and form an interconnected network; and an external surface, being the outmost surface of the rubber particles.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G10 | the rubber | has | an internal structure |
| G11 | an internal structure | is characterized by | open cellular structure |
| G12 | open cellular structure | contains | pores |
| G13 | pores | are connected to | one another |
| G14 | pores | form | an interconnected network |
| G15 | the rubber | has | an external surface |
| G16 | external surface | is the outmost surface of | the rubber particles |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S4 | The rubber | has | an internal structure |
| #6 / 原来源=S4 | The rubber | has | an external surface |
| #7 / 原来源=S4 | an internal structure | being characterized by | open cellular structure |
| #8 / 原来源=S4 | pores | are connected to | one another |
| #9 / 原来源=S4 | pores | form | an interconnected network |
| #10 / 原来源=S4 | an external surface | being | the outmost surface of the rubber particles |
| #22 / 原来源=S4 | open cellular structure | contains | pores |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S4 | The rubber | has | an internal structure |
| #6 / 原来源=S4 | The rubber | has | an external surface |
| #7 / 原来源=S4 | an internal structure | being characterized by | open cellular structure |
| #8 / 原来源=S4 | pores | are connected to | one another |
| #9 / 原来源=S4 | pores | form | an interconnected network |
| #10 / 原来源=S4 | an external surface | being | the outmost surface of the rubber particles |
| #22 / 原来源=S4 | open cellular structure | contains | pores |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G10 | #5 / 1.000000 | #5 / 1.000000 |
| G11 | #7 / 0.888889 | #7 / 0.888889 |
| G12 | #22 / 1.000000 | #22 / 1.000000 |
| G13 | #8 / 1.000000 | #8 / 1.000000 |
| G14 | #9 / 1.000000 | #9 / 1.000000 |
| G15 | #6 / 1.000000 | #6 / 1.000000 |
| G16 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S4"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S4",
      "triple_indices": [
        5,
        6,
        7,
        8,
        9,
        10,
        22
      ],
      "text_b": "The rubber has an internal structure and an external surface. The internal structure is characterized by open cellular structure, which contains pores. The pores are connected to one another and form an interconnected network. The external surface is the outmost surface of the rubber particles.",
      "generation_status": "generated",
      "text_a": "The rubber has an internal structure, being characterized by open cellular structure containing pores that are connected to one another and form an interconnected network; and an external surface, being the outmost surface of the rubber particles.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

七条数量足够，但#10 external surface / being / outmost surface…与G16 is the outmost surface of / rubber particles不对应，未匹配；#7 being characterized by与Gold is characterized by也不同。重建可自动组织成通顺语句，比较没有暴露关系字段的非限定形式。

### doc3/S5：free of oil只出现在定义的尾实体

**源句（本轮实际输入）**

```text
The term oil-dry thus stands to mean that the external surface, namely the out-most layer of the rubber composite, is substantially, or completely, free of oil.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G17 | the term oil-dry | stands to mean that | the external surface is substantially, or completely, free of oil. |
| G18 | the external surface | is namely | the out-most layer of the rubber composite |
| G19 | the external surface | is substantially, or completely, free of | oil |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #11 / 原来源=S5 | The term oil-dry | stands to mean that | the external surface is substantially, or completely, free of oil |
| #23 / 原来源=S5 | the external surface | is namely | the out-most layer of the rubber composite |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #11 / 原来源=S5 | The term oil-dry | stands to mean that | the external surface is substantially, or completely, free of oil |
| #23 / 原来源=S5 | the external surface | is namely | the out-most layer of the rubber composite |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G17 | #11 / 0.941176 | #11 / 0.941176 |
| G18 | #23 / 1.000000 | #23 / 1.000000 |
| G19 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S5"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S5",
      "triple_indices": [
        11,
        23
      ],
      "text_b": "The term oil-dry stands to mean that the external surface is substantially, or completely, free of oil. The external surface is namely the out-most layer of the rubber composite.",
      "generation_status": "generated",
      "text_a": "The term oil-dry thus stands to mean that the external surface, namely the out-most layer of the rubber composite, is substantially, or completely, free of oil.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条为oil-dry定义和external surface namely；G19 external surface / is…free of / oil未独立抽取。重建完整表达定义内容，比较为空。这是明确的已有文字、缺少独立关系，按当前反馈职责边界容易被跳过。

### doc3/S6：When条件写进每个头实体，缺独立形状关系

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #12 / 原来源=S6 | When the particles are of non-spheroid shape, the term | refers to | the average equivalent diameter of the particle |
| #24 / 原来源=S6 | When the particles are of non-spheroid shape, the average equivalent diameter of the particle | is namely | the diameter of an equivalent spherical particle |
| #25 / 原来源=S6 | When the particles are of non-spheroid shape, the diameter of an equivalent spherical particle | is based on | the longest dimension of the particle |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #12 / 原来源=S6 | When the particles are of non-spheroid shape, the term | refers to | the average equivalent diameter of the particle |
| #24 / 原来源=S6 | When the particles are of non-spheroid shape, the average equivalent diameter of the particle | is namely | the diameter of an equivalent spherical particle |
| #25 / 原来源=S6 | When the particles are of non-spheroid shape, the diameter of an equivalent spherical particle | is based on | the longest dimension of the particle |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G20 | 未配对 | 未配对 |
| G21 | #12 / 0.758621 | #12 / 0.758621 |
| G22 | #24 / 0.820513 | #24 / 0.820513 |
| G23 | #25 / 0.820513 | #25 / 0.820513 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S6"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S6",
      "triple_indices": [
        12,
        24,
        25
      ],
      "text_b": "When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle. The average equivalent diameter of the particle is namely the diameter of an equivalent spherical particle. The diameter of an equivalent spherical particle is based on the longest dimension of the particle.",
      "generation_status": "generated",
      "text_a": "When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle, namely the diameter of an equivalent spherical particle based on the longest dimension of the particle.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

实际三条头实体都带When particles…，Gold G20单列particles are of shape，其余三条用短主体。保留条件符合当前提示词，但不符合该Gold字段划分；重建看起来完整，比较为空。评分以Gold为准，不能把保留条件称为本轮有效提升。

### doc3/S7：目的已有，prior to关系没有独立抽出

**源句（本轮实际输入）**

```text
In some embodiments, the process further comprises a pre-step of grinding the rubber prior to employing the process of this invention to reduce the particles to a desired size.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G24 | the process | comprises | a pre-step of grinding the rubber |
| G25 | a pre-step of grinding the rubber | is prior to | employing the process of this invention |
| G26 | a pre-step of grinding the rubber prior to employing the process of this invention | is to reduce the particles to | a desired size |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #13 / 原来源=S7 | the process | further comprises | a pre-step of grinding the rubber prior to employing the process of this invention |
| #14 / 原来源=空（本报告关联到S7） | a pre-step of grinding the rubber prior to employing the process of this invention | aims to reduce | the particles to a desired size |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #13 / 原来源=S7 | the process | further comprises | a pre-step of grinding the rubber prior to employing the process of this invention |
| #14 / 原来源=空（本报告关联到S7） | a pre-step of grinding the rubber prior to employing the process of this invention | aims to reduce | the particles to a desired size |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G24 | #13 / 0.666667 | #13 / 0.666667 |
| G25 | 未配对 | 未配对 |
| G26 | #14 / 0.826087；来源为空 | #14 / 0.826087；来源为空 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S7"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S7",
      "triple_indices": [
        13
      ],
      "text_b": "The process further comprises a pre-step of grinding the rubber prior to employing the process of this invention.",
      "generation_status": "generated",
      "text_a": "In some embodiments, the process further comprises a pre-step of grinding the rubber prior to employing the process of this invention to reduce the particles to a desired size.",
      "unique_to_text_a": [
        "In some embodiments",
        "to reduce the particles to a desired size"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**同一次输入中的 UNASSIGNED 对象（完整原文，独立于本句）**

以下对象在实际JSON中是同级的独立分组；把它放在这里便于人工核查，不表示反馈agent输入时已将它归入本句。内容可能涉及其他源句，保留全部差异，不筛选或改挂到本句。

```json
{
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        14
      ],
      "text_b": "A pre-step of grinding the rubber prior to employing the process of this invention aims to reduce the particles to a desired size.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [
        "A pre-step of grinding the rubber prior to employing the process of this invention aims to reduce the particles to a desired size."
      ],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#14确实是pre-step… / aims to reduce / particles to desired size，仍无来源编号；因此差异中to reduce缺失是分组错位，不是真内容遗漏。G25的pre-step prior to process埋在#13尾部和#14头部，未独立表达；反馈既未修来源，也未展开该关系。

### doc3/S8：第二条缺少Gold的all the possible

**源句（本轮实际输入）**

```text
Accordingly, the description of a range should be considered to have specifically disclosed all the possible sub-ranges as well as individual numerical values within that range.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G27 | the description of a range | should be considered to have specifically disclosed | all the possible sub-ranges |
| G28 | the description of a range | should be considered to have specifically disclosed | all the possible individual numerical values within that range |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #15 / 原来源=S8 | the description of a range | should be considered to have specifically disclosed | all the possible sub-ranges |
| #26 / 原来源=S8 | the description of a range | should be considered to have specifically disclosed | individual numerical values within that range |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #15 / 原来源=S8 | the description of a range | should be considered to have specifically disclosed | all the possible sub-ranges |
| #26 / 原来源=S8 | the description of a range | should be considered to have specifically disclosed | individual numerical values within that range |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G27 | #15 / 1.000000 | #15 / 1.000000 |
| G28 | #26 / 0.923077 | #26 / 0.923077 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S8"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S8",
      "triple_indices": [
        15,
        26
      ],
      "text_b": "The description of a range should be considered to have specifically disclosed all the possible sub-ranges and individual numerical values within that range.",
      "generation_status": "generated",
      "text_a": "Accordingly, the description of a range should be considered to have specifically disclosed all the possible sub-ranges as well as individual numerical values within that range.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两个关系均存在，#26尾部是individual numerical values within that range，比Gold少all the possible。重建/比较未提示量化范围差异，反馈未改；这是已有三元组限定词修复空间。

### doc3/S9：比较层级及材料内部关系全部未对齐

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #16 / 原来源=S9 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures with RAR |
| #27 / 原来源=S9 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures without RAR |
| #28 / 原来源=S9 | It | is clearly the lowest value as compared with | traditional SMA mixtures with highly modified bitumen and fibres |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #16 / 原来源=S9 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures with RAR |
| #27 / 原来源=S9 | It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures without RAR |
| #28 / 原来源=S9 | It | is clearly the lowest value as compared with | traditional SMA mixtures with highly modified bitumen and fibres |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G29 | 未配对 | 未配对 |
| G30 | 未配对 | 未配对 |
| G31 | 未配对 | 未配对 |
| G32 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S9"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S9",
      "triple_indices": [
        16,
        27,
        28
      ],
      "text_b": "It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures with RAR, tradition Asphalt Rubber gap graded mixtures without RAR, and traditional SMA mixtures with highly modified bitumen and fibres.",
      "generation_status": "generated",
      "text_a": "It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even compared with traditional SMA mixtures with highly modified bitumen and fibres.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

三个预测都以It为主体，将lowest value as compared with放进relation；Gold用一条It is clearly lowest value、两条lowest value compared with及一条SMA mixtures with材料。不是仅缺一条：本句四条Gold都未配对，主体和字段层级需重新组织。重建能完整陈述比较内容，差异为空，是明显的文字覆盖掩盖关系错误。

### doc3/S10：同义字段划分在Gold中占两行

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #17 / 原来源=S10 | the range | is given as such merely for | convenience |
| #18 / 原来源=S10 | the range | should not be construed as | an inflexible limitation on the scope of the invention |
| #29 / 原来源=S10 | the range | is given as such merely for | brevity |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #17 / 原来源=S10 | the range | is given as such merely for | convenience |
| #18 / 原来源=S10 | the range | should not be construed as | an inflexible limitation on the scope of the invention |
| #29 / 原来源=S10 | the range | is given as such merely for | brevity |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G33 | #17 / 1.000000 | #17 / 1.000000 |
| G34 | #29 / 1.000000 | #29 / 1.000000 |
| G35 | #18 / 1.000000 | #18 / 1.000000 |
| G36 | 未配对 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc3 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S10"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S10",
      "triple_indices": [
        17,
        18,
        29
      ],
      "text_b": "The range is given as such merely for convenience and brevity, and should not be construed as an inflexible limitation on the scope of the invention.",
      "generation_status": "generated",
      "text_a": "It should be noted that the range is given as such merely for convenience and brevity and should not be construed as an inflexible limitation on the scope of the invention.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

三条预测已分别给出convenience、brevity及scope limitation，G36还用另一字段划分表达同一限制。全文一对一评测剩一条Gold未配对。应记为Gold标注粒度要求，而不是凭空缺了一项新事实；语义去重机制自然不会再生成该近重复条目。

### doc4/S1：主要是句首大小写

**源句（本轮实际输入）**

```text
The disclosure is directed to a communication path managing method and a communication path managing system.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G0 | the disclosure | is directed to | a communication path managing method |
| G1 | the disclosure | is directed to | a communication path managing system |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | The disclosure | is directed to | a communication path managing method |
| #11 / 原来源=S1 | The disclosure | is directed to | a communication path managing system |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #0 / 原来源=S1 | The disclosure | is directed to | a communication path managing method |
| #11 / 原来源=S1 | The disclosure | is directed to | a communication path managing system |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G0 | #0 / 1.000000 | #0 / 1.000000 |
| G1 | #11 / 1.000000 | #11 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S1"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S1",
      "triple_indices": [
        0,
        11
      ],
      "text_b": "The disclosure is directed to a communication path managing method and a communication path managing system.",
      "generation_status": "generated",
      "text_a": "The disclosure is directed to a communication path managing method and a communication path managing system.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条关系完整，The/the造成严格差异；不需要补充新事实。

### doc4/S2：本句完整，但共享条目影响全文一对一计数

**源句（本轮实际输入）**

```text
At least one of the communication paths for the vehicle is selected according to the evaluation items based on the item importance information.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G2 | at least one of the communication paths for the vehicle | is selected according to | the evaluation items |
| G3 | the evaluation items | are based on | the item importance information |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #1 / 原来源=S2 | At least one of the communication paths for the vehicle | is selected according to | the evaluation items |
| #12 / 原来源=S2,S3 | the evaluation items | are based on | the item importance information |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #1 / 原来源=S2 | At least one of the communication paths for the vehicle | is selected according to | the evaluation items |
| #12 / 原来源=S2,S3 | the evaluation items | are based on | the item importance information |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G2 | #1 / 1.000000 | #1 / 1.000000 |
| G3 | #12 / 1.000000 | #12 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S2"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S2",
      "triple_indices": [
        1,
        12
      ],
      "text_b": "At least one of the communication paths for the vehicle is selected according to the evaluation items. The evaluation items are based on the item importance information.",
      "generation_status": "generated",
      "text_a": "At least one of the communication paths for the vehicle is selected according to the evaluation items based on the item importance information.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

#12关联S2/S3，Gold在两个源句各有一条相同的evaluation items based on importance。全文评测每个预测只用一次，#12不能同时满足两行Gold。不能把两个来源编号当作两条预测；文本比较会认为两句都有内容。

### doc4/S3：同一关系跨两句出现，但预测只保留一个实例

**源句（本轮实际输入）**

```text
The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G4 | the selecting unit | is for selecting | at least one of the communication paths for the vehicle |
| G5 | selecting at least one of the communication paths for the vehicle | is according to | the evaluation items |
| G6 | the evaluation items | are based on | the item importance information |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #2 / 原来源=S3 | The selecting unit | is for selecting | at least one of the communication paths for the vehicle |
| #12 / 原来源=S2,S3 | the evaluation items | are based on | the item importance information |
| #13 / 原来源=S3 | The selecting unit | selects according to | the evaluation items based on the item importance information |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #2 / 原来源=S3 | The selecting unit | is for selecting | at least one of the communication paths for the vehicle |
| #12 / 原来源=S2,S3 | the evaluation items | are based on | the item importance information |
| #13 / 原来源=S3 | The selecting unit | selects according to | the evaluation items based on the item importance information |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G4 | #2 / 1.000000 | #2 / 1.000000 |
| G5 | #13 / 0.437500 | #13 / 0.437500 |
| G6 | #16 / 0.357143；来源S7，与本句不同 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S3"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S3",
      "triple_indices": [
        2,
        12,
        13
      ],
      "text_b": "The selecting unit is for selecting at least one of the communication paths for the vehicle. The evaluation items are based on the item importance information. The selecting unit selects according to the evaluation items based on the item importance information.",
      "generation_status": "generated",
      "text_a": "The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

本句G6与S2的G3完全相同，#12给了两个源句编号；全文只可匹配一次。本句#13的selecting unit selects according to…与G5的selecting…is according to…也有主体、字段差别。反馈前G6曾被无关S7#16以弱词面重合配上，修订后该替代配对消失。这里没有跨句事实，只是相同事实在两句出现与评测计数不一致。

### doc4/S4：本句已严格匹配

**源句（本轮实际输入）**

```text
Besides, the performance of some of the communication path PH may be limited to a particular geographical range.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G7 | the performance of some of the communication path PH | may be limited to | a particular geographical range |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S4 | the performance of some of the communication path PH | may be limited to | a particular geographical range |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #3 / 原来源=S4 | the performance of some of the communication path PH | may be limited to | a particular geographical range |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G7 | #3 / 1.000000 | #3 / 1.000000 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S4"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S4",
      "triple_indices": [
        3
      ],
      "text_b": "The performance of some of the communication path PH may be limited to a particular geographical range.",
      "generation_status": "generated",
      "text_a": "Besides, the performance of some of the communication path PH may be limited to a particular geographical range.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

唯一三元组与Gold一致，比较为空、反馈不修改合理。

### doc4/S5：Gold使用更长的主体限定

**源句（本轮实际输入）**

```text
The shaded area located at the lower side of the dotted line L2 belongs the good category of the available bandwidth.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G8 | the shaded area | is located at | the lower side of the dotted line L2 |
| G9 | the shaded area located at the lower side of the dotted line L2 | belongs | the good category of the available bandwidth |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #4 / 原来源=S5 | The shaded area | belongs | the good category of the available bandwidth |
| #14 / 原来源=S5 | The shaded area | is located at | the lower side of the dotted line L2 |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #4 / 原来源=S5 | The shaded area | belongs | the good category of the available bandwidth |
| #14 / 原来源=S5 | The shaded area | is located at | the lower side of the dotted line L2 |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G8 | #14 / 1.000000 | #14 / 1.000000 |
| G9 | #4 / 0.687500 | #4 / 0.687500 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S5"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S5",
      "triple_indices": [
        4,
        14
      ],
      "text_b": "The shaded area belongs the good category of the available bandwidth. The shaded area is located at the lower side of the dotted line L2.",
      "generation_status": "generated",
      "text_a": "The shaded area located at the lower side of the dotted line L2 belongs the good category of the available bandwidth.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

belongs条目以The shaded area作主体，Gold G9把located at lower side…也放入主体；该限定另由#14独立表示。内容不缺，但字段长度及大小写不同。对比自然语言不会提示为贴近Gold而重复限定。

### doc4/S6：目的词放在tail而Gold放在relation

**源句（本轮实际输入）**

```text
Both of the routing path latency and the connection keeping ability are taken into consideration to find out the best communication path PH.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G10 | the routing path latency | is taken into consideration to find out | the best communication path PH |
| G11 | the connection keeping ability | is taken into consideration to find out | the best communication path PH |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S6 | the routing path latency | is taken into consideration | to find out the best communication path PH |
| #15 / 原来源=S6 | the connection keeping ability | is taken into consideration | to find out the best communication path PH |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #5 / 原来源=S6 | the routing path latency | is taken into consideration | to find out the best communication path PH |
| #15 / 原来源=S6 | the connection keeping ability | is taken into consideration | to find out the best communication path PH |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G10 | #5 / 0.812500 | #5 / 0.812500 |
| G11 | #15 / 0.812500 | #15 / 0.812500 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S6"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S6",
      "triple_indices": [
        5,
        15
      ],
      "text_b": "The routing path latency is taken into consideration to find out the best communication path PH. The connection keeping ability is taken into consideration to find out the best communication path PH.",
      "generation_status": "generated",
      "text_a": "Both of the routing path latency and the connection keeping ability are taken into consideration to find out the best communication path PH.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：无操作。

**Gold差距及反馈未发现/未修好的原因**

两条预测都是is taken into consideration / to find out best path，Gold将to find out并入relation。主要是SPO边界差异，重建文字相同、比较为空，反馈没有调整。

### doc4/S7：一项关系修好，同时一项主体被改长

**源句（本轮实际输入）**

```text
All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G12 | all of the evaluation items EV | is worse than | the standard thresholds E0 |
| G13 | all of the evaluation items EV | is of | each of the communication paths PH in the third group G3 |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #6 / 原来源=S7 | All of the evaluation items EV | is worse than | the standard thresholds E0 |
| #16 / 原来源=S7 | the evaluation items EV | are associated with | each of the communication paths PH in the third group G3 |
| #17 / 原来源=S7 | each of the communication paths PH | is in | the third group G3 |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #6 / 原来源=S7 | All of the evaluation items EV of each of the communication paths PH in the third group G3 | is worse than | the standard thresholds E0 |
| #16 / 原来源=S7 | the evaluation items EV | are of | each of the communication paths PH in the third group G3 |
| #17 / 原来源=S7 | each of the communication paths PH | is in | the third group G3 |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G12 | #6 / 1.000000 | #6 / 0.684211 |
| G13 | #17 / 0.451613 | #16 / 0.888889 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S7"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S7",
      "triple_indices": [
        6,
        16,
        17
      ],
      "text_b": "All of the evaluation items EV is worse than the standard thresholds E0. The evaluation items EV are associated with each of the communication paths PH in the third group G3. Each of the communication paths PH is in the third group G3.",
      "generation_status": "generated",
      "text_a": "All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：replace 原#6；replace 原#16。

**Gold差距及反馈未发现/未修好的原因**

#16 are of更接近G13，#6长主体更远离G12。全文匹配还发生与S3、S8之间的词面竞争，不能将局部配对改善直接等同于整体增益。没有A/B差异提示，这些修改来自反馈额外检查；逐组净效应见阶段一。

### doc4/S8：反馈删除了独立类别关系

**源句（本轮实际输入）**

```text
In the good category of the available bandwidth, the value of the routing path latency is equal to or lower than 500 kbps.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G14 | the value of the routing path latency | is equal to or lower than | 500 kbps |
| G15 | the value of the routing path latency | is equal to or lower than 500 kbps in | the good category of the available bandwidth |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=空（本报告关联到S8） | the value of the routing path latency | is equal to or lower than | 500 kbps |
| #18 / 原来源=空（本报告关联到S8） | the value of the routing path latency | is in | the good category of the available bandwidth |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #7 / 原来源=S8 | the value of the routing path latency in the good category of the available bandwidth | is equal to or lower than | 500 kbps |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G14 | #7 / 1.000000；来源为空 | #7 / 0.789474 |
| G15 | #18 / 0.820513；来源为空 | #17 / 0.285714；来源S7，与本句不同 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S8"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S8",
      "triple_indices": [],
      "text_b": "",
      "generation_status": "empty_triples",
      "text_a": "In the good category of the available bandwidth, the value of the routing path latency is equal to or lower than 500 kbps.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**同一次输入中的 UNASSIGNED 对象（完整原文，独立于本句）**

以下对象在实际JSON中是同级的独立分组；把它放在这里便于人工核查，不表示反馈agent输入时已将它归入本句。内容可能涉及其他源句，保留全部差异，不筛选或改挂到本句。

```json
{
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        7,
        8,
        9,
        10,
        18,
        19,
        20,
        21
      ],
      "text_b": "The value of the routing path latency is equal to or lower than 500 kbps. The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims. The value of the routing path latency is equal to or lower than 50 ms. The value of the routing path latency is in the good category of the available bandwidth. The examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by their equivalents. The value of the routing path latency is in the good category of the routing path latency.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：remove 原#18；replace 原#7。

**Gold差距及反馈未发现/未修好的原因**

最终只剩#7长头阈值关系；G14由严格匹配变成部分匹配，G15竟被S7#17弱词面配对。必须按源句核查才能看见实际缺少类别条目，不能因G15在全文匹配表中“已匹配”就判抽对。该退化由反馈制造，见阶段一。

### doc4/S9：合并claims/equivalents且原有字段差距未解决

**源句（本轮实际输入）**

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

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #8 / 原来源=空（本报告关联到S9） | The specification | is intended to be considered as | exemplary only |
| #9 / 原来源=空（本报告关联到S9） | a true scope of the disclosure | is indicated by | the following claims |
| #19 / 原来源=空（本报告关联到S9） | The examples | are intended to be considered as | exemplary only |
| #20 / 原来源=空（本报告关联到S9） | a true scope of the disclosure | is indicated by | their equivalents |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #8 / 原来源=S9 | The specification | is intended to be considered as | exemplary only |
| #9 / 原来源=S9 | a true scope of the disclosure | is indicated by | the following claims and their equivalents |
| #18 / 原来源=S9 | The examples | are intended to be considered as | exemplary only |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G16 | #19 / 0.666667；来源为空 | #18 / 0.666667 |
| G17 | 未配对 | 未配对 |
| G18 | #9 / 0.761905；来源为空 | #9 / 0.666667 |
| G19 | #20 / 0.736842；来源为空 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S9"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S9",
      "triple_indices": [],
      "text_b": "",
      "generation_status": "empty_triples",
      "text_a": "It is intended that the specification and examples be considered as exemplary only, with a true scope of the disclosure being indicated by the following claims and their equivalents.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**同一次输入中的 UNASSIGNED 对象（完整原文，独立于本句）**

以下对象在实际JSON中是同级的独立分组；把它放在这里便于人工核查，不表示反馈agent输入时已将它归入本句。内容可能涉及其他源句，保留全部差异，不筛选或改挂到本句。

```json
{
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        7,
        8,
        9,
        10,
        18,
        19,
        20,
        21
      ],
      "text_b": "The value of the routing path latency is equal to or lower than 500 kbps. The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims. The value of the routing path latency is equal to or lower than 50 ms. The value of the routing path latency is in the good category of the available bandwidth. The examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by their equivalents. The value of the routing path latency is in the good category of the routing path latency.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：remove 原#20；replace 原#8；replace 原#9；replace 原#19。

**Gold差距及反馈未发现/未修好的原因**

最终三条中claims/equivalents被并在#9，G19失去匹配；G17的exemplary only with scope关系也没有独立表达。specification/examples的主体组合与Gold不同，scope与disclosure主语也不同。比较原本为空，反馈却认为and应整体表达，既没解决旧差距，又制造新损失。

### doc4/S10：反馈删除了第二个独立类别关系

**源句（本轮实际输入）**

```text
In the good category of the routing path latency, the value of the routing path latency is equal to or lower than 50 ms.
```

**对应Gold**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| G20 | the value of the routing path latency | is equal to or lower than | 50 ms |
| G21 | the value of the routing path latency | is equal to or lower than 50 ms in | the good category of the routing path latency |

**反馈前完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #10 / 原来源=空（本报告关联到S10） | the value of the routing path latency | is equal to or lower than | 50 ms |
| #21 / 原来源=空（本报告关联到S10） | the value of the routing path latency | is in | the good category of the routing path latency |

**反馈后完整相关三元组（编号属于本阶段）**

| 编号 | head | relation | tail |
| --- | --- | --- | --- |
| #10 / 原来源=S10 | the value of the routing path latency in the good category of the routing path latency | is equal to or lower than | 50 ms |

**整篇一对一评分中本句Gold的实际对应**

| Gold | 反馈前预测 / 配对F1 | 反馈后预测 / 配对F1 |
| --- | --- | --- |
| G20 | #10 / 1.000000；来源为空 | #10 / 0.769231 |
| G21 | #21 / 0.829268；来源为空 | 未配对 |

**反馈 agent 实际收到的本句对象（原文摘录）**

位置：doc4 的 `<text_difference_json>.sentence_differences` 中 `sentence_id="S10"` 的对象。下面保留附件中的字段、值和原始数组，不是把源文、重建、差异重新拼成的新输入。完整文档输入见文末附录。

```json
{
      "sentence_id": "S10",
      "triple_indices": [],
      "text_b": "",
      "generation_status": "empty_triples",
      "text_a": "In the good category of the routing path latency, the value of the routing path latency is equal to or lower than 50 ms.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**同一次输入中的 UNASSIGNED 对象（完整原文，独立于本句）**

以下对象在实际JSON中是同级的独立分组；把它放在这里便于人工核查，不表示反馈agent输入时已将它归入本句。内容可能涉及其他源句，保留全部差异，不筛选或改挂到本句。

```json
{
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        7,
        8,
        9,
        10,
        18,
        19,
        20,
        21
      ],
      "text_b": "The value of the routing path latency is equal to or lower than 500 kbps. The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims. The value of the routing path latency is equal to or lower than 50 ms. The value of the routing path latency is in the good category of the available bandwidth. The examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by their equivalents. The value of the routing path latency is in the good category of the routing path latency.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
```

**本轮反馈动作**：remove 原#21；replace 原#10。

**Gold差距及反馈未发现/未修好的原因**

最终只剩#10长头阈值关系，G20失去严格匹配，G21未配对。源句分组空、UNASSIGNED有内容的定位问题与删除合并的决策问题都存在；修来源本身不会恢复被删独立关系。

## 后续修改应解决的具体问题

第一，重建前补齐可确定的来源，避免把已有内容变成A侧缺失/B侧新增；本轮反馈后仍有doc3#14无来源。第二，直接对源句与实际SPO检查主体、关系方向、目的/能力/否定及必要限定，不能只看重建是否通顺。第三，对已经报告的真实差异记录处理结果，核实是否修复或有依据地保留，重点防止doc0/S2这样的提示未落实。第四，明确反馈是否承担已有长字段中独立关系的补抽；如果继续排除这一类，其增长范围自然有限。

Gold的选择性标注、重复行、主动/被动及长短字段划分也会影响评分。改善这些差距需要统一抽取标注规则并用固定Gold验证，单靠增加拆分数量或禁止所有remove都不够。本次只更新分析，不修改抽取程序。

完整阶段SPO和匹配现已齐全；后续若要追溯来源最初丢失位置、核对实际prompt或导出是否忠实，需要原始revision_result、splitting、feedback调用文件，而不是再次索要完整三元组。

## 附录：五篇反馈 agent 输入四完整原文

以下逐篇保留附件中代码块内的完整文字：前导语、`<text_difference_json>`标签、顶层汇总、全部sentence_differences对象及结束标签。正文只是摘录其中相关对象；这里是本次分析采用的完整输入四原文。

### doc0：输入四原文

```text
文本A是源文本，文本B由当前三元组重建。源句指带 sentence_id 的原文句子。
unique_to_text_a 提示可能遗漏的信息，unique_to_text_b 提示可能缺乏源文支持的信息。
sentence_differences 按源句提供重建、差异及相关三元组的全局 index；重建失败、
比较失败或来源未定位均不代表没有问题。UNASSIGNED 表示来源尚未确定的条目。
差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。
<text_difference_json>
{
  "unique_to_text_a": [
    "[S2] The original sentence indicates a purpose chain: query the ECU to identify the compromised PUF component in order to determine where the compromise is located. The reconstruction lists query, identify, and determine as parallel actions, losing the purpose relationship.",
    "[S7] The original includes that the instructions may be read and executed by a computing platform to perform the operations described herein. The reconstruction omits this information entirely.",
    "[S8] The original includes the concessive clause 'While specific exemplary embodiments have been discussed', which is completely absent in the reconstruction.",
    "[S9] The original includes 'although they may', indicating that repeated uses of the phrases may refer to the same embodiment. The reconstruction omits this concession."
  ],
  "unique_to_text_b": [
    "[UNASSIGNED] The instructions may be read by a computing platform.",
    "[UNASSIGNED] The instructions may be executed by a computing platform.",
    "[UNASSIGNED] The instructions perform the operations described herein.",
    "[UNASSIGNED] Repeated use of the phrase \"in one embodiment\" may refer to the same embodiment.",
    "[UNASSIGNED] Repeated use of the phrase \"in an exemplary embodiment\" may refer to the same embodiment."
  ],
  "sentence_differences": [
    {
      "sentence_id": "S1",
      "triple_indices": [
        0,
        1,
        2,
        16,
        17,
        18
      ],
      "text_b": "Such elements are well known in the art and do not facilitate a better understanding of the present disclosure, and a discussion of such elements may not be provided herein. Such operations are well known in the art and do not facilitate a better understanding of the present disclosure, and a discussion of such operations may not be provided herein.",
      "generation_status": "generated",
      "text_a": "Because such elements and operations are well known in the art, and because they do not facilitate a better understanding of the present disclosure, a discussion of such elements and operations may not be provided herein.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S2",
      "triple_indices": [
        3,
        4,
        19,
        20
      ],
      "text_b": "The ECUs may include PUF components. The controller may query the ECU, identify which PUF component is compromised, and determine where in the sub-system the compromise is located.",
      "generation_status": "generated",
      "text_a": "As the ECUs may include PUF components, the controller may query the ECU to identify which PUF component is compromised, in order to determine where in the sub-system the compromise is located.",
      "unique_to_text_a": [
        "The original sentence indicates a purpose chain: query the ECU to identify the compromised PUF component in order to determine where the compromise is located. The reconstruction lists query, identify, and determine as parallel actions, losing the purpose relationship."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S3",
      "triple_indices": [
        5,
        6,
        21,
        22
      ],
      "text_b": "Validation of the vehicle identity ensures the integrity of all of the components and ensures information generated by any of the components. The components make up the vehicle. Any of the components generate information.",
      "generation_status": "generated",
      "text_a": "In this manner, validation of the vehicle identity ensures the integrity of all of the components that make up the vehicle as well as information generated by any of the components that make up the vehicle.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S4",
      "triple_indices": [
        7,
        23,
        24
      ],
      "text_b": "The term computer readable medium is meant to refer to any machine-readable medium (automated data medium). Any machine-readable medium (automated data medium) stores data in a format. The format is readable by a mechanical device.",
      "generation_status": "generated",
      "text_a": "Further, the term computer readable medium is meant to refer to any machine-readable medium (automated data medium) capable of storing data in a format readable by a mechanical device.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S5",
      "triple_indices": [
        8,
        25,
        26
      ],
      "text_b": "Each specific element includes all technical equivalents. All technical equivalents operate in a similar manner and accomplish a similar purpose.",
      "generation_status": "generated",
      "text_a": "It is to be understood that each specific element includes all technical equivalents that operate in a similar manner to accomplish a similar purpose.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S6",
      "triple_indices": [
        9,
        27,
        28,
        29
      ],
      "text_b": "Embodiments of the invention may also be implemented in hardware, firmware, software, or a combination of hardware, firmware, and software.",
      "generation_status": "generated",
      "text_a": "Embodiments of the invention may also be implemented in one or a combination of hardware, firmware, and software.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S7",
      "triple_indices": [
        10,
        30
      ],
      "text_b": "They may be implemented as instructions. Instructions are stored on a machine-readable medium.",
      "generation_status": "generated",
      "text_a": "They may be implemented as instructions stored on a machine-readable medium, which may be read and executed by a computing platform to perform the operations described herein.",
      "unique_to_text_a": [
        "The original includes that the instructions may be read and executed by a computing platform to perform the operations described herein. The reconstruction omits this information entirely."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S8",
      "triple_indices": [
        12
      ],
      "text_b": "This is done for illustration purposes only.",
      "generation_status": "generated",
      "text_a": "While specific exemplary embodiments have been discussed, it should be understood that this is done for illustration purposes only.",
      "unique_to_text_a": [
        "The original includes the concessive clause 'While specific exemplary embodiments have been discussed', which is completely absent in the reconstruction."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S9",
      "triple_indices": [
        13,
        33
      ],
      "text_b": "Repeated use of the phrase \"in one embodiment,\" does not necessarily refer to the same embodiment. Repeated use of the phrase \"in an exemplary embodiment,\" does not necessarily refer to the same embodiment.",
      "generation_status": "generated",
      "text_a": "Further, repeated use of the phrase \"in one embodiment,\" or \"in an exemplary embodiment,\" do not necessarily refer to the same embodiment, although they may.",
      "unique_to_text_a": [
        "The original includes 'although they may', indicating that repeated uses of the phrases may refer to the same embodiment. The reconstruction omits this concession."
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S10",
      "triple_indices": [
        15,
        35,
        36,
        37,
        38
      ],
      "text_b": "This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance, and factory services.",
      "generation_status": "generated",
      "text_a": "This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        11,
        14,
        31,
        32,
        34
      ],
      "text_b": "The instructions may be read by a computing platform. Repeated use of the phrase \"in one embodiment,\" may refer to the same embodiment. The instructions may be executed by a computing platform. The instructions perform the operations described herein. Repeated use of the phrase \"in an exemplary embodiment,\" may refer to the same embodiment.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [
        "The instructions may be read by a computing platform.",
        "The instructions may be executed by a computing platform.",
        "The instructions perform the operations described herein.",
        "Repeated use of the phrase \"in one embodiment\" may refer to the same embodiment.",
        "Repeated use of the phrase \"in an exemplary embodiment\" may refer to the same embodiment."
      ],
      "comparison_status": "compared"
    }
  ]
}
</text_difference_json>
```

### doc1：输入四原文

```text
文本A是源文本，文本B由当前三元组重建。源句指带 sentence_id 的原文句子。
unique_to_text_a 提示可能遗漏的信息，unique_to_text_b 提示可能缺乏源文支持的信息。
sentence_differences 按源句提供重建、差异及相关三元组的全局 index；重建失败、
比较失败或来源未定位均不代表没有问题。UNASSIGNED 表示来源尚未确定的条目。
差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。
<text_difference_json>
{
  "unique_to_text_a": [
    "[S1] enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion",
    "[S5] While (expressing contrast)",
    "[S8] Although (expressing concession)",
    "[S9] since (expressing cause)",
    "[S9] such that (expressing result/purpose)"
  ],
  "unique_to_text_b": [],
  "sentence_differences": [
    {
      "sentence_id": "S1",
      "triple_indices": [
        0
      ],
      "text_b": "A further aspect provides a meaningful capture of the congestion level information.",
      "generation_status": "generated",
      "text_a": "A further aspect provides a meaningful capture of the congestion level information enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion.",
      "unique_to_text_a": [
        "enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S2",
      "triple_indices": [
        2
      ],
      "text_b": "A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.",
      "generation_status": "generated",
      "text_a": "A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S3",
      "triple_indices": [
        3,
        4,
        18,
        19
      ],
      "text_b": "The term \"part\" in connection with the term \"network\" is to be understood in a broad sense. Part of the network can be any real or imaginary fraction, portion, or component of the network.",
      "generation_status": "generated",
      "text_a": "The term \"part\" in connection with the term \"network\" is to be understood in a broad sense, meaning that part of the network can be any real or imaginary fraction, portion or component of the network.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S4",
      "triple_indices": [
        5,
        6,
        20
      ],
      "text_b": "Most eNBs use variants of proportional-fair scheduling. Cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.",
      "generation_status": "generated",
      "text_a": "Most eNBs use variants of proportional-fair scheduling, where cell capacity fluctuates depending on time-variant radio conditions and scheduling assignments.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S5",
      "triple_indices": [
        7,
        8,
        21,
        22,
        23,
        24,
        25,
        26
      ],
      "text_b": "The invention has been illustrated and described in detail in the drawings and in the foregoing description. Such illustration is to be considered illustrative or exemplary and not restrictive. Such description is to be considered illustrative or exemplary and not restrictive.",
      "generation_status": "generated",
      "text_a": "While the invention has been illustrated and described in detail in the drawings and foregoing description, such illustration and description are to be considered illustrative or exemplary and not restrictive.",
      "unique_to_text_a": [
        "While (expressing contrast)"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S6",
      "triple_indices": [
        9,
        27
      ],
      "text_b": "At least one embodiment has the advantage of capturing of congestion levels. The capturing of congestion levels is in such a way that congestion mitigation measures can be reliably performed.",
      "generation_status": "generated",
      "text_a": "At least one embodiment has the advantage of capturing of congestion levels in such a way that congestion mitigation measures can be reliably performed.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S7",
      "triple_indices": [
        10,
        11
      ],
      "text_b": "Said congestion value may be adapted via a transformation function. Said transformation function amends at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve.",
      "generation_status": "generated",
      "text_a": "Said congestion value may be adapted via a transformation function, wherein said transformation function amends at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S8",
      "triple_indices": [
        12,
        13,
        28
      ],
      "text_b": "Specific terms are employed herein. They are used in a generic and descriptive sense only and not for purposes of limitation.",
      "generation_status": "generated",
      "text_a": "Although specific terms are employed herein, they are used in a generic and descriptive sense only and not for purposes of limitation.",
      "unique_to_text_a": [
        "Although (expressing concession)"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S9",
      "triple_indices": [
        14,
        15,
        16,
        29
      ],
      "text_b": "This enhances the flexibility of the congestion value. Different operators can use different transformation functions or profiles. The congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.",
      "generation_status": "generated",
      "text_a": "This enhances the flexibility of the congestion value, since different operators can use different transformation functions or profiles such that the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.",
      "unique_to_text_a": [
        "since (expressing cause)",
        "such that (expressing result/purpose)"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S10",
      "triple_indices": [
        17,
        30
      ],
      "text_b": "This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and due to dependence on medium- to long-term congestion situations for reporting.",
      "generation_status": "generated",
      "text_a": "This may lead to inaccuracy due to the varying nature of instantaneous traffic patterns and dependence on medium- to long-term congestion situations for reporting.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        1
      ],
      "text_b": "A meaningful capture of the congestion level information enables appropriate congestion mitigation measures.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
  ]
}
</text_difference_json>
```

### doc2：输入四原文

```text
文本A是源文本，文本B由当前三元组重建。源句指带 sentence_id 的原文句子。
unique_to_text_a 提示可能遗漏的信息，unique_to_text_b 提示可能缺乏源文支持的信息。
sentence_differences 按源句提供重建、差异及相关三元组的全局 index；重建失败、
比较失败或来源未定位均不代表没有问题。UNASSIGNED 表示来源尚未确定的条目。
差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。
<text_difference_json>
{
  "unique_to_text_a": [
    "[S1] 缺少'Even'，弱化了强调语气",
    "[S7] 缺少'Preferably'，弱化了优选条件",
    "[S8] 缺少时间状语'Later'"
  ],
  "unique_to_text_b": [],
  "sentence_differences": [
    {
      "sentence_id": "S1",
      "triple_indices": [
        0
      ],
      "text_b": "A small open area can present a danger when loose items are being transported in high-traffic areas.",
      "generation_status": "generated",
      "text_a": "Even a small open area can present a danger when loose items are being transported in high-traffic areas.",
      "unique_to_text_a": [
        "缺少'Even'，弱化了强调语气"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S2",
      "triple_indices": [
        1,
        11,
        12,
        13
      ],
      "text_b": "The application relates to a tarpaulin bracket system that is for mounting to a vehicle and provides a structure for attachment of a tarp.",
      "generation_status": "generated",
      "text_a": "Particularly, the application relates to a tarpaulin bracket system for mounting to a vehicle to provide a structure for attachment of a tarp.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S3",
      "triple_indices": [
        2,
        14
      ],
      "text_b": "The hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.",
      "generation_status": "generated",
      "text_a": "Further, the hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S4",
      "triple_indices": [
        3,
        15
      ],
      "text_b": "The plurality of connectors is detachably connected to one of either the first and second cables and to each end of every bow.",
      "generation_status": "generated",
      "text_a": "The plurality of connectors is detachably connected to one of either the first and second cables and to each end of every bow.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S5",
      "triple_indices": [
        4,
        16
      ],
      "text_b": "The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not by way of a limitation.",
      "generation_status": "generated",
      "text_a": "The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not as a limitation.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S6",
      "triple_indices": [
        5,
        17,
        18
      ],
      "text_b": "The actual scope of the protection sought is intended to be defined in the following claims, which are viewed in their proper perspective based on the prior art.",
      "generation_status": "generated",
      "text_a": "The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S7",
      "triple_indices": [
        6,
        19
      ],
      "text_b": "Most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.",
      "generation_status": "generated",
      "text_a": "Preferably, most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.",
      "unique_to_text_a": [
        "缺少'Preferably'，弱化了优选条件"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S8",
      "triple_indices": [
        7,
        20
      ],
      "text_b": "A series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.",
      "generation_status": "generated",
      "text_a": "Later, a series of bows was brought into use to keep the tarpaulin from lying in direct contact with goods in the truck trailer and to prevent water accumulation.",
      "unique_to_text_a": [
        "缺少时间状语'Later'"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S9",
      "triple_indices": [
        8
      ],
      "text_b": "The motorized system doesn't always extend far enough to cover the entire open-top cargo hold.",
      "generation_status": "generated",
      "text_a": "Additionally, the motorized system doesn't always extend far enough to cover the entire open-top cargo hold.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S10",
      "triple_indices": [
        9,
        10
      ],
      "text_b": "A first set of left and right pulleys are attached at the front, and a second set of left and right pulleys are attached at the rear of the cargo hold.",
      "generation_status": "generated",
      "text_a": "A first set of left and right pulleys are attached at the front with a second set of left and right pulleys attached at the rear of the cargo hold.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
  ]
}
</text_difference_json>
```

### doc3：输入四原文

```text
文本A是源文本，文本B由当前三元组重建。源句指带 sentence_id 的原文句子。
unique_to_text_a 提示可能遗漏的信息，unique_to_text_b 提示可能缺乏源文支持的信息。
sentence_differences 按源句提供重建、差异及相关三元组的全局 index；重建失败、
比较失败或来源未定位均不代表没有问题。UNASSIGNED 表示来源尚未确定的条目。
差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。
<text_difference_json>
{
  "unique_to_text_a": [
    "[S7] In some embodiments",
    "[S7] to reduce the particles to a desired size"
  ],
  "unique_to_text_b": [
    "[UNASSIGNED] A pre-step of grinding the rubber prior to employing the process of this invention aims to reduce the particles to a desired size."
  ],
  "sentence_differences": [
    {
      "sentence_id": "S1",
      "triple_indices": [
        0,
        1,
        2,
        19,
        20
      ],
      "text_b": "The present invention relates to a rubber composite and a process for manufacturing same. The rubber composite comprises rubber, oil, and a combination of powdered additives.",
      "generation_status": "generated",
      "text_a": "The present invention relates to a rubber composite comprising rubber, oil and a combination of powdered additives, as well as a process for manufacturing same.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S2",
      "triple_indices": [
        3
      ],
      "text_b": "The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.",
      "generation_status": "generated",
      "text_a": "The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S3",
      "triple_indices": [
        4,
        21
      ],
      "text_b": "The properties of the asphalt bitumen-based binders in high temperature conditions and in low temperature conditions are of a decisive importance.",
      "generation_status": "generated",
      "text_a": "In this connection, the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S4",
      "triple_indices": [
        5,
        6,
        7,
        8,
        9,
        10,
        22
      ],
      "text_b": "The rubber has an internal structure and an external surface. The internal structure is characterized by open cellular structure, which contains pores. The pores are connected to one another and form an interconnected network. The external surface is the outmost surface of the rubber particles.",
      "generation_status": "generated",
      "text_a": "The rubber has an internal structure, being characterized by open cellular structure containing pores that are connected to one another and form an interconnected network; and an external surface, being the outmost surface of the rubber particles.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S5",
      "triple_indices": [
        11,
        23
      ],
      "text_b": "The term oil-dry stands to mean that the external surface is substantially, or completely, free of oil. The external surface is namely the out-most layer of the rubber composite.",
      "generation_status": "generated",
      "text_a": "The term oil-dry thus stands to mean that the external surface, namely the out-most layer of the rubber composite, is substantially, or completely, free of oil.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S6",
      "triple_indices": [
        12,
        24,
        25
      ],
      "text_b": "When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle. The average equivalent diameter of the particle is namely the diameter of an equivalent spherical particle. The diameter of an equivalent spherical particle is based on the longest dimension of the particle.",
      "generation_status": "generated",
      "text_a": "When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle, namely the diameter of an equivalent spherical particle based on the longest dimension of the particle.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S7",
      "triple_indices": [
        13
      ],
      "text_b": "The process further comprises a pre-step of grinding the rubber prior to employing the process of this invention.",
      "generation_status": "generated",
      "text_a": "In some embodiments, the process further comprises a pre-step of grinding the rubber prior to employing the process of this invention to reduce the particles to a desired size.",
      "unique_to_text_a": [
        "In some embodiments",
        "to reduce the particles to a desired size"
      ],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S8",
      "triple_indices": [
        15,
        26
      ],
      "text_b": "The description of a range should be considered to have specifically disclosed all the possible sub-ranges and individual numerical values within that range.",
      "generation_status": "generated",
      "text_a": "Accordingly, the description of a range should be considered to have specifically disclosed all the possible sub-ranges as well as individual numerical values within that range.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S9",
      "triple_indices": [
        16,
        27,
        28
      ],
      "text_b": "It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures with RAR, tradition Asphalt Rubber gap graded mixtures without RAR, and traditional SMA mixtures with highly modified bitumen and fibres.",
      "generation_status": "generated",
      "text_a": "It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even compared with traditional SMA mixtures with highly modified bitumen and fibres.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S10",
      "triple_indices": [
        17,
        18,
        29
      ],
      "text_b": "The range is given as such merely for convenience and brevity, and should not be construed as an inflexible limitation on the scope of the invention.",
      "generation_status": "generated",
      "text_a": "It should be noted that the range is given as such merely for convenience and brevity and should not be construed as an inflexible limitation on the scope of the invention.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        14
      ],
      "text_b": "A pre-step of grinding the rubber prior to employing the process of this invention aims to reduce the particles to a desired size.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [
        "A pre-step of grinding the rubber prior to employing the process of this invention aims to reduce the particles to a desired size."
      ],
      "comparison_status": "compared"
    }
  ]
}
</text_difference_json>
```

### doc4：输入四原文

```text
文本A是源文本，文本B由当前三元组重建。源句指带 sentence_id 的原文句子。
unique_to_text_a 提示可能遗漏的信息，unique_to_text_b 提示可能缺乏源文支持的信息。
sentence_differences 按源句提供重建、差异及相关三元组的全局 index；重建失败、
比较失败或来源未定位均不代表没有问题。UNASSIGNED 表示来源尚未确定的条目。
差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。
<text_difference_json>
{
  "unique_to_text_a": [],
  "unique_to_text_b": [],
  "sentence_differences": [
    {
      "sentence_id": "S1",
      "triple_indices": [
        0,
        11
      ],
      "text_b": "The disclosure is directed to a communication path managing method and a communication path managing system.",
      "generation_status": "generated",
      "text_a": "The disclosure is directed to a communication path managing method and a communication path managing system.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S2",
      "triple_indices": [
        1,
        12
      ],
      "text_b": "At least one of the communication paths for the vehicle is selected according to the evaluation items. The evaluation items are based on the item importance information.",
      "generation_status": "generated",
      "text_a": "At least one of the communication paths for the vehicle is selected according to the evaluation items based on the item importance information.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S3",
      "triple_indices": [
        2,
        12,
        13
      ],
      "text_b": "The selecting unit is for selecting at least one of the communication paths for the vehicle. The evaluation items are based on the item importance information. The selecting unit selects according to the evaluation items based on the item importance information.",
      "generation_status": "generated",
      "text_a": "The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S4",
      "triple_indices": [
        3
      ],
      "text_b": "The performance of some of the communication path PH may be limited to a particular geographical range.",
      "generation_status": "generated",
      "text_a": "Besides, the performance of some of the communication path PH may be limited to a particular geographical range.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S5",
      "triple_indices": [
        4,
        14
      ],
      "text_b": "The shaded area belongs the good category of the available bandwidth. The shaded area is located at the lower side of the dotted line L2.",
      "generation_status": "generated",
      "text_a": "The shaded area located at the lower side of the dotted line L2 belongs the good category of the available bandwidth.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S6",
      "triple_indices": [
        5,
        15
      ],
      "text_b": "The routing path latency is taken into consideration to find out the best communication path PH. The connection keeping ability is taken into consideration to find out the best communication path PH.",
      "generation_status": "generated",
      "text_a": "Both of the routing path latency and the connection keeping ability are taken into consideration to find out the best communication path PH.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S7",
      "triple_indices": [
        6,
        16,
        17
      ],
      "text_b": "All of the evaluation items EV is worse than the standard thresholds E0. The evaluation items EV are associated with each of the communication paths PH in the third group G3. Each of the communication paths PH is in the third group G3.",
      "generation_status": "generated",
      "text_a": "All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S8",
      "triple_indices": [],
      "text_b": "",
      "generation_status": "empty_triples",
      "text_a": "In the good category of the available bandwidth, the value of the routing path latency is equal to or lower than 500 kbps.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S9",
      "triple_indices": [],
      "text_b": "",
      "generation_status": "empty_triples",
      "text_a": "It is intended that the specification and examples be considered as exemplary only, with a true scope of the disclosure being indicated by the following claims and their equivalents.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "S10",
      "triple_indices": [],
      "text_b": "",
      "generation_status": "empty_triples",
      "text_a": "In the good category of the routing path latency, the value of the routing path latency is equal to or lower than 50 ms.",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    },
    {
      "sentence_id": "UNASSIGNED",
      "triple_indices": [
        7,
        8,
        9,
        10,
        18,
        19,
        20,
        21
      ],
      "text_b": "The value of the routing path latency is equal to or lower than 500 kbps. The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims. The value of the routing path latency is equal to or lower than 50 ms. The value of the routing path latency is in the good category of the available bandwidth. The examples are intended to be considered as exemplary only. A true scope of the disclosure is indicated by their equivalents. The value of the routing path latency is in the good category of the routing path latency.",
      "generation_status": "generated",
      "text_a": "",
      "unique_to_text_a": [],
      "unique_to_text_b": [],
      "comparison_status": "compared"
    }
  ]
}
</text_difference_json>
```
