"""Lexical ranking, atomic Remove corrections and current-version integration."""
import copy
import json
import re
import unittest
from unittest.mock import patch

from evaluation_common import pair_details
from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.feedback_replace.agent import FeedbackReplaceAgent
from karma.agents.feedback_remove.agent import FeedbackRemoveAgent
from karma.agents.feedback_operations import apply_operations, validate_reply
from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KnowledgeTriple
from karma.core.feedback_pipeline import FeedbackPipeline
from karma.core.sentence_feedback_pipeline import SentenceFeedbackPipeline
from karma.core.triple_overlap import rank_triple_overlap
from feedback_fixtures import context_from_prompt, no_changes


def triple(head='the module', relation='stores', tail='data', sid='S1'):
    return KnowledgeTriple(head, relation, tail, source_sentence_ids=[sid])


class OverlapTests(unittest.TestCase):
    def test_matches_evaluation_word_counts_when_fields_align(self):
        a, b = triple('The module module'), triple('the module')
        row = rank_triple_overlap([a, b], 'V2')['pairs'][0]
        evaluation = pair_details(a.to_dict(), b.to_dict(), 'lenient')
        self.assertAlmostEqual(row['overlap_f1'], evaluation['f1'])
        self.assertAlmostEqual(row['left_containment'], evaluation['recall'])
        self.assertAlmostEqual(row['right_containment'], evaluation['precision'])
        self.assertEqual(row['left_only_words'], {'module': 1})

    def test_whole_triple_overlap_keeps_role_changes_visible_for_review(self):
        a, b = triple('Alpha', 'controls', 'Beta'), triple('Beta', 'controls', 'Alpha')
        row = rank_triple_overlap([a, b], 'V2')['pairs'][0]
        self.assertEqual(row['overlap_f1'], 1)
        self.assertEqual(pair_details(a.to_dict(), b.to_dict(), 'lenient')['f1'], 0)

    def test_all_pairs_retained_and_rankings_are_independent(self):
        triples = [triple(words, '', '') for words in
                   ('a b', 'a b c d e f g h', 'a b c', 'a c d', 'z')]
        result = rank_triple_overlap(triples, 'V5')
        rows = {tuple(row['indices']): row for row in result['pairs']}
        self.assertEqual(len(rows), 10)
        self.assertEqual(result['basis_version'], 'V5')
        self.assertEqual(rows[0, 4]['overlap_f1'], 0)
        self.assertGreater(rows[0, 1]['overall_rank'], rows[2, 3]['overall_rank'])
        self.assertLess(rows[0, 1]['containment_rank'], rows[2, 3]['containment_rank'])
        self.assertEqual(rows[0, 1]['containment_rank'], rows[0, 2]['containment_rank'])
        self.assertEqual(result, rank_triple_overlap(triples, 'V5'))

    def test_empty_single_and_empty_text_inputs(self):
        for triples in ([], [triple()]):
            self.assertEqual(rank_triple_overlap(triples, 'V0')['pairs'], [])
        row = rank_triple_overlap([triple('', '', ''), triple()], 'V0')['pairs'][0]
        self.assertEqual(row['left_containment'], 0)
        self.assertEqual(row['right_containment'], 0)


