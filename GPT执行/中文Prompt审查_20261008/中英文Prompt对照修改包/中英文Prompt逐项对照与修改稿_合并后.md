# 中英文 Prompt 逐项对照与修改稿（合并后）

日期：2026年10月8日。已确定采用中文Prompt；本文件用于检查规则及编辑修改草案。主目录已完成未提交的Prompt位置整理，实际措辞保持不变；下列规则修改草案尚未应用。

## 版本与使用方式

- GitHub仓库：<https://github.com/lichuanpei12-coder/KARMA>。
- 当前主目录 `E:\huawei after\KARMA` 的Git HEAD仍为main的 `127f1a1399376fb5e9214cb656b045ca9a698a0b`；最近线上核查的远程main为同一提交。当前实体、关系与支持工具源码已有未提交的位置整理，HEAD相同不表示工作树未修改。
- 更新分支为 `codex/feedback-comparison-entity`，领先main两个提交，最新为 `9d6883e2e56a008ecf70bb5ca695fead32a1abea`，北京时间2026年9月11日11:06:48。
- 更新分支本地副本在 `E:\huawei after\临时\KARMA`，HEAD为上述9d6883e；保留合并前布局，本次未修改。两个目录的实体、关系和支持工具文件现在字节不同，不能沿用历史“8文件相同”结论描述当前状态。
- 中文摘录来自当前主目录；旧英文摘录来自 `E:\huawei after\KARMA\旧版\KARMA`。当前中文位置通过AST定位，旧英文行号保持不变；临时副本的实体/关系行号不适用本稿。
- ENTITY_RULES已移入实体agent；FACT_RULES、SCORE_RULES已移入关系agent；两份difference_context分别在各agent中。extraction_support仅保留结构解析与工具函数。
- 已有迁移验证记录确认8个实际请求的system/user/parameters逐字一致且无网络调用；这验证位置整理未改变Prompt，不表示修改草案已执行或模型效果已验证。
- 每项按“当前中文原文—旧英文原文—区别与建议—中文修改草案—我的修改记录”排列。可直接编辑草案和修改记录。
- 摘录保留源码中的Prompt措辞和行号，只移除Python字符串包裹；不把注释、中文回译或新写英文冒充原文。
- 旧版无对应条款时明确标注。完整核心模板和源文件链接另见同目录 `核心Prompt完整模板参考_合并后.md`。旧两份Markdown及原摘录定位JSON保留。

## 修改项索引

| 编号 | 修改项 | 有旧英文参考 |
|---|---|---|
| 01 | 文本重建：完整保留与压缩删减冲突 | 无对应模块 |
| 02 | 差异比较：只有完整语义等价的改写才忽略 | 无对应模块 |
| 03 | 差异比较：JSON示例需要合法 | 无对应模块 |
| 04 | 事实限定：明确最终三元组如何保留条件等信息 | 有，适用程度见该项说明 |
| 05 | 证据：统一第一轮和第二轮的来源与充分性要求 | 有，适用程度见该项说明 |
| 06 | 评分：补判定锚点，不把可能性自动当作低支持度 | 有，适用程度见该项说明 |
| 07 | 实体：补全称、简称、缩写及源内别名规则 | 有，适用程度见该项说明 |
| 08 | 实体：同类对象的类型名称保持一致 | 有，适用程度见该项说明 |
| 09 | 实体边界：原文提及与并列共享成分补齐的例外 | 有，适用程度见该项说明 |
| 10 | 内容语言：中文指令、源文字段和混合缩写分别规定 | 有，适用程度见该项说明 |
| 11 | 示例：补中文业务样例及第二轮实体审校样例 | 有，适用程度见该项说明 |
| 12 | 不确定情况：统一指代、方向和修订的保守处理 | 有，适用程度见该项说明 |
| 13 | Reader：旧生物医学领域规则需适配当前文档 | 有，适用程度见该项说明 |
| 14 | Summarizer：任务领域、长度和输入名称冲突（默认关闭） | 有，适用程度见该项说明 |
| 15 | Summarizer：示例不应将并列观察强化为因果（默认关闭） | 有，适用程度见该项说明 |
| 16 | Ingestion：估算年份与不猜测冲突（元数据调用停用） | 有，适用程度见该项说明 |

## 01. 文本重建：完整保留与压缩删减冲突

### 当前中文原文

**完整保留要求**：[agent.py:47](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:47>)，第47—59行。

```text
生成规则：
1. 保留三元组中的所有信息
2. 生成流畅、语法正确的句子
3. 适当时将相关三元组合并为连贯的段落
4. 保持原始含义，不添加外部知识
5. 使用适当的连接词和过渡
6. 输出语言必须与三元组中实体的语言保持一致（实体为英文则用英文输出，实体为中文则用中文输出）

质量标准：
- 准确性：三元组中的所有信息必须存在
- 流畅性：句子应自然阅读
- 连贯性：多个三元组应逻辑流畅
- 完整性：不应遗漏任何信息
```

**领域压缩与删减要求**：[agent.py:75](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:75>)，第75—108行。

