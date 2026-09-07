"""
Entity Extraction Agent Implementation

The Entity Extraction Agent identifies and classifies biomedical entities
from summarized text using LLM-based named entity recognition.
"""

import logging
from typing import List, Tuple, Dict
import json
import re

from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KGEntity

logger = logging.getLogger(__name__)


class EntityExtractionAgent(BaseAgent):
    """
    Entity Extraction Agent (EEA) for biomedical entity identification.

    This agent:
    1. Identifies biomedical entities (Disease, Drug, Gene, Protein, Chemical, etc.)
    2. Classifies entity types using domain knowledge
    3. Links entities to canonical ontology references where possible
    4. Handles entity normalization and synonym resolution
    """

    def __init__(self, client, model_name: str):
        """
        Initialize the Entity Extraction Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
        """
        system_prompt = """
你是一个专门用于商业领域文档的实体抽取代理。

目标：从文本中提取所有商业实体。

提取规则：

- 提取文本中出现的精确提及
- 保留商业和技术术语的原始大写和格式
- 包括缩写和首字母缩略词
- 捕获数值、货币金额、日期、阈值和标识符
- 包括版本号、文档引用、条款编号和章节标识符
- 对于合同：提取当事人名称、日期、货币金额、定义术语、条款引用
- 对于金融文档：提取金额、百分比、日期、实体名称、财务指标
- 对于专利：提取系统组件、方法步骤、图表、技术参数

实体边界规则：

- 实体必须是承载意义的最小、原子性术语
- 原子性判断规则：
  - 并列实体必须拆分：原文"first and second cables"应拆分为"first cable"和"second cable"两个实体
  - 带介词短语的保留整体：原文"pre-step of grinding"应提取为"pre-step of grinding"一个实体，不拆分
  - 带修饰语的复合名词保留整体：原文"machine-readable medium"应提取为"machine-readable medium"一个实体，不拆分
  - 判断标准：拆分后若某部分失去原文中的特定含义则不拆；若各部分仍保持独立完整含义则拆分
- 实体名应严格从原文中提取，保持原文的原始格式。不要擅自将原文中用空格分隔的单词改为下划线连接。例如原文为"front running vehicle"时，不要写成"front_running_vehicle"。如果原文本身使用下划线，则保持原文格式。
- 允许：
  - 简单名词
  - 带限定的名词
  - 带数值的名词
  - 带标识符的名词
- 禁止：
  - 实验条件
  - 统计值
  - 不增加特定含义的过于宽泛的修饰词

质量标准：

- 高精度：仅提取明确定义和可识别的术语
- 完整性：识别文档中所有重要实体
- 一致性：在整个提取过程中使用相同的实体名称格式
- 上下文适当性：同一类型的术语在一种文档类型中可能是实体（例如合同中的"适用法律"），在另一种类型中可能不是

文档类型适配：

- 对于合同：优先提取当事人、日期、货币金额、条款、定义术语、义务、适用法律
- 对于财务报告：优先提取货币值、百分比、日期、实体名称、财务指标
- 对于专利：优先提取系统组件、方法、图表、技术参数、新颖特征
- 对于商业文档：优先提取公司名称、角色、日期、金额、关键术语

输出格式：
仅返回有效的 JSON 数组，结构如下：
[
  {
    "mention": "来源中的精确术语",
    "type": "类别名称",
    "context": "文本中的简要上下文"
  }
]
"""

        super().__init__(client, model_name, system_prompt)

    def process(self, summaries: List[str], diff: dict) -> List[KGEntity]:
        """
        Extract entities from a list of text summaries.

        Args:
            summaries: List of text summaries to process

        Returns:
            List of extracted and deduplicated entities
        """
        all_entities = []

        for summary in summaries:
            if summary and summary not in ["[OMITTED - Low Relevance]", "[LOW CONTENT]"]:
                entities = self._extract_entities_from_text(summary, diff)
                all_entities.extend(entities)

        # Deduplicate entities
        unique_entities = self._deduplicate_entities(all_entities)

        return unique_entities

    def _extract_entities_from_text(self, text: str, diff: dict) -> List[KGEntity]:
        """
        Extract entities from a single text.

        Args:
            text: Text to extract entities from

        Returns:
            List of KGEntity objects
        """
        prompt = f"""
从以下专利文档中提取所有技术实体。

专利文档：
{text}

仅返回实体的 JSON 数组。
"""

        unique_text_old = "".join(diff['unique_to_text_a']) if diff else ""
        unique_text_new = "".join(diff['unique_to_text_b']) if diff else ""
        prompt = prompt + f"""你正在从专利文档中提取实体。重点关注上一次三元组提取中遗漏的信息。

1. 优先处理：来自文本A的信息（上一次提取中遗漏的）
文本A包含上一次三元组提取中未被捕获的技术细节。这些是你的主要提取目标。
文本A（上一次提取中遗漏的信息）：{unique_text_old}

2. 忽略：来自文本B的信息（噪声 - 幻觉）
文本B包含出现在三元组提取中但原文档中无支持的内容。这是噪声。
文本B（应忽略的幻觉噪声）：{unique_text_new}
仅关注原文档支持的内容。

3. 维持：从原文档标准提取
从原文档提取所有有效的技术实体，特别关注文本A中识别的遗漏信息。

提取规则
- 从原文档提取精确提及
- 优先处理与文本A（遗漏信息）相关的实体
- 关注原文档支持的信息
- 包括具体的数字、标识符和引用
- 捕获带引用编号的方法步骤
- 包括附图引用
- 保留技术术语
- 仅提取原文档中出现的实体

        """ if diff else prompt

        try:
            response, _, _, _ = self._make_llm_call(prompt, temperature=0.0)

            # Parse JSON response
            entities_data = self._parse_json_response(response)

            entity_list = []
            for ent_data in entities_data:
                if isinstance(ent_data, dict) and "mention" in ent_data:
                    entity = KGEntity(
                        entity_id=ent_data.get("mention", ""),
                        entity_type=ent_data.get("type", "Unknown"),
                        name=ent_data.get("mention", ""),
                        normalized_id=ent_data.get("normalized_id", "N/A"),
                        aliases=ent_data.get("aliases", [])
                    )
                    entity_list.append(entity)

            return entity_list

        except Exception as e:
            logger.warning(f"Entity extraction failed for text: {str(e)}")
            # Fallback: use simple regex-based extraction
            return self._fallback_entity_extraction(text)

    def _fallback_entity_extraction(self, text: str) -> List[KGEntity]:
        """
        Fallback entity extraction using pattern matching.

        Args:
            text: Text to extract entities from

        Returns:
            List of KGEntity objects
        """
        entities = []

        # Common biomedical entity patterns
        patterns = {
            'Gene': [
                r'\b[A-Z][A-Z0-9]{2,}[a-z]?\b',  # Gene symbols (e.g., TP53, BRCA1)
                r'\b[A-Z]{1,2}[0-9]+[A-Z]?\b'     # Gene IDs (e.g., IL6, TNF)
            ],
            'Protein': [
                r'\b[A-Z][a-z]+[0-9]*\s*receptor\b',  # Receptors
                r'\b[A-Z][a-z]+ase\b',                # Enzymes ending in -ase
                r'\b[A-Z][a-z]+in\b'                  # Proteins ending in -in
            ],
            'Drug': [
                r'\b[a-z]+mycin\b',                   # Antibiotics
                r'\b[a-z]+cillin\b',                  # Penicillins
                r'\b[a-z]+statin\b'                   # Statins
            ],
            'Disease': [
                r'\b[a-z]+\s+cancer\b',               # Cancers
                r'\b[a-z]+\s+disease\b',              # Diseases
                r'\b[a-z]+\s+syndrome\b'              # Syndromes
            ]
        }

        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    mention = match.group().strip()
                    if len(mention) > 2:  # Skip very short matches
                        entity = KGEntity(
                            entity_id=mention,
                            entity_type=entity_type,
                            name=mention,
                            normalized_id="N/A"
                        )
                        entities.append(entity)

        return entities

    def _deduplicate_entities(self, entities: List[KGEntity]) -> List[KGEntity]:
        """
        Remove duplicate entities based on name similarity.

        Args:
            entities: List of entities to deduplicate

        Returns:
            List of unique entities
        """
        if not entities:
            return []

        unique_entities = {}

        for entity in entities:
            # Create a normalized key for comparison
            key = entity.name.lower().strip()

            # If we've seen this entity before, merge information
            if key in unique_entities:
                existing = unique_entities[key]

                # Prefer more specific entity types
                if entity.entity_type != "Unknown" and existing.entity_type == "Unknown":
                    existing.entity_type = entity.entity_type

                # Merge aliases
                if entity.aliases:
                    existing.aliases.extend(entity.aliases)
                    existing.aliases = list(set(existing.aliases))  # Remove duplicates

                # Prefer non-N/A normalized IDs
                if entity.normalized_id != "N/A" and existing.normalized_id == "N/A":
                    existing.normalized_id = entity.normalized_id

            else:
                unique_entities[key] = entity

        return list(unique_entities.values())

    def extract_entities(self, text: str) -> Tuple[List[KGEntity], int, int, float]:
        """
        Legacy method for backward compatibility.

        Args:
            text: Text to extract entities from

        Returns:
            Tuple of (entity_list, prompt_tokens, completion_tokens, processing_time)
        """
        entities = self._extract_entities_from_text(text)
        return entities, 0, 0, 0.0  # Token counts handled internally now