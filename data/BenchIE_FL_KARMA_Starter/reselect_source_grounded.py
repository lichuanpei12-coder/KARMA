"""Build a conservative, source-span-based BenchIE subset; never call a model.

Default: dry-run statistics. Use --apply for the mechanical JSON transformation.
This is lexical/syntactic evidence checking, not a proof of semantic entailment.
"""
import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ('head', 'relation', 'tail')
WORD = re.compile(r"\w+", re.UNICODE)
# Do not drop these operators between the selected subject and object.
SCOPE = set('not no never neither nor without only unless except if whether '
            'may might can could must shall should will would cannot '
            'before after until since because although despite '
            'first second third last least most less more nearly almost '
            'approximately about over under up down off out'.split())
CONTEXT = set('if unless whether said says say reported reportedly allegedly '
              'claimed claims claim believed believes believe thought thinks think '
              'denied denies deny suspected suspects suspect suggested suggests '
              'suggest feared fears fear when stated states told noted accused '
              'expected expects hoped hopes suspected ruled asks asked believes'.split())
PARTICLE_ONLY = set('up down off out in on at to of for from with by as into onto'.split())
HEAD_SCOPE = set('not no never neither nor without only unless except if whether '
                 'may might can could must shall should will would cannot '
                 'able necessary attempt attempts attempted intended designed '
                 'aim aims aiming try tries trying tried'.split())
# Explicitly reviewed defects: mere token occurrence is insufficient evidence.
REVIEW_EXCLUSIONS = {
    ('benchie_3', 8): 'United Nations trade sanctions cannot be shortened to the organization United Nations.',
    ('benchie_16', 4): 'a classical liberal truncates classical liberal/libertarian think tank and changes the referent type.',
    ('benchie_17', 3): 'support is a noun in its support, not an asserted verb of this adoption.',
    ('benchie_40', 1): 'Dropping When the band is not touring removes the condition.',
    ('benchie_58', 1): 'Dropping For patients who do not recover quickly removes the patient restriction.',
    ('benchie_194', 4): 'medical training with is a noun phrase, not an asserted predicate.',
    ('benchie_212', 3): 'a federal is an incomplete noun phrase after removing organization.',
}


def tokens(text):
    return [m.group().casefold() for m in WORD.finditer(text)]


def parse_source():
    docs = []
    current = cluster = None
    for line_no, line in enumerate(
            (ROOT / 'benchie-annotated_300.txt').read_text(encoding='utf-8').splitlines(), 1):
        if line.startswith('sent_id:'):
            identity, sentence = line.split('\t', 1)
            current = {'id': 'benchie_' + identity.split(':', 1)[1],
                       'sentence': sentence, 'source_line': line_no, 'clusters': []}
            docs.append(current)
            cluster = None
        elif re.match(r'^\d+--> Cluster ', line):
            cluster = {'label': line, 'source_line': line_no, 'rows': []}
            current['clusters'].append(cluster)
        elif line.count('-->') == 2:
            if cluster is None:
                cluster = {'label': 'implicit cluster', 'source_line': line_no, 'rows': []}
                current['clusters'].append(cluster)
            cluster['rows'].append({'source_line': line_no,
                                    'fields': [s.strip() for s in line.split('-->')]})
    return docs


def span_matches(annotation, source_words):
    """Match whole optional bracket groups to contiguous source word spans."""
    segments = []
    for part in re.split(r'(\[[^\]]*\])', annotation):
        optional = part.startswith('[') and part.endswith(']')
        words = tokens(part[1:-1] if optional else part)
        if words:
            segments.append((words, optional))
    matches = set()
    for start in range(len(source_words)):
        ends = {start}
        for words, optional in segments:
            next_ends = set(ends) if optional else set()
            for end in ends:
                if source_words[end:end + len(words)] == words:
                    next_ends.add(end + len(words))
            ends = next_ends
            if not ends:
                break
        matches.update((start, end) for end in ends if end > start)
    return sorted(matches)