```text
专利压缩的特定规则：
11. 按以下优先级排序（重要性从高到低）：
    - 系统架构和总体结构
    - 组件描述及其互连
    - 功能操作和工作流程
    - 独特或新颖的特征
    - 实施例和替代配置

12. 减少或移除：
    - 重复描述
    - 冗长的法律或程序性语言
    - 过于详细的背景信息
    - 对基本概念的冗余解释

合同和保密协议压缩的特定规则：

13. 按以下优先级排序（重要性从高到低）：
    - 当事人和定义：识别所有合同当事人和关键定义术语
    - 核心义务：每方必须做什么、交付或提供什么
    - 关键日期：生效日期、期限、续签、终止、通知期
    - 货币条款：费用、付款计划、罚款、上限、最低承诺
    - 法律条款：适用法律、管辖权、争议解决、保密、赔偿
    - 终止和存续：终止条件、终止后义务、存续条款
    - 保证和陈述：每方保证什么
    - 责任限制：责任上限、排除损害、免责声明

14. 减少或移除：
    - 重复的法律模板（例如，在多个章节中重复的标准不可抗力、通知条款）
    - 冗长的序言（"鉴于"条款提供上下文但几乎无可操作信息）
    - 过于详细的定义术语（不证自明或仅使用一次的术语）
    - 对文档内其他章节的冗余交叉引用
    - 没有特定管辖细节的标准适用法律条款
    - 收据确认或其他纯程序性语言
    - 不影响当前义务的历史背景或前置协议
```

**User忠实性与流畅性要求**：[agent.py:214](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:214>)，第214—231行。

```text
        忠实性规则：
        1. 生成文本中的每个关系必须直接存在于三元组中。
        2. 不要改变任何关系的强度或方向。
        3. 不要升级或强化任何关系。
        4. 不要降级或弱化任何关系。
        5. 不要添加三元组中没有的修饰词。
        6. 不要遗漏任何三元组。
        7. 如果合并会改变含义，不要将两个三元组合并为一个。
        8. 生成的句子必须忠实反映三元组的内容。

        流畅性规则：
        9. 尽可能将共享同一头实体的三元组合并为一个句子。
        10. 使用连接词（和、同时、其中、此外）来链接相关信息。
        11. 避免在相近位置重复同一个头实体。
        12. 使用关系从句（其中、那个）来平滑地附加修饰词。
        13. 变换句子结构以避免单调的短句列表。
        14. 当多个三元组共享同一关系时，将它们合并为一个结构化列表。
        15. 输出应读起来像一个连贯的段落，而非独立句子的列表。
```

### 旧英文原文

**无对应英文模块或条款。** 不补造英文原文。

### 区别与建议

旧版没有text_generation模块，没有可配对的英文重建Prompt。这是中文新增模块内部的冲突。

### 中文修改草案（尚未应用，可直接编辑）

```text
逐条忠实表达输入三元组，保留全部信息及否定、情态、条件、数量和方向。不得按领域重要性压缩或删除事实，不添加外部知识。仅在完整含义不变时合并句子；不得为连贯而添加因果、时间、组成、条件或指代关系。输出仅包含重建文本。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 02. 差异比较：只有完整语义等价的改写才忽略

### 当前中文原文

**差异验证与数量要求**：[agent.py:183](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:183>)，第183—208行。

```text
关键："unique_to_text_b"必须仅包含出现在文本B中但未出现在文本A中的信息。
如果文本B中的某个陈述也出现在文本A中（即使措辞略有不同），则不得将其包含在"unique_to_text_b"中。

验证规则：
- "unique_to_text_b"必须包含出现在文本B中但未出现在文本A中的信息。
- 如果文本B中的某个陈述是对文本A中已有内容的改写、摘要或浓缩，则不要将其包含在"unique_to_text_b"中。
- 在向"unique_to_text_b"添加项之前，先问："这个声明是否在文本A中明确陈述或清晰暗示？"如果是，则不要包含。
- "unique_to_text_b"应仅包含文本A中确实找不到的真正新信息。

具体性规则：
- 不要说"文本A更详细"——要说文本A有什么。
- 不要说"文本B缺少细节"——要说缺少了什么。
- 不要说"文本A涵盖更多"——列出涵盖了什么。
- 引用文本中的具体短语、数字、实体或声明。
- 每个差异/独特项应可追溯回原始文本。

提取规则：
- 提取文本A中存在但文本B中缺失的事实元素 → 放入"unique_to_text_a"
- 提取文本B中存在但文本A中缺失的事实元素 → 放入"unique_to_text_b"
- 引用文本中的具体短语、数字、实体、条款或声明。
- 每个项必须可追溯回原始文本。

数量要求：
- unique_to_text_a：尽可能多的具体事实
- unique_to_text_b：尽可能多的具体事实
- 每个项必须是单一的、原子性的事实（非组合句子）
```

### 旧英文原文

**无对应英文模块或条款。** 不补造英文原文。

### 区别与建议

旧版没有text_comparison模块，没有对应英文Prompt。A有B无与B有A无应使用相同的事实判定标准。

### 中文修改草案（尚未应用，可直接编辑）

```text
只有完整事实含义相同的表达才视为等价，包括主客体、方向、否定、情态、条件、数量、时间及限定范围。改写、摘要或浓缩若改变或遗漏这些信息，仍应报告差异。不得凭领域常识认定文本已表达某事实。覆盖全部可核实差异，去除重复与猜测；确无差异时返回空数组。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 03. 差异比较：JSON示例需要合法

