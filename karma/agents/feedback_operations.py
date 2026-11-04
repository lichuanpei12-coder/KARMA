"""Validate and apply three-step feedback without changing legacy split operations."""
import copy
from karma.core.data_structures import KnowledgeTriple
from karma.core.triple_scores import FIXED_TRIPLE_SCORE


def validate_reply(reply, stage, triples, sentences):
    required = {stage, 'handoff'}
    allowed = required
    if not isinstance(reply, dict) or not required <= reply.keys() or reply.keys() - allowed:
        raise ValueError('Reply must contain only this stage operations and handoff')
    for key in reply:
        if not isinstance(reply[key], list) or any(not isinstance(x, dict) for x in reply[key]):
            raise ValueError(f'{key} must be an array of objects')
    known = {s['sentence_id'] for s in sentences}
    for item in reply['handoff']:
        _text(item, 'problem')
        if item.get('target') not in ('add', 'replace', 'remove', 'text_generation', 'text_comparison', 'review'):
            raise ValueError('Invalid handoff target')
        refs = item.get('indices')
        if not isinstance(refs, list) or any(type(i) is not int or i not in range(len(triples)) for i in refs):
            raise ValueError('Handoff references invalid current indices')
        ids = item.get('source_sentence_ids')
        if not isinstance(ids, list) or not ids or any(not isinstance(s, str) or s not in known for s in ids):
            raise ValueError('Handoff must identify valid source sentences')


def _text(item, key):
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Missing {key}')
    return value.strip()


def _index(value, size):
    if type(value) is not int or not 0 <= value < size:
        raise ValueError('Invalid current index')
    return value


def _triple(item, stage, sentences):
    if not isinstance(item, dict):
        raise ValueError('New triple must be an object')
    spo = {key: _text(item, key) for key in ('head', 'relation', 'tail')}
    evidence = _text(item, 'evidence')
    ids = item.get('source_sentence_ids')
    known = {s['sentence_id']: s['text'] for s in sentences}
    if (not isinstance(ids, list) or len(ids) != 1 or any(not isinstance(s, str) or s not in known for s in ids)):
        raise ValueError('New triple must reference exactly one valid source sentence ID')
    source = known[ids[0]]
    if evidence not in source:
        raise ValueError('Evidence must quote the referenced source sentences verbatim')
    return KnowledgeTriple(**spo, confidence=FIXED_TRIPLE_SCORE, clarity=FIXED_TRIPLE_SCORE,
                           relevance=FIXED_TRIPLE_SCORE, source=f'feedback_{stage}',
                           source_sentence_ids=list(ids), evidence=evidence)


def apply_operations(stage, triples, reply, sentences):
    """No silent deduplication. Replace/remove batches are all-or-nothing."""
    current = copy.deepcopy(triples)
    operations = reply[stage]
    accepted, rejected, prepared = [], [], []
    targets = set()
    for op in operations:
        try:
            _text(op, 'reason')
            if stage == 'add':
                prepared.append((op, None, [_triple(op, stage, sentences)]))
            else:
                index = _index(op.get('index'), len(current))
                if index in targets:
                    raise ValueError('Multiple operations target the same index')
                targets.add(index)
                if stage == 'replace':
                    children = op.get('new_triples')
                    if not isinstance(children, list) or not children:
                        raise ValueError('replace.new_triples must contain at least one triple')
                    prepared.append((op, index, [_triple(c, stage, sentences) for c in children]))
                else:
                    keep = _index(op.get('keep_index'), len(current))
                    if keep == index:
                        raise ValueError('Cannot keep the deleted triple itself')
                    evidence = _text(op, 'evidence')
                    if not any(evidence in s['text'] for s in sentences):
                        raise ValueError('Deletion evidence must quote the source')
                    prepared.append((op, index, keep))
        except (ValueError, TypeError) as exc:
            rejected.append({'operation': stage, 'item': op, 'reason': str(exc)})
    if stage == 'remove':
        deleted = {index for _, index, _ in prepared}
        for op, _, keep in prepared:
            if keep in deleted:
                rejected.append({'operation': stage, 'item': op, 'reason': 'keep_index is also deleted'})
    identity = {i: [i] for i in range(len(current))}
    if rejected and stage in ('replace', 'remove'):
        return current, {'accepted': [], 'rejected': rejected, 'status': 'rejected_batch',
                         'index_map': identity, 'reason': 'Original stage input retained'}

    index_map = {}
    result = []
    modifications = {index: children for _, index, children in prepared if index is not None}
    for i, triple in enumerate(current):
        start = len(result)
        if stage == 'replace' and i in modifications:
            result.extend(modifications[i])
        elif stage != 'remove' or i not in modifications:
            result.append(triple)
        index_map[i] = list(range(start, len(result)))
    if stage == 'add':
        for op, _, children in prepared:
            indices = [len(result)]
            result.extend(children)
            accepted.append({'operation': stage, 'item': op, 'before': None,
                             'after': [x.to_dict() for x in children], 'output_indices': indices})
    else:
        for op, index, children in prepared:
            accepted.append({'operation': stage, 'item': op, 'before': current[index].to_dict(),
                             'after': [x.to_dict() for x in children] if stage == 'replace' else [],
                             'output_indices': index_map[index],
                             'kept_output_index': index_map[children][0] if stage == 'remove' else None})
    return result, {'accepted': accepted, 'rejected': rejected,
                    'status': 'partial' if rejected else 'applied' if accepted else 'no_changes',
                    'index_map': index_map}
