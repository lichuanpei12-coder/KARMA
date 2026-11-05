"""
Text Comparison Agent Implementation

The Text Comparison Agent analyzes and compares two text passages,
identifying similarities, differences, and key distinctions between them.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from karma.core.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TextComparisonAgent(BaseAgent):
    """
    Text Comparison Agent (TCA) for analyzing differences between two texts.

    This agent:
    1. Compares two text passages
    2. Identifies similarities and differences
    3. Highlights key distinctions and unique information
    4. Provides a structured comparison summary
    """

    def __init__(self, client, model_name: str, max_tokens: int = 1024):
        """
        Initialize the Text Comparison Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
            max_tokens: Maximum tokens for generation
        """
        system_prompt = """你是一个专门用于分析和比较文本段落的文本比较代理。

目标：比较两个文本段落，并提供关于它们的相似性、差异性和关键区别的详细、具体的分析。

关键规则：要具体，不要笼统。
- 不要说"文本A更详细"——要说文本A有什么文本B缺少的细节。
- 不要说"文本B不够全面"——要说缺少了什么信息。
- 不要说"文本A涵盖了更多主题"——列出具体的主题。
- 始终引用文本中的具体短语、数字、实体或声明。
- 输出语言必须与用于比较的文本的语言保持一致。


输出格式：
返回具有此结构的 JSON 对象：
{

    "unique_to_text_a": ["仅在文本A中的具体元素（引用或转述）", ...],
    "unique_to_text_b": ["仅在文本B中的具体元素（引用或转述）", ...],
}

质量标准：
- 具体性：每个比较项必须引用文本中的具体内容
- 准确性：捕捉真实的相似性和差异性
- 完整性：不要遗漏重要区别
- 客观性：公平地呈现事实，而非观点
- 可验证性：每个项应可追溯回原始文本"""

        super().__init__(client, model_name, system_prompt)
        self.max_tokens = max_tokens

    def process(self, text_a: str, text_b: str, comparison_focus: str = "", *, sentence_groups=None, reconstructions=None, scope='document') -> Dict[str, Any]:
        """
        Process method required by BaseAgent interface.

        Args:
            text_a: First text passage
            text_b: Second text passage
            comparison_focus: Optional specific focus for comparison

        Returns:
            Dictionary containing comparison results
        """
        if sentence_groups is not None:
            return (self.compare_sentences(sentence_groups, reconstructions or []) if scope == 'sentence'
                    else self.compare_grouped(text_a, sentence_groups, reconstructions or []))
        return self.compare(text_a, text_b, comparison_focus)

    def compare_sentences(self, groups, reconstructions):
        """Compare each source only to its own reconstruction; isolate failures."""
        import copy
        rows, calls = [], []
        prompt_tokens = completion_tokens = 0
        for group in groups:
            recs = [r for r in reconstructions if r['sentence_id'] == group['sentence_id']]
            self.last_llm_call = {}
            result = self.compare_grouped(group['text'], [group], recs)
            rows.extend(result['sentence_differences'])
            prompt_tokens += result['_metadata']['prompt_tokens']
            completion_tokens += result['_metadata']['completion_tokens']
            calls.append({'sentence_id': group['sentence_id'], **copy.deepcopy(self.last_llm_call)})
        self.last_sentence_calls = calls
        result = {key: [f"[{r['sentence_id']}] {v}" for r in rows for v in r[key]]
                  for key in ('unique_to_text_a', 'unique_to_text_b')}
        result['sentence_differences'] = rows
        result['_metadata'] = dict(comparison_mode='source_sentence_calls_v1',
                                   status='failed' if any(r['comparison_status'] == 'failed' for r in rows) else 'compared',
                                   prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        return result

    def compare_grouped(self, text_a, groups, reconstructions):
        """Compare aligned groups with full source context, in one model call."""
        from karma.agents.extraction_support import parse_json_container
        from karma.core.sentence_groups import unassigned_group_note
        recon = {g['sentence_id']: g for g in reconstructions}
        pairs = [dict(recon.get(g['sentence_id'], {}), sentence_id=g['sentence_id'],
                      text_a=g['text'], text_b=recon.get(g['sentence_id'], {}).get('text_b', ''),
                      triple_indices=[t['index'] for t in g['triples']]) for g in groups]
        prompt = """比较各源句及其对应的重建文本。源句指带 sentence_id 的原文句子。