### 当前中文原文

**当前输出示例**：[agent.py:49](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:49>)，第49—55行。

```text
输出格式：
返回具有此结构的 JSON 对象：
{

    "unique_to_text_a": ["仅在文本A中的具体元素（引用或转述）", ...],
    "unique_to_text_b": ["仅在文本B中的具体元素（引用或转述）", ...],
}
```

### 旧英文原文

**无对应英文模块或条款。** 不补造英文原文。

### 区别与建议

旧版无对应模块。当前示例中的省略号和尾逗号不能作为合法JSON直接解析。

### 中文修改草案（尚未应用，可直接编辑）

```text
仅返回合法JSON对象，无差异时使用：
{"unique_to_text_a": [], "unique_to_text_b": []}
有差异时两字段均为字符串数组，不使用省略号或尾逗号。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 04. 事实限定：明确最终三元组如何保留条件等信息

### 当前中文原文

**两轮共用的事实规则**：[agent.py:26](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:26>)，第26—40行。

```text
1. 逐句检查源文本支持的事实，包括动作、状态、定义、组成、属性与比较关系。
   同一对象可能参与多个独立事实，分别检查；抽取数量由源文本的事实数量决定。
2. 将 head、relation、tail 作为完整事实判断。主动和被动表达均结合语法确认角色，
   按源文本的表达保留方向、否定、情态、条件和数量范围。
3. head 和 tail 保留必要的限定词和修饰语，可使用代词或充当宾语的较长表达。
   relation 使用源文本措辞、大小写和空格；例如 "mounts to" 保持 "mounts to"。
   并列项省略的共享词可按原文语法补齐，其余措辞保持原文表达。
4. 每条三元组表达一个独立事实。复合动作在各自得到源文本支持时拆分；
   目的、条件和可能性保留相应限定。例如 "queries the ECU to determine the location"
   中的目的并不等于已经确定了位置，抽取时保留这一语义区别。
5. 候选实体帮助检查对象和边界，最终头尾以源文本为准，可以补充名单之外的表达。
   候选对象只被提及而没有对应事实时，可以保持未连接状态。
6. 按完整事实检查重复；主动被动改写或轻微边界变化在语义等价时视为同一事实，
   否定、情态、条件或数量不同的陈述分别核实。

```

**第一轮输出字段**：[agent.py:92](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:92>)，第92—93行。

```text
完整回复采用 JSON 数组，每项包含 head、relation、tail、context、
confidence、clarity、relevance。context 使用原文支撑片段。无可抽取事实时返回 []。
```

### 旧英文原文

**旧英文质量控制，包含相反规则**：[agent.py:100](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:100>)，第100—105行。

```text
QUALITY CONTROLS:
- Ignore negated relationships ("does not treat", "no association")
- Avoid circular relationships (A-B, B-A unless distinct)
- Prioritize specific over general relationships
- Ensure entity names match exactly from entity extraction
- Include supporting evidence text
```

**旧英文输出结构**：[agent.py:107](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:107>)，第107—117行。

```text
OUTPUT FORMAT:
Return only valid JSON array:
[
  {
    "head": "exact_entity_name",
    "relation": "RELATIONSHIP_TYPE",
    "tail": "exact_entity_name",
    "confidence": 0.85,
    "evidence": "direct quote supporting relationship"
  }
]
```

### 区别与建议

旧英文没有同功能的限定承载规则，且要求忽略否定。这一旧规则不应恢复。中文已有保护要求，缺的是限定在最终结果中如何保存的约定。

### 中文修改草案（尚未应用，可直接编辑）

```text
head、relation、tail的完整组合必须保留原文的否定、情态、条件和数量范围，必要限定不得只放入context或evidence。不能为了缩短三元组删除限制，必要时保留较长原文表达。若采用独立限定字段，须同时修改数据结构、重建输入、去重和评价。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 05. 证据：统一第一轮和第二轮的来源与充分性要求

### 当前中文原文

**第一轮context**：[agent.py:92](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:92>)，第92—93行。

```text
完整回复采用 JSON 数组，每项包含 head、relation、tail、context、
confidence、clarity、relevance。context 使用原文支撑片段。无可抽取事实时返回 []。
```

**第二轮evidence**：[agent.py:193](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:193>)，第193—194行。

```text
- add 和 replace 的 evidence 使用源文本中逐字复制的连续片段，
  覆盖支持三元组的完整上下文。
```

**实体context**：[agent.py:58](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:58>)，第58—59行。

```text
完整回复采用 JSON 数组，每项含 mention、type、context。
mention 是候选表达，context 是源文本中支持该候选的上下文片段。
```

### 旧英文原文

**旧英文关系条件**：[agent.py:78](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:78>)，第78—79行。

```text
- Evidence must be present within the analyzed text segment
- Relationship direction must be determinable from context
```

**旧英文关系证据要求**：[agent.py:105](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:105>)，第105—105行。

