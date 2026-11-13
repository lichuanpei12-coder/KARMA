# 阶段二　run1_5doc_013_1 剩余 Gold 差距与中间证据


运行标识 `run1_5doc_013_1`。分析日期 2026-11-13。依据用户提供的五份导出和仓库同口径的修改后 Gold（五篇、153 条）。

[阶段一_反馈变化_逐句完整对照](阶段一_反馈变化_逐句完整对照.md) · [阶段二_剩余Gold差距与中间证据](阶段二_剩余Gold差距与中间证据.md) · [反馈问题总结与修改建议_含三元组证据](反馈问题总结与修改建议_含三元组证据.md)

输入与复算：[拆分清单](inputs/split.md) · [最终清单](inputs/final.md) · [操作摘要](inputs/operations.md) · [重建与对比](inputs/comparison.md) · [差异 JSON 摘录](inputs/diff_excerpt.md) · [核对与评估证据](核对与评估证据.json)。

## 残差统计

| 检查点 | 三元组数 | 宽松 P | 宽松 R | 宽松 F1 | 严格 F1 | 配对数 | 未配 Gold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 拆分后 | 134 | 63.92% | 60.47% | 62.15% | 20.21% | 103 | 50 |
| 反馈后 | 130 | 69.47% | 64.18% | 66.72% | 24.73% | 107 | 46 |


反馈后有 **46 条 Gold 未配对**，其中 42 条延续自拆分阶段，4 条从原来有配对变为未配对；另有 8 条恢复配对。按整篇配对记录统计；局部词形差距、字段错位与真正事实遗漏分别解读，未配对不直接等于事实不存在。

## 各文档恢复与回退

| 文档 | 拆分未配 | 最终未配 | 恢复配对 Gold 编号 | 失去配对 Gold 编号 |
| --- | --- | --- | --- | --- |
| doc0 | 11 | 12 | G25 | G5, G6 |
| doc1 | 9 | 8 | G35, G36 | G32 |
| doc2 | 9 | 7 | G2, G5, G20 | G7 |
| doc3 | 14 | 13 | G19 | — |
| doc4 | 7 | 6 | G6 | — |


## 全部 46 条未配 Gold

按源句展示原文、重建、最终条目和残差。编号 G 为文档内从零编号。附件表中的“no match”与本报告复算可不同，例如 doc2/S10 两条在本次宽松配对均为 1.00，而附件操作摘要只标一条 1.00。

### doc0 857. Systems and methods for a cryptographically guaranteed vehicle identity.txt

#### doc0/S1

> Because such elements and operations are well known in the art, and because they do not facilitate a better understanding of the present disclosure.

**重建** · Such elements are well known in the art and do not facilitate a better understanding of the present disclosure. Such operations are well known in the art and do not facilitate a better understanding of the present disclosure.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| such elements | are well known in | the art |
| such elements | do not facilitate | a better understanding of the present disclosure |
| such operations | are well known in | the art |
| such operations | do not facilitate | a better understanding of the present disclosure |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G2 | (they, do not facilitate, a better understanding of the present disclosure) | 仍未配 |


**残差判断** · 标注表述差异。明确名词替换 they，整篇词匹配只分给部分重复陈述。

#### doc0/S2

> As the ECUs may include PUF components, the controller may query the ECU to identify which PUF component is compromised, in order to determine where in the sub-system the compromise is located.

**重建** · The ECUs may include PUF components. The controller may query the ECU. The controller may identify which PUF component is compromised. The controller may determine where in the sub-system the compromise is located.

差异摘要：A 1 项; B 2 项。已执行 8 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| the ECUs | may include | PUF components |
| the controller | may query | the ECU |
| the controller may query the ECU | with purpose | to identify which PUF component is compromised |
| to identify which PUF component is compromised | with purpose | to determine where in the sub-system the compromise is located |
| the ECUs may include PUF components | is a reason for | the controller may query the ECU |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G5 | (the controller, may query the ECU to identify, which PUF component is compromised) | 从有配到未配 |
| G6 | (the controller, may query the ECU in order to determine, where in the sub-system the compromise is located) | 从有配到未配 |


**残差判断** · 目的关系表达不同。with purpose 与 Gold 的 may query ... 无关系字段重合。

#### doc0/S7

> They may be implemented as instructions stored on a machine-readable medium, which may be read and executed by a computing platform to perform the operations described herein.

**重建** · They may be implemented as instructions stored on a machine-readable medium. The instructions may be read and executed by a computing platform. The computing platform performs the operations described herein.

