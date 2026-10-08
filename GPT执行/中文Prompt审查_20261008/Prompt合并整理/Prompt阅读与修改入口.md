# Prompt阅读与修改入口

2026年10月8日：已在 `E:\huawei after\KARMA` 将实体、关系的Prompt原文移回各自Agent。原来的 `extraction_support.py` 现在只保存JSON解析、字符串处理及分数校验工具。

## 实体Prompt：只看这个文件

[entity_extraction/agent.py](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py>)

| 阅读顺序 | 搜索名称及入口 | 负责什么 |
|---|---|---|
| 1 | [ENTITY_RULES，第19行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:19>) | 两轮共用的实体识别、边界与并列规则 |
| 2 | [system_prompt，第53行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:53>) | 两轮共用的身份、依据、类型和字段要求 |
| 3 | [_output_instructions，第66行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:66>) | 两轮共用的输出格式和示例 |
| 4 | [第一轮prompt，第92行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:92>) | 根据源文发现候选对象 |
| 5 | [第二轮prompt，第121行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:121>) | 结合源文、当前实体、三元组与差异审校候选集合 |

[difference_context，第33行](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:33>)保存差异解释文字，审校时会拼入Prompt。

## 关系Prompt：只看这个文件

[relationship_extraction/agent.py](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py>)

| 阅读顺序 | 搜索名称及入口 | 负责什么 |
|---|---|---|
| 1 | [FACT_RULES，第26行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:26>) | 两轮共用的完整事实、限定、拆分和重复判断规则 |
| 2 | [SCORE_RULES，第42行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:42>) | 两轮共用的三维评分定义 |
| 3 | [system_prompt，第84行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:84>) | 第一轮系统要求、输出格式及示例 |
| 4 | [第一轮prompt，第439行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:439>) | 根据源文和候选实体抽取三元组 |
| 5 | [第二轮prompt，第155行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:155>) | 根据源文及反馈生成add/remove/replace |
| 6 | [revision_system_prompt，第289行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:289>) | 第二轮专用的系统要求 |

[difference_context，第49行](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:49>)保存本Agent的差异解释文字。它与实体文件中有一份相同的内容，修改差异解释时应同步两处。

## 怎样修改

三引号内的自然语言是Prompt文字；`{text}`、实体JSON和三元组JSON等是运行时填入的数据；`+ ENTITY_RULES`或`{FACT_RULES}`表示把本文件顶部定义的规则拼进来。

修改两轮共用规则时，改本文件顶部的规则定义一次即可。修改某一轮的任务时，改对应函数里的`prompt`。修改输出结构和示例时，找到对应的输出说明。行号会随编辑变化，按上述名称搜索可以继续定位。

前面让你在 `extraction_support.py` 的 `FACT_RULES` 中补充“限定不能只写在证据里”，这项现在应在关系Agent的 `FACT_RULES` 中处理，入口为上面的第26行。此次只是原文搬移，未代替你正在逐项核对的措辞修改。

## 验证及版本状态

- 对比合并前后8种实际请求：两轮实体、两轮关系，分别覆盖无差异/有差异。system、user和调用参数全部逐字一致。
- 现有15项离线回归测试全部通过，没有调用模型或外部API。
- 此次源码仅修改实体Agent、关系Agent和extraction_support三个文件，改动尚未提交或推送。
- 修改的是当前主目录；`E:\huawei after\临时\KARMA` 保留原布局。两处Git提交号仍分别为main的127f1a1及更新分支的9d6883e，不能因此把整理后的工作文件看作已经上传GitHub。
- 合并前后请求记录及验证结果保存在本目录，便于核对。
