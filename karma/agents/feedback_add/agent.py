"""Task-focused add feedback."""
from karma.agents.feedback_common import FeedbackAgent

SYSTEM_PROMPT = """你负责依据源句补充当前集合完全遗漏的关系，并自主检查源句中的遗漏。
结合当前完整集合判断是否需要新增；文本差异和前序提示用于帮助定位问题。
已有表达需要修正或拆分时，将对应条目和具体问题交给 replace；已有正确独立表达时保留现有条目。
输出 add 和 handoff 两个数组，具体步骤与格式见本次任务说明。"""

TASK_PROMPT = """# 阶段一：核对并确定问题
1. 逐句找出源句明确表达的关系，确定主体、动作或状态、对象及必要限定。
2. 在当前完整集合中查找这些关系，同时检查长字段包含的内容。
3. 核对文本差异和收到的 handoff 提示，回查对应源句与当前条目，确定实际遗漏。

# 阶段二：生成本阶段操作
1. 关系在整个集合中都没有表达时，生成新增三元组，使用源句中的主体、词形及必要限定。
2. 已有正确独立表达时保留现有条目；已有表达需要修正时，在 handoff 中记录编号与具体问题，交给 replace。
3. 关系包含在长字段中、尚无独立表达时，将对应条目交给 replace 拆分。

# 阶段三：复核并输出
1. 逐条对照源句核对新增关系及必要限定。
2. 将拟新增关系与当前集合及本轮新增项逐一比较，同一事实只保留一份表达。
3. 输出 add、handoff。文本差异或收到的问题为空时，仍完成逐句检查。"""

OUTPUT_RULES = """# 输出格式
返回 JSON 对象，包含 add、handoff 两个数组；无内容的数组写 []。
add 每项写 head、relation、tail、source_sentence_ids、reason；reason 简述哪项关系完全遗漏。
handoff 每项写 target、source_sentence_ids、indices、problem：target 指处理阶段；indices 填当前相关条目编号，缺少条目时填 []；problem 简述具体位置与问题。
target 使用 add、replace、remove、text_generation、text_comparison 或 review；源句与三元组正确而重建文本或对比判断有误时，分别记录 text_generation 或 text_comparison。"""

EXAMPLES = """# 示例
示例仅列判断所需的输入字段，输出展示本阶段完整格式。

源句有关系完全没有抽取
输入：{"source_sentences":[{"sentence_id":"S1","text":"The controller reads and stores sensor data."}],"current_collection":{"triples":[{"index":0,"head":"The controller","relation":"reads","tail":"sensor data","source_sentence_ids":["S1"]}]}}
输出：{"add":[{"head":"The controller","relation":"stores","tail":"sensor data","source_sentence_ids":["S1"],"reason":"当前只表达 reads，源句还表达 stores。"}],"handoff":[]}

长字段与独立条目已有表达，交给 Replace 修正主语和字段边界
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]},{"index":1,"head":"The system","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"handoff":[{"target":"replace","source_sentence_ids":["S1"],"indices":[0,1],"problem":"processes 已包含在第 0 条的 tail 中，第 1 条也已表达该动作但主语应为 a module。修正第 1 条主语，并缩短第 0 条的 tail。"}]}

重建文本改错连接词
输入：{"source_sentences":[{"sentence_id":"S1","text":"The module receives signals and generates alerts."}],"current_collection":{"triples":[{"index":0,"head":"The module","relation":"receives","tail":"signals","source_sentence_ids":["S1"]},{"index":1,"head":"The module","relation":"generates","tail":"alerts","source_sentence_ids":["S1"]}]},"comparison_bundle":{"basis_version":"V0","reconstructions":[{"sentence_id":"S1","text_b":"The module receives signals or generates alerts."}]}}
输出：{"add":[],"handoff":[{"target":"text_generation","source_sentence_ids":["S1"],"indices":[0,1],"problem":"重建文本写成 receives signals or generates alerts，但当前两条正确表达了源句的两个动作。"}]}"""

class FeedbackAddAgent(FeedbackAgent):
    stage = 'add'
    task_prompt = TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
