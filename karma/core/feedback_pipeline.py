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
        history, pending, stages = [], [], []
        comparison = {'basis_version': 'V0', 'source_text': text,
                      'diff': copy.deepcopy(diff), 'reconstructions': copy.deepcopy(reconstructions or [])}
        version = 'V0'

        def run(stage, repair=False):
            nonlocal current, version, pending
            pass_id = f'{len(stages) + 1}_{stage}'
            input_version = version
            indexed = [dict(index=i, **prompt_triple(t)) for i, t in enumerate(current)]
            received = [p for p in pending if p['target'] == stage
                        and p['delivery_status'] in ('queued', 'delivery_failed')]
            # Historical IDs and complete execution records stay in the audit.
            hints = [{k: copy.deepcopy(p[k]) for k in ('indices', 'source_sentence_ids', 'problem')}
                     for p in received]
            changes = [{'stage': h['stage'], 'changes': [
                {'operation': a['operation'], 'before': _fact(a['before']),
                 'after': [_fact(t) for t in a['after']]}
                for a in h['accepted']],
                'failures': [r['reason'] for r in h['rejected']], 'status': h['status']}
                for h in history]
            context = {
                'stage': stage, 'repair_pass': repair,
                'source_sentences': copy.deepcopy(sentences),
                'current_collection': {'version': version, 'triples': indexed},
                'sentence_index': {s['sentence_id']: [i for i, t in enumerate(current)
                                   if s['sentence_id'] in t.source_sentence_ids] for s in sentences},
                'unassigned_indices': [i for i, t in enumerate(current) if not t.source_sentence_ids],
                'comparison_bundle': comparison,
                'candidate_entities': [{'mention': e.name} for e in (entities or [])],
                'applied_change_log': changes,
                'handoff': hints,
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
            record = {'pass_id': pass_id, 'stage': stage, 'repair_pass': repair,
                      'input_version': input_version, 'output_version': version,
                      'received_handoff_ids': [p['id'] for p in received],
                      'input': before, 'context': copy.deepcopy(context),
                      **copy.deepcopy(getattr(agent, 'last_call', {})),
                      'reply': copy.deepcopy(reply), 'application': application,
                      'output': [t.to_dict() for t in revised],
                      'elapsed': time.perf_counter() - started}
            stages.append(record)
            valid = application['status'] not in ('failed', 'rejected_batch')
            for item in received:
                # This records delivery/execution, never semantic resolution.
                item['delivery_status'] = 'delivered' if valid else 'delivery_failed'
                item['delivery_attempts'].append({'pass_id': pass_id, 'application_status': application['status']})
            if valid:
                for issue in reply['handoff']:
                    pending.append({**{k: copy.deepcopy(issue[k]) for k in
                                       ('target', 'source_sentence_ids', 'indices', 'problem')},
                                    'id': f'{pass_id}:H{len(pending)}',
                                    'origin_version': input_version,
                                    'origin_indices': list(issue['indices']),
                                    'delivery_status': 'queued' if issue['target'] in self.agents else 'needs_review',
                                    'semantic_status': 'unverified', 'delivery_attempts': []})
            if not valid or application['rejected']:
                pending.append({'id': f'{pass_id}:failure', 'target': 'review',
                                'indices': [], 'origin_indices': [], 'origin_version': input_version,
                                'source_sentence_ids': [],
                                'problem': f'{stage} has unapplied operations: {application.get("reason", application["rejected"])}',
                                'delivery_status': 'needs_review', 'semantic_status': 'unverified', 'delivery_attempts': []})
            for item in pending:
                refs = item.get('indices', [])
                item['indices'] = sorted({j for i in refs for j in application['index_map'].get(i, [])})
                item['current_version'] = version
                if refs and not item['indices']:
                    item['referenced_items_removed'] = True
            current = revised
            history.append({'stage': stage, 'pass_id': pass_id, 'input_version': input_version, 'output_version': version,
                            **copy.deepcopy(application)})
            if not repair:
                self.snapshots[f'after_{stage}'] = copy.deepcopy(current)

        for stage in ('add', 'replace', 'remove'):
            run(stage)
        # At most one repair sweep, for Add/Replace hints not yet delivered successfully.
        repair_targets = {p['target'] for p in pending if p['delivery_status'] in ('queued', 'delivery_failed')}
        if repair_targets & {'add', 'replace'}:
            if 'add' in repair_targets:
                run('add', True)
            run('replace', True)
            run('remove', True)
        self.last_revision = {'mode': 'three_step_feedback', 'protocol': 'task_outputs_v4', 'scope': scope, 'score_policy': 'fixed_0.8', 'stages': stages,
                              'handoff_log': pending,
                              'undelivered_issues': [p for p in pending if p['delivery_status'] in ('queued', 'delivery_failed')],
                              'review_issues': [p for p in pending if p['delivery_status'] == 'needs_review'],
                              'unverified_issues': copy.deepcopy(pending),
                              'resolution_policy': 'delivery_does_not_confirm_semantic_resolution',
                              'baseline_count': len(triples), 'final_count': len(current),
                              'status': 'completed_with_errors' if any(s['application']['status'] in
                                  ('failed', 'rejected_batch', 'partial') for s in stages) else 'completed'}
        return current
