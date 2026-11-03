"""Offline provenance, aligned reconstruction, and feedback regression tests."""

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from karma.core.data_structures import KnowledgeTriple
from karma.core.sentence_groups import source_sentences, attach_sources, group_triples
from karma.agents.triple_revision import TripleRevisionMixin
from karma.agents.relationship_extraction.agent import RelationshipExtractionAgent
from karma.agents.text_generation.agent import TextGenerationAgent
from karma.agents.text_comparison.agent import TextComparisonAgent
from karma.agents.entity_extraction.agent import difference_context as entity_diff
from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.feedback_replace.agent import FeedbackReplaceAgent
from karma.agents.feedback_remove.agent import FeedbackRemoveAgent
from karma.core.feedback_pipeline import FeedbackPipeline
from karma.core.base_agent import BaseAgent
from feedback_fixtures import no_changes_call


def reply(value):
    return json.dumps(value), 11, 7, 0.0


def tagged_json(prompt, name):
    return json.loads(prompt.split(f'<{name}>')[1].split(f'</{name}>')[0])


class SentenceGroupsTests(unittest.TestCase):
    def setUp(self):
        self.text = 'Controller reads data. Sensor measures temperature.'
        self.sentences = source_sentences(self.text)
        self.triple = KnowledgeTriple('Controller', 'reads', 'data', source_sentence_ids=['S1'])

    def test_dataset_boundaries_override_splitter_and_roundtrip(self):
        parts = ['Controller reads data. Sensor measures temperature.', 'A value is 3.5 ms.']
        sentences = source_sentences(' '.join(parts), parts)
        self.assertEqual([s['text'] for s in sentences], parts)
        self.assertEqual([s['sentence_id'] for s in sentences], ['S1', 'S2'])
        with self.assertRaises(ValueError):
            source_sentences('different text', parts)
        self.assertEqual(len(source_sentences('Dr. Smith reads 3.5 ms. It works.')), 2)
        self.assertEqual(len(source_sentences('控制器读取数据。传感器测量温度！')), 2)
        old = dict(head='Controller', relation='reads', tail='data')
        restored = KnowledgeTriple.from_dict(old)
        self.assertEqual(restored.source_sentence_ids, [])
        self.assertNotIn('source_sentence_ids', restored.to_dict())
        self.assertEqual(KnowledgeTriple.from_dict(self.triple.to_dict()), self.triple)

    def test_empty_cross_sentence_and_unknown_groups_keep_global_indices(self):
        cross = KnowledgeTriple('It', 'uses', 'data', source_sentence_ids=['S1', 'S2'])
        unknown = KnowledgeTriple('Unknown', 'has', 'no evidence')
        groups = group_triples(self.sentences, [self.triple])
        self.assertEqual(groups[1]['triples'], [])
        groups = group_triples(self.sentences, [self.triple, cross, unknown])
        self.assertEqual([t['index'] for t in groups[0]['triples']], [0, 1])
        self.assertEqual([t['index'] for t in groups[1]['triples']], [1])
        self.assertEqual(groups[2]['sentence_id'], 'UNASSIGNED')
        self.assertEqual(groups[2]['triples'][0]['index'], 2)

    def test_legacy_exact_recovery_does_not_guess_from_shared_entity(self):
        exact = KnowledgeTriple('Sensor', 'measures', 'temperature')
        attach_sources(exact, self.sentences)
        self.assertEqual(exact.source_sentence_ids, ['S2'])
        wrong = KnowledgeTriple('Sensor', 'reads', 'data')
        attach_sources(wrong, self.sentences, {'source_sentence_ids': ['S99']})
        self.assertEqual(wrong.source_sentence_ids, [])
        attach_sources(wrong, self.sentences, {'context': 'Sensor measures temperature.'})
        self.assertEqual(wrong.source_sentence_ids, ['S2'])

    def test_extracts_provenance_and_uncovered_sentence_remains_visible(self):
        agent = RelationshipExtractionAgent(None, 'offline')
        response = [dict(head='Controller', relation='reads', tail='data',
                         context='Controller reads data.', source_sentence_ids=['S1'])]
        with patch.object(agent, '_make_llm_call', return_value=reply(response)) as call:
            triples = agent.process([self.text], [], sentences=self.sentences)
        self.assertEqual(tagged_json(call.call_args.args[0], 'source_sentences_json'), self.sentences)
        self.assertEqual(triples[0].source_sentence_ids, ['S1'])
        self.assertEqual(triples[0].evidence, 'Controller reads data.')
        self.assertEqual(group_triples(self.sentences, triples)[1]['triples'], [])

    def test_split_inherits_and_duplicate_merges_provenance(self):
        mixin = TripleRevisionMixin()
        parent = copy.deepcopy(self.triple)
        parent.evidence = 'Controller reads data.'
        parent.confidence = .91
        operation = dict(index=0, head='Controller', relation='stores', tail='data',
                         reason='split', source_sentence_ids=['S99'])
        children, audit = mixin._apply_revision([parent], dict(
            add=[operation], remove=[], replace=[]), split_only=True)
        self.assertEqual(children[1].source_sentence_ids, ['S1'])
        self.assertEqual(children[1].evidence, parent.evidence)
        self.assertEqual(children[1].confidence, .91)
        duplicate = copy.deepcopy(parent)
        duplicate.source_sentence_ids = ['S2']
        duplicate.confidence = .99
        unique = mixin._deduplicate_relationships([parent, duplicate])
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0].source_sentence_ids, ['S1', 'S2'])
        self.assertEqual(unique[0].confidence, .99)

    def test_revision_add_replace_keep_source_and_document_indices(self):
        agent = RelationshipExtractionAgent(None, 'offline')
        missing = dict(head='Sensor', relation='measures', tail='temperature',
                       evidence='Sensor measures temperature.', reason='missing', source_sentence_ids=['S2'])
        replace = dict(index=0, head='Controller', relation='reads', tail='data',
                       evidence='Controller reads data.', reason='wording', source_sentence_ids=['S1'])
        changes = dict(add=[missing], replace=[replace], remove=[])
        result, audit = agent._apply_revision([self.triple], changes, source_sentences=self.sentences)
        groups = group_triples(self.sentences, result)
        self.assertEqual(groups[0]['triples'][0]['index'], 0)
        self.assertEqual(groups[1]['triples'][0]['index'], 1)
        self.assertEqual([t.source_sentence_ids for t in result], [['S1'], ['S2']])
        # Old revisions omitting provenance recover it from exact source evidence.
        missing.pop('source_sentence_ids')
        result, _ = agent._apply_revision([self.triple], dict(add=[missing], replace=[], remove=[]),
                                         source_sentences=self.sentences)
        self.assertEqual(result[1].source_sentence_ids, ['S2'])

    def test_reconstruction_has_no_source_or_evidence_and_restores_id_order(self):
        agent = TextGenerationAgent(None, 'offline')
        self.triple.evidence = 'SECRET EVIDENCE'
        groups = group_triples(self.sentences, [self.triple])
        response = [{'sentence_id': 'S2', 'text': 'Invented empty-group fact'},
                    {'sentence_id': 'S1', 'text': 'Controller reads data.'}]
        with patch.object(agent, '_make_llm_call', return_value=reply(response)) as call:
            text = agent.process([self.triple], sentence_groups=groups)
        call.assert_called_once()
        prompt = call.call_args.args[0]
        self.assertNotIn('Sensor measures temperature.', prompt)
        self.assertNotIn('SECRET EVIDENCE', prompt)
        self.assertNotIn('text', tagged_json(prompt, 'triple_groups_json')[0])
        self.assertEqual(text, 'Controller reads data.')
        self.assertEqual([r['sentence_id'] for r in agent.last_grouped_generation], ['S1', 'S2'])
        self.assertEqual(agent.last_grouped_generation[1]['text_b'], '')

    def test_reconstruction_invalid_id_fallback_retains_every_fact(self):
        agent = TextGenerationAgent(None, 'offline')
        groups = group_triples(self.sentences, [self.triple])
        for response in ([{'sentence_id': 'S99', 'text': 'wrong'}],
                         [{'sentence_id': 'S1', 'text': 'missing S2'}]):
            with self.subTest(response=response), patch.object(agent, '_make_llm_call', return_value=reply(response)):
                agent.process([self.triple], sentence_groups=groups)
            first, second = agent.last_grouped_generation
            self.assertEqual(first['generation_status'], 'literal_fallback')
            self.assertIn('Controller : reads : data', first['text_b'])
            self.assertEqual(second['text_b'], '')

    def test_comparison_includes_empty_group_and_survives_both_feedback_formatters(self):
        agent = TextComparisonAgent(None, 'offline')
        groups = group_triples(self.sentences, [self.triple])
        recon = [{'sentence_id': 'S1', 'text_b': 'Controller reads data.', 'generation_status': 'generated'},
                 {'sentence_id': 'S2', 'text_b': '', 'generation_status': 'empty_triples'}]
        response = [{'sentence_id': 'S2', 'unique_to_text_a': ['Sensor measures temperature.'], 'unique_to_text_b': []},
                    {'sentence_id': 'S1', 'unique_to_text_a': [], 'unique_to_text_b': []}]
        with patch.object(agent, '_make_llm_call', return_value=reply(response)) as call:
            diff = agent.process(self.text, recon[0]['text_b'], sentence_groups=groups, reconstructions=recon)
        call.assert_called_once()
        pairs = tagged_json(call.call_args.args[0], 'sentence_pairs_json')
        self.assertEqual(pairs[1]['text_a'], 'Sensor measures temperature.')
        self.assertEqual(pairs[1]['text_b'], '')
        self.assertEqual(diff['unique_to_text_a'], ['[S2] Sensor measures temperature.'])
        for formatter in (entity_diff,):
            self.assertEqual(tagged_json(formatter(diff), 'text_difference_json')['sentence_differences'][1]['sentence_id'], 'S2')

    def test_failed_comparison_is_not_reported_as_successful_no_difference(self):
        agent = TextComparisonAgent(None, 'offline')
        groups = group_triples(self.sentences, [self.triple])
        with patch.object(agent, '_make_llm_call', return_value=reply([])):
            diff = agent.process(self.text, '', sentence_groups=groups, reconstructions=[])
        self.assertEqual(diff['_metadata']['status'], 'failed')
        self.assertEqual(len(diff['sentence_differences']), 2)
        self.assertTrue(all(r['comparison_status'] == 'failed' for r in diff['sentence_differences']))

    def test_unassigned_note_is_conditional_and_records_survive(self):
        for has_unknown in (False, True):
            with self.subTest(has_unknown=has_unknown):
                triples = [copy.deepcopy(self.triple)]
                if has_unknown:
                    triples.append(KnowledgeTriple('Unknown', 'has', 'unlocated evidence'))
                groups = group_triples(self.sentences, triples)
                generated = [dict(sentence_id=g['sentence_id'], text='Existing input facts.')
                             for g in groups]
                generation = TextGenerationAgent(None, 'offline')
                with patch.object(generation, '_make_llm_call', return_value=reply(generated)) as call:
                    generation.process(triples, sentence_groups=groups)
                generation_prompt = call.call_args.args[0]
                self.assertEqual('UNASSIGNED' in generation_prompt, has_unknown)
                self.assertEqual([r['sentence_id'] for r in generation.last_grouped_generation],
                                 [g['sentence_id'] for g in groups])
                compared = [dict(sentence_id=g['sentence_id'], unique_to_text_a=[], unique_to_text_b=[])
                            for g in groups]
                comparison = TextComparisonAgent(None, 'offline')
                with patch.object(comparison, '_make_llm_call', return_value=reply(compared)) as call:
                    diff = comparison.process(self.text, '', sentence_groups=groups,
                                              reconstructions=generation.last_grouped_generation)
                self.assertEqual('UNASSIGNED' in call.call_args.args[0], has_unknown)
                self.assertEqual([r['sentence_id'] for r in diff['sentence_differences']],
                                 [g['sentence_id'] for g in groups])
                for formatter in (entity_diff,):
                    self.assertEqual('UNASSIGNED' in formatter(diff), has_unknown)
                    self.assertEqual(tagged_json(formatter(diff), 'text_difference_json')['sentence_differences'],
                                     diff['sentence_differences'])
                feedback = FeedbackPipeline(FeedbackAddAgent(None,'offline'), FeedbackReplaceAgent(None,'offline'), FeedbackRemoveAgent(None,'offline'))
                with patch.object(BaseAgent, '_make_llm_call', side_effect=no_changes_call):
                    result = feedback.process(self.text, triples, diff, sentences=self.sentences)
                context = feedback.last_revision['stages'][0]['context']
                self.assertEqual(bool(context['unassigned_indices']), has_unknown)
                self.assertEqual([(t.head, t.relation, t.tail) for t in result],
                                 [(t.head, t.relation, t.tail) for t in triples])


    def test_feedback_explains_unknown_group_from_either_input(self):
        unknown = KnowledgeTriple('Unknown', 'has', 'unlocated evidence')
        old_diff = dict(sentence_differences=[dict(sentence_id='UNASSIGNED',
                                                  unique_to_text_a=[], unique_to_text_b=[])])
        for triples, diff in (([unknown], {}), ([copy.deepcopy(self.triple)], old_diff)):
            with self.subTest(current_unknown=triples[0].head == 'Unknown'):
                pipeline = FeedbackPipeline(FeedbackAddAgent(None,'offline'), FeedbackReplaceAgent(None,'offline'), FeedbackRemoveAgent(None,'offline'))
                with patch.object(BaseAgent, '_make_llm_call', side_effect=no_changes_call):
                    pipeline.process(self.text, triples, diff, sentences=self.sentences)
                context = pipeline.last_revision['stages'][0]['context']
                self.assertEqual(context['comparison_bundle']['diff'], diff)
                self.assertEqual(context['unassigned_indices'], [0] if triples[0].head == 'Unknown' else [])



if __name__ == '__main__':
    unittest.main()
