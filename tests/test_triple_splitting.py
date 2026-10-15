"""Offline parity checks against captured pre-migration responses and outputs."""

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
from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KnowledgeTriple, IntermediateOutput
from karma.core.pipeline import KARMAPipeline
from karma.core.run_artifacts import save_baseline
import evaluation_common as ev


class SplittingParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'tests/fixtures/triple_splitting_parity.json').read_text(encoding='utf-8'))

    def test_prompt_operations_scores_and_audit_match_legacy(self):
        for case in self.fixture['cases']:
            with self.subTest(case=case['name']):
                agent = TripleSplittingAgent(None, 'offline')
                baseline = [KnowledgeTriple.from_dict(t) for t in self.fixture['baseline']]
                with patch.object(agent, '_make_llm_call', return_value=(case['response'], 0, 0, 0)) as call:
                    actual = agent.process(self.fixture['source'], baseline)
                call.assert_called_once()
                self.assertEqual(call.call_args.kwargs['temperature'], 0.0)
                prompt = call.call_args.args[0]
                system = call.call_args.kwargs['system_prompt']
                self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), self.fixture['prompt_sha256'])
                self.assertEqual(hashlib.sha256(system.encode()).hexdigest(), self.fixture['system_prompt_sha256'])
                self.assertEqual([t.to_dict() for t in actual], case['expected'])
                self.assertEqual(agent.last_revision, case['audit'])
                self.assertEqual([t.to_dict() for t in baseline], self.fixture['baseline'])

    def test_call_failure_preserves_input(self):
        baseline = [KnowledgeTriple.from_dict(t) for t in self.fixture['baseline']]
        agent = TripleSplittingAgent(None, 'offline')
        with patch.object(agent, '_make_llm_call', side_effect=RuntimeError('offline failure')) as call:
            actual = agent.process(self.fixture['source'], baseline)
        call.assert_called_once()
        self.assertEqual([t.to_dict() for t in actual], self.fixture['baseline'])
        self.assertEqual(agent.last_revision['mode'], 'baseline_fallback')

    def test_pipeline_preserves_split_parity_when_feedback_has_no_edits(self):
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
                for case in self.fixture['cases']:
                    with self.subTest(case=case['name']):
                        pipe = KARMAPipeline('offline', model_name='offline', integration_threshold=.8)
                        pipe.evaluator_agent._dump_dir = Path(case['name'])
                        pipe.evaluator_agent._dump_dir.mkdir()
                        try:
                            # Isolate split parity with explicit no-op feedback; forbid network.
                            with patch.object(BaseAgent, '_make_llm_call', side_effect=AssertionError('Unexpected LLM stage')), \
                                 patch('httpx.Client.send', side_effect=AssertionError('Network forbidden')), \
                                 patch.object(pipe.text_generation_agent, 'process', return_value=source), \
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
                            self.assertEqual([t.to_dict() for t in output.split_triples], case['expected'])
                            actual = [t.to_dict() for t in output.integrated_triples]
                            self.assertEqual(actual, expected)
                            doc = pipe.last_run_manifest['documents'][0]
                            self.assertEqual(doc['rounds']['1'], baseline)
                            self.assertEqual(doc['rounds']['2'], expected)
                            self.assertEqual(doc['stages']['after_split'], case['expected'])
                            samples = lambda triples: [{'doc_id': 'parity', 'gold_key': 'parity', 'gold': gold,
                                                        'rounds': {'R1': baseline, 'R2': triples}}]
                            old_report, _ = ev.evaluate_samples(samples(expected), ['strict', 'lenient'], {})
                            new_report, _ = ev.evaluate_samples(samples(actual), ['strict', 'lenient'], {})
                            self.assertEqual(old_report['metrics'], new_report['metrics'])
                            self.assertEqual(Path('baseline.json').read_bytes(), original)
                            audit = json.loads((pipe.evaluator_agent._dump_dir / '_dump_doc0_revision_result.json').read_text(encoding='utf-8'))
                            self.assertEqual(audit['revision_agent'], 'RelationshipExtractionAgent')
                            self.assertEqual(audit['revision_input'], case['expected'])
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