差异摘要：A 1 项; B 1 项。已执行 4 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| They | may be implemented as | instructions stored on a machine-readable medium |
| instructions | may be read and executed by a computing platform to perform | the operations described herein |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G18 | (instructions, are stored on, a machine-readable medium) | 仍未配 |
| G19 | (a machine-readable medium, may be read by, a computing platform) | 仍未配 |
| G20 | (a machine-readable medium, may be executed by, a computing platform) | 仍未配 |
| G21 | (a computing platform, is to perform, the operations) | 仍未配 |


**残差判断** · 存储在长客体；独立 read 和 execute 被删除；perform 压进长关系。结合原句另核对 which 的先行词。

#### doc0/S10

> This method may be integrated in a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services.

**重建** · This method may be integrated in connected cars, car sharing, rental car services, maintenance, and factory services.

差异摘要：A 2 项; B 2 项。已执行 7 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| This method | may be integrated in | a variety of systems including connected cars, car sharing, rental car services, maintenance and factory services |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G26 | (a variety of systems, include, connected cars) | 仍未配 |
| G27 | (a variety of systems, include, car sharing) | 仍未配 |
| G28 | (a variety of systems, include, rental car services) | 仍未配 |
| G29 | (a variety of systems, include, maintenance) | 仍未配 |
| G30 | (a variety of systems, include, factory services) | 仍未配 |


**残差判断** · 五个系统仍为外层客体的列举，欠独立的 include 关系。

### doc1 2786. Method for providing congestion information in a network.txt

#### doc1/S1

> A further aspect provides a meaningful capture of the congestion level information enabling appropriate congestion mitigation measures, for example according to the severeness of the congestion.

**重建** · A further aspect provides a meaningful capture of the congestion level information, which enables appropriate congestion mitigation measures, for example according to the severeness of the congestion.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| A further aspect | provides | a meaningful capture of the congestion level information |
| a meaningful capture of the congestion level information | enables | appropriate congestion mitigation measures, for example according to the severeness of the congestion |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G2 | (congestion mitigation measures, are for example according to, the severeness of the congestion) | 仍未配 |


**残差判断** · 严重程度的依据藏在 enables 的长客体内。

#### doc1/S2

> A congestion may be detected based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.

**重建** · A congestion may be detected based on said congestion value, and may be detected when said minimum bandwidth demand exceeds the measured traffic per time over a given time span.

差异摘要：A 1 项; B 1 项。已执行 2 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| A congestion | may be detected | based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G4 | (said minimum bandwidth demand, exceeds, the measured traffic per time) | 仍未配 |
| G5 | (the measured traffic per time, is over, a given time span) | 仍未配 |


**残差判断** · 条件里的 exceeds 与时间跨度保留在长客体，独立表达不足。

#### doc1/S3

> The term "part" in connection with the term "network" is to be understood in a broad sense, meaning that part of the network can be any real or imaginary fraction, portion or component of the network.

**重建** · The term "part" in connection with the term "network" is to be understood in a broad sense. Part of the network can be any real or imaginary fraction of the network. Part of the network can be any real or imaginary portion of the network. Part of the network can be any real or imaginary component of the network.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| The term "part" in connection with the term "network" | is to be understood | in a broad sense |
| part of the network | can be | any real or imaginary fraction of the network |
| part of the network | can be | any real or imaginary portion of the network |
| part of the network | can be | any real or imaginary component of the network |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G7 | (the term "part" in connection with the term "network", means that, part of the network) | 仍未配 |


**残差判断** · 回查术语定义的主语及定义对象边界，现有表述与 Gold 分配不同。

#### doc1/S5

> While the invention has been illustrated and described in detail in the drawings and foregoing description, such illustration and description are to be considered illustrative or exemplary and not restrictive.

**重建** · Such illustration and description are to be considered illustrative or exemplary, and not restrictive. The invention has been illustrated and described in detail in the drawings and in the foregoing description.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| such illustration and description | are to be considered | illustrative or exemplary |
| the invention | has been illustrated | in detail in the drawings |
| such illustration and description | are to be considered | not restrictive |
| the invention | has been illustrated | in detail in the foregoing description |
| the invention | has been described | in detail in the drawings |
| the invention | has been described | in detail in the foregoing description |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G19 | (such description, are to be considered, illustrative or exemplary) | 仍未配 |
| G21 | (such description, are to be considered not, restrictive) | 仍未配 |


**残差判断** · 复核 illustrative/exemplary/restrictive 的并列、否定范围及重复拆分。

#### doc1/S9

> This enhances the flexibility of the congestion value, since different operators can use different transformation functions or profiles such that the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator.