```text
- Include supporting evidence text
```

**旧英文关系输出字段**：[agent.py:111](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:111>)，第111—115行。

```text
    "head": "exact_entity_name",
    "relation": "RELATIONSHIP_TYPE",
    "tail": "exact_entity_name",
    "confidence": 0.85,
    "evidence": "direct quote supporting relationship"
```

**旧英文实体输出，无context字段**：[agent.py:85](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:85>)，第85—94行。

```text
OUTPUT FORMAT:
Return only a valid JSON array with this exact structure:
[
  {
    "mention": "exact text from source",
    "type": "CATEGORY_NAME",
    "normalized_id": "ontology:identifier or N/A",
    "aliases": ["synonym1", "synonym2"]
  }
]
```

### 区别与建议

英文关系要求直接引文，可以借鉴；英文实体没有context证据要求，不能把关系证据冒充实体证据。英文也没有第二轮增量证据规则。

### 中文修改草案（尚未应用，可直接编辑）

```text
context或evidence应逐字引用源文，覆盖支持完整事实及其限定的连续上下文。存在跨句指代时包含必要前文。不以释义替代原文证据。JSON键按各接口保留，但证据标准统一。还需代码保存证据并校验其确实来自源文。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 06. 评分：补判定锚点，不把可能性自动当作低支持度

### 当前中文原文

**当前三维评分定义**：[agent.py:42](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:42>)，第42—44行。

```text
confidence 表示源文本对事实的支持强度，clarity 表示头尾和关系表达的
清晰程度，relevance 表示事实与文档主题的相关程度。三个维度分别评估，取值为
0.0 到 1.0；分别有依据时可以相同。分数表达判断，不替代事实核实。
```

**当前may query评分示例**：[agent.py:103](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:103>)，第103—104行。

```text
  {"head": "It", "relation": "may query", "tail": "the ECU",
   "context": "It may query the ECU.", "confidence": 0.95, "clarity": 0.8, "relevance": 0.9}
```

### 旧英文原文

**旧英文confidence分档**：[agent.py:81](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:81>)，第81—98行。

```text
CONFIDENCE SCORING:
HIGH CONFIDENCE (0.8-1.0):
- Direct experimental evidence stated
- Quantitative measurements provided
- Established scientific facts
- Clear causal language

MODERATE CONFIDENCE (0.5-0.7):
- Observational evidence
- Statistical associations
- Literature citations mentioned
- Qualified statements (may, appears to, suggests)

LOW CONFIDENCE (0.3-0.4):
- Preliminary findings
- Hypothetical relationships
- Weak associations
- Speculative statements
```

### 区别与建议

旧英文可以借鉴分档结构，医学实验标准及may自动降分不宜复制。当前confidence衡量抽取事实与源文是否一致，不衡量事件已发生的概率。

### 中文修改草案（尚未应用，可直接编辑）

```text
confidence衡量原文对完整陈述的支持度；原文明说“可能”且结果保留“可能”，可以具有高支持度。缺少原文支持的事实不应因给低分而输出。clarity衡量角色和表达是否清楚，不能因对象短语长而机械降分。relevance衡量与当前文档主题的相关性。为三维分别提供高、中、低的可观察判定示例，再统一数值区间。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 07. 实体：补全称、简称、缩写及源内别名规则

### 当前中文原文

**当前最接近的不同提及规则**：[agent.py:24](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:24>)，第24—24行。

```text
3. 代词保留原文提及，结合上下文理解其指代。不同提及形式分别保留，供事实判断使用。
```

### 旧英文原文

**旧英文缩写与别名规则**：[agent.py:75](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:75>)，第75—77行。

```text
- Capture abbreviated forms and acronyms
- Identify synonyms and alternative names
- Distinguish context-dependent meanings
```

**旧英文User别名要求**：[agent.py:151](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:151>)，第151—151行。

```text
        4. Include common aliases if applicable
```

### 区别与建议

当前未单列此要求，不等于模型无法识别。只吸收原文出现的形式，不恢复外部知识生成别名。

### 中文修改草案（尚未应用，可直接编辑）

```text
原文出现的全称、简称、缩写及明确标注的别名分别保留为候选，不推测未出现的展开形式，不凭外部知识生成别名或身份关系。不同提及形式分别保留，是否等价仅依据原文明确说明。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 08. 实体：同类对象的类型名称保持一致

### 当前中文原文

**当前类型要求**：[agent.py:57](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:57>)，第57—57行。

```text
类型使用简短、贴合语境的名称；不确定时填写 Unknown。
```

### 旧英文原文

**旧英文一致性要求**：[agent.py:83](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:83>)，第83—83行。

```text
- Consistency: uniform handling of similar entity types
```

**旧英文User类型要求**：[agent.py:149](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:149>)，第149—149行。

```text
        2. Assign the most specific entity type
```

### 区别与建议

不需要恢复固定医学类型；应在当前开放对象范围中统一命名。类型语言与命名表可在此修改稿中进一步确定。

### 中文修改草案（尚未应用，可直接编辑）

```text
类型使用简短、贴合语境的名称，同篇文档中同类对象使用一致的类型名称和命名语言；不要将同类对象交替标为多个同义类型。不确定时填写Unknown。类型命名不能改变原文提及或缩窄允许抽取的对象范围。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 09. 实体边界：原文提及与并列共享成分补齐的例外

