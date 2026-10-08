# KARMA 三元组正确性与标注标准：师生讨论材料

## 讨论目标

先确定如何判断一条抽取是否忠实于输入，再确定希望输出的粒度、表达形式和评估匹配规则。不要让现有 Gold 或已有分数替代对原文的判断。

建议每个候选分别记录：①忠实于原文：是／否／依赖上下文；②信息是否完整：完整／遗漏限定／复合多个事实；③是否符合项目粒度：是／需拆分／不应拆分；④是否应与对应 Gold 匹配：是／否／Gold 待审校。判断一条三元组正确与否，与判断一整组抽取是否充分覆盖原文，需要分开。

本材料中的“候选 A/B/C”全部是为讨论整理的表达，不冒充 KARMA 的实际模型输出。若汇报实际系统表现，需要另附运行结果、轮次和提示词版本。原始 Gold 保留方括号：它表示数据集允许该词可选，不是助手建议删除该词。只展示与问题有关的部分簇或元组，未展示不等于 Gold 未标注。

本次未修改任何数据集、提示词或评估程序。案例优先使用已在项目中讨论的 BenchIE-FL 和 DocOIE transportation。BenchIE-FL 引用此前使用的原始文件快照；不把我们每簇选一条后的代表版误称为官方全量 Gold。

## 如何组织讨论

优先讨论案例 1–3；案例 4–8 用来补足关键边界，案例 9–12 是按时间选用的反例。先给老师看原文和候选，分别判断后再展示官方 Gold，减少参考答案对判断的影响。每个案例最终记录一句可执行规则及其例外。

| 顺序 | 议题 | 来源 |
|---|---|---|
| 1 | 情态：may 能否删除 | BenchIE-FL，sent_id:293 |
| 2 | 并列：官方 Gold 没有拆开两个动作 | DocOIE transportation，文档 9442，原文第 33 句（从 1 起） |
| 3 | 定语：是否作为独立属性或事件抽取 | BenchIE-FL，sent_id:268 |
| 4 | 条件：Gold 有记录，不代表脱离条件仍正确 | BenchIE-FL，sent_id:240 |
| 5 | 否定与程度：不显著贡献不等于完全没有贡献 | BenchIE-FL，sent_id:32 |
| 6 | 信息来源：怀疑某事实不等于该事实成立 | BenchIE-FL，sent_id:280 |
| 7 | 指代：输入没有前文时是否可以补全实体 | BenchIE-FL，sent_id:85 |
| 8 | 限制性定语：抽成属性会不会扩大断言范围 | BenchIE-FL，sent_id:58 |
| 9 | 并列补例：拆开时是否允许调整谓词 | BenchIE-FL，sent_id:195 |
| 10 | 并列反例：专有名称中的 and | BenchIE-FL，sent_id:155 |
| 11 | 数量与多组并列：禁止盲目交叉组合 | BenchIE-FL，sent_id:34 |
| 12 | 表达与匹配：关系边界不同但事实相同 | BenchIE-FL，sent_id:1 |

## 案例 1：情态：may 能否删除

来源：[BenchIE-FL 原始 Gold，sent_id:293](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L7939)。

**原句**

The office may also be able to advise foreign and multinational clients on international law and general matters .

**中文释义**

该机构也许还能就国际法及一般事务为外国和跨国客户提供咨询。

**相关官方 Gold（原样摘录）**

```text
293--> Cluster 3:
[The] office --> may [also] be able to advise --> foreign clients
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (office; may also be able to advise; foreign clients)
B. (office; is able to advise; foreign clients)
C. (office; advises; foreign clients)
```

**请老师判断**

- may 的可能性含义是否必须保留？
- be able to 表示能力，能否进一步改成实际提供咨询？
- also 等篇章衔接信息是否与 may 采用不同保留规则？

**助手初步判断（待讨论确定）**

在当前只有 head/relation/tail 的格式下，应在关系中保留 may 及 be able to。B 把可能具有能力改成确定具有能力，C 进一步写成实际行为。不能把情态变化只当作措辞差异。

**老师结论／项目规则：** ______________________________

## 案例 2：并列：官方 Gold 没有拆开两个动作

来源：DocOIE transportation，`9442. Methods and systems for noise removal in indoor positioning.txt`；该文档第 5 个有 Gold 的句子，全篇句子数组索引 32。你仓库 `data/DocIOE/transport/6.json` 也保留相同三条 Gold。

