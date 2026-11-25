"""Task-focused replace feedback."""
from karma.agents.feedback_common import FeedbackAgent, OUTPUT_RULES

SYSTEM_PROMPT = """你负责检查并修正已有三元组，包括主语错误、词形错误、必要限定缺失和嵌套关系未拆分。
依据源句判断事实，结合当前完整集合确定修改；文本差异和已执行的修改记录用于帮助定位问题。
一条旧三元组可以替换成一条或多条，已有正确的独立关系保留在当前集合中。
输出本次修正涉及的全部操作，具体步骤与格式见本次任务说明。"""

TASK_TEMPLATE = """# 阶段一：核对并确定问题
1. 逐条读取当前三元组，包括前一步新增项，找到支持该关系的源句。
2. 根据源句确定主体、动作和对象，检查主语归属、词形、方向及目的、风险、条件联系。若同一句内能唯一确定指代对象，优先用该句中的实体原称写出三元组，使三元组可以独立阅读；无法唯一确定时保留原文指代表达。
3. 从源句找出当前条目各字段内部表达的关系。
4. 为每项内部关系分别确定主体、动作和对象，再查找当前集合中的独立条目。
{time_place_check}{difference_step}. 对照当前集合核实文本差异；保留源句支持的正确条目。文本差异为空时仍完成上述检查。

# 阶段二：生成本阶段操作
1. 按源句修正 head、relation、tail，保留决定对象、关系含义或成立条件的修饰{background}
2. 普通修正将一条完整结果放入 new_triples；拆分将外层关系及需要补出的内部关系放入同一 new_triples。
3. 逐项对照找到的内部关系：已有正确独立条目时保留；已有错误条目时直接修正；尚无独立条目时，将拆出的关系放入原条目的new_triples。
4. 每条内部关系使用自身的主体，并保留与目的、风险等外层内容的联系。
5. 内部关系独立后，调整外层字段，保留识别对象和表达必要限定所需的内容。{name_example}
6. {coordination}
7. 修正条目时发现完全遗漏的独立关系，直接新增；发现重复项，确定保留项并直接删除重复项。修改依据不足时保留原表达。

# 阶段三：复核并输出
1. 核对每条新结果的单句依据、实义词词形及必要限定。
2. 对照修改后的完整集合，确认原有正确关系仍有对应条目，补齐丢失的正确事实与必要限定。
3. 检查被修正的错误旧表达是否仍由其他条目保留：需要修正时一并替换；完整重复时保留其中一条，在本轮删除重复项。
4. 取消本轮重复生成的关系，合并对同一index的修改，输出本轮操作。差异仅来自重建文本时保留正确三元组。"""

TASK_PROMPT = TASK_TEMPLATE.format(
    time_place_check="",
    difference_step=5,
    background="；省略 In some embodiments 这类句首背景。",
    name_example="a pre-step of grinding the rubber 说明具体步骤时可作为完整步骤名称。",
    coordination="or 保留选择范围；and 表示整套设备组成时保留集合主体，各对象独立参与关系时分别表达。",
)

CHINESE_TASK_PROMPT = TASK_TEMPLATE.format(
    time_place_check=(
        "5. 核对事件的时间和发生地点。若头实体或关系中含有时间、地点，先确定它直接修饰哪个动作。"
        "对照当前集合，检查该事件的主干及相应的时间、地点条目。应单列的时间或地点只写在长字段里时，补出相应条目；"
        "事件有独立宾语时，保留或补回一条“主体｜动作｜宾语”作为主干。"
        "已有“主体｜动作＋宾语｜时间或地点”的条目且归属正确时，保留在原处。动作直接以时间或地点作补足成分时，保留原表达。\n"
    ),
    difference_step=6,
    background="。只作引入且省略后事实完整的背景可省略。",
    name_example="「研磨橡胶的预处理步骤」可用作识别该步骤的完整名称。",
    coordination="「或」保留选择范围。整体参与关系时保留组合，各对象独立参与关系时分别表达。",
)

EXAMPLES = """# 示例
示例仅列判断所需的输入字段，输出展示本阶段完整格式。

一条嵌套三元组直接换成两条
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"将原条目中的两项关系分别表达。","new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"]},{"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}],"remove":[]}

已有内部关系时修正它，不再重复拆出
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]},{"index":1,"head":"The system","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":1,"reason":"processes 的主体是 a module。","new_triples":[{"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]},{"index":0,"reason":"内部关系已由第 1 条表达。","new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"]}]}],"remove":[]}

同时修正主语、实义词词形和目的表达
输入：{"source_sentences":[{"sentence_id":"S1","text":"A cooling fan mounted near the outlet is used to remove excess heat."}],"current_collection":{"triples":[{"index":0,"head":"the outlet","relation":"removes","tail":"excess heat","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"主语为冷却风扇；removes 改回原文 remove，保留 is used to 表达用途。","new_triples":[{"head":"A cooling fan mounted near the outlet","relation":"is used to remove","tail":"excess heat","source_sentence_ids":["S1"]}]}],"remove":[]}

内部动作要保留与危险的联系
输入：{"source_sentences":[{"sentence_id":"S1","text":"The risk of cargo falling from the deck causes concern."}],"current_collection":{"triples":[{"index":0,"head":"cargo","relation":"falls from","tail":"the deck","source_sentence_ids":["S1"]},{"index":1,"head":"The risk of cargo falling from the deck","relation":"causes","tail":"concern","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"保留风险与内部动作之间的联系及 falling 词形。","new_triples":[{"head":"The risk","relation":"is of cargo falling from","tail":"the deck","source_sentence_ids":["S1"]}]}],"remove":[]}"""

