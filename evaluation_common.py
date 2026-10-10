"""Offline strict/lenient triple evaluation. Standard library only; no model calls.

Protocol lexical-one-to-one-v1:
strict = whitespace-normalized, case-sensitive field equality;
lenient = lowercased whitespace tokens, multiset overlap in corresponding fields.
Lenient candidates require positive overlap in ALL three fields. Assignment
maximizes the sum of pair F1; final P/R aggregate pair P/R, NOT pair F1.
"""

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import tempfile
from collections import Counter, defaultdict, deque
from pathlib import Path
from urllib.parse import quote


FIELDS = ("head", "relation", "tail")
PROTOCOL = "lexical-one-to-one-v1"


def normalize(text, mode):
    if mode not in ("strict", "lenient"):
        raise ValueError("Unknown metric: " + mode)
    text = " ".join(text.split())
    return text.lower() if mode == "lenient" else text


def triple_key(triple, mode):
    return tuple(normalize(triple[field], mode) for field in FIELDS)


def harmonic(p, r):
    return 2 * p * r / (p + r) if p + r else 0.0


def pair_details(gold, pred, mode):
    """Return score plus auditable token counts; missing sides are empty tokens."""
    details = {}
    for field in FIELDS:
        g = Counter(normalize(gold[field], mode).split()) if gold else Counter()
        p = Counter(normalize(pred[field], mode).split()) if pred else Counter()
        common = g & p
        details[field] = {
            "gold_count": sum(g.values()), "pred_count": sum(p.values()),
            "overlap_count": sum(common.values()),
            "overlap_words": dict(sorted(common.items())),
            "gold_missing_words": dict(sorted((g - p).items())),
            "pred_extra_words": dict(sorted((p - g).items())),
        }
    eligible = bool(gold and pred and all(details[f]["overlap_count"] for f in FIELDS))
    exact = bool(eligible and triple_key(gold, "strict") == triple_key(pred, "strict"))
    if mode == "strict":
        eligible = exact
        precision = recall = float(exact)
    elif eligible:
        overlap = sum(details[f]["overlap_count"] for f in FIELDS)
        precision = overlap / sum(details[f]["pred_count"] for f in FIELDS)
        recall = overlap / sum(details[f]["gold_count"] for f in FIELDS)
    else:
        precision = recall = 0.0
    return {"eligible": eligible, "exact": exact, "precision": precision,
            "recall": recall, "f1": harmonic(precision, recall), "fields": details}


