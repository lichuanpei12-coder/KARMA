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
2. 再用源句中的词形填写连接两端的关系，保留否定、条件及必要的时间等限定。head、relation、tail 三项都必须有实义；任一项不能为空。
3. 已有正确独立表达时保留现有条目；已有表达缺少必要成分时，按该条 index 在 replace 数组中给出补全后的三元组。

# 阶段三：复核并输出
1. 逐条对照源句核对新增关系及必要限定。
2. 将每个候选与当前完整集合及本轮拟新增项逐条比较，核对参与者、关系方向、动作或状态及限定范围。仅语序、指代或字段边界不同而事实相同的，跳过重复项。已有条目表达同一事件但遗漏必要限定时，进行补全。相同实体间另有独立动作的，按独立事实判断。
3. 输出本轮操作。文本差异为空时，仍完成逐句检查。"""

CHINESE_TASK_PROMPT = """# 阶段一：核对并确定问题
1. 逐句找出源句明确表达的关系，确定主体、动作或状态、对象及必要限定。
2. 在当前完整集合中查找这些关系，同时检查 head、relation、tail 中的长字段。
3. 核对文本差异，回查源句与当前条目，区分完全遗漏、只包含在已有字段中、已有正确独立表达三种情况。

# 阶段二：拆分已有条目中的独立事实
1. 检查「和」「及」「并」「但不」、顿号及「……的」「用于」「由于」「由……构成」等表达。根据源句判断并列项能否各自成立，以及字段中是否还有能独立说清主体、关系和对象的事实。
2. 为每项关系确定它自己的主体和客体。三元组可以共享主体或关系，也可以首尾相接。按源句补回共同成分，检查每个动作实际由谁执行、指向什么对象。
3. 集合整体、合计数量、选项和「之一」按原句保留范围。否定、可能性、目的、风险、引述、条件和时间随它们约束的动作保留。拆开会改变原意时保留原表达。
4. 对照当前集合和本轮拟拆出的事实。确需拆分时，照填当前输入中该条的 index，在 replace 中为它写一项，把替换后需保留的主要事实和拆出的各条完整三元组写入同一 new_triples。其他条目已正确独立表达的事实保留在原处，同一内部事实只拆出一次。
5. 单独阅读替换后的外层三元组。缩短字段后仍要能识别原来的对象，并保留动作和成立条件。决定对象身份或范围的修饰保留在外层字段中。

# 阶段三：补全已有事实，新增遗漏事实
1. 对照阶段二拟保留和拆出的事实。对仍完全遗漏的事实，先从同一句确定头实体和尾实体，再用源句中的词形填写连接两端的关系，保留必要限定。head、relation、tail 任一项不能为空，三项都要有实义。
2. 已有表达缺少必要成分时，按该条 index 在 replace 中直接补全。该条同时需要拆分时，将补全与拆分合在同一项 replace 中。已有正确独立表达时保留现有条目。

# 阶段四：复核并输出
1. 逐条对照源句核对新增和替换后的三元组，检查主客体、关系方向及必要限定。再合起来读，确认主要事实和拆出的事实均有完整表达。
2. 将每个候选与修改后拟保留的条目及本轮其他候选比较，核对参与者、动作或状态及限定范围。仅语序、指代或字段边界不同而事实相同的，跳过重复项。相同实体间另有独立动作的，按独立事实判断。
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
输出：{"add":[{"head":"库管员","relation":"发现数量不符时会通知","tail":"配送员","source_sentence_ids":["S1"],"reason":"当前集合只表达核对出库单，缺少发现数量不符时通知配送员的关系。"}],"replace":[],"remove":[]}

长字段中已经有该动作，独立条目的主体需要修正
输入：{"source_sentences":[{"sentence_id":"S1","text":"控制台配有用于识别车牌的摄像头。"}],"current_collection":{"triples":[{"index":0,"head":"控制台","relation":"配有","tail":"用于识别车牌的摄像头","source_sentence_ids":["S1"]},{"index":1,"head":"控制台","relation":"用于识别","tail":"车牌","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"new_triples":[{"head":"控制台","relation":"配有","tail":"摄像头","source_sentence_ids":["S1"]}],"reason":"保留配备关系，识别用途由第1条表达。"},{"index":1,"new_triples":[{"head":"摄像头","relation":"用于识别","tail":"车牌","source_sentence_ids":["S1"]}],"reason":"按源句修正该动作的主体。"}],"remove":[]}

从头实体中拆出发行事实，保留收益率对应的债券
输入：{"source_sentences":[{"sentence_id":"S1","text":"纽约市发行的7.57亿美元免税债券的发行收益率为6.50％至7.88％之间，具体取决于到期日。"}],"current_collection":{"triples":[{"index":0,"head":"纽约市发行的7.57亿美元免税债券","relation":"发行收益率为","tail":"6.50％至7.88％之间","source_sentence_ids":["S1"]},{"index":1,"head":"纽约市发行的7.57亿美元免税债券的发行收益率","relation":"具体取决于","tail":"到期日","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"new_triples":[{"head":"纽约市发行的7.57亿美元免税债券","relation":"发行收益率为","tail":"6.50％至7.88％之间","source_sentence_ids":["S1"]},{"head":"纽约市","relation":"发行","tail":"7.57亿美元免税债券","source_sentence_ids":["S1"]}],"reason":"第0条说明这批债券的发行收益率，头实体还说明了谁发行哪批债券。保留原来的收益率事实，再把发行事实单独写一条。第1条已完整表达收益率取决于到期日，其中相同的发行事实只需抽取一次。"}],"remove":[]}

拆开同一关系下的两个对象，分别保留各自的限定
输入：{"source_sentences":[{"sentence_id":"S1","text":"社区中心向居民提供免费的图书借阅服务和仅限周末的场地预约服务。"}],"current_collection":{"triples":[{"index":0,"head":"社区中心","relation":"向居民提供","tail":"免费的图书借阅服务和仅限周末的场地预约服务","source_sentence_ids":["S1"]}]}}
输出：{"add":[],"replace":[{"index":0,"new_triples":[{"head":"社区中心","relation":"向居民提供","tail":"免费的图书借阅服务","source_sentence_ids":["S1"]},{"head":"社区中心","relation":"向居民提供","tail":"仅限周末的场地预约服务","source_sentence_ids":["S1"]}],"reason":"两项服务都由社区中心向居民提供；“免费”修饰图书借阅，“仅限周末”修饰场地预约。"}],"remove":[]}

现有事实完整，重建文本改变了连接关系
输入：{"source_sentences":[{"sentence_id":"S1","text":"值班员核对编号并登记故障。"}],"current_collection":{"triples":[{"index":0,"head":"值班员","relation":"核对","tail":"编号","source_sentence_ids":["S1"]},{"index":1,"head":"值班员","relation":"登记","tail":"故障","source_sentence_ids":["S1"]}]},"comparison_bundle":{"basis_version":"V0","reconstructions":[{"sentence_id":"S1","text_b":"值班员核对编号或登记故障。"}]}}
输出：{"add":[],"replace":[],"remove":[]}"""


class FeedbackAddAgent(FeedbackAgent):
    stage = 'add'
    task_prompt = TASK_PROMPT
    chinese_task_prompt = CHINESE_TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES
    chinese_examples_prompt = CHINESE_EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
