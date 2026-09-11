"""Shared R1, followed by independent entity + relation feedback branches.

Only this entry point uses the experiment. main.py and pipeline.py are unchanged.
"""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import logging
import os
import platform
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from karma.agents import (EntityExtractionAgent, RelationshipExtractionAgent,
                          IngestionAgent, SummarizerAgent, TextGenerationAgent,
                          TextComparisonAgent, ConflictResolutionAgent, EvaluatorAgent)
from recorded_calls import RecordedCalls, save

METHODS = ('reextract', 'incremental')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def api_config(mode=None):
    if mode is None:
        # Read the constant; importing main.py would activate its legacy sys.path insertion.
        tree = ast.parse((ROOT / 'main.py').read_text(encoding='utf-8-sig'))
        mode = next(ast.literal_eval(n.value) for n in tree.body
                    if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'API_MODE' for t in n.targets))
    prefix = 'KARMA_' if mode == 0 else 'KARMA_PROXY_'
    config = {'api_mode': 'chat_completions' if mode == 0 else 'responses',
              'api_mode_number': mode, 'model': os.getenv(prefix + 'MODEL', ''),
              'base_url': os.getenv(prefix + 'BASE_URL', ''),
              'max_retries': 2, 'timeout': 600,
              'temperature': 'Use existing agent call parameters (entity/relation: 0.0)'}
    return config, os.getenv(prefix + 'API_KEY', '')


def load_documents(path, doc_ids):
    collection = read(path)
    if not isinstance(collection, dict):
        raise ValueError('Input must be the document-name → sentence-list JSON object')
    items = list(collection.items())
    selected = list(range(len(items))) if doc_ids == 'all' else [int(n) for n in doc_ids.split(',')]
    if not selected or len(set(selected)) != len(selected):
        raise ValueError('Document IDs must be nonempty and unique')
    result = []
    for i in selected:
        if i < 0 or i >= len(items):
            raise ValueError(f'Document {i} is outside the input collection')
        title, sentences = items[i]
        if not isinstance(sentences, list) or not all(isinstance(s, str) for s in sentences):
            raise ValueError(f'doc{i}: expected a list of sentence strings; do not skip/reindex documents')
        result.append({'doc_id': i, 'title': title, 'sentences': sentences,
                       'raw_text': ' '.join(sentences)})
    return result


def serialize(items):
    return [x.to_dict() for x in items]


def changes(before, after):
    # Exact changes are descriptive, not semantic correctness or confirmed add/remove effects.
    key = lambda t: (t['head'], t['relation'], t['tail'])
    old, new = {key(t): i for i, t in enumerate(before)}, {key(t): i for i, t in enumerate(after)}
    return {'definition': 'Case-sensitive exact head/relation/tail equality; not a semantic judgment',
            'unchanged': [{'t1_index': old[k], 't2_index': new[k]} for k in old if k in new],
            't1_only': [{'index': i, 'triple': before[i]} for k, i in old.items() if k not in new],
            't2_only': [{'index': i, 'triple': after[i]} for k, i in new.items() if k not in old]}


def audit_status(audit):
    if isinstance(audit, list):
        statuses = [audit_status(x) for x in audit]
        return next((s for s in statuses if s != 'success'), 'success')
    if isinstance(audit, dict):
        mode = audit.get('mode', '')
        if 'failure' in mode or 'fallback' in mode:
            return 'fallback_or_parse_failure'
        if audit.get('rejected'):
            return 'partial_rejected'
    return 'success'