def maximum_weight_pairs(weights):
    """Rectangular Hungarian assignment, returning only positive-weight edges.

    Nonnegative scores allow extending any partial matching with zero edges.
    Rows/columns are visited in index order, with first-wins ties: deterministic
    for identical input. This maximizes SUM(pair F1), not match count or final F1.
    """
    if not weights:
        return []
    width = len(weights[0])
    if any(len(row) != width for row in weights):
        raise ValueError("Assignment matrix must be rectangular")
    if not width:
        return []
    if any(not math.isfinite(x) or x < 0 for row in weights for x in row):
        raise ValueError("Assignment weights must be finite and nonnegative")
    transposed = len(weights) > width
    matrix = list(zip(*weights)) if transposed else weights
    n, m = len(matrix), len(matrix[0])  # n <= m
    u, v = [0.0] * (n + 1), [0.0] * (m + 1)
    owner, previous = [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        owner[0] = i
        j0 = 0
        minimum = [float("inf")] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = owner[j0], float("inf"), 0
            for j in range(1, m + 1):
                if not used[j]:
                    cost = -matrix[i0 - 1][j - 1] - u[i0] - v[j]
                    if cost < minimum[j]:
                        minimum[j], previous[j] = cost, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(m + 1):
                if used[j]:
                    u[owner[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if owner[j0] == 0:
                break
        while j0:
            j1 = previous[j0]
            owner[j0] = owner[j1]
            j0 = j1
    result = []
    for j in range(1, m + 1):
        if owner[j]:
            a, b = owner[j] - 1, j - 1
            gi, pi = (b, a) if transposed else (a, b)
            if weights[gi][pi] > 0:
                result.append((gi, pi))
    return sorted(result)


def select_pairs(gold, pred, mode):
    """Strict uses FIFO equality groups; lenient uses maximum weight assignment."""
    if mode == "strict":
        buckets = defaultdict(deque)
        for gi, triple in enumerate(gold):
            key = triple_key(triple, mode)
            if all(key):
                buckets[key].append(gi)
        pairs = []
        for pi, triple in enumerate(pred):
            bucket = buckets.get(triple_key(triple, mode))
            if bucket:
                pairs.append((bucket.popleft(), pi))
        return sorted(pairs)
    if mode != "lenient":
        raise ValueError("Unknown metric: " + mode)
    weights = [[pair_details(g, p, mode)["f1"] for p in pred] for g in gold]
    return maximum_weight_pairs(weights)


def item_id(doc_id, round_label, side, index):
    prefix = "D" + quote(doc_id, safe="")
    return f"{prefix}-G{index}" if side == "gold" else f"{prefix}-{round_label}-P{index}"


def duplicate_groups(triples, mode):
    """Report equality groups without dropping ANY original rows."""
    groups = defaultdict(list)
    for index, triple in enumerate(triples):
        key = triple_key(triple, mode)
        if mode == "lenient":
            key = tuple(tuple(sorted(Counter(text.split()).items())) for text in key)
        groups[key].append(index)
    return [indices for indices in groups.values() if len(indices) > 1]


def match_row(doc_id, round_label, mode, gold, pred, gi, pi):
    g, p = gold[gi] if gi is not None else None, pred[pi] if pi is not None else None
    score = pair_details(g, p, mode)
    row = {
        "metric": mode, "doc": doc_id, "round": round_label,
        "status": "matched" if g is not None and p is not None else (
            "gold_unmatched" if g is not None else "pred_unmatched"),
        "gold_id": item_id(doc_id, round_label, "gold", gi) if gi is not None else "",
        "pred_id": item_id(doc_id, round_label, "pred", pi) if pi is not None else "",
        "gold_index": gi if gi is not None else "", "pred_index": pi if pi is not None else "",
        "pair_precision": score["precision"], "pair_recall": score["recall"],
        "pair_f1": score["f1"], "exact_after_whitespace_cleanup": int(score["exact"]),
    }
    for field in FIELDS:
        for side, triple in (("gold", g), ("pred", p)):
            text = triple[field] if triple is not None else ""
            row[f"{side}_{field}"] = text
            row[f"{side}_{field}_normalized"] = normalize(text, mode)
        for name, value in score["fields"][field].items():
            row[f"{field}_{name}"] = (
                json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, dict) else value
            )
    return row


CSV_FIELDS = list(match_row("", "R1", "strict", [], [{f: "" for f in FIELDS}], None, 0))


def summary(p_sum, r_sum, num_pred, num_gold, pairs, mode):
    p = p_sum / num_pred if num_pred else 0.0
    r = r_sum / num_gold if num_gold else 0.0
    result = {"precision": p, "recall": r, "f1": harmonic(p, r),
              "precision_sum": p_sum, "recall_sum": r_sum,
              "num_pred": num_pred, "num_gold": num_gold,
              "selected_pairs": pairs, "unmatched_pred": num_pred - pairs,
              "unmatched_gold": num_gold - pairs}
    if mode == "strict":
        result.update(tp=pairs, fp=num_pred - pairs, fn=num_gold - pairs)
    return result


def evaluate_round(samples, round_label, mode):
    per_doc, rows = [], []
    for sample in samples:
        doc_id, gold = sample["doc_id"], sample["gold"]
        pred = sample["rounds"][round_label]
        pairs = select_pairs(gold, pred, mode)
        used_g, used_p = {g for g, _ in pairs}, {p for _, p in pairs}
        selected_rows = [match_row(doc_id, round_label, mode, gold, pred, g, p) for g, p in pairs]
        rows.extend(selected_rows)
        rows.extend(match_row(doc_id, round_label, mode, gold, pred, g, None)
                    for g in range(len(gold)) if g not in used_g)
        rows.extend(match_row(doc_id, round_label, mode, gold, pred, None, p)
                    for p in range(len(pred)) if p not in used_p)
        result = summary(math.fsum(r["pair_precision"] for r in selected_rows),
                         math.fsum(r["pair_recall"] for r in selected_rows),
                         len(pred), len(gold), len(pairs), mode)
        result.update(doc=doc_id, gold_key=sample["gold_key"],
                      gold_duplicate_groups=duplicate_groups(gold, mode),
                      pred_duplicate_groups=duplicate_groups(pred, mode))
        per_doc.append(result)
    micro = summary(math.fsum(d["precision_sum"] for d in per_doc),
                    math.fsum(d["recall_sum"] for d in per_doc),
                    sum(d["num_pred"] for d in per_doc), sum(d["num_gold"] for d in per_doc),
                    sum(d["selected_pairs"] for d in per_doc), mode)
    macro_p = math.fsum(d["precision"] for d in per_doc) / len(per_doc) if per_doc else 0.0
    macro_r = math.fsum(d["recall"] for d in per_doc) / len(per_doc) if per_doc else 0.0
    return {"micro": micro, "macro": {"precision": macro_p, "recall": macro_r,
                                       "f1": harmonic(macro_p, macro_r)},
            "per_doc": per_doc}, rows


def evaluate_samples(samples, modes, input_info):
    if not samples:
        raise ValueError("No documents to evaluate")
    rounds = list(samples[0]["rounds"])
    report = {
        "protocol": PROTOCOL, "input": input_info,
        "rules": {
            "strict": "Whitespace cleanup only; case, punctuation and word order retained; binary equality in all fields.",
            "lenient": "lower().split(); per-field Counter intersection; all three fields need positive overlap; no score threshold.",
            "assignment": "Strict: maximum equality-pair count. Lenient: maximum SUM of pair F1, deterministic index-order ties.",
            "aggregation": "micro P=sum(pair P)/all predictions; R=sum(pair R)/all gold; F1=harmonic(P,R). Unmatched contributes zero.",
            "macro": "Mean per-document P and R, then harmonic mean (legacy convention); NOT mean document/pair F1.",
            "empty": "Zero denominators produce zero; empty-field triples never match but remain in denominators.",
            "duplicates": "Preserve all entries; report equality groups; one-to-one matching penalizes excess predictions.",
            "language": "Whitespace tokenization, designed for English. No stemming, stopword removal, synonyms or language-specific rules.",
            "interpretation": "Lenient scores measure lexical overlap, not whole-triple factual correctness; not the official CaRB protocol.",
        },
        "document_ids": [s["doc_id"] for s in samples], "metrics": {},
    }
    rows = []
    for mode in modes:
        mode_results = {}
        for round_label in rounds:
            mode_results[round_label], new_rows = evaluate_round(samples, round_label, mode)
            rows.extend(new_rows)
        if "R1" in rounds and "R2" in rounds:
            for averaging in ("micro", "macro"):
                mode_results["delta_" + averaging] = {
                    key: mode_results["R2"][averaging][key] - mode_results["R1"][averaging][key]
                    for key in ("precision", "recall", "f1")
                }
        report["metrics"][mode] = mode_results
    return report, rows


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_object)


def validate_triples(value, location):
    if not isinstance(value, list):
        raise ValueError(f"{location}: expected a triple list")
    triples = []
    for index, triple in enumerate(value):
        if not isinstance(triple, dict) or any(not isinstance(triple.get(f), str) for f in FIELDS):
            raise ValueError(f"{location}[{index}]: head/relation/tail must all be strings")
        triples.append({f: triple[f] for f in FIELDS})
    return triples


def load_gold(source):
    source = Path(source)
    if source.is_dir():
        files = list(source.glob("*.json"))
        files.sort(key=lambda p: (0, int(p.stem)) if p.stem.isdigit() else (1, p.stem))
        gold = {p.stem: validate_triples(read_json(p), str(p)) for p in files}
    else:
        value = read_json(source)
        if isinstance(value, list):
            value = {"0": value}
        if not isinstance(value, dict):
            raise ValueError("Gold JSON must be a triple list or a mapping of document IDs to lists")
        gold = {key: validate_triples(triples, f"{source}:{key}") for key, triples in value.items()}
    if not gold:
        raise ValueError("Gold source contains no documents")
    return gold


def load_inputs(result_dir, gold_source, allow_legacy_prefix=False):
    """Read manifest by ID or validated legacy 2i/2i+1 files, never silently skip."""
    result_dir, gold_source = Path(result_dir).resolve(), Path(gold_source).resolve()
    if not result_dir.is_dir():
        raise ValueError(f"Result directory does not exist: {result_dir}")
    gold_by_id = load_gold(gold_source)
    if (result_dir / "details" / "_run_manifest.json").is_file():
        result_dir = result_dir / "details"
    manifest_path = result_dir / "_run_manifest.json"
    samples, warnings = [], []
    info = {"result_dir": str(result_dir), "gold_source": str(gold_source)}
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if (not isinstance(manifest, dict) or manifest.get("format") != "karma_run"
                or type(manifest.get("version")) is not int or manifest["version"] != 1
                or manifest.get("complete") is not True
                or manifest.get("stage") not in ("baseline", "revise", "full")):
            raise ValueError("Run manifest is incomplete or unsupported")
        documents = manifest.get("documents")
        if not isinstance(documents, list) or not documents:
            raise ValueError("Run manifest contains no completed documents")
        round_keys = ["1"] if manifest["stage"] == "baseline" else ["1", "2"]
        seen_ids, seen_indices, seen_gold = set(), set(), set()
        for doc in documents:
            if not isinstance(doc, dict):
                raise ValueError("Run manifest document must be an object")
            doc_id, index = doc.get("doc_id"), doc.get("source_index")
            if not isinstance(doc_id, str) or not doc_id or doc_id in seen_ids:
                raise ValueError("Run document IDs must be nonempty and unique")
            if type(index) is not int or index < 0 or index in seen_indices:
                raise ValueError("Run source indices must be nonnegative and unique")
            seen_ids.add(doc_id)
            seen_indices.add(index)
            key = doc_id
            if key not in gold_by_id and gold_source.is_dir():
                key = str(index)
            if key not in gold_by_id:
                raise ValueError(f"Gold missing for document {doc_id!r} (source_index={index})")
            if key in seen_gold:
                raise ValueError(f"Multiple documents resolve to the same Gold key: {key}")
            seen_gold.add(key)
            rounds = doc.get("rounds")
            if not isinstance(rounds, dict) or set(rounds) != set(round_keys):
                raise ValueError(f"Missing/extra rounds for document {doc_id}")
            samples.append({
                "doc_id": doc_id, "gold_key": key, "gold": gold_by_id[key],
                "rounds": {"R" + r: validate_triples(rounds[r], f"{doc_id}:R{r}") for r in round_keys},
            })
        info.update(layout="manifest", stage=manifest["stage"],
                    baseline_sha256=manifest.get("baseline_sha256"), manifest_path=str(manifest_path))
    else:
        numbered = {}
        for path in result_dir.glob("*.json"):
            match = re.fullmatch(r"(\d+)_.+\.json", path.name)
            if match:
                index = int(match.group(1))
                if index in numbered:
                    raise ValueError(f"Duplicate legacy extraction index: {index}")
                numbered[index] = path
        if not numbered:
            raise ValueError("No run manifest or legacy NNN_timestamp.json files found")
        if sorted(numbered) != list(range(len(numbered))):
            raise ValueError("Legacy file indices must be contiguous from zero; cannot infer missing files")
        if len(numbered) % 2:
            raise ValueError("Legacy input must contain both R1 and R2 for every document")
        num_docs = len(numbered) // 2
        if num_docs > len(gold_by_id):
            raise ValueError("More legacy prediction documents than Gold documents")
        if num_docs != len(gold_by_id) and not allow_legacy_prefix:
            raise ValueError(
                "Legacy prediction/Gold counts differ. Supply matching Gold, or use "
                "--allow-legacy-prefix only if predictions are the first N Gold documents."
            )
        warnings.append("Legacy alignment assumes files 2i/2i+1 correspond to Gold in its recorded order; IDs cannot be verified.")
        if num_docs < len(gold_by_id):
            warnings.append(f"Explicit legacy prefix: using first {num_docs} of {len(gold_by_id)} Gold documents.")
        for i, (key, gold) in enumerate(list(gold_by_id.items())[:num_docs]):
            samples.append({"doc_id": key, "gold_key": key, "gold": gold, "rounds": {
                "R1": validate_triples(read_json(numbered[2 * i]), str(numbered[2 * i])),
                "R2": validate_triples(read_json(numbered[2 * i + 1]), str(numbered[2 * i + 1])),
            }})
        info.update(layout="legacy_two_rounds", stage="legacy")
    selected_keys = {s["gold_key"] for s in samples}
    info["unused_gold_ids"] = [key for key in gold_by_id if key not in selected_keys]
    info["warnings"] = warnings
    encoded = json.dumps(samples, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    info["aligned_triples_sha256"] = hashlib.sha256(encoded).hexdigest()
    return samples, info


def _check_number(actual, expected, name):
    # Tolerance is only for serialized floating-point verification, never matching.
    if not math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"CSV/report mismatch for {name}: {actual} != {expected}")


def validate_rows(rows, report):
    """Check one-to-one IDs, token evidence, all denominators and score sums."""
    groups = defaultdict(list)
    for row in rows:
        groups[(row["metric"], row["round"], row["doc"])].append(row)
    allowed = set()
    for mode, mode_results in report["metrics"].items():
        for round_label, result in mode_results.items():
            if round_label not in ("R1", "R2"):
                continue
            round_p, round_r, round_pairs = [], [], 0
            round_np = round_ng = 0
            for doc in result["per_doc"]:
                key = (mode, round_label, doc["doc"])
                allowed.add(key)
                doc_rows = groups[key]
                gold_ids, pred_ids, p_scores, r_scores = [], [], [], []
                matched = 0
                for row in doc_rows:
                    status = row["status"]
                    has_g, has_p = bool(row["gold_id"]), bool(row["pred_id"])
                    expected_sides = {"matched": (True, True), "gold_unmatched": (True, False),
                                      "pred_unmatched": (False, True)}
                    if status not in expected_sides or (has_g, has_p) != expected_sides[status]:
                        raise ValueError(f"Invalid CSV status/IDs: {key}")
                    for side, present, ids in (("gold", has_g, gold_ids), ("pred", has_p, pred_ids)):
                        if present:
                            expected_id = item_id(doc["doc"], round_label, side, int(row[side + "_index"]))
                            if row[side + "_id"] != expected_id:
                                raise ValueError(f"CSV ID/index mismatch: {key}")
                            ids.append(row[side + "_id"])
                    g = {f: row["gold_" + f] for f in FIELDS} if has_g else None
                    p = {f: row["pred_" + f] for f in FIELDS} if has_p else None
                    score = pair_details(g, p, mode)
                    if status == "matched":
                        if not score["eligible"]:
                            raise ValueError(f"Ineligible CSV pair selected: {key}")
                        matched += 1
                    for name in ("precision", "recall", "f1"):
                        _check_number(row["pair_" + name], score[name], name)
                    _check_number(row["exact_after_whitespace_cleanup"], int(score["exact"]), "exact")
                    for field in FIELDS:
                        for side, triple in (("gold", g), ("pred", p)):
                            expected = normalize(triple[field], mode) if triple is not None else ""
                            if row[f"{side}_{field}_normalized"] != expected:
                                raise ValueError(f"CSV normalization mismatch: {key}")
                        for name, expected in score["fields"][field].items():
                            actual = row[f"{field}_{name}"]
                            if isinstance(expected, dict):
                                if json.loads(actual) != expected:
                                    raise ValueError(f"CSV token evidence mismatch: {key}")
                            else:
                                _check_number(actual, expected, name)
                    p_scores.append(float(row["pair_precision"]))
                    r_scores.append(float(row["pair_recall"]))
                for side, ids, count in (("gold", gold_ids, doc["num_gold"]),
                                         ("pred", pred_ids, doc["num_pred"])):
                    expected_ids = {item_id(doc["doc"], round_label, side, i) for i in range(count)}
                    if len(ids) != len(set(ids)) or set(ids) != expected_ids:
                        raise ValueError(f"CSV missing/repeated {side} IDs: {key}")
                reconstructed = summary(math.fsum(p_scores), math.fsum(r_scores), len(pred_ids),
                                        len(gold_ids), matched, mode)
                for name, value in reconstructed.items():
                    _check_number(doc[name], value, f"{key}:{name}")
                round_p.append(reconstructed["precision_sum"])
                round_r.append(reconstructed["recall_sum"])
                round_pairs += matched
                round_np += len(pred_ids)
                round_ng += len(gold_ids)
            reconstructed = summary(math.fsum(round_p), math.fsum(round_r), round_np, round_ng, round_pairs, mode)
            for name, value in reconstructed.items():
                _check_number(result["micro"][name], value, f"{mode}/{round_label}:{name}")
            count = len(result["per_doc"])
            macro_p = math.fsum(d["precision"] for d in result["per_doc"]) / count if count else 0.0
            macro_r = math.fsum(d["recall"] for d in result["per_doc"]) / count if count else 0.0
            for name, value in {"precision": macro_p, "recall": macro_r,
                                "f1": harmonic(macro_p, macro_r)}.items():
                _check_number(result["macro"][name], value, f"{mode}/{round_label}/macro:{name}")
        if "R1" in mode_results and "R2" in mode_results:
            for averaging in ("micro", "macro"):
                for name in ("precision", "recall", "f1"):
                    delta = mode_results["R2"][averaging][name] - mode_results["R1"][averaging][name]
                    _check_number(mode_results["delta_" + averaging][name], delta,
                                  f"{mode}/delta_{averaging}:{name}")
    if set(groups) - allowed:
        raise ValueError("CSV contains unexpected metric/round/document groups")


def save_outputs(report, rows, output_dir, label):
    """Validate memory rows AND reopen the staged CSV before publishing outputs."""
    validate_rows(rows, report)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"match_{label}.csv"
    json_path = output_dir / f"eval_{label}.json"
    temporary_csv = temporary_json = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8-sig",
                                         dir=output_dir, suffix=".csv.tmp", delete=False) as fp:
            temporary_csv = Path(fp.name)
            writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        with temporary_csv.open(newline="", encoding="utf-8-sig") as fp:
            validate_rows(list(csv.DictReader(fp)), report)
        report["csv_verified"] = True
        report["csv_file"] = csv_path.name
        report["csv_sha256"] = hashlib.sha256(temporary_csv.read_bytes()).hexdigest()
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output_dir,
                                         suffix=".json.tmp", delete=False) as fp:
            temporary_json = Path(fp.name)
            json.dump(report, fp, ensure_ascii=False, indent=2, allow_nan=False)
            fp.write("\n")
        temporary_csv.replace(csv_path)
        temporary_json.replace(json_path)
    finally:
        for path in (temporary_csv, temporary_json):
            if path is not None and path.exists():
                path.unlink()
    return json_path, csv_path


