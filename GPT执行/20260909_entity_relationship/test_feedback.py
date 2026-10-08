"""Offline regression tests: run with python -B <this file>. No external requests."""
import contextlib
import io
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from karma.agents.entity_extraction.agent import EntityExtractionAgent
from karma.agents.relationship_extraction.agent import RelationshipExtractionAgent
from karma.agents.extraction_support import parse_json_container, safe_score
from karma.agents.evaluator.agent import EvaluatorAgent
from karma.core.base_agent import BaseAgent
from karma.core.pipeline import KARMAPipeline
from karma.core.data_structures import KGEntity, KnowledgeTriple, IntermediateOutput
import evaluate
import main

logging.disable(logging.CRITICAL)


def response(data):
    return json.dumps(data, ensure_ascii=False), 0, 0, 0.0


def entity(name):
    return KGEntity(entity_id=name, name=name)


def operation(**updates):
    data = dict(head='The controller', relation='may query', tail='the ECU',
                reason='Correct source wording', evidence='The controller may query the ECU.',
                confidence=.9, clarity=.9, relevance=.9)
    data.update(updates)
    return data


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.e = EntityExtractionAgent(None, 'offline')
        self.r = RelationshipExtractionAgent(None, 'offline')

    def test_json_wrappers_and_wrong_root(self):
        for value in ('[]', '```json\n[]\n```', 'Result:\n[]'):
            self.assertEqual(parse_json_container(value, list), [])
        for value in ('{"entities": []}', 'broken [', '[] {}', 'null'):
            with self.assertRaises(ValueError):
                parse_json_container(value, list)
        with self.assertRaises(ValueError):
            self.r._parse_revision_response('{}')

    def test_relationship_without_entity_gate(self):
        for candidates in ([], [entity('unrelated')]):
            with patch.object(self.r, '_make_llm_call', return_value=response([operation()])) as llm:
                triples = self.r.process(['The controller may query the ECU.'], candidates)
            self.assertEqual(len(triples), 1)
            llm.assert_called_once()

    def test_per_item_parsing_and_scores(self):
        rows = [operation(confidence='bad'), operation(head='Other', clarity=0),
                operation(tail=None), 9, operation(head=['bad'])]
        with patch.object(self.r, '_make_llm_call', return_value=response(rows)):
            triples = self.r.process(['Text'], [])
        self.assertEqual(len(triples), 2)
        self.assertEqual(triples[0].confidence, .5)
        self.assertEqual(triples[1].clarity, 0)
        self.assertEqual(len(self.r.last_extraction[0]['rejected']), 3)
        for value in (True, None, float('nan'), float('inf'), 'bad'):
            self.assertEqual(safe_score(value), .5)

    def test_first_round_parse_failure_is_distinct_from_empty(self):
        for reply, mode in [('[]', 'extraction'), ('not JSON', 'extraction_failure')]:
            with patch.object(self.r, '_make_llm_call', return_value=(reply, 0, 0, 0)):
                self.assertEqual(self.r.process(['Text'], []), [])
            self.assertEqual(self.r.last_extraction[0]['mode'], mode)

    def test_entity_revision_replaces_instead_of_union(self):
        old = [entity('old name'), entity('phantom')]
        with patch.object(self.e, '_make_llm_call', return_value=response([
            {'mention': 'The controller', 'type': 'Component', 'context': 'source'}
        ])) as llm:
            new = self.e.revise_entities('source', old, [], {})
        self.assertEqual([e.name for e in new], ['The controller'])
        self.assertEqual([e.name for e in old], ['old name', 'phantom'])
        self.assertIn('current_entities_json', llm.call_args.args[0])

    def test_entity_fallback_and_valid_empty(self):
        old = [entity('old')]
        for reply in ('not JSON', '{"entities": []}', '[{"mention":"valid"},null]'):
            with patch.object(self.e, '_make_llm_call', return_value=(reply, 0, 0, 0)):
                new = self.e.revise_entities('source', old, [], {})
            self.assertEqual(new, old)
            self.assertIsNot(new[0], old[0])
            self.assertEqual(self.e.last_revision['mode'], 'baseline_fallback')
        with patch.object(self.e, '_make_llm_call', return_value=response([])):
            self.assertEqual(self.e.revise_entities('source', old, [], {}), [])
        with patch.object(self.e, '_make_llm_call', side_effect=RuntimeError('offline failure')):
            self.assertEqual(self.e.process(['source']), [])

    def test_entity_mentions_preserve_boundaries_and_case(self):
        rows = [{'mention': name} for name in ['ECU', 'the ECU', 'ecu', 'ECU']]
        parsed, _, _ = self.e._parse_entities(json.dumps(rows))
        self.assertEqual([e.name for e in parsed], ['ECU', 'the ECU', 'ecu'])

    def test_incremental_ops_and_evidence_without_matching(self):
        baseline = [KnowledgeTriple('old', 'controls', 'ECU'),
                    KnowledgeTriple('phantom', 'stores', 'data'),
                    KnowledgeTriple('keep', 'is', 'valid')]
        patch_data = {'add': [operation(head='new', evidence='format does not match source')],
                      'remove': [{'index': 1, 'reason': 'unsupported'}],
                      'replace': [operation(index=0)]}
        with patch.object(self.r, '_make_llm_call', return_value=response(patch_data)) as llm:
            result = self.r.revise_relationships('source', baseline, {}, entities=[entity('reviewed')])
        self.assertEqual([t.head for t in result], ['The controller', 'keep', 'new'])
        self.assertEqual(baseline[0].head, 'old')
        self.assertIn('reviewed', llm.call_args.args[0])

    def test_conflicting_operations_preserve_original(self):
        original = KnowledgeTriple('keep', 'is', 'valid')
        for removes, replaces in [([{'index': 0, 'reason': 'x'}], [operation(index=0)]),
                                   ([], [operation(index=0), operation(index=0, head='different')])]:
            result, audit = self.r._apply_revision([original], {'add': [], 'remove': removes, 'replace': replaces})
            self.assertEqual(result, [original])
            self.assertEqual(len(audit['rejected']), 2)

    def test_strict_indices_and_invalid_fields(self):
        base = [KnowledgeTriple('a', 'is', 'b')]
        for index in (True, False, 0.2, 0.0, -1, '0.2', None, 5):
            self.assertIsNone(self.r._valid_revision_index(index, base))
        self.assertEqual(self.r._valid_revision_index('0', base), 0)
        for item in (operation(evidence=None), operation(reason=[]), operation(tail=None)):
            result, audit = self.r._apply_revision([], {'add':[item], 'remove':[], 'replace':[]})
            self.assertEqual(result, [])
            self.assertEqual(len(audit['rejected']), 1)

    def test_revision_failure_keeps_baseline_and_empty_can_add(self):
        base = [KnowledgeTriple('a', 'is', 'b')]
        with patch.object(self.r, '_make_llm_call', return_value=('[]', 0, 0, 0)):
            self.assertEqual(self.r.revise_relationships('source', base, {}), base)
        with patch.object(self.r, '_make_llm_call', return_value=response({'add':[operation()], 'remove':[], 'replace':[]})):
            self.assertEqual(len(self.r.revise_relationships('source', [], {}, [])), 1)

    def test_legacy_entry_points(self):
        with patch.object(self.e, '_make_llm_call', return_value=response([{'mention':'X'}])):
            self.assertEqual(len(self.e.extract_entities('source')[0]), 1)
        with patch.object(self.r, '_make_llm_call', return_value=response([operation()])):
            self.assertEqual(len(self.r.extract_relationships('source', [entity('X')])[0]), 1)

    def test_final_entities_and_serialization(self):
        nodes = KARMAPipeline._entities_from_triples([KnowledgeTriple('actual', 'is', 'new')],
                                                    [entity('actual'), entity('phantom')])
        self.assertEqual([e.name for e in nodes], ['actual', 'new'])
        data = IntermediateOutput(entities=nodes, initial_entities=[entity('old')],
                                  revised_entities=[entity('actual')], baseline_triples=[KnowledgeTriple('a','r','b')])
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            path = Path(temp) / 'roundtrip.json'
            data.save_to_file(path)
            loaded = IntermediateOutput.load_from_file(path)
            self.assertEqual(loaded, data)

    def test_full_pipeline_two_documents_both_api_modes(self):
        for mode in ('chat_completions', 'responses'):
            self._run_pipeline(mode)

    def _run_pipeline(self, mode):
        calls = []
        texts = ['The controller may query the ECU. The sensor monitors the road.',
                 'The controller may query the ECU. The sensor monitors the road. Additional text.']
        def fake_call(agent, prompt, **kwargs):
            self.assertEqual(agent.api_mode, mode)
            kind = type(agent).__name__
            calls.append(kind)
            if kind == 'ReaderAgent':
                return '0.9\n' * 10, 0, 0, 0
            if kind == 'EntityExtractionAgent':
                if '# 当前三元组' in prompt:
                    self.assertIn('old phantom', prompt)
                    return response([{'mention': x} for x in ['The controller','the ECU','The sensor','the road']])
                return response([{'mention': x} for x in ['The controller','the ECU','old phantom']])
            if kind == 'RelationshipExtractionAgent':
                if kwargs.get('system_prompt'):
                    candidates = prompt.split('<candidate_entities_json>')[1].split('</candidate_entities_json>')[0]
                    self.assertIn('The sensor', candidates)
                    self.assertNotIn('old phantom', candidates)
                    return response({'replace':[operation(index=0)],
                                     'remove':[{'index':1, 'reason':'unsupported'}],
                                     'add':[operation(head='The sensor', relation='monitors', tail='the road')]})
                self.assertNotIn('text_difference_json', prompt)
                return response([operation(relation='controls'),
                                 operation(head='the ECU', relation='stores', tail='old phantom'),
                                 operation(head='weak', confidence=.1, clarity=.1, relevance=.1)])
            if kind == 'TextGenerationAgent':
                self.assertNotIn('weak', prompt)
                return 'The controller controls the ECU. The ECU stores old phantom.', 0, 0, 0
            if kind == 'TextComparisonAgent':
                return response({'unique_to_text_a':['The sensor monitors the road.'],
                                 'unique_to_text_b':['The ECU stores old phantom.']})
            raise AssertionError('Unexpected LLM: '+kind)

        previous_cwd = Path.cwd()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            try:
                os.chdir(temp)
                input_path = Path('input.json')
                input_path.write_text(json.dumps({str(i):[t] for i,t in enumerate(texts)}), encoding='utf-8')
                with patch.dict(os.environ, {'KARMA_USE_SUMMARIZER':''}), \
                     patch.object(BaseAgent, '_make_llm_call', new=fake_call), \
                     patch('httpx.Client.send', side_effect=AssertionError('Unexpected network')), \
                     contextlib.redirect_stdout(io.StringIO()):
                    pipe = KARMAPipeline(api_key='offline-test', model_name='offline', integration_threshold=.6, api_mode=mode)
                    out = pipe.process_document(input_path)
                    self.assertNotIn('schema_alignment', pipe.get_pipeline_statistics()['agents'])
                    docs, files = evaluate.load_extracted(pipe.evaluator_agent._dump_dir)
                    self.assertEqual(len(files), 4)
                    self.assertEqual([len(d) for d in docs], [2,2,2,2])
                    self.assertEqual(docs[1], docs[3])
                    self.assertEqual(len(pipe.knowledge_graph.triples), 4)
                    self.assertNotIn('old phantom', pipe.knowledge_graph.entities)
                    self.assertEqual(out.baseline_triples[0].relation, 'controls')
                    self.assertEqual(out.integrated_triples[0].relation, 'may query')
                    self.assertEqual(len(out.initial_entities), 3)
                    self.assertEqual(len(out.revised_entities), 4)
                    self.assertEqual(len(out.entities), 4)
                    self.assertEqual(main.save_relationships_to_csv(out, Path('out.csv'), .6), 2)
                    pipe.export_knowledge_graph('graph.json')
                    out.save_to_file('intermediate.json')
                    self.assertEqual(IntermediateOutput.load_from_file('intermediate.json'), out)
                    self.assertEqual(calls.count('EntityExtractionAgent'), 4)
                    self.assertEqual(calls.count('RelationshipExtractionAgent'), 4)
                    self.assertEqual(calls.count('TextComparisonAgent'), 2)
                    pipe.client.close()

                    # Exercise the actual CLI/config/export path on a fresh pipeline.
                    argv = ['main.py', '--input', str(input_path), '--api-key', 'offline-test',
                            '--output-dir', 'cli-output', '--model', 'offline', '--integration-threshold', '.6']
                    api_env = {'KARMA_BASE_URL': 'https://example.invalid/v1',
                               'KARMA_PROXY_BASE_URL': 'https://example.invalid/v1',
                               'KARMA_PROXY_MODEL': 'offline', 'KARMA_PROXY_API_KEY': 'offline-test'}
                    with patch.object(main, 'API_MODE', 0 if mode == 'chat_completions' else 1), \
                         patch.dict(os.environ, api_env), patch.object(sys, 'argv', argv):
                        self.assertEqual(main.main(), 0)
                    self.assertTrue(list(Path('cli-output').glob('knowledge_graph_*.json')))
                    self.assertTrue(list(Path('cli-output').glob('intermediate_results_*.json')))
            finally:
                os.chdir(previous_cwd)

    def test_evaluator_zero_scores_and_empty_dump(self):
        previous_cwd = Path.cwd()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            try:
                os.chdir(temp)
                evaluator = EvaluatorAgent(None, 'offline', integrate_threshold=.6)
                weak = KnowledgeTriple('a','r','b',confidence=0,clarity=0,relevance=0)
                self.assertEqual(evaluator.process([weak]), [])
                self.assertEqual(weak.confidence, 0)
                evaluator.process([])
                docs, files = evaluate.load_extracted(evaluator._dump_dir)
                self.assertEqual(docs, [[], []])
                self.assertEqual(len(files), 2)
            finally:
                os.chdir(previous_cwd)


if __name__ == '__main__':
    unittest.main(verbosity=2)