**重建** · This enhances the flexibility of the congestion value. Different operators can use different transformation functions. The congestion level may be based per cell with different feedback profiles depending on the need of an operator. Different operators can use different profiles. The congestion level may be based per link with different feedback profiles depending on the need of an operator.

差异摘要：A 1 项; B 1 项。已执行 6 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| This | enhances | the flexibility of the congestion value |
| different operators | can use | different transformation functions or profiles |
| the congestion level | may be based | per cell and per link with different feedback profiles depending on the need of an operator |
| the flexibility of the congestion value | is enhanced because | different operators can use different transformation functions or profiles |
| different operators can use different transformation functions or profiles | such that | the congestion level may be based per cell and per link with different feedback profiles depending on the need of an operator |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G32 | (the congestion level, may be based, per link with different feedback profiles) | 从有配到未配 |
| G33 | (different feedback profiles, depending on, the need of an operator) | 仍未配 |


**残差判断** · per link 与 per cell 合并；depending on 仍在客体，未独立。

### doc2 5921. Tarpaulin bracket system.txt

#### doc2/S1

> Even a small open area can present a danger when loose items are being transported in high-traffic areas.

**重建** · a small open area can present a danger when loose items are being transported in high-traffic areas

差异摘要：A 1 项; B 1 项。已执行 2 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| Even a small open area | can present | a danger |
| loose items | are being transported in | high-traffic areas |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G1 | (a danger, is when, loose items are being transported in high-traffic areas) | 仍未配 |


**残差判断** · 运输条件已抽为一个事实，仍缺 danger 与 when 条件的关系。

#### doc2/S3

> Further, the hazards of loose items flying out of the open-top of cargo trailers has led many governing bodies to enact strict laws against such open transport.

**重建** · The hazards of loose items flying out of the open-top of cargo trailers have led many governing bodies to enact strict laws against such open transport. Loose items fly out of the open-top of cargo trailers.

差异摘要：A 0 项; B 0 项。已执行 2 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| the hazards | has led | many governing bodies |
| the hazards | are of | loose items flying out of the open-top of cargo trailers |
| many governing bodies | enact | strict laws against such open transport |
| loose items | flying out of | the open-top of cargo trailers |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G7 | (the hazards, has led many governing bodies to enact, strict laws) | 从有配到未配 |
| G8 | (strict laws, is against, such open transport) | 仍未配 |


**残差判断** · 法律颁布与危险导致颁布的链路拆散；法律针对开放式运输的关系在长客体。

#### doc2/S5

> The matter set forth in the foregoing description and accompanying drawings is offered by way of illustration only and not as a limitation.

**重建** · The matter set forth in the foregoing description is offered by way of illustration only and is not offered as a limitation. The matter set forth in the accompanying drawings is offered by way of illustration only and is not offered as a limitation.

差异摘要：A 1 项; B 2 项。已执行 4 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| The matter set forth in the foregoing description and accompanying drawings | is offered | by way of illustration only |
| The matter set forth in the foregoing description and accompanying drawings | is not offered | as a limitation |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G11 | (the matter set forth, is in, the foregoing description and accompanying drawings) | 仍未配 |


**残差判断** · 出处只留在主语中，未独立表达。

#### doc2/S6

> The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.

**重建** · The actual scope of the protection sought is intended to be defined in the following claims when viewed in their proper perspective based on the prior art.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| The actual scope of the protection sought | is intended to be defined | in the following claims when viewed in their proper perspective based on the prior art |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G15 | (the following claims, are viewed in, their proper perspective) | 仍未配 |
| G16 | (their proper perspective, is based on, the prior art) | 仍未配 |


**残差判断** · 审查视角与 prior art 依据被保留在字段中或未独立抽出。

#### doc2/S7

> Preferably, most of these components are made of strong materials to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.

**重建** · Most of these components are made of strong materials. Most of these components are intended to withstand the conditions of being atop an open cargo area of a vehicle during transportation of goods.

差异摘要：A 1 项; B 1 项。已执行 2 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| most of these components | are preferably made of | strong materials |
| most of these components | to withstand | the conditions of being atop an open cargo area of a vehicle during transportation of goods |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G19 | (the conditions, are of being atop, an open cargo area of a vehicle during transportation of goods) | 仍未配 |


**残差判断** · 条件的具体内容仍在目的关系长客体中。

### doc3 6519. Rubber composite and process for obtaining same.txt

#### doc3/S1

> The present invention relates to a rubber composite comprising rubber, oil and a combination of powdered additives, as well as a process for manufacturing same.

