"""Evaluate KARMA checkpoints on BenchIE Chinese fact clusters offline."""

import argparse
import json
import math
import re
import sys
import tempfile
from collections import defaultdict
from itertools import product
from pathlib import Path

from evaluation_common import (
    FIELDS, harmonic, load_inputs, maximum_weight_pairs, pair_details, read_json,
    summary, validate_triples,
)
from lexical_tokens import normalize_chinese_spacing


DEFAULT_GOLD = (
    Path(__file__).resolve().parent / "data/benchie-main/11.13 input/benchie_zh_gold_clusters.json"
)


def expand_optional(field, location):
    """Treat each bracketed phrase as a single optional span."""
    parts = re.split(r"\[([^\[\]]+)\]", field)
    if any("[" in part or "]" in part for part in parts):
        raise ValueError(f"{location}: invalid optional span in {field!r}")
    choices = [(part, "") if index % 2 else (part,) for index, part in enumerate(parts)]
    return dict.fromkeys(
        normalize_chinese_spacing("".join(option)) for option in product(*choices)
    )


def load_clusters(path):
    raw = read_json(path)
    if not isinstance(raw, dict) or not raw:
        raise ValueError("BenchIE Gold must map sample IDs to fact-cluster lists")
    gold = {}
    for sample_id, items in raw.items():
        if not sample_id or not isinstance(items, list):
            raise ValueError(f"{sample_id!r}: expected a sample ID and a cluster list")
        clusters = {}
        for item in items:
            cluster_id = item.get("cluster_id") if isinstance(item, dict) else None
            if type(cluster_id) is not int or cluster_id < 1 or cluster_id in clusters:
                raise ValueError(f"{sample_id}: invalid or duplicate cluster ID {cluster_id!r}")
            location = f"{sample_id}/cluster {cluster_id}"
            patterns = validate_triples(item.get("variants"), location)
            triples = {}
            for pattern in patterns:
                fields = (expand_optional(pattern[field], location) for field in FIELDS)
                for triple in product(*fields):
                    if all(triple):
                        triples.setdefault(triple, dict(zip(FIELDS, triple)))
            if not triples:
                raise ValueError(f"{location}: expected at least one nonempty variant")
            clusters[cluster_id] = {"cluster_id": cluster_id, "variants": list(triples.values())}
        gold[sample_id] = [clusters[key] for key in sorted(clusters)]
    return gold


def evaluate_exact(predictions, clusters):
    by_variant = defaultdict(list)
    for cluster in clusters:
        for variant in cluster["variants"]:
            by_variant[tuple(variant[field] for field in FIELDS)].append(cluster["cluster_id"])
    matches, covered = [], set()
    false_positives = repeated = 0
    for index, prediction in enumerate(predictions):
        key = tuple(normalize_chinese_spacing(prediction[field]) for field in FIELDS)
        candidates = by_variant.get(key, [])
        # The upstream scorer takes the first cluster when a variant is shared.
        cluster_id = candidates[0] if candidates else None
        status = "unmatched"
        if cluster_id is None:
            false_positives += 1
        elif cluster_id in covered:
            repeated += 1
            status = "additional_hit"
        else:
            covered.add(cluster_id)
            status = "hit"
        matches.append({"prediction_index": index, "prediction": prediction, "status": status,
                        "cluster_id": cluster_id, "candidate_cluster_ids": candidates})
    missed = [cluster["cluster_id"] for cluster in clusters if cluster["cluster_id"] not in covered]
    return {"tp": len(covered), "fp": false_positives, "fn": len(missed),
            "num_gold_clusters": len(clusters), "num_predictions": len(predictions),
            "additional_same_cluster_hits": repeated,
            "uncovered_cluster_ids": missed, "predictions": matches}