def run_cli(mode, argv=None):
    parser = argparse.ArgumentParser(description=f"Offline {mode} one-to-one triple evaluation; no model or similarity threshold.")
    parser.add_argument("result_dir", type=Path, help="Run output/details directory or legacy two-round result directory")
    parser.add_argument("gold_source", type=Path, help="Gold directory, document-ID JSON mapping, or one triple-list JSON")
    parser.add_argument("--output-dir", type=Path, help="Defaults to RESULT_DIR/lexical_evaluation")
    parser.add_argument("--allow-legacy-prefix", action="store_true",
                        help="Explicitly evaluate the first N Gold documents when a legacy run contains only a prefix")
    if mode == "lenient":
        parser.add_argument("--compare-strict", action="store_true", help="Evaluate both modes and save ONE comparison CSV/JSON")
    args = parser.parse_args(argv)
    modes = ["strict", "lenient"] if getattr(args, "compare_strict", False) else [mode]
    label = "comparison" if len(modes) == 2 else mode
    try:
        samples, info = load_inputs(args.result_dir, args.gold_source, args.allow_legacy_prefix)
        for warning in info["warnings"]:
            print("[input] " + warning, file=sys.stderr)
        report, rows = evaluate_samples(samples, modes, info)
        out_dir = args.output_dir or args.result_dir / "lexical_evaluation"
        json_path, csv_path = save_outputs(report, rows, out_dir, label)
        for metric, results in report["metrics"].items():
            for round_label in ("R1", "R2"):
                if round_label in results:
                    s = results[round_label]["micro"]
                    print(f"{metric} {round_label}: P={s['precision']:.6f} R={s['recall']:.6f} F1={s['f1']:.6f} "
                          f"pairs={s['selected_pairs']} pred={s['num_pred']} gold={s['num_gold']}")
            if "delta_micro" in results:
                print(f"{metric} R2-R1: {results['delta_micro']}")
        print(f"JSON: {json_path.resolve()}\nCSV (verified): {csv_path.resolve()}")
    except (ValueError, OSError, csv.Error) as exc:
        print(f"Evaluation error: {exc}", file=sys.stderr)
        return 1
    return 0