**重建** · The present invention relates to a rubber composite and a process for manufacturing same. A rubber composite comprises rubber, oil, and a combination of powdered additives.

差异摘要：A 0 项; B 1 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| The present invention | relates to | a rubber composite |
| The present invention | relates to | a process for manufacturing same |
| a rubber composite | comprising | rubber |
| a rubber composite | comprising | oil |
| a rubber composite | comprising | a combination of powdered additives |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G1 | (a rubber composite, comprises, rubber) | 仍未配 |
| G2 | (a rubber composite, comprises, oil) | 仍未配 |
| G3 | (a rubber composite, comprises, a combination of powdered additives) | 仍未配 |


**残差判断** · 三条事实已存在，关系沿用 comprising，Gold 为 comprises；属于词面不配。

#### doc3/S2

> The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.

**重建** · The incorporation of granulated recycled tire rubber into bitumen aimed to improve the mechanical behavior of bituminous mixtures.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| The incorporation of granulated recycled tire rubber into bitumen | aimed to improve | the mechanical behavior of bituminous mixtures |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G6 | (granulated recycled tire rubber, is incorporated into, bitumen) | 仍未配 |


**残差判断** · 复核 incorporated into 的实体和关系边界，候选表达未分到此 Gold。

#### doc3/S3

> In this connection, the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance.

**重建** · the properties of the asphalt bitumen-based binders in high and low temperature conditions are of a decisive importance

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| the properties of the asphalt bitumen-based binders in high and low temperature conditions | are of | a decisive importance |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G8 | (the asphalt bitumen-based binders, are in, high temperature conditions) | 仍未配 |
| G9 | (the asphalt bitumen-based binders, are in, low temperature conditions) | 仍未配 |


**残差判断** · 高、低温条件主要在原条目的条件表达中，未独立拆出。

#### doc3/S6

> When the particles are of non-spheroid shape, the term refers to the average equivalent diameter of the particle, namely the diameter of an equivalent spherical particle based on the longest dimension of the particle.

**重建** · When the particles are of non-spheroid shape: the term refers to the average equivalent diameter of the particle; the average equivalent diameter of the particle is namely the diameter of an equivalent spherical particle; the diameter of an equivalent spherical particle is based on the longest dimension of the particle.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| When the particles are of non-spheroid shape, the term | refers to | the average equivalent diameter of the particle |
| When the particles are of non-spheroid shape, the average equivalent diameter of the particle | is namely | the diameter of an equivalent spherical particle |
| When the particles are of non-spheroid shape, the diameter of an equivalent spherical particle | is based on | the longest dimension of the particle |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G20 | (the particles, are of, non-spheroid shape) | 仍未配 |


**残差判断** · 非球状属性未形成对应独立条目，需回查修饰归属。

#### doc3/S9

> It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR) or even compared with traditional SMA mixtures with highly modified bitumen and fibres.

**重建** · It is clearly the lowest value as compared with tradition Asphalt Rubber gap graded mixtures (with and without RAR). It is clearly the lowest value as compared with traditional SMA mixtures with highly modified bitumen and fibres.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| It | is clearly the lowest value as compared with | tradition Asphalt Rubber gap graded mixtures (with and without RAR) |
| It | is clearly the lowest value as compared with | traditional SMA mixtures with highly modified bitumen and fibres |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G29 | (it, is clearly, the lowest value) | 仍未配 |
| G30 | (the lowest value, is compared with, tradition Asphalt Rubber gap graded mixtures (with and without RAR)) | 仍未配 |
| G31 | (the lowest value, is even compared with, traditional SMA mixtures with highly modified bitumen and fibres) | 仍未配 |
| G32 | (traditional SMA mixtures, are with highly modified, bitumen and fibres) | 仍未配 |


**残差判断** · 两条长关系把最低值、比较和材料属性放在一起，两处比较的范围和层次未区分；没有抽出四项对应事实。

#### doc3/S10

> It should be noted that the range is given as such merely for convenience and brevity and should not be construed as an inflexible limitation on the scope of the invention.

**重建** · The range is given as such merely for convenience and brevity. The range should not be construed as an inflexible limitation on the scope of the invention.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| the range | is given as such merely for | convenience and brevity |
| the range | should not be construed as | an inflexible limitation on the scope of the invention |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G34 | (the range, is given as such merely for, brevity) | 仍未配 |
| G36 | (the range, should not be construed as an inflexible limitation on, the scope of the invention) | 仍未配 |


**残差判断** · 检查 brevity 的目的和“不得作为刚性限制”的独立表达及词形。

### doc4 6818. Communication path managing method and communication path managing system.txt

