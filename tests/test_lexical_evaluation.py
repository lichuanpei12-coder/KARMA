"""Offline protocol, assignment, input-alignment and CSV regression tests."""
import copy
import csv
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluation_common as ev


def triple(head="vehicle", relation="has", tail="identity"):
    return dict(head=head, relation=relation, tail=tail)


def sample(gold, pred, doc="sample", r2=None):
    rounds = {"R1": pred}
    if r2 is not None:
        rounds["R2"] = r2
    return dict(doc_id=doc, gold_key=doc, gold=gold, rounds=rounds)


class ScoringTests(unittest.TestCase):
    def test_strict_whitespace_only(self):
        g = triple("the vehicle")
        self.assertEqual(ev.pair_details(g, triple(" the\tvehicle\n"), "strict")["f1"], 1)
        for text in ("The vehicle", "the vehicle,", "vehicle the", "vehicle"):
            self.assertEqual(ev.pair_details(g, triple(text), "strict")["f1"], 0)

    def test_repeated_words_use_minimum_counts(self):
        score = ev.pair_details(triple("car car car"), triple("car car"), "lenient")
        self.assertEqual(score["fields"]["head"]["overlap_words"], {"car": 2})
        self.assertEqual(score["fields"]["head"]["gold_missing_words"], {"car": 1})
        self.assertEqual(score["precision"], 1)
        self.assertEqual(score["recall"], 4 / 5)

    def test_each_corresponding_field_requires_overlap(self):
        for field in ev.FIELDS:
            p = triple()
            p[field] = "unrelated"
            self.assertFalse(ev.pair_details(triple(), p, "lenient")["eligible"])
        p = triple("identity", "has", "vehicle")
        self.assertEqual(ev.pair_details(triple(), p, "lenient")["f1"], 0)

    def test_lowercase_and_word_order(self):
        g, p = triple("The Vehicle"), triple("vehicle the")
        self.assertEqual(ev.pair_details(g, p, "lenient")["f1"], 1)
        self.assertEqual(ev.pair_details(triple(tail="10 MW"), triple(tail="10 mW"), "lenient")["f1"], 1)

    def test_no_word_deletion_stemming_or_synonyms(self):
        g = triple("the car", "may not have", "10 MW")
        p = triple("car", "have", "10 MW")
        score = ev.pair_details(g, p, "lenient")
        self.assertEqual(score["precision"], 1)
        self.assertEqual(score["recall"], 4 / 7)
        self.assertEqual(score["fields"]["relation"]["gold_missing_words"], {"may": 1, "not": 1})
        for word in ("cars", "automobile", "car,"):
            self.assertFalse(ev.pair_details(triple("car"), triple(word), "lenient")["eligible"])

    def test_empty_fields_never_match(self):
        for mode in ("strict", "lenient"):
            for field in ev.FIELDS:
                t = triple()
                t[field] = "  "
                self.assertEqual(ev.select_pairs([t], [t], mode), [])

    def test_duplicate_triples_preserved_and_excess_penalized(self):
        for mode in ("strict", "lenient"):
            result, rows = ev.evaluate_round([sample([triple()] * 2, [triple()] * 3)], "R1", mode)
            self.assertEqual(result["micro"]["selected_pairs"], 2)
            self.assertEqual(result["micro"]["precision"], 2 / 3)
            self.assertEqual(result["micro"]["recall"], 1)
            self.assertEqual(result["per_doc"][0]["gold_duplicate_groups"], [[0, 1]])
            self.assertEqual(len(rows), 3)

    def test_aggregate_pair_precision_recall_not_pair_f1(self):
        gold = [triple("a", "b", "c"), triple("d e", "f g", "h i")]
        pred = [triple("a", "b", "c"), triple("d", "f", "h")]
        result, rows = ev.evaluate_round([sample(gold, pred)], "R1", "lenient")
        self.assertEqual(result["micro"]["precision"], 1)
        self.assertEqual(result["micro"]["recall"], .75)
        self.assertAlmostEqual(result["micro"]["f1"], 6 / 7)
        self.assertNotAlmostEqual(result["micro"]["f1"], sum(r["pair_f1"] for r in rows) / 2)

    def test_empty_sides_and_documents(self):
        for mode in ("strict", "lenient"):
            for gold, pred in (([], []), ([triple()], []), ([], [triple()])):
                report, rows = ev.evaluate_samples([sample(gold, pred)], [mode], {})
                self.assertEqual(report["metrics"][mode]["R1"]["micro"]["f1"], 0)
                ev.validate_rows(rows, report)

    def test_macro_and_round_deltas(self):
        samples = [sample([triple()], [triple()], "a", []),
                   sample([triple()] * 3, [], "b", [triple()] * 3)]
        report, rows = ev.evaluate_samples(samples, ["strict"], {})
        r = report["metrics"]["strict"]
        self.assertEqual(r["R1"]["micro"]["recall"], .25)
        self.assertEqual(r["R1"]["macro"]["recall"], .5)
        self.assertEqual(r["delta_micro"]["recall"], .5)
        ev.validate_rows(rows, report)


