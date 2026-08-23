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


class IngestionAgent(BaseAgent):#一个子类，父类是BaseAgent，后面有super调用父类的代码
    """
    Ingestion Agent (IA) for document processing and metadata extraction.

    This agent:
    1. Retrieves raw documents from various sources (PDF, text files, URLs)
    2. Converts documents into a consistent normalized text format
    3. Extracts metadata (title, authors, journal, publication date, etc.)
    4. Handles OCR artifacts and text normalization

    用于文档处理和元数据提取的摄取代理（IA）。

    该代理：
    1. 从各种来源（PDF、文本文件、URL）检索原始文档
    2. 将文档转换为一致的标准化文本格式
    3. 提取元数据（标题、作者、期刊、出版日期等）
    4. 处理OCR产生的异常及文本标准化
    """

    def __init__(self, client, model_name: str):
        """
        Initialize the Ingestion Agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
            
        初始化数据采集代理。

        参数：
            client：OpenAI 客户端实例
            model_name：LLM 模型标识符
        """
        system_prompt = """You are a specialized Ingestion Agent for scientific literature processing. Your task is to extract structured metadata from academic documents with high precision and reliability.

OBJECTIVE: Extract bibliographic metadata from scientific documents and return it in a standardized JSON format.

REQUIRED OUTPUT FORMAT:
{
  "title": "Complete document title",
  "authors": ["FirstName LastName", "FirstName LastName"],
  "journal": "Journal or venue name",
  "pub_date": "YYYY-MM-DD",
  "doi": "10.xxxx/xxxxx",
  "pmid": "xxxxxxxx",
  "document_type": "article"
}

EXTRACTION GUIDELINES:
1. TITLE: Extract the complete main title, excluding subtitles unless they provide critical context
2. AUTHORS: List authors in "FirstName LastName" format, exclude affiliations and degrees
3. JOURNAL: Provide full journal name, not abbreviations
4. PUB_DATE: Use YYYY-MM-DD format, estimate year if month/day unavailable
5. DOI: Extract complete DOI including "10." prefix
6. PMID: Extract PubMed ID if present
7. DOCUMENT_TYPE: Classify as "article", "review", "case_study", "editorial", or "other"

QUALITY STANDARDS:
- Use "Unknown" for genuinely unextractable fields
- Maintain original capitalization for proper nouns
- Do not invent or guess missing information
- If multiple titles exist, select the primary research title
- For author names, preserve exact spelling from the document

ERROR HANDLING:
- Return "N/A" for missing DOI/PMID
- Return "Unknown" for indeterminate metadata
- Ensure all required fields are present in response
- Do not return partial or malformed JSON"""
#您是一个专门处理科学文献的摄取代理。您的任务是以高精度和高可靠性从学术文档中提取结构化元数据。
# 目标：从科学文档中提取书目元数据，并以标准化的 JSON 格式返回。
# 必需输出格式：
# {
#   "title": "完整的文档标题",
#   "authors": ["名字 姓氏", "名字 姓氏"],
#   "journal": "期刊或会议名称",
#   "pub_date": "YYYY-MM-DD",
#   "doi": "10.xxxx/xxxxx",
#   "pmid": "xxxxxxxx",
#   "document_type": "article"
# }
# 提取指南：
# 1. 标题：提取完整的主标题，除非副标题提供关键上下文，否则不包括副标题
# 2. 作者：以"名字 姓氏"格式列出作者，不包括所属机构和学位头衔
# 3. 期刊：提供完整的期刊名称，不使用缩写
# 4. 出版日期：使用 YYYY-MM-DD 格式，如果无法获取月份/日期，则估算年份
# 5. DOI：提取完整的 DOI，包括"10."前缀
# 6. PMID：如果存在 PubMed ID，则提取
# 7. 文档类型：分类为"article"（原创论文）、"review"（综述）、"case_study"（案例研究）、"editorial"（社论）或"other"（其他）
# 质量标准：
# - 对于确实无法提取的字段，使用"Unknown"
# - 保留专有名词的原始大小写
# - 不要捏造或猜测缺失信息
# - 如果存在多个标题，选择主要研究标题
# - 对于作者姓名，保留文档中的确切拼写
# 错误处理：
# - 对于缺失的 DOI/PMID，返回"N/A"
# - 对于无法确定的元数据，返回"Unknown"
# - 确保响应中存在所有必需字段
# - 不要返回不完整或格式错误的 JSON
        super().__init__(client, model_name, system_prompt) #调用父类的_init_

    def process(self, raw_text: str, source_info: Dict = None) -> Tuple[DocumentMetadata, str]:
        """
        Process raw text to extract metadata and normalize content.

        Args:
            raw_text: Raw text content to process
            source_info: Optional source information (filepath, URL, etc.)

        Returns:
            Tuple of (DocumentMetadata, normalized_content)

            处理原始文本以提取元数据并规范化内容。
        参数：
            raw_text：待处理的原始文本内容
            source_info：可选的来源信息（文件路径、URL 等）
        返回值：
            (DocumentMetadata, normalized_content) 元组
        """
        # Extract metadata using LLM使用大型语言模型（LLM）提取元数据
        metadata = self._extract_metadata(raw_text)

        # Normalize text content 规范化文本内容
        normalized_content = self._normalize_text(raw_text)

        return metadata, normalized_content

    def _extract_metadata(self, text: str) -> DocumentMetadata:
        """
        Extract document metadata using LLM analysis.

        Args:
            text: Document text to analyze

        Returns:
            DocumentMetadata object with extracted information

         使用大型语言模型（LLM）分析提取文档元数据。
        参数：
            text：待分析的文档文本
        """
        # Truncate text for efficiency (first 5000 characters usually contain metadata)
        sample_text = text[:5000] if len(text) > 5000 else text

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
        #请分析此文档，并提取以下元数据（如果可用）：
        # - 标题
        # - 作者（以列表形式）
        # - 期刊或出版会议/场所
        # - 出版日期（尽可能使用 YYYY-MM-DD 格式）
        # - DOI（数字对象标识符）
        # - PubMed ID（PMID）
        # - 文档类型（article、review、conference paper 等）

        # 如果无法确定任何字段，请将其标记为 "Unknown" 或 "N/A"。
        # 请按以下精确 JSON 格式提供您的响应：
        # {
        #   "title": "...",
        #   "authors": ["...", "..."],
        #   "journal": "...",
        #   "pub_date": "...",
        #   "doi": "...",
        #   "pmid": "...",
        #   "document_type": "..."
        # }

        # 文档样本：
        # {sample_text}

        try:
            response, _, _, _ = self._make_llm_call(prompt, temperature=0.1) #调用大模型 

            # Parse the JSON response
            metadata_dict = self._parse_json_response(response)
            if metadata_dict and isinstance(metadata_dict, dict): #检查结果是否合法（是不是字典 ？）
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

        对文本内容进行规范化处理，以确保处理的一致性。
        参数：
            text：待规范化的原始文本
        返回值：
            规范化后的文本内容
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks 规范段落分隔
        text = re.sub(r'[ \t]+', ' ', text)      # Normalize spaces 规则空格

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
        text = re.sub(r'[\t]+', ' ', text)
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