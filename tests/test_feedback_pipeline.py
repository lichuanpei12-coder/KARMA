"""Offline tests of actual three-agent handoffs, multi-replacement and failure paths."""
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

    def test_add_then_one_to_many_replace_then_remove_and_index_handoff(self):
        def respond(ctx):
            r = no_changes(ctx)
            if ctx['stage'] == 'add':
                r['add'] = [dict(self.fact('The module','reports','status','S3'), issue_id='A1',reason='missing')]
                r['handoff'] = [dict(target='replace',indices=[1],problem='files incorrect',source_sentence_ids=['S2'])]
            elif ctx['stage'] == 'replace':
                self.assertEqual(len(ctx['current_collection']['triples']),4)
                self.assertEqual(ctx['current_collection']['triples'][3]['relation'],'reports')
                r['replace'] = [dict(index=0,issue_id='R1',reason='split',new_triples=[
                    self.fact('The system','includes','a module','S1'), self.fact('a module','processes','data','S1')]),
                    dict(index=1,issue_id='R1',reason='correct object',new_triples=[self.fact('The module','stores','records','S2')])]
                r['handoff']=[dict(target='remove',indices=[1,2],problem='duplicates',source_sentence_ids=['S2'])]
            else:
                self.assertEqual(len(ctx['current_collection']['triples']),5)
                note=ctx['handoff'][0]
                self.assertEqual(note['indices'],[2,3])
                self.assertNotIn('origin_indices',note)
                self.assertEqual(len(ctx['handoff']), 1)
                r['remove']=[dict(issue_id='D1',index=3,keep_index=2,reason='same fact')]
            return r
        final, contexts=self.run_flow(respond)
        self.assertEqual([c['stage'] for c in contexts],['add','replace','remove'])
        self.assertEqual([t.relation for t in final],['includes','processes','stores','reports'])
        self.assertEqual([t.source_sentence_ids for t in final],[['S1'],['S1'],['S2'],['S3']])
        self.assertEqual(self.pipe.last_revision['undelivered_issues'],[])
        self.assertTrue(self.pipe.last_revision['unverified_issues'])
        self.assertTrue(all(h['delivery_status']=='delivered' for h in self.pipe.last_revision['handoff_log']))
        for c in contexts:self.assertEqual(c['comparison_bundle']['basis_version'],'V0')
        audit=self.pipe.last_revision['stages'][1]
        self.assertEqual(audit['application']['index_map'][0],[0,1])
        self.assertEqual(audit['messages'][0]['role'],'system')
        self.assertIn('new_triples',audit['messages'][1]['content'])
        self.assertIsNotNone(audit['raw_response'])

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

    def test_late_replace_request_runs_only_one_bounded_repair_sweep(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='remove' and not c['repair_pass']:
                r['handoff']=[dict(target='replace',indices=[1],problem='object wrong',source_sentence_ids=['S2'])]
            if c['stage']=='replace' and c['repair_pass']:
                r['replace']=[dict(index=1,issue_id='R',reason='fix object',new_triples=[self.fact('The module','stores','records','S2')])]
            return r
        final,contexts=self.run_flow(respond)
        self.assertEqual([c['stage'] for c in contexts],['add','replace','remove','replace','remove'])
        self.assertEqual(final[1].tail,'records')
        self.assertEqual(self.pipe.snapshots['after_replace'][1].tail,'files')
        self.assertEqual(self.pipe.last_revision['undelivered_issues'],[])
        self.assertTrue(self.pipe.last_revision['unverified_issues'])
        self.assertTrue(all(h['delivery_status']=='delivered' for h in self.pipe.last_revision['handoff_log']))

    def test_unresolved_request_does_not_loop(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='remove':
                r['handoff']=[dict(target='replace',indices=[0],problem='uncertain',source_sentence_ids=['S1'])]
            return r
        _,contexts=self.run_flow(respond)
        self.assertEqual(len(contexts),5)
        self.assertTrue(self.pipe.last_revision['undelivered_issues'])

    def test_wrong_stage_operation_is_rejected(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='add':r['remove']=[{'index':0}]
            return r
        final,_=self.run_flow(respond)
        self.assertEqual(final,fixed_score_copy(self.initial))
        self.assertEqual(self.pipe.last_revision['stages'][0]['application']['status'],'failed')

    def test_new_triple_rejects_missing_sources(self):
        for key,value in [('source_sentence_ids',[]),('source_sentence_ids',['S999'])]:
            with self.subTest(key=key,value=value):
                item=self.fact('The module','reports','status','S3');item[key]=value
                r=dict(add=[dict(item,issue_id='A',reason='missing')])
                result,audit=apply_operations('add',self.initial,r,self.sentences)
                self.assertEqual(result,self.initial)
                self.assertEqual(audit['status'],'partial')

    def test_received_handoff_requires_no_reply_and_is_not_semantically_closed(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='add':
                r['handoff']=[dict(target='replace',indices=[0],source_sentence_ids=['S1'],problem='check nested relation')]
            return r
        final,_=self.run_flow(respond)
        self.assertEqual(final,fixed_score_copy(self.initial))
        self.assertEqual(self.pipe.last_revision['stages'][1]['application']['status'],'no_changes')
        note=self.pipe.last_revision['handoff_log'][0]
        self.assertEqual(note['delivery_status'],'delivered')
        self.assertEqual(note['semantic_status'],'unverified')
        self.assertEqual(len(self.pipe.last_revision['stages']),3)

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

    def test_wrong_handoff_reference_is_rejected(self):
        def respond(c):
            r = no_changes(c)
            if c['stage'] == 'add':
                r['handoff'] = [dict(target='replace', indices=[999], source_sentence_ids=['S1'], problem='bad index')]
            return r
        final, _ = self.run_flow(respond)
        self.assertEqual(final, fixed_score_copy(self.initial))
        self.assertEqual(self.pipe.last_revision['stages'][0]['application']['status'], 'failed')

    def test_only_target_stage_receives_hints_without_tracking_fields(self):
        def respond(c):
            r = no_changes(c)
            if c['stage'] == 'add':
                r['handoff'] = [dict(target='replace', indices=[0], source_sentence_ids=['S1'], problem='nested relation')]
            return r
        _, contexts = self.run_flow(respond)
        self.assertEqual([bool(c['handoff']) for c in contexts], [False, True, False])
        messages = [s['messages'][1]['content'] for s in self.pipe.last_revision['stages']]
        self.assertTrue(all('handoff_results' not in m and '# 收到的问题' not in m for m in messages))
        self.assertEqual(set(contexts[1]['handoff'][0]), {'indices','source_sentence_ids','problem'})

    def test_failed_delivery_is_retried_once_and_never_claims_resolution(self):
        def respond(c):
            r = no_changes(c)
            if c['stage'] == 'add':
                r['handoff'] = [dict(target='replace', indices=[0], source_sentence_ids=['S1'], problem='nested relation')]
            if c['stage'] == 'replace' and not c['repair_pass']:
                return ('invalid response', 0, 0, 0)
            return r
        _, contexts = self.run_flow(respond)
        self.assertEqual([c['stage'] for c in contexts], ['add','replace','remove','replace','remove'])
        note = self.pipe.last_revision['handoff_log'][0]
        self.assertEqual([a['application_status'] for a in note['delivery_attempts']], ['failed','no_changes'])
        self.assertEqual(note['delivery_status'], 'delivered')
        self.assertEqual(note['semantic_status'], 'unverified')
        self.assertTrue(self.pipe.last_revision['review_issues'])

    def test_backward_add_handoff_has_at_most_six_calls(self):
        def respond(c):
            r = no_changes(c)
            if c['stage'] == 'remove':
                r['handoff'] = [dict(target='add', indices=[], source_sentence_ids=['S3'], problem='reports missing')]
            return r
        _, contexts = self.run_flow(respond)
        self.assertEqual([c['stage'] for c in contexts], ['add','replace','remove','add','replace','remove'])
        self.assertEqual(len(self.pipe.last_revision['undelivered_issues']), 1)
        self.assertEqual(self.pipe.last_revision['undelivered_issues'][0]['target'], 'add')

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
