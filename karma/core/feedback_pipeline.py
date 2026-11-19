"""Sequential Add -> Replace -> Remove feedback with explicit stage snapshots."""
import copy
import time
from karma.agents.feedback_operations import apply_operations, validate_reply
from karma.core.triple_scores import fixed_score_copy, prompt_triple
from karma.core.triple_overlap import rank_triple_overlap


def _fact(data):
    if data is None:
        return None
    return {k: v for k, v in data.items() if k in
            ('head', 'relation', 'tail', 'source_sentence_ids')}


class FeedbackPipeline:
    def __init__(self, add_agent, replace_agent, remove_agent):
        self.agents = {'add': add_agent, 'replace': replace_agent, 'remove': remove_agent}
        self.last_revision = {}
        self.snapshots = {}

    def process(self, text, triples, diff, entities=None, *, sentences, reconstructions=None, scope='document'):
        current = fixed_score_copy(triples)
        self.snapshots = {}
        history, stages, failures = [], [], []
        comparison = {'basis_version': 'V0', 'source_text': text,
                      'diff': copy.deepcopy(diff), 'reconstructions': copy.deepcopy(reconstructions or [])}
        version = 'V0'

        for stage in self.agents:
            pass_id = f'{len(stages) + 1}_{stage}'
            input_version = version
            indexed = [dict(index=i, **prompt_triple(t)) for i, t in enumerate(current)]
            changes = [{'stage': h['stage'], 'changes': [
                {'operation': a['operation'], 'before': _fact(a['before']),
                 'after': [_fact(t) for t in a['after']]}
                for a in h['accepted']],
                'failures': [r['reason'] for r in h['rejected']], 'status': h['status']}
                for h in history]
            context = {
                'stage': stage,
                'source_sentences': copy.deepcopy(sentences),
                'current_collection': {'version': version, 'triples': indexed},
                'sentence_index': {s['sentence_id']: [i for i, t in enumerate(current)
                                   if s['sentence_id'] in t.source_sentence_ids] for s in sentences},
                'unassigned_indices': [i for i, t in enumerate(current) if not t.source_sentence_ids],
                'comparison_bundle': comparison,
                'candidate_entities': [{'mention': e.name} for e in (entities or [])],
                'applied_change_log': changes,
            }
            if stage == 'remove':
                context['lexical_overlap'] = rank_triple_overlap(current, version)
            agent = self.agents[stage]
            agent.last_call = {}
            reply = None
            started = time.perf_counter()
            before = [t.to_dict() for t in current]
            try:
                reply = agent.process(context)
                validate_reply(reply, stage, current, sentences)
                revised, application = apply_operations(stage, current, reply, sentences)
            except Exception as exc:
                revised = copy.deepcopy(current)
                application = {'status': 'failed', 'reason': str(exc), 'accepted': [], 'rejected': [],
                               'index_map': {i: [i] for i in range(len(current))}}
            version = f'V{len(stages) + 1}'
            record = {'pass_id': pass_id, 'stage': stage,
                      'input_version': input_version, 'output_version': version,
                      'input': before, 'context': copy.deepcopy(context),
                      **copy.deepcopy(getattr(agent, 'last_call', {})),
                      'reply': copy.deepcopy(reply), 'application': application,
                      'output': [t.to_dict() for t in revised],
                      'elapsed': time.perf_counter() - started}
            stages.append(record)
            if application['status'] in ('failed', 'rejected_batch', 'partial'):
                failures.append({'pass_id': pass_id, 'stage': stage,
                                 'reason': application.get('reason'), 'rejected': copy.deepcopy(application['rejected'])})
            current = revised
            history.append({'stage': stage, 'pass_id': pass_id, 'input_version': input_version, 'output_version': version,
                            **copy.deepcopy(application)})
            self.snapshots[f'after_{stage}'] = copy.deepcopy(current)

        self.last_revision = {'mode': 'three_step_feedback', 'protocol': 'direct_operations_v1',
                              'scope': scope, 'score_policy': 'fixed_0.8', 'stages': stages,
                              'review_issues': failures,
                              'baseline_count': len(triples), 'final_count': len(current),
                              'status': 'completed_with_errors' if failures else 'completed'}
        return current
