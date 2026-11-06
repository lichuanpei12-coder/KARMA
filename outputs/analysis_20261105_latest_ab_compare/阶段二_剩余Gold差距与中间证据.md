# 阶段二　剩余 Gold 差距与中间证据

分析日期 2026-11-05。A 为本次消息前 3 份附件，B 为后 3 份，均按中间阶段记录、R2 三元组和差异摘要配组。附件未提供准确运行名、模型和 Git 提交。

关联报告 · [阶段一_两次反馈变化_逐句完整对照](阶段一_两次反馈变化_逐句完整对照.md) · [阶段二_剩余Gold差距与中间证据](阶段二_剩余Gold差距与中间证据.md) · [反馈问题总结与修改建议_含三元组证据](反馈问题总结与修改建议_含三元组证据.md)

共同输入是此前 11.4 对照保存的 134 条拆分三元组。逐文档应用 A、B 已执行操作后，全部 10 份输出的 head、relation、tail 多重集与附件 R2 完全一致。这个核对覆盖条目和重复次数，原始操作索引、完整证据、请求和冲突筛选快照未提供。本文称该端点为 R2。

评估使用当前修改后 Gold 的同 5 篇 153 条，文档内按仓库词匹配做一对一分配，整体分数为五篇微平均。逐句分数用于定位，多个来源句共享的条目可在分句表重复展示，整篇只计一次。源句取自修改后数据集，差异附件只提供摘要。

## 剩余差距统计

| 检查点 | 预测数 | 宽松 P | 宽松 R | 宽松 F1 | 变化 | 严格 F1 | 未配 Gold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 拆分 | 134 | 63.92% | 60.47% | 62.15% | — | 20.21% | 50 |
| A | 138 | 62.55% | 61.03% | 61.78% | -0.37 pp | 21.31% | 48 |
| B | 131 | 67.84% | 63.68% | 65.69% | +3.55 pp | 24.65% | 48 |

两组各有 48 条 Gold 未获整篇一对一配对，配到的是哪些条目以及配对质量存在差别。弱配定义为已配对的单对 F1 ≤ 0.50，仅作人工复核标记。

## 关键源句

| 位置 | 拆分 F1 | A F1 | B F1 | 已核对现象 |
| --- | --- | --- | --- | --- |
| doc0/S2 | 91.29% | 69.40% | 77.31% | A 新增因果和目的条目，保留原有独立动作。B 替换独立查询，并在返修删除独立确定条目。两组局部 F1 均下降。 |
| doc0/S3 | 71.46% | 69.70% | 80.93% | B 删掉任一部件单独构成车辆的断言。A 修正 integrity of 的作用范围，但仍保留 any of the components 作 make up 主语。Gold 还保留了 vlidation 拼写。 |
| doc0/S4 | 83.20% | 61.60% | 78.23% | A 把 readable by 写入长尾，再删掉独立的格式可读关系。B 保留独立条目。 |
| doc0/S7 | 16.22% | 14.12% | 23.08% | 两组都识别到目的变成断言。B 把读取、执行、目的合入长条目。Gold 分列介质被读取、介质被执行及平台目的，两组仍有主体和层级差距。 |
| doc0/S10 | 0.00% | 16.67% | 24.39% | A 增加 a variety of systems，保留以 This method 为主语的具体列表项。B 把范围和例子合进一条长尾。Gold 则另用 systems 作各条 include 的主语。 |
| doc1/S5 | 65.28% | 60.75% | 60.75% | 两组都保留原有 6 条，并新增一条整句让步关系。Gold 中分列的 illustration 和 description 仍有缺口。 |
| doc1/S8 | 83.70% | 71.38% | 25.00% | B 把整句 Although 拆成两条 is despite，并把已有条目的 they 改成 specific terms。两种改动都影响局部配对。 |
| doc1/S10 | 23.26% | 0.00% | 97.37% | B 将 inaccuracy 和两条独立原因拆开。A 只把 inaccuracy due to 移到 relation，仍有字段边界差距。 |
| doc2/S2 | 66.67% | 100.00% | 98.11% | 两组均将 mounting to a vehicle / provides 修成 a tarpaulin bracket system / is to provide，恢复主语和目的。 |
| doc2/S3 | 14.12% | 42.15% | 0.00% | A 恢复 hazards 风险表达。B 保留 loose items 作独立 flying out of 的主体，并将 has led 的结果与动作分开。 |
| doc2/S5 | 40.94% | 40.94% | 55.41% | B 首轮 Replace 因空 new_triples 被整批拒绝，返修改写共同主体，再删除拆开的部分表达。 |
| doc2/S10 | 63.35% | 100.00% | 100.00% | 两组均先恢复前后两套左右滑轮，再删修正后完全等价的重复项。A 的差异摘要未列本句。 |
| doc3/S6 | 70.63% | 100.00% | 79.66% | B 的部分新条目移除了 When the particles are of non-spheroid shape 条件。核对时应分开看条件的作用域与字段边界。 |
| doc4/S2 | 100.00% | 59.65% | 100.00% | A 扩长两个路径条目的 tail，再删掉同时归于 S2/S3 的独立评价依据关系。B 保留输入。 |
| doc4/S3 | 75.90% | 42.67% | 75.90% | 与 S2 共享的评价依据条目在 A 中消失。同一条删除在整篇只计一次。 |

