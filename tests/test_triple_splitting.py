"""Compact split protocol, inherited scores, and legacy feedback validation."""

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from karma.agents.triple_splitting import TripleSplittingAgent
from karma.agents.triple_revision import TripleRevisionMixin
from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KnowledgeTriple, IntermediateOutput
from karma.core.pipeline import KARMAPipeline
from karma.core.run_artifacts import save_baseline
import evaluation_common as ev


class SplittingParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'tests/fixtures/triple_splitting_parity.json').read_text(encoding='utf-8'))

    def compact_case(self):
        parent, other = copy.deepcopy(self.fixture['baseline'])
        def operation(relation):
            return dict(index=0, head=parent['head'], relation=relation,
                        tail=parent['tail'], reason='split coordinated actions')
        return {
            'name': 'compact_split',
            'response': json.dumps({'add': [operation('may store')],
                                    'remove': [], 'replace': [operation('may read')]}),
            'expected': [
                dict(parent, relation='may read', source='relationship_revision'),
                other,
                dict(parent, relation='may store', source='relationship_revision'),
            ],
        }

    def test_current_prompt_and_legacy_feedback_validation(self):
        for case in self.fixture['cases']:
            with self.subTest(case=case['name']):
                agent = TripleSplittingAgent(None, 'offline')
                baseline = [KnowledgeTriple.from_dict(t) for t in self.fixture['baseline']]
                # Keep the historical fixture as a regression for the shared
                # feedback rules, which still require evidence and model scores.
                legacy_apply = lambda previous, revision, **_: TripleRevisionMixin._apply_revision(
                    agent, previous, revision)
                with patch.object(agent, '_apply_revision', side_effect=legacy_apply), \
                     patch.object(agent, '_make_llm_call', return_value=(case['response'], 0, 0, 0)) as call:
                    actual = agent.process(self.fixture['source'], baseline)
                call.assert_called_once()
                self.assertEqual(call.call_args.kwargs['temperature'], 0.0)
                prompt = call.call_args.args[0]
                system = call.call_args.kwargs['system_prompt']
                # Examples may evolve; captured legacy operations and outputs stay fixed.
                self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), self.fixture['current_prompt_sha256'])
                self.assertEqual(hashlib.sha256(system.encode()).hexdigest(), self.fixture['system_prompt_sha256'])
                self.assertEqual([t.to_dict() for t in actual], case['expected'])
                self.assertEqual(agent.last_revision, case['audit'])
                self.assertEqual([t.to_dict() for t in baseline], self.fixture['baseline'])

    def test_compact_split_inherits_scores_without_evidence(self):
        agent = TripleSplittingAgent(None, 'offline')
        baseline = [KnowledgeTriple.from_dict(t) for t in self.fixture['baseline']]
        case = self.compact_case()
        with patch.object(agent, '_make_llm_call', return_value=(case['response'], 0, 0, 0)) as call:
            actual = agent.process(self.fixture['source'], baseline)
        self.assertEqual([t.to_dict() for t in actual], case['expected'])
        self.assertEqual(agent.last_revision['rejected'], [])
        self.assertEqual(agent.last_revision['score_policy'], 'inherit_from_source_triple')
        for op in ('add', 'replace'):
            entry = agent.last_revision['accepted'][op][0]
            self.assertEqual(entry['score_source_index'], 0)
            self.assertEqual(entry['inherited_scores'], dict(confidence=.9, clarity=.85, relevance=.8))
            self.assertFalse(set(entry) & {'evidence', 'confidence', 'clarity', 'relevance'})
        prompt = call.call_args.args[0]
        for field in ('evidence', 'confidence', 'clarity', 'relevance'):
            self.assertNotIn(field, prompt)
        self.assertEqual([t.to_dict() for t in baseline], self.fixture['baseline'])

    def test_split_parent_indices_and_invalid_operations(self):
        agent = TripleSplittingAgent(None, 'offline')
        baseline = [KnowledgeTriple.from_dict(t) for t in self.fixture['baseline']]
        valid = json.loads(self.compact_case()['response'])['add'][0]
        for index in (None, True, -1, 99):
            with self.subTest(index=index):
                actual, audit = agent._apply_revision(baseline, {
                    'add': [dict(valid, index=index)], 'replace': [], 'remove': [],
                }, split_only=True)
                self.assertEqual(actual, baseline)
                self.assertEqual(audit['rejected'][0]['reason'], 'invalid index')
        # Multiple children may share a parent; they inherit that parent's
        # scores even if an old model response still contains score fields.
        actual, audit = agent._apply_revision(baseline, {
            'add': [dict(valid, confidence=1, clarity=1, relevance=1),
                    dict(valid, relation='may archive')],
            'replace': [], 'remove': [{'index': 1, 'reason': 'unsupported'}],
        }, split_only=True)
        self.assertEqual(len(actual), 4)
        self.assertEqual(len(audit['accepted']['add']), 2)
        self.assertTrue(all(t.clarity == .85 for t in actual[2:]))
        self.assertEqual(audit['rejected'][0]['reason'], 'remove is not allowed during splitting')
        # Distinct source indices must not be confused with output positions.
        actual, audit = agent._apply_revision(baseline, {
            'add': [dict(valid, index=1)], 'replace': [], 'remove': [],
        }, split_only=True)
        self.assertEqual(actual[-1].clarity, .9)
        baseline[0].confidence = .2
        actual, audit = agent._apply_revision(baseline, {
            'add': [dict(valid, confidence=1)], 'replace': [], 'remove': [],
        }, split_only=True)
        self.assertEqual(actual[-1].confidence, .2)
        actual, audit = agent._apply_revision(baseline, {
            'add': [], 'replace': [valid, dict(valid, relation='may read')], 'remove': [],
        }, split_only=True)
        self.assertEqual(actual, baseline)
        self.assertEqual(len(audit['rejected']), 2)
        # Evidence is still required for ordinary relationship feedback.
        actual, audit = agent._apply_revision(baseline, {
            'add': [valid], 'replace': [], 'remove': [],
        })
        self.assertEqual(actual, baseline)
        self.assertEqual(audit['rejected'][0]['reason'], 'missing evidence')

    def test_call_failure_preserves_input(self):
        baseline = [KnowledgeTriple.from_dict(t) for t in self.fixture['baseline']]
        agent = TripleSplittingAgent(None, 'offline')
        with patch.object(agent, '_make_llm_call', side_effect=RuntimeError('offline failure')) as call:
            actual = agent.process(self.fixture['source'], baseline)
        call.assert_called_once()
        self.assertEqual([t.to_dict() for t in actual], self.fixture['baseline'])
        self.assertEqual(agent.last_revision['mode'], 'baseline_fallback')

    def test_pipeline_preserves_split_parity_when_feedback_has_no_edits(self):
        def without_provenance(triples):
            return [{k: v for k, v in t.items() if k not in ('source_sentence_ids', 'evidence')}
                    for t in triples]

        def generate(prompt, **kwargs):
            groups = json.loads(prompt.split('<triple_groups_json>')[1].split('</triple_groups_json>')[0])
            return json.dumps([{'sentence_id': g['sentence_id'], 'text': ' '.join(
                ' '.join(t[k] for k in ('head', 'relation', 'tail')) for t in g['triples'])}
                for g in groups]), 0, 0, 0
        previous_cwd = Path.cwd()
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as directory:
            os.chdir(directory)
            try:
                source = self.fixture['source']
                baseline = copy.deepcopy(self.fixture['baseline'])
                save_baseline(Path('baseline.json'), {'integration_threshold': .8}, [{
                    'doc_id': 'parity', 'source_index': 0, 'raw_text': source,
                    'extraction_text': source, 'initial_entities': [],
                    'initial_relationships': baseline, 'baseline_triples': baseline,
                    'conflict_context': [], 'preparation': {
                        'metadata': None, 'segments': [], 'relevant_segments': [], 'summaries': [source],
                    },
                }])
                original = Path('baseline.json').read_bytes()
                gold = [dict(head='The controller', relation='may read', tail='sensor data'),
                        dict(head='The controller', relation='may store', tail='sensor data')]
                for case in [self.compact_case()]:
                    with self.subTest(case=case['name']):
                        pipe = KARMAPipeline('offline', model_name='offline', integration_threshold=.8)
                        pipe.evaluator_agent._dump_dir = Path(case['name'])
                        pipe.evaluator_agent._dump_dir.mkdir()
                        try:
                            # Isolate split parity with explicit no-op feedback; forbid network.
                            with patch.object(BaseAgent, '_make_llm_call', side_effect=AssertionError('Unexpected LLM stage')), \
                                 patch('httpx.Client.send', side_effect=AssertionError('Network forbidden')), \
                                 patch.object(pipe.text_generation_agent, '_make_llm_call', side_effect=generate), \
                                 patch.object(pipe.text_comparison_agent, 'process', return_value={}), \
                                 patch.object(pipe.entity_extraction_agent, 'revise_entities', return_value=[]), \
                                 patch.object(pipe.relationship_extraction_agent, '_make_llm_call',
                                              return_value=('{"add": [], "remove": [], "replace": []}', 0, 0, 0)) as feedback, \
                                 patch.object(pipe.triple_splitting_agent, '_make_llm_call',
                                              return_value=(case['response'], 0, 0, 0)) as call:
                                output = pipe.process_document('', stage='revise', baseline_path='baseline.json')
                            call.assert_called_once()
                            feedback.assert_called_once()
                            expected = [t for t in case['expected']
                                        if .5 * t['confidence'] + .25 * t['clarity'] + .25 * t['relevance'] >= .8]
                            self.assertEqual(without_provenance([t.to_dict() for t in output.split_triples]), case['expected'])
                            actual = without_provenance([t.to_dict() for t in output.integrated_triples])
                            self.assertEqual(actual, expected)
                            doc = pipe.last_run_manifest['documents'][0]
                            self.assertEqual(without_provenance(doc['rounds']['1']), baseline)
                            self.assertEqual(without_provenance(doc['rounds']['2']), expected)
                            self.assertEqual(without_provenance(doc['stages']['after_split']), case['expected'])
                            samples = lambda triples: [{'doc_id': 'parity', 'gold_key': 'parity', 'gold': gold,
                                                        'rounds': {'R1': baseline, 'R2': triples}}]
                            old_report, _ = ev.evaluate_samples(samples(expected), ['strict', 'lenient'], {})
                            new_report, _ = ev.evaluate_samples(samples(actual), ['strict', 'lenient'], {})
                            self.assertEqual(old_report['metrics'], new_report['metrics'])
                            self.assertEqual(Path('baseline.json').read_bytes(), original)
                            audit = json.loads((pipe.evaluator_agent._dump_dir / '_dump_doc0_revision_result.json').read_text(encoding='utf-8'))
                            self.assertEqual(audit['revision_agent'], 'RelationshipExtractionAgent')
                            self.assertEqual(without_provenance(audit['revision_input']), case['expected'])
                        finally:
                            pipe.client.close()
            finally:
                os.chdir(previous_cwd)

    def test_split_snapshot_serialization(self):
        triples = [KnowledgeTriple.from_dict(t) for t in self.fixture['baseline']]
        output = IntermediateOutput(split_triples=triples)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as directory:
            path = Path(directory) / 'snapshot.json'
            output.save_to_file(str(path))
            loaded = IntermediateOutput.load_from_file(str(path))
        self.assertEqual([t.to_dict() for t in loaded.split_triples], self.fixture['baseline'])


if __name__ == '__main__':
    unittest.main()
