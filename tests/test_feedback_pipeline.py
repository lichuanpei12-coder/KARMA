"""Offline tests of direct three-agent operations, multi-replacement and failure paths."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KnowledgeTriple
from karma.core.feedback_pipeline import FeedbackPipeline
from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.feedback_replace.agent import FeedbackReplaceAgent
from karma.agents.feedback_remove.agent import FeedbackRemoveAgent
from karma.agents.relationship_extraction.agent import RelationshipExtractionAgent
from karma.agents.feedback_operations import apply_operations, validate_reply
from feedback_fixtures import context_from_prompt, no_changes
from karma.core.triple_scores import fixed_score_copy


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.sentences = [dict(sentence_id='S1', text='The system includes a module that processes data.'),
                          dict(sentence_id='S2', text='The module stores records.'),
                          dict(sentence_id='S3', text='The module reports status.')]
        self.text = ' '.join(s['text'] for s in self.sentences)
        self.initial = [KnowledgeTriple('The system', 'includes', 'a module that processes data',
                                         source_sentence_ids=['S1']),
                        KnowledgeTriple('The module', 'stores', 'files', source_sentence_ids=['S2']),
                        KnowledgeTriple('The module', 'stores', 'records', source_sentence_ids=['S2'])]
        self.pipe = FeedbackPipeline(FeedbackAddAgent(None, 'offline'), FeedbackReplaceAgent(None, 'offline'),
                                     FeedbackRemoveAgent(None, 'offline'))

    def fact(self, h, r, t, sid):
        return dict(head=h, relation=r, tail=t, source_sentence_ids=[sid],
                    confidence=.9, clarity=.85, relevance=.8)

    def run_flow(self, fn):
        contexts = []
        def call(agent, prompt, **kwargs):
            ctx = context_from_prompt(prompt)
            contexts.append(copy.deepcopy(ctx))
            result = fn(ctx)
            return result if isinstance(result, tuple) else (json.dumps(result), 12, 8, .1)
        original = copy.deepcopy(self.initial)
        with patch.object(BaseAgent, '_make_llm_call', new=call), \
                patch('httpx.Client.send', side_effect=AssertionError('No network')):
            final = self.pipe.process(self.text, self.initial, {'unique_to_text_a':['old difference']},
                                      sentences=self.sentences, reconstructions=[{'sentence_id':'S1','text_b':'old'}])
        self.assertEqual(self.initial, original)
        return final, contexts

    def test_each_agent_can_finish_a_mixed_correction_on_its_own_snapshot(self):
        for owner in ('add', 'replace', 'remove'):
            with self.subTest(owner=owner):
                def respond(context):
                    if context['stage'] != owner:
                        return no_changes(context)
                    return {
                        'replace': [dict(index=0, reason='split nested fact', new_triples=[
                            self.fact('The system', 'includes', 'a module', 'S1'),
                            self.fact('a module', 'processes', 'data', 'S1')])],
                        'remove': [dict(index=1, keep_index=2, reason='correct stores object already present')],
                        'add': [dict(self.fact('The module', 'reports', 'status', 'S3'), reason='missing')],
                    }
                final, contexts = self.run_flow(respond)
                self.assertEqual([c['stage'] for c in contexts], ['add', 'replace', 'remove'])
                self.assertEqual(self.pipe.snapshots['after_' + owner], final)
                self.assertEqual([t.relation for t in final], ['includes', 'processes', 'stores', 'reports'])
                self.assertEqual([t.source_sentence_ids for t in final], [['S1'], ['S1'], ['S2'], ['S3']])
                audit = next(s for s in self.pipe.last_revision['stages'] if s['stage'] == owner)
                self.assertEqual(audit['application']['index_map'], {0: [0, 1], 1: [], 2: [2]})
                self.assertEqual(audit['application']['accepted'][1]['kept_output_index'], 2)
                self.assertTrue(all(c['comparison_bundle']['basis_version'] == 'V0' for c in contexts))
                self.assertFalse(any('handoff' in c or 'repair_pass' in c for c in contexts))
                self.assertEqual(self.pipe.last_revision['review_issues'], [])

    def test_bad_child_rolls_back_entire_replace_batch(self):
        def respond(ctx):
            r=no_changes(ctx)
            if ctx['stage']=='replace':
                bad=self.fact('a module','processes','data','S1');bad['source_sentence_ids']=['S99']
                r['replace']=[dict(index=0,issue_id='R1',reason='split',new_triples=[self.fact('The system','includes','a module','S1'),bad]),
                              dict(index=1,issue_id='R1',reason='fix',new_triples=[self.fact('The module','stores','records','S2')])]
            return r
        final, contexts=self.run_flow(respond)
        self.assertEqual(final,fixed_score_copy(self.initial))
        self.assertEqual(contexts[2]['current_collection']['triples'][0]['tail'],self.initial[0].tail)
        self.assertEqual(self.pipe.last_revision['stages'][1]['application']['status'],'rejected_batch')
        self.assertEqual(self.pipe.last_revision['status'],'completed_with_errors')

    def test_invalid_json_preserves_input_and_next_stage_still_runs(self):
        final, contexts=self.run_flow(lambda c: ('not json',0,0,0) if c['stage']=='add' else no_changes(c))
        self.assertEqual(final,fixed_score_copy(self.initial))
        self.assertEqual(len(contexts),3)
        self.assertEqual(self.pipe.last_revision['stages'][0]['raw_response'],'not json')
        self.assertEqual(self.pipe.last_revision['stages'][0]['application']['status'],'failed')

    def test_remove_cannot_delete_its_keep_target(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='remove':
                r['remove']=[dict(index=i,keep_index=j,reason='duplicate') for i,j in [(1,2),(2,1)]]
            return r
        final,_=self.run_flow(respond)
        self.assertEqual(final,fixed_score_copy(self.initial))
        self.assertEqual(self.pipe.last_revision['stages'][2]['application']['status'],'rejected_batch')
        self.assertTrue(any(r['reason']=='keep_index is also deleted'
                            for r in self.pipe.last_revision['stages'][2]['application']['rejected']))

    def test_mixed_add_batch_rolls_back_if_an_indexed_edit_fails(self):
        def respond(context):
            reply = no_changes(context)
            if context['stage'] == 'add':
                reply['add'] = [dict(self.fact('The module', 'reports', 'status', 'S3'), reason='missing')]
                reply['remove'] = [dict(index=10, keep_index=1, reason='duplicate')]
            return reply
        final, _ = self.run_flow(respond)
        self.assertEqual(final, fixed_score_copy(self.initial))
        self.assertEqual(self.pipe.last_revision['stages'][0]['application']['status'], 'rejected_batch')

    def test_direct_deletion_with_no_surviving_duplicate(self):
        reply = {'remove': [dict(index=1, keep_index=None, reason='wrong object')]}
        result, audit = apply_operations('replace', self.initial, reply, self.sentences)
        self.assertEqual(result, [self.initial[0], self.initial[2]])
        self.assertIsNone(audit['accepted'][0]['kept_output_index'])

    def test_new_triple_rejects_missing_sources(self):
        for key,value in [('source_sentence_ids',[]),('source_sentence_ids',['S999'])]:
            with self.subTest(key=key,value=value):
                item=self.fact('The module','reports','status','S3');item[key]=value
                r=dict(add=[dict(item,issue_id='A',reason='missing')])
                result,audit=apply_operations('add',self.initial,r,self.sentences)
                self.assertEqual(result,self.initial)
                self.assertEqual(audit['status'],'partial')

    def test_each_new_replacement_keeps_source_and_gets_fixed_score(self):
        children=[self.fact('The system','includes','a module','S1'),self.fact('a module','processes','data','S1')]
        children[1]['confidence']=.7
        r=dict(replace=[dict(index=0,issue_id='R',reason='split',new_triples=children)])
        final,audit=apply_operations('replace',self.initial,r,self.sentences)
        self.assertEqual(audit['status'],'applied')
        self.assertEqual([t.confidence for t in final[:2]],[.8,.8])
        self.assertTrue(all(t.source_sentence_ids == ['S1'] for t in final[:2]))
        self.assertTrue(all('evidence' not in t.to_dict() for t in final[:2]))

    def test_score_free_operations_and_score_free_model_context(self):
        def respond(c):
            r = no_changes(c)
            if c['stage'] == 'add':
                item = self.fact('The module', 'reports', 'status', 'S3')
                for key in ('confidence', 'clarity', 'relevance'):
                    item.pop(key)
                r['add'] = [dict(item, reason='missing relation')]
            return r
        final, contexts = self.run_flow(respond)
        self.assertEqual(len(final), 4)
        for triple in final:
            self.assertEqual((triple.confidence, triple.clarity, triple.relevance), (.8, .8, .8))
        for stage in self.pipe.last_revision['stages']:
            sent = json.dumps(stage['messages'], ensure_ascii=False)
            for field in ('confidence', 'clarity', 'relevance', 'origin_indices', 'reviewed_indices'):
                self.assertNotIn(field, sent)
            self.assertNotIn('# 收到的问题', sent)

    def test_baseline_without_scores_uses_fixed_scores_and_verbatim_sources(self):
        agent = RelationshipExtractionAgent(None, 'offline')
        item = dict(head='The module', relation='stores', tail='records',
                    context=self.sentences[1]['text'], source_sentence_ids=['S2'])
        for payload in (item, dict(item, confidence=True, clarity=0, relevance=1)):
            with patch.object(agent, '_make_llm_call', return_value=(json.dumps([payload]), 0, 0, 0)) as call:
                result = agent.process([self.text], [], sentences=self.sentences)
            self.assertEqual(len(result), 1)
            self.assertEqual((result[0].confidence, result[0].clarity, result[0].relevance), (.8, .8, .8))
            self.assertEqual(result[0].source_sentence_ids, ['S2'])
            for field in ('confidence', 'clarity', 'relevance'):
                self.assertNotIn(field, agent.system_prompt + call.call_args.args[0])

    def test_legacy_handoff_is_rejected_in_place_and_never_delivered(self):
        for stage, target in [('add', 'replace'), ('replace', 'remove'), ('remove', 'add')]:
            with self.subTest(stage=stage):
                def respond(context):
                    reply = no_changes(context)
                    if context['stage'] == stage:
                        reply['handoff'] = [dict(target=target, indices=[0], source_sentence_ids=['S1'],
                                                 problem='change the current item')]
                    return reply
                result, contexts = self.run_flow(respond)
                self.assertEqual(len(contexts), 3)
                self.assertEqual(result, fixed_score_copy(self.initial))
                self.assertEqual([i['stage'] for i in self.pipe.last_revision['review_issues']], [stage])
                for record in self.pipe.last_revision['stages']:
                    self.assertNotIn('handoff', record['messages'][1]['content'])
                    if record['stage'] == stage:
                        self.assertEqual(record['application']['status'], 'failed')

    def test_new_fact_requires_one_valid_sentence(self):
        valid = self.fact('The module','reports','status','S3')
        variants = [dict(valid, source_sentence_ids=['S2','S3']),
                    dict(valid, source_sentence_ids=['S99']),
                    dict(valid, source_sentence_ids=[])]
        for item in variants:
            with self.subTest(item=item):
                result, audit = apply_operations('add', self.initial, {'add':[dict(item,reason='missing')]}, self.sentences)
                self.assertEqual(result,self.initial)
                self.assertEqual(audit['status'],'partial')

    def test_baseline_rejects_combined_sentences_and_recovers_one_exact_source(self):
        agent = RelationshipExtractionAgent(None,'offline')
        base = dict(head='The module',relation='stores',tail='records')
        invalid = [dict(base, source_sentence_ids=['S1','S2']),
                   dict(base, source_sentence_ids=['S99'])]
        with patch.object(agent,'_make_llm_call', return_value=(json.dumps(invalid+[base]),0,0,0)):
            result = agent.process([self.text],[],sentences=self.sentences)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].source_sentence_ids,['S2'])
        self.assertEqual(len(agent.last_extraction[0]['rejected']),2)

    def test_existing_multiple_sources_are_preserved(self):
        self.initial[0].source_sentence_ids = ['S1','S2']
        final, _ = self.run_flow(no_changes)
        self.assertEqual(final[0].source_sentence_ids,['S1','S2'])


if __name__ == '__main__':
    unittest.main()