def evaluate_lenient(predictions, clusters):
    best = []
    for cluster in clusters:
        row = []
        for prediction in predictions:
            # Keep one variant per edge, with first occurrence on a tied F1.
            variant, score = max(
                ((v, pair_details(v, prediction, "lenient")) for v in cluster["variants"]),
                key=lambda candidate: candidate[1]["f1"],
            )
            row.append((variant, score))
        best.append(row)
    pairs = maximum_weight_pairs([[score["f1"] for _, score in row] for row in best])
    matches = []
    for gi, pi in pairs:
        variant, score = best[gi][pi]
        matches.append({"cluster_id": clusters[gi]["cluster_id"], "prediction_index": pi,
                        "gold_variant": variant, "prediction": predictions[pi], **score})
    metrics = summary(math.fsum(row["precision"] for row in matches),
                      math.fsum(row["recall"] for row in matches),
                      len(predictions), len(clusters), len(pairs), "lenient")
    used_g = {gi for gi, _ in pairs}
    used_p = {pi for _, pi in pairs}
    return {**metrics, "matches": matches,
            "unpaired_cluster_ids": [c["cluster_id"] for gi, c in enumerate(clusters) if gi not in used_g],
            "unpaired_prediction_indices": [pi for pi in range(len(predictions)) if pi not in used_p]}


def evaluate(samples, info):
    results = {}
    for label, stage in info["round_stages"].items():
        per_sample = []
        for sample in samples:
            predictions = sample["rounds"][label]
            clusters = sample["gold"]
            per_sample.append({"doc_id": sample["doc_id"], "gold_clusters": clusters,
                               "benchie_exact": evaluate_exact(predictions, clusters),
                               "han_overlap_lenient": evaluate_lenient(predictions, clusters)})
        exact_rows = [item["benchie_exact"] for item in per_sample]
        exact = {key: sum(row[key] for row in exact_rows) for key in
                 ("tp", "fp", "fn", "num_gold_clusters", "num_predictions", "additional_same_cluster_hits")}
        tp, fp, fn = exact["tp"], exact["fp"], exact["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        exact.update(precision=precision, recall=recall, f1=harmonic(precision, recall))
        soft_rows = [item["han_overlap_lenient"] for item in per_sample]
        soft = summary(math.fsum(row["precision_sum"] for row in soft_rows),
                       math.fsum(row["recall_sum"] for row in soft_rows),
                       sum(row["num_pred"] for row in soft_rows), sum(row["num_gold"] for row in soft_rows),
                       sum(row["selected_pairs"] for row in soft_rows), "lenient")
        results[stage] = {"benchie_exact": exact, "han_overlap_lenient": soft, "samples": per_sample}
    return {
        "input": info,
        "rules": {
            "benchie_exact": (
                "BenchIE slot scoring with Chinese whitespace normalization. First matching cluster "
                "per prediction, each covered cluster counts once. Only predictions with no exact "
                "variant are false positives. Additional hits on a covered cluster are reported separately."
            ),
            "han_overlap_lenient": (
                "KARMA character overlap, not the official BenchIE score. Each Han character is one token. "
                "Lowercased non-Han text is split at whitespace and Han boundaries. Use the best variant "
                "per cluster/prediction pair and maximize sum of pair F1 in a one-to-one assignment."
            ),
        },
        "stages": results,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", type=Path, help="KARMA output directory or its details subdirectory")
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD, help="BenchIE Chinese cluster JSON")
    parser.add_argument("--output", type=Path, help="Defaults to RESULT_DIR/benchie_evaluation/eval_benchie.json")
    args = parser.parse_args(argv)
    output = args.output or args.result_dir / "benchie_evaluation/eval_benchie.json"
    temporary = None
    try:
        samples, info = load_inputs(args.result_dir, args.gold, comparison="all", gold_loader=load_clusters)
        report = evaluate(samples, info)
        if output.resolve() in (args.gold.resolve(), Path(info["manifest_path"])):
            raise ValueError("Output must differ from Gold and the run manifest")
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        temporary.replace(output)
        for stage, result in report["stages"].items():
            for metric in report["rules"]:
                score = result[metric]
                print(f"{stage} {metric}: P={score['precision']:.6f} "
                      f"R={score['recall']:.6f} F1={score['f1']:.6f}")
        print(output.resolve())
    except (ValueError, OSError) as error:
        print(f"Evaluation error: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