#### doc4/S3

> The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items based on the item importance information.

**重建** · The selecting unit is for selecting at least one of the communication paths for the vehicle according to the evaluation items.

差异摘要：A 1 项; B 1 项。已执行 3 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| The selecting unit | is for selecting | at least one of the communication paths for the vehicle according to the evaluation items |
| the evaluation items | are based on | the item importance information |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G5 | (selecting at least one of the communication paths for the vehicle, is according to, the evaluation items) | 仍未配 |


**残差判断** · 评价项是选择方式，仍嵌在选择单元的长客体；评价项依据已恢复。

#### doc4/S7

> All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.

**重建** · All of the evaluation items EV of each of the communication paths PH in the third group G3 is worse than the standard thresholds E0.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| All of the evaluation items EV of each of the communication paths PH in the third group G3 | is worse than | the standard thresholds E0 |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G13 | (all of the evaluation items EV, is of, each of the communication paths PH in the third group G3) | 仍未配 |


**残差判断** · 评估项与第三组路径的范围挂接未形成匹配关系。

#### doc4/S8

> In the good category of the available bandwidth, the value of the routing path latency is equal to or lower than 500 kbps.

**重建** · The value of the routing path latency in the good category of the available bandwidth is equal to or lower than 500 kbps.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| the value of the routing path latency | in the good category of the available bandwidth, is equal to or lower than | 500 kbps |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G15 | (the value of the routing path latency, is equal to or lower than 500 kbps in, the good category of the available bandwidth) | 仍未配 |


**残差判断** · 原文使用 latency + 500 kbps，照录原文；一条预测有多个可对齐的标注表达，其次检查分段。

#### doc4/S9

> It is intended that the specification and examples be considered as exemplary only, with a true scope of the disclosure being indicated by the following claims and their equivalents.

**重建** · The specification is intended to be considered as exemplary only. A true scope of the disclosure is indicated by the following claims and their equivalents. Examples are intended to be considered as exemplary only.

差异摘要：A 0 项; B 0 项。已执行 0 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| the specification | is intended to be considered as | exemplary only |
| a true scope of the disclosure | is indicated by | the following claims and their equivalents |
| examples | are intended to be considered as | exemplary only |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G17 | (the specification and examples, are considered as exemplary only with, a true scope of the disclosure) | 仍未配 |
| G19 | (the disclosure, is being indicated by, their equivalents) | 仍未配 |


**残差判断** · 示例性限定与等效项关系需回查原句，词匹配未覆盖对应 Gold。

#### doc4/S10

> In the good category of the routing path latency, the value of the routing path latency is equal to or lower than 50 ms.

**重建** · the value of the routing path latency in the good category of the routing path latency is equal to or lower than 50 ms

差异摘要：A 0 项; B 0 项。已执行 1 项操作。

| 最终 Head | Relation | Tail |
| --- | --- | --- |
| the value of the routing path latency | in the good category of the routing path latency is equal to or lower than | 50 ms |


| Gold | 未配三元组 | 配对变化 |
| --- | --- | --- |
| G21 | (the value of the routing path latency, is equal to or lower than 50 ms in, the good category of the routing path latency) | 仍未配 |


**残差判断** · 数值与类别在一条长关系中；第二个 Gold 是带类别的独立表达，复查字段边界。

## 弱配附表（4 对）

配对 F1 ≤ 0.50 作为复核标记。该阈值仅用于报告标记，与程序 Remove 的排名和匹配规则无关。

| 文档 | Gold | 最终条目 | 配对 F1 | Gold 三元组 | 最终三元组 |
| --- | --- | --- | --- | --- | --- |
| doc1 | G3 | F2 | 0.4444 | (a congestion, may be detected based on, said congestion value) | (A congestion, may be detected, based on said congestion value when said minimum bandwidth demand exceeds the measured traffic per time over a given time span) |
| doc1 | G23 | F27 | 0.2286 | (capturing of congestion levels, is in such a way that, congestion mitigation measures can be reliably performed) | (the flexibility of the congestion value, is enhanced because, different operators can use different transformation functions or profiles) |
| doc1 | G25 | F19 | 0.5000 | (said transformation function, amends, at least one of the following: a number of congestion levels, a steepness of a congestion level curve, a shape of a congestion level curve) | (said transformation function, amends at least one of, a steepness of a congestion level curve) |
| doc2 | G18 | F15 | 0.4571 | (most of these components made of strong materials, is to withstand, the conditions) | (most of these components, to withstand, the conditions of being atop an open cargo area of a vehicle during transportation of goods) |