## 未配条目的候选怎么读

本句候选优先选三个对应字段都有交集的预测，再按配对 F1 排序。没有合格项时，表格展示重合词最多的候选及无交集字段。整篇最高合格候选一列还显示该预测是否配给了另一条 Gold。邻近候选用于定位词面与分配差距，是否表达同一事实仍需对照源句。

## doc0 · 857. Systems and methods for a cryptographically guaranteed vehicle identity.txt

### doc0 · A 未配 Gold（11 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G2 | S1 | they / do not facilitate / a better understanding of the present disclosure | A1 · such elements / do not facilitate / a better understanding of the present disclosure · 无交集字段 head · 未配 | — |
| G13 | S4 | a format / is readable by / a mechanical device | A5 · the term computer readable medium / is meant to refer to / any machine-readable medium capable of storing data in a format readable by a mechanical device · 无交集字段 head · 已配 G11 | — |
| G17 | S7 | they / may be implemented as / instructions | A8 · Embodiments of the invention / may be implemented as / instructions stored on a machine-readable medium · 无交集字段 head · 未配 | — |
| G18 | S7 | instructions / are stored on / a machine-readable medium | A8 · Embodiments of the invention / may be implemented as / instructions stored on a machine-readable medium · 无交集字段 head, relation · 未配 | — |
| G19 | S7 | a machine-readable medium / may be read by / a computing platform | A26 · instructions / may be read by / a computing platform · 无交集字段 head · 未配 | — |
| G20 | S7 | a machine-readable medium / may be executed by / a computing platform | A27 · instructions / may be executed by / a computing platform · 无交集字段 head · 未配 | — |
| G26 | S10 | a variety of systems / include / connected cars | A11 · This method / may be integrated in / connected cars · 无交集字段 head, relation · 未配 | — |
| G27 | S10 | a variety of systems / include / car sharing | A29 · This method / may be integrated in / car sharing · 无交集字段 head, relation · 未配 | — |
| G28 | S10 | a variety of systems / include / rental car services | A30 · This method / may be integrated in / rental car services · 无交集字段 head, relation · 未配 | — |
| G29 | S10 | a variety of systems / include / maintenance | A31 · This method / may be integrated in / maintenance · 无交集字段 head, relation · 未配 | — |
| G30 | S10 | a variety of systems / include / factory services | A32 · This method / may be integrated in / factory services · 无交集字段 head, relation · 未配 | — |

### doc0 · A 弱配 Gold（1 条）

| 编号 | 源句 | Gold | 预测编号 | 预测来源 | 预测 | 配对 F1 |
| --- | --- | --- | --- | --- | --- | --- |
| G23 | S9 | repeated use of the phrase "in one embodiment," / do not necessarily refer to / the same embodiment | A35 | S2 | the controller / may query the ECU to identify which PUF component is compromised, in order to determine / where in the sub-system the compromise is located | 0.146 |

