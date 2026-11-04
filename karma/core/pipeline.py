"""
KARMA Main Pipeline Implementation

This module contains the main KARMA pipeline that orchestrates all agents
to process documents and extract knowledge.
"""

import logging
import copy
import os
import time
import httpx
from typing import List, Union, Optional, Dict
from pathlib import Path
import json
import hashlib
import inspect

from .run_artifacts import load_baseline, save_baseline, select_documents, write_json
from .sentence_groups import source_sentences, attach_sources, group_triples
from .feedback_pipeline import FeedbackPipeline
from .sentence_feedback_pipeline import SentenceFeedbackPipeline
from .triple_scores import fixed_score_copy
from ..agents.feedback_add.agent import FeedbackAddAgent
from ..agents.feedback_replace.agent import FeedbackReplaceAgent
from ..agents.feedback_remove.agent import FeedbackRemoveAgent

from openai import OpenAI

from .data_structures import (
    KnowledgeTriple, KGEntity, IntermediateOutput,
    DocumentMetadata, ProcessingMetrics, KnowledgeGraph
)

from ..agents import (
    IngestionAgent, ReaderAgent, SummarizerAgent,
    EntityExtractionAgent, RelationshipExtractionAgent, TripleSplittingAgent,
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
        api_mode: str = "chat_completions",
        feedback_scope: str = "sentence",
        text_scope: str = "sentence"
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

        if feedback_scope not in ("sentence", "document") or text_scope not in ("sentence", "document"):
            raise ValueError("feedback_scope and text_scope must be sentence or document")
        self.feedback_scope = feedback_scope
        self.text_scope = text_scope

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
            api_mode=api_mode,
            feedback_scope=config.pipeline.feedback_scope,
            text_scope=config.pipeline.text_scope
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
        self.triple_splitting_agent = TripleSplittingAgent(self.client, self.model_name)
        self.feedback_add_agent = FeedbackAddAgent(self.client, self.model_name)
        self.feedback_replace_agent = FeedbackReplaceAgent(self.client, self.model_name)
        self.feedback_remove_agent = FeedbackRemoveAgent(self.client, self.model_name)
        feedback_class = SentenceFeedbackPipeline if self.feedback_scope == "sentence" else FeedbackPipeline
        self.feedback_pipeline = feedback_class(
            self.feedback_add_agent, self.feedback_replace_agent, self.feedback_remove_agent)
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
            self.triple_splitting_agent,
            self.feedback_add_agent,
            self.feedback_replace_agent,
            self.feedback_remove_agent,
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
        relevance_threshold: float = 0.2,
        *, stage: str = "full", baseline_path: Optional[Union[str, Path]] = None,
        doc_ids: Optional[List[str]] = None, limit: Optional[int] = None,
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
            if stage not in {"full", "baseline", "revise"}:
                raise ValueError("stage must be full, baseline, or revise")
            if (self.evaluator_agent._dump_dir / "_run_manifest.json").exists():
                self.evaluator_agent._dump_dir = self.evaluator_agent._dump_dir / f"run_{time.time_ns()}"
                self.evaluator_agent._dump_dir.mkdir(parents=True)
                self.evaluator_agent._dump_counter = 0
            package_path = Path(baseline_path) if baseline_path else self.evaluator_agent._dump_dir / "baseline.json"
            loaded_package = None
            if stage == "revise":
                if baseline_path is None:
                    raise ValueError("Revision requires a baseline package")
                loaded_package = load_baseline(package_path)
                if self.integration_threshold != loaded_package["config"]["integration_threshold"]:
                    raise ValueError("Revision must use the baseline integration threshold")
                documents = loaded_package["documents"]
                raw_text = [d["raw_text"] for d in documents]
            else:
                if package_path.exists():
                    raise FileExistsError(f"Baseline already exists: {package_path}")
                raw_text = self._load_document(source)
                texts = raw_text if isinstance(raw_text, list) else [raw_text]
                ids = [str(i) for i in range(len(texts))]
                sentence_lists = {}
                source_path = Path(source)
                if source_path.is_file() and source_path.suffix.lower() == ".json":
                    source_data = json.loads(source_path.read_text(encoding="utf-8"))
                    ids = [str(k) for k, v in source_data.items() if isinstance(v, list)]
                    sentence_lists = {str(k): v for k, v in source_data.items() if isinstance(v, list)}
                documents = [{"doc_id": key, "source_index": i, "raw_text": text,
                              "raw_sentences": sentence_lists.get(key)}
                             for i, (key, text) in enumerate(zip(ids, texts))]
            documents = select_documents(documents, doc_ids, limit)
            intermediate.raw_text = raw_text
            baseline_documents = []
            run_config = self._run_configuration(domain, relevance_threshold)
            manifest = {"format": "karma_run", "version": 1, "stage": stage,
                        "complete": False, "config": run_config, "documents": [],
                        "baseline_config": loaded_package["config"] if loaded_package else run_config,
                        "baseline_sha256": loaded_package["sha256"] if loaded_package else None}
            manifest_path = self.evaluator_agent._dump_dir / "_run_manifest.json"
            # Do not mix two invocations in the same output directory.
            if manifest_path.exists():
                raise FileExistsError(f"Run output already exists: {manifest_path.parent}")
            write_json(manifest_path, manifest)
            self._log("Starting KARMA pipeline...")
            for document in documents:
                i, document_text = document["source_index"], document["raw_text"]
                diff = {}
                conflict_context = (
                    [KnowledgeTriple.from_dict(x) for x in document["conflict_context"]]
                    if stage == "revise" else copy.deepcopy(self.knowledge_graph.triples)
                )
                conflict_context = fixed_score_copy(conflict_context)
                run_document = {"doc_id": document["doc_id"], "source_index": i, "rounds": {}}
                intermediate.split_triples = []
                manifest["documents"].append(run_document)
                print('--------------------------------------------------------------------------')
                print("carrying out knowledge extraction for the article "+str(i))
                if stage == "revise":
                    preparation = document["preparation"]
                    intermediate.metadata = DocumentMetadata(**preparation["metadata"]) if preparation["metadata"] else None
                    intermediate.segments = copy.deepcopy(preparation["segments"])
                    intermediate.relevant_segments = copy.deepcopy(preparation["relevant_segments"])
                    intermediate.summaries = list(preparation["summaries"])
                    summaries = intermediate.summaries
                    extraction_text = document["extraction_text"]
                    intermediate.initial_relationships = [KnowledgeTriple.from_dict(x) for x in document["initial_relationships"]]
                else:
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
                saved_sentences = document.get('source_sentences')
                supplied = ([s['text'] for s in saved_sentences] if saved_sentences is not None
                            else document.get('raw_sentences'))
                if supplied is not None and ' '.join(' '.join(supplied).split()) != ' '.join(extraction_text.split()):
                    if saved_sentences is not None:
                        raise ValueError('Saved sentence boundaries do not match extraction text')
                    supplied = None  # Summarization/normalization changed the text.
                sentences = source_sentences(extraction_text, supplied)
                if saved_sentences is not None and sentences != saved_sentences:
                    raise ValueError('Invalid saved source sentence IDs')
                run_document['source_sentences'] = sentences
                # Round 2 starts with one split-only call.
                # General feedback always reviews the split collection.
                initial_entities = ([KGEntity.from_dict(x) for x in document["initial_entities"]]
                                    if stage == "revise" else [])
                baseline_triples = ([KnowledgeTriple.from_dict(x) for x in document["baseline_triples"]]
                                    if stage == "revise" else [])
                if stage == "revise":
                    baseline_triples = fixed_score_copy(baseline_triples)
                    for triple in baseline_triples:
                        attach_sources(triple, sentences)
                    intermediate.initial_entities = copy.deepcopy(initial_entities)
                    intermediate.baseline_triples = copy.deepcopy(baseline_triples)
                    run_document["rounds"]["1"] = [x.to_dict() for x in baseline_triples]
                rounds = (0,) if stage == "baseline" else (1,) if stage == "revise" else (0, 1)
                for t in rounds:
                    if t == 1:
                        self._log("[split] Running Triple Splitting Agent...")
                        step_start = time.time()
                        split_triples = self.triple_splitting_agent.process(
                            extraction_text, copy.deepcopy(baseline_triples)
                        )
                        intermediate.split_triples = copy.deepcopy(split_triples)
                        run_document["stages"] = {
                            "after_split": [x.to_dict() for x in split_triples]
                        }
                        write_json(self.evaluator_agent._dump_dir / f"_dump_doc{i}_splitting.json", {
                            "agent": "TripleSplittingAgent",
                            "input": [x.to_dict() for x in baseline_triples],
                            "audit": self.triple_splitting_agent.last_revision,
                            "output": [x.to_dict() for x in split_triples],
                        })
                        intermediate.metrics.add_agent_time("triple_splitting", time.time() - step_start)
                    if t == 1:
                        self._log("[7.5/8] Running Text Generation Agent...")
                        step_start = time.time()
                        sentence_groups = group_triples(sentences, split_triples)
                        text_generation = self.text_generation_agent.process(
                            copy.deepcopy(split_triples), sentence_groups=sentence_groups, scope=self.text_scope
                        )
                        if self.text_scope == 'sentence':
                            for record in self.text_generation_agent.last_sentence_calls:
                                write_json(self.evaluator_agent._dump_dir / f"_dump_doc{i}_generation_{record['sentence_id']}.json", record)
                        print(text_generation)
                        step_time = time.time() - step_start
                        intermediate.metrics.add_agent_time("text_generation", step_time)
                        self._log(
                            f"[7.5/8] Text generation completed in {step_time:.2f}s."
                        )

                        self._log("[9/8] Running Comparison Agent...")
                        step_start = time.time()
                        diff = self.text_comparison_agent.process(
                            extraction_text, text_generation, sentence_groups=sentence_groups,
                            reconstructions=self.text_generation_agent.last_grouped_generation, scope=self.text_scope
                        )
                        if self.text_scope == 'sentence':
                            for record in self.text_comparison_agent.last_sentence_calls:
                                write_json(self.evaluator_agent._dump_dir / f"_dump_doc{i}_comparison_{record['sentence_id']}.json", record)
                        with open(self.evaluator_agent._dump_dir / f"_dump_doc{i}_feedback.json", "w", encoding="utf-8") as _f:
                            json.dump({"text_a": extraction_text, "text_b": text_generation, "diff": diff,
                                       "source_sentences": sentences, "sentence_groups": sentence_groups,
                                       "reconstructions": self.text_generation_agent.last_grouped_generation},
                                      _f, ensure_ascii=False, indent=2)
                        print(diff)
                        step_time = time.time() - step_start
                        intermediate.metrics.add_agent_time("diff", step_time)
                        self._log(
                            f"[9/8] Comparison completed in {step_time:.2f}s. "
                            f"Split triples: {len(split_triples)}"
                        )
                    # Step 5: Entity Extraction - Identify entities
                    self._log("[4/8] Running Entity Extraction Agent...")
                    step_start = time.time()

                    if t == 0:
                        entities = self.entity_extraction_agent.process(summaries, diff)
                        initial_entities = copy.deepcopy(entities)
                        intermediate.initial_entities = copy.deepcopy(entities)
                    else:
                        entities = self.entity_extraction_agent.revise_entities(
                            extraction_text, initial_entities, split_triples, diff
                        )
                        intermediate.revised_entities = copy.deepcopy(entities)

                    entity_audit = (
                        self.entity_extraction_agent.last_extraction if t == 0
                        else self.entity_extraction_agent.last_revision
                    )
                    with open(self.evaluator_agent._dump_dir / f"_dump_doc{i}_r{t}_entity_audit.json", "w", encoding="utf-8") as _f:
                        json.dump(entity_audit, _f, ensure_ascii=False, indent=2)

                    # dump 中间结果：实体列表
                    _dump_path = self.evaluator_agent._dump_dir / f"_dump_doc{i}_r{t}_entities.json"
                    with open(_dump_path, "w", encoding="utf-8") as _f:
                        json.dump([{"name": e.name, "type": e.entity_type} for e in entities],
                                  _f, ensure_ascii=False, indent=2)

                    step_time = time.time() - step_start
                    intermediate.metrics.add_agent_time("entity_extraction", step_time)
                    self._log(f"[4/8] Entity extraction completed in {step_time:.2f}s. Entities: {len(entities)}")

                    # Step 6: Relationship Extraction - Find relationships
                    self._log("[5/8] Running Relationship Extraction Agent..." if t == 0
                              else "[feedback] Running Add -> Replace -> Remove...")
                    step_start = time.time()

                    if t == 0:
                        relationships = self.relationship_extraction_agent.process(
                            summaries, entities, diff, sentences=sentences
                        )
                        intermediate.initial_relationships = copy.deepcopy(relationships)
                        with open(self.evaluator_agent._dump_dir / f"_dump_doc{i}_r{t}_relationship_audit.json", "w", encoding="utf-8") as _f:
                            json.dump(self.relationship_extraction_agent.last_extraction, _f, ensure_ascii=False, indent=2)
                    else:
                        relationships = self.feedback_pipeline.process(
                            extraction_text, copy.deepcopy(split_triples), diff, entities=entities, sentences=sentences,
                            reconstructions=self.text_generation_agent.last_grouped_generation,
                        )
                        intermediate.after_add = copy.deepcopy(self.feedback_pipeline.snapshots['after_add'])
                        intermediate.after_replace = copy.deepcopy(self.feedback_pipeline.snapshots['after_replace'])
                        for stage_name in ('after_add', 'after_replace'):
                            run_document['stages'][stage_name] = [t.to_dict() for t in getattr(intermediate, stage_name)]
                        for feedback_stage in self.feedback_pipeline.last_revision['stages']:
                            write_json(self.evaluator_agent._dump_dir / f"_dump_doc{i}_feedback_{feedback_stage['pass_id']}.json", feedback_stage)
                    relationships = fixed_score_copy(relationships)
                    intermediate.relationships = relationships

                    # dump 中间结果：关系列表
                    _dump_path = self.evaluator_agent._dump_dir / f"_dump_doc{i}_r{t}_relationships.json"
                    with open(_dump_path, "w", encoding="utf-8") as _f:
                        json.dump([{"head": r.head, "relation": r.relation, "tail": r.tail}
                                  for r in relationships],
                                  _f, ensure_ascii=False, indent=2)

                    if t == 1:
                        # Compatibility audit points to the stage producing after_revision.
                        revision_agent = self.feedback_pipeline
                        _revision_path = (
                            self.evaluator_agent._dump_dir /
                            f"_dump_doc{i}_r{t}_revision.json"
                        )
                        with open(_revision_path, "w", encoding="utf-8") as _f:
                            json.dump(
                                getattr(
                                    revision_agent,
                                    "last_revision",
                                    {"mode": "revision_audit_unavailable"},
                                ),
                                _f,
                                ensure_ascii=False,
                                indent=2,
                            )

                    step_time = time.time() - step_start
                    if t == 0:
                        intermediate.metrics.add_agent_time("relationship_extraction", step_time)
                    else:
                        for name in ('add', 'replace', 'remove'):
                            elapsed = sum(s['elapsed'] for s in self.feedback_pipeline.last_revision['stages'] if s['stage'] == name)
                            intermediate.metrics.add_agent_time('feedback_' + name, elapsed)
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
                        relationships, conflict_context
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
                    run_document["rounds"][str(t + 1)] = [x.to_dict() for x in integrated_triples]
                    if t == 1:
                        revision_result = {
                            "source_sentences": sentences,
                            "sentence_groups_after_split": sentence_groups,
                            "sentence_groups_after_revision": group_triples(sentences, relationships),
                            "sentence_groups_final": group_triples(sentences, integrated_triples),
                            "revision_agent": type(revision_agent).__name__,
                            # 第一轮最终结果：第二轮修改的基础
                            "baseline": [
                                x.to_dict() for x in baseline_triples
                            ],
                            "after_split": [x.to_dict() for x in intermediate.split_triples],
                            "after_add": [x.to_dict() for x in intermediate.after_add],
                            "after_replace": [x.to_dict() for x in intermediate.after_replace],
                            "splitting_audit": self.triple_splitting_agent.last_revision,
                            # Feedback indices refer to this set, not the original baseline.
                            "revision_input": [x.to_dict() for x in (
                                intermediate.split_triples
                            )],
                            # 模型提出的操作，以及程序接受、拒绝的情况
                            "revision_audit": getattr(
                                revision_agent,
                                "last_revision", {}
                            ),
                            # 应用修改并去重后的结果
                            "after_revision": [
                                x.to_dict() for x in relationships
                            ],
                            # 冲突处理后的结果
                            "after_conflict_resolution": [
                                x.to_dict() for x in resolved_relationships
                            ],
                            # 评分过滤后的最终结果
                            "final": [
                                x.to_dict() for x in integrated_triples
                            ],
                        }
                        result_path = (
                            self.evaluator_agent._dump_dir
                            / f"_dump_doc{i}_revision_result.json"
                        )
                        with open(result_path, "w", encoding="utf-8") as f:
                            json.dump(
                                revision_result, f,
                                ensure_ascii=False, indent=2
                            )
                    triples = []
                    for _ti in range(len(integrated_triples)):
                        triple = integrated_triples[_ti].head + ',' + integrated_triples[_ti].relation + ',' + integrated_triples[_ti].tail
                        triples.append(triple)

                    step_time = time.time() - step_start
                    intermediate.metrics.add_agent_time("evaluator", step_time)
                    self._log(f"[8/8] Evaluation completed in {step_time:.2f}s. Integrated: {len(integrated_triples)}")

                    if t == 0:
                        baseline_triples = copy.deepcopy(integrated_triples)
                        intermediate.baseline_triples = copy.deepcopy(baseline_triples)
                        baseline_documents.append({
                            "doc_id": document["doc_id"], "source_index": i,
                            "raw_text": document_text, "extraction_text": extraction_text,
                            "source_sentences": sentences,
                            "initial_entities": [x.to_dict() for x in initial_entities],
                            "initial_relationships": [x.to_dict() for x in intermediate.initial_relationships],
                            "baseline_triples": [x.to_dict() for x in baseline_triples],
                            "conflict_context": [x.to_dict() for x in conflict_context],
                            "preparation": {
                                "metadata": intermediate.metadata.to_dict() if intermediate.metadata else None,
                                "segments": copy.deepcopy(intermediate.segments),
                                "relevant_segments": copy.deepcopy(intermediate.relevant_segments),
                                "summaries": list(summaries),
                            },
                        })

                # Step 10: Update Knowledge Graph
                final_entities = self._entities_from_triples(integrated_triples, entities)
                intermediate.entities = final_entities
                self._update_knowledge_graph(final_entities, integrated_triples)
                with open(self.evaluator_agent._dump_dir / f"_dump_doc{i}_final_entities.json", "w", encoding="utf-8") as _f:
                    json.dump([e.to_dict() for e in final_entities], _f, ensure_ascii=False, indent=2)

                # Finalize metrics
                total_time = time.time() - start_time
                intermediate.metrics.processing_time = total_time

                self._log(f"KARMA pipeline completed in {total_time:.2f}s. Added {len(integrated_triples)} knowledge triples.")

                write_json(manifest_path, manifest)

            if stage != "revise":
                package = save_baseline(package_path, run_config, baseline_documents)
                manifest["baseline_sha256"] = package["sha256"]
            manifest["complete"] = True
            write_json(manifest_path, manifest)
            self.last_run_manifest = manifest
            self.last_baseline_path = package_path
            return intermediate

        except Exception as e:
            intermediate.metrics.error_count += 1
            logger.error(f"Pipeline failed: {str(e)}")
            raise

    def _run_configuration(self, domain, relevance_threshold):
        # Record reproducibility information only; never serialize API credentials.
        agents = (self.entity_extraction_agent, self.relationship_extraction_agent,
                  self.triple_splitting_agent,
                  self.feedback_add_agent, self.feedback_replace_agent, self.feedback_remove_agent,
                  self.text_generation_agent, self.text_comparison_agent,
                  self.conflict_resolution_agent, self.evaluator_agent)
        hashes = {}
        for agent in agents:
            module_path = Path(inspect.getfile(type(agent)))
            hashes[type(agent).__name__] = hashlib.sha256(module_path.read_bytes()).hexdigest()
        from ..agents.triple_revision import TripleRevisionMixin
        shared_path = Path(inspect.getfile(TripleRevisionMixin))
        hashes["TripleRevisionMixin"] = hashlib.sha256(shared_path.read_bytes()).hexdigest()
        grouping_path = Path(inspect.getfile(source_sentences))
        hashes['SentenceGrouping'] = hashlib.sha256(grouping_path.read_bytes()).hexdigest()
        from ..agents import feedback_common, feedback_operations
        from . import triple_scores
        for name, module in (('FeedbackCommon', feedback_common), ('FeedbackOperations', feedback_operations), ('TripleScores', triple_scores)):
            hashes[name] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
        hashes['FeedbackPipeline'] = hashlib.sha256(Path(inspect.getfile(FeedbackPipeline)).read_bytes()).hexdigest()
        from . import base_agent, sentence_feedback_pipeline
        for name, module in [('BaseAgent', base_agent), ('SentenceFeedbackPipeline', sentence_feedback_pipeline)]:
            hashes[name] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
        return {"model": self.model_name, "api_mode": self.api_mode,
                "feedback_scope": self.feedback_scope, "text_scope": self.text_scope,
                "api_retry_policy": "original_chat_retry_unlimited_cap30",
                "integration_threshold": self.integration_threshold,
                "relevance_threshold": relevance_threshold, "domain": domain,
                "use_summarizer": bool(os.environ.get("KARMA_USE_SUMMARIZER")),
                "feedback_grouping": "source_sentence_groups_v1",
                "feedback_flow": "add_replace_remove_v3",
                "triple_score_policy": "fixed_0.8",
                "agent_code_sha256": hashes}

    @staticmethod
    def _entities_from_triples(triples: List[KnowledgeTriple], candidates: List[KGEntity]) -> List[KGEntity]:
        """Create graph nodes from final arguments; reuse metadata only for exact mentions."""
        known = {e.name: e for e in candidates}
        final = {}
        for triple in triples:
            for name in (triple.head, triple.tail):
                if name not in final:
                    final[name] = copy.deepcopy(known[name]) if name in known else KGEntity(entity_id=name, name=name)
        return list(final.values())


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
            ('triple_splitting', self.triple_splitting_agent),
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