class RemoveOperationsTests(unittest.TestCase):
    def setUp(self):
        self.sentences = [{'sentence_id': 'S1', 'text': 'The module stores data.'}]
        self.triples = [triple(tail=str(i)) for i in range(4)]
        self.reply = {'replace': [{'index': 3, 'reason': 'unify', 'new_triples': [triple().to_dict()]}],
                      'remove': [{'index': 0, 'keep_index': 3, 'reason': 'same fact'}], 'handoff': []}

    def test_replacement_and_deletion_share_input_indices(self):
        before = copy.deepcopy(self.triples)
        validate_reply(self.reply, 'remove', self.triples, self.sentences)
        result, audit = apply_operations('remove', self.triples, self.reply, self.sentences)
        self.assertEqual(audit['status'], 'applied')
        self.assertEqual(audit['index_map'], {0: [], 1: [0], 2: [1], 3: [2]})
        self.assertEqual(result[2].tail, 'data')
        self.assertEqual(result[2].source, 'feedback_remove')
        self.assertEqual([op['operation'] for op in audit['accepted']], ['replace', 'remove'])
        self.assertEqual(audit['accepted'][1]['kept_output_index'], 2)
        self.assertEqual(self.triples, before)

    def test_invalid_mixed_batch_rolls_back_both_operations(self):
        bad_source = copy.deepcopy(self.reply)
        bad_source['replace'][0]['new_triples'][0]['source_sentence_ids'] = ['S99']
        overlapping_target = copy.deepcopy(self.reply)
        overlapping_target['replace'][0]['index'] = 0
        deleted_keep = copy.deepcopy(self.reply)
        deleted_keep['remove'].append({'index': 3, 'keep_index': 2, 'reason': 'duplicate'})
        expansion = copy.deepcopy(self.reply)
        expansion['replace'][0]['new_triples'].append(triple().to_dict())
        for reply in (bad_source, overlapping_target, deleted_keep, expansion):
            with self.subTest(reply=reply):
                result, audit = apply_operations('remove', self.triples, reply, self.sentences)
                self.assertEqual(result, self.triples)
                self.assertEqual(audit['status'], 'rejected_batch')
                self.assertEqual(audit['accepted'], [])
                self.assertEqual(audit['index_map'], {i: [i] for i in range(4)})

    def test_remove_protocol_accepts_replacement_but_not_addition(self):
        with self.assertRaises(ValueError):
            validate_reply(dict(self.reply, add=[]), 'remove', self.triples, self.sentences)
        validate_reply({'remove': [], 'handoff': []}, 'remove', self.triples, self.sentences)

    def test_all_remove_examples_execute_and_preserve_outer_qualifiers(self):
        agent = FeedbackRemoveAgent(None, 'offline')
        cases = re.findall(r'输入：(\{[^\n]+\})\n输出：(\{[^\n]+\})', agent.examples_prompt)
        self.assertEqual(len(cases), 3)
        for raw_input, raw_output in cases:
            context, reply = json.loads(raw_input), json.loads(raw_output)
            triples = [KnowledgeTriple.from_dict(t) for t in context['current_collection']['triples']]
            validate_reply(reply, 'remove', triples, context['source_sentences'])
            result, audit = apply_operations('remove', triples, reply, context['source_sentences'])
            self.assertEqual(audit['status'], 'applied')
            if 'workstations' in raw_input:
                self.assertEqual(len(result), 4)
                self.assertEqual(result[0].head, 'the workstations')
                self.assertEqual(result[1:], triples[2:])


class RemoveIntegrationTests(unittest.TestCase):
    def agents(self):
        return FeedbackAddAgent(None, 'offline'), FeedbackReplaceAgent(None, 'offline'), FeedbackRemoveAgent(None, 'offline')

    def test_rankings_refresh_after_merge_and_handoff_uses_updated_indices(self):
        pipeline = FeedbackPipeline(*self.agents())
        seen = []
        def call(agent, prompt, **kwargs):
            context = context_from_prompt(prompt)
            seen.append(context)
            reply = no_changes(context)
            if context['stage'] == 'remove' and not context['repair_pass']:
                reply['replace'] = [{'index': 1, 'reason': 'unify', 'new_triples': [triple().to_dict()]}]
                reply['remove'] = [{'index': 0, 'keep_index': 1, 'reason': 'duplicate'}]
                reply['handoff'] = [{'target': 'replace', 'indices': [1], 'source_sentence_ids': ['S1'], 'problem': 'check wording'}]
            return json.dumps(reply), 0, 0, 0
        with patch.object(BaseAgent, '_make_llm_call', new=call):
            result = pipeline.process('The module stores data.', [triple(), triple()], {},
                                      sentences=[{'sentence_id': 'S1', 'text': 'The module stores data.'}])
        self.assertEqual(len(result), 1)
        removes = [c for c in seen if c['stage'] == 'remove']
        self.assertEqual(len(removes[0]['lexical_overlap']['pairs']), 1)
        self.assertEqual(removes[1]['lexical_overlap']['pairs'], [])
        for context in removes:
            self.assertEqual(context['lexical_overlap']['basis_version'], context['current_collection']['version'])
        repair = next(c for c in seen if c['stage'] == 'replace' and c['repair_pass'])
        self.assertEqual(repair['handoff'][0]['indices'], [0])
        self.assertTrue(all('lexical_overlap' not in c for c in seen if c['stage'] != 'remove'))
        self.assertEqual(pipeline.last_revision['stages'][2]['application']['accepted'][0]['operation'], 'replace')

    def test_sentence_local_ranking_and_no_automatic_deletion(self):
        pipeline = SentenceFeedbackPipeline(*self.agents())
        seen = []
        def call(agent, prompt, **kwargs):
            context = context_from_prompt(prompt)
            seen.append(context)
            return json.dumps(no_changes(context)), 0, 0, 0
        sentences = [{'sentence_id': sid, 'text': 'The module stores data.'} for sid in ('S1', 'S2')]
        with patch.object(BaseAgent, '_make_llm_call', new=call):
            result = pipeline.process('The module stores data. The module stores data.',
                                      [triple(), triple(), triple(sid='S2')], {}, sentences=sentences)
        removes = [c for c in seen if c['stage'] == 'remove']
        self.assertEqual(removes[0]['lexical_overlap']['pairs'][0]['indices'], [0, 1])
        self.assertEqual(removes[1]['lexical_overlap']['pairs'], [])
        self.assertEqual(len(result), 3)


if __name__ == '__main__':
    unittest.main()
