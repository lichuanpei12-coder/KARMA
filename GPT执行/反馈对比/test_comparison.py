"""Offline integration tests: actual agents and transport, mocked HTTP only."""
import copy
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from compare_feedback import (ROOT, HERE, Experiment, RecordedCalls, load_documents,
                              prepare, read, run, save, sha, evaluate_run)

CONFIG = {'api_mode': 'chat_completions', 'model': 'offline-model',
          'base_url': 'https://offline.invalid/v1', 'max_retries': 1, 'timeout': 1}


def triple(head, relation='contains', tail='data'):
    return {'head': head, 'relation': relation, 'tail': tail,
            'confidence': 0.9, 'clarity': 0.8, 'relevance': 0.7}


def completion(content, finish='stop'):
    return httpx.Response(200, json={'model': 'returned-offline-model',
        'choices': [{'message': {'content': content}, 'finish_reason': finish}]})


class FakeClient:
    def __init__(self, respond):
        self.respond = respond

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, url, **kwargs):
        return self.respond(url, **kwargs)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        # Never put test artifacts outside the user-designated process folder.
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.root = Path(self.temp.name)
        self.network = patch.object(socket.socket, 'connect', side_effect=AssertionError('Network forbidden'))
        self.network.start()

    def tearDown(self):
        self.network.stop()
        self.temp.cleanup()

    def caller(self, respond, config=None):
        return RecordedCalls(self.root, config or CONFIG, 'secret-test-key',
                             client_factory=lambda **kw: FakeClient(respond), sleep=lambda _: None)

    def synthetic_response(self, caller, seen):
        def respond(url, **kwargs):
            stage = caller.stage
            payload = kwargs['json']
            seen.append((stage, copy.deepcopy(payload)))
            if stage.endswith('/entity'):
                name = ('E2-reextract' if '/reextract/' in stage else
                        'E2-incremental' if '/incremental/' in stage else 'E1-shared')
                body = [{'mention': name, 'type': 'Object', 'context': 'source'}]
            elif stage.endswith('/relationship'):
                if '/incremental/' in stage:
                    body = {'add': [{**triple('E2-incremental'), 'evidence': 'source', 'reason': 'addition'}],
                            'remove': [{'index': 1, 'reason': 'unsupported'}],
                            'replace': [{'index': 0, **triple('corrected'), 'evidence': 'source', 'reason': 'repair'}]}
                elif '/reextract/' in stage:
                    body = [triple('E2-reextract')]
                else:
                    body = [triple('T1-a'), triple('T1-b'), triple('T1-c')]
            elif stage.endswith('/text_generation'):
                return completion('Generated text B from T1.')
            elif stage.endswith('/text_comparison'):
                body = {'unique_to_text_a': ['a missing fact'], 'unique_to_text_b': []}
            else:
                raise AssertionError(stage)
            return completion(json.dumps(body))
        return respond

    def test_shared_round_one_and_independent_entities(self):
        caller = self.caller(lambda *a, **k: None)
        seen = []
        caller.client_factory = lambda **kw: FakeClient(self.synthetic_response(caller, seen))
        experiment = Experiment(self.root, CONFIG, caller)
        result = experiment.run_document({'doc_id': 0, 'title': 'test', 'sentences': ['Source.'], 'raw_text': 'Source.'})
        self.assertTrue(result['paired_usable'])
        self.assertEqual(len(seen), 8)
        self.assertEqual(sum('/shared/entity' in s for s, _ in seen), 1)
        by_stage = {s: p['messages'][1]['content'] for s, p in seen}
        self.assertIn('E2-reextract', by_stage['documents/doc_000/reextract/relationship'])
        self.assertNotIn('E2-incremental', by_stage['documents/doc_000/reextract/relationship'])
        self.assertIn('E2-incremental', by_stage['documents/doc_000/incremental/relationship'])
        self.assertIn('E1-shared', by_stage['documents/doc_000/incremental/entity'])
        self.assertIn('T1-a', by_stage['documents/doc_000/incremental/entity'])
        self.assertNotIn('E1-shared', by_stage['documents/doc_000/reextract/entity'])
        self.assertNotIn('T1-a', by_stage['documents/doc_000/reextract/entity'])
        baseline = read(self.root / result['baseline'])
        self.assertEqual([t['head'] for t in baseline['T1']], ['T1-a', 'T1-b', 'T1-c'])
        final = read(self.root / result['branches']['incremental']['T2'])
        self.assertEqual([t['head'] for t in final], ['corrected', 'T1-c', 'E2-incremental'])
        for method in ('reextract', 'incremental'):
            info = read(self.root / f'documents/doc_000/{method}/input.json')
            self.assertEqual(info['shared_sha256'], result['shared_sha256'])
        self.assertEqual(caller.records[0]['returned_model'], 'returned-offline-model')
        self.assertIsNone(caller.records[0]['prompt_tokens'])
        for path in self.root.rglob('*.json'):
            self.assertNotIn('secret-test-key', path.read_text(encoding='utf-8'))

    def test_retry_attempts_and_null_usage(self):
        responses = iter([httpx.Response(429, headers={'Retry-After': '0'}, text='retry'), completion('[]')])
        caller = self.caller(lambda *a, **kw: next(responses))
        from karma.agents import EntityExtractionAgent
        agent = caller.bind(EntityExtractionAgent(None, 'offline-model'))
        self.assertEqual(agent.process(['text'], {}), [])
        self.assertEqual(len(caller.records[0]['attempts']), 2)
        self.assertEqual(caller.records[0]['status'], 'success')
        self.assertEqual(caller.records[0]['attempts'][0]['http_status'], 429)

    def test_malformed_response_and_auth_stop(self):
        from karma.agents import EntityExtractionAgent
        for response in (httpx.Response(200, text='not JSON'), httpx.Response(200, json={'choices': []})):
            caller = self.caller(lambda *a, **kw: response)
            caller.bind(EntityExtractionAgent(None, 'offline-model')).process(['text'], {})
            self.assertNotEqual(caller.records[0]['status'], 'success')
        caller = self.caller(lambda *a, **kw: httpx.Response(401, text='Unauthorized'))
        experiment = Experiment(self.root, CONFIG, caller)
        with self.assertRaises(PermissionError):
            experiment.run_document({'doc_id': 0, 'title': 'x', 'raw_text': 'text', 'sentences': ['text']})
        self.assertEqual(len(caller.records), 1)

    def test_entity_fallback_is_not_success(self):
        from karma.agents import EntityExtractionAgent
        from karma.core.data_structures import KGEntity
        caller = self.caller(lambda *a, **kw: completion('not JSON'))
        experiment = Experiment(self.root, CONFIG, caller)
        agent = experiment.agent(EntityExtractionAgent)
        old = [KGEntity('a', name='a')]
        e2 = experiment.stage('entity', lambda: agent.revise_entities('text', old, [], {}),
                              lambda: agent.last_revision)
        self.assertEqual(e2[0].name, 'a')
        self.assertIsNot(e2[0], old[0])
        self.assertEqual(experiment.statuses['entity']['status'], 'fallback_or_parse_failure')

    def test_truncated_response_saved_and_flagged(self):
        from karma.agents import EntityExtractionAgent
        caller = self.caller(lambda *a, **kw: completion('[]', 'length'))
        agent = caller.bind(EntityExtractionAgent(None, 'offline-model'))
        self.assertEqual(agent.process(['text'], {}), [])
        self.assertEqual(caller.records[0]['status'], 'truncated')
        self.assertEqual(caller.records[0]['content'], '[]')

    def test_responses_mode_http_path_and_body(self):
        from karma.agents import EntityExtractionAgent
        def respond(url, **kwargs):
            self.assertTrue(url.endswith('/responses'))
            self.assertIn('instructions', kwargs['json'])
            self.assertFalse(kwargs['json']['store'])
            return httpx.Response(200, json={'status': 'completed', 'model': 'response-model',
                'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '[]'}]}]})
        caller = self.caller(respond, {**CONFIG, 'api_mode': 'responses'})
        agent = caller.bind(EntityExtractionAgent(None, 'offline-model'))
        self.assertEqual(agent.process(['source'], {}), [])
        self.assertEqual(caller.records[0]['status'], 'success')

    def test_original_doc_ids_and_dry_run(self):
        source = ROOT / 'data/DocIOE/DocOIE_transportation_gold_input.json'
        docs = load_documents(source, '0,8,16,24,32,39')
        self.assertEqual([d['doc_id'] for d in docs], [0, 8, 16, 24, 32, 39])
        out = self.root / 'dry'
        manifest = prepare(out, docs, source, ROOT / 'data/DocIOE/transport', CONFIG, False, True)
        self.assertEqual(manifest['documents'][1]['gold_path'], str(ROOT / 'data/DocIOE/transport/8.json'))
        self.assertEqual(sha(out / 'gold/doc_008.json'), sha(ROOT / 'data/DocIOE/transport/8.json'))
        self.assertEqual(manifest['status'], 'dry_run')
        self.assertFalse(list(out.rglob('call_*.json')))

    def test_full_run_and_frozen_evaluation_alignment(self):
        source = ROOT / 'data/DocIOE/DocOIE_transportation_gold_input.json'
        docs = load_documents(source, '0,8')
        out = self.root / 'run'
        manifest = prepare(out, docs, source, ROOT / 'data/DocIOE/transport', CONFIG, False, False)
        caller = RecordedCalls(out, CONFIG, 'secret-test-key', sleep=lambda _: None)
        seen = []
        caller.client_factory = lambda **kw: FakeClient(self.synthetic_response(caller, seen))
        result = run(out, docs, manifest, caller)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['call_count'], 16)
        self.assertEqual(result['results'][1]['branch_order'], ['incremental', 'reextract'])
        # A partial rejection must not remove this document's final output from
        # the primary comparison, but must exclude it from the clean subset.
        result['results'][1]['paired_usable'] = False
        result['results'][1]['branches']['incremental']['status'] = 'needs_review'
        result['results'][1]['branches']['incremental']['relationship_status'] = 'partial_rejected'
        save(out / 'manifest.json', result)
        manifest_before_evaluation = sha(out / 'manifest.json')
        # Exercise the real frozen scoring/matrix functions; only embeddings are mocked.
        import importlib.util
        import numpy as np
        original = importlib.util.module_from_spec
        def module_from_spec(spec):
            module = original(spec)
            loader_exec = spec.loader.exec_module
            def execute(m):
                loader_exec(m)
                def embeddings(golds, preds):
                    for docs_ in (golds, preds):
                        for triples in docs_:
                            for t in triples:
                                for fn in (m._serialize_triple, m._serialize_entity):
                                    m._embed_cache[fn(t)] = np.ones(1024, dtype=np.float32) / 32
                m.precompute_embeddings = embeddings
            spec.loader.exec_module = execute
            return module
        with patch('importlib.util.module_from_spec', side_effect=module_from_spec):
            evaluate_run(out)
        report = read(next((out / 'evaluation').rglob('comparison.json')))
        self.assertEqual(report['included_doc_ids'], [0, 8])
        self.assertEqual(report['clean_pairs']['included_doc_ids'], [0])
        self.assertEqual(report['clean_pairs']['excluded_doc_ids'], [8])
        self.assertEqual(report['results']['incremental']['totals']['num_gold'], 65)
        self.assertEqual(report['clean_pairs']['results']['incremental']['totals']['num_gold'], 35)
        self.assertEqual(sha(out / 'manifest.json'), manifest_before_evaluation)
        self.assertEqual([d['doc'] for d in report['results']['incremental']['per_doc']], [0, 8])
        self.assertEqual(len(list((out / 'evaluation').rglob('*_matrix.npz'))), 6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
