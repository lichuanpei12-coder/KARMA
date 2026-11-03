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
from karma.agents.feedback_operations import apply_operations, validate_reply
from feedback_fixtures import context_from_prompt, no_changes, issue


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
                    evidence=next(s['text'] for s in self.sentences if s['sentence_id'] == sid),
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
                r['issues'] = [issue('A1', [], self.text, 'reports missing'), issue('A2', [1], self.text, 'files incorrect')]
                r['add'] = [dict(self.fact('The module','reports','status','S3'), issue_id='A1',reason='missing')]
                r['handoff'] = [dict(issue_id='A2',target='replace',related_indices=[1],finding='files incorrect',evidence=self.sentences[1]['text'])]
            elif ctx['stage'] == 'replace':
                self.assertEqual(len(ctx['current_collection']['triples']),4)
                self.assertEqual(ctx['current_collection']['triples'][3]['relation'],'reports')
                r['handoff_results'] = [dict(issue_id=h['id'],status='resolved',reason='corrected') for h in ctx['handoff']]
                r['issues'] = [issue('R1',[0,1],self.text,'split and fix'),issue('R2',[1,2],self.text,'duplicates after fix')]
                r['replace'] = [dict(index=0,issue_id='R1',reason='split',new_triples=[
                    self.fact('The system','includes','a module','S1'), self.fact('a module','processes','data','S1')]),
                    dict(index=1,issue_id='R1',reason='correct object',new_triples=[self.fact('The module','stores','records','S2')])]
                r['handoff']=[dict(issue_id='R2',target='remove',related_indices=[1,2],finding='duplicates',evidence=self.sentences[1]['text'])]
            else:
                self.assertEqual(len(ctx['current_collection']['triples']),5)
                note=next(h for h in ctx['handoff'] if h['target']=='remove')
                self.assertEqual(note['related_indices'],[2,3])
                self.assertEqual(note['origin_indices'],[1,2])
                r['handoff_results']=[dict(issue_id=h['id'],status='resolved',reason='handled') for h in ctx['handoff']]
                r['issues']=[issue('D1',[2,3],self.sentences[1]['text'],'duplicate','S2')]
                r['remove']=[dict(issue_id='D1',index=3,keep_index=2,reason='same fact',evidence=self.sentences[1]['text'])]
            return r
        final, contexts=self.run_flow(respond)
        self.assertEqual([c['stage'] for c in contexts],['add','replace','remove'])
        self.assertEqual([t.relation for t in final],['includes','processes','stores','reports'])
        self.assertEqual([t.source_sentence_ids for t in final],[['S1'],['S1'],['S2'],['S3']])
        self.assertEqual(self.pipe.last_revision['unresolved_issues'],[])
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
                r['issues']=[issue('R1',[0,1],self.text)]
                bad=self.fact('a module','processes','data','S1');bad['evidence']='fabricated'
                r['replace']=[dict(index=0,issue_id='R1',reason='split',new_triples=[self.fact('The system','includes','a module','S1'),bad]),
                              dict(index=1,issue_id='R1',reason='fix',new_triples=[self.fact('The module','stores','records','S2')])]
            return r
        final, contexts=self.run_flow(respond)
        self.assertEqual(final,self.initial)
        self.assertEqual(contexts[2]['current_collection']['triples'][0]['tail'],self.initial[0].tail)
        self.assertEqual(self.pipe.last_revision['stages'][1]['application']['status'],'rejected_batch')
        self.assertEqual(self.pipe.last_revision['status'],'completed_with_errors')

    def test_invalid_json_preserves_input_and_next_stage_still_runs(self):
        final, contexts=self.run_flow(lambda c: ('not json',0,0,0) if c['stage']=='add' else no_changes(c))
        self.assertEqual(final,self.initial)
        self.assertEqual(len(contexts),3)
        self.assertEqual(self.pipe.last_revision['stages'][0]['raw_response'],'not json')
        self.assertEqual(self.pipe.last_revision['stages'][0]['application']['status'],'failed')

    def test_remove_cannot_delete_its_keep_target(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='remove':
                r['issues']=[issue('D',[1,2],self.text)]
                r['remove']=[dict(index=i,keep_index=j,issue_id='D',reason='duplicate',evidence=self.text) for i,j in [(1,2),(2,1)]]
            return r
        final,_=self.run_flow(respond)
        self.assertEqual(final,self.initial)
        self.assertEqual(self.pipe.last_revision['stages'][2]['application']['status'],'rejected_batch')

    def test_late_replace_request_runs_only_one_bounded_repair_sweep(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='remove' and not c['repair_pass']:
                r['issues']=[issue('D',[1],self.text,'object wrong')]
                r['handoff']=[dict(issue_id='D',target='replace',related_indices=[1],finding='object wrong',evidence=self.text)]
            if c['stage']=='replace' and c['repair_pass']:
                r['issues']=[issue('R',[1],self.text)]
                r['replace']=[dict(index=1,issue_id='R',reason='fix object',new_triples=[self.fact('The module','stores','records','S2')])]
                r['handoff_results']=[dict(issue_id=h['id'],status='resolved',reason='fixed') for h in c['handoff']]
            if c['stage']=='remove' and c['repair_pass']:
                r['handoff_results']=[dict(issue_id=h['id'],status='resolved',reason='fixed') for h in c['handoff']]
            return r
        final,contexts=self.run_flow(respond)
        self.assertEqual([c['stage'] for c in contexts],['add','replace','remove','replace','remove'])
        self.assertEqual(final[1].tail,'records')
        self.assertEqual(self.pipe.snapshots['after_replace'][1].tail,'files')
        self.assertEqual(self.pipe.last_revision['unresolved_issues'],[])

    def test_unresolved_request_does_not_loop(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='remove':
                r['issues']=[issue('D',[0],self.text,'uncertain')]
                r['handoff']=[dict(issue_id='D',target='replace',related_indices=[0],finding='uncertain',evidence=self.text)]
            return r
        _,contexts=self.run_flow(respond)
        self.assertEqual(len(contexts),5)
        self.assertTrue(self.pipe.last_revision['unresolved_issues'])

    def test_wrong_stage_operation_is_rejected(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='add':r['remove']=[{'index':0}]
            return r
        final,_=self.run_flow(respond)
        self.assertEqual(final,self.initial)
        self.assertEqual(self.pipe.last_revision['stages'][0]['application']['status'],'failed')

    def test_new_triple_rejects_missing_sources_and_boolean_scores(self):
        for key,value in [('source_sentence_ids',[]),('source_sentence_ids',['S999']),('confidence',True)]:
            with self.subTest(key=key,value=value):
                item=self.fact('The module','reports','status','S3');item[key]=value
                r=dict(issues=[issue('A',[],self.text)],add=[dict(item,issue_id='A',reason='missing')])
                result,audit=apply_operations('add',self.initial,r,self.sentences)
                self.assertEqual(result,self.initial)
                self.assertEqual(audit['status'],'partial')

    def test_checks_are_declared_for_all_sentences_even_without_differences(self):
        def respond(c):
            r=no_changes(c)
            if c['stage']=='replace':r['reviewed_sentence_ids']=[]
            return r
        final,_=self.run_flow(respond)
        self.assertEqual(final,self.initial)
        self.assertEqual(self.pipe.last_revision['stages'][1]['application']['status'],'failed')

    def test_each_new_replacement_keeps_its_own_evidence_and_score(self):
        children=[self.fact('The system','includes','a module','S1'),self.fact('a module','processes','data','S1')]
        children[1]['confidence']=.7
        r=dict(issues=[issue('R',[0],self.text)],replace=[dict(index=0,issue_id='R',reason='split',new_triples=children)])
        final,audit=apply_operations('replace',self.initial,r,self.sentences)
        self.assertEqual(audit['status'],'applied')
        self.assertEqual([t.confidence for t in final[:2]],[.9,.7])
        self.assertTrue(all(t.evidence==self.sentences[0]['text'] for t in final[:2]))


if __name__ == '__main__':
    unittest.main()
