"""Sequential Add -> Replace -> Remove feedback with explicit stage snapshots."""
import copy
import time
from karma.agents.feedback_operations import apply_operations, validate_reply


class FeedbackPipeline:
    def __init__(self, add_agent, replace_agent, remove_agent):
        self.agents = {'add': add_agent, 'replace': replace_agent, 'remove': remove_agent}
        self.last_revision = {}
        self.snapshots = {}

    def process(self, text, triples, diff, entities=None, *, sentences, reconstructions=None):
        current = copy.deepcopy(triples)
        self.snapshots = {}
        history, pending, stages = [], [], []
        comparison = {'basis_version': 'V0', 'source_text': text,
                      'diff': copy.deepcopy(diff), 'reconstructions': copy.deepcopy(reconstructions or [])}
        version = 'V0'

        def run(stage, repair=False):
            nonlocal current, version, pending
            pass_id = f'{len(stages) + 1}_{stage}'
            input_version = version
            indexed = [dict(index=i, **t.to_dict()) for i, t in enumerate(current)]
            context = {
                'stage': stage, 'repair_pass': repair,
                'source_sentences': copy.deepcopy(sentences),
                'current_collection': {'version': version, 'triples': indexed},
                'sentence_index': {s['sentence_id']: [i for i, t in enumerate(current)
                                   if s['sentence_id'] in t.source_sentence_ids] for s in sentences},
                'unassigned_indices': [i for i, t in enumerate(current) if not t.source_sentence_ids],
                'comparison_bundle': comparison,
                'candidate_entities': [{'mention': e.name} for e in (entities or [])],
                'applied_change_log': copy.deepcopy(history),
                'handoff': copy.deepcopy(pending),
            }
            agent = self.agents[stage]
            agent.last_call = {}
            reply = None
            started = time.perf_counter()
            before = [t.to_dict() for t in current]
            try:
                reply = agent.process(context)
                validate_reply(reply, stage, current, sentences)
                known = {p['id'] for p in pending}
                reported = [r.get('issue_id') for r in reply['handoff_results']]
                if len(reported) != len(set(reported)) or set(reported) != known:
                    raise ValueError('handoff_results must address every received issue exactly once')
                revised, application = apply_operations(stage, current, reply, sentences)
            except Exception as exc:
                revised = copy.deepcopy(current)
                application = {'status': 'failed', 'reason': str(exc), 'accepted': [], 'rejected': [],
                               'index_map': {i: [i] for i in range(len(current))}}
            version = f'V{len(stages) + 1}'
            record = {'pass_id': pass_id, 'stage': stage, 'repair_pass': repair,
                      'input_version': input_version, 'output_version': version,
                      'input': before, 'context': copy.deepcopy(context),
                      **copy.deepcopy(getattr(agent, 'last_call', {})),
                      'reply': copy.deepcopy(reply), 'application': application,
                      'output': [t.to_dict() for t in revised],
                      'elapsed': time.perf_counter() - started}
            stages.append(record)
            valid = application['status'] not in ('failed', 'rejected_batch')
            if valid:
                rejected_issues = {r['item'].get('issue_id') for r in application['rejected']}
                accepted_issues = {a['item'].get('issue_id') for a in application['accepted']}
                for answer in reply['handoff_results']:
                    item = next(p for p in pending if p['id'] == answer['issue_id'])
                    item['last_assessment'] = copy.deepcopy(answer)
                    # Rejected operations must not silently close an upstream issue.
                    item['status'] = answer['status'] if not application['rejected'] else 'still_open'
                for issue in reply['handoff']:
                    pending.append({**copy.deepcopy(issue), 'id': f'{pass_id}:{issue["issue_id"]}:{len(pending)}',
                                    'origin_version': input_version,
                                    'origin_indices': list(issue['related_indices']), 'status': 'still_open'})
                # Keep unapplied operation problems visible even if the model forgot to hand them off.
                for issue in reply['issues']:
                    if issue['issue_id'] in rejected_issues - accepted_issues:
                        pending.append({'id': f'{pass_id}:rejected:{issue["issue_id"]}', 'target': stage,
                                        'finding': issue['finding'], 'evidence': issue.get('evidence', ''),
                                        'related_indices': issue['related_indices'], 'origin_indices': issue['related_indices'],
                                        'origin_version': input_version, 'status': 'still_open'})
            else:
                pending.append({'id': f'{pass_id}:failure', 'target': 'review',
                                'related_indices': [], 'origin_indices': [], 'origin_version': input_version,
                                'finding': f'{stage} did not apply: {application.get("reason", "invalid batch")}',
                                'status': 'still_open', 'evidence': ''})
            for item in pending:
                refs = item.get('related_indices', [])
                item['related_indices'] = sorted({j for i in refs for j in application['index_map'].get(i, [])})
                item['current_version'] = version
                if refs and not item['related_indices']:
                    item['referenced_items_removed'] = True
            current = revised
            history.append({'pass_id': pass_id, 'input_version': input_version, 'output_version': version,
                            **copy.deepcopy(application)})
            if not repair:
                self.snapshots[f'after_{stage}'] = copy.deepcopy(current)

        for stage in ('add', 'replace', 'remove'):
            run(stage)
        # At most one repair sweep, only for explicitly unresolved Add/Replace work.
        repair_targets = {p['target'] for p in pending if p['status'] in ('still_open', 'uncertain')}
        if repair_targets & {'add', 'replace'}:
            if 'add' in repair_targets:
                run('add', True)
            run('replace', True)
            run('remove', True)
        self.last_revision = {'mode': 'three_step_feedback', 'stages': stages,
                              'pending_issues': pending,
                              'unresolved_issues': [p for p in pending if p['status'] not in ('resolved', 'disagreed')],
                              'baseline_count': len(triples), 'final_count': len(current),
                              'status': 'completed_with_errors' if any(s['application']['status'] in
                                  ('failed', 'rejected_batch', 'partial') for s in stages) else 'completed'}
        return current
