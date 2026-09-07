"""
KARMA: Leveraging Multi-Agent LLMs for Automated Knowledge Graph Enrichment

A multi-agent framework for extracting, validating, and integrating scientific knowledge
into structured knowledge graphs using specialized Large Language Model agents.

Main Classes:
    KARMAPipeline: Main pipeline for document processing
    KnowledgeTriple: Represents extracted knowledge relationships
    KGEntity: Represents entities in the knowledge graph
    KARMAConfig: Configuration management

Example:
    >>> from karma import KARMAPipeline
    >>> from karma.config import create_default_config
    >>>
    >>> config = create_default_config(api_key="your-api-key")
    >>> pipeline = KARMAPipeline.from_config(config)
    >>> result = pipeline.process_document("path/to/document.pdf")
    >>> print(f"Extracted {len(result.integrated_triples)} knowledge triples")
"""
import os as _os
from pathlib import Path as _Path

# 加载项目根目录的 .env 文件（无外部依赖，不覆盖已有的环境变量）
_env_path = _Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                _k, _v = _k.strip(), _v.strip()
                if _k and _k not in _os.environ:
                    _os.environ[_k] = _v
                    
__version__ = "1.0.0"
__author__ = "Yuxing Lu"
__email__ = "yxlu0613@gmail.com"

# Core imports
from .core.pipeline import KARMAPipeline
from .core.data_structures import (
    KnowledgeTriple,
    KGEntity,
    IntermediateOutput,
    KnowledgeGraph,
    DocumentMetadata,
    ProcessingMetrics
)

# Configuration imports
from .config import KARMAConfig, load_config, save_config

# Agent imports (for advanced usage)
from .agents import (
    IngestionAgent,
    ReaderAgent,
    SummarizerAgent,
    EntityExtractionAgent,
    RelationshipExtractionAgent,
    SchemaAlignmentAgent,
    ConflictResolutionAgent,
    EvaluatorAgent
)

__all__ = [
    # Core classes
    'KARMAPipeline',
    'KnowledgeTriple',
    'KGEntity',
    'IntermediateOutput',
    'KnowledgeGraph',
    'DocumentMetadata',
    'ProcessingMetrics',

    # Configuration
    'KARMAConfig',
    'load_config',
    'save_config',

    # Agents (for advanced usage)
    'IngestionAgent',
    'ReaderAgent',
    'SummarizerAgent',
    'EntityExtractionAgent',
    'RelationshipExtractionAgent',
    'SchemaAlignmentAgent',
    'ConflictResolutionAgent',
    'EvaluatorAgent'
]


def get_version() -> str:
    """Get the KARMA version string."""
    return __version__


def get_info() -> dict:
    """Get information about the KARMA package."""
    return {
        'name': 'KARMA',
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'description': 'Multi-Agent LLMs for Automated Knowledge Graph Enrichment',
        'agents': [
            'IngestionAgent', 'ReaderAgent', 'SummarizerAgent',
            'EntityExtractionAgent', 'RelationshipExtractionAgent',
            'SchemaAlignmentAgent', 'ConflictResolutionAgent', 'EvaluatorAgent'
        ]
    }
