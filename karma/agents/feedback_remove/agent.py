"""Task-focused remove feedback."""
from karma.agents.feedback_common import FeedbackAgent

SYSTEM_PROMPT = """依据源句自主识别重复三元组，选择保留项并删除完整重复项。完整回复采用本阶段指定的 JSON 格式。"""

TASK_PROMPT = """# 阶段一：核对并确定问题
1. 阅读源句与当前完整集合，自主查找表达同一事实的条目。
2. 比较主体、关系、客体，以及否定、可能性、条件、数量、时间和范围。
3. 回查文本差异和收到的 handoff 提示，依据源句区分完整重复、部分重叠和不同事实。

# 阶段二：生成本阶段操作
1. 对完整重复选择保留项：优先保留主体、关系、原文用词及必要限定正确的条目；同样正确且等价时保留编号较小的一条。
2. 为每项删除填写 index、keep_index、reason、evidence，说明重复依据和保留理由。
3. 保留不同事实。部分重叠或两条都需要修正时交给 replace；依据不足时保留当前结果并记录 review。

# 阶段三：复核并输出
1. 确认待删除条目的全部事实与必要限定均由保留项表达，保留仍含独有内容的条目。
2. 确认每个 keep_index 指向本轮最终保留的条目。
3. 输出 remove、handoff。收到的问题为空时，仍独立检查完整集合。"""

OUTPUT_RULES = """# 输出格式
返回 JSON 对象，包含 remove、handoff 两个数组；无内容的数组写 []。
remove 每项写 index、keep_index、reason、evidence；reason 简述重复依据与保留理由，evidence 引用源句。
handoff 每项写 target、source_sentence_ids、indices、problem：target 指处理阶段；indices 填当前相关条目编号，缺少条目时填 []；problem 简述具体位置与问题。
target 使用 add、replace、remove、text_generation、text_comparison 或 review；源句与三元组正确而重建文本或对比判断有误时，分别记录 text_generation 或 text_comparison。"""

EXAMPLES = """# 示例
示例仅列判断所需的输入字段，输出展示本阶段完整格式。

自主找重复，并说明保留谁
输入：{"source_sentences":[{"sentence_id":"S1","text":"The module receives signals and generates alerts."}],"current_collection":{"triples":[{"index":0,"head":"The module","relation":"receives","tail":"signals","source_sentence_ids":["S1"]},{"index":1,"head":"The module","relation":"receives","tail":"signals","source_sentence_ids":["S1"]},{"index":2,"head":"The module","relation":"generates","tail":"alerts","source_sentence_ids":["S1"]}]}}
输出：{"remove":[{"index":1,"keep_index":0,"reason":"两条完整表达相同的 receives 关系。","evidence":"The module receives signals and generates alerts."}],"handoff":[]}

字段部分重叠，不删除整条
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]},{"index":1,"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}}
输出：{"remove":[],"handoff":[{"target":"replace","source_sentence_ids":["S1"],"indices":[0,1],"problem":"两条分别表达 includes 和 processes；只是第 0 条的 tail 包含了内部关系。"}]}

同一主体、同一动作词也不一定重复
输入：{"source_sentences":[{"sentence_id":"S1","text":"The module may send a warning and must send a report."}],"current_collection":{"triples":[{"index":0,"head":"The module","relation":"may send","tail":"a warning","source_sentence_ids":["S1"]},{"index":1,"head":"The module","relation":"must send","tail":"a report","source_sentence_ids":["S1"]}]}}
输出：{"remove":[],"handoff":[]}"""

class FeedbackRemoveAgent(FeedbackAgent):
    stage = 'remove'
    task_prompt = TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
