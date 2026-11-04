"""Replay identical saved inputs through both feedback scopes, without re-splitting."""
import argparse
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from karma.core.pipeline import KARMAPipeline
from karma.core.data_structures import KnowledgeTriple, KGEntity
from karma.core.run_artifacts import fingerprint, write_json
from karma.core.sentence_groups import source_sentences
from evaluation_common import evaluate_round, load_gold


def load_inputs(revision_path, feedback_path, entities_path):
    revision = json.loads(Path(revision_path).read_text(encoding='utf-8'))
    feedback = json.loads(Path(feedback_path).read_text(encoding='utf-8'))
    entities = json.loads(Path(entities_path).read_text(encoding='utf-8'))
    sentences = revision['source_sentences']
    text = feedback['text_a']
    if source_sentences(text, [s['text'] for s in sentences]) != sentences:
        raise ValueError('Source text and saved source IDs/boundaries disagree')
    # Require actual saved values; absence is not an empty successful comparison.
    diff = feedback['diff']
    recon = feedback['reconstructions']
    triples = revision['after_split']
    if not isinstance(diff, dict) or not isinstance(recon, list) or not isinstance(entities, list):
        raise ValueError('Expected saved diff object, reconstruction array, and entity array')
    for t in triples:
        KnowledgeTriple.from_dict(t)
    candidates = []
    for i, e in enumerate(entities):
        if not isinstance(e, dict) or not isinstance(e.get('name', e.get('mention')), str):
            raise ValueError('Each candidate entity needs name or mention')
        candidates.append(dict(entity_id=e.get('entity_id', str(i)), name=e.get('name', e.get('mention')),
                               aliases=e.get('aliases', [])))
    return dict(text=text, sentences=sentences, triples=triples, diff=diff, reconstructions=recon, entities=candidates)


def replay(inputs, pipeline):
    result = pipeline.feedback_pipeline.process(inputs['text'],
        [KnowledgeTriple.from_dict(t) for t in copy.deepcopy(inputs['triples'])], copy.deepcopy(inputs['diff']),
        [KGEntity.from_dict(e) for e in inputs['entities']], sentences=copy.deepcopy(inputs['sentences']),
        reconstructions=copy.deepcopy(inputs['reconstructions']))
    return dict(after_split=inputs['triples'],
                after_add=[t.to_dict() for t in pipeline.feedback_pipeline.snapshots['after_add']],
                after_replace=[t.to_dict() for t in pipeline.feedback_pipeline.snapshots['after_replace']],
                after_revision=[t.to_dict() for t in result], revision_audit=pipeline.feedback_pipeline.last_revision)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('revision-result', 'feedback-input', 'entities', 'output-dir'):
        parser.add_argument('--'+arg, required=True)
    parser.add_argument('--base-url', default=os.getenv('KARMA_BASE_URL'))
    parser.add_argument('--model', default=os.getenv('KARMA_MODEL'))
    parser.add_argument('--api-mode', choices=('chat_completions','responses'), default='chat_completions')
    parser.add_argument('--api-min-interval', type=float, default=1.0)
    parser.add_argument('--gold')
    parser.add_argument('--gold-key')
    args = parser.parse_args(argv)
    if not os.getenv('KARMA_API_KEY') or not args.base_url or not args.model:
        parser.error('Set KARMA_API_KEY and supply base URL/model (or their KARMA_* environment variables)')
    if bool(args.gold) != bool(args.gold_key):
        parser.error('--gold and --gold-key must be supplied together')
    inputs = load_inputs(args.revision_result, args.feedback_input, args.entities)
    gold = load_gold(args.gold)[args.gold_key] if args.gold else None
    out = Path(args.output_dir)
    if out.exists() and any(out.iterdir()):
        parser.error('Use an empty output directory')
    outputs = {}
    for scope in ('document', 'sentence'):
        pipeline = KARMAPipeline(os.environ['KARMA_API_KEY'], base_url=args.base_url, model_name=args.model,
                                 api_mode=args.api_mode, feedback_scope=scope, api_min_interval=args.api_min_interval)
        try:
            outputs[scope] = replay(inputs, pipeline)
            write_json(out / (scope + '.json'), dict(outputs[scope], input_sha256=fingerprint(inputs),
                                                    config=pipeline._run_configuration('transportation', 0.2)))
        finally:
            pipeline.client.close()
    if gold is not None:
        metrics = {}
        for scope, result in outputs.items():
            scores = {}
            for stage in ('after_split','after_add','after_replace','after_revision'):
                scores[stage], _ = evaluate_round([dict(doc_id=args.gold_key, gold_key=args.gold_key,
                    gold=gold, rounds={'R1':result[stage]})], 'R1', 'lenient')
            scores['feedback_delta'] = {key: scores['after_revision']['micro'][key] - scores['after_split']['micro'][key]
                                        for key in ('precision','recall','f1')}
            scores['actual_scope'] = result['revision_audit']['scope']
            metrics[scope] = scores
        write_json(out / 'lenient_metrics.json', metrics)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
