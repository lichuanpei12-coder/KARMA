"""Task-focused add feedback."""
from karma.agents.feedback_common import FeedbackAgent, OUTPUT_RULES

SYSTEM_PROMPT = """你负责依据源句补充当前集合完全遗漏的关系，并自主检查源句中的遗漏。
结合当前完整集合判断是否需要新增；文本差异和已执行的修改记录用于帮助定位问题。
补遗漏时，已有条目的表达需要补全或拆分，就在本次回复中直接修改；已有正确独立表达时保留现有条目。
输出本次新增、替换和删除操作，具体步骤与格式见本次任务说明。"""

TASK_PROMPT = """# 阶段一：核对并确定问题
1. 逐句找出源句明确表达的关系，确定主体、动作或状态、对象及必要限定。
2. 在当前完整集合中查找这些关系，同时检查长字段包含的内容。
3. 核对文本差异，回查对应源句与当前条目，确定实际遗漏。

# 阶段二：生成本阶段操作
1. 对完全遗漏的事实，先从同一句确定头实体和尾实体：谁或什么作主体，这个动作或状态指向谁、什么对象或明确的补足成分。
2. 再用源句中的词形填写连接两端的关系，保留否定、条件及必要的时间等限定。head、relation、tail 三项都必须有实义；任一项为空、只有空白或缺少源句依据时，跳过该候选，不用占位词补齐。
3. 已有正确独立表达时保留现有条目；已有表达缺少必要成分时，按该条 index 在 replace 数组中给出补全后的三元组。
4. 关系包含在长字段中、尚无独立表达时，在本次 replace 的 new_triples 中写出外层关系及源句支持的各项内部关系。已有独立条目但字段有误时，就地修正该条，同时缩短外层字段。

# 阶段三：复核并输出
1. 逐条对照源句核对新增关系及必要限定。
2. 将每个候选与当前完整集合及本轮拟新增项逐条比较，核对参与者、关系方向、动作或状态及限定范围。仅语序、指代或字段边界不同而事实相同的，跳过重复项。已有条目表达同一事件但遗漏必要限定时，直接替换原条目并补全限定。相同实体间另有独立动作的，按独立事实判断。
3. 输出本轮操作。文本差异为空时，仍完成逐句检查。"""

EXAMPLES = """# 示例
示例仅列判断所需的输入字段，输出展示本阶段完整格式。

源句有关系完全没有抽取
输入：{"source_sentences":[{"sentence_id":"S1","text":"The controller reads and stores sensor data."}],"current_collection":{"triples":[{"index":0,"head":"The controller","relation":"reads","tail":"sensor data","source_sentence_ids":["S1"]}]}}
输出：{"add":[{"head":"The controller","relation":"stores","tail":"sensor data","source_sentence_ids":["S1"],"reason":"当前只表达 reads，源句还表达 stores。"}],"replace":[],"remove":[]}

在本次回复中修正独立条目的主语和长字段边界
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]},{"index":1,"head":"The system","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"]}],"reason":"保留包含关系，处理数据由第1条表达。"},{"index":1,"new_triples":[{"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"]}],"reason":"按源句修正该动作的主体。"}],"remove":[]}

重建文本改错连接词
输入：{"source_sentences":[{"sentence_id":"S1","text":"The module receives signals and generates alerts."}],"current_collection":{"triples":[{"index":0,"head":"The module","relation":"receives","tail":"signals","source_sentence_ids":["S1"]},{"index":1,"head":"The module","relation":"generates","tail":"alerts","source_sentence_ids":["S1"]}]},"comparison_bundle":{"basis_version":"V0","reconstructions":[{"sentence_id":"S1","text_b":"The module receives signals or generates alerts."}]}}
输出：{"add":[],"replace":[],"remove":[]}"""

CHINESE_EXAMPLES = """# 示例
源句还有一项带条件的动作未表达
输入：{"source_sentences":[{"sentence_id":"S1","text":"库管员每天核对出库单，发现数量不符时会通知配送员。"}],"current_collection":{"triples":[{"index":0,"head":"库管员","relation":"每天核对","tail":"出库单","source_sentence_ids":["S1"]}]}}
输出：{"add":[{"head":"发现数量不符时，库管员","relation":"会通知","tail":"配送员","source_sentence_ids":["S1"],"reason":"当前集合只表达核对出库单，缺少发现数量不符时通知配送员的关系。"}],"replace":[],"remove":[]}

长字段中已经有该动作，独立条目的主体需要修正
输入：{"source_sentences":[{"sentence_id":"S1","text":"控制台配有用于识别车牌的摄像头。"}],"current_collection":{"triples":[{"index":0,"head":"控制台","relation":"配有","tail":"用于识别车牌的摄像头","source_sentence_ids":["S1"]},{"index":1,"head":"控制台","relation":"用于识别","tail":"车牌","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"new_triples":[{"head":"控制台","relation":"配有","tail":"摄像头","source_sentence_ids":["S1"]}],"reason":"保留配备关系，识别用途由第1条表达。"},{"index":1,"new_triples":[{"head":"摄像头","relation":"用于识别","tail":"车牌","source_sentence_ids":["S1"]}],"reason":"按源句修正该动作的主体。"}],"remove":[]}

现有事实完整，重建文本改变了连接关系
输入：{"source_sentences":[{"sentence_id":"S1","text":"值班员核对编号并登记故障。"}],"current_collection":{"triples":[{"index":0,"head":"值班员","relation":"核对","tail":"编号","source_sentence_ids":["S1"]},{"index":1,"head":"值班员","relation":"登记","tail":"故障","source_sentence_ids":["S1"]}]},"comparison_bundle":{"basis_version":"V0","reconstructions":[{"sentence_id":"S1","text_b":"值班员核对编号或登记故障。"}]}}
输出：{"add":[],"replace":[],"remove":[]}"""


class FeedbackAddAgent(FeedbackAgent):
    stage = 'add'
    task_prompt = TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES
    chinese_examples_prompt = CHINESE_EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