def build():
    old_input_text = (ROOT / 'input.json').read_text(encoding='utf-8')
    old_gold_text = (ROOT / 'gold.json').read_text(encoding='utf-8')
    old_input, old_gold = json.loads(old_input_text), json.loads(old_gold_text)
    # Preserve the first pre-reselection snapshot if this script is rerun.
    backup = ROOT / 'before_source_grounded'
    if (backup / 'input.json').exists():
        old_input = json.loads((backup / 'input.json').read_text(encoding='utf-8'))
    baseline_gold = json.loads((backup / 'gold.json').read_text(encoding='utf-8')) if (backup / 'gold.json').exists() else old_gold
    inputs, golds, audit = {}, {}, []
    reasons = Counter()
    duplicate_count = 0
    for doc in parse_source():
        sentence = doc['sentence']
        offsets = list(WORD.finditer(sentence))
        words = [m.group().casefold() for m in offsets]
        kept = []
        seen = {}
        for cluster_no, cluster in enumerate(doc['clusters'], 1):
            candidates = []
            rejects = Counter()
            for row_no, row in enumerate(cluster['rows'], 1):
                if (doc['id'], cluster_no) in REVIEW_EXCLUSIONS:
                    rejects['manual_semantic_exclusion'] += 1
                    continue
                if any('XXX' in field for field in row['fields']):
                    rejects['XXX_placeholder'] += 1
                    continue
                if set(tokens(row['fields'][2])) <= PARTICLE_ONLY:
                    rejects['particle_only_object'] += 1
                    continue
                matches = [span_matches(field, words) for field in row['fields']]
                if not all(matches):
                    rejects['field_not_a_source_span'] += 1
                    continue
                ordered = scoped = False
                for spans in itertools.product(*matches):
                    h, r, t = spans
                    if not (h[1] <= r[0] and r[1] <= t[0]):
                        continue
                    ordered = True
                    # Conservative boundary: do not jump from a predicate to an
                    # arbitrary later object (e.g. 'was re-elected' -> 'was').
                    if r[1] != t[0]:
                        rejects['nonadjacent_relation_object'] += 1
                        continue
                    selected = set(i for a, b in spans for i in range(a, b))
                    missing = [i for i in range(h[0], t[1]) if i not in selected]
                    # Protect scope/degree/quantity, including contractions such as n't.
                    if any((words[i] in (SCOPE if i >= r[0] else HEAD_SCOPE)) or
                           (i >= r[0] and words[i].isdigit()) or
                           (words[i] == 't' and i and words[i-1].endswith('n'))
                           for i in missing):
                        continue
                    # Avoid presenting a reported/conditional proposition as a fact.
                    if any(words[i] in CONTEXT and i not in selected for i in range(r[0])):
                        rejects['omitted_report_or_condition'] += 1
                        continue
                    if any(words[i] in {'if', 'unless', 'whether'} and i not in selected
                           for i in range(len(words))):
                        rejects['omitted_conditional_scope'] += 1
                        continue
                    if t[1] < len(words) and words[t[1]] in {'until', 'unless', 'if', 'except'}:
                        rejects['truncated_conditional_or_temporal_scope'] += 1
                        continue
                    if h[0] and words[h[0]-1] in {'no', 'not', 'few', 'neither', 'only', 'most', 'all'}:
                        rejects['dropped_subject_quantifier'] += 1
                        continue
                    scoped = True
                    char_spans = []
                    for field, (a, b) in zip(FIELDS, spans):
                        start, end = offsets[a].start(), offsets[b-1].end()
                        if field != 'relation':
                            opening = re.search(r'(?:``|["“])\s*$', sentence[:start])
                            closing = re.match(r'\s*(?:\'\'|["”])', sentence[end:])
                            if opening: start = opening.start()
                            if closing: end += closing.end()
                            if words[a].isdigit():
                                currency = re.search(r'[$£€¥]\s*$', sentence[:start])
                                if currency: start = currency.start()
                            if words[b-1].isdigit():
                                percent = re.match(r'\s*%', sentence[end:])
                                if percent: end += percent.end()
                        char_spans.append((start, end))
                    values = [sentence[a:b] for a, b in char_spans]
                    # More source words and fewer gaps preserve the fuller claim.
                    # Tie-breaks favor the shorter predicate, then original row order.
                    score = (len(selected), -len(missing), -(r[1]-r[0]), -row_no,
                             -h[0], -r[0], -t[0])
                    candidates.append((score, dict(zip(FIELDS, values)), spans, row, char_spans))
                if not ordered:
                    rejects['source_order_or_argument_overlap'] += 1
                elif not scoped:
                    rejects['dropped_scope_or_quantity'] += 1
            entry = {'sample_id': doc['id'], 'cluster_ordinal': cluster_no,
                     'original_cluster_label': cluster['label'],
                     'cluster_source_line': cluster['source_line'], 'sentence': sentence,
                     'rejected_row_counts': dict(rejects)}
            if (doc['id'], cluster_no) in REVIEW_EXCLUSIONS:
                entry['manual_review_reason'] = REVIEW_EXCLUSIONS[(doc['id'], cluster_no)]
            if candidates:
                _, triple, spans, row, char_spans = max(candidates, key=lambda c: c[0])
                signature = tuple(tokens(triple[f]) for f in FIELDS)
                signature = tuple(tuple(x) for x in signature)
                if signature in seen:
                    entry.update(status='duplicate', same_as_cluster=seen[signature], triple=triple)
                    duplicate_count += 1
                else:
                    seen[signature] = cluster_no
                    kept.append(triple)
                    evidence = {}
                    for field, (a, b), (start, end) in zip(FIELDS, spans, char_spans):
                        evidence[field] = {'word_start': a, 'word_end_exclusive': b,
                                           'char_start': start,
                                           'char_end_exclusive': end}
                    entry.update(status='kept', triple=triple, evidence=evidence,
                                 selected_annotation=row['fields'],
                                 selected_annotation_line=row['source_line'])
            else:
                reason = ('XXX_only' if rejects and set(rejects) == {'XXX_placeholder'} else
                          'no_source_grounded_candidate')
                entry.update(status='removed', reason=reason)
                reasons[reason] += 1
            audit.append(entry)
        # Empty after filtering does not imply the sentence contains no facts.
        # Exclude these paired samples from evaluation rather than score them as negatives.
        if doc['id'] in old_input and kept:
            inputs[doc['id']] = old_input[doc['id']]
            golds[doc['id']] = kept
    manifest = []
    updates = {}
    def put(name, data):
        updates[name] = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if not (backup / 'input.json').exists(): updates['before_source_grounded/input.json'] = old_input_text
    if not (backup / 'gold.json').exists(): updates['before_source_grounded/gold.json'] = old_gold_text
    put('input.json', inputs)
    put('gold.json', golds)
    ids = list(inputs)
    quotient, remainder = divmod(len(ids), 20)
    cursor = 0
    for batch in range(20):
        batch_size = quotient + (batch < remainder)
        batch_ids = ids[cursor:cursor+batch_size]
        cursor += batch_size
        put(f'input/{batch}.json', {key: inputs[key] for key in batch_ids})
        put(f'gold/{batch}.json', {key: golds[key] for key in batch_ids})
        manifest.append({'batch': batch, 'input_file': f'input/{batch}.json',
                         'gold_file': f'gold/{batch}.json', 'sample_count': len(batch_ids),
                         'triple_count': sum(len(golds[key]) for key in batch_ids),
                         'empty_gold_count': sum(not golds[key] for key in batch_ids),
                         'first_id': batch_ids[0], 'last_id': batch_ids[-1]})
    summary = {'original_cluster_count': len(audit), 'input_samples': len(inputs),
               'previous_gold_triples': sum(map(len, baseline_gold.values())),
               'new_gold_triples': sum(map(len, golds.values())),
               'removed_clusters': sum(e['status'] == 'removed' for e in audit),
               'deduplicated_clusters': duplicate_count,
               'removal_reasons': dict(reasons),
               'excluded_input_sample_ids': [key for key in old_input if key not in golds],
               'empty_gold_sample_ids': [key for key in ids if not golds[key]],
               'method': 'contiguous source spans, source order, protected gap operators; lexical evidence, not semantic proof'}
    put('batch_manifest.json', manifest)
    put('source_grounded_audit.json', {'summary': summary, 'clusters': audit})
    if '--apply' in sys.argv:
        for name, content in updates.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if '--examples' in sys.argv:
        for entry in audit:
            if entry['sample_id'] in ('benchie_1', 'benchie_2', 'benchie_23', 'benchie_30', 'benchie_69'):
                print(json.dumps({k: entry[k] for k in ('sample_id', 'cluster_ordinal', 'status', 'triple') if k in entry}, ensure_ascii=False))


if __name__ == '__main__':
    build()