### 当前中文原文

**输出中的原文提及**：[agent.py:69](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:69>)，第69—70行。

```text
返回完整候选实体集合，重复的相同提及保留一次。无候选时返回 []。
每项格式为 {"mention": "原文提及", "type": "类别或 Unknown", "context": "原文上下文"}。
```

**边界与并列补齐要求**：[agent.py:22](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:22>)，第22—26行。

```text
2. 保留决定含义的限定词、修饰语、数值和编号，保持原文大小写与空格。
   例如 "a variety of systems" 保留整体，"the measured traffic per time" 保留整体。
3. 代词保留原文提及，结合上下文理解其指代。不同提及形式分别保留，供事实判断使用。
4. 并列项在各自含义明确时分别识别；省略的共享词可按原文语法补齐。
   例如 "first and second cables" 对应 "first cable" 和 "second cable"。
```

### 旧英文原文

**旧英文精确提及要求**：[agent.py:72](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:72>)，第72—74行。

```text
- Extract exact mentions as they appear in text
- Preserve original capitalization and formatting
- Include multi-word expressions as single entities
```

**旧英文mention字段**：[agent.py:89](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:89>)，第89—89行。

```text
    "mention": "exact text from source",
```

### 区别与建议

英文没有并列补齐规则。中文的合法语法补齐应保留，但不能与通常逐字保留的要求混淆。

### 中文修改草案（尚未应用，可直接编辑）

```text
通常逐字保留源文表达及其必要限定、大小写和格式。仅对语法明确的并列项允许补齐共享成分，例如first and second cables可识别为first cable与second cable。补齐不允许翻译、同义改写或加入外部信息；证据仍引用原文。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 10. 内容语言：中文指令、源文字段和混合缩写分别规定

### 当前中文原文

**原格式要求**：[agent.py:22](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:22>)，第22—23行。

```text
2. 保留决定含义的限定词、修饰语、数值和编号，保持原文大小写与空格。
   例如 "a variety of systems" 保留整体，"the measured traffic per time" 保留整体。
```

**类型及字段要求**：[agent.py:57](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:57>)，第57—59行。

```text
类型使用简短、贴合语境的名称；不确定时填写 Unknown。
完整回复采用 JSON 数组，每项含 mention、type、context。
mention 是候选表达，context 是源文本中支持该候选的上下文片段。
```

**System按实体语言决定输出**：[agent.py:53](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:53>)，第53—53行。

```text
6. 输出语言必须与三元组中实体的语言保持一致（实体为英文则用英文输出，实体为中文则用中文输出）
```

**User按实体语言决定输出**：[agent.py:212](<E:/huawei after/KARMA/karma/agents/text_generation/agent.py:212>)，第212—212行。

```text
        输出语言必须与三元组中实体的语言保持一致（实体为英文则用英文输出，实体为中文则用中文输出）。
```

**比较输出语言**：[agent.py:218](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:218>)，第218—218行。

```text
重要：输出内容必须与上方输入文本的语言保持一致。输入文本为英文时，所有输出内容必须使用英文，不要使用中文。
```

### 旧英文原文

**旧英文原文保留要求**：[agent.py:72](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:72>)，第72—73行。

```text
- Extract exact mentions as they appear in text
- Preserve original capitalization and formatting
```

### 区别与建议

两版都没有完整的集中语言约定。旧英文这里只是原文保留参考，不能冒充完整对应条款。中文关系中出现ECU等字母缩写不应自动把整段输出切换成英文。

### 中文修改草案（尚未应用，可直接编辑）

```text
任务指令采用中文。mention、head、relation、tail及原始证据保留源文表达和语言，不为中文指令翻译英文事实。JSON键保持程序约定。type使用统一命名约定，Unknown原样保留；审校reason使用中文。混合文本按事实原表达生成，不凭字母缩写判定整段语言。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 11. 示例：补中文业务样例及第二轮实体审校样例

### 当前中文原文

**当前初抽示例**：[agent.py:72](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:72>)，第72—80行。

```text
# 示例
源文本：The controller may query the ECU. It stores the readings.
输出：
[
  {"mention": "The controller", "type": "Component", "context": "The controller may query the ECU."},
  {"mention": "the ECU", "type": "Component", "context": "The controller may query the ECU."},
  {"mention": "It", "type": "Unknown", "context": "It stores the readings."},
  {"mention": "the readings", "type": "Data", "context": "It stores the readings."}
]
```

**当前E2任务**：[agent.py:121](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:121>)，第121—123行。

```text
        prompt = f"""# 任务
依据源文本审校当前候选实体集合，返回完整的审校后集合。
保留有效候选，补充遗漏，修正边界，移除缺少源文本依据的候选。
```

**当前E2审校顺序**：[agent.py:144](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:144>)，第144—148行。

