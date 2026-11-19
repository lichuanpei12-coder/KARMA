import json
import tempfile
import unittest
from pathlib import Path

from evaluate_benchie import DEFAULT_GOLD, evaluate_exact, load_clusters, main
from evaluation_common import HAN_PROTOCOL, evaluate_samples
from karma.core.data_structures import KnowledgeTriple
from karma.core.triple_overlap import rank_triple_overlap
from lexical_tokens import overlap_tokens


def triple(head, relation, tail):
    return {"head": head, "relation": relation, "tail": tail}


class BenchieEvaluationTests(unittest.TestCase):
    def test_chinese_overlap_is_shared_by_remove_and_lenient_evaluation(self):
        gold = triple("设备GPS2", "曾担任", "岗位")
        pred = triple("设备GPS2", "担任", "岗位")
        self.assertEqual(overlap_tokens("设备GPS2"), ["设", "备", "gps2"])
        self.assertEqual(overlap_tokens("The lab, GPS2"), ["the", "lab,", "gps2"])
        report, rows = evaluate_samples([{"doc_id": "doc", "gold_key": "doc",
                                          "gold": [gold], "rounds": {"R1": [pred]}}],
                                        ["lenient"], {})
        self.assertEqual(report["protocol"], HAN_PROTOCOL)
        self.assertEqual(rows[0]["relation_overlap_count"], 2)
        ranked = rank_triple_overlap([KnowledgeTriple(**gold), KnowledgeTriple(**pred)], "V0")
        self.assertEqual(ranked["pairs"][0]["left_only_words"], {"曾": 1})
        self.assertAlmostEqual(ranked["pairs"][0]["overlap_f1"], rows[0]["pair_f1"])

    def test_real_gold_and_cli_score_each_stage_by_sample_id(self):
        gold = load_clusters(DEFAULT_GOLD)
        self.assertEqual(len(gold), 300)
        self.assertEqual(sum(map(len, gold.values())), 996)
        self.assertEqual(gold["benchie-zh-249"], [])
        self.assertEqual([cluster["cluster_id"] for cluster in gold["benchie-zh-206"]], [1, 2, 3, 4])
        prime_minister = triple("他", "曾担任", "澳大利亚第一任总理")
        spaced_duplicate = triple("他", "曾担任", "澳 大 利 亚 第 一 任 总 理")
        judge = triple("他", "成为", "澳大利亚高等法院的创始法官")
        omitted_qualifier = triple("他", "担任", "澳大利亚第一任总理")
        manifest = {"format": "karma_run", "version": 1, "complete": True, "stage": "revise",
                    "documents": [{"doc_id": "benchie-zh-001", "source_index": 0,
                                   "rounds": {"1": [prime_minister, spaced_duplicate, omitted_qualifier],
                                              "2": [prime_minister, judge]},
                                   "stages": {"after_split": [prime_minister, spaced_duplicate]}}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            details = root / "details"
            details.mkdir()
            (details / "_run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(main([directory]), 0)
            report = json.loads((root / "benchie_evaluation/eval_benchie.json").read_text(encoding="utf-8"))
        stages = report["stages"]
        self.assertEqual(list(stages), ["baseline", "after_split", "final"])
        exact = stages["baseline"]["benchie_exact"]
        self.assertEqual((exact["tp"], exact["fp"], exact["fn"], exact["additional_same_cluster_hits"]),
                         (1, 1, 1, 1))
        self.assertEqual(stages["after_split"]["benchie_exact"]["precision"], 1.0)
        self.assertEqual(stages["final"]["benchie_exact"]["f1"], 1.0)
        self.assertEqual(stages["final"]["han_overlap_lenient"]["f1"], 1.0)

    def test_shared_variant_only_covers_first_cluster(self):
        shared_variant = triple("该节目", "出现", "节目元素")
        clusters = [{"cluster_id": cluster_id, "variants": [shared_variant]} for cluster_id in (2, 3, 4)]
        scores = evaluate_exact([shared_variant], clusters)
        match = scores["predictions"][0]
        self.assertEqual(match["candidate_cluster_ids"], [2, 3, 4])
        self.assertEqual(match["cluster_id"], 2)
        self.assertEqual(scores["tp"], 1)