CHINESE_EXAMPLES = """# 示例
修正内部动作的主体和用途，保留位置关系
输入：{"source_sentences":[{"sentence_id":"S1","text":"安装在仓门内侧的摄像头用于识别车辆编号，但尚未接入值班系统。"}],"current_collection":{"triples":[{"index":0,"head":"仓门","relation":"识别","tail":"车辆编号","source_sentence_ids":["S1"]},{"index":1,"head":"摄像头","relation":"安装在","tail":"仓门内侧","source_sentence_ids":["S1"]},{"index":2,"head":"摄像头","relation":"已接入","tail":"值班系统","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"识别车辆编号是摄像头的用途，主体是摄像头。","new_triples":[{"head":"摄像头","relation":"用于识别","tail":"车辆编号","source_sentence_ids":["S1"]}]},{"index":2,"reason":"源句用「尚未」限定接入状态。","new_triples":[{"head":"摄像头","relation":"尚未接入","tail":"值班系统","source_sentence_ids":["S1"]}]}],"remove":[]}

嵌套关系一起写入一项 replace
输入：{"source_sentences":[{"sentence_id":"S1","text":"检票台旁设有用于回收旧票的箱子。"}],"current_collection":{"triples":[{"index":0,"head":"检票台旁","relation":"设有","tail":"用于回收旧票的箱子","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"先保留箱子所在的位置，再独立表达箱子的用途。","new_triples":[{"head":"检票台旁","relation":"设有","tail":"箱子","source_sentence_ids":["S1"]},{"head":"箱子","relation":"用于回收","tail":"旧票","source_sentence_ids":["S1"]}]}],"remove":[]}

内部动作已有独立条目，修正它并缩短外层客体
输入：{"source_sentences":[{"sentence_id":"S1","text":"场馆配有处理访客登记的终端。"}],"current_collection":{"triples":[{"index":0,"head":"场馆","relation":"配有","tail":"处理访客登记的终端","source_sentence_ids":["S1"]},{"index":1,"head":"场馆","relation":"处理","tail":"访客登记","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":1,"reason":"处理访客登记的主体是终端。","new_triples":[{"head":"终端","relation":"处理","tail":"访客登记","source_sentence_ids":["S1"]}]},{"index":0,"reason":"内部动作已由修正后的第1条表达。","new_triples":[{"head":"场馆","relation":"配有","tail":"终端","source_sentence_ids":["S1"]}]}],"remove":[]}

保留风险发生的可能性和条件
输入：{"source_sentences":[{"sentence_id":"S1","text":"转弯时货物可能滑出车厢，司机已加装挡板。"}],"current_collection":{"triples":[{"index":0,"head":"货物","relation":"滑出","tail":"车厢","source_sentence_ids":["S1"]},{"index":1,"head":"司机","relation":"已加装","tail":"挡板","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"reason":"滑出是转弯时可能发生的风险，保留条件和「可能」。","new_triples":[{"head":"转弯时货物","relation":"可能滑出","tail":"车厢","source_sentence_ids":["S1"]}]}],"remove":[]}

保留已有的接收时间，补出接收地点
输入：{"source_sentences":[{"sentence_id":"S1","text":"当市档案馆于2018年在南馆接收这批手稿时，北馆仍在修缮中。"}],"current_collection":{"triples":[{"index":0,"head":"市档案馆","relation":"在南馆接收","tail":"这批手稿","source_sentence_ids":["S1"]},{"index":1,"head":"市档案馆","relation":"接收这批手稿","tail":"于2018年","source_sentence_ids":["S1"]},{"index":2,"head":"北馆","relation":"仍处于","tail":"修缮中","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"new_triples":[{"head":"市档案馆","relation":"接收","tail":"这批手稿","source_sentence_ids":["S1"]},{"head":"市档案馆","relation":"接收这批手稿","tail":"在南馆","source_sentence_ids":["S1"]}],"reason":"南馆是接收手稿的地点。第0条拆成接收主干和地点两条。第1条已正确表达接收时间，第2条已完整表达北馆当时仍在修缮。"}],"remove":[]}"""


class FeedbackReplaceAgent(FeedbackAgent):
    stage = 'replace'
    task_prompt = TASK_PROMPT
    chinese_task_prompt = CHINESE_TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES
    chinese_examples_prompt = CHINESE_EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
