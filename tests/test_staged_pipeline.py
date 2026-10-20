"""Offline stage handoff/CLI/evaluation regression tests; no external API calls."""

import contextlib
import copy
import io
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from karma.core.pipeline import KARMAPipeline
from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KnowledgeTriple
from karma.core.run_artifacts import load_baseline, fingerprint
import main
import evaluate

logging.disable(logging.CRITICAL)


def reply(data):
    return json.dumps(data), 0, 0, 0.0


def fact(relation='controls', **fields):
    return dict(head='Controller', relation=relation, tail='ECU', confidence=.9,
                clarity=.9, relevance=.9, **fields)


class StagedPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.old_cwd = Path.cwd()
        os.chdir(self.tmp.name)
        self.source = Path('input.json')
        self.source.write_text(json.dumps({'alpha': ['Controller may query ECU.'],
                                           'empty': ['EMPTY'],
                                           'omega': ['Controller may query ECU. Again.']}), encoding='utf-8')
        self.calls = []
        self.pipes = []
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(patch.dict(os.environ, {'KARMA_USE_SUMMARIZER': ''}))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(patch('httpx.Client.send', side_effect=AssertionError('Network forbidden')))
        calls = self.calls

        def fake_call(agent, prompt, **kwargs):
            name = type(agent).__name__
            calls.append((name, prompt, kwargs))
            empty = 'EMPTY' in prompt
            if name == 'ReaderAgent':
                return '0.9\n' * 10, 0, 0, 0
            if name == 'EntityExtractionAgent':
                return reply([] if empty else [{'mention': 'Controller'}, {'mention': 'ECU'}])
            if name == 'RelationshipExtractionAgent':
                if kwargs.get('system_prompt'):
                    return reply({'add': [], 'remove': [], 'replace': [] if empty else [
                        fact('may query', index=0, evidence='Controller may query ECU.', reason='source wording')]})
                return reply([] if empty else [fact()])
            if name == 'TripleSplittingAgent':
                return reply({'add': [], 'remove': [], 'replace': [] if empty else [
                    dict(head='Controller', relation='may query', tail='ECU',
                         index=0, reason='source wording')]})
            if name == 'TextGenerationAgent':
                return 'Controller controls ECU.', 0, 0, 0
            if name == 'TextComparisonAgent':
                return reply({'unique_to_text_a': [], 'unique_to_text_b': []})
            raise AssertionError(name)

        self.stack.enter_context(patch.object(BaseAgent, '_make_llm_call', new=fake_call))

    def tearDown(self):
        for pipe in self.pipes:
            pipe.client.close()
        self.stack.close()
        os.chdir(self.old_cwd)
        self.tmp.cleanup()

    def pipeline(self, name, mode='chat_completions'):
        pipe = KARMAPipeline('offline', model_name='offline', integration_threshold=.6, api_mode=mode)
        pipe.evaluator_agent._dump_dir = Path(name)
        Path(name).mkdir()
        self.pipes.append(pipe)
        return pipe

    def test_baseline_stops_before_feedback_and_preserves_ids_and_scores(self):
        pipe = self.pipeline('base')
        pipe.process_document(self.source, stage='baseline', doc_ids=['omega', 'empty'])
        package = load_baseline(pipe.last_baseline_path)
        self.assertEqual([d['doc_id'] for d in package['documents']], ['empty', 'omega'])
        self.assertEqual([d['source_index'] for d in package['documents']], [1, 2])
        self.assertEqual(package['documents'][0]['baseline_triples'], [])
        self.assertEqual(package['documents'][1]['baseline_triples'][0]['confidence'], .9)
        self.assertNotIn('TextGenerationAgent', [c[0] for c in self.calls])
        self.assertNotIn('TextComparisonAgent', [c[0] for c in self.calls])
        self.assertNotIn('TripleSplittingAgent', [c[0] for c in self.calls])
        self.assertEqual(set(pipe.last_run_manifest['documents'][0]['rounds']), {'1'})

    def test_split_equals_full_with_fixed_responses_and_replay_is_immutable(self):
        for mode in ('chat_completions', 'responses'):
            full = self.pipeline('full_' + mode, mode)
            full.process_document(self.source)
            base = self.pipeline('base_' + mode, mode)
            base.process_document(self.source, stage='baseline')
            baseline_bytes = base.last_baseline_path.read_bytes()
            # Resume works without the original input file or an extraction call.
            self.source.rename('hidden.json')
            for n in range(2):
                self.calls.clear()
                resumed = self.pipeline(f'resume_{mode}_{n}', mode)
                resumed.process_document('missing.json', stage='revise', baseline_path=base.last_baseline_path)
                self.assertEqual(resumed.last_run_manifest['documents'], full.last_run_manifest['documents'])
                self.assertNotIn('ReaderAgent', [c[0] for c in self.calls])
                entity_calls = [c for c in self.calls if c[0] == 'EntityExtractionAgent']
                self.assertEqual(len(entity_calls), 3)
                self.assertEqual(len([c for c in self.calls if c[0] == 'TripleSplittingAgent']), 3)
                self.assertIn('TextComparisonAgent', [c[0] for c in self.calls])
                self.assertIn('TextGenerationAgent', [c[0] for c in self.calls])
                self.assertEqual(len([c for c in self.calls if c[0] == 'RelationshipExtractionAgent']), 3)
                self.assertEqual(base.last_baseline_path.read_bytes(), baseline_bytes)
            Path('hidden.json').rename(self.source)

    def test_feedback_replay_and_consumer_inputs(self):
        for mode in ('chat_completions', 'responses'):
            full = self.pipeline('feedback_full_' + mode, mode)
            full.process_document(self.source)
            base = self.pipeline('feedback_base_' + mode, mode)
            base.process_document(self.source, stage='baseline')
            original = base.last_baseline_path.read_bytes()
            self.calls.clear()
            resumed = self.pipeline('feedback_resume_' + mode, mode)
            reconstructed = []
            generation = resumed.text_generation_agent.process
            def capture(triples):
                reconstructed.append([x.to_dict() for x in triples])
                return generation(triples)
            with patch.object(resumed.text_generation_agent, 'process', side_effect=capture):
                resumed.process_document('', stage='revise', baseline_path=base.last_baseline_path)
            self.assertEqual(full.last_run_manifest['documents'], resumed.last_run_manifest['documents'])
            self.assertEqual(reconstructed, [d['stages']['after_split'] for d in resumed.last_run_manifest['documents']])
            split_calls = [c for c in self.calls if c[0] == 'TripleSplittingAgent']
            self.assertEqual(len(split_calls), 3)
            self.assertTrue(all(c[2]['temperature'] == 0.0 for c in split_calls))
            for name, prompt, kwargs in self.calls:
                if name in ('EntityExtractionAgent', 'RelationshipExtractionAgent') and 'EMPTY' not in prompt:
                    current = json.loads(prompt.split('<current_triples_json>')[1].split('</current_triples_json>')[0])
                    self.assertEqual(current[0]['relation'], 'may query')
            self.assertEqual(base.last_baseline_path.read_bytes(), original)

    def test_feedback_replace_index_refers_to_split_set(self):
        base = self.pipeline('index_base')
        base.process_document(self.source, stage='baseline', limit=1)
        pipe = self.pipeline('index_revise')
        split_reply = {'add': [dict(head='Controller', relation='may store', tail='ECU', index=0, reason='split')],
                       'remove': [], 'replace': [dict(head='Controller', relation='may query', tail='ECU', index=0, reason='split')]}
        feedback_reply = {'add': [], 'remove': [], 'replace': [
            fact('may read', index=1, evidence='Controller may query ECU.', reason='correct second split triple')]}
        with patch.object(pipe.triple_splitting_agent, '_make_llm_call', return_value=reply(split_reply)), \
             patch.object(pipe.relationship_extraction_agent, '_make_llm_call', return_value=reply(feedback_reply)):
            result = pipe.process_document('', stage='revise', baseline_path=base.last_baseline_path)
        self.assertEqual([x.relation for x in result.split_triples], ['may query', 'may store'])
        self.assertEqual([x.relation for x in result.integrated_triples], ['may query', 'may read'])
        self.assertEqual(pipe.relationship_extraction_agent.last_revision['accepted']['replace'][0]['before']['relation'], 'may store')
        saved = json.loads((pipe.evaluator_agent._dump_dir / '_dump_doc0_revision_result.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['revision_agent'], 'RelationshipExtractionAgent')
        self.assertEqual(saved['revision_input'], [x.to_dict() for x in result.split_triples])

    def test_split_failure_keeps_baseline_and_is_audited(self):
        base = self.pipeline('fallback_base')
        base.process_document(self.source, stage='baseline', limit=1)
        pipe = self.pipeline('fallback_revise')
        self.calls.clear()
        with patch.object(pipe.triple_splitting_agent, '_make_llm_call', return_value=('invalid', 0, 0, 0)) as call:
            pipe.process_document('', stage='revise', baseline_path=base.last_baseline_path)
        self.assertEqual(call.call_count, 1)
        doc = pipe.last_run_manifest['documents'][0]
        self.assertEqual(doc['rounds']['2'][0]['relation'], 'may query')
        self.assertEqual(doc['stages']['after_split'], doc['rounds']['1'])
        audit = json.loads((pipe.evaluator_agent._dump_dir / '_dump_doc0_splitting.json').read_text(encoding='utf-8'))
        self.assertEqual(audit['audit']['mode'], 'baseline_fallback')
        self.assertEqual(audit['audit']['raw_response'], 'invalid')
        self.assertIn('RelationshipExtractionAgent', [c[0] for c in self.calls])

    def test_saved_graph_context_is_used_even_when_new_graph_differs(self):
        base = self.pipeline('base')
        base.knowledge_graph.add_triple(KnowledgeTriple('External', 'is', 'fixed', confidence=.9))
        base.process_document(self.source, stage='baseline')
        saved = load_baseline(base.last_baseline_path)
        resumed = self.pipeline('resume')
        resumed.knowledge_graph.add_triple(KnowledgeTriple('WRONG', 'is', 'new'))
        observed = []
        real = resumed.conflict_resolution_agent.process
        def capture(triples, context):
            observed.append([x.to_dict() for x in context])
            return real(triples, context)
        with patch.object(resumed.conflict_resolution_agent, 'process', side_effect=capture):
            resumed.process_document('', stage='revise', baseline_path=base.last_baseline_path)
        self.assertEqual(observed, [d['conflict_context'] for d in saved['documents']])

    def test_text_input_restores_actual_summarized_text_and_skips_preprocessing(self):
        Path('source.txt').write_text('A much longer original source.', encoding='utf-8')
        base = self.pipeline('base')
        with patch.dict(os.environ, {'KARMA_USE_SUMMARIZER': '1'}), patch.object(
            base.summarizer_agent, 'process', return_value=(['Controller may query ECU.'], [])
        ):
            base.process_document(Path('source.txt'), stage='baseline')
        package = load_baseline(base.last_baseline_path)
        self.assertEqual(package['documents'][0]['extraction_text'], 'Controller may query ECU.')
        resumed = self.pipeline('resume')
        with patch.object(resumed.ingestion_agent, 'process', side_effect=AssertionError('Preprocessing reran')):
            result = resumed.process_document('', stage='revise', baseline_path=base.last_baseline_path)
        self.assertEqual(result.summaries, ['Controller may query ECU.'])
        self.assertTrue(resumed.last_run_manifest['baseline_config']['use_summarizer'])

    def test_full_snapshot_replay_including_cross_document_conflicts(self):
        full = self.pipeline('full')
        # Exaggerate history sensitivity to ensure replay uses per-document snapshots.
        def history_filter(triples, context):
            return [] if any(t.relation == 'may query' for t in context) else triples
        with patch.object(full.conflict_resolution_agent, 'process', side_effect=history_filter):
            full.process_document(self.source)
        resumed = self.pipeline('resume')
        with patch.object(resumed.conflict_resolution_agent, 'process', side_effect=history_filter):
            resumed.process_document('', stage='revise', baseline_path=full.last_baseline_path)
        self.assertEqual(full.last_run_manifest['documents'], resumed.last_run_manifest['documents'])

    def test_corrupt_missing_unknown_and_threshold_mismatch_fail_before_llm(self):
        base = self.pipeline('base')
        base.process_document(self.source, stage='baseline')
        package = load_baseline(base.last_baseline_path)
        for change in ('tamper', 'missing_field'):
            value = copy.deepcopy(package)
            if change == 'tamper':
                value['documents'][0]['extraction_text'] += 'changed'
            else:
                del value['documents'][0]['conflict_context']
                value['sha256'] = fingerprint({k: v for k, v in value.items() if k != 'sha256'})
            Path(change + '.json').write_text(json.dumps(value), encoding='utf-8')
            self.calls.clear()
            with self.assertRaises(ValueError):
                self.pipeline(change).process_document('', stage='revise', baseline_path=change + '.json')
            self.assertEqual(self.calls, [])
        for kwargs in ({'doc_ids': ['unknown']}, {'limit': 0}):
            with self.assertRaises(ValueError):
                self.pipeline('bad_' + str(len(self.pipes))).process_document('', stage='revise', baseline_path=base.last_baseline_path, **kwargs)
        wrong = self.pipeline('threshold')
        wrong.integration_threshold = .7
        with self.assertRaises(ValueError):
            wrong.process_document('', stage='revise', baseline_path=base.last_baseline_path)

    def test_baseline_cannot_be_overwritten_and_repeated_pipeline_runs_are_separate(self):
        pipe = self.pipeline('base')
        pipe.process_document(self.source, stage='baseline', limit=1)
        path = pipe.last_baseline_path
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            pipe.process_document(self.source, stage='baseline', baseline_path=path)
        pipe.process_document(self.source, stage='baseline', limit=1)
        self.assertNotEqual(path, pipe.last_baseline_path)
        self.assertEqual(path.read_bytes(), original)

    def test_cli_handoff_and_subset_evaluation_by_id(self):
        env = {'KARMA_API_KEY': 'offline', 'KARMA_BASE_URL': 'https://example.invalid/v1', 'KARMA_MODEL': 'offline'}
        def cli(args):
            with patch.dict(os.environ, env), patch.object(main, 'API_MODE', 0), patch.object(sys, 'argv', ['main.py'] + args):
                return main.main()
        self.assertEqual(cli(['--stage', 'baseline', '--input', str(self.source), '--output-dir', 'cli_base',
                              '--integration-threshold', '.6', '--limit', '3']), 0)
        original = Path('cli_base/baseline.json').read_bytes()
        self.source.unlink()
        self.assertEqual(cli(['--stage', 'revise', '--baseline', 'cli_base/baseline.json',
                              '--doc-ids', 'omega', 'empty', '--output-dir', 'cli_rev']), 0)
        self.assertEqual(cli(['--stage', 'revise', '--baseline', 'cli_base/baseline.json', '--output-dir', 'cli_rev']), 1)
        self.assertEqual(Path('cli_base/baseline.json').read_bytes(), original)
        Path('gold.json').write_text(json.dumps({'omega': [], 'alpha': [], 'empty': []}), encoding='utf-8')
        manifest, paired = evaluate.load_run_pairs('cli_rev/details', 'gold.json')
        self.assertEqual([doc['doc_id'] for doc, _ in paired], ['empty', 'omega'])
        with patch.object(evaluate, 'precompute_embeddings'), patch.object(evaluate, 'match_pair', return_value=0):
            # Empty gold uses the existing evaluator's no-embedding path.
            self.assertEqual(evaluate.evaluate_run_manifest(Path('cli_base/details'), Path('gold.json')), 0)
            self.assertEqual(evaluate.evaluate_run_manifest(Path('cli_rev/details'), Path('gold.json')), 0)
        report = json.loads(Path('cli_rev/details/eval_result.json').read_text(encoding='utf-8'))
        self.assertEqual([d['doc'] for d in report['round2']['per_doc']], ['empty', 'omega'])
        self.assertIn('delta_micro', report)
        Path('gold.json').write_text(json.dumps({'alpha': []}), encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluate.load_run_pairs('cli_rev/details', 'gold.json')

    def test_full_evaluation_keeps_automatic_gold_detection(self):
        full = self.pipeline('full')
        full.process_document(self.source)
        Path('gold.json').write_text(json.dumps({'alpha': [], 'empty': [], 'omega': []}), encoding='utf-8')
        with patch.object(sys, 'argv', ['evaluate.py', 'full']), \
             patch.object(evaluate, 'detect_gold_dir', return_value=Path('gold.json')) as detect, \
             patch.object(evaluate, 'precompute_embeddings'), \
             patch.object(evaluate, 'match_pair', return_value=0):
            self.assertEqual(evaluate.main(), 0)
            detect.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