```text
# 审校顺序
1. 对照源文本逐项核对当前候选，保留有效提及并修正边界。
2. 结合三元组头尾和差异线索，检查源文本中遗漏的对象。
3. 候选是否有效取决于源文本；没有参与当前三元组的有效候选仍然保留。
4. 核对完整集合包含所有保留、修正和新增的候选，最后按输出格式生成数组。
```

### 旧英文原文

**旧英文实体示例**：[agent.py:101](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/entity_extraction/agent.py:101>)，第101—107行。

```text
EXAMPLES:
Text: "Aspirin inhibits COX-2 enzyme activity"
Output:
[
  {"mention": "Aspirin", "type": "DRUG", "normalized_id": "MESH:D001241", "aliases": ["acetylsalicylic acid"]},
  {"mention": "COX-2", "type": "PROTEIN", "normalized_id": "NCBI:5743", "aliases": ["cyclooxygenase-2", "PTGS2"]}
]
```

### 区别与建议

两版示例源文都为英文；旧英文没有E2任务或对应样例。当前E2复用初抽输出说明，需新增审校样例。下面是新增中文示例草案，不是源码原文。

### 中文修改草案（尚未应用，可直接编辑）

```text
新增样例源文：控制器可以查询ECU。ECU存储读数。
当前候选：控制器、ECU、读数、GPS。当前错误三元组：控制器—包含—ECU。
审校要点：源文中的ECU真实存在，关系错误不应导致删除ECU；GPS无源文依据，应删除；若读数漏抽，应补回。另增加中文否定、条件、并列共享成分和长宾语样例。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 12. 不确定情况：统一指代、方向和修订的保守处理

### 当前中文原文

**代词保留**：[agent.py:24](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:24>)，第24—24行。

```text
3. 代词保留原文提及，结合上下文理解其指代。不同提及形式分别保留，供事实判断使用。
```

**语法角色与方向**：[agent.py:28](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:28>)，第28—30行。

```text
2. 将 head、relation、tail 作为完整事实判断。主动和被动表达均结合语法确认角色，
   按源文本的表达保留方向、否定、情态、条件和数量范围。
3. head 和 tail 保留必要的限定词和修饰语，可使用代词或充当宾语的较长表达。
```

**第二轮无法确认的处理**：[agent.py:197](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:197>)，第197—197行。

```text
- 差异仅提供候选线索，每项修改以源文本核实结果为准。无法确认的疑点保留原状态。
```

### 旧英文原文

**旧英文实体及方向条件**：[agent.py:76](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/relationship_extraction/agent.py:76>)，第76—79行。

```text
- Both entities must be explicitly mentioned in text
- Relationship must be explicitly stated or clearly implied
- Evidence must be present within the analyzed text segment
- Relationship direction must be determinable from context
```

### 区别与建议

旧英文没有代词歧义或第二轮保守修订规则。保留未能确认的旧条目，不等于它已经被核实正确。

### 中文修改草案（尚未应用，可直接编辑）

```text
不得自行补全无法确认的指代、身份、角色、关系方向或限定范围。能忠实表达的原文代词可以保留，不能无依据替换为具体对象。第一轮不新增需要猜测的事实；第二轮无足够依据修订时保留原条目，另记录待核查状态，不把保留解释为确认正确。待核查状态需要相应接口支持。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 13. Reader：旧生物医学领域规则需适配当前文档

### 当前中文原文

**角色与评分目标**：[agent.py:36](<E:/huawei after/KARMA/karma/agents/reader/agent.py:36>)，第36—38行。

```text
你是一个专门用于生物医学文献分析的阅读代理。你的任务是评估文本段落并为知识提取分配精确的相关性分数。

目标：根据文本段落包含可提取生物医学知识关系的潜力，对其进行评分（0.0-1.0）。
```

**低相关性分类**：[agent.py:55](<E:/huawei after/KARMA/karma/agents/reader/agent.py:55>)，第55—60行。

```text
低相关性（0.1-0.3）：
- 没有结果的方法描述
- 致谢、资助信息
- 没有解释的纯统计分析
- 设备描述或操作规程
- 作者所属机构和联系信息
```

**评分要求**：[agent.py:68](<E:/huawei after/KARMA/karma/agents/reader/agent.py:68>)，第68—73行。

```text
评分要求：
- 仅返回一个 0.0 到 1.0 之间的浮点数
- 考虑生物医学术语密度
- 优先考虑描述实体之间关系的内容
- 考虑特定测量或结果的存在
- 评估实体-关系提取的潜力
```

### 旧英文原文

**旧英文角色与目标**：[agent.py:44](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/reader/agent.py:44>)，第44—46行。

```text
You are a specialized Reader Agent for biomedical literature analysis. Your task is to evaluate text segments and assign precise relevance scores for knowledge extraction.

OBJECTIVE: Score text segments (0.0-1.0) based on their potential to contain extractable biomedical knowledge relationships.
```

**旧英文低相关性分类**：[agent.py:63](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/reader/agent.py:63>)，第63—68行。

```text
LOW RELEVANCE (0.1-0.3):
- Methodological descriptions without outcomes
- Acknowledgments, funding information
- Pure statistical analysis without interpretation
- Equipment descriptions or protocols
- Author affiliations and contact information
```

