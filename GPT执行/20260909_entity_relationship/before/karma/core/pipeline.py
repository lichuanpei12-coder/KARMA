"""
KARMA Main Pipeline Implementation

This module contains the main KARMA pipeline that orchestrates all agents
to process documents and extract knowledge.
"""

import logging
import os
import time
import httpx
from typing import List, Union, Optional, Dict
from pathlib import Path
import json

from openai import OpenAI

from .data_structures import (
    KnowledgeTriple, KGEntity, IntermediateOutput,
    DocumentMetadata, ProcessingMetrics, KnowledgeGraph
)

from ..agents import (
    IngestionAgent, ReaderAgent, SummarizerAgent,
    EntityExtractionAgent, RelationshipExtractionAgent,
    # SchemaAlignmentAgent,
    ConflictResolutionAgent, TextGenerationAgent, EvaluatorAgent, TextComparisonAgent
)

from karma.utils.pdf_reader import PDFReader

logger = logging.getLogger(__name__)


class KARMAPipeline:
    """
    Main KARMA pipeline for automated knowledge graph enrichment.

    This class orchestrates the entire pipeline:
    1. Ingestion -> 2. Reading -> 3. Summarization -> 4. Entity Extraction
    -> 5. Relationship Extraction -> 6. Schema Alignment
    -> 7. Conflict Resolution -> 8. Evaluation -> Integration
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model_name: str = "gpt-4o",
        integration_threshold: float = 0.0,
        api_mode: str = "chat_completions"
    ):
        """
        Initialize KARMA pipeline with API credentials.

        Args:
            api_key: OpenAI API key
            base_url: Optional API base URL for Azure or custom endpoints
            model_name: Model identifier
            integration_threshold: Minimum score to integrate knowledge
            api_mode: ``chat_completions`` or ``responses``
        """

        if api_mode not in {"chat_completions", "responses"}:
            raise ValueError("api_mode must be 'chat_completions' or 'responses'")

        # Initialize OpenAI client
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        self.model_name = model_name
        self.integration_threshold = integration_threshold
        self.api_key = api_key
        self.base_url = base_url
        self.api_mode = api_mode

        # Initialize all agent instances
        self._initialize_agents()

        # Initialize knowledge graph and utilities
        self.knowledge_graph = KnowledgeGraph()
        self.pdf_reader = PDFReader()

        # Track processing
        self.output_log: List[str] = []

    @classmethod
    def from_config(cls, config, api_mode: str = "chat_completions") -> 'KARMAPipeline':
        """
        Create pipeline from configuration object.

        Args:
            config: KARMAConfig instance

        Returns:
            Configured pipeline instance
        """
        # Validate and setup configuration
        config.validate()
        config.setup_logging()

        # Create pipeline instance
        pipeline = cls(
            api_key=config.model.api_key,
            base_url=config.model.base_url,
            model_name=config.model.name,
            integration_threshold=config.pipeline.integration_threshold,
            api_mode=api_mode
        )

        return pipeline

    def _initialize_agents(self):
        """Initialize all KARMA agents."""
        self.ingestion_agent = IngestionAgent(self.client, self.model_name)
        self.reader_agent = ReaderAgent(self.client, self.model_name)
        self.summarizer_agent = SummarizerAgent(self.client, self.model_name)
        # self.entity_counter_agent = EntityCounterAgent(self.client, self.model_name)
        self.entity_extraction_agent = EntityExtractionAgent(self.client, self.model_name)
        self.relationship_extraction_agent = RelationshipExtractionAgent(self.client, self.model_name)
        # Disabled for the current open-relation DocOIE evaluation. Keep the
        # original initialization here so the schema stage can be restored later.
        # self.schema_alignment_agent = SchemaAlignmentAgent(self.client, self.model_name)
        self.conflict_resolution_agent = ConflictResolutionAgent(self.client, self.model_name)
        self.text_generation_agent = TextGenerationAgent(self.client, self.model_name)
        self.text_comparison_agent = TextComparisonAgent(self.client, self.model_name)
        self.evaluator_agent = EvaluatorAgent(
            self.client, self.model_name,
            integrate_threshold=self.integration_threshold
        )
        for agent in (
            self.ingestion_agent,
            self.reader_agent,
            self.summarizer_agent,
            self.entity_extraction_agent,
            self.relationship_extraction_agent,
            # self.schema_alignment_agent,
            self.conflict_resolution_agent,
            self.text_generation_agent,
            self.text_comparison_agent,
            self.evaluator_agent,
        ):
            agent.api_mode = self.api_mode

    def process_document(
        self,
        source: Union[str, Path],
        domain: str = "biomedical",
        relevance_threshold: float = 0.2
    ) -> IntermediateOutput:
        # """
        # Process a document and extract knowledge.

        # Args:
        #     source: Text content or path to PDF/text file
        #     domain: Domain context for relevance scoring
        #     relevance_threshold: Minimum relevance score for segments

        # Returns:
        #     IntermediateOutput containing all pipeline results
        # """
        start_time = time.time()
        intermediate = IntermediateOutput()

        try:
            triple = []
            # Step 1: Load and ingest document
            raw_text = self._load_document(source)
            intermediate.raw_text = raw_text

            self._log("Starting KARMA pipeline...")
            # JSON collections are loaded as a list of documents.  A PDF, text
            # file, or raw text is processed as one document.
            documents = raw_text if isinstance(raw_text, list) else [raw_text]
            for i, document_text in enumerate(documents):
                # Feedback belongs to one document only: round 1 starts clean,
                # and round 2 consumes the comparison produced by round 1.
                diff = {}
                print('--------------------------------------------------------------------------')
                print("carrying out knowledge extraction for the article "+str(i))
                # Step 2: Ingestion - Extract metadata and normalize text
                self._log("[1/8] Running Ingestion Agent...")
                step_start = time.time()

                metadata, normalized_content = self.ingestion_agent.process(document_text)
                intermediate.metadata = metadata

                import re as _re
                _PLACEHOLDER = "__NEWLINE_AFTER_PUNCT__"

                # Preserve newline after punctuation marks
                normalized_content = _re.sub(
                    r'([.!?])\s*\n',
                    r'\1' + _PLACEHOLDER,
                    normalized_content
                )

                # Collapse single newlines (that are not part of double newlines) to spaces
                normalized_content = _re.sub(r'(?<!\n)\n(?!\n)', ' ', normalized_content)

                # Restore placeholders
                normalized_content = normalized_content.replace(_PLACEHOLDER, '\n')

                step_time = time.time() - step_start
                intermediate.metrics.add_agent_time("ingestion", step_time)
                self._log(f"[1/8] Ingestion completed in {step_time:.2f}s")

                # Step 3: Reader - Segment and score relevance
                self._log("[2/8] Running Reader Agent...")
                step_start = time.time()

                # ---- NEW: 确保返回的始终是字典列表 ----
                all_segments, relevant_segments = self.reader_agent.process(
                    normalized_content, relevance_threshold
                )

                # 如果 ReaderAgent 不小心返回了字符串列表，统一包装为字典
                def _ensure_dicts(seg_list: List) -> List[Dict]:
                    cleaned: List[Dict] = []
                    for idx, seg in enumerate(seg_list):
                        if isinstance(seg, dict):
                            cleaned.append(seg)
                        else:  # seg 是普通字符串
                            txt = str(seg)
                            cleaned.append({
                                "text": txt,
                                "score": 0.0,
                                "section": self.reader_agent._identify_section_type(txt),
                                "position": idx,
                                "word_count": len(txt.split()),
                            })
                    return cleaned

                all_segments = _ensure_dicts(all_segments)
                relevant_segments = _ensure_dicts(relevant_segments)
                # -----------------------------------------

                intermediate.segments = all_segments
                intermediate.relevant_segments = relevant_segments

                step_time = time.time() - step_start
                intermediate.metrics.add_agent_time("reader", step_time)
                self._log(
                    f"[2/8] Reader completed in {step_time:.2f}s. "
                    f"Segments: {len(all_segments)}, Relevant: {len(relevant_segments)}"
                )

                # Step 4: Summarizer - Create concise summaries
                step_start = time.time()
                if os.environ.get("KARMA_USE_SUMMARIZER"):
                    # 显式开启 summarizer（默认跳过，直接用原文抽取以与 gold 原文对齐）
                    self._log("[3/8] Running Summarizer Agent...")
                    summaries, texts = self.summarizer_agent.process(normalized_content)
                else:
                    self._log("[3/8] 跳过 Summarizer，直接用原文抽取")
                    summaries = [normalized_content]
                    texts = [normalized_content]
                print(summaries)
                intermediate.summaries = summaries
                extraction_text = "\n".join(summaries)

                step_time = time.time() - step_start
                intermediate.metrics.add_agent_time("summarizer", step_time)
                self._log(f"[3/8] Summarizer completed in {step_time:.2f}s. Summaries: {len(summaries)}")

                    
                    # # Step 4.5: Entity Counter - count entities
                    # self._log("[3.5/8] Running Entity Extraction Agent...")
                    # step_start = time.time()

                    # counter = self.entity_counter_agent.process(summaries)

                    # step_time = time.time() - step_start
                    # intermediate.metrics.add_agent_time("entity_extraction", step_time)
                    # self._log(f"[3.5/8] Entity extraction completed in {step_time:.2f}s. Entities: {len(entities)}")
                # Round 1 creates the baseline. Round 2 revises that baseline
                # with explicit add/remove/replace operations grounded in source.
                accumulated_entities: List[KGEntity] = []
                baseline_triples: List[KnowledgeTriple] = []
                for t in range(2):
                    # Step 5: Entity Extraction - Identify entities
                    self._log("[4/8] Running Entity Extraction Agent...")
                    step_start = time.time()

                    round_entities = self.entity_extraction_agent.process(summaries, diff)
                    entities = self.entity_extraction_agent._deduplicate_entities(
                        accumulated_entities + round_entities
                    )
                    accumulated_entities = entities
                    intermediate.entities = entities

                    # dump 中间结果：实体列表
                    _dump_path = self.evaluator_agent._dump_dir / f"_dump_doc{i}_r{t}_entities.json"
                    with open(_dump_path, "w", encoding="utf-8") as _f:
                        json.dump([{"name": e.name, "type": e.entity_type} for e in entities],
                                  _f, ensure_ascii=False, indent=2)

                    step_time = time.time() - step_start
                    intermediate.metrics.add_agent_time("entity_extraction", step_time)
                    self._log(f"[4/8] Entity extraction completed in {step_time:.2f}s. Entities: {len(entities)}")

                    # Step 6: Relationship Extraction - Find relationships
                    self._log("[5/8] Running Relationship Extraction Agent...")
                    step_start = time.time()

                    if t == 0:
                        relationships = self.relationship_extraction_agent.process(
                            summaries, entities, diff
                        )
                    else:
                        relationships = self.relationship_extraction_agent.revise_relationships(
                            extraction_text, baseline_triples, diff
                        )
                    intermediate.relationships = relationships

                    # dump 中间结果：关系列表
                    _dump_path = self.evaluator_agent._dump_dir / f"_dump_doc{i}_r{t}_relationships.json"
                    with open(_dump_path, "w", encoding="utf-8") as _f:
                        json.dump([{"head": r.head, "relation": r.relation, "tail": r.tail}
                                  for r in relationships],
                                  _f, ensure_ascii=False, indent=2)

                    if t == 1:
                        _revision_path = (
                            self.evaluator_agent._dump_dir /
                            f"_dump_doc{i}_r{t}_revision.json"
                        )
                        with open(_revision_path, "w", encoding="utf-8") as _f:
                            json.dump(
                                getattr(
                                    self.relationship_extraction_agent,
                                    "last_revision",
                                    {"mode": "revision_audit_unavailable"},
                                ),
                                _f,
                                ensure_ascii=False,
                                indent=2,
                            )

                    step_time = time.time() - step_start
                    intermediate.metrics.add_agent_time("relationship_extraction", step_time)
                    self._log(f"[5/8] Relationship extraction completed in {step_time:.2f}s. Relationships: {len(relationships)}")

                    # Step 7: Schema Alignment - Align to standard schema
                    # Disabled for the current open-relation DocOIE evaluation.
                    # The original call is preserved below. It intentionally passes
                    # the original objects, so the rule-based agent normalizes them
                    # in place before conflict resolution.
                    # self._log("[6/8] Running Schema Alignment Agent...")
                    # step_start = time.time()
                    # aligned_entities, aligned_relationships = self.schema_alignment_agent.process(
                    #     entities, relationships
                    # )
                    # intermediate.aligned_entities = aligned_entities
                    # intermediate.aligned_triples = aligned_relationships
                    # step_time = time.time() - step_start
                    # intermediate.metrics.add_agent_time("schema_alignment", step_time)
                    # self._log(f"[6/8] Schema alignment completed in {step_time:.2f}s")

                    # Step 8: Conflict Resolution - Handle contradictions
                    self._log("[7/8] Running Conflict Resolution Agent...")
                    step_start = time.time()

                    resolved_relationships = self.conflict_resolution_agent.process(
                        relationships, self.knowledge_graph.triples
                    )
                    intermediate.final_triples = resolved_relationships

                    step_time = time.time() - step_start
                    intermediate.metrics.add_agent_time("conflict_resolution", step_time)
                    self._log(f"[7/8] Conflict resolution completed in {step_time:.2f}s. Non-conflicting: {len(resolved_relationships)}")

                    # Step 9: Evaluation - Final quality assessment
                    self._log("[8/8] Running Evaluator Agent...")
                    step_start = time.time()

                    integrated_triples = self.evaluator_agent.process(resolved_relationships)
                    intermediate.integrated_triples = integrated_triples
                    triples = []
                    for _ti in range(len(integrated_triples)):
                        triple = integrated_triples[_ti].head + ',' + integrated_triples[_ti].relation + ',' + integrated_triples[_ti].tail
                        triples.append(triple)

                    step_time = time.time() - step_start
                    intermediate.metrics.add_agent_time("evaluator", step_time)
                    self._log(f"[8/8] Evaluation completed in {step_time:.2f}s. Integrated: {len(integrated_triples)}")

                    if t == 0:
                        baseline_triples = list(integrated_triples)

                        self._log("[7.5/8] Running Text Generation Agent...")
                        step_start = time.time()
                        text_generation = self.text_generation_agent.process(
                            baseline_triples
                        )
                        print(text_generation)
                        step_time = time.time() - step_start
                        intermediate.metrics.add_agent_time("text_generation", step_time)
                        self._log(
                            f"[7.5/8] Text generation completed in {step_time:.2f}s."
                        )

                        self._log("[9/8] Running Comparison Agent...")
                        step_start = time.time()
                        diff = self.text_comparison_agent.process(
                            extraction_text, text_generation
                        )
                        print(diff)
                        step_time = time.time() - step_start
                        intermediate.metrics.add_agent_time("diff", step_time)
                        self._log(
                            f"[9/8] Comparison completed in {step_time:.2f}s. "
                            f"Integrated: {len(integrated_triples)}"
                        )
                
                
                
                # Step 10: Update Knowledge Graph
                self._update_knowledge_graph(entities, integrated_triples)

                # Finalize metrics
                total_time = time.time() - start_time
                intermediate.metrics.processing_time = total_time

                self._log(f"KARMA pipeline completed in {total_time:.2f}s. Added {len(integrated_triples)} knowledge triples.")

            return intermediate

        except Exception as e:
            intermediate.metrics.error_count += 1
            logger.error(f"Pipeline failed: {str(e)}")
            raise


    def _load_document(self, source: Union[str, Path]) -> str:
        """
        Load document content from various sources.

        Args:
            source: File path or text content

        Returns:
            Raw text content
        """
        if isinstance(source, (str, Path)):
            source_path = Path(source)

            # Check if it's a file path
            if source_path.exists():
                if source_path.suffix.lower() == '.pdf':
                    return self.pdf_reader.extract_text(source_path)
                
                elif source_path.suffix.lower() == '.json':
                    with open(source_path, 'r', encoding='utf-8') as f:
                        d = json.loads(f.read())
                        res = [" ".join(v) for v in d.values() if isinstance(v, list)]
                        return res
                else:
                    # Assume text file
                    with open(source_path, 'r', encoding='utf-8') as f:
                        return f.read()
            else:
                # Treat as raw text if not a valid file path
                return str(source)
        else:
            return str(source)

    def _update_knowledge_graph(self, entities: List[KGEntity], triples: List[KnowledgeTriple]):
        """
        Update the internal knowledge graph with new knowledge.

        Args:
            entities: New entities to add
            triples: New triples to add
        """
        # Add entities
        for entity in entities:
            self.knowledge_graph.add_entity(entity)

        # Add triples
        for triple in triples:
            self.knowledge_graph.add_triple(triple)

    def _log(self, message: str):
        """
        Log message to both logger and internal log.

        Args:
            message: Message to log
        """
        logger.info(message)
        self.output_log.append(message)

    def get_knowledge_graph(self) -> KnowledgeGraph:
        """
        Get the current knowledge graph.

        Returns:
            Current knowledge graph
        """
        return self.knowledge_graph

    def clear_knowledge_graph(self):
        """Clear the knowledge graph."""
        self.knowledge_graph = KnowledgeGraph()
        self._log("Knowledge graph cleared")

    def export_knowledge_graph(self, output_path: Union[str, Path]) -> Dict:
        """
        Export knowledge graph to file.

        Args:
            output_path: Path to save the knowledge graph

        Returns:
            Dictionary representation of the knowledge graph
        """
        self.knowledge_graph.save_to_file(output_path)
        return self.knowledge_graph.to_dict()

    def get_pipeline_statistics(self) -> Dict:
        """
        Get statistics about the pipeline and knowledge graph.

        Returns:
            Dictionary of statistics
        """
        stats = {
            'knowledge_graph': self.knowledge_graph.get_statistics(),
            'agents': {}
        }

        # Get agent-specific metrics
        agents = [
            ('ingestion', self.ingestion_agent),
            ('reader', self.reader_agent),
            ('summarizer', self.summarizer_agent),
            ('entity_extraction', self.entity_extraction_agent),
            ('relationship_extraction', self.relationship_extraction_agent),
            # ('schema_alignment', self.schema_alignment_agent),
            ('conflict_resolution', self.conflict_resolution_agent),
            ('evaluator', self.evaluator_agent)
        ]

        for name, agent in agents:
            stats['agents'][name] = agent.get_metrics()

        return stats

    def process_batch(
        self,
        sources: List[Union[str, Path]],
        domain: str = "biomedical",
        relevance_threshold: float = 0.2
    ) -> List[IntermediateOutput]:
        """
        Process multiple documents in batch.

        Args:
            sources: List of document sources
            domain: Domain context
            relevance_threshold: Minimum relevance threshold

        Returns:
            List of processing results
        """
        results = []

        for i, source in enumerate(sources):
            self._log(f"Processing document {i+1}/{len(sources)}: {source}")
            try:
                result = self.process_document(source, domain, relevance_threshold)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {source}: {str(e)}")
                # Create empty result for failed processing
                failed_result = IntermediateOutput()
                failed_result.metrics.error_count = 1
                results.append(failed_result)

        return results
