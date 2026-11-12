"""Task-focused replace feedback."""
from karma.agents.feedback_common import FeedbackAgent

SYSTEM_PROMPT = """你负责检查并修正已有三元组，包括主语错误、词形错误、必要限定缺失和嵌套关系未拆分。
依据源句判断事实，结合当前完整集合确定修改；文本差异和前序提示用于帮助定位问题。
一条旧三元组可以替换成一条或多条，已有正确的独立关系保留在当前集合中。
输出 replace 和 handoff 两个数组，具体步骤与格式见本次任务说明。"""

TASK_PROMPT = """# 阶段一：核对并确定问题
1. 逐条读取当前三元组，包括前一步新增项，找到支持该关系的源句。
2. 根据源句确定主体、动作和对象，检查主语归属、词形、方向及目的、风险、条件联系。
3. 从源句找出当前条目各字段内部表达的关系。
4. 为每项内部关系分别确定主体、动作和对象，再查找当前集合中的独立条目。
5. 核对文本差异和收到的 handoff 提示；保留源句支持的正确条目。文本差异为空时仍完成上述检查。

# 阶段二：生成本阶段操作
1. 按源句修正 head、relation、tail，保留决定对象、关系含义或成立条件的修饰；省略 In some embodiments 这类句首背景。
2. 普通修正将一条完整结果放入 new_triples；拆分将外层关系及需要补出的内部关系放入同一 new_triples。
3. 逐项对照找到的内部关系：已有正确独立条目时保留；已有错误条目时直接修正；尚无独立条目时，将拆出的关系放入原条目的new_triples。
4. 每条内部关系使用自身的主体，并保留与目的、风险等外层内容的联系。
5. 内部关系独立后，调整外层字段，保留识别对象和表达必要限定所需的内容。a pre-step of grinding the rubber 说明具体步骤时可作为完整步骤名称。
6. or 保留选择范围；and 表示整套设备组成时保留集合主体，各对象独立参与关系时分别表达。
7. 完全遗漏的关系交给 add，需要删除的重复条目交给 remove；修改依据不足时保留当前结果并记录 review。

# 阶段三：复核并输出
1. 核对每条新结果的单句依据、实义词词形及必要限定。
2. 对照修改后的完整集合，确认原有正确关系仍有对应条目，补齐丢失的正确事实与必要限定。
3. 检查被修正的错误旧表达是否仍由其他条目保留：需要修正时一并替换；需要删除的完整重复条目交给remove。
4. 取消本轮重复生成的关系，合并对同一index的修改，输出replace、handoff。重建文本错误时保留正确三元组并记录问题。"""

OUTPUT_RULES = """# 输出格式
返回 JSON 对象，包含 replace、handoff 两个数组；无内容的数组写 []。
replace 每项写 index、reason、new_triples；reason 简述具体修正内容。
new_triples 至少包含一条，每条写 head、relation、tail、source_sentence_ids。
原 index 的整条三元组由 new_triples 中的全部条目替换，拆分结果直接放在这个数组中。
handoff 每项写 target、source_sentence_ids、indices、problem：target 指处理阶段；indices 填当前相关条目编号，缺少条目时填 []；problem 简述具体位置与问题。
target 使用 add、replace、remove、text_generation、text_comparison 或 review；源句与三元组正确而重建文本或对比判断有误时，分别记录 text_generation 或 text_comparison。"""

EXAMPLES = """# 示例
示例仅列判断所需的输入字段，输出展示本阶段完整格式。

一条嵌套三元组直接换成两条
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":0,"reason":"将原条目中的两项关系分别表达。","new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"]},{"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}],"handoff":[]}

已有内部关系时修正它，不再重复拆出
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]},{"index":1,"head":"The system","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":1,"reason":"processes 的主体是 a module。","new_triples":[{"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]},{"index":0,"reason":"内部关系已由第 1 条表达。","new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"]}]}],"handoff":[]}

同时修正主语、实义词词形和目的表达
输入：{"source_sentences":[{"sentence_id":"S1","text":"A cooling fan mounted near the outlet is used to remove excess heat."}],"current_collection":{"triples":[{"index":0,"head":"the outlet","relation":"removes","tail":"excess heat","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":0,"reason":"主语为冷却风扇；removes 改回原文 remove，保留 is used to 表达用途。","new_triples":[{"head":"A cooling fan mounted near the outlet","relation":"is used to remove","tail":"excess heat","source_sentence_ids":["S1"]}]}],"handoff":[]}

内部动作要保留与危险的联系
输入：{"source_sentences":[{"sentence_id":"S1","text":"The risk of cargo falling from the deck causes concern."}],"current_collection":{"triples":[{"index":0,"head":"cargo","relation":"falls from","tail":"the deck","source_sentence_ids":["S1"]},{"index":1,"head":"The risk of cargo falling from the deck","relation":"causes","tail":"concern","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":0,"reason":"保留风险与内部动作之间的联系及 falling 词形。","new_triples":[{"head":"The risk","relation":"is of cargo falling from","tail":"the deck","source_sentence_ids":["S1"]}]}],"handoff":[]}"""

class FeedbackReplaceAgent(FeedbackAgent):
    stage = 'replace'
    task_prompt = TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
