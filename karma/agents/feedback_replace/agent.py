"""Task-focused replace feedback."""
from karma.agents.feedback_common import FeedbackAgent

SYSTEM_PROMPT = """依据源句修正和拆分已有三元组。一条旧三元组可以直接替换成一条或多条。完整回复采用本阶段指定的 JSON 格式。"""

TASK_PROMPT = """# 执行步骤
1. 逐条读取当前三元组，包括前一步新增的条目，找到源句中直接支持它的关系。
2. 从源句确定该关系的主体，将 head 修正为这个主体；区分主体与中间的修饰短语。
3. 根据源句修正 relation 的动作、词形、方向，以及目的、风险或条件联系。
4. 根据源句修正 tail 的对象与边界，找出字段内部另外表达的关系。
5. 保留决定对象、关系含义或成立条件的修饰；省略 In some embodiments 这类句首背景。a pre-step of grinding the rubber 说明具体步骤时可作为完整步骤名称。
6. 针对每项内部关系查找当前集合：已有正确独立条目时保留它；已有错误条目时修正它；缺少独立条目时拆出该关系。
7. 在原条目的 new_triples 中放入修正后的外层关系与需要拆出的内部关系。普通修正放一条，拆分放多条；已由其他正确条目表达的内部关系沿用现有条目。
8. 内部关系独立后，缩短外层多余字段，保留识别对象和限定事实所需的内容。每条内部关系使用它在源句中的主体，并保留与目的、危险等外层内容的联系。
9. 对 or 保留选择范围；and 表示整套设备组成时保留集合主体，各对象独立参与关系时分别表达。
10. 核对替换后的完整集合，保留原有正确事实及必要限定，合并本轮对同一 index 的修改，取消重复生成的关系。
11. 完全遗漏的关系交给 add；需要删除的重复条目交给 remove；依据不足的情况记录 review。文本差异仅提示重建文本错误时保留正确三元组并记录问题。
12. 输出 replace 及转交问题。独立检查全部当前条目，前序提示用于补查。"""

OUTPUT_RULES = """# 输出格式
返回 JSON 对象，包含 replace、handoff 两个数组；无内容的数组写 []。
replace 每项写 index、reason、new_triples；reason 简述具体修正内容。
new_triples 至少包含一条，每条写 head、relation、tail、source_sentence_ids、evidence。
原 index 的整条三元组由 new_triples 中的全部条目替换，拆分结果直接放在这个数组中。
handoff 每项写 target、source_sentence_ids、indices、problem：target 指处理阶段；indices 填当前相关条目编号，缺少条目时填 []；problem 简述具体位置与问题。
target 使用 add、replace、remove、text_generation、text_comparison 或 review；源句与三元组正确而重建文本或对比判断有误时，分别记录 text_generation 或 text_comparison。"""