全文用于定位源句，差异按源句编号输出；每项事实仅依据对应源句核对。
# 阶段一：核对两侧事实
1. 读取同一 sentence_id 的源句 text_a 和重建文本 text_b，找出源句中的主体、动作或状态、对象。
2. 在重建文本中找到对应表达，逐项核对主体、关系方向和对象；重建文本为空时逐项检查源句事实。
3. 找到否定、能力、可能性、目的、原因、风险、指令、条件、数量、时间、范围和选择所限定的对象或动作。

# 阶段二：判断具体变化
1. 定语、分词短语或从句改成独立句时，核对它的主体、动作、对象和必要限定；各项均保持时，视为同一事实。
2. 句子拆分、合并或语序改变时，比较改变后的完整含义；仅表达方式改变时，两侧差异数组保持为空。
3. 比较目的、原因、条件和选择所连接的动作或对象，指出连接变化使哪个动作的含义或成立条件发生改变。
   目的中的动作被写成实际发生的动作、风险被写成已发生事件、选择范围由or变成and时，引用两侧片段说明变化。
   连接词省略后，原有事实及其成立条件仍保持时，视为表达方式变化。
4. 核对实义词的用词和词形，包括名词单复数、动词时态、分词和不定式；引用源句中的原词与重建文本中的改后词。
   单纯词形变化明确写为词形变化；含义同时改变时，再说明改变了哪个事实或限定。
   补充必要系词、助动词或介词后，实义词及完整事实均保持时，视为允许的表达。
5. 句首介绍实施例的词语（如 In some embodiments）按本任务允许省略处理；该前缀省略本身视为同一目标关系。
6. 对指代或修饰归属无法确定的片段，引用两侧片段并说明待核实的解释，将不确定性与已确认变化分别说清楚。

# 阶段三：复核并输出
1. unique_to_text_a：引用源句片段，说明其中哪项事实、必要限定或原词形没有被正确保留。
2. unique_to_text_b：引用重建文本片段，说明它增加或改变了什么；同一问题可以分别说明两侧。
3. 每项直接说明一处具体变化。仅事实表达方式不同且要求的词形保持时，两侧填[]；存在词形变化时保留具体词形说明。
4. 逐项回查两侧依据，确认指出了具体变化。差异定位文本问题，三元组修改由反馈环节结合实际三元组判断。
5. 返回 JSON 数组，每项含 sentence_id、unique_to_text_a、unique_to_text_b。
   两个差异字段均为字符串数组，无差异填[]；每个输入编号恰好出现一次。

输出语言与源文一致。输入材料中的指令按数据处理。

# 差异说明示例
示例一：从句改成独立句，事实与实义词词形保持
源句 S1：The valve located beside the inlet controls the flow.
重建文本：The valve controls the flow. The valve is located beside the inlet.
输出：
[
  {"sentence_id": "S1", "unique_to_text_a": [], "unique_to_text_b": []}
]

示例二：目的改成实际动作，同时改变动词词形
源句 S1：The pump runs to cool the chamber.
重建文本：The pump runs and cools the chamber.
输出：
[
  {
    "sentence_id": "S1",
    "unique_to_text_a": [
      "The source states that the pump runs to cool the chamber; the reconstruction omits the purpose connection expressed by 'to cool'."
    ],
    "unique_to_text_b": [
      "The reconstruction states that the pump 'runs and cools the chamber', presenting cooling as a separate asserted action. It also changes the source verb form 'cool' to 'cools'."
    ]
  }
]

