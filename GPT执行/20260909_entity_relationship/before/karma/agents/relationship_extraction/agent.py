"""
Relationship Extraction Agent Implementation

The Relationship Extraction Agent identifies relationships between entities
using contextual analysis and domain knowledge.
"""

import logging
from typing import Any, Dict, List, Tuple
import json

from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KGEntity, KnowledgeTriple

logger = logging.getLogger(__name__)


class RelationshipExtractionAgent(BaseAgent):
    """
    Relationship Extraction Agent (REA) for identifying entity relationships.

    This agent:
    1. Identifies relationships between extracted entities
    2. Classifies relationship types using domain patterns
    3. Handles negation and conditional relationships
    4. Provides confidence scores for extracted relationships
    """

    def __init__(self, client, model_name: str):
        """
        Initialize the Relationship Extraction Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
        """
        system_prompt = full_prompt = """
你是一个专门用于技术与专利文档的关系抽取和质量评估代理。

任务：从文本中提取技术关系，然后在三个质量维度上评估每个提取的三元组。

---

# 第一部分：关系抽取

## 抽取规则：
- 仅提取明确陈述或清晰暗示的关系
- 每个关系必须有明确的方向性动作
- 存在时包含具体细节（参数、条件、配置）
- 关系词应严格从原文中提取，保持原文的原始格式。不要擅自将原文中用空格分隔的单词改为下划线连接。例如原文为"mounts to"时，不要写成"mounts_to"。如果原文本身使用下划线，则保持原文格式。
- 三元组原子性：每条三元组表达一个独立的事实（一个主语、一个谓语、一个宾语）
  - 复合关系必须拆分：原文"reads and executes"应拆分为两条三元组：(A, reads, B) 和 (A, executes, B)
  - 因果链必须拆分：原文"controller queries ECU to determine location"应拆分为：(controller, queries, ECU) 和 (controller, determines, location)
  - 一条原文句子中的每个独立关系对应一条三元组，不要将多个关系合并到一条三元组中

## 实体边界规则：
- 头实体和尾实体必须是文本中的原子性技术术语
- 允许：带限定的名词

---

# 第二部分：质量评估

对每个提取的三元组，在三个维度上独立评估。

关键：三个分数必须分开评估。不要简单地给三个维度相同的分数。一个三元组可以具有高置信度但低清晰度（例如，明确陈述但使用模糊术语），或高相关性但低置信度（例如，明显相关但仅是暗示），或任何其他组合。

## 输出格式

仅返回有效的 JSON 数组。前后不要有额外文本。

[
  {
    "head": "执行动作的实体",
    "relation": "动作术语（例如 controls, communicates, generates）",
    "tail": "接受动作的实体",
    "context": "来自专利的简要支撑文本",
    "confidence": 0.0-1.0,
    "clarity": 0.0-1.0,
    "relevance": 0.0-1.0
  }
]


如果无法评估某个三元组，提供默认分数 0.5 并添加"note"字段。

---

## 示例

以下示例展示了期望的抽取风格：

输入文本片段："This method may be integrated in a variety of systems. Such a variety of systems include connected cars, car sharing, rental car services. The instructions are stored on a machine-readable medium. The machine-readable medium is automated data medium. Said minimum bandwidth demand exceeds the measured traffic per time."

期望输出：
[
  {"head": "a variety of systems", "relation": "include", "tail": "car sharing", "context": "Such a variety of systems include connected cars, car sharing", "confidence": 0.9, "clarity": 0.85, "relevance": 0.8},
  {"head": "said minimum bandwidth demand", "relation": "exceeds", "tail": "the measured traffic per time", "context": "Said minimum bandwidth demand exceeds the measured traffic per time", "confidence": 0.9, "clarity": 0.85, "relevance": 0.8},
  {"head": "instructions", "relation": "are stored on", "tail": "a machine-readable medium", "context": "The instructions are stored on a machine-readable medium", "confidence": 0.9, "clarity": 0.85, "relevance": 0.8},
  {"head": "machine-readable medium", "relation": "is", "tail": "automated data medium", "context": "The machine-readable medium is automated data medium", "confidence": 0.9, "clarity": 0.85, "relevance": 0.8}
]

注意：
- 关系词保留原文措辞，如"are stored on"不写成"stored_on"，"is"不写成"is_a"
- 实体保留原文中的限定词和修饰语，如"a variety of systems"不简化为"systems"

---
"""

        super().__init__(client, model_name, system_prompt)

    def process(self, summaries: List[str], entities: List[KGEntity], diff:dict) -> List[KnowledgeTriple]:
        """
        Extract relationships from summaries using the provided entities.

        Args:
            summaries: List of text summaries
            entities: List of entities to find relationships between

        Returns:
            List of extracted knowledge triples
        """
        if not entities:
            return []

        all_relationships = []

        for summary in summaries:
            if summary and summary not in ["[OMITTED - Low Relevance]", "[LOW CONTENT]"]:
                relationships = self._extract_relationships_from_text(summary, entities, diff)
                all_relationships.extend(relationships)

        # Deduplicate relationships
        unique_relationships = self._deduplicate_relationships(all_relationships)

        return unique_relationships

    def revise_relationships(
        self,
        text: str,
        previous_relationships: List[KnowledgeTriple],
        diff: Dict[str, Any],
    ) -> List[KnowledgeTriple]:
        """Revise the current triple list with explicit add/remove/replace operations.

        The current list is the baseline. If the revision response is invalid,
        the baseline is returned unchanged.
        """
        indexed_triples = [
            {
                "index": index,
                "head": triple.head,
                "relation": triple.relation,
                "tail": triple.tail,
            }
            for index, triple in enumerate(previous_relationships)
        ]
        text_a_only = diff.get("unique_to_text_a", []) if diff else []
        text_b_only = diff.get("unique_to_text_b", []) if diff else []

        prompt = f"""
# 任务目标
依据源文本审校当前三元组集合，并根据审校结果生成最小必要的新增、删除和
替换操作。当前集合中没有对应修订操作的三元组由程序原样保留。源文本是
本次事实判断的唯一依据，文本差异只用于帮助定位候选问题。
“最小必要修订”表示仅输出发生变化的操作，不限制应补充的有效事实数量。

# 输入一：源文本
该文本是当前抽取流程使用的文本A。
<source_text>
{text}
</source_text>

# 输入二：当前三元组集合
每条三元组的 index 是从 0 开始的固定编号，remove 和 replace 通过该编号
指向需要修订的三元组。
<current_triples_json>
{json.dumps(indexed_triples, ensure_ascii=False, indent=2)}
</current_triples_json>

# 输入三：文本差异
文本A是源文本，文本B是根据当前三元组集合生成的自然语言文本。

`unique_to_text_a` 表示比较模型认为只在源文本中出现、没有体现在重建文本
中的信息。它的用途是定位可能遗漏的事实，新增结论由源文本核实结果决定。
<unique_to_text_a_json>
{json.dumps(text_a_only, ensure_ascii=False, indent=2)}
</unique_to_text_a_json>

`unique_to_text_b` 表示比较模型认为只在重建文本中出现、没有在源文本中
找到对应依据的信息。它的用途是定位需要复核的当前三元组，删除或替换
结论由源文本核实结果决定。
<unique_to_text_b_json>
{json.dumps(text_b_only, ensure_ascii=False, indent=2)}
</unique_to_text_b_json>

# 修订操作
- add：源文本明确支持，并且当前三元组集合尚未表达的独立事实。
- remove：当前三元组的核心事实缺少源文本支持或与源文本矛盾，并且无法
  通过调整实体边界、关系措辞或方向得到正确事实。
- replace：核心事实存在，但实体边界、关系措辞或方向需要修正。

# 审校规则
1. 将 head、relation、tail 作为一个完整事实判断，结合主动与被动表达确认
   语义角色和关系方向，并按照源文本的句法结构与措辞规范化。
2. head 和 tail 使用源文本中的完整实体边界，保留必要的限定词和修饰语。
3. relation 使用源文本措辞并保留原有空格；源文本使用 "mounts to" 时，
   relation 写作 "mounts to"。
4. 每条三元组只表达一个原子事实。复合动作分别形成多条三元组，因果链
   按独立关系拆分。
5. add 和 replace 的 evidence 使用源文本中逐字复制的连续片段，覆盖
   支持该三元组的完整上下文。
6. 在语义层面检查重复，主动与被动改写、大小写变化和轻微边界差异视为
   同一事实。
7. 每个 index 最多参与一个 remove 或 replace。一个原三元组需要拆成多条
   时，用 replace 给出主要修正，其余独立事实放入 add。
8. `unique_to_text_a` 和 `unique_to_text_b` 均为比较模型生成的候选线索；
   每项操作都以源文本重新核实。证据不足的候选保持当前状态。
9. confidence 表示源文本对事实的支持强度，clarity 表示实体和关系表达的
   清晰程度，relevance 表示该事实对文档技术内容的相关程度。三个分数分别
   评估，取值范围为 0.0 到 1.0，并根据实际情况给分。

# 审校顺序
1. 逐条核对当前三元组，确定其保持当前状态、remove 或 replace。
2. 结合源文本与 `unique_to_text_a` 检查遗漏的原子事实，形成 add。
3. 结合源文本与 `unique_to_text_b` 复核可能缺少依据的当前三元组。
4. 检查操作冲突、语义重复、实体边界和关系方向，形成最终操作集合。

# 操作示例
示例源文本：
The ECUs may include PUF components. The controller may query the ECU.

示例当前三元组：
[
  {{"index": 0, "head": "the controller", "relation": "controls", "tail": "the ECU"}},
  {{"index": 1, "head": "the ECU", "relation": "stores", "tail": "vehicle identity"}}
]

示例操作：
{{
  "add": [
    {{
      "head": "The ECUs",
      "relation": "may include",
      "tail": "PUF components",
      "evidence": "The ECUs may include PUF components.",
      "reason": "源文本中的独立事实尚未包含在当前集合中",
      "confidence": 0.95,
      "clarity": 0.95,
      "relevance": 0.90
    }}
  ],
  "remove": [
    {{
      "index": 1,
      "reason": "源文本没有表达 ECU stores vehicle identity 这一事实"
    }}
  ],
  "replace": [
    {{
      "index": 0,
      "head": "the controller",
      "relation": "may query",
      "tail": "the ECU",
      "evidence": "The controller may query the ECU.",
      "reason": "源文本表达的是 may query，而不是 controls",
      "confidence": 0.95,
      "clarity": 0.95,
      "relevance": 0.90
    }}
  ]
}}

# 输出要求
完整回复采用以下 JSON 对象结构。add、remove、replace 只包含需要执行的
操作；没有修订操作时，对应数组为空。
{{
  "add": [
    {{
      "head": "...",
      "relation": "...",
      "tail": "...",
      "evidence": "源文本中的连续片段",
      "reason": "新增原因",
      "confidence": 0.90,
      "clarity": 0.90,
      "relevance": 0.90
    }}
  ],
  "remove": [
    {{
      "index": 0,
      "reason": "删除原因"
    }}
  ],
  "replace": [
    {{
      "index": 0,
      "head": "...",
      "relation": "...",
      "tail": "...",
      "evidence": "源文本中的连续片段",
      "reason": "修正原因",
      "confidence": 0.90,
      "clarity": 0.90,
      "relevance": 0.90
    }}
  ]
}}
"""

        revision_system_prompt = """你是知识三元组审校专家。依据源文本审校
当前三元组集合，并根据审校结果生成必要的新增、删除和替换操作。完整回复
是一个顶层 JSON 对象，包含 add、remove、replace 三个键，每个键的值是
JSON 数组。"""

        try:
            response, _, _, _ = self._make_llm_call(
                prompt,
                temperature=0.0,
                system_prompt=revision_system_prompt,
            )
            revision = self._parse_revision_response(response)
            revised, audit = self._apply_revision(previous_relationships, revision)
            self.last_revision = audit
            return revised
        except Exception as exc:
            logger.warning("Relationship revision failed; keeping round 1: %s", exc)
            self.last_revision = {
                "mode": "baseline_fallback",
                "reason": str(exc),
                "final_count": len(previous_relationships),
            }
            return list(previous_relationships)

    def _parse_revision_response(self, response: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse the JSON object returned by the revision call."""
        start = response.find("{")
        end = response.rfind("}")
        if start < 0 or end < start:
            raise ValueError("revision response does not contain a JSON object")

        data = json.loads(response[start:end + 1])
        if not isinstance(data, dict):
            raise ValueError("revision response must be a JSON object")

        parsed: Dict[str, List[Dict[str, Any]]] = {}
        for operation in ("add", "remove", "replace"):
            items = data.get(operation, [])
            if not isinstance(items, list):
                raise ValueError(f"revision field '{operation}' must be a list")
            parsed[operation] = [item for item in items if isinstance(item, dict)]
        return parsed

    def _apply_revision(
        self,
        previous_relationships: List[KnowledgeTriple],
        revision: Dict[str, List[Dict[str, Any]]],
    ) -> Tuple[List[KnowledgeTriple], Dict[str, Any]]:
        """Validate and deterministically apply revision operations."""
        replacements: Dict[int, KnowledgeTriple] = {}
        removals = set()
        additions: List[KnowledgeTriple] = []
        accepted: Dict[str, List[Dict[str, Any]]] = {
            "add": [], "remove": [], "replace": []
        }
        rejected: List[Dict[str, Any]] = []

        for item in revision["replace"]:
            index = self._valid_revision_index(item.get("index"), previous_relationships)
            triple = self._triple_from_revision_item(item, "relationship_revision")
            if index is None:
                rejected.append({"operation": "replace", "reason": "invalid index", "item": item})
            elif triple is None:
                rejected.append({"operation": "replace", "reason": "incomplete triple", "item": item})
            elif not str(item.get("evidence", "")).strip():
                rejected.append({"operation": "replace", "reason": "missing evidence", "item": item})
            else:
                replacements[index] = triple
                accepted["replace"].append(item)

        for item in revision["remove"]:
            index = self._valid_revision_index(item.get("index"), previous_relationships)
            reason = str(item.get("reason", "")).strip()
            if index is None:
                rejected.append({"operation": "remove", "reason": "invalid index", "item": item})
            elif not reason:
                rejected.append({"operation": "remove", "reason": "missing reason", "item": item})
            elif index not in replacements:
                removals.add(index)
                accepted["remove"].append(item)

        for item in revision["add"]:
            triple = self._triple_from_revision_item(item, "relationship_revision")
            if triple is None:
                rejected.append({"operation": "add", "reason": "incomplete triple", "item": item})
            elif not str(item.get("evidence", "")).strip():
                rejected.append({"operation": "add", "reason": "missing evidence", "item": item})
            else:
                additions.append(triple)
                accepted["add"].append(item)

        revised: List[KnowledgeTriple] = []
        for index, triple in enumerate(previous_relationships):
            if index in replacements:
                revised.append(replacements[index])
            elif index not in removals:
                revised.append(triple)
        revised.extend(additions)
        revised = self._deduplicate_relationships(revised)

        audit: Dict[str, Any] = {
            "mode": "incremental_revision",
            "accepted": accepted,
            "rejected": rejected,
            "baseline_count": len(previous_relationships),
            "final_count": len(revised),
        }
        return revised, audit

    @staticmethod
    def _valid_revision_index(value: Any, triples: List[KnowledgeTriple]):
        """Return a valid integer index, otherwise None."""
        if isinstance(value, bool):
            return None
        try:
            index = int(value)
        except (TypeError, ValueError):
            return None
        return index if 0 <= index < len(triples) else None

    @staticmethod
    def _safe_score(value: Any, default: float) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return default

    def _triple_from_revision_item(
        self, item: Dict[str, Any], source: str
    ):
        head = str(item.get("head", "")).strip()
        relation = str(item.get("relation", "")).strip()
        tail = str(item.get("tail", "")).strip()
        if not head or not relation or not tail:
            return None
        return KnowledgeTriple(
            head=head,
            relation=relation,
            tail=tail,
            confidence=self._safe_score(item.get("confidence"), 0.5),
            clarity=self._safe_score(item.get("clarity"), 0.5),
            relevance=self._safe_score(item.get("relevance"), 0.5),
            source=source,
        )

    def _extract_relationships_from_text(self, text: str, entities: List[KGEntity], diff: dict) -> List[KnowledgeTriple]:
        """
        Extract relationships from text using LLM analysis.

        Args:
            text: Text to analyze
            entities: List of entities to consider

        Returns:
            List of KnowledgeTriple objects
        """
        if len(entities) < 2:  # Need at least 2 entities for relationships
            return []

        # Create entity reference for the prompt
        entity_names = [ent.name for ent in entities]
        entity_bullets = "\n".join(f"- {name}" for name in entity_names)

        prompt = f"""
        关注的实体：
        {entity_bullets}

        从以下文本中，识别这些实体之间的直接关系。

        待分析文本：
        {text}

        仅返回关系的 JSON 数组。
        """

        unique_text_old = "".join(diff['unique_to_text_a']) if diff else ""
        unique_text_new = "".join(diff['unique_to_text_b']) if diff else ""
        prompt = prompt + f"""你正在从文档中提取关系。重点关注上一次三元组提取中遗漏的信息。
        
1. 优先处理：来自文本A的关系（上一次提取中遗漏的）
文本A包含上一次三元组提取中未被捕获的细节。这些是你的主要提取目标。
文本A（上一次提取中遗漏的信息）：{unique_text_old}

2. 忽略：来自文本B的关系（噪声 - 幻觉）
文本B包含出现在三元组提取中但原文档中无支持的内容。这是噪声。
文本B（应忽略的幻觉噪声）：{unique_text_new}
仅关注原文档支持的关系。

3. 维持：从原文档标准关系提取
从原文档提取所有有效的技术关系，特别关注文本A中识别的遗漏信息。

提取规则
- 提取原文档中明确陈述或清晰暗示的关系
- 每个关系必须有明确的方向性动作（A → B）
- 优先处理与文本A（遗漏信息）相关的关系
- 关注原文档支持的关系
- 存在时包含具体细节（组件标识符、方法步骤、引用编号）
- 包含描述关系的附图引用

关系边界规则
- 头实体和尾实体必须是文本中的原子性技术术语
- 允许：带限定的名词
- 关注：具体的、明确定义的、含义清晰的术语

关键提醒
- 文本A：上一次提取遗漏的内容 → 优先处理这些关系
- 文本B：原文档不支持的内容 → 仅关注原文档支持的内容
- 包括具体的数字、标识符和方法步骤
- 原文档是唯一权威来源

        """ if diff else prompt

        try:
            response, _, _, _ = self._make_llm_call(prompt, temperature=0.0)

            # Parse JSON response
            relations_data = self._parse_json_response(response)

            triples = []
            for rel_data in relations_data:
                if isinstance(rel_data, dict) and all(key in rel_data for key in ["head", "relation", "tail"]):
                    # Validate that entities exist in our entity list
                    head = rel_data.get("head", "").strip()
                    tail = rel_data.get("tail", "").strip()

                    # if self._entity_exists(head, entity_names) and self._entity_exists(tail, entity_names):
                    confidence = float(rel_data.get("confidence", 0.5))
                    evidence = rel_data.get("evidence", "")

                    # Estimate clarity and relevance
                    clarity = float(rel_data.get("clarity", 0.5))
                    relevance = float(rel_data.get("relevance", 0.5))

                    triple = KnowledgeTriple(
                        head=head,
                        relation=rel_data.get("relation", "").strip(),
                        tail=tail,
                        confidence=confidence,
                        clarity=clarity,
                        relevance=relevance,
                        source="relationship_extraction"
                    )
                    triples.append(triple)

            return triples

        except Exception as e:
            logger.warning(f"Relationship extraction failed: {str(e)}")
            return []

    def _entity_exists(self, entity_name: str, entity_list: List[str]) -> bool:
        """
        Check if entity name exists in the entity list (case-insensitive).

        Args:
            entity_name: Name to check
            entity_list: List of entity names

        Returns:
            True if entity exists
        """
        entity_lower = entity_name.lower()
        return any(ent.lower() == entity_lower for ent in entity_list)

    def _estimate_clarity(self, head: str, relation: str, tail: str) -> float:
        """
        Estimate clarity of a relationship triple.

        Args:
            head: Subject entity
            relation: Relationship type
            tail: Object entity

        Returns:
            Clarity score (0-1)
        """
        clarity = 0.5  # Base score

        # Higher clarity for specific relations
        specific_relations = ["treats", "inhibits", "activates", "causes", "regulates"]
        if relation.lower() in specific_relations:
            clarity += 0.2

        # Higher clarity for well-defined entities (not too generic)
        generic_terms = ["protein", "gene", "drug", "disease", "chemical"]
        if head.lower() not in generic_terms:
            clarity += 0.1
        if tail.lower() not in generic_terms:
            clarity += 0.1

        # Lower clarity for very general relations
        if relation.lower() in ["associated_with", "interacts_with"]:
            clarity -= 0.1

        return min(1.0, max(0.1, clarity))

    def _estimate_relevance(self, head: str, relation: str, tail: str) -> float:
        """
        Estimate biomedical relevance of a relationship triple.

        Args:
            head: Subject entity
            relation: Relationship type
            tail: Object entity

        Returns:
            Relevance score (0-1)
        """
        relevance = 0.5  # Base score

        # Higher relevance for therapeutic relationships
        therapeutic_relations = ["treats", "prevents", "causes", "inhibits", "activates"]
        if relation.lower() in therapeutic_relations:
            relevance += 0.2

        # Higher relevance for disease-related triples
        disease_keywords = ["cancer", "disease", "disorder", "syndrome", "infection"]
        if any(keyword in head.lower() or keyword in tail.lower() for keyword in disease_keywords):
            relevance += 0.1

        # Higher relevance for drug-related triples
        drug_keywords = ["drug", "medication", "inhibitor", "agonist", "antagonist", "therapy"]
        if any(keyword in head.lower() or keyword in tail.lower() for keyword in drug_keywords):
            relevance += 0.1

        return min(1.0, max(0.1, relevance))

    def _deduplicate_relationships(self, relationships: List[KnowledgeTriple]) -> List[KnowledgeTriple]:
        """
        Remove duplicate relationships.

        Args:
            relationships: List of relationships to deduplicate

        Returns:
            List of unique relationships
        """
        if not relationships:
            return []

        unique_rels = {}

        for rel in relationships:
            # Create key for deduplication
            key = f"{rel.head.lower()}__{rel.relation.lower()}__{rel.tail.lower()}"

            # Keep the one with higher confidence if duplicates exist
            if key not in unique_rels or rel.confidence > unique_rels[key].confidence:
                unique_rels[key] = rel

        return list(unique_rels.values())

    def extract_relationships(self, text: str, entities: List[KGEntity]) -> Tuple[List[KnowledgeTriple], int, int, float]:
        """
        Legacy method for backward compatibility.

        Args:
            text: Source text
            entities: List of entities to find relationships between

        Returns:
            Tuple of (relationship_list, prompt_tokens, completion_tokens, processing_time)
        """
        relationships = self._extract_relationships_from_text(text, entities)
        return relationships, 0, 0, 0.0  # Token counts handled internally now