EXAMPLES = """# 示例
示例仅列判断所需的输入字段，输出展示本阶段完整格式。

一条嵌套三元组直接换成两条
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":0,"reason":"将原条目中的两项关系分别表达。","new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"],"evidence":"The system includes a module that processes data."},{"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"],"evidence":"The system includes a module that processes data."}]}],"handoff":[]}

已有内部关系时修正它，不再重复拆出
输入：{"source_sentences":[{"sentence_id":"S1","text":"The system includes a module that processes data."}],"current_collection":{"triples":[{"index":0,"head":"The system","relation":"includes","tail":"a module that processes data","source_sentence_ids":["S1"]},{"index":1,"head":"The system","relation":"processes","tail":"data","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":1,"reason":"processes 的主体是 a module。","new_triples":[{"head":"a module","relation":"processes","tail":"data","source_sentence_ids":["S1"],"evidence":"The system includes a module that processes data."}]},{"index":0,"reason":"内部关系已由第 1 条表达。","new_triples":[{"head":"The system","relation":"includes","tail":"a module","source_sentence_ids":["S1"],"evidence":"The system includes a module that processes data."}]}],"handoff":[]}

同时修正主语和用途表达
输入：{"source_sentences":[{"sentence_id":"S1","text":"The application relates to a bracket system for mounting to a vehicle to provide a support structure."}],"current_collection":{"triples":[{"index":0,"head":"mounting to a vehicle","relation":"provides","tail":"a support structure","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":0,"reason":"找回系统主体并保留 to provide 的用途含义。","new_triples":[{"head":"a bracket system for mounting to a vehicle","relation":"is to provide","tail":"a support structure","source_sentence_ids":["S1"],"evidence":"The application relates to a bracket system for mounting to a vehicle to provide a support structure."}]}],"handoff":[]}

在已有条目补回目的联系
输入：{"source_sentences":[{"sentence_id":"S1","text":"The controller may query the ECU to identify the fault."}],"current_collection":{"triples":[{"index":0,"head":"The controller","relation":"may query","tail":"the ECU","source_sentence_ids":["S1"]},{"index":1,"head":"The controller","relation":"may identify","tail":"the fault","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":1,"reason":"保留查询与识别之间的目的联系。","new_triples":[{"head":"The controller","relation":"may query the ECU to identify","tail":"the fault","source_sentence_ids":["S1"],"evidence":"The controller may query the ECU to identify the fault."}]}],"handoff":[]}

内部动作要保留与危险的联系
输入：{"source_sentences":[{"sentence_id":"S1","text":"The risk of cargo falling from the deck causes concern."}],"current_collection":{"triples":[{"index":0,"head":"cargo","relation":"falls from","tail":"the deck","source_sentence_ids":["S1"]},{"index":1,"head":"The risk of cargo falling from the deck","relation":"causes","tail":"concern","source_sentence_ids":["S1"]}]}}
输出：{"replace":[{"index":0,"reason":"保留风险与内部动作之间的联系及 falling 词形。","new_triples":[{"head":"The risk","relation":"is of cargo falling from","tail":"the deck","source_sentence_ids":["S1"],"evidence":"The risk of cargo falling from the deck causes concern."}]}],"handoff":[]}

原三元组正确，重建文本错误
输入：{"source_sentences":[{"sentence_id":"S1","text":"The process includes a grinding step to reduce particle size."}],"current_collection":{"triples":[{"index":0,"head":"The process","relation":"includes","tail":"a grinding step","source_sentence_ids":["S1"]},{"index":1,"head":"a grinding step","relation":"is to reduce","tail":"particle size","source_sentence_ids":["S1"]}]},"comparison_bundle":{"basis_version":"V0","reconstructions":[{"sentence_id":"S1","text_b":"The process includes a grinding step. A grinding step reduces particle size."}]}}
输出：{"replace":[],"handoff":[{"target":"text_generation","source_sentence_ids":["S1"],"indices":[0,1],"problem":"重建文本写成 A grinding step reduces particle size；第 1 条原本已保留目的表达。"}]}

保留 or 的选择含义
输入：{"source_sentences":[{"sentence_id":"S1","text":"The operator can use a standard mode or an emergency mode."}],"current_collection":{"triples":[{"index":0,"head":"The operator","relation":"can use","tail":"a standard mode or an emergency mode","source_sentence_ids":["S1"]}]}}
输出：{"replace":[],"handoff":[]}

and 描述一套设备的组成
输入：{"source_sentences":[{"sentence_id":"S1","text":"A pair of upper and lower rollers supports the sheet."}],"current_collection":{"triples":[{"index":0,"head":"A pair of upper and lower rollers","relation":"supports","tail":"the sheet","source_sentence_ids":["S1"]}]}}
输出：{"replace":[],"handoff":[]}

保留步骤名称，省略句首背景
输入：{"source_sentences":[{"sentence_id":"S1","text":"In some embodiments, the process includes a pre-step of washing the parts."}],"current_collection":{"triples":[{"index":0,"head":"the process","relation":"includes","tail":"a pre-step of washing the parts","source_sentence_ids":["S1"]}]}}
输出：{"replace":[],"handoff":[]}"""

class FeedbackReplaceAgent(FeedbackAgent):
    stage = 'replace'
    task_prompt = TASK_PROMPT
    output_prompt = OUTPUT_RULES
    examples_prompt = EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