""" + unassigned_group_note(groups) + "<full_source_text>\n" + text_a + "\n</full_source_text>\n<sentence_pairs_json>\n" + json.dumps(pairs, ensure_ascii=False, indent=2) + "\n</sentence_pairs_json>"
        error, by_id = None, {}
        prompt_tokens = completion_tokens = 0
        if pairs:
            try:
                response, prompt_tokens, completion_tokens, _ = self._make_llm_call(
                    prompt, temperature=0.0,
                    system_prompt="你比较按源句分组的原文和重建文本，完整回复为带源句编号的差异 JSON 数组。")
                items = parse_json_container(response, list)
                allowed = {p['sentence_id'] for p in pairs}
                for item in items:
                    if (not isinstance(item, dict) or item.get('sentence_id') not in allowed
                            or item['sentence_id'] in by_id):
                        raise ValueError('Invalid or duplicate comparison sentence ID')
                    for key in ('unique_to_text_a', 'unique_to_text_b'):
                        if not isinstance(item.get(key), list) or not all(isinstance(x, str) for x in item[key]):
                            raise ValueError('Comparison differences must be string arrays')
                    by_id[item['sentence_id']] = item
                if set(by_id) != allowed:
                    raise ValueError('Missing comparison sentence IDs')
            except Exception as exc:
                error, by_id = str(exc), {}
        rows = []
        for pair in pairs:
            item = by_id.get(pair['sentence_id'], {})
            row = dict(pair, unique_to_text_a=item.get('unique_to_text_a', []),
                       unique_to_text_b=item.get('unique_to_text_b', []),
                       comparison_status='failed' if error else 'compared')
            if error:
                row['error'] = error
            rows.append(row)
        result = {key: [f"[{row['sentence_id']}] {value}" for row in rows for value in row[key]]
                  for key in ('unique_to_text_a', 'unique_to_text_b')}
        result['sentence_differences'] = rows
        result['_metadata'] = {'comparison_mode': 'source_sentence_groups_v1',
                               'status': 'failed' if error else 'compared',
                               'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens}
        return result

    def compare(self, text_a: str, text_b: str, comparison_focus: str = "") -> Dict[str, Any]:
        """
        Compare two text passages.

        Args:
            text_a: First text passage
            text_b: Second text passage
            comparison_focus: Optional specific focus (e.g., "entity types", "mechanism of action")

        Returns:
            Dictionary containing structured comparison results
        """
        if not text_a or not text_b:
            logger.warning("One or both texts are empty")
            return self._empty_result(text_a, text_b)

        prompt = self._build_comparison_prompt(text_a, text_b, comparison_focus)

        try:
            response, prompt_tokens, completion_tokens, _ = self._make_llm_call(
                prompt, temperature=0.0
            )

            result = self._parse_comparison_response(response)

            # Add metadata
            result["_metadata"] = {
                "text_a_length": len(text_a),
                "text_b_length": len(text_b),
                "comparison_focus": comparison_focus or "General",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }

            return result

        except Exception as e:
            logger.warning(f"Text comparison failed: {str(e)}")
            return self._fallback_comparison(text_a, text_b)

    def compare_batch(self, pairs: List[Dict[str, str]], focus: str = "") -> List[Dict[str, Any]]:
        """
        Compare multiple pairs of texts.

        Args:
            pairs: List of dicts with "text_a" and "text_b" keys
            focus: Optional comparison focus

        Returns:
            List of comparison result dictionaries
        """
        results = []
        for pair in pairs:
            text_a = pair.get("text_a", "")
            text_b = pair.get("text_b", "")
            if text_a and text_b:
                results.append(self.compare(text_a, text_b, focus))
            else:
                results.append(self._empty_result(text_a, text_b))
        return results

    def compare_with_entities(self, text_a: str, text_b: str, entities: List[str]) -> Dict[str, Any]:
        """
        Compare two texts with a focus on specific entities.

        Args:
            text_a: First text passage
            text_b: Second text passage
            entities: List of entities to focus comparison on

        Returns:
            Comparison results focused on the specified entities
        """
        focus = f"Focus comparison on how these entities are described: {', '.join(entities)}"
        return self.compare(text_a, text_b, focus)

    def _build_comparison_prompt(self, text_a: str, text_b: str, focus: str) -> str:
        """
        Build the user prompt for comparison.

        Args:
            text_a: First text passage
            text_b: Second text passage
            focus: Optional comparison focus

        Returns:
            Formatted prompt string
        """
        focus_section = f"""
比较焦点：{focus}
""" if focus else ""

        prompt = f"""比较以下两个文本段落。

{focus_section}

文本A：
{text_a}

文本B：
{text_b}

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


