"""Review redundant facts with lexical rankings and apply replacements/deletions."""
from karma.agents.feedback_common import FeedbackAgent, OUTPUT_RULES

SYSTEM_PROMPT = """你负责依据源句处理当前三元组中的重复和冗余。
发现重复或冗余时，依据源句确定应保留的完整表达，在本次处理中完成必要的替换和删除。
输出本次修正涉及的全部操作，具体步骤与格式见本次任务说明。"""

TASK_TEMPLATE = """# 阶段一：确定问题
1. 阅读源句和当前集合，了解每条关系表达的事实。
2. lexical_overlap.pairs 列出当前集合的全部三元组对。重点检查 overall_rank 或 containment_rank 靠前的条目对，随后检查其余条目；每对条目形成一次完整判断。
   程序把每个汉字作为一个计数单位，其余文本转小写后按空白和汉字边界切分。overlap_f1 表示整体重合程度，left_containment、right_containment 分别表示左、右条目的计数单位被另一条包含的比例。overall_rank 按整体重合程度排名，containment_rank 按两侧较高的包含率排名，同分同排名。
   数值用于安排检查顺序。结合原条目核对主体、关系方向、字段归属，并参考 left_only_words、right_only_words 列出的差异字词。
3. 比较两条的主体、关系、客体及必要限定。遇到数量、条件、范围等限定时，回查源句，确定限定词修饰哪个对象或关系，再判断当前两条表达的是同一事实还是不同事实。{time_place_rule}
4. 遇到字词包含关系时，分别确定外层关系和字段内部关系，保留各项独立事实。
5. 结合源句和文本差异，核实当前集合中需要处理的条目。

# 阶段二：确定保留表达并处理
1. 依据源句确定应保留的主体、关系、客体和必要限定；限定属于其他关系时，在对应关系中保留其范围。
2. 表达同一事实的条目选择一项保留，必要时替换为统一的完整表达，并删除重复项；同样正确且等价时保留编号较小的一条。
3. 字段部分重叠时，直接调整需要修改的字段，并保留各项独立关系。
4. 处理重叠条目时，若需拆分或补回独立事实，在本轮完整表达。源句依据不足时保留当前表达。

# 阶段三：整理输出
1. index 和 keep_index 均使用本次输入编号。删除重复项时，keep_index 指向本轮保留的条目，也可以指向本轮替换后的保留项。
2. 将同一条目的修改合为一次操作，为每项操作填写具体理由，输出本次修正涉及的全部操作。"""

TASK_PROMPT = TASK_TEMPLATE.format(time_place_rule="")
CHINESE_TASK_PROMPT = TASK_TEMPLATE.format(
    time_place_rule="以事件的发生时间或地点为尾实体的三元组，用于独立表达该事件的时间或地点。即使与事件主干的主体和动作相同，也应单独保留。"
)

EXAMPLES = """# 示例
示例使用通用构造，输入列出判断所需字段，输出展示完整格式。

删除完整重复，保留情态和条件各自表达的事实
输入：{"source_sentences":[{"sentence_id":"S1","text":"The module may send a warning in test mode and must send a warning in normal mode."}],"current_collection":{"triples":[{"index":0,"head":"The module","relation":"may send","tail":"a warning in test mode","source_sentence_ids":["S1"]},{"index":1,"head":"The module","relation":"may send","tail":"a warning in test mode","source_sentence_ids":["S1"]},{"index":2,"head":"The module","relation":"must send","tail":"a warning in normal mode","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[],"remove":[{"index":1,"keep_index":0,"reason":"第0、1条表达同一事实，保留第0条。第2条表达 normal mode 下必须发送，单独保留。"}]}

调整外层字段，保留独立的内部关系
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]},{"index":1,"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"第1条独立表达模块处理数据，第0条保留系统包含模块。","new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"]}]}],"remove":[]}

确定限定词归属，统一位置关系
输入：{"source_sentences":[{"sentence_id":"S1","text":"The supervisor inspects all of the workstations located in the lab and records messages sent by any of the workstations located in the lab."}],"current_collection":{"triples":[{"index":0,"head":"all of the workstations","relation":"are located in","tail":"the lab","source_sentence_ids":["S1"]},{"index":1,"head":"any of the workstations","relation":"are located in","tail":"the lab","source_sentence_ids":["S1"]},{"index":2,"head":"The supervisor","relation":"inspects","tail":"all of the workstations located in the lab","source_sentence_ids":["S1"]},{"index":3,"head":"The supervisor","relation":"records","tail":"messages sent by any of the workstations located in the lab","source_sentence_ids":["S1"]},{"index":4,"head":"messages","relation":"are sent by","tail":"any of the workstations located in the lab","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"两条位置关系指向同一组工作站，统一为 the workstations。all 表达检查范围，any 表达发送者范围，分别保留在第2条和第3、4条。","new_triples":[{"head":"the workstations","relation":"are located in","tail":"the lab","source_sentence_ids":["S1"]}]}],"remove":[{"index":1,"keep_index":0,"reason":"第1条的位置关系由替换后的第0条表达。"}]}"""


CHINESE_EXAMPLES = """# 示例
合并同一检查动作，保留其条件和对象范围
输入：{"source_sentences":[{"sentence_id":"S1","text":"停电时，值班员检查机房门口的备用照明，并记录检查结果。"}],"current_collection":{"triples":[{"index":0,"head":"停电时，值班员","relation":"检查","tail":"备用照明","source_sentence_ids":["S1"]},{"index":1,"head":"值班员","relation":"检查","tail":"机房门口的备用照明","source_sentence_ids":["S1"]},{"index":2,"head":"停电时，值班员","relation":"记录","tail":"检查结果","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"在同一条检查关系中保留停电条件和机房门口的对象范围。","new_triples":[{"head":"停电时，值班员","relation":"检查","tail":"机房门口的备用照明","source_sentence_ids":["S1"]}]}],"remove":[{"index":1,"keep_index":0,"reason":"第0、1条对应同一检查动作，第2条独立表达记录结果。"}]}

删除完整重复，保留条件和情态不同的关系
输入：{"source_sentences":[{"sentence_id":"S1","text":"试运行时终端可以发送提示，正式运行时终端必须发送提示。"}],"current_collection":{"triples":[{"index":0,"head":"试运行时终端","relation":"可以发送","tail":"提示","source_sentence_ids":["S1"]},{"index":1,"head":"试运行时终端","relation":"可以发送","tail":"提示","source_sentence_ids":["S1"]},{"index":2,"head":"正式运行时终端","relation":"必须发送","tail":"提示","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[],"remove":[{"index":1,"keep_index":0,"reason":"第0、1条完整重复；第2条的运行条件和义务不同，单独保留。"}]}

独立关系已表达，缩短外层字段
输入：{"source_sentences":[{"sentence_id":"S1","text":"办公区配有可打印通行证的终端。"}],"current_collection":{"triples":[{"index":0,"head":"办公区","relation":"配有","tail":"可打印通行证的终端","source_sentence_ids":["S1"]},{"index":1,"head":"终端","relation":"可打印","tail":"通行证","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"第1条已独立表达打印功能，第0条保留办公区配有终端。","new_triples":[{"head":"办公区","relation":"配有","tail":"终端","source_sentence_ids":["S1"]}]}],"remove":[]}"""


class FeedbackRemoveAgent(FeedbackAgent):
    stage = 'remove'
    task_prompt = TASK_PROMPT
    chinese_task_prompt = CHINESE_TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES
    chinese_examples_prompt = CHINESE_EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
