"""Sentence-local feedback with document snapshots and explicit index scopes."""
import copy
from .feedback_pipeline import FeedbackPipeline


def sentence_context(sentence, diff, reconstructions):
    """Whitelist sentence data; never forward global indices or full source text."""
    sid = sentence['sentence_id']
    rows = [r for r in (diff or {}).get('sentence_differences', []) if r.get('sentence_id') == sid]
    row = rows[0] if len(rows) == 1 else {}
    local = {'sentence_id': sid, 'text_a': sentence['text']}
    for key in ('text_b', 'generation_status', 'comparison_status', 'error'):
        if key in row:
            local[key] = copy.deepcopy(row[key])
    for key in ('unique_to_text_a', 'unique_to_text_b'):
        local[key] = copy.deepcopy(row.get(key, [v[len(sid) + 3:] for v in (diff or {}).get(key, [])
                                                  if isinstance(v, str) and v.startswith(f'[{sid}] ')]))
    local.setdefault('comparison_status', 'unavailable')
    recs = [{k: copy.deepcopy(r[k]) for k in ('sentence_id', 'text_b', 'generation_status', 'error') if k in r}
            for r in (reconstructions or []) if r.get('sentence_id') == sid]
    return {**{k: local[k] for k in ('unique_to_text_a', 'unique_to_text_b')},
            'sentence_differences': [local]}, recs


class SentenceFeedbackPipeline:
    def __init__(self, add_agent, replace_agent, remove_agent):
        self.agents = (add_agent, replace_agent, remove_agent)
        self.snapshots = {}
        self.last_revision = {}

    def process(self, text, triples, diff, entities=None, *, sentences, reconstructions=None):
        ids = [s['sentence_id'] for s in sentences]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate source sentence IDs')
        unsafe = [i for i, t in enumerate(triples)
                  if len(t.source_sentence_ids) != 1 or t.source_sentence_ids[0] not in ids]
        if unsafe:
            raise ValueError(f'Sentence feedback requires one valid source sentence per triple; invalid indices: {unsafe}')
        self.snapshots = {key: [] for key in ('after_add', 'after_replace', 'after_remove')}
        final, runs, stages = [], [], []
        mappings = {key: [] for key in (*self.snapshots, 'after_revision')}
        logs = {key: [] for key in ('handoff_log', 'undelivered_issues', 'review_issues', 'unverified_issues')}
        for sentence in sentences:
            sid = sentence['sentence_id']
            origins = [i for i, t in enumerate(triples) if t.source_sentence_ids == [sid]]
            selected = [copy.deepcopy(triples[i]) for i in origins]
            local_diff, local_recon = sentence_context(sentence, diff, reconstructions)
            local_entities = [e for e in (entities or [])
                              if any(n and n in sentence['text'] for n in [e.name, *getattr(e, 'aliases', [])])]
            worker = FeedbackPipeline(*self.agents)
            result = worker.process(sentence['text'], selected, local_diff, local_entities,
                                    sentences=[sentence], reconstructions=local_recon, scope='sentence')
            audit = copy.deepcopy(worker.last_revision)
            for record in audit['stages']:
                record['local_pass_id'] = record['pass_id']
                record['pass_id'] = f"{sid}_{record['pass_id']}"
                record['sentence_id'] = sid
                record['index_scope'] = 'sentence'
            stages.extend(audit['stages'])
            for key in logs:
                logs[key].extend(dict(copy.deepcopy(item), sentence_id=sid) for item in audit[key])
            for key, snapshot in worker.snapshots.items():
                offset = len(self.snapshots[key])
                self.snapshots[key].extend(copy.deepcopy(snapshot))
                mappings[key].extend(dict(sentence_id=sid, local_index=i, global_index=offset+i)
                                     for i in range(len(snapshot)))
            offset = len(final)
            final.extend(result)
            mappings['after_revision'].extend(dict(sentence_id=sid, local_index=i, global_index=offset+i)
                                              for i in range(len(result)))
            runs.append(dict(sentence_id=sid, initial_index_map=dict(enumerate(origins)),
                             snapshots={k: [t.to_dict() for t in v] for k, v in worker.snapshots.items()},
                             final=[t.to_dict() for t in result], audit=audit))
        self.last_revision = dict(mode='three_step_feedback', protocol='sentence_feedback_v1', scope='sentence',
                                  requested_scope='sentence', score_policy='fixed_0.8', stages=stages,
                                  sentence_runs=runs, snapshot_index_maps=mappings, **logs,
                                  resolution_policy='delivery_does_not_confirm_semantic_resolution',
                                  baseline_count=len(triples), final_count=len(final),
                                  status='completed_with_errors' if any(r['audit']['status'] != 'completed' for r in runs)
                                  else 'completed')
        return final
