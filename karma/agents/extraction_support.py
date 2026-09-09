"""Shared extraction conventions and structural response validation."""

import json
import math
import re


ENTITY_RULES = """候选实体用于辅助发现事实中的参与对象。
1. 根据源文本识别可能作为 head 或 tail 的完整表达，包括技术对象、普通名词短语、
   代词以及充当宾语的较长短语或从句。
2. 保留决定含义的限定词、修饰语、数值和编号，保持原文大小写与空格。
   例如 "a variety of systems" 保留整体，"the measured traffic per time" 保留整体。
3. 代词保留原文提及，结合上下文理解其指代。不同提及形式分别保留，供事实判断使用。
4. 并列项在各自含义明确时分别识别；省略的共享词可按原文语法补齐。
   例如 "first and second cables" 对应 "first cable" 和 "second cable"。
5. 数值、条件、日期和图号在充当事实参与对象或限定其含义时保留。
   候选集合可以包含暂未参与三元组的对象，事实是否成立由源文本决定。
"""

FACT_RULES = """1. 逐句检查源文本支持的事实，包括动作、状态、定义、组成、属性与比较关系。
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
"""

SCORE_RULES = """confidence 表示源文本对事实的支持强度，clarity 表示头尾和关系表达的
清晰程度，relevance 表示事实与文档主题的相关程度。三个维度分别评估，取值为
0.0 到 1.0；分别有依据时可以相同。分数表达判断，不替代事实核实。
"""


def difference_context(diff):
    """Share the same A/B definitions with extraction and revision agents."""
    diff = diff if isinstance(diff, dict) else {}
    data = {key: diff.get(key, []) for key in ('unique_to_text_a', 'unique_to_text_b')}
    return """文本A是本次抽取使用的源文本，文本B由当前三元组生成。
unique_to_text_a 是比较模型认为源文本中有、重建文本中未体现的信息，帮助定位候选遗漏。
unique_to_text_b 是比较模型认为重建文本中有、源文本中未找到对应依据的信息，帮助定位待复核事实。
两组差异均可能存在比较或重建误差。对象出现在 B 侧差异中，可能只是其关系有误；
对象是否有效、事实是否成立均以源文本核实结果为准。空差异仍需检查源文本的事实覆盖。
<text_difference_json>
""" + json.dumps(data, ensure_ascii=False, indent=2) + "\n</text_difference_json>"


def parse_json_container(response, expected_type):
    """Accept JSON, fenced JSON or a prose wrapper, but never a nested wrong-root value."""
    if not isinstance(response, str):
        raise ValueError('model response must be text')
    value = response.strip()
    fence = re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```', value, re.IGNORECASE)
    if fence:
        value = fence.group(1).strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        positions = [p for p in (value.find('['), value.find('{')) if p >= 0]
        if not positions:
            raise ValueError('model response contains no JSON container')
        # Decode the first container, not an inner array of a wrong-root object.
        start = min(positions)
        parsed, end = json.JSONDecoder().raw_decode(value, start)
        if '[' in value[end:] or '{' in value[end:]:
            raise ValueError('model response contains multiple JSON containers')
    if not isinstance(parsed, expected_type):
        raise ValueError('unexpected JSON root type')
    return parsed


def clean_string(value):
    return value.strip() if isinstance(value, str) else ''


def safe_score(value, default=0.5):
    if isinstance(value, bool):
        return default
    try:
        score = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return min(1.0, max(0.0, score)) if math.isfinite(score) else default