### doc0 · B 未配 Gold（11 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G2 | S1 | they / do not facilitate / a better understanding of the present disclosure | B1 · such elements / do not facilitate / a better understanding of the present disclosure · 无交集字段 head · 未配 | — |
| G4 | S2 | the controller / may query / the ECU | B14 · the controller / may identify which PUF component is compromised to determine / where in the sub-system the compromise is located · F1 0.320 · 已配 G6 | B14 · F1 0.320 · 已配 G6 |
| G18 | S7 | instructions / are stored on / a machine-readable medium | B8 · They / may be implemented as / instructions stored on a machine-readable medium · 无交集字段 head, relation · 已配 G17 | — |
| G19 | S7 | a machine-readable medium / may be read by / a computing platform | B25 · instructions / may be read and executed by a computing platform to perform / the operations described herein · 无交集字段 head, tail · 未配 | B19 · F1 0.333 · 已配 G13 |
| G20 | S7 | a machine-readable medium / may be executed by / a computing platform | B25 · instructions / may be read and executed by a computing platform to perform / the operations described herein · 无交集字段 head, tail · 未配 | B19 · F1 0.333 · 已配 G13 |
| G21 | S7 | a computing platform / is to perform / the operations | B25 · instructions / may be read and executed by a computing platform to perform / the operations described herein · 无交集字段 head · 未配 | — |
| G26 | S10 | a variety of systems / include / connected cars | B11 · This method / may be integrated in / a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services · 无交集字段 head, relation · 已配 G25 | — |
| G27 | S10 | a variety of systems / include / car sharing | B11 · This method / may be integrated in / a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services · 无交集字段 head, relation · 已配 G25 | — |
| G28 | S10 | a variety of systems / include / rental car services | B11 · This method / may be integrated in / a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services · 无交集字段 head, relation · 已配 G25 | — |
| G29 | S10 | a variety of systems / include / maintenance | B11 · This method / may be integrated in / a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services · 无交集字段 head, relation · 已配 G25 | — |
| G30 | S10 | a variety of systems / include / factory services | B11 · This method / may be integrated in / a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services · 无交集字段 head, relation · 已配 G25 | — |

### doc0 · B 弱配 Gold（0 条）

该组该篇没有符合此阈值的弱配。

## doc1 · 2786. Method for providing congestion information in a network.txt

### doc1 · A 未配 Gold（10 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G2 | S1 | congestion mitigation measures / are for example according to / the severeness of the congestion | A1 · a meaningful capture of the congestion level information / enables / appropriate congestion mitigation measures, for example according to the severeness of the congestion · 无交集字段 relation · 已配 G1 | — |
| G5 | S2 | the measured traffic per time / is over / a given time span | A2 · A congestion / may be detected / based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span · 无交集字段 head, relation · 已配 G3 | A4 · F1 0.214 · 已配 G6 |
| G7 | S3 | the term "part" in connection with the term "network" / means that / part of the network | A4 · The term "part" in connection with the term "network" / is to be understood / in a broad sense · 无交集字段 relation, tail · 已配 G6 | — |
| G19 | S5 | such description / are to be considered / illustrative or exemplary | A11 · such illustration and description / are to be considered / illustrative or exemplary · F1 0.900 · 已配 G18 | A11 · F1 0.900 · 已配 G18 |
| G21 | S5 | such description / are to be considered not / restrictive | A13 · such illustration and description / are to be considered / not restrictive · F1 0.778 · 已配 G20 | A13 · F1 0.778 · 已配 G20 |
| G23 | S6 | capturing of congestion levels / is in such a way that / congestion mitigation measures can be reliably performed | A19 · capturing of congestion levels / enables / congestion mitigation measures to be reliably performed · 无交集字段 relation · 未配 | — |
| G33 | S9 | different feedback profiles / depending on / the need of an operator | A32 · different operators can use different transformation functions or profiles / results in / the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator · 无交集字段 relation · 未配 | — |
| G34 | S10 | this / may lead to / inaccuracy | A33 · This / may lead to inaccuracy due to / the varying nature of instantaneous traffic patterns · 无交集字段 tail · 未配 | — |
| G35 | S10 | inaccuracy / is due to / the varying nature of instantaneous traffic patterns | A33 · This / may lead to inaccuracy due to / the varying nature of instantaneous traffic patterns · 无交集字段 head · 未配 | — |
| G36 | S10 | inaccuracy / is due to / dependence on medium- to long-term congestion situations | A34 · This / may lead to inaccuracy due to / dependence on medium- to long-term congestion situations for reporting · 无交集字段 head · 未配 | — |

### doc1 · A 弱配 Gold（1 条）

| 编号 | 源句 | Gold | 预测编号 | 预测来源 | 预测 | 配对 F1 |
| --- | --- | --- | --- | --- | --- | --- |
| G3 | S2 | a congestion / may be detected based on / said congestion value | A2 | S2 | A congestion / may be detected / based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span | 0.444 |

