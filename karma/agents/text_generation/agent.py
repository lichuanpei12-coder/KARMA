"""
Text Generation Agent Implementation

The Text Generation Agent converts structured triples (head, relation, tail)
into natural language sentences using LLM-based generation.
"""

import json
import logging
from typing import List, Tuple, Dict, Any, Optional

from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KGEntity, KnowledgeTriple

logger = logging.getLogger(__name__)


class TextGenerationAgent(BaseAgent):
    """
    Text Generation Agent (TGA) for converting triples to natural language.

    This agent:
    1. Takes structured triples as input
    2. Converts them to a linearized format
    3. Uses LLM to generate fluent natural language sentences
    4. Supports batch processing and fallback strategies
    """

    def __init__(self, client, model_name: str, max_tokens: int = 256):
        """
        Initialize the Text Generation Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
            max_tokens: Maximum tokens for generation
        """
        system_prompt = """你是一个专门用于将结构化三元组转换为流畅自然语言句子的文本生成代理。

目标：将结构化三元组（头实体、关系、尾实体）转换为连贯、自然的句子。

输入格式：
- 三元组以如下方式提供："entity1 : relation : entity2 | entity3 : relation : entity4"
- "|"分隔多个三元组
- ":"分隔头实体、关系和尾实体

生成规则：
1. 保留三元组中的所有信息
2. 生成流畅、语法正确的句子
3. 适当时将相关三元组合并为连贯的段落
4. 保持原始含义，不添加外部知识
5. 使用适当的连接词和过渡
6. 输出语言必须与三元组中实体的语言保持一致（实体为英文则用英文输出，实体为中文则用中文输出）

质量标准：
- 准确性：三元组中的所有信息必须存在
- 流畅性：句子应自然阅读
- 连贯性：多个三元组应逻辑流畅
- 完整性：不应遗漏任何信息

忠实性规则：
1. 完全按照描述保留所有技术声明和系统组件
2. 保留所有特定的数值、测量值和参数
3. 保留所有组件名称、零件编号和引用标签
4. 保持组件之间的所有功能关系
5. 不要添加、推断或创建原文中未明确陈述的任何信息
6. 保留所有描述系统架构的附图引用

流畅性规则：
7. 生成连贯的段落，而非项目符号列表
8. 使用清晰、专业的技术语言
9. 用逻辑过渡连接相关概念
10. 保持原始文档的技术语调和精确性

专利压缩的特定规则：
11. 按以下优先级排序（重要性从高到低）：
    - 系统架构和总体结构
    - 组件描述及其互连
    - 功能操作和工作流程
    - 独特或新颖的特征
    - 实施例和替代配置

12. 减少或移除：
    - 重复描述
    - 冗长的法律或程序性语言
    - 过于详细的背景信息
    - 对基本概念的冗余解释

合同和保密协议压缩的特定规则：

13. 按以下优先级排序（重要性从高到低）：
    - 当事人和定义：识别所有合同当事人和关键定义术语
    - 核心义务：每方必须做什么、交付或提供什么
    - 关键日期：生效日期、期限、续签、终止、通知期
    - 货币条款：费用、付款计划、罚款、上限、最低承诺
    - 法律条款：适用法律、管辖权、争议解决、保密、赔偿
    - 终止和存续：终止条件、终止后义务、存续条款
    - 保证和陈述：每方保证什么
    - 责任限制：责任上限、排除损害、免责声明

14. 减少或移除：
    - 重复的法律模板（例如，在多个章节中重复的标准不可抗力、通知条款）
    - 冗长的序言（"鉴于"条款提供上下文但几乎无可操作信息）
    - 过于详细的定义术语（不证自明或仅使用一次的术语）
    - 对文档内其他章节的冗余交叉引用
    - 没有特定管辖细节的标准适用法律条款
    - 收据确认或其他纯程序性语言
    - 不影响当前义务的历史背景或前置协议

输出格式：
- 仅返回生成的文本
- 不附加解释或格式

"""

        super().__init__(client, model_name, system_prompt)
        self.max_tokens = max_tokens

    def process(self, triples: List[Dict[str, str]]) -> str:
        """
        Process method required by BaseAgent interface.

        Args:
            triples: List of triples, each with "head", "relation", "tail" keys

        Returns:
            Generated natural language sentence
        """
        return self.generate_text(triples)

    def generate_text(self, triples: List[KnowledgeTriple]) -> str:
        """
        Convert triples to natural language text.

        Args:
            triples: List of triples, each with "head", "relation", "tail" keys

        Returns:
            Generated natural language sentence
        """
        if not triples:
            logger.warning("No triples provided for generation")
            return ""

        linearized = self._linearize_triples(triples)
        prompt = self._build_generation_prompt(linearized)

        try:
            response, _, _, _ = self._make_llm_call(prompt, temperature=0.0)

            generated_text = self._parse_generation_response(response)

            return generated_text

        except Exception as e:
            logger.warning(f"Text generation failed: {str(e)}")
            return self._fallback_generate(linearized)

    def generate_batch(self, triple_batch: List[List[Dict[str, str]]]) -> List[str]:
        """
        Generate text for multiple sets of triples.

        Args:
            triple_batch: List of triple lists

        Returns:
            List of generated sentences
        """
        results = []
        for triples in triple_batch:
            if triples:
                result = self.generate_text(triples)
                results.append(result)
            else:
                results.append("")
        return results


    def _linearize_triples(self, triples: List[Dict[str, str]]) -> str:
        """
        Convert triples to linearized string format.

        Args:
            triples: List of triples

        Returns:
            Linearized string: "head1 : relation1 : tail1 | head2 : relation2 : tail2"
        """
        triple_strs = []
        for triple in triples:
            head = triple.head
            relation = triple.relation
            tail = triple.tail
            triple_strs.append(f"{head} : {relation} : {tail}")

        return " | ".join(triple_strs)

    def _build_generation_prompt(self, linearized_triples: str) -> str:
        """
        Build the user prompt for text generation.

        Args:
            linearized_triples: Linearized triple string

        Returns:
            Formatted prompt string
        """
        prompt = f"""
                生成指令：

        将以下结构化三元组转换为流畅的自然语言句子。
        输出语言必须与三元组中实体的语言保持一致（实体为英文则用英文输出，实体为中文则用中文输出）。

        忠实性规则：
        1. 生成文本中的每个关系必须直接存在于三元组中。
        2. 不要改变任何关系的强度或方向。
        3. 不要升级或强化任何关系。
        4. 不要降级或弱化任何关系。
        5. 不要添加三元组中没有的修饰词。
        6. 不要遗漏任何三元组。
        7. 如果合并会改变含义，不要将两个三元组合并为一个。
        8. 生成的句子必须忠实反映三元组的内容。

        流畅性规则：
        9. 尽可能将共享同一头实体的三元组合并为一个句子。
        10. 使用连接词（和、同时、其中、此外）来链接相关信息。
        11. 避免在相近位置重复同一个头实体。
        12. 使用关系从句（其中、那个）来平滑地附加修饰词。
        13. 变换句子结构以避免单调的短句列表。
        14. 当多个三元组共享同一关系时，将它们合并为一个结构化列表。
        15. 输出应读起来像一个连贯的段落，而非独立句子的列表。

        三元组格式：
        - 每个三元组："head : relation : tail"
        - 多个三元组用"|"分隔

        结构化输入：
        {linearized_triples}

        自然语言输出：
        """
        return prompt

    def _parse_generation_response(self, response: str) -> str:
        """
        Parse the LLM response to extract the generated text.

        Args:
            response: LLM response string

        Returns:
            Generated text
        """
        # Clean up the response
        generated = response.strip()

        # If the response is quoted, remove quotes
        if generated.startswith('"') and generated.endswith('"'):
            generated = generated[1:-1]

        # If the response contains multiple lines, join them
        if "\n" in generated:
            generated = " ".join(line.strip() for line in generated.split("\n") if line.strip())

        return generated

    def _fallback_generate(self, linearized_triples: str) -> str:
        """
        Fallback generation when LLM fails.

        Args:
            linearized_triples: Linearized triple string

        Returns:
            Simple concatenated text
        """
        # Simple fallback: convert " : " and " | " to natural separators
        text = linearized_triples.replace(" : ", " ").replace(" | ", ". ")
        return text