class Experiment:
    def __init__(self, output, config, caller):
        self.output, self.config, self.caller = Path(output), config, caller
        self.statuses = {}

    def agent(self, cls):
        return self.caller.bind(cls(None, self.config['model']))

    def stage(self, path, invoke, audit_fn=lambda: {}):
        self.caller.stage = path
        start = len(self.caller.records)
        result = invoke()
        audit = copy.deepcopy(audit_fn())
        calls = self.caller.records[start:]
        status = audit_status(audit)
        if any(c['status'] != 'success' for c in calls):
            status = 'call_failed_or_incomplete'
        if not calls:
            status = 'not_called'
        record = {'status': status, 'audit': audit, 'call_ids': [c['id'] for c in calls]}
        self.statuses[path] = record
        save(self.output / path / 'stage.json', record)
        if self.caller.auth_failed:
            raise PermissionError('API authentication/permission failed; stopping the experiment')
        return result

    def postprocess(self, triples, folder):
        # Each document is independent. Neither branch can see the other branch's graph.
        relation = RelationshipExtractionAgent(None, self.config['model'])
        deduped = relation._deduplicate_relationships(copy.deepcopy(triples))
        conflict = ConflictResolutionAgent(None, self.config['model'])
        resolved = conflict.process(deduped, [])
        evaluator = EvaluatorAgent(None, self.config['model'], integrate_threshold=0,
                                   dump_dir=self.output / folder / 'evaluator')
        final = evaluator.process(resolved)
        save(self.output / folder / 'postprocess.json', {
            'existing_graph': [], 'integration_threshold': 0,
            'input': serialize(triples), 'deduplicated': serialize(deduped),
            'conflict_resolved': serialize(resolved), 'final': serialize(final)})
        return final

    def run_document(self, document, use_summarizer=False):
        doc = document['doc_id']
        folder = f'documents/doc_{doc:03d}'
        ingestion = IngestionAgent(None, self.config['model'])
        _, normalized = ingestion.process(document['raw_text'])
        marker = '__NEWLINE_AFTER_PUNCT__'
        normalized = re.sub(r'([.!?])\s*\n', r'\1' + marker, normalized)
        normalized = re.sub(r'(?<!\n)\n(?!\n)', ' ', normalized).replace(marker, '\n')
        summaries = [normalized]
        if use_summarizer:
            summarizer = self.agent(SummarizerAgent)
            summaries, _ = self.stage(folder + '/shared/summarizer', lambda: summarizer.process(normalized))
        source = '\n'.join(summaries)
        save(self.output / folder / 'source.json', {**document, 'normalized_content': normalized,
                                                  'summaries': summaries, 'source_text': source})

        entity, relation = self.agent(EntityExtractionAgent), self.agent(RelationshipExtractionAgent)
        e1 = self.stage(folder + '/shared/entity', lambda: entity.process(summaries, {}),
                        lambda: entity.last_extraction)
        raw_t1 = self.stage(folder + '/shared/relationship', lambda: relation.process(summaries, e1, {}),
                           lambda: relation.last_extraction)
        t1 = self.postprocess(raw_t1, folder + '/shared')
        generator, comparator = self.agent(TextGenerationAgent), self.agent(TextComparisonAgent)
        text_b = self.stage(folder + '/shared/text_generation', lambda: generator.process(t1))
        diff = self.stage(folder + '/shared/text_comparison', lambda: comparator.process(source, text_b))
        comparison_path = folder + '/shared/text_comparison'
        if diff.get('summary') in ('Comparison parsed from raw text', 'Fallback comparison generated',
                                   'One or both texts are empty'):
            self.statuses[comparison_path]['status'] = 'comparison_fallback'
        if not all(isinstance(diff.get(k), list) and all(isinstance(s, str) for s in diff[k])
                   for k in ('unique_to_text_a', 'unique_to_text_b')):
            self.statuses[comparison_path]['status'] = 'invalid_diff'
        save(self.output / comparison_path / 'stage.json', self.statuses[comparison_path])
        shared = {'source_text': source, 'summaries': summaries, 'E1': serialize(e1),
                  'T1': serialize(t1), 'text_b': text_b, 'diff': diff}
        frozen_hash = digest(shared)
        save(self.output / folder / 'shared/baseline.json', {**shared, 'sha256': frozen_hash})
        shared_ok = all(v['status'] == 'success' for k, v in self.statuses.items()
                        if k.startswith(folder + '/shared/'))
        result = {'doc_id': doc, 'title': document['title'], 'shared_sha256': frozen_hash,
                  'baseline_usable': shared_ok, 'branches': {},
                  'baseline': folder + '/shared/baseline.json',
                  'baseline_file_sha256': sha(self.output / folder / 'shared/baseline.json')}
        # Alternate order by sample ID without choosing order from observed quality.
        order = METHODS if (doc // 8) % 2 == 0 else tuple(reversed(METHODS))
        result['branch_order'] = list(order)
        for method in order:
            branch = folder + '/' + method
            entity, relation = self.agent(EntityExtractionAgent), self.agent(RelationshipExtractionAgent)
            local_e1, local_t1, local_diff = copy.deepcopy((e1, t1, diff))
            save(self.output / branch / 'input.json', {
                'shared_sha256': frozen_hash, 'source_text': source, 'diff': local_diff,
                **({'E1': serialize(local_e1), 'T1': serialize(local_t1)} if method == 'incremental' else {})})
            if method == 'reextract':
                e2 = self.stage(branch + '/entity', lambda: entity.process(summaries, local_diff),
                                lambda: entity.last_extraction)
                t2_raw = self.stage(branch + '/relationship',
                                    lambda: relation.process(summaries, e2, local_diff),
                                    lambda: relation.last_extraction)
            else:
                e2 = self.stage(branch + '/entity',
                                lambda: entity.revise_entities(source, local_e1, local_t1, local_diff),
                                lambda: entity.last_revision)
                t2_raw = self.stage(branch + '/relationship',
                                    lambda: relation.revise_relationships(source, local_t1, local_diff, entities=e2),
                                    lambda: relation.last_revision)
            t2 = self.postprocess(t2_raw, branch)
            save(self.output / branch / 'E2.json', serialize(e2))
            save(self.output / branch / 'T2.json', serialize(t2))
            save(self.output / branch / 'changes.json', changes(serialize(t1), serialize(t2)))
            e1_names, e2_names = {e.name for e in e1}, {e.name for e in e2}
            save(self.output / branch / 'entity_changes.json', {
                'definition': 'Exact name equality; not semantic correctness',
                'retained': sorted(e1_names & e2_names), 'E1_only': sorted(e1_names - e2_names),
                'E2_only': sorted(e2_names - e1_names)})
            branch_ok = all(self.statuses[branch + '/' + s]['status'] == 'success'
                            for s in ('entity', 'relationship'))
            result['branches'][method] = {
                'status': 'success' if branch_ok else 'needs_review', 'E2_count': len(e2),
                'T2_count': len(t2), 'T2': branch + '/T2.json',
                'T2_sha256': sha(self.output / branch / 'T2.json'),
                'entity_status': self.statuses[branch + '/entity']['status'],
                'relationship_status': self.statuses[branch + '/relationship']['status']}
            if digest(shared) != frozen_hash or serialize(e1) != shared['E1'] or serialize(t1) != shared['T1']:
                raise AssertionError('Shared R1 state was modified by a feedback branch')
        result['paired_usable'] = shared_ok and all(b['status'] == 'success' for b in result['branches'].values())
        save(self.output / folder / 'summary.json', result)
        return result


def snapshot_code(output):
    files = list((ROOT / 'karma').rglob('*.py')) + [ROOT / 'main.py', ROOT / 'evaluate.py'] + list(HERE.glob('*.py'))
    hashes = {}
    for path in files:
        relative = path.relative_to(ROOT)
        target = output / 'code_snapshot' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        hashes[str(relative)] = sha(path)
    save(output / 'code_hashes.json', hashes)
    return hashes


def prepare(output, documents, input_path, gold_dir, config, use_summarizer, dry_run):
    output.mkdir(parents=True, exist_ok=False)
    manifest = {'version': 1, 'status': 'dry_run' if dry_run else 'running',
                'workspace': str(ROOT), 'python': sys.version, 'platform': platform.platform(),
                'input_path': str(input_path), 'input_sha256': sha(input_path),
                'config': config, 'use_summarizer': use_summarizer,
                'scope': 'Shared R1; independently generated R2 entities and relationships; independent documents',
                'reader': 'Not executed: current default source uses normalized_content, not reader outputs',
                'schema_alignment': False, 'integration_threshold': 0,
                'documents': [], 'results': []}
    for index, document in enumerate(documents):
        doc = document['doc_id']
        gold_path = gold_dir / f'{doc}.json'
        gold = read(gold_path)
        if not isinstance(gold, list) or not all(isinstance(t, dict) and
                all(isinstance(t.get(k), str) for k in ('head', 'relation', 'tail')) for t in gold):
            raise ValueError(f'Invalid Gold structure: {gold_path}')
        dest = f'gold/doc_{doc:03d}.json'
        (output / 'gold').mkdir(exist_ok=True)
        shutil.copy2(gold_path, output / dest)
        save(output / f'documents/doc_{doc:03d}/input.json', document)
        manifest['documents'].append({'doc_id': doc, 'sample_index': index, 'title': document['title'],
            'gold_path': str(gold_path), 'gold_snapshot': dest, 'gold_sha256': sha(gold_path), 'gold_n': len(gold)})
    manifest['code_hashes'] = snapshot_code(output)
    save(output / 'manifest.json', manifest)
    return manifest


def run(output, documents, manifest, caller, use_summarizer=False):
    experiment = Experiment(output, manifest['config'], caller)
    for document in documents:
        print(f'doc{document["doc_id"]}: shared R1 -> entity + relationship feedback in both branches', flush=True)
        try:
            summary = experiment.run_document(document, use_summarizer)
            manifest['results'].append(summary)
        except Exception as exc:
            manifest['results'].append({'doc_id': document['doc_id'], 'paired_usable': False,
                                        'error': caller._redact(f'{type(exc).__name__}: {exc}')})
            if isinstance(exc, PermissionError):
                manifest['status'] = 'stopped_auth_error'
                break
        finally:
            manifest['call_count'] = len(caller.records)
            manifest['attempt_count'] = sum(len(c.get('attempts', [])) for c in caller.records)
            save(output / 'stage_statuses.json', experiment.statuses)
            save(output / 'manifest.json', manifest)
    if manifest['status'] == 'running':
        manifest['status'] = 'completed' if all(r.get('paired_usable') for r in manifest['results']) else 'completed_with_issues'
    save(output / 'manifest.json', manifest)
    print(f'Saved: {output}\nStatus: {manifest["status"]}; logical calls: {len(caller.records)}', flush=True)
    return manifest


def evaluate_run(output):
    # Import THIS RUN's frozen evaluate.py. Never infer document IDs from file sort order.
    manifest = read(output / 'manifest.json')
    script = output / 'code_snapshot/evaluate.py'
    if sha(script) != manifest['code_hashes']['evaluate.py']:
        raise ValueError('Frozen evaluate.py hash mismatch')
    spec = importlib.util.spec_from_file_location('frozen_evaluate', script)
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    # Partial rejection is an observed outcome of a strategy, not a reason to
    # remove the whole document from the primary comparison. Keep strict pairs
    # as a separate diagnostic subset without rewriting the extraction manifest.
    usable = [r for r in manifest['results'] if r.get('baseline')
              and all(r.get('branches', {}).get(method, {}).get('T2') for method in METHODS)]
    if not usable:
        raise ValueError('No documents with a saved baseline and both final outputs; inspect manifest.json')
    gold_index = {d['doc_id']: d for d in manifest['documents']}
    gold_docs, predictions = [], {name: [] for name in ('T1', *METHODS)}
    for result in usable:
        info = gold_index[result['doc_id']]
        path = output / info['gold_snapshot']
        if sha(path) != info['gold_sha256']:
            raise ValueError(f'Gold snapshot changed: {path}')
        gold_docs.append(read(path))
        if sha(output / result['baseline']) != result['baseline_file_sha256']:
            raise ValueError('Shared baseline file changed since extraction')
        predictions['T1'].append(read(output / result['baseline'])['T1'])
        for method in METHODS:
            if sha(output / result['branches'][method]['T2']) != result['branches'][method]['T2_sha256']:
                raise ValueError(f'{method} prediction file changed since extraction')
            predictions[method].append(read(output / result['branches'][method]['T2']))
    evaluator.precompute_embeddings(gold_docs, [p for docs in predictions.values() for p in docs])
    report = {'scope': 'All documents with saved T1 and both final outputs, including partial rejection/fallback',
              'included_doc_ids': [r['doc_id'] for r in usable],
              'excluded_doc_ids': [d['doc_id'] for d in manifest['documents'] if d['doc_id'] not in {r['doc_id'] for r in usable}],
              'exclusion_reason': 'No saved baseline or missing a final branch output; never count missing files as empty predictions',
              'operational_statuses': [{'doc_id': r['doc_id'],
                  'baseline_usable': r.get('baseline_usable'), 'paired_usable': r.get('paired_usable'),
                  'branches': r.get('branches', {}), 'error': r.get('error')}
                  for r in manifest['results']],
              'thresholds': {'whole': evaluator.WHOLE_THRESHOLD, 'entity': evaluator.ENTITY_THRESHOLD},
              'embedding_model': evaluator.EMBED_MODEL,
              'macro_definition': 'Original evaluator: harmonic mean of mean document P and mean document R',
              'results': {}}
    eval_dir = output / 'evaluation' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    eval_dir.mkdir(parents=True, exist_ok=False)
    import numpy as np
    for name, docs in predictions.items():
        score = evaluator.evaluate(gold_docs, docs)
        for row, result, gold, pred in zip(score['per_doc'], usable, gold_docs, docs):
            row['doc'] = result['doc_id']
            if gold and pred:
                whole, entity = evaluator._build_sim_matrices(gold, pred)
            else:
                whole = entity = np.zeros((len(gold), len(pred)))
            mask = (whole >= evaluator.WHOLE_THRESHOLD) & (entity >= evaluator.ENTITY_THRESHOLD)
            np.savez_compressed(eval_dir / f'doc_{result["doc_id"]:03d}_{name}_matrix.npz',
                                whole=whole, entity=entity, matches=mask)
            save(eval_dir / f'doc_{result["doc_id"]:03d}_{name}_pairs.json', {
                'gold': gold, 'predictions': pred, 'matched_pairs': [
                    {'gold_index': int(g), 'pred_index': int(p), 'whole': float(whole[g, p]),
                     'entity': float(entity[g, p])} for g, p in zip(*np.where(mask))]})
        report['results'][name] = score
    strict_indices = [i for i, result in enumerate(usable) if result.get('paired_usable')]
    report['clean_pairs'] = {
        'scope': 'Diagnostic subset only: baseline and both branches marked paired_usable by the original run',
        'included_doc_ids': [usable[i]['doc_id'] for i in strict_indices],
        'excluded_doc_ids': [d['doc_id'] for d in manifest['documents']
                             if d['doc_id'] not in {usable[i]['doc_id'] for i in strict_indices}],
        'results': {}}
    if strict_indices:
        for name, docs in predictions.items():
            score = evaluator.evaluate([gold_docs[i] for i in strict_indices], [docs[i] for i in strict_indices])
            for row, i in zip(score['per_doc'], strict_indices):
                row['doc'] = usable[i]['doc_id']
            report['clean_pairs']['results'][name] = score
    else:
        report['clean_pairs']['note'] = 'No strictly clean pairs; no subset scores computed'
    save(eval_dir / 'comparison.json', report)
    print(f'Evaluated all final outputs: {report["included_doc_ids"]}; '
          f'clean diagnostic subset: {report["clean_pairs"]["included_doc_ids"]}\n'
          f'Evaluation saved: {eval_dir}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true', help='Validate/snapshot inputs; no model calls')
    action.add_argument('--run', action='store_true', help='Run shared R1 and both complete feedback branches')
    action.add_argument('--evaluate-run', type=Path, help='Evaluate a saved run; calls embedding API')
    parser.add_argument('--input', type=Path, default=ROOT / 'data/DocIOE/DocOIE_transportation_gold_input.json')
    parser.add_argument('--gold-dir', type=Path, default=ROOT / 'data/DocIOE/transport')
    parser.add_argument('--docs', default='0,8,16,24,32,39', help='Original document IDs separated by commas, or all')
    parser.add_argument('--api-mode', type=int, choices=(0, 1), default=None, help='Default: main.py API_MODE')
    parser.add_argument('--use-summarizer', action='store_true', help='Explicitly enable summarizer; default uses normalized source')
    args = parser.parse_args()
    os.chdir(ROOT)
    logging.getLogger().setLevel(logging.WARNING)
    if args.evaluate_run:
        evaluate_run(args.evaluate_run.resolve())
        return
    documents = load_documents(args.input, args.docs)
    config, key = api_config(args.api_mode)
    if args.run and (not key or not config['model'] or not config['base_url']):
        parser.error('Selected API mode requires key, model and base URL; configure the COPY .env')
    output = HERE / 'runs' / (('dry_' if args.dry_run else 'run_') + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    manifest = prepare(output, documents, args.input.resolve(), args.gold_dir.resolve(), config,
                       args.use_summarizer, args.dry_run)
    if args.dry_run:
        print(f'Validated {len(documents)} documents. Planned: approximately {len(documents) * 8} calls without summarizer.\n{output}')
        return
    caller = RecordedCalls(output, config, key)
    run(output, documents, manifest, caller, args.use_summarizer)


if __name__ == '__main__':
    main()