### doc1 · B 未配 Gold（8 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G2 | S1 | congestion mitigation measures / are for example according to / the severeness of the congestion | B1 · a meaningful capture of the congestion level information / enables / appropriate congestion mitigation measures, for example according to the severeness of the congestion · 无交集字段 relation · 已配 G1 | — |
| G5 | S2 | the measured traffic per time / is over / a given time span | B3 · A congestion / may be detected when / said minimum bandwidth demand exceeds the measured traffic per time over a given time span · 无交集字段 head, relation · 未配 | B5 · F1 0.214 · 已配 G6 |
| G7 | S3 | the term "part" in connection with the term "network" / means that / part of the network | B5 · The term "part" in connection with the term "network" / is to be understood / in a broad sense · 无交集字段 relation, tail · 已配 G6 | — |
| G19 | S5 | such description / are to be considered / illustrative or exemplary | B12 · such illustration and description / are to be considered / illustrative or exemplary · F1 0.900 · 已配 G18 | B12 · F1 0.900 · 已配 G18 |
| G21 | S5 | such description / are to be considered not / restrictive | B14 · such illustration and description / are to be considered / not restrictive · F1 0.778 · 已配 G20 | B14 · F1 0.778 · 已配 G20 |
| G26 | S8 | they / are used in / a generic and descriptive sense | B27 · specific terms / are used / in a generic and descriptive sense only · 无交集字段 head · 未配 | — |
| G27 | S8 | they / are not for purposes of / limitation | B28 · specific terms / are not used for / purposes of limitation · 无交集字段 head · 未配 | — |
| G33 | S9 | different feedback profiles / depending on / the need of an operator | B33 · the congestion level / may be based / per cell with different feedback profiles depending on the need of an operator · 无交集字段 head, relation · 已配 G31 | — |

### doc1 · B 弱配 Gold（1 条）

| 编号 | 源句 | Gold | 预测编号 | 预测来源 | 预测 | 配对 F1 |
| --- | --- | --- | --- | --- | --- | --- |
| G25 | S7 | said transformation function / amends / at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve | B25 | S7 | said transformation function / amends at least one of / a shape of a congestion level curve | 0.500 |

## doc2 · 5921. Tarpaulin bracket system.txt

### doc2 · A 未配 Gold（6 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G1 | S1 | a danger / is when / loose items are being transported in high-traffic areas | A0 · Even a small open area / can present / a danger when loose items are being transported in high-traffic areas · 无交集字段 relation · 已配 G0 | — |
| G2 | S1 | loose items / are being transported in / high-traffic areas | A0 · Even a small open area / can present / a danger when loose items are being transported in high-traffic areas · 无交集字段 head, relation · 已配 G0 | — |
| G8 | S3 | strict laws / is against / such open transport | A4 · the hazards / has led / many governing bodies to enact strict laws against such open transport · 无交集字段 head, relation · 已配 G7 | — |
| G15 | S6 | the following claims / are viewed in / their proper perspective | A13 · the following claims / are viewed in their proper perspective based on / the prior art · 无交集字段 tail · 已配 G11 | — |
| G16 | S6 | their proper perspective / is based on / the prior art | A13 · the following claims / are viewed in their proper perspective based on / the prior art · 无交集字段 head · 已配 G11 | — |
| G20 | S8 | a series of bows / was brought into / use | A16 · a series of bows / was later brought into use to keep / the tarpaulin from lying in direct contact with goods in the truck trailer · 无交集字段 tail · 已配 G21 | — |

### doc2 · A 弱配 Gold（5 条）

| 编号 | 源句 | Gold | 预测编号 | 预测来源 | 预测 | 配对 F1 |
| --- | --- | --- | --- | --- | --- | --- |
| G6 | S3 | the hazards / is of loose items flying out of / the open-top of cargo trailers | A10 | S5 | The matter set forth in the accompanying drawings / is offered / by way of illustration only | 0.207 |
| G7 | S3 | the hazards / has led many governing bodies to enact / strict laws | A4 | S3 | the hazards / has led / many governing bodies to enact strict laws against such open transport | 0.462 |
| G11 | S5 | the matter set forth / is in / the foregoing description and accompanying drawings | A13 | S6 | the following claims / are viewed in their proper perspective based on / the prior art | 0.231 |
| G18 | S7 | most of these components made of strong materials / is to withstand / the conditions | A15 | S7 | most of these components / are to withstand / the conditions of being atop an open cargo area of a vehicle during transportation of goods | 0.444 |
| G19 | S7 | the conditions / are of being atop / an open cargo area of a vehicle during transportation of goods | A5 | S3 | the hazards / are of / loose items flying out of the open-top of cargo trailers | 0.387 |

