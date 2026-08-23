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
    
    用于文档分段和相关性评分的阅读代理（RA）。
    该代理：
    1. 将规范化的文本划分为逻辑分段（段落级块）
    2. 根据领域知识为每个分段分配相关性评分
    3. 根据相关性阈值过滤内容
    4. 处理文档的结构化元素（标题、章节等）

    """

    def __init__(self, client, model_name: str):
        """
        Initialize the Reader Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
        """
        system_prompt = """You are a specialized Reader Agent for biomedical literature analysis. Your task is to evaluate text segments and assign precise relevance scores for knowledge extraction.

OBJECTIVE: Score text segments (0.0-1.0) based on their potential to contain extractable biomedical knowledge relationships.

SCORING CRITERIA:
HIGH RELEVANCE (0.8-1.0):
- Results sections with quantitative findings
- Discussion of mechanisms, pathways, or interactions
- Novel discoveries or experimental outcomes
- Specific drug-disease relationships
- Quantitative data (IC50, p-values, concentrations)

MODERATE RELEVANCE (0.4-0.7):
- Background information with entity relationships
- Clinical observations or case descriptions
- General statements about biological processes
- Abstract summaries of findings
- Introduction sections with known facts

LOW RELEVANCE (0.1-0.3):
- Methodological descriptions without outcomes
- Acknowledgments, funding information
- Pure statistical analysis without interpretation
- Equipment descriptions or protocols
- Author affiliations and contact information

MINIMAL RELEVANCE (0.0-0.1):
- References and citations
- Copyright notices
- Figure/table captions without data
- Purely administrative content

SCORING REQUIREMENTS:
- Return only a single float value between 0.0 and 1.0
- Consider biomedical terminology density
- Prioritize content describing relationships between entities
- Account for presence of specific measurements or outcomes
- Evaluate potential for entity-relationship extraction

EXAMPLES:
"IL-6 significantly reduced tumor growth (p<0.001) compared to control" → 0.95
"Patients were enrolled according to institutional guidelines" → 0.15
"Aspirin inhibits COX-2 through covalent binding" → 0.90
"Statistical analysis was performed using SPSS software" → 0.20"""

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

        #return scored_segments, relevant_segments
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
            segments: List of segments to score

        Returns:
            List of segments with relevance scores
        """
        # Process segments in batches to be more efficient
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
            section_info = f" [Section: {seg['section']}]" if seg.get('section') != 'content' else ""
            segment_texts.append(f"Segment {i+1}{section_info}:\n{seg['text'][:500]}...")

        prompt = f"""
        You are a biomedical text relevance scorer.
        Rate how relevant each of the following segments is (0.0 to 1.0) for extracting
        new biomedical knowledge (e.g., relationships between diseases, drugs, genes, proteins).

        Consider:
        - Results and discussion sections usually have higher relevance (0.7-0.9)
        - Abstract and introduction sections have moderate relevance (0.5-0.7)
        - Methods sections without findings have lower relevance (0.2-0.4)
        - References, acknowledgments have very low relevance (0.0-0.2)
        - Content with specific biomedical entities, relationships, or findings scores higher

        For each segment, return only a single float value between 0.0 and 1.0, with no other text.

        {chr(10).join(segment_texts)}

        Return one score per line, with no labels:
        """
        # 您是一名生物医学文本相关性评分员。
        # 请对以下每个片段在提取
        # 新生物医学知识（例如疾病、药物、基因、蛋白质之间的关系）方面的相关性进行评分（0.0 至 1.0）。
        # 请注意：
        # - “结果”和“讨论”部分通常相关性较高（0.7-0.9）
        # - “摘要”和“引言”部分相关性中等（0.5-0.7）
        # - 未包含研究结果的方法部分相关性较低（0.2-0.4）
        # - 参考文献和致谢部分相关性极低（0.0-0.2）
        # - 包含具体生物医学实体、关系或研究结果的内容评分更高
        # 对于每个片段，仅返回一个介于 0.0 到 1.0 之间的浮点数值，不包含其他文本。
        
        try:
            response, _, _, _ = self._make_llm_call(prompt, temperature=0.1)

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