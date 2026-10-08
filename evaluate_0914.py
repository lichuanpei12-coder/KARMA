"""KARMA 三元组抽取评估（2026-09-14 多重匹配可审计版）。

本文件保留 evaluate.py 的语义匹配阈值和 P/R 定义，但让评分与 CSV
严格共享同一份匹配矩阵：

1. 每个通过阈值的 (gold, pred) 配对在 CSV 中恰好出现一次；
2. 同一条 pred 可以匹配多个 gold，同一条 gold 也可以匹配多个 pred；
3. Precision 的分子是至少匹配一条 gold 的唯一 pred 数；
4. Recall 的分子是至少被一条 pred 匹配的唯一 gold 数；
5. CSV 行数不直接参与 P/R 计数，避免多重匹配重复计分。

嵌入、数据加载和文档/轮次对齐继续复用原 evaluate.py，避免两个评测器
在非本次目标的地方产生差异。
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import evaluate as legacy


WHOLE_THRESHOLD = legacy.WHOLE_THRESHOLD
ENTITY_THRESHOLD = legacy.ENTITY_THRESHOLD

CSV_FIELDS = [
    "doc",
    "round",
    "gold_id",
    "pred_id",
    "gold_head",
    "gold_relation",
    "gold_tail",
    "pred_head",
    "pred_relation",
    "pred_tail",
    "whole_similarity",
    "entity_similarity",
    "gold_match_count",
    "pred_match_count",
    "match_type",
]


def build_match_graph(gold, pred):
    """建立单篇文档唯一的匹配依据。

    返回的 ``match_mask[gi, pi]`` 是评分和 CSV 共同使用的最终判断。
    ``gold_degree[gi]`` 表示该 gold 匹配的 pred 数；
    ``pred_degree[pi]`` 表示该 pred 匹配的 gold 数。
    """
    num_gold = len(gold)
    num_pred = len(pred)

    if num_gold and num_pred:
        whole_sim, entity_sim = legacy._build_sim_matrices(gold, pred)
    else:
        whole_sim = np.zeros((num_gold, num_pred), dtype=np.float32)
        entity_sim = np.zeros((num_gold, num_pred), dtype=np.float32)

    match_mask = (
        (whole_sim >= WHOLE_THRESHOLD)
        & (entity_sim >= ENTITY_THRESHOLD)
    )

    return {
        "gold": gold,
        "pred": pred,
        "whole_sim": whole_sim,
        "entity_sim": entity_sim,
        "match_mask": match_mask,
        "gold_degree": match_mask.sum(axis=1).astype(int),
        "pred_degree": match_mask.sum(axis=0).astype(int),
    }


def _matched_type(gold_match_count, pred_match_count):
    """根据配对两端的度数标记其所处的匹配结构。"""
    if gold_match_count == 1 and pred_match_count == 1:
        return "one_to_one"
    if gold_match_count == 1 and pred_match_count > 1:
        return "many_gold_to_one_pred"
    if gold_match_count > 1 and pred_match_count == 1:
        return "one_gold_to_many_pred"
    return "many_to_many"


def _gold_id(doc_id, gold_index):
    return f"D{doc_id}-G{gold_index}"


def _pred_id(doc_id, round_label, pred_index):
    return f"D{doc_id}-{round_label}-P{pred_index}"


def graph_to_rows(graph, doc_id, round_label):
    """把匹配图展开为 CSV 行：一条唯一匹配边一行。"""
    gold = graph["gold"]
    pred = graph["pred"]
    whole_sim = graph["whole_sim"]
    entity_sim = graph["entity_sim"]
    match_mask = graph["match_mask"]
    gold_degree = graph["gold_degree"]
    pred_degree = graph["pred_degree"]
    rows = []

    # 所有正式匹配边都输出，不再只展示每条 pred 的最佳 gold。
    for gold_index, pred_index in np.argwhere(match_mask):
        gold_index = int(gold_index)
        pred_index = int(pred_index)
        g = gold[gold_index]
        p = pred[pred_index]
        gold_count = int(gold_degree[gold_index])
        pred_count = int(pred_degree[pred_index])
        rows.append({
            "doc": doc_id,
            "round": round_label,
            "gold_id": _gold_id(doc_id, gold_index),
            "pred_id": _pred_id(doc_id, round_label, pred_index),
            "gold_head": g["head"],
            "gold_relation": g["relation"],
            "gold_tail": g["tail"],
            "pred_head": p["head"],
            "pred_relation": p["relation"],
            "pred_tail": p["tail"],
            "whole_similarity": round(float(whole_sim[gold_index, pred_index]), 6),
            "entity_similarity": round(float(entity_sim[gold_index, pred_index]), 6),
            "gold_match_count": gold_count,
            "pred_match_count": pred_count,
            "match_type": _matched_type(gold_count, pred_count),
        })

    # 未覆盖的 gold 各自输出一行，pred 一侧留空。
    for gold_index, degree in enumerate(gold_degree):
        if int(degree) != 0:
            continue
        g = gold[gold_index]
        rows.append({
            "doc": doc_id,
            "round": round_label,
            "gold_id": _gold_id(doc_id, gold_index),
            "pred_id": "",
            "gold_head": g["head"],
            "gold_relation": g["relation"],
            "gold_tail": g["tail"],
            "pred_head": "",
            "pred_relation": "",
            "pred_tail": "",
            "whole_similarity": "",
            "entity_similarity": "",
            "gold_match_count": 0,
            "pred_match_count": "",
            "match_type": "gold_unmatched",
        })

    # 未匹配的 pred 各自输出一行，gold 一侧留空。
    for pred_index, degree in enumerate(pred_degree):
        if int(degree) != 0:
            continue
        p = pred[pred_index]
        rows.append({
            "doc": doc_id,
            "round": round_label,
            "gold_id": "",
            "pred_id": _pred_id(doc_id, round_label, pred_index),
            "gold_head": "",
            "gold_relation": "",
            "gold_tail": "",
            "pred_head": p["head"],
            "pred_relation": p["relation"],
            "pred_tail": p["tail"],
            "whole_similarity": "",
            "entity_similarity": "",
            "gold_match_count": "",
            "pred_match_count": 0,
            "match_type": "pred_unmatched",
        })

    return rows


def evaluate_round(gold_docs, pred_docs, doc_ids, round_label):
    """评估一轮，并同时生成与评分严格一致的 CSV 行。"""
    total_matched = 0
    total_covered = 0
    total_pred = 0
    total_gold = 0
    per_doc = []
    rows = []

    for local_index, gold in enumerate(gold_docs):
        pred = pred_docs[local_index] if local_index < len(pred_docs) else []
        doc_id = doc_ids[local_index]
        graph = build_match_graph(gold, pred)

        matched = int((graph["pred_degree"] > 0).sum())
        covered = int((graph["gold_degree"] > 0).sum())
        num_pred = len(pred)
        num_gold = len(gold)
        precision = matched / num_pred if num_pred else 0.0
        recall = covered / num_gold if num_gold else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        total_matched += matched
        total_covered += covered
        total_pred += num_pred
        total_gold += num_gold
        per_doc.append({
            "doc": doc_id,
            "matched": matched,
            "covered": covered,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "gold_n": num_gold,
            "pred_n": num_pred,
        })
        rows.extend(graph_to_rows(graph, doc_id, round_label))

    micro_precision = total_matched / total_pred if total_pred else 0.0
    micro_recall = total_covered / total_gold if total_gold else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if micro_precision + micro_recall
        else 0.0
    )
    macro_precision = (
        sum(item["precision"] for item in per_doc) / len(per_doc)
        if per_doc
        else 0.0
    )
    macro_recall = (
        sum(item["recall"] for item in per_doc) / len(per_doc)
        if per_doc
        else 0.0
    )
    macro_f1 = (
        2 * macro_precision * macro_recall / (macro_precision + macro_recall)
        if macro_precision + macro_recall
        else 0.0
    )

    type_counts = Counter(
        row["match_type"]
        for row in rows
        if row["match_type"] not in {"gold_unmatched", "pred_unmatched"}
    )
    result = {
        "micro": {
            "precision": round(micro_precision, 4),
            "recall": round(micro_recall, 4),
            "f1": round(micro_f1, 4),
            "matched": total_matched,
            "covered": total_covered,
        },
        "macro": {
            "precision": round(macro_precision, 4),
            "recall": round(macro_recall, 4),
            "f1": round(macro_f1, 4),
        },
        "per_doc": per_doc,
        "totals": {
            "num_pred": total_pred,
            "num_gold": total_gold,
            "matched": total_matched,
            "covered": total_covered,
            "num_docs": len(per_doc),
            "matched_edges": sum(type_counts.values()),
        },
        "match_type_edge_counts": dict(sorted(type_counts.items())),
    }

    validate_rows_against_result(rows, result, round_label)
    return result, rows


def validate_rows_against_result(rows, result, round_label):
    """断言 CSV 所呈现的配对可精确还原本轮评分。"""
    round_rows = [row for row in rows if row["round"] == round_label]
    matched_rows = [
        row for row in round_rows
        if row["match_type"] not in {"gold_unmatched", "pred_unmatched"}
    ]

    pair_ids = {(row["gold_id"], row["pred_id"]) for row in matched_rows}
    if len(pair_ids) != len(matched_rows):
        raise AssertionError(f"{round_label} CSV 中出现重复 Gold-Pred 配对")

    matched_pred_ids = {row["pred_id"] for row in matched_rows}
    covered_gold_ids = {row["gold_id"] for row in matched_rows}
    all_pred_ids = {row["pred_id"] for row in round_rows if row["pred_id"]}
    all_gold_ids = {row["gold_id"] for row in round_rows if row["gold_id"]}

    expected = result["totals"]
    checks = {
        "matched": (len(matched_pred_ids), expected["matched"]),
        "covered": (len(covered_gold_ids), expected["covered"]),
        "num_pred": (len(all_pred_ids), expected["num_pred"]),
        "num_gold": (len(all_gold_ids), expected["num_gold"]),
    }
    for name, (from_rows, from_score) in checks.items():
        if from_rows != from_score:
            raise AssertionError(
                f"{round_label} CSV/评分不一致: {name} "
                f"CSV={from_rows}, score={from_score}"
            )


def write_match_csv(rows, output_path):
    with open(output_path, "w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _delta(round1, round2, key):
    return round(round2[key] - round1[key], 4)


def _print_round(title, result):
    micro = result["micro"]
    macro = result["macro"]
    totals = result["totals"]
    print(f"\n-- {title} --")
    print(
        f"Micro P/R/F1: {micro['precision']:.4f} / "
        f"{micro['recall']:.4f} / {micro['f1']:.4f} "
        f"(matched={micro['matched']}, covered={micro['covered']})"
    )
    print(
        f"Macro P/R/F1: {macro['precision']:.4f} / "
        f"{macro['recall']:.4f} / {macro['f1']:.4f}"
    )
    print(
        f"pred={totals['num_pred']}, gold={totals['num_gold']}, "
        f"有效配对边={totals['matched_edges']}"
    )
    print(f"配对边类型: {result['match_type_edge_counts']}")


def main():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        result_dir = Path(sys.argv[1])
    else:
        result_dir = legacy.latest_result_dir()

    if not result_dir or not result_dir.exists():
        print(
            "用法: python evaluate_0914.py "
            "[data/result/<时间戳文件夹>] [gold目录或分片文件]"
        )
        print("未找到抽取结果目录。")
        return 1

    extracted, _ = legacy.load_extracted(result_dir)
    if len(sys.argv) > 2 and sys.argv[2].strip():
        gold_source = Path(sys.argv[2])
        print(f"[gold] 手动指定: {gold_source}")
    else:
        print("[gold] 未指定，自动检测领域...")
        gold_source = legacy.detect_gold_dir(extracted)

    gold_docs = legacy.load_gold(gold_source)
    print(f"gold 来源: {gold_source}")
    print(f"抽取目录: {result_dir}")
    print(f"gold 文档数: {len(gold_docs)}")
    print(f"抽取文件数: {len(extracted)}（预期约为 2×gold）")

    gold_common = []
    pred_round1 = []
    pred_round2 = []
    doc_ids = []
    skipped = 0
    for doc_id, gold in enumerate(gold_docs):
        round1_index = 2 * doc_id
        round2_index = round1_index + 1
        if round2_index < len(extracted):
            gold_common.append(gold)
            pred_round1.append(extracted[round1_index])
            pred_round2.append(extracted[round2_index])
            doc_ids.append(doc_id)
        else:
            skipped += 1

    if skipped:
        print(f"[SKIP] {skipped} 篇 gold 缺少完整两轮抽取")
    if not gold_common:
        print("没有可评估的文档（每篇需同时存在 R1 和 R2）。")
        return 1

    print("\n[预计算] 开始嵌入 gold + R1/R2 pred 文本...")
    legacy.precompute_embeddings(gold_common, pred_round1 + pred_round2)
    print("[预计算] 完成")

    result_round1, rows_round1 = evaluate_round(
        gold_common, pred_round1, doc_ids, "R1"
    )
    result_round2, rows_round2 = evaluate_round(
        gold_common, pred_round2, doc_ids, "R2"
    )

    all_rows = rows_round1 + rows_round2
    csv_path = result_dir / "match_details_0914.csv"
    write_match_csv(all_rows, csv_path)

    delta_micro = {
        key: _delta(result_round1["micro"], result_round2["micro"], key)
        for key in ("precision", "recall", "f1")
    }
    delta_macro = {
        key: _delta(result_round1["macro"], result_round2["macro"], key)
        for key in ("precision", "recall", "f1")
    }
    output = {
        "method": "bge-m3 cosine + whole/entity thresholds + non-exclusive matches",
        "thresholds": {
            "whole": WHOLE_THRESHOLD,
            "entity": ENTITY_THRESHOLD,
        },
        "counting": {
            "precision_numerator": "unique matched pred ids",
            "recall_numerator": "unique covered gold ids",
            "csv_unit": "one unique gold-pred edge per row",
        },
        "round1": result_round1,
        "round2": result_round2,
        "delta_micro": delta_micro,
        "delta_macro": delta_macro,
        "match_csv": csv_path.name,
    }
    json_path = result_dir / "eval_result_0914.json"
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(output, fp, ensure_ascii=False, indent=2)

    print("\n" + "=" * 68)
    print("评估结果（评分与 CSV 共用同一匹配矩阵）")
    print(f"阈值: 整条>={WHOLE_THRESHOLD}，头尾>={ENTITY_THRESHOLD}")
    print(f"评估文档数: {len(gold_common)}")
    _print_round("R1 第1次抽取", result_round1)
    _print_round("R2 第2次抽取", result_round2)
    print("\n-- R2 - R1 --")
    print(
        f"Micro P:{delta_micro['precision']:+.4f} "
        f"R:{delta_micro['recall']:+.4f} "
        f"F1:{delta_micro['f1']:+.4f}"
    )
    print(
        f"Macro P:{delta_macro['precision']:+.4f} "
        f"R:{delta_macro['recall']:+.4f} "
        f"F1:{delta_macro['f1']:+.4f}"
    )
    print(f"\n匹配明细: {csv_path}")
    print(f"评估汇总: {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