[官方 Gold 文件](https://github.com/daviddongkc/DocOIE/blob/main/DocOIE/data_evaluation/DocOIE_transportation_eval_gold.json)；[项目 Gold 文件](https://github.com/lichuanpei12-coder/KARMA/blob/main/data/DocIOE/transport/6.json)

**原句**

First, in an indoor venue, the signals are attenuated and scattered by static obstacles such as walls and "dynamic obstacles" such as people.

**中文释义**

首先，在室内场所，信号会被墙壁等静态障碍物和人员等动态障碍物衰减和散射。

**该句全部官方 Gold（原字段值）**

```text
(the signals; are attenuated and scattered by; static obstacles and "dynamic obstacles")
(static obstacles; are such as; walls)
("dynamic obstacles"; are such as; people)
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (the signals; are attenuated and scattered by; static obstacles and "dynamic obstacles")
B1. (the signals; are attenuated by; static obstacles and "dynamic obstacles")
B2. (the signals; are scattered by; static obstacles and "dynamic obstacles")
```

**请老师判断**

- A 是否事实正确，但不符合一条三元组只表达一个动作事实的粒度要求？
- B1、B2 是否都应计为正确？能否共同覆盖 A 对应的 Gold？
- 是否进一步拆分两类障碍物？原文是否支持每种障碍物与每种作用的全部组合？

**助手初步判断（待讨论确定）**

这个例子直接符合“并列存在但 Gold 未拆开”。优先讨论把两个动作分为 B1、B2，同时暂时保留宾语整体。不要将 and 一律展开成主语、动作、宾语的所有组合。原句还限定了室内场景，而该 Gold 没有表示；建议把场景范围作为独立问题记录，避免混淆并列判断。

**老师结论／项目规则：** ______________________________

## 案例 3：定语：是否作为独立属性或事件抽取

来源：[BenchIE-FL 原始 Gold，sent_id:268](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L7279)。

**原句**

Hani Zayadi was appointed president and chief executive officer of this financially troubled department store chain , effective Nov. 15 , succeeding Frank Robertson , who is retiring early .

**中文释义**

Hani Zayadi 被任命为这家陷入财务困境的百货连锁企业的总裁兼首席执行官，任命自 11 月 15 日生效，接替提前退休的 Frank Robertson。

**相关官方 Gold（原样摘录）**

```text
268--> Cluster 3:
Hani Zayadi --> was [appointed] president of --> [this] department store chain
268--> Cluster 8:
Frank Robertson --> is --> retiring
Frank Robertson --> was --> retiring
268--> Cluster 9:
Frank Robertson --> is retiring --> early
Frank Robertson --> was retiring --> early
268--> Cluster 10:
[this] department store chain --> was --> financially troubled
[this] department store chain --> is --> financially troubled
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (Hani Zayadi; was appointed president of; this financially troubled department store chain)
B1. (Hani Zayadi; was appointed president of; this department store chain)
B2. (this department store chain; is; financially troubled)
C. (Frank Robertson; is retiring; early)
```

**请老师判断**

- A 与 B1+B2 是否都事实正确？哪种形式是本项目的目标？
- B2 是否应当作为必须抽出的独立事实，而不是仅保留在实体描述中？
- who is retiring early 这样的定语从句是否也应独立抽取？

**助手初步判断（待讨论确定）**

本例的 financially troubled 明确描述企业状态，适合形成属性事实；who is retiring early 明确陈述另一个人的事件，也适合独立抽取。B1 单独出现会丢失属性信息，B1+B2 则保留了它。不能推广为所有定语都拆：专名组成部分、假设属性、限制适用对象的定语需要分别处理。

**老师结论／项目规则：** ______________________________

## 案例 4：条件：Gold 有记录，不代表脱离条件仍正确

来源：[BenchIE-FL 原始 Gold，sent_id:240](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L6552)。

**原句**

These objects are thrown away if their screen projection is too small .

**中文释义**

如果这些对象在屏幕上的投影太小，它们就会被丢弃。

**相关官方 Gold（原样摘录）**

```text
240--> Cluster 1:
These objects --> are --> thrown away
240--> Cluster 2:
These objects --> are thrown away if --> [their] screen projection is too small
These objects --> are thrown away if --> These objects screen projection is too small
240--> Cluster 4:
their screen projection --> is --> too small
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (These objects; are thrown away if; their screen projection is too small)
B. (These objects; are; thrown away)
C. (their screen projection; is; too small)
```

**请老师判断**

- B、C 在脱离条件后是否把条件命题变成无条件断言？
- 官方 Gold 同时包含这些表达时，是否仍应按原文判断其正确性？
- 如果只允许三字段，条件放在关系、尾项或受限定的主体中，哪些表达可以接受？

**助手初步判断（待讨论确定）**

A 保留条件。单独把 B 或 C 当作实际成立的无条件事实有语义风险；条件成立才丢弃，并不证明当前对象已经被丢弃或其投影确实太小。本例尤其适合讨论原文忠实性与 Gold 一致性的区别。Gold 本身不能充当正确性的唯一论据。

**老师结论／项目规则：** ______________________________

## 案例 5：否定与程度：不显著贡献不等于完全没有贡献

来源：[BenchIE-FL 原始 Gold，sent_id:32](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L1020)。

**原句**

Often , objects are so far away that they do not contribute significantly to the final image .

**中文释义**

物体常常离得太远，以至于对最终图像没有显著贡献。

**相关官方 Gold（原样摘录）**

```text
32--> Cluster 2:
objects --> [Often] do not --> contribute [significantly] to [the] final image
objects --> [often] do not --> contribute [significantly] to [the] final image
objects --> [Often] do not contribute [significantly] to --> [the] final image
objects --> [often] do not contribute [significantly] to --> [the] final image
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (objects; often do not contribute significantly to; the final image)
B. (objects; often do not contribute to; the final image)
C. (objects; often contribute significantly to; the final image)
```

**请老师判断**

- not 是否必须保留？
- significantly 被 Gold 标成可选词，是否意味着语义上可以无条件删除？
- 是否区分“未达到显著程度”和“完全没有贡献”？

**助手初步判断（待讨论确定）**

C 改变否定方向。B 也比 A 更强：没有显著贡献仍可能有少量贡献。因此不仅要保留 not，还要注意程度词及否定作用范围。该例正好显示，官方可选词规则也可能与严格语义判断冲突。

**老师结论／项目规则：** ______________________________

## 案例 6：信息来源：怀疑某事实不等于该事实成立

来源：[BenchIE-FL 原始 Gold，sent_id:280](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L7543)。

**原句**

Mr. Stoll suspected the intruder was one of those precocious students who has fun breaking into computers .

**中文释义**

Stoll 先生怀疑，入侵者是那些以侵入计算机为乐的早慧学生之一。

**相关官方 Gold（原样摘录）**

```text
280--> Cluster 1:
[Mr.] Stoll --> suspected --> [the] intruder was one of those [precocious] students
[Mr.] Stoll --> suspected [the] intruder was --> one of those [precocious] students
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (Mr. Stoll; suspected; the intruder was one of those precocious students)
B. (the intruder; was; one of those precocious students)
```

**请老师判断**

- 能否删除 suspected，把被怀疑的内容直接作为事实输出？
- said、believes、reportedly 等来源或认知状态是否采用同类规则？

**助手初步判断（待讨论确定）**

A 表达的是怀疑。B 将怀疑内容直接断言为真，缺少原文保证。只有输入其他证据明确支持时，才可能另外输出 B。

**老师结论／项目规则：** ______________________________

## 案例 7：指代：输入没有前文时是否可以补全实体

来源：[BenchIE-FL 原始 Gold，sent_id:85](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L2546)。

**原句**

These skills were readily proven when squadrons and personnel were mobilized and recalled back to active duty during the Korean War and the Berlin Crisis .

**中文释义**

在朝鲜战争和柏林危机期间，中队和人员被动员并召回现役，这些技能得到了充分验证。

**相关官方 Gold（原样摘录）**

```text
85--> Cluster 1:
These skills --> were --> [readily] proven
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (These skills; were; readily proven)
B. (the aviation skills of naval reservists; were; readily proven)
```

**请老师判断**

- 只提供这一句时，A 是否可接受？是否应将指代未消解单独标记？
- B 虽能结合原始文章解释，但在句子输入任务中是否属于引入输入之外的信息？

**助手初步判断（待讨论确定）**

这就是之前讨论 These skills 上下文时的例子。若输入仅为本句，A 忠实于输入，B 需要额外上下文。若允许补上下文，应作为新的任务设置，不能悄悄扩充原句的 Gold。

**老师结论／项目规则：** ______________________________

## 案例 8：限制性定语：抽成属性会不会扩大断言范围

来源：[BenchIE-FL 原始 Gold，sent_id:58](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L1719)。

**原句**

For patients who do not recover quickly , the protocol also includes support groups and/or psychotherapy .

**中文释义**

对于不能迅速康复的患者，该方案还包括支持小组和／或心理治疗。

**相关官方 Gold（原样摘录）**

```text
58--> Cluster 5:
[the] protocol --> includes support groups For patients who do not --> recover quickly
[the] protocol --> includes support groups for patients who do not --> recover quickly
[the] protocol --> includes support groups and/or psychotherapy For patients who do not --> recover quickly
[the] protocol --> includes support groups and/or psychotherapy for patients who do not --> recover quickly
[the] protocol --> includes psychotherapy and/or support groups For patients who do not --> recover quickly
[the] protocol --> includes psychotherapy and/or support groups for patients who do not --> recover quickly
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (the protocol; includes for patients who do not recover quickly; support groups and/or psychotherapy)
B. (patients; do not recover; quickly)
```

**请老师判断**

- who do not recover quickly 是对所有患者的事实陈述，还是在限定方案适用对象？
- 如果拆出 B，是否把“满足条件的患者”扩大成了“患者普遍如此”？
- and/or 能否当作 and，拆成两项确定都会提供的治疗？

**助手初步判断（待讨论确定）**

本例的定语限定适用患者，并不意味着所有患者都无法迅速康复。A 是讨论用重写，非原始 Gold；保留了适用对象和 and/or。B 脱离限定范围有泛化风险。和第 3 例对照，有助于制定定语拆分的例外。

**老师结论／项目规则：** ______________________________

## 案例 9：并列补例：拆开时是否允许调整谓词

来源：[BenchIE-FL 原始 Gold，sent_id:195](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L5493)。

**原句**

Kim graduated from Ballard High School in Louisville , Kentucky , in 1989 and from Oberlin College in Ohio in 1993 where he double-majored in Government and English and played for the varsity lacrosse team .

**中文释义**

句子叙述 Kim 的毕业经历，并提到其在 Oberlin College 双主修 Government 和 English。这里只讨论双主修片段。

**相关官方 Gold（原样摘录）**

```text
195--> Cluster 11:
Kim --> double [-] majored in --> Government and English
Kim --> double-majored in --> Government and English
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (Kim; double-majored in; Government and English)
B1. (Kim; majored in; Government)
B2. (Kim; majored in; English)
C. (Kim; double-majored in; Government)
```

**请老师判断**

- B1+B2 是否可接受，且还需不需要额外保留“双主修”的整体信息？
- 是否允许将 double-majored 调整为 majored，以正确表达拆分后的事实？

**助手初步判断（待讨论确定）**

本句全量 Gold 没有另列单独的 Government 与 English 主修关系；第 11–13 簇均保留两者整体。B1、B2 是讨论候选，不是官方 Gold。C 把双主修只接一个学科，语义不完整，说明并列拆分不能只做字符串切割。

**老师结论／项目规则：** ______________________________

## 案例 10：并列反例：专有名称中的 and

来源：[BenchIE-FL 原始 Gold，sent_id:155](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L4459)。

**原句**

Mr. Baker heads the Kentucky Association of Science Educators and Skeptics .

**中文释义**

Baker 先生领导 Kentucky Association of Science Educators and Skeptics 这一组织。

**相关官方 Gold（原样摘录）**

```text
155--> Cluster 1:
[Mr.] Baker --> heads --> [the] Kentucky Association of Science Educators and Skeptics
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (Mr. Baker; heads; the Kentucky Association of Science Educators and Skeptics)
B. 将组织名在 and 处拆成两个组织，各生成一条 heads 关系。
```

**请老师判断**

- 是否明确规定：专有名称内部的 and 不触发拆分？

**助手初步判断（待讨论确定）**

该句表示一个组织，不能仅凭名称含 and 就制造两个组织。

**老师结论／项目规则：** ______________________________

## 案例 11：数量与多组并列：禁止盲目交叉组合

来源：[BenchIE-FL 原始 Gold，sent_id:34](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L1076)。

**原句**

They held the first Triangle workshop in 1982 for thirty sculptors and painters from the US , the UK and Canada at Pine Plains , New York .

**中文释义**

他们在 1982 年于纽约州 Pine Plains 为来自美国、英国、加拿大的三十名雕塑家和画家举办了首届 Triangle 工作坊。

**相关官方 Gold（原样摘录）**

```text
34--> Cluster 3:
They --> held [the] first Triangle workshop for --> thirty sculptors and painters
34--> Cluster 4:
They --> held [the] first Triangle workshop for [thirty] sculptors and painters from --> [the] US [,] [the] UK and Canada
34--> Cluster 8:
They --> held [the] first Triangle workshop for sculptors from --> [the] US
34--> Cluster 9:
They --> held [the] first Triangle workshop for sculptors from --> [the] UK
34--> Cluster 10:
They --> held [the] first Triangle workshop for sculptors from --> Canada
34--> Cluster 11:
They --> held [the] first Triangle workshop for painters from --> [the] US
34--> Cluster 12:
They --> held [the] first Triangle workshop for painters from --> [the] UK
34--> Cluster 13:
They --> held [the] first Triangle workshop for painters from --> Canada
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (They; held the first Triangle workshop for; thirty sculptors and painters)
B1. (They; held the first Triangle workshop for; thirty sculptors)
B2. (They; held the first Triangle workshop for; thirty painters)
C. 生成“雕塑家／画家 × 美国／英国／加拿大”的六种确定组合。
```

**请老师判断**

- 三十是否是总人数？是否允许拆分后给每类都保留三十？
- 原文是否保证每种职业在每个国家都有代表，还是仅给出两个集合？
- 如果 Gold 列出了六种组合，是否仍要将其列为待审校项？

**助手初步判断（待讨论确定）**

B1、B2 错把总数分配给各类。原句也不必然支持两类职业与三国的全部六种组合，而原始 Gold 第 8–13 簇确实列出了这些组合。这是“Gold 与严格语义判断冲突”的另一个实际案例。

**老师结论／项目规则：** ______________________________

## 案例 12：表达与匹配：关系边界不同但事实相同

来源：[BenchIE-FL 原始 Gold，sent_id:1](https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated(300).txt#L1)。

**原句**

He served as the first Prime Minister of Australia and became a founding justice of the High Court of Australia .

**中文释义**

原句说他成为澳大利亚高等法院的创始法官之一。这里只讨论该片段。

**相关官方 Gold（原样摘录）**

```text
1--> Cluster 5:
He --> became [a] founding justice of --> [the] High Court of Australia
```

**讨论候选：以下是整理的对照方案，不是模型实测输出**

```text
A. (He; became a founding justice of; the High Court of Australia)
B. (He; became; a founding justice of the High Court of Australia)
```

**请老师判断**

- A、B 是否应按同一事实接受？
- 是否分别制定事实正确性和推荐三元组边界，避免“格式偏好”被计为事实错误？

**助手初步判断（待讨论确定）**

A 是对该簇 Gold 可选冠词的展开；B 是讨论候选，并非该簇已列出的第二条 Gold。两者句子级陈述一致，但关系／尾项边界不同。前面选择事实簇代表三元组时也遇到过这一问题。

**老师结论／项目规则：** ______________________________

## 建议最后形成的规则表

| 项目 | 待确定规则 |
|---|---|
| 证据范围 | 只依据实际输入；是否允许补全文上下文；禁止凭外部常识补全未提供的事实。 |
| 情态与来源 | 保留 may/might、能力、计划、怀疑、转述等信息，避免把非确定事实改成确定断言。 |
| 否定与限定 | 保留否定方向及其作用范围，检查条件、程度、时间、数量等限定是否影响真值。 |
| 并列拆分 | 在语义可分配时拆分；专名、共同动作、总数量和多组交叉并列设置例外。 |
| 定语拆分 | 可独立断言的属性或事件是否必须抽出；限制性定语的作用域如何保留。 |
| 信息粒度 | 区分事实错误、信息不完整、表达复合及冗余；是否同时保留粗粒度和细粒度事实。 |
| 表达边界 | 可接受的必要改写、关系/尾项边界变化、冠词及分词差异。 |
| Gold 冲突 | 保留官方版本，另列争议样本与审校结论；不能为提高匹配率选择性删改。 |
| 评估匹配 | 一条复合 Gold 与多条细粒度预测如何覆盖；反向多 Gold 对一预测如何计数，避免重复奖励。 |

## 来源与使用说明

- Fabrice Lamarche and Philippe Langlais (2024). BenchIE-FL: A Manually Re-Annotated Fact-Based Open Information Extraction Benchmark. [论文](https://aclanthology.org/2024.findings-acl.496/)。数据来源：[官方仓库](https://github.com/rali-udem/benchie_fl)，数据许可 CC BY 4.0。
- Kuicai Dong et al. (2021). DocOIE: A Document-level Context-Aware Dataset for OpenIE. [论文](https://aclanthology.org/2021.findings-acl.210/)。[官方仓库](https://github.com/daviddongkc/DocOIE)。
- 当前材料只支持案例讨论，不是新 Gold，也不是对数据集总体错误率的统计估计。候选表达、中文释义和初步判断由助手整理。
