import copy
import json
import unittest
from unittest.mock import patch
from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KnowledgeTriple, KGEntity
from karma.core.sentence_feedback_pipeline import SentenceFeedbackPipeline, sentence_context
from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.feedback_replace.agent import FeedbackReplaceAgent
from karma.agents.feedback_remove.agent import FeedbackRemoveAgent
from karma.agents.text_generation.agent import TextGenerationAgent
from karma.agents.text_comparison.agent import TextComparisonAgent
from feedback_fixtures import context_from_prompt, no_changes


class SentenceFlowTests(unittest.TestCase):
    def setUp(self):
        self.sentences = [dict(sentence_id='S3', text='Alpha reads data.'),
                          dict(sentence_id='S8', text='Beta stores records.')]
        self.triples = [KnowledgeTriple('Beta', 'stores', 'records', source_sentence_ids=['S8']),
                        KnowledgeTriple('Alpha', 'reads', 'data', source_sentence_ids=['S3'])]
        self.pipe = SentenceFeedbackPipeline(FeedbackAddAgent(None, 'offline'),
                                             FeedbackReplaceAgent(None, 'offline'), FeedbackRemoveAgent(None, 'offline'))
        self.diff = {'sentence_differences': [dict(sentence_id=s['sentence_id'], text_a=s['text'],
                     text_b=s['text'], triple_indices=[i], unique_to_text_a=[s['text']],
                     unique_to_text_b=[], comparison_status='compared') for i,s in enumerate(self.sentences)]}
        self.recon = [dict(sentence_id=s['sentence_id'], text_b=s['text']) for s in self.sentences]

    def run_pipe(self, respond=None):
        contexts = []
        def call(agent, prompt, **kwargs):
            ctx = context_from_prompt(prompt)
            contexts.append(copy.deepcopy(ctx))
            result = respond(ctx) if respond else no_changes(ctx)
            return (result if isinstance(result, str) else json.dumps(result)), 0, 0, 0
        with patch.object(BaseAgent, '_make_llm_call', new=call):
            out = self.pipe.process(' '.join(s['text'] for s in self.sentences), self.triples,
                                    self.diff, [KGEntity('a', name='Alpha'), KGEntity('b', name='Beta')],
                                    sentences=self.sentences, reconstructions=self.recon)
        return out, contexts

    def test_isolated_inputs_and_complete_document_snapshots(self):
        original = copy.deepcopy(self.triples)
        out, contexts = self.run_pipe()
        self.assertEqual(len(contexts), 6)
        for i, ctx in enumerate(contexts):
            own = self.sentences[i // 3]
            other = self.sentences[1 - i // 3]
            self.assertEqual(ctx['source_sentences'], [own])
            self.assertNotIn(other['text'], json.dumps(ctx))
            self.assertNotIn(other['sentence_id'], json.dumps(ctx))
            self.assertEqual(ctx['current_collection']['triples'][0]['index'], 0)
            self.assertNotIn('triple_indices', json.dumps(ctx['comparison_bundle']))
        self.assertEqual(self.triples, original)
        self.assertEqual([t.head for t in out], ['Alpha', 'Beta'])
        self.assertEqual(len(self.pipe.snapshots['after_add']), 2)
        self.assertEqual(self.pipe.last_revision['sentence_runs'][0]['initial_index_map'], {0: 1})
        self.assertEqual(len({s['pass_id'] for s in self.pipe.last_revision['stages']}), 6)
        self.assertEqual(self.pipe.last_revision['snapshot_index_maps']['after_revision'][1]['global_index'], 1)

    def test_empty_sentence_still_adds_and_failure_stays_local(self):
        self.triples = self.triples[:1]
        def respond(ctx):
            reply = no_changes(ctx)
            sid = ctx['source_sentences'][0]['sentence_id']
            if sid == 'S3' and ctx['stage'] == 'add':
                reply['add'] = [dict(head='Alpha', relation='reads', tail='data', source_sentence_ids=['S3'],
                                      reason='missing')]
            if sid == 'S8' and ctx['stage'] == 'replace':
                return 'invalid json'
            return reply
        out, contexts = self.run_pipe(respond)
        self.assertEqual(contexts[0]['current_collection']['triples'], [])
        self.assertEqual(contexts[1]['current_collection']['triples'][0]['head'], 'Alpha')
        self.assertEqual(len(out), 2)
        self.assertEqual(self.pipe.last_revision['status'], 'completed_with_errors')

    def test_split_updates_local_handoff_indices_before_remove(self):
        self.sentences = [dict(sentence_id='S3', text='Alpha reads and stores data.')]
        self.triples = [KnowledgeTriple('Alpha', 'reads and stores', 'data', source_sentence_ids=['S3']),
                        KnowledgeTriple('Alpha', 'stores', 'data', source_sentence_ids=['S3'])]
        def respond(ctx):
            r = no_changes(ctx)
            if ctx['stage'] == 'replace':
                r['replace'] = [dict(index=0, reason='split', new_triples=[
                    dict(head='Alpha', relation=rel, tail='data', source_sentence_ids=['S3']) for rel in ('reads', 'stores')])]
                r['handoff'] = [dict(target='remove', indices=[0,1], source_sentence_ids=['S3'], problem='duplicate stores')]
            if ctx['stage'] == 'remove':
                self.assertEqual(ctx['handoff'][0]['indices'], [0,1,2])
                r['remove'] = [dict(index=2, keep_index=1, reason='same stores')]
            return r
        out, _ = self.run_pipe(respond)
        self.assertEqual([t.relation for t in out], ['reads', 'stores'])

    def test_invalid_source_ownership_never_falls_back_to_document(self):
        for ids in (['S3', 'S8'], [], ['S99']):
            with self.subTest(ids=ids):
                self.triples[0].source_sentence_ids = ids
                with patch.object(BaseAgent, '_make_llm_call', side_effect=AssertionError('No model call')):
                    with self.assertRaisesRegex(ValueError, 'one valid source sentence'):
                        self.run_pipe()

    def test_legacy_difference_not_guessed_between_sentences(self):
        diff, rec = sentence_context(self.sentences[0], {'unique_to_text_a': ['[S3] own', '[S8] other', 'unknown']}, [])
        self.assertEqual(diff['unique_to_text_a'], ['own'])
        self.assertEqual(diff['sentence_differences'][0]['comparison_status'], 'unavailable')

    def test_repair_bounded_per_sentence(self):
        def respond(ctx):
            r = no_changes(ctx)
            if ctx['stage'] == 'remove':
                r['handoff'] = [dict(target='add', indices=[], source_sentence_ids=[ctx['source_sentences'][0]['sentence_id']], problem='check')]
            return r
        _, contexts = self.run_pipe(respond)
        self.assertEqual(len(contexts), 12)
        self.assertEqual(len(self.pipe.last_revision['undelivered_issues']), 2)

    def test_reconstruction_and_comparison_isolate_sentences_and_failures(self):
        groups = [dict(s, triples=[dict(index=i, head=t.head, relation=t.relation, tail=t.tail)])
                  for i,(s,t) in enumerate(zip(self.sentences, reversed(self.triples)))]
        gen, cmp = TextGenerationAgent(None,'offline'), TextComparisonAgent(None,'offline')
        generation_inputs, compare_inputs = [], []
        def call(agent, prompt, **kwargs):
            if isinstance(agent, TextGenerationAgent):
                items = json.loads(prompt.split('<triple_groups_json>')[1].split('</triple_groups_json>')[0])
                generation_inputs.append(items)
                self.assertEqual(len(items), 1)
                out = [dict(sentence_id=items[0]['sentence_id'], text='generated '+items[0]['sentence_id'])]
            else:
                items = json.loads(prompt.split('<sentence_pairs_json>')[1].split('</sentence_pairs_json>')[0])
                compare_inputs.append(prompt)
                self.assertEqual(len(items), 1)
                if items[0]['sentence_id'] == 'S3':
                    return 'invalid json',0,0,0
                out = [dict(sentence_id=items[0]['sentence_id'], unique_to_text_a=[], unique_to_text_b=[])]
            return json.dumps(out),0,0,0
        with patch.object(BaseAgent, '_make_llm_call', new=call):
            gen.process([], sentence_groups=groups, scope='sentence')
            result = cmp.process('FULL OTHER DOCUMENT', '', sentence_groups=groups,
                                 reconstructions=gen.last_grouped_generation, scope='sentence')
        self.assertEqual(len(generation_inputs),2)
        self.assertNotIn('Beta stores records.',compare_inputs[0])
        self.assertNotIn('Alpha reads data.',compare_inputs[1])
        self.assertTrue(all('FULL OTHER DOCUMENT' not in p for p in compare_inputs))
        self.assertEqual([r['comparison_status'] for r in result['sentence_differences']],['failed','compared'])