### doc2 · B 未配 Gold（9 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G2 | S1 | loose items / are being transported in / high-traffic areas | B1 · a danger / occurs when / loose items are being transported in high-traffic areas · 无交集字段 head, relation · 已配 G1 | — |
| G6 | S3 | the hazards / is of loose items flying out of / the open-top of cargo trailers | B7 · loose items / flying out of / the open-top of cargo trailers · 无交集字段 head · 未配 | B8 · F1 0.267 · 已配 G9 |
| G7 | S3 | the hazards / has led many governing bodies to enact / strict laws | B5 · the hazards of loose items flying out of the open-top of cargo trailers / has led / many governing bodies · 无交集字段 tail · 未配 | — |
| G8 | S3 | strict laws / is against / such open transport | B6 · many governing bodies / enact / strict laws against such open transport · 无交集字段 head, relation · 未配 | — |
| G11 | S5 | the matter set forth / is in / the foregoing description and accompanying drawings | B10 · The matter set forth in the foregoing description and accompanying drawings / is offered / by way of illustration only · 无交集字段 tail · 已配 G12 | B8 · F1 0.286 · 已配 G9 |
| G15 | S6 | the following claims / are viewed in / their proper perspective | B12 · The actual scope of the protection sought / is intended to be defined / in the following claims when viewed in their proper perspective based on the prior art · 无交集字段 relation · 已配 G14 | — |
| G16 | S6 | their proper perspective / is based on / the prior art | B12 · The actual scope of the protection sought / is intended to be defined / in the following claims when viewed in their proper perspective based on the prior art · 无交集字段 head · 已配 G14 | — |
| G19 | S7 | the conditions / are of being atop / an open cargo area of a vehicle during transportation of goods | B14 · most of these components / to withstand / the conditions of being atop an open cargo area of a vehicle during transportation of goods · 无交集字段 head, relation · 已配 G18 | — |
| G20 | S8 | a series of bows / was brought into / use | B15 · a series of bows / was brought into use to keep / the tarpaulin from lying in direct contact with goods in the truck trailer · 无交集字段 tail · 已配 G21 | — |

### doc2 · B 弱配 Gold（1 条）

| 编号 | 源句 | Gold | 预测编号 | 预测来源 | 预测 | 配对 F1 |
| --- | --- | --- | --- | --- | --- | --- |
| G18 | S7 | most of these components made of strong materials / is to withstand / the conditions | B14 | S7 | most of these components / to withstand / the conditions of being atop an open cargo area of a vehicle during transportation of goods | 0.457 |

## doc3 · 6519. Rubber composite and process for obtaining same.txt

### doc3 · A 未配 Gold（13 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G1 | S1 | a rubber composite / comprises / rubber | A2 · a rubber composite / comprising / rubber · 无交集字段 relation · 未配 | — |
| G2 | S1 | a rubber composite / comprises / oil | A3 · a rubber composite / comprising / oil · 无交集字段 relation · 未配 | — |
| G3 | S1 | a rubber composite / comprises / a combination of powdered additives | A4 · a rubber composite / comprising / a combination of powdered additives · 无交集字段 relation · 未配 | — |
| G6 | S2 | granulated recycled tire rubber / is incorporated into / bitumen | A5 · The incorporation of granulated recycled tire rubber into bitumen / aimed to improve / the mechanical behavior of bituminous mixtures · 无交集字段 relation, tail · 已配 G5 | — |
| G8 | S3 | the asphalt bitumen-based binders / are in / high temperature conditions | A6 · the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance · 无交集字段 tail · 已配 G7 | — |
| G9 | S3 | the asphalt bitumen-based binders / are in / low temperature conditions | A6 · the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance · 无交集字段 tail · 已配 G7 | — |
| G19 | S5 | the external surface / is substantially, or completely, free of / oil | A15 · the external surface / is / the out-most layer of the rubber composite · 无交集字段 tail · 已配 G18 | — |
| G29 | S9 | it / is clearly / the lowest value | A25 · It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) · 无交集字段 tail · 未配 | — |
| G30 | S9 | the lowest value / is compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) | A25 · It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) · 无交集字段 head · 未配 | A15 · F1 0.222 · 已配 G18 |
| G31 | S9 | the lowest value / is even compared with / traditional SMA mixtures with highly modified bitumen and fibres | A26 · It / is clearly the lowest value even compared with / traditional SMA mixtures with highly modified bitumen and fibres · 无交集字段 head · 未配 | A27 · F1 0.222 · 已配 G33 |
| G32 | S9 | traditional SMA mixtures / are with highly modified / bitumen and fibres | A26 · It / is clearly the lowest value even compared with / traditional SMA mixtures with highly modified bitumen and fibres · 无交集字段 head · 未配 | — |
| G34 | S10 | the range / is given as such merely for / brevity | A27 · the range / is given as such merely for / convenience and brevity · F1 0.900 · 已配 G33 | A27 · F1 0.900 · 已配 G33 |
| G36 | S10 | the range / should not be construed as an inflexible limitation on / the scope of the invention | A28 · the range / should not be construed as / an inflexible limitation on the scope of the invention · F1 0.750 · 已配 G35 | A28 · F1 0.750 · 已配 G35 |

