"""
Relationship Extraction Agent Implementation

The Relationship Extraction Agent identifies relationships between entities
using contextual analysis and domain knowledge.
"""

import logging
from typing import List, Tuple
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
你是一个专门用于商业领域文档的关系抽取和质量评估代理。

任务：从文本中提取商业关系，然后在三个质量维度上评估每个提取的三元组。

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

## 待分析文本：

{text}
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