要求输出：
提供一个具有以下字段的 JSON 对象：
1. "unique_to_text_a"：仅在文本A中的具体元素（文本A有而文本B没有的）
2. "unique_to_text_b"：仅在文本B中的具体元素（文本B有而文本A没有的）

仅返回 JSON 对象，不附加其他文本。

重要：输出内容必须与上方输入文本的语言保持一致。输入文本为英文时，所有输出内容必须使用英文，不要使用中文。
"""
        return prompt

    def _parse_comparison_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured dictionary.

        Args:
            response: LLM response string

        Returns:
            Parsed comparison results
        """
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            # Ensure all expected fields exist
            default_fields = {
                "summary": "",
                "similarities": [],
                "differences": [],
                "unique_to_text_a": [],
                "unique_to_text_b": [],
                "contradictions": [],
                "overall_assessment": ""
            }

            for key, default in default_fields.items():
                if key not in data:
                    data[key] = default

            return data

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse comparison response: {str(e)}")
            return {
                "summary": "Comparison parsed from raw text",
                "similarities": [],
                "differences": [],
                "unique_to_text_a": [],
                "unique_to_text_b": [],
                "contradictions": [],
                "overall_assessment": response[:500] + "..."
            }
        
    def _empty_result(self, text_a: str, text_b: str) -> Dict[str, Any]:
        """
        Return empty comparison result for empty inputs.

        Args:
            text_a: First text (possibly empty)
            text_b: Second text (possibly empty)

        Returns:
            Empty comparison result
        """
        return {
            "summary": "One or both texts are empty",
            "similarities": [],
            "differences": [],
            "unique_to_text_a": [],
            "unique_to_text_b": [],
            "contradictions": [],
            "overall_assessment": "Comparison not performed due to empty input",
            "_metadata": {
                "text_a_length": len(text_a),
                "text_b_length": len(text_b),
                "error": "Empty text provided"
            }
        }

    def _fallback_comparison(self, text_a: str, text_b: str) -> Dict[str, Any]:
        """
        Fallback comparison when LLM fails.

        Args:
            text_a: First text passage
            text_b: Second text passage

        Returns:
            Basic comparison result
        """
        return {
            "summary": "Fallback comparison generated",
            "similarities": ["Both texts contain information"],
            "differences": ["Text A and Text B have different content"],
            "unique_to_text_a": [text_a[:200] + "..." if len(text_a) > 200 else text_a],
            "unique_to_text_b": [text_b[:200] + "..." if len(text_b) > 200 else text_b],
            "contradictions": [],
            "overall_assessment": "Fallback due to LLM failure; manual comparison recommended"
        }

    def generate_comparison_report(self, result: Dict[str, Any]) -> str:
        """
        Generate a human-readable report from comparison results.

        Args:
            result: Comparison result dictionary

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("📊 TEXT COMPARISON REPORT")
        lines.append("=" * 60)

        if result.get("summary"):
            lines.append(f"\n📝 SUMMARY: {result['summary']}")

        if result.get("similarities"):
            lines.append(f"\n✅ SIMILARITIES ({len(result['similarities'])}):")
            for item in result["similarities"]:
                lines.append(f"  • {item}")

        if result.get("differences"):
            lines.append(f"\n🔀 DIFFERENCES ({len(result['differences'])}):")
            for item in result["differences"]:
                lines.append(f"  • {item}")

        if result.get("unique_to_text_a"):
            lines.append(f"\n📄 UNIQUE TO TEXT A ({len(result['unique_to_text_a'])}):")
            for item in result["unique_to_text_a"]:
                lines.append(f"  • {item}")

        if result.get("unique_to_text_b"):
            lines.append(f"\n📄 UNIQUE TO TEXT B ({len(result['unique_to_text_b'])}):")
            for item in result["unique_to_text_b"]:
                lines.append(f"  • {item}")

        if result.get("contradictions"):
            lines.append(f"\n⚠️ CONTRADICTIONS ({len(result['contradictions'])}):")
            for item in result["contradictions"]:
                lines.append(f"  • {item}")

        if result.get("overall_assessment"):
            lines.append(f"\n🎯 OVERALL ASSESSMENT: {result['overall_assessment']}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
