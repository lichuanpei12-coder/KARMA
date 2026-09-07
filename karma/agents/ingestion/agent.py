"""
Ingestion Agent Implementation

The Ingestion Agent handles document retrieval, format normalization,
and metadata extraction for various input types.
"""

import logging
from typing import Dict, Tuple
import re
from pathlib import Path

from karma.core.base_agent import BaseAgent
from karma.core.data_structures import DocumentMetadata

logger = logging.getLogger(__name__)


class IngestionAgent(BaseAgent):
    """
    Ingestion Agent (IA) for document processing and metadata extraction.

    This agent:
    1. Retrieves raw documents from various sources (PDF, text files, URLs)
    2. Converts documents into a consistent normalized text format
    3. Extracts metadata (title, authors, journal, publication date, etc.)
    4. Handles OCR artifacts and text normalization
    """

    def __init__(self, client, model_name: str):
        """
        Initialize the Ingestion Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
        """
        system_prompt = """你是一个专门用于科学文献处理的摄入代理。你的任务是从学术文档中高精度、高可靠性地提取结构化元数据。

目标：从科学文档中提取书目元数据，并以标准化的 JSON 格式返回。

要求输出格式：
{
  "title": "完整的文档标题",
  "authors": ["名 姓", "名 姓"],
  "journal": "期刊或会议名称",
  "pub_date": "YYYY-MM-DD",
  "doi": "10.xxxx/xxxxx",
  "pmid": "xxxxxxxx",
  "document_type": "article"
}

提取指南：
1. 标题：提取完整的主标题，除非副标题提供关键上下文，否则不包括副标题
2. 作者：以"名 姓"格式列出作者，排除所属机构和学位
3. 期刊：提供完整的期刊名称，不使用缩写
4. 发布日期：使用 YYYY-MM-DD 格式，如果月/日不可用则估算年份
5. DOI：提取完整的 DOI，包括"10."前缀
6. PMID：如果存在则提取 PubMed ID
7. 文档类型：分类为"article"、"review"、"case_study"、"editorial"或"other"

质量标准：
- 对确实无法提取的字段使用"Unknown"
- 专有名词保持原始大写
- 不要编造或猜测缺失的信息
- 如果存在多个标题，选择主要的研究标题
- 对于作者姓名，保持文档中的精确拼写

错误处理：
- 缺失的 DOI/PMID 返回"N/A"
- 不确定的元数据返回"Unknown"
- 确保响应中包含所有必需字段
- 不要返回不完整或格式错误的 JSON"""

        super().__init__(client, model_name, system_prompt)

    def process(self, raw_text: str, source_info: Dict = None) -> Tuple[DocumentMetadata, str]:
        """
        Process raw text to extract metadata and normalize content.

        Args:
            raw_text: Raw text content to process
            source_info: Optional source information (filepath, URL, etc.)

        Returns:
            Tuple of (DocumentMetadata, normalized_content)
        """
        # Extract metadata using LLM
        # metadata = self._extract_metadata(raw_text)
        metadata = None

        # Normalize text content
        normalized_content = self._normalize_text(raw_text)

        return metadata, normalized_content

    def _extract_metadata(self, text: str) -> DocumentMetadata:
        """
        Extract document metadata using LLM analysis.

        Args:
            text: Document text to analyze

        Returns:
            DocumentMetadata object with extracted information
        """
        # Truncate text for efficiency (first 5000 characters usually contain metadata)
        # sample_text = text[:5000] if len(text) > 5000 else text
        sample_text = text

        prompt = f"""
        Please analyze this document and extract the following metadata if available:
        - Title
        - Authors (as a list)
        - Journal or publication venue
        - Publication date (in YYYY-MM-DD format if possible)
        - DOI (Digital Object Identifier)
        - PubMed ID (PMID)
        - Document type (article, review, conference paper, etc.)

        If any field cannot be determined, mark it as "Unknown" or "N/A".
        Provide your response in this exact JSON format:
        {{
          "title": "...",
          "authors": ["...", "..."],
          "journal": "...",
          "pub_date": "...",
          "doi": "...",
          "pmid": "...",
          "document_type": "..."
        }}

        Document sample:
        {sample_text}
        """

        try:
            response, _, _, _ = self._make_llm_call(prompt, temperature=0.0)

            # Parse the JSON response
            metadata_dict = self._parse_json_response(response)
            if metadata_dict and isinstance(metadata_dict, dict):
                return DocumentMetadata(
                    title=metadata_dict.get("title", "Unknown Title"),
                    authors=metadata_dict.get("authors", []),
                    journal=metadata_dict.get("journal", "Unknown Journal"),
                    pub_date=metadata_dict.get("pub_date", "N/A"),
                    doi=metadata_dict.get("doi", "N/A"),
                    pmid=metadata_dict.get("pmid", "N/A"),
                    document_type=metadata_dict.get("document_type", "article")
                )

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {str(e)}")

        # Fallback: try to extract basic metadata using regex patterns
        return self._extract_metadata_fallback(text)

    def _extract_metadata_fallback(self, text: str) -> DocumentMetadata:
        """
        Fallback metadata extraction using regex patterns.

        Args:
            text: Document text to analyze

        Returns:
            DocumentMetadata with basic extracted information
        """
        metadata = DocumentMetadata()

        # Extract title (usually first significant line)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:  # Reasonable title length
                metadata.title = line
                break

        # Extract DOI
        doi_pattern = r'10\.\d{4,}(?:\.\d+)?\/[^\s]+'
        doi_match = re.search(doi_pattern, text)
        if doi_match:
            metadata.doi = doi_match.group()

        # Extract PubMed ID
        pmid_pattern = r'PMID:?\s*(\d{8,})'
        pmid_match = re.search(pmid_pattern, text, re.IGNORECASE)
        if pmid_match:
            metadata.pmid = pmid_match.group(1)

        # Extract potential authors from common patterns
        author_patterns = [
            r'Authors?:?\s*([A-Za-z\s,.-]+?)(?:\n|$)',
            r'By\s+([A-Za-z\s,.-]+?)(?:\n|$)'
        ]
        for pattern in author_patterns:
            author_match = re.search(pattern, text[:1000], re.IGNORECASE)
            if author_match:
                authors_text = author_match.group(1).strip()
                metadata.authors = [
                    author.strip() for author in re.split(r'[,;]', authors_text)
                    if author.strip() and len(author.strip()) > 2
                ]
                break

        return metadata

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text content for consistent processing.

        Args:
            text: Raw text to normalize

        Returns:
            Normalized text content
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)      # Normalize spaces

        # Handle common OCR artifacts
        ocr_fixes = {
            r'\bﬁ\b': 'fi',           # Common ligature errors
            r'\bﬂ\b': 'fl',
            r'\b1\b(?=\w)': 'I',      # Number 1 confused with letter I
            r'\b0\b(?=[a-z])': 'o',   # Number 0 confused with letter o
            r'([a-z])1([a-z])': r'\1l\2',  # 1 confused with l in middle of words
        }

        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)

        # Normalize Unicode characters
        unicode_fixes = {
            'α': 'alpha',
            'β': 'beta',
            'γ': 'gamma',
            'δ': 'delta',
            'ε': 'epsilon',
            'μ': 'mu',
            '°': ' degrees',
            '±': '+/-',
            '→': ' -> ',
            '←': ' <- ',
            '↑': ' up ',
            '↓': ' down '
        }

        for unicode_char, replacement in unicode_fixes.items():
            text = text.replace(unicode_char, replacement)

        # Clean up extra spaces introduced by replacements
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()

        return text

    def ingest_document(self, raw_text: str) -> Dict:
        """
        Legacy method for backward compatibility.

        Args:
            raw_text: Raw text to process

        Returns:
            Dictionary with metadata and content
        """
        metadata, content = self.process(raw_text)

        return {
            "metadata": metadata.to_dict(),
            "content": content
        }