### doc3 · A 弱配 Gold（0 条）

该组该篇没有符合此阈值的弱配。

### doc3 · B 未配 Gold（13 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G1 | S1 | a rubber composite / comprises / rubber | B2 · a rubber composite / comprising / rubber · 无交集字段 relation · 未配 | — |
| G2 | S1 | a rubber composite / comprises / oil | B3 · a rubber composite / comprising / oil · 无交集字段 relation · 未配 | — |
| G3 | S1 | a rubber composite / comprises / a combination of powdered additives | B4 · a rubber composite / comprising / a combination of powdered additives · 无交集字段 relation · 未配 | — |
| G6 | S2 | granulated recycled tire rubber / is incorporated into / bitumen | B5 · The incorporation of granulated recycled tire rubber into bitumen / aimed to improve / the mechanical behavior of bituminous mixtures · 无交集字段 relation, tail · 已配 G5 | — |
| G8 | S3 | the asphalt bitumen-based binders / are in / high temperature conditions | B6 · the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance · 无交集字段 tail · 已配 G7 | — |
| G9 | S3 | the asphalt bitumen-based binders / are in / low temperature conditions | B6 · the properties of the asphalt bitumen-based binders in high and low temperature conditions / are of / a decisive importance · 无交集字段 tail · 已配 G7 | — |
| G20 | S6 | the particles / are of / non-spheroid shape | B17 · When the particles are of non-spheroid shape, the term / refers to / the average equivalent diameter of the particle · 无交集字段 relation, tail · 已配 G21 | — |
| G29 | S9 | it / is clearly / the lowest value | B25 · It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) · 无交集字段 tail · 未配 | — |
| G30 | S9 | the lowest value / is compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) | B25 · It / is clearly the lowest value as compared with / tradition Asphalt Rubber gap graded mixtures (with and without RAR) · 无交集字段 head · 未配 | B27 · F1 0.222 · 已配 G33 |
| G31 | S9 | the lowest value / is even compared with / traditional SMA mixtures with highly modified bitumen and fibres | B26 · It / is clearly the lowest value as compared with / traditional SMA mixtures with highly modified bitumen and fibres · 无交集字段 head · 未配 | B27 · F1 0.222 · 已配 G33 |
| G32 | S9 | traditional SMA mixtures / are with highly modified / bitumen and fibres | B26 · It / is clearly the lowest value as compared with / traditional SMA mixtures with highly modified bitumen and fibres · 无交集字段 head · 未配 | — |
| G34 | S10 | the range / is given as such merely for / brevity | B27 · the range / is given as such merely for / convenience and brevity · F1 0.900 · 已配 G33 | B27 · F1 0.900 · 已配 G33 |
| G36 | S10 | the range / should not be construed as an inflexible limitation on / the scope of the invention | B28 · the range / should not be construed as / an inflexible limitation on the scope of the invention · F1 0.750 · 已配 G35 | B28 · F1 0.750 · 已配 G35 |

### doc3 · B 弱配 Gold（0 条）

该组该篇没有符合此阈值的弱配。

## doc4 · 6818. Communication path managing method and communication path managing system.txt