class AssignmentTests(unittest.TestCase):
    def test_global_assignment_beats_greedy(self):
        self.assertEqual(ev.maximum_weight_pairs([[.9, .8], [.85, .1]]), [(0, 1), (1, 0)])

    def test_rectangular_zeros_and_ties(self):
        self.assertEqual(ev.maximum_weight_pairs([[0, 0]]), [])
        self.assertEqual(ev.maximum_weight_pairs([[.1], [.9], [.2]]), [(1, 0)])
        self.assertEqual(ev.maximum_weight_pairs([[.1, .9, .2]]), [(0, 1)])
        self.assertEqual(ev.maximum_weight_pairs([[1, 1], [1, 1]]), [(0, 0), (1, 1)])
        self.assertEqual(ev.maximum_weight_pairs([[], []]), [])
        for bad in ([[1], [1, 2]], [[], [1]], [[-1]], [[float("nan")]], [[float("inf")]]):
            with self.assertRaises(ValueError):
                ev.maximum_weight_pairs(bad)

    def test_against_exhaustive_assignment(self):
        rng = random.Random(1107)
        for n in range(1, 5):
            for m in range(1, 5):
                for _ in range(20):
                    w = [[rng.randrange(10) / 9 for _ in range(m)] for _ in range(n)]
                    pairs = ev.maximum_weight_pairs(w)
                    self.assertEqual(len(pairs), len({g for g, _ in pairs}))
                    self.assertEqual(len(pairs), len({p for _, p in pairs}))
                    if n <= m:
                        optimal = max(sum(w[i][j] for i, j in enumerate(perm))
                                      for perm in itertools.permutations(range(m), n))
                    else:
                        optimal = max(sum(w[i][j] for j, i in enumerate(perm))
                                      for perm in itertools.permutations(range(n), m))
                    self.assertAlmostEqual(sum(w[g][p] for g, p in pairs), optimal)
                    self.assertEqual(pairs, ev.maximum_weight_pairs(w))


class InputAndExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lexical_test_", dir=ROOT / "tests")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.results = self.root / "results"
        self.results.mkdir()
        self.gold = self.root / "gold.json"
        self.write(self.gold, {"doc": [triple()]})

    def write(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def manifest(self, stage="baseline", documents=None):
        if documents is None:
            rounds = {"1": [triple()]}
            if stage != "baseline":
                rounds["2"] = []
            documents = [dict(doc_id="doc", source_index=0, rounds=rounds)]
        value = dict(format="karma_run", version=1, stage=stage, complete=True, documents=documents)
        self.write(self.results / "_run_manifest.json", value)
        return value

    def test_manifest_rounds_and_empty_prediction(self):
        for stage in ("baseline", "revise", "full"):
            self.manifest(stage)
            samples, info = ev.load_inputs(self.results, self.gold)
            self.assertEqual(list(samples[0]["rounds"]), ["R1"] if stage == "baseline" else ["R1", "R2"])
            self.assertEqual(info["stage"], stage)
            self.assertEqual(len(info["aligned_triples_sha256"]), 64)

    def test_manifest_uses_ids_with_reordered_subset(self):
        self.write(self.gold, {"other": [], "doc": [triple()], "first": [triple("first")]})
        docs = [dict(doc_id="first", source_index=9, rounds={"1": []}),
                dict(doc_id="doc", source_index=2, rounds={"1": []})]
        self.manifest(documents=docs)
        samples, info = ev.load_inputs(self.results, self.gold)
        self.assertEqual(samples[0]["gold"][0]["head"], "first")
        self.assertEqual(info["unused_gold_ids"], ["other"])

    def test_numeric_gold_directory_fallback_and_details(self):
        gold_dir = self.root / "gold"
        gold_dir.mkdir()
        self.write(gold_dir / "0.json", [triple()])
        self.manifest()
        details = self.results / "details"
        details.mkdir()
        (self.results / "_run_manifest.json").rename(details / "_run_manifest.json")
        samples, _ = ev.load_inputs(self.results, gold_dir)
        self.assertEqual(samples[0]["gold_key"], "0")

    def test_bad_manifests_rejected(self):
        original = self.manifest()
        variants = []
        for name, value in (("complete", False), ("version", True), ("stage", "unknown")):
            changed = copy.deepcopy(original)
            changed[name] = value
            variants.append(changed)
        for rounds in ({}, {"1": [], "2": []}, {"1": [{"head": "x"}]}):
            changed = copy.deepcopy(original)
            changed["documents"][0]["rounds"] = rounds
            variants.append(changed)
        changed = copy.deepcopy(original)
        changed["documents"] *= 2
        variants.append(changed)
        changed = copy.deepcopy(original)
        changed["documents"][0]["doc_id"] = "missing"
        variants.append(changed)
        for changed in variants:
            self.write(self.results / "_run_manifest.json", changed)
            with self.assertRaises(ValueError):
                ev.load_inputs(self.results, self.gold)

    def test_duplicate_json_keys_rejected(self):
        self.gold.write_text('{"doc": [], "doc": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            ev.load_gold(self.gold)

    def test_gold_alignment_collision_rejected(self):
        gold_dir = self.root / "gold"
        gold_dir.mkdir()
        self.write(gold_dir / "0.json", [triple()])
        docs = [dict(doc_id="0", source_index=1, rounds={"1": []}),
                dict(doc_id="fallback", source_index=0, rounds={"1": []})]
        self.manifest(documents=docs)
        with self.assertRaisesRegex(ValueError, "same Gold key"):
            ev.load_inputs(self.results, gold_dir)

    def test_legacy_prefix_requires_explicit_flag(self):
        self.write(self.results / "000_123456.json", [triple()])
        self.write(self.results / "001_123457.json", [])
        self.write(self.results / "eval_summary.json", {})
        samples, info = ev.load_inputs(self.results, self.gold)
        self.assertEqual(len(samples), 1)
        self.assertTrue(info["warnings"])
        self.write(self.gold, {"doc": [triple()], "other": []})
        with self.assertRaisesRegex(ValueError, "counts differ"):
            ev.load_inputs(self.results, self.gold)
        samples, info = ev.load_inputs(self.results, self.gold, True)
        self.assertEqual(info["unused_gold_ids"], ["other"])

    def test_legacy_missing_duplicate_and_odd_files_rejected(self):
        first = self.results / "000_123456.json"
        second = self.results / "002_123457.json"
        self.write(first, [])
        with self.assertRaisesRegex(ValueError, "both R1 and R2"):
            ev.load_inputs(self.results, self.gold)
        self.write(second, [])
        with self.assertRaisesRegex(ValueError, "contiguous"):
            ev.load_inputs(self.results, self.gold)
        second.rename(self.results / "000_999999.json")
        with self.assertRaisesRegex(ValueError, "Duplicate legacy"):
            ev.load_inputs(self.results, self.gold)

    def test_csv_roundtrip_unicode_commas_newlines(self):
        g = triple('the "car",\n汽车', "may not have", "10 MW")
        p = triple('the "car",\n汽车', "have", "10 mW")
        samples = [sample([g, g], [p], "doc /中文", [g, p]), sample([], [], "empty", [])]
        report, rows = ev.evaluate_samples(samples, ["strict", "lenient"], {})
        json_path, csv_path = ev.save_outputs(report, rows, self.root, "comparison")
        saved = ev.read_json(json_path)
        self.assertTrue(saved["csv_verified"])
        with csv_path.open(encoding="utf-8-sig", newline="") as fp:
            loaded = list(csv.DictReader(fp))
        self.assertEqual(rows[0]["gold_head"], loaded[0]["gold_head"])
        ev.validate_rows(loaded, saved)

    def test_csv_corruption_detected(self):
        report, rows = ev.evaluate_samples([sample([triple()] * 2, [triple()])], ["lenient"], {})
        changes = [("pair_precision", .3), ("head_overlap_words", "{}"),
                   ("gold_id", "bad"), ("gold_head_normalized", "bad")]
        for field, value in changes:
            bad = copy.deepcopy(rows)
            bad[0][field] = value
            with self.assertRaises(ValueError):
                ev.validate_rows(bad, report)
        with self.assertRaises(ValueError):
            ev.validate_rows(rows + [rows[0]], report)
        with self.assertRaises(ValueError):
            ev.validate_rows(rows[:-1], report)

    def test_cli_both_entrypoints_and_comparison(self):
        self.manifest("revise")
        for script, flags, label in (("evaluate_strict.py", [], "strict"),
                                     ("evaluate_lenient.py", [], "lenient"),
                                     ("evaluate_lenient.py", ["--compare-strict"], "comparison")):
            out = self.root / label
            process = subprocess.run([sys.executable, str(ROOT / script), str(self.results), str(self.gold),
                                      "--output-dir", str(out), *flags], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue((out / f"match_{label}.csv").exists())
        bad = subprocess.run([sys.executable, str(ROOT / "evaluate_strict.py"),
                              str(self.root / "missing"), str(self.gold)], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("Evaluation error", bad.stderr)


if __name__ == "__main__":
    unittest.main()
