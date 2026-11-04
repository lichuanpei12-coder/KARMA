"""
Reader Agent Implementation

The Reader Agent handles document segmentation and relevance scoring
for efficient downstream processing.
"""

import logging
from typing import List, Dict, Tuple, Optional
import re

from karma.core.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ReaderAgent(BaseAgent):
    """
    Reader Agent (RA) for document segmentation and relevance scoring.

    This agent:
    1. Splits normalized text into logical segments (paragraph-level chunks)
    2. Assigns relevance scores to each segment based on domain knowledge
    3. Filters content based on relevance thresholds
    4. Handles structural document elements (headers, sections, etc.)
    """

    def __init__(self, client, model_name: str):
        """
        Initialize the Reader Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
        """
        system_prompt = """你是一个专门用于生物医学文献分析的阅读代理。你的任务是评估文本段落并为知识提取分配精确的相关性分数。

目标：根据文本段落包含可提取生物医学知识关系的潜力，对其进行评分（0.0-1.0）。

评分标准：
高相关性（0.8-1.0）：
- 包含定量发现的结果部分
- 对机制、通路或相互作用的讨论
- 新发现或实验结果
- 特定的药物-疾病关系
- 定量数据（IC50、p值、浓度）

中等相关性（0.4-0.7）：
- 包含实体关系的背景信息
- 临床观察或病例描述
- 关于生物过程的一般性陈述
- 研究发现的摘要总结
- 包含已知事实的引言部分

低相关性（0.1-0.3）：
- 没有结果的方法描述
- 致谢、资助信息
- 没有解释的纯统计分析
- 设备描述或操作规程
- 作者所属机构和联系信息

最低相关性（0.0-0.1）：
- 参考文献和引用
- 版权声明
- 没有数据的图表标题
- 纯行政内容

评分要求：
- 仅返回一个 0.0 到 1.0 之间的浮点数
- 考虑生物医学术语密度
- 优先考虑描述实体之间关系的内容
- 考虑特定测量或结果的存在
- 评估实体-关系提取的潜力

示例：
"IL-6显著减少肿瘤生长（p<0.001）与对照组相比" → 0.95
"患者根据机构指南入组" → 0.15
"阿司匹林通过共价结合抑制COX-2" → 0.90
"使用SPSS软件进行统计分析" → 0.20"""

        super().__init__(client, model_name, system_prompt)

    def process(self, content: str, relevance_threshold: float = 0.2) -> Tuple[List[Dict], List[Dict]]:
        """
        Segment content and score relevance of each segment.

        Args:
            content: Text content to segment
            relevance_threshold: Minimum relevance score to keep segments

        Returns:
            Tuple of (all_segments, relevant_segments)
        """
        # Split into logical segments
        segments = self._split_into_segments(content)

        # Score relevance for each segment
        scored_segments = self._score_segments_batch(segments)

        # Filter relevant segments
        relevant_segments = [
            seg for seg in scored_segments
            if seg.get('score', 0.0) >= relevance_threshold
        ]

        return (
            self._ensure_dict_segments(scored_segments),
            self._ensure_dict_segments(relevant_segments)
        )

    def _split_into_segments(self, content: str) -> List[Dict]:
        """
        Split content into logical segments.
        If the document contains sub‑headings, the text **between two consecutive headings**
        will be merged into a single paragraph segment.  If no headings are detected,
        we fall back to a simple sentence‑based split: a newline that follows a period
        (or other end‑of‑sentence punctuation) creates a new segment.
        """
        segments: List[Dict] = []

        # ------------------------------------------------------------
        # 1️⃣ 先把行宽换行（单个 \n）合并为普通空格，保留真正的换行符
        #    （这里仍然保留所有原始换行，后面的 split('\n') 会把每行都当段落）
        # ------------------------------------------------------------
        # content = re.sub(r'(?<!\n)\n(?!\n)', ' ', content)

        # ------------------------------------------------------------
        # 2️⃣ 小标题检测规则（词数 ≤8、无标点、每词首字母大写）
        # ------------------------------------------------------------
        def _is_heading(line: str) -> bool:
            stripped = line.strip()
            if not stripped:
                return False
            # 词数阈值
            if len(stripped.split()) > 8:
                return False
            # 没有常见句子标点
            if re.search(r'[.!?;:,]', stripped):
                return False
            # 所有单词首字母大写（忽略全大写或全小写的情况）
            words = stripped.split()
            return all(word[0].isupper() for word in words if word)

        # ------------------------------------------------------------
        # 3️⃣ 收集所有标题行的索引及文本
        # ------------------------------------------------------------
        lines = content.split('\n')
        heading_indices: List[int] = []
        heading_texts: List[str] = []
        for idx, line in enumerate(lines):
            if _is_heading(line):
                heading_indices.append(idx)
                heading_texts.append(line.strip())

        # ------------------------------------------------------------
        # 4️⃣ 如果检测到标题，则按标题分块合并段落
        # ------------------------------------------------------------
        if heading_indices:
            # 为每个标题创建一个 header 段落
            for h_idx, h_text in zip(heading_indices, heading_texts):
                segments.append({
                    "text": h_text,
                    "score": 0.0,
                    "section": "header",
                    "position": h_idx,
                    "word_count": len(h_text.split()),
                })

            # 合并标题之间的正文（不包括标题本身）
            for i in range(len(heading_indices)):
                start = heading_indices[i] + 1
                end = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(lines)
                body_lines = [ln.strip() for ln in lines[start:end] if ln.strip()]
                if body_lines:
                    body_text = " ".join(body_lines)
                    section_type = self._identify_section_type(body_text)
                    segments.append({
                        "text": body_text,
                        "score": 0.0,
                        "section": section_type,
                        "position": start,
                        "word_count": len(body_text.split()),
                    })
        else:
            # ------------------------------------------------------------
            # 5️⃣ 没有标题时，使用句号后换行的自然段划分
            # ------------------------------------------------------------
            # 把 "句号+换行" 当作段落分隔符（保留句号）
            raw_paragraphs = re.split(r'(?<=[.!?])\s*\n+', content)
            for i, para in enumerate(raw_paragraphs):
                para = para.strip()
                if not para:
                    continue
                section_type = self._identify_section_type(para)
                segments.append({
                    "text": para,
                    "score": 0.0,
                    "section": section_type,
                    "position": i,
                    "word_count": len(para.split()),
                })

        return segments


    def _ensure_dict_segments(self, segments: List) -> List[Dict]:
        """
        将可能出现的字符串段落包装成最小的字典结构，防止后续 .get 调用出错。
        """
        cleaned: List[Dict] = []
        for idx, seg in enumerate(segments):
            if isinstance(seg, dict):
                cleaned.append(seg)
            else:
                txt = str(seg)
                cleaned.append({
                    "text": txt,
                    "score": 0.0,
                    "section": self._identify_section_type(txt),
                    "position": idx,
                    "word_count": len(txt.split()),
                })
        return cleaned

    def _identify_section_type(self, text: str) -> str:
        """
        Identify the type of section based on content patterns.

        Args:
            text: Segment text to analyze

        Returns:
            Section type identifier
        """
        text_lower = text.lower()

        # Common section headers
        section_patterns = {
            'abstract': [r'^abstract\b', r'summary\b'],
            'introduction': [r'^introduction\b', r'^background\b'],
            'methods': [r'^methods?\b', r'^methodology\b', r'^materials\b', r'^experimental\b'],
            'results': [r'^results?\b', r'^findings\b', r'^outcomes?\b'],
            'discussion': [r'^discussion\b', r'^conclusion\b', r'^implications\b'],
            'references': [r'^references?\b', r'^bibliography\b', r'^\d+\.\s+\w+.*et al'],
            'acknowledgments': [r'^acknowledgments?\b', r'^acknowledgements?\b'],
            'funding': [r'^funding\b', r'^grants?\b', r'^financial\b'],
            'supplementary': [r'^supplement', r'^appendix\b', r'^additional\b']
        }

        for section_type, patterns in section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return section_type

        # If no specific section identified, categorize by content characteristics
        if len(text.split()) < 10:
            return 'header'
        elif re.search(r'\d+\.\s+\w+.*\(\d{4}\)', text):  # Citation pattern
            return 'references'
        elif text.startswith(('Figure', 'Table', 'Fig.')):
            return 'figure_caption'
        else:
            return 'content'

    def _score_segments_batch(self, segments: List[Dict]) -> List[Dict]:
        """
        Score relevance for multiple segments efficiently.

        Args:
            segments: List of segments to score (may contain raw strings)

        Returns:
            List of segments with relevance scores (all as dicts)
        """
        # ------------------------------------------------------------
        # 1️⃣ Ensure every item is a dict; wrap raw strings if needed
        # ------------------------------------------------------------
        normalized: List[Dict] = []
        for idx, seg in enumerate(segments):
            if isinstance(seg, dict):
                normalized.append(seg)
            else:
                txt = str(seg)
                normalized.append({
                    "text": txt,
                    "section": self._identify_section_type(txt),
                    "score": 0.0,
                    "position": idx,
                    "word_count": len(txt.split()),
                })
        # Now work with the guaranteed‑dict list
        segments = normalized

        # ------------------------------------------------------------
        # 2️⃣ Process in batches to be more efficient
        # ------------------------------------------------------------
        batch_size = 5
        scored_segments = []

        for i in range(0, len(segments), batch_size):
            batch = segments[i:i+batch_size]
            scores = self._batch_score_relevance(batch)

            for j, segment in enumerate(batch):
                if j < len(scores):
                    segment['score'] = scores[j]
                else:
                    segment['score'] = self._get_default_score(segment)
                scored_segments.append(segment)

        return scored_segments

    def _batch_score_relevance(self, segments: List[Dict]) -> List[float]:
        """
        Score relevance for a batch of segments using LLM.

        Args:
            segments: List of segments to score

        Returns:
            List of relevance scores
        """
        if not segments:
            return []

        # Create batch prompt
        segment_texts = []
        for i, seg in enumerate(segments):
            # Ensure seg is a dict; if it's a raw string, wrap it minimally
            if not isinstance(seg, dict):
                seg = {
                    "text": str(seg),
                    "section": self._identify_section_type(str(seg)),
                }
            section_info = f" [Section: {seg['section']}]" if seg.get('section') != 'content' else ""
            segment_texts.append(f"Segment {i+1}{section_info}:\n{seg['text'][:500]}...")

        prompt = f"""
        你是一个生物医学文本相关性评分器。
        对以下每个段落的相关性进行评分（0.0 到 1.0），评估其对于提取
        新的生物医学知识（例如疾病、药物、基因、蛋白质之间的关系）的潜力。

        考虑因素：
        - 结果和讨论部分通常具有更高的相关性（0.7-0.9）
        - 摘要和引言部分具有中等相关性（0.5-0.7）
        - 没有发现的方法部分具有较低的相关性（0.2-0.4）
        - 参考文献、致谢具有很低的相关性（0.0-0.2）
        - 包含特定生物医学实体、关系或发现的内容得分更高

        对每个段落，仅返回一个 0.0 到 1.0 之间的浮点数，不附加其他文本。

        {chr(10).join(segment_texts)}

        每行返回一个分数，不带标签：
        """

        try:
            response, _, _, _ = self._make_llm_call(prompt, temperature=0.0)

            lines = response.strip().split('\n')
            scores = []

            for line in lines:
                score = self._extract_float_from_text(line.strip(), default=0.5)
                scores.append(score)

            # Ensure we have scores for all segments
            while len(scores) < len(segments):
                scores.append(0.5)

            return scores[:len(segments)]

        except Exception as e:
            logger.warning(f"Batch scoring failed: {str(e)}")
            return [self._get_default_score(seg) for seg in segments]

    def _get_default_score(self, segment: Dict) -> float:
        """
        Get default relevance score based on segment characteristics.

        Args:
            segment: Segment to score

        Returns:
            Default relevance score
        """
        section_type = segment.get('section', 'content')
        word_count = segment.get('word_count', 0)

        # Default scores based on section type
        section_scores = {
            'results': 0.8,
            'discussion': 0.7,
            'abstract': 0.6,
            'introduction': 0.5,
            'content': 0.5,
            'methods': 0.3,
            'references': 0.1,
            'acknowledgments': 0.1,
            'funding': 0.1,
            'supplementary': 0.2,
            'header': 0.2,
            'figure_caption': 0.4
        }

        base_score = section_scores.get(section_type, 0.5)

        # Adjust based on content length
        if word_count < 10:
            base_score *= 0.5  # Very short segments less relevant
        elif word_count > 100:
            base_score *= 1.1  # Longer segments might be more informative

        return min(1.0, max(0.0, base_score))

    def score_relevance(self, segment: str) -> Tuple[float, int, int, float]:
        """
        Legacy method for backward compatibility.

        Args:
            segment: Text segment to score

        Returns:
            Tuple of (relevance_score, prompt_tokens, completion_tokens, processing_time)
        """
        segment_dict = {'text': segment, 'section': 'content', 'word_count': len(segment.split())}
        scored_segments = self._score_segments_batch([segment_dict])

        if scored_segments:
            return scored_segments[0]['score'], 0, 0, 0.0
        else:
            return 0.5, 0, 0, 0.0

    def split_into_segments(self, content: str) -> List[Dict]:
        """
        Legacy method for backward compatibility.

        Args:
            content: Content to segment

        Returns:
            List of segment dictionaries
        """
        all_segments, _ = self.process(content)
        return all_segments