**旧英文评分要求**：[agent.py:76](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/reader/agent.py:76>)，第76—81行。

```text
SCORING REQUIREMENTS:
- Return only a single float value between 0.0 and 1.0
- Consider biomedical terminology density
- Prioritize content describing relationships between entities
- Account for presence of specific measurements or outcomes
- Evaluate potential for entity-relationship extraction
```

### 区别与建议

这是旧英文继承问题；不能说中文翻译漏掉技术领域规则。Reader默认评分，但当前不按此结果裁剪默认抽取全文。

### 中文修改草案（尚未应用，可直接编辑）

```text
根据段落包含源文可支持事实的潜力评分，覆盖动作、状态、定义、组成、属性与比较。设备描述、操作流程、系统组件和条件参数可能具有很高抽取价值，不能仅因文档类型而判低相关。不使用生物医学术语密度作为通用文档评分标准。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 14. Summarizer：任务领域、长度和输入名称冲突（默认关闭）

### 当前中文原文

**当前System角色和长度**：[agent.py:35](<E:/huawei after/KARMA/karma/agents/summarizer/agent.py:35>)，第35—37行。

```text
你是一个专门用于生物医学文献处理的摘要代理。你的任务是创建简洁、信息密集的摘要，保留所有与知识相关的内容。

目标：将文本段落转化为简洁的摘要（<=100词），同时保留所有对知识提取至关重要的实体、关系和定量数据。
```

**当前System输出要求**：[agent.py:61](<E:/huawei after/KARMA/karma/agents/summarizer/agent.py:61>)，第61—65行。

```text

输出格式：
- 单一段落，最多100词
- 完整的句子，使用正确的科学语法
- 不使用项目符号或碎片化短语
```

**当前User任务和长度**：[agent.py:128](<E:/huawei after/KARMA/karma/agents/summarizer/agent.py:128>)，第128—139行。

```text
            你是一个文档压缩代理。你的任务是将文档压缩为简洁、信息密集的摘要，同时保留所有关键技术信息。
            生成的摘要理想长度应在 400 到 600 词之间。

            ## 输入
            包含技术描述、系统架构、组件和实施例的文档。

            ## 压缩规则
            质量标准：
            - 准确性：三元组中的所有信息必须存在
            - 流畅性：句子应自然阅读
            - 连贯性：多个三元组应逻辑流畅
            - 完整性：不应遗漏任何信息
```

### 旧英文原文

**旧英文System**：[agent.py:35](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/summarizer/agent.py:35>)，第35—37行。

```text
You are a specialized Summarizer Agent for biomedical literature processing. Your task is to create concise, information-dense summaries that preserve all knowledge-relevant content.

OBJECTIVE: Transform text segments into concise summaries (≤100 words) while preserving all entities, relationships, and quantitative data essential for knowledge extraction.
```

**旧英文System输出**：[agent.py:61](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/summarizer/agent.py:61>)，第61—65行。

```text

OUTPUT FORMAT:
- Single paragraph, maximum 100 words
- Complete sentences with proper scientific grammar
- No bullet points or fragmented phrases
```

**旧英文User**：[agent.py:126](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/summarizer/agent.py:126>)，第126—140行。

```text
        Summarize the following biomedical text in 2-4 sentences, keeping it under 100 words.

        Critical Requirements:
        - Retain ALL technical terms (genes, proteins, drugs, diseases, chemicals)
        - Preserve ALL numeric data (concentrations, p-values, percentages, doses)
        - Keep relationship indicators (inhibits, activates, treats, causes, etc.)
        - Maintain scientific precision and accuracy
        - Use clear, unambiguous language

        If the text contains very little scientific information, provide a brief summary or return "[LOW CONTENT]".

        Provide only the summary with no additional text, formatting, or explanations.

        Text to summarize:
        {text}
```

### 区别与建议

System近似翻译，User从医学摘要改成技术压缩，产生100词与400—600词冲突。此模块默认关闭，重新开启前统一；不能把它当作当前默认流程已经造成摘要遗漏。

### 中文修改草案（尚未应用，可直接编辑）

```text
启用前先确定摘要的业务用途，再统一System、User与代码长度限制。输入是源文档，不应误称三元组。需要完整事实抽取时，应避免把压缩摘要作为唯一事实来源；若不需要摘要，保持默认关闭。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 15. Summarizer：示例不应将并列观察强化为因果（默认关闭）

### 当前中文原文

**当前示例**：[agent.py:69](<E:/huawei after/KARMA/karma/agents/summarizer/agent.py:69>)，第69—71行。

```text
输入："阿司匹林治疗（每日100mg）显著减少骨骼肌中的炎症标志物。COX-2活性较安慰剂组降低45%（p<0.001）。PGE2水平也显著降低（2.1 +/- 0.3 vs 4.2 +/- 0.5 ng/ml, p<0.05）。"

输出："阿司匹林治疗（每日100mg）通过降低COX-2活性45%（p<0.001）显著减少骨骼肌炎症标志物。PGE2水平显著降低（2.1 +/- 0.3 vs 4.2 +/- 0.5 ng/ml, p<0.05）。"
```

### 旧英文原文

**旧英文示例**：[agent.py:69](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/summarizer/agent.py:69>)，第69—71行。

