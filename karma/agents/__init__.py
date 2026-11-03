"""
KARMA Agents Module

This module contains all the specialized agents used in the KARMA pipeline.
Each agent handles a specific stage of the knowledge extraction process.
"""

from .ingestion.agent import IngestionAgent
from .reader.agent import ReaderAgent
from .summarizer.agent import SummarizerAgent
# from .entity_counter.agent import EntityCounterAgent
from .entity_extraction.agent import EntityExtractionAgent
from .relationship_extraction.agent import RelationshipExtractionAgent
from .triple_splitting.agent import TripleSplittingAgent
from .schema_alignment.agent import SchemaAlignmentAgent
from .conflict_resolution.agent import ConflictResolutionAgent
from .text_generation.agent import TextGenerationAgent
from .evaluator.agent import EvaluatorAgent
from .text_comparison.agent import TextComparisonAgent
from .feedback_add.agent import FeedbackAddAgent
from .feedback_replace.agent import FeedbackReplaceAgent
from .feedback_remove.agent import FeedbackRemoveAgent


__all__ = [
    'IngestionAgent',
    'ReaderAgent',
    'SummarizerAgent',
    'EntityExtractionAgent',
    'RelationshipExtractionAgent',
    'TripleSplittingAgent',
    'SchemaAlignmentAgent',
    'ConflictResolutionAgent',
    'TextGenerationAgent',
    'EvaluatorAgent',
    'TextComparisonAgent',
    'FeedbackAddAgent', 'FeedbackReplaceAgent', 'FeedbackRemoveAgent'
]
