"""
Summarizer Agent Implementation

The Summarizer Agent converts high-relevance text segments into concise summaries
while preserving technical details crucial for knowledge extraction.
"""
from karma.core.api_retry import FatalLLMError

import logging
from typing import List, Tuple

from karma.core.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SummarizerAgent(BaseAgent):
    """
    Summarizer Agent (SA) for text segment summarization.

    This agent:
    1. Converts high-relevance segments into concise summaries
    2. Preserves technical details (gene symbols, chemical names, numeric data)
    3. Maintains entity relationships and quantitative information
    4. Filters out very low relevance content
    """

    def __init__(self, client, model_name: str):
        """
        Initialize the Summarizer Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
        """
        system_prompt = """你是一个专门用于生物医学文献处理的摘要代理。你的任务是创建简洁、信息密集的摘要，保留所有与知识相关的内容。

目标：将文本段落转化为简洁的摘要（<=100词），同时保留所有对知识提取至关重要的实体、关系和定量数据。

保留要求：
必须保留：
- 所有生物医学实体（基因、蛋白质、药物、疾病、化学物质）
- 精确术语（IL-6、p53、BRCA1、阿司匹林等）
- 定量测量（IC50值、p值、浓度、百分比）
- 关系指示词（抑制、激活、治疗、导致、与...相关）
- 统计显著性标记（p<0.05、95% CI、倍数变化）
- 剂量、时间框架和实验条件

语言要求：
- 使用精确的科学语言
- 保持因果关系和逻辑流程
- 保留技术特殊性，不过度简化
- 包含上下文限定词（显著的、中等的、轻微的）
- 保留比较性语言（多于、少于、类似于）

摘要策略：
1. 识别核心知识主张
2. 提取所有命名实体
3. 保留关系陈述
4. 浓缩方法学但保留关键参数
5. 保持定量精确性

输出格式：
- 单一段落，最多100词
- 完整的句子，使用正确的科学语法
- 不使用项目符号或碎片化短语
- 完全按照原文保留术语

示例：
输入："阿司匹林治疗（每日100mg）显著减少骨骼肌中的炎症标志物。COX-2活性较安慰剂组降低45%（p<0.001）。PGE2水平也显著降低（2.1 +/- 0.3 vs 4.2 +/- 0.5 ng/ml, p<0.05）。"

输出："阿司匹林治疗（每日100mg）通过降低COX-2活性45%（p<0.001）显著减少骨骼肌炎症标志物。PGE2水平显著降低（2.1 +/- 0.3 vs 4.2 +/- 0.5 ng/ml, p<0.05）。"

质量控制：
- 绝不编造或修改实体名称
- 绝不近似精确的数值
- 绝不遗漏统计显著性指标
- 绝不简化技术关系"""

        super().__init__(client, model_name, system_prompt)

    def process(self, segments: List[str], relevance_threshold: float = 0.2) -> List[str]:
        """
        Summarize a list of text segments.

        Args:
            segments: List of text segments to summarize
            relevance_threshold: Minimum relevance to process segment

        Returns:
            List of summaries
        """
        summaries, texts = [], []

        # for segment in segments:
        #     if isinstance(segment, dict):
        #         text = segment.get('text', '')
        #         relevance = segment.get('score', 1.0)
        #     else:
        #         text = segment
        #         relevance = 1.0  # Assume relevant if no score provided

        #     if relevance < relevance_threshold:
        #         summaries.append("[OMITTED - Low Relevance]")
        #         continue

        summary = self._summarize_single_segment(segments)
        summaries.append(summary)
        text = segments
        texts.append(text)

        return summaries, texts

    def _summarize_single_segment(self, text: str) -> str:
        """
        Summarize a single text segment.

        Args:
            text: Text segment to summarize

        Returns:
            Summarized text
        """
        # Skip very short segments
        if len(text) < 15:
            return text  # Return as-is if too short to meaningfully summarize

        prompt = f"""
            你是一个文档压缩代理。你的任务是将文档压缩为简洁、信息密集的摘要，同时保留所有关键技术信息。
            生成的摘要理想长度应在 400 到 600 词之间。

            ## 输入
            包含技术描述、系统架构、组件和实施例的文档。

            ## 压缩规则
            质量标准：
            - 准确性：三元组中的所有信息必须存在
            - 流畅性：句子应自然阅读
            - 连贯性：多个三元组应逻辑流畅
            - 完整性：不应遗漏任何信息

            ### 忠实性规则：
            1. 完全按照描述保留所有技术声明和系统组件
            2. 保留所有特定的数值、测量值和参数
            3. 保留所有组件名称、零件编号和引用标签
            4. 保持组件之间的所有功能关系
            5. 不要添加、推断或创建原文中未明确陈述的任何信息
            6. 保留所有描述系统架构的附图引用

            ### 流畅性规则：
            7. 生成连贯的段落，而非项目符号列表
            8. 使用清晰、专业的技术语言
            9. 用逻辑过渡连接相关概念
            10. 保持原始文档的技术语调和精确性

            ### 专利压缩的特定规则：
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

            ## 输出格式
            仅返回压缩后的文本。不附加评论、解释或 JSON 格式。

            ## 输入文本
            {text}

            ## 压缩输出
            """

        try:
            summary, _, _, _ = self._make_llm_call(prompt, temperature=0.0)

            # Basic validation and cleanup
            summary = summary.strip()

            # Handle empty or low-quality responses
            if not summary or summary.lower() in ['[low content]', 'low content', 'n/a']:
                # Fallback: extract key sentences
                return self._extract_key_sentences(text)

            # Ensure summary is within length limit
            if len(summary.split()) > 1000:  # Allow some flexibility
                # Truncate while preserving sentence structure
                sentences = summary.split('. ')
                truncated_summary = ""
                word_count = 0

                for sentence in sentences:
                    sentence_words = len(sentence.split())
                    if word_count + sentence_words <= 1000:
                        truncated_summary += sentence + ". "
                        word_count += sentence_words
                    else:
                        break

                summary = truncated_summary.strip()

            return summary

        except FatalLLMError:
            raise
        except Exception as e:
            logger.warning(f"Summarization failed for segment: {str(e)}")
            return self._extract_key_sentences(text)

    def _extract_key_sentences(self, text: str) -> str:
        """
        Fallback method to extract key sentences when LLM summarization fails.

        Args:
            text: Original text

        Returns:
            Key sentences extracted from text
        """
        sentences = text.split('. ')

        # Score sentences based on biomedical content
        scored_sentences = []

        for sentence in sentences:
            score = self._score_sentence_importance(sentence)
            scored_sentences.append((sentence, score))

        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # Select top sentences within word limit
        selected_sentences = []
        word_count = 0

        for sentence, score in scored_sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= 100 and score > 0.3:
                selected_sentences.append(sentence)
                word_count += sentence_words

        if selected_sentences:
            return '. '.join(selected_sentences) + '.'
        else:
            # Return first 100 words as last resort
            words = text.split()[:100]
            return ' '.join(words) + '...'

    def _score_sentence_importance(self, sentence: str) -> float:
        """
        Score the importance of a sentence for biomedical knowledge extraction.

        Args:
            sentence: Sentence to score

        Returns:
            Importance score (0-1)
        """
        sentence_lower = sentence.lower()
        score = 0.0

        # High-value biomedical terms
        high_value_terms = [
            'inhibit', 'activate', 'regulate', 'express', 'bind', 'interact',
            'cause', 'treat', 'prevent', 'induce', 'suppress', 'enhance',
            'protein', 'gene', 'enzyme', 'receptor', 'pathway', 'mechanism',
            'disease', 'cancer', 'tumor', 'therapy', 'treatment', 'drug',
            'significant', 'increase', 'decrease', 'effect', 'response'
        ]

        # Count high-value terms
        for term in high_value_terms:
            if term in sentence_lower:
                score += 0.1

        # Bonus for numeric data
        import re
        if re.search(r'\d+\.?\d*\s*(%|mg|μg|ng|mM|μM|nM|p\s*[<>=])', sentence):
            score += 0.3

        # Bonus for entity mentions (capitalized terms)
        capitalized_words = re.findall(r'\b[A-Z][A-Za-z0-9-]+\b', sentence)
        score += len(capitalized_words) * 0.05

        # Penalty for very short or very long sentences
        word_count = len(sentence.split())
        if word_count < 5:
            score *= 0.5
        elif word_count > 50:
            score *= 0.8

        return min(1.0, score)

    def summarize_segment(self, segment: str) -> Tuple[str, int, int, float]:
        """
        Legacy method for backward compatibility.

        Args:
            segment: Text segment to summarize

        Returns:
            Tuple of (summary, prompt_tokens, completion_tokens, processing_time)
        """
        summary = self._summarize_single_segment(segment)
        return summary, 0, 0, 0.0  # Token counts handled internally now