```text
Input: "Treatment with aspirin (100mg daily) significantly reduced inflammatory markers in skeletal muscle. COX-2 activity decreased by 45% (p<0.001) compared to placebo group. PGE2 levels were also significantly reduced (2.1 ± 0.3 vs 4.2 ± 0.5 ng/ml, p<0.05)."

Output: "Aspirin treatment (100mg daily) significantly reduced inflammatory markers in skeletal muscle by decreasing COX-2 activity 45% (p<0.001) versus placebo. PGE2 levels were significantly reduced (2.1 ± 0.3 vs 4.2 ± 0.5 ng/ml, p<0.05)."
```

### 区别与建议

英文原示例也使用by decreasing COX-2，中文通过降低COX-2继承了同样的因果强化。此处是两版共有问题。

### 中文修改草案（尚未应用，可直接编辑）

```text
摘要只能保留源文明确支持的因果或机制。原文并列报告治疗后指标变化时，描述观察到的各项变化，不额外写成“通过某变化导致另一结果”。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：


## 16. Ingestion：估算年份与不猜测冲突（元数据调用停用）

### 当前中文原文

**日期字段规则**：[agent.py:56](<E:/huawei after/KARMA/karma/agents/ingestion/agent.py:56>)，第56—59行。

```text
3. 期刊：提供完整的期刊名称，不使用缩写
4. 发布日期：使用 YYYY-MM-DD 格式，如果月/日不可用则估算年份
5. DOI：提取完整的 DOI，包括"10."前缀
6. PMID：如果存在则提取 PubMed ID
```

**准确性规则**：[agent.py:62](<E:/huawei after/KARMA/karma/agents/ingestion/agent.py:62>)，第62—66行。

```text
质量标准：
- 对确实无法提取的字段使用"Unknown"
- 专有名词保持原始大写
- 不要编造或猜测缺失的信息
- 如果存在多个标题，选择主要的研究标题
```

### 旧英文原文

**旧英文日期规则**：[agent.py:70](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/ingestion/agent.py:70>)，第70—73行。

```text
3. JOURNAL: Provide full journal name, not abbreviations
4. PUB_DATE: Use YYYY-MM-DD format, estimate year if month/day unavailable
5. DOI: Extract complete DOI including "10." prefix
6. PMID: Extract PubMed ID if present
```

**旧英文准确性规则**：[agent.py:76](<E:/huawei after/KARMA/旧版/KARMA/karma/agents/ingestion/agent.py:76>)，第76—80行。

```text
QUALITY STANDARDS:
- Use "Unknown" for genuinely unextractable fields
- Maintain original capitalization for proper nouns
- Do not invent or guess missing information
- If multiple titles exist, select the primary research title
```

### 区别与建议

冲突是旧英文继承的；当前元数据模型调用停用。该文件User仍为英文，如以后启用，应一并改为中文任务指令。

### 中文修改草案（尚未应用，可直接编辑）

```text
只提取文中明确给出的发表日期；缺失时使用Unknown，不根据研究内容、文风或引用推测年份。若业务需要日期推断，应单列推断字段及依据，不能冒充文档已给出的元数据。
```

### 我的修改记录

- 采用的措辞：
- 需要进一步确认的规则：
- 对应源码修改位置：

## 配套代码问题：与Prompt修改分开处理

| 问题 | 位置 | 原因 |
|---|---|---|
| 实体context未强制验证 | [agent.py:176](<E:/huawei after/KARMA/karma/agents/entity_extraction/agent.py:176>)，第176—187行 | 目前主要验证mention，证据缺失仍可接受 |
| 三元组对象未保存证据 | [agent.py:418](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:418>)，第418—433行；[data_structures.py:30](<E:/huawei after/KARMA/karma/core/data_structures.py:30>)，第30—30行 | 原回复在审计中，标准结果没有context/evidence字段 |
| 第二轮evidence仅检查非空 | [agent.py:370](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:370>)，第370—370行 | 没验证逐字来自源文 |
| 去重只用小写头关系尾 | [agent.py:578](<E:/huawei after/KARMA/karma/agents/relationship_extraction/agent.py:578>)，第578—578行 | 不能区分只存在于证据中的不同条件 |
| 比较解析失败返回空差异 | [agent.py:258](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:258>)，第258—267行 | 与真正没有差异混淆 |
| 调用失败用两侧前200字代替差异 | [agent.py:307](<E:/huawei after/KARMA/karma/agents/text_comparison/agent.py:307>)，第307—314行 | 这些是未比较的文本片段，不能当成已核实差异 |

Evaluator、Conflict和Schema现行执行的是Python评分或规则，不是把system文字交给模型完成所有检查。修改其文字不能代替实现修改。当前未调用的医学评分备用函数也不能作为现行模型已被医学规则错误评分的证据。

## 建议修改顺序

先处理01—05的当前反馈与事实保真问题，再完善06—12的核心规则。13的Reader需适配当前领域；14—16为关闭或停用模块，启用前处理。配套代码问题需与证据及错误状态一起实现。修改后的验证使用实际业务样本，检查忠实性、完整性和反馈准确性。