### doc4 · A 未配 Gold（8 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G3 | S2 | the evaluation items / are based on / the item importance information | A2 · At least one of the communication paths for the vehicle / is selected according to / the evaluation items based on the item importance information · 无交集字段 relation · 已配 G2 | — |
| G5 | S3 | selecting at least one of the communication paths for the vehicle / is according to / the evaluation items | A3 · The selecting unit / is for selecting / at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information · F1 0.273 · 已配 G4 | A2 · F1 0.800 · 已配 G2 |
| G6 | S3 | the evaluation items / are based on / the item importance information | A3 · The selecting unit / is for selecting / at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information · 无交集字段 relation · 已配 G4 | — |
| G13 | S7 | all of the evaluation items EV / is of / each of the communication paths PH in the third group G3 | A7 · All of the evaluation items EV of each of the communication paths PH in the third group G3 / is worse than / the standard thresholds E0 · F1 0.364 · 已配 G12 | A7 · F1 0.364 · 已配 G12 |
| G15 | S8 | the value of the routing path latency / is equal to or lower than 500 kbps in / the good category of the available bandwidth | A8 · the value of the routing path latency / in the good category of the available bandwidth, is equal to or lower than / 500 kbps · 无交集字段 tail · 已配 G14 | A6 · F1 0.359 · 已配 G10 |
| G17 | S9 | the specification and examples / are considered as exemplary only with / a true scope of the disclosure | A9 · the specification / is intended to be considered as / exemplary only · 无交集字段 tail · 未配 | — |
| G19 | S9 | the disclosure / is being indicated by / their equivalents | A10 · a true scope of the disclosure / is indicated by / the following claims and their equivalents · F1 0.609 · 已配 G18 | A10 · F1 0.609 · 已配 G18 |
| G21 | S10 | the value of the routing path latency / is equal to or lower than 50 ms in / the good category of the routing path latency | A11 · the value of the routing path latency / in the good category of the routing path latency, is equal to or lower than / 50 ms · 无交集字段 tail · 已配 G20 | A6 · F1 0.400 · 已配 G10 |

### doc4 · A 弱配 Gold（0 条）

该组该篇没有符合此阈值的弱配。

### doc4 · B 未配 Gold（7 条）

| 编号 | 源句 | Gold 三元组 | 本句最接近预测 | 整篇最高合格候选 |
| --- | --- | --- | --- | --- |
| G5 | S3 | selecting at least one of the communication paths for the vehicle / is according to / the evaluation items | B3 · The selecting unit / is for selecting / at least one of the communication paths for the vehicle according to the evaluation items · F1 0.316 · 已配 G4 | B2 · F1 0.941 · 已配 G2 |
| G6 | S3 | the evaluation items / are based on / the item importance information | B12 · the evaluation items / are based on / the item importance information · F1 1.000 · 已配 G3 | B12 · F1 1.000 · 已配 G3 |
| G13 | S7 | all of the evaluation items EV / is of / each of the communication paths PH in the third group G3 | B7 · All of the evaluation items EV of each of the communication paths PH in the third group G3 / is worse than / the standard thresholds E0 · F1 0.364 · 已配 G12 | B7 · F1 0.364 · 已配 G12 |
| G15 | S8 | the value of the routing path latency / is equal to or lower than 500 kbps in / the good category of the available bandwidth | B8 · the value of the routing path latency / in the good category of the available bandwidth, is equal to or lower than / 500 kbps · 无交集字段 tail · 已配 G14 | B6 · F1 0.359 · 已配 G10 |
| G17 | S9 | the specification and examples / are considered as exemplary only with / a true scope of the disclosure | B9 · the specification / is intended to be considered as / exemplary only · 无交集字段 tail · 未配 | B12 · F1 0.231 · 已配 G3 |
| G19 | S9 | the disclosure / is being indicated by / their equivalents | B10 · a true scope of the disclosure / is indicated by / the following claims and their equivalents · F1 0.609 · 已配 G18 | B10 · F1 0.609 · 已配 G18 |
| G21 | S10 | the value of the routing path latency / is equal to or lower than 50 ms in / the good category of the routing path latency | B11 · the value of the routing path latency / in the good category of the routing path latency, is equal to or lower than / 50 ms · 无交集字段 tail · 已配 G20 | B6 · F1 0.400 · 已配 G10 |

### doc4 · B 弱配 Gold（0 条）

该组该篇没有符合此阈值的弱配。
