"""evaluate.py — KARMA 三元组抽取评估（余弦相似度 + 二值评分 + gold 侧非独占）。

对齐方式（选项A，按调用顺序）：
  pipeline 每篇文档调用 evaluator.process 两次（内层 for t in range(2)），
  故抽取文件序号 2i = 文档i第1轮，2i+1 = 文档i第2轮（最终结果）。
  gold[i] 对齐抽取文件 2i+1。

匹配方式（整条拼接 + 头尾守卫 + 二值评分 + gold 侧非独占）：
  1. 整条三元组拼接 (head + relation + tail) 算余弦相似度 → 主判断
  2. 头尾合并 (head + tail) 算余弦相似度 → 守卫，低于阈值则否决
  3. 每条 pred 独立找最佳 gold，一条 gold 可被多条 pred 匹配
  4. P = matched_preds / total_pred, R = gold_covered / total_gold
     matched_preds = 匹配上至少一条 gold 的 pred 数
     gold_covered = 被至少一条 pred 匹配上的 gold 数
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import httpx

GOLD_DIR = Path("data/DocIOE/transport")
RESULT_ROOT = Path("data/result")

# ---------- 余弦相似度配置 ----------

WHOLE_THRESHOLD = 0.76
ENTITY_THRESHOLD = 0.40  # 头尾守卫（经全量验证，0.68误杀12条正确匹配，降至0.40）
EMBED_MODEL = "bge-m3"
EMBED_BATCH_SIZE = 64
_embed_cache = {}  # text -> np.array, 全局缓存


def _load_env():
    """加载项目根目录 .env 文件（与 load_env.py 同逻辑）。"""
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v


def _cosine_sim(a, b):
    """计算两个向量的余弦相似度（向量已归一化，直接点积）。"""
    return float(np.dot(a, b))


def precompute_embeddings(gold_docs, pred_docs):
    """收集所有唯一的 relation 和 entity 文本，批量嵌入并缓存。

    gold_docs / pred_docs: 三元组列表的列表（每文档一个列表）。
    """
    _load_env()
    api_key = os.getenv("KARMA_API_KEY", "")
    proxy = os.getenv("KARMA_PROXY", "")
    base_url = "https://api.modelarts-maas.com/v1/embeddings"

    if not api_key:
        raise RuntimeError("KARMA_API_KEY 未设置，请检查 .env 文件")

    # 收集所有唯一文本（整条三元组 + 头尾合并）
    texts = set()
    for docs in (gold_docs, pred_docs):
        for triples in docs:
            for t in triples:
                texts.add(_serialize_triple(t))
                texts.add(_serialize_entity(t))
    texts.discard("")  # 跳过空串
    text_list = sorted(texts)  # 确定性顺序

    # 跳过已缓存的
    new_texts = [t for t in text_list if t not in _embed_cache]
    if not new_texts:
        print(f"[embed] 全部 {len(text_list)} 个文本已缓存，跳过 API 调用")
        return

    print(f"[embed] 需嵌入 {len(new_texts)} 个唯一文本 (模型: {EMBED_MODEL})")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for i in range(0, len(new_texts), EMBED_BATCH_SIZE):
        batch = new_texts[i:i + EMBED_BATCH_SIZE]
        payload = {"model": EMBED_MODEL, "input": batch}

        for attempt in range(4):
            try:
                with httpx.Client(proxy=proxy or None, verify=False, timeout=60.0) as client:
                    r = client.post(base_url, json=payload, headers=headers)
                    if r.status_code == 200:
                        data = r.json()
                        for j, item in enumerate(data["data"]):
                            vec = np.array(item["embedding"], dtype=np.float32)
                            norm = np.linalg.norm(vec)
                            if norm > 0:
                                vec = vec / norm  # 归一化，之后点积=余弦相似度
                            _embed_cache[batch[j]] = vec
                        break
                    elif r.status_code == 429:
                        wait = min(2 ** attempt, 16)
                        print(f"[embed] 429 限流，等待 {wait}s 后重试 ({attempt+1}/4)")
                        time.sleep(wait)
                    else:
                        raise RuntimeError(f"API {r.status_code}: {r.text[:200]}")
            except RuntimeError:
                raise
            except Exception as e:
                if attempt < 3:
                    wait = min(2 ** attempt, 16)
                    print(f"[embed] 错误，等待 {wait}s 后重试: {str(e)[:100]}")
                    time.sleep(wait)
                else:
                    raise

        done = min(i + EMBED_BATCH_SIZE, len(new_texts))
        print(f"[embed] 进度 {done}/{len(new_texts)}")

    print(f"[embed] 完成，缓存 {len(_embed_cache)} 个向量")


def _get_embedding(text):
    """从缓存获取嵌入向量，若未缓存则报错。"""
    key = text.lower().strip()
    if key not in _embed_cache:
        raise KeyError(f"嵌入缓存缺失: '{key}'，请先调用 precompute_embeddings()")
    return _embed_cache[key]


def _serialize_triple(t):
    """整条三元组拼接: head + relation + tail。"""
    return (t["head"] + " " + t["relation"] + " " + t["tail"]).lower().strip()


def _serialize_entity(t):
    """头尾合并: head + tail（允许头尾互换）。"""
    return (t["head"] + " " + t["tail"]).lower().strip()


def _build_sim_matrices(gold, pred):
    """用归一化向量的矩阵乘法，一次算出整条和头尾的相似度矩阵。

    返回 (whole_sim, ent_sim)，均为 np.ndarray shape=(len(gold), len(pred))。
    空串三元组用零向量填充，相似度为 0（不匹配）。
    """
    _zero = np.zeros(1024, dtype=np.float32)  # bge-m3 维度

    def _safe_vec(text, serialize_fn):
        key = serialize_fn(text)
        if not key:
            return _zero
        return _get_embedding(key)

    g_full = np.array([_safe_vec(g, _serialize_triple) for g in gold])
    p_full = np.array([_safe_vec(p, _serialize_triple) for p in pred])
    g_ent = np.array([_safe_vec(g, _serialize_entity) for g in gold])
    p_ent = np.array([_safe_vec(p, _serialize_entity) for p in pred])

    whole_sim = g_full @ p_full.T  # (len_gold, len_pred)
    ent_sim = g_ent @ p_ent.T
    return whole_sim, ent_sim


# ---------- 匹配（整条拼接 + 头尾守卫） ----------

def match_pair(gold, pred, raw=False):
    """gold/pred: {head, relation, tail}。返回相似度 (float)。

    供 generate_match_rows (CSV) 使用。greedy_doc 用矩阵乘法替代逐对调用。
    两道检查都通过 → 返回整条相似度；任一不通过 → 返回 0.0。
    raw=True 时返回整条原始相似度（不卡阈值），供 CSV 显示未匹配对的接近程度。
    """
    g_full = _serialize_triple(gold)
    p_full = _serialize_triple(pred)
    if not g_full or not p_full:
        return 0.0
    full_sim = _cosine_sim(_get_embedding(g_full), _get_embedding(p_full))
    if raw:
        return full_sim
    if full_sim < WHOLE_THRESHOLD:
        return 0.0

    g_ent = _serialize_entity(gold)
    p_ent = _serialize_entity(pred)
    if not g_ent or not p_ent:
        return 0.0
    ent_sim = _cosine_sim(_get_embedding(g_ent), _get_embedding(p_ent))
    if ent_sim < ENTITY_THRESHOLD:
        return 0.0

    return full_sim


# ---------- 贪心配对（移植 carb.py compare 单点版） ----------

def greedy_doc(gold, pred):
    """单文档匹配（二值评分 + gold 侧非独占）。返回 (matched_preds, gold_covered, num_pred, num_gold)。

    每条 pred 独立找最佳 gold，一条 gold 可被多条 pred 匹配。
    matched_preds = 匹配上至少一条 gold 的 pred 数（用于 precision）
    gold_covered = 被至少一条 pred 匹配的唯一 gold 数（用于 recall）
    """
    if not pred:
        return (0, 0, 0, len(gold))
    if not gold:
        return (0, 0, len(pred), 0)

    whole_sim, ent_sim = _build_sim_matrices(gold, pred)

    # 两道阈值都通过的位置才算匹配
    match_mask = (whole_sim >= WHOLE_THRESHOLD) & (ent_sim >= ENTITY_THRESHOLD)
    # shape: (len_gold, len_pred)

    # 每条 pred 是否有至少一条 gold 匹配（列方向 any）
    matched_preds = int(match_mask.any(axis=0).sum())
    # 每条 gold 是否有至少一条 pred 匹配（行方向 any）
    gold_covered = int(match_mask.any(axis=1).sum())

    return (matched_preds, gold_covered, len(pred), len(gold))


def evaluate(gold_docs, pred_docs):
    """gold_docs[i] / pred_docs[i] = 该文档的三元组列表。"""
    total_matched = 0   # 匹配上的 pred 总数（用于 precision）
    total_covered = 0   # 被覆盖的 gold 总数（用于 recall）
    total_npd = total_ngd = 0
    per_doc = []
    for i, gold in enumerate(gold_docs):
        pred = pred_docs[i] if i < len(pred_docs) else []
        matched, covered, npd, ngd = greedy_doc(gold, pred)
        total_matched += matched
        total_covered += covered
        total_npd += npd
        total_ngd += ngd
        p = matched / npd if npd else 0.0
        r = covered / ngd if ngd else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        per_doc.append({"doc": i, "matched": matched, "covered": covered,
                        "precision": round(p, 4), "recall": round(r, 4),
                        "f1": round(f, 4), "gold_n": ngd, "pred_n": npd})

    micro_p = total_matched / total_npd if total_npd else 0.0
    micro_r = total_covered / total_ngd if total_ngd else 0.0
    micro_f = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) else 0.0
    macro_p = sum(d["precision"] for d in per_doc) / len(per_doc) if per_doc else 0.0
    macro_r = sum(d["recall"] for d in per_doc) / len(per_doc) if per_doc else 0.0
    macro_f = 2 * macro_p * macro_r / (macro_p + macro_r) if (macro_p + macro_r) else 0.0

    return {
        "micro": {"precision": round(micro_p, 4), "recall": round(micro_r, 4),
                  "f1": round(micro_f, 4), "matched": total_matched, "covered": total_covered},
        "macro": {"precision": round(macro_p, 4), "recall": round(macro_r, 4),
                  "f1": round(macro_f, 4)},
        "per_doc": per_doc,
        "totals": {"num_pred": total_npd, "num_gold": total_ngd,
                   "matched": total_matched, "covered": total_covered,
                   "num_docs": len(per_doc)},
    }
def generate_match_rows(gold_docs, pred_docs, round_label):
    """生成每条 pred 三元组的最佳匹配明细，返回行列表。

    gold 侧非独占：每条 pred 独立找自己最接近的 gold，一条 gold 可被多条 pred 匹配。
    """
    rows = []
    for i, gold in enumerate(gold_docs):
        pred = pred_docs[i] if i < len(pred_docs) else []

        if not gold:
            for p in pred:
                rows.append({'doc': i, 'round': round_label, 'type': 'pred_only',
                             'gold_head': '', 'gold_relation': '', 'gold_tail': '',
                             'pred_head': p['head'], 'pred_relation': p['relation'], 'pred_tail': p['tail'],
                             'similarity': 0})
            continue

        if not pred:
            for g in gold:
                rows.append({'doc': i, 'round': round_label, 'type': 'gold_only',
                             'gold_head': g['head'], 'gold_relation': g['relation'], 'gold_tail': g['tail'],
                             'pred_head': '', 'pred_relation': '', 'pred_tail': '',
                             'similarity': 0})
            continue

        # 每条 pred 独立找最佳 gold（非独占，gold 可被多条 pred 匹配）
        matched_gold_indices = set()  # 记录被匹配上的 gold 索引
        for pj, p in enumerate(pred):
            best_gi, best_sim = -1, 0.0
            for gi, g in enumerate(gold):
                sim = match_pair(g, p)  # 过阈值返回相似度，不过返回 0
                if sim > best_sim:
                    best_sim = sim
                    best_gi = gi

            if best_gi >= 0 and best_sim > 0:
                # 匹配上：显示匹配的 gold
                g = gold[best_gi]
                matched_gold_indices.add(best_gi)
                rows.append({'doc': i, 'round': round_label, 'type': 'matched',
                             'gold_head': g['head'], 'gold_relation': g['relation'], 'gold_tail': g['tail'],
                             'pred_head': p['head'], 'pred_relation': p['relation'], 'pred_tail': p['tail'],
                             'similarity': round(best_sim, 4)})
            else:
                # 没匹配上：用原始相似度找最接近的 gold（显示接近程度）
                best_gi = max(range(len(gold)),
                              key=lambda gi: match_pair(gold[gi], p, raw=True))
                g = gold[best_gi]
                raw_sim = match_pair(g, p, raw=True)
                rows.append({'doc': i, 'round': round_label, 'type': 'pred_unmatched',
                             'gold_head': g['head'], 'gold_relation': g['relation'], 'gold_tail': g['tail'],
                             'pred_head': p['head'], 'pred_relation': p['relation'], 'pred_tail': p['tail'],
                             'similarity': round(raw_sim, 4)})

        # 没被任何 pred 匹配上的 gold（非独占：只要任何 pred 过阈值就算覆盖）
        for gi, g in enumerate(gold):
            # 检查这条 gold 是否被任何 pred 匹配（不只是"最佳"）
            any_match = any(match_pair(g, pred[pj]) > 0 for pj in range(len(pred)))
            if not any_match:
                rows.append({'doc': i, 'round': round_label, 'type': 'gold_unmatched',
                             'gold_head': g['head'], 'gold_relation': g['relation'], 'gold_tail': g['tail'],
                             'pred_head': '', 'pred_relation': '', 'pred_tail': '',
                             'similarity': 0})
    return rows


def write_match_csv(rows, output_path):
    """将匹配明细行列表写入 CSV 文件。"""
    fieldnames = ['doc', 'round', 'type',
                  'gold_head', 'gold_relation', 'gold_tail',
                  'pred_head', 'pred_relation', 'pred_tail',
                  'similarity']
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------- 数据加载 ----------

def load_gold(gold_source):
    """加载 Gold，返回 ``[triples, ...]``（每个样本一个三元组列表）。

    支持两种格式：
    1. DocIOE 旧格式目录：``0.json..N.json``，每个文件是一篇文档的三元组列表；
    2. BenchIE 分片文件：一个 JSON 对象，键为 ``benchie_<id>``，值为该句 Gold 列表。
    """
    gold_source = Path(gold_source)

    def load_file(path):
        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, list):
            return [data]
        if isinstance(data, dict):
            docs = []
            for sample_id, triples in data.items():
                if not isinstance(triples, list):
                    raise ValueError(
                        f"Gold 样本 {sample_id!r} 应为三元组列表: {path}"
                    )
                docs.append(triples)
            return docs
        raise ValueError(f"不支持的 Gold JSON 根类型: {path}")

    if gold_source.is_file():
        return load_file(gold_source)

    docs = []
    files = sorted(
        [f for f in os.listdir(gold_source) if f.endswith(".json")],
        key=lambda f: int(Path(f).stem),
    )
    for filename in files:
        docs.extend(load_file(gold_source / filename))
    return docs


def load_extracted(result_dir):
    """读 data/result/{ts}/NNN_HHMMSS.json，按序号排序，返回 ([triples, ...], [filename, ...])。
    跳过非 NNN_ 前缀的文件（如 eval_result.json）。"""
    docs = []
    files = []
    for f in os.listdir(result_dir):
        if not f.endswith(".json"):
            continue
        prefix = f.split("_")[0]
        if prefix.isdigit():
            files.append(f)
    files.sort(key=lambda f: int(f.split("_")[0]))
    for f in files:
        with open(result_dir / f, encoding="utf-8") as fp:
            docs.append(json.load(fp))
    return docs, files


def latest_result_dir():
    """自动选 data/result 下最新的时间戳文件夹。"""
    if not RESULT_ROOT.exists():
        return None
    subs = [d for d in RESULT_ROOT.iterdir() if d.is_dir()]
    if not subs:
        return None
    return max(subs, key=lambda d: d.name)


# gold 候选目录：名字 -> 路径
GOLD_CANDIDATES = {
    "transportation": Path("data/DocIOE/transport"),
}


def detect_gold_dir(extracted):
    """根据抽取三元组的关系词，自动判断用哪个 gold 目录。

    对每个候选 gold 目录，采样前 5 个文件，统计其关系词与抽取关系词的交集大小，
    选交集最大的（领域匹配度最高）。
    """
    # 收集抽取的关系词
    pred_words = set()
    for doc in extracted:
        for t in doc:
            for w in t["relation"].lower().split():
                pred_words.add(w)

    best_dir, best_score, best_name = GOLD_DIR, -1, "healthcare(default)"
    for name, gdir in GOLD_CANDIDATES.items():
        if not gdir.exists():
            continue
        gold_words = set()
        files = sorted([f for f in os.listdir(gdir) if f.endswith(".json")],
                       key=lambda f: int(f.split(".")[0]))[:5]
        for f in files:
            with open(gdir / f, encoding="utf-8") as fp:
                for t in json.load(fp):
                    for w in t["relation"].lower().split():
                        gold_words.add(w)
        score = len(pred_words & gold_words)
        print(f"  [auto-detect] {name:<14} 关系词重叠 {score}")
        if score > best_score:
            best_score = score
            best_dir = gdir
            best_name = name

    print(f"  [auto-detect] 选用: {best_name} ({best_dir})")
    return best_dir


def main():
    result_dir = None
    # 第 1 参数为空串或不传 → 自动选最新时间戳文件夹
    if len(sys.argv) > 1 and sys.argv[1].strip():
        result_dir = Path(sys.argv[1])
    else:
        result_dir = latest_result_dir()
    if not result_dir or not result_dir.exists():
        print("用法: python evaluate.py [data/result/<时间戳文件夹>] [gold目录或分片文件]")
        print("  不指定抽取目录则自动选最新；不指定 gold 来源则自动检测领域")
        print("未指定抽取目录且 data/result 下无时间戳文件夹，请先跑 pipeline 生成抽取结果。")
        return 1

    # 先加载抽取结果（gold 自动检测需要用到）
    extracted, extracted_files = load_extracted(result_dir)

    # gold 来源（目录或 BenchIE 分片文件）：第 2 个参数指定，否则自动检测领域
    if len(sys.argv) > 2 and sys.argv[2].strip():
        gold_dir = Path(sys.argv[2])
        print(f"[gold] 手动指定: {gold_dir}")
    else:
        print("[gold] 未指定，自动检测领域...")
        gold_dir = detect_gold_dir(extracted)

    print(f"gold 来源: {gold_dir}")
    print(f"抽取目录: {result_dir}")

    gold_docs = load_gold(gold_dir)
    print(f"gold 文档数: {len(gold_docs)}")
    print(f"抽取文件数: {len(extracted)}（预期 ≈ 2×gold）")

    # 对齐：每篇文档有两次抽取
    #   序号 2i   = 第 1 次抽取（无反馈）
    #   序号 2i+1 = 第 2 次抽取（自反馈后，最终结果）
    # 只评估两次抽取都有的文档，保证 round1 vs round2 对比公平
    gold_common = []
    pred_r1 = []   # 第 1 次
    pred_r2 = []   # 第 2 次
    common_indices = []  # 原始 gold 文档索引
    skipped = 0
    for i in range(len(gold_docs)):
        idx_r1 = 2 * i
        idx_r2 = 2 * i + 1
        if idx_r1 < len(extracted) and idx_r2 < len(extracted):
            gold_common.append(gold_docs[i])
            pred_r1.append(extracted[idx_r1])
            pred_r2.append(extracted[idx_r2])
            common_indices.append(i)
        else:
            skipped += 1
    if skipped:
        print(f"[SKIP] {skipped} 篇 gold 缺少某次抽取，跳过"
              f"（只评估两次都有的 {len(gold_common)} 篇）")

    if not gold_common:
        print("没有可评估的文档（需至少一篇有两次抽取结果）")
        return 1

    # 预计算所有文本的嵌入向量（gold + 两次抽取的所有文本）
    print("\n[预计算] 开始嵌入 gold + pred 文本...")
    precompute_embeddings(gold_common, pred_r1 + pred_r2)
    print("[预计算] 完成\n")

    result_r1 = evaluate(gold_common, pred_r1)
    result_r2 = evaluate(gold_common, pred_r2)

    def d(r1, r2, key):
        return round(r2[key] - r1[key], 4)

    print("\n" + "=" * 60)
    print(" 评估结果（余弦相似度 bge-m3 + 整条拼接 + 头尾守卫 + 二值评分）")
    print(f" 阈值: 整条>={WHOLE_THRESHOLD} 头尾>={ENTITY_THRESHOLD}")
    print("=" * 60)
    print(f"评估文档数: {len(gold_common)}")
    print("Micro: 所有文档的 matched/covered 加总后算 P/R/F1（大文档权重更高）")
    print("Macro: 先算每篇文档的 P/R/F1，再取算术平均（每篇文档权重相同）")
    print()
    print("-- 第 1 次抽取（无反馈）--")
    print(f"Micro P/R/F1: {result_r1['micro']['precision']:.4f} / "
          f"{result_r1['micro']['recall']:.4f} / {result_r1['micro']['f1']:.4f}"
          f"  (matched={result_r1['micro']['matched']}, covered={result_r1['micro']['covered']})")
    print(f"Macro P/R/F1: {result_r1['macro']['precision']:.4f} / "
          f"{result_r1['macro']['recall']:.4f} / {result_r1['macro']['f1']:.4f}")
    print(f"抽取: {result_r1['totals']['num_pred']}, "
          f"gold: {result_r1['totals']['num_gold']}, "
          f"matched: {result_r1['totals']['matched']}, "
          f"covered: {result_r1['totals']['covered']}")
    print()
    print("-- 第 2 次抽取（自反馈后）--")
    print(f"Micro P/R/F1: {result_r2['micro']['precision']:.4f} / "
          f"{result_r2['micro']['recall']:.4f} / {result_r2['micro']['f1']:.4f}"
          f"  (matched={result_r2['micro']['matched']}, covered={result_r2['micro']['covered']})")
    print(f"Macro P/R/F1: {result_r2['macro']['precision']:.4f} / "
          f"{result_r2['macro']['recall']:.4f} / {result_r2['macro']['f1']:.4f}")
    print(f"抽取: {result_r2['totals']['num_pred']}, "
          f"gold: {result_r2['totals']['num_gold']}, "
          f"matched: {result_r2['totals']['matched']}, "
          f"covered: {result_r2['totals']['covered']}")
    print()
    print("-- 自反馈提升（第2次 - 第1次）--")
    print(f"Micro  P:{d(result_r1['micro'], result_r2['micro'], 'precision'):+.4f} "
          f"R:{d(result_r1['micro'], result_r2['micro'], 'recall'):+.4f} "
          f"F1:{d(result_r1['micro'], result_r2['micro'], 'f1'):+.4f}")
    print(f"Macro  P:{d(result_r1['macro'], result_r2['macro'], 'precision'):+.4f} "
          f"R:{d(result_r1['macro'], result_r2['macro'], 'recall'):+.4f} "
          f"F1:{d(result_r1['macro'], result_r2['macro'], 'f1'):+.4f}")

    # 每篇文档对比明细
    print()
    print("-- 每篇文档对比 --")
    hdr = (f"{'doc':<5}{'gold':<6}"
           f"{'R1抽':<6}{'R1匹':<6}{'R1覆':<6}{'R1P':<8}{'R1R':<8}{'R1F1':<8}"
           f"{'R2抽':<6}{'R2匹':<6}{'R2覆':<6}{'R2P':<8}{'R2R':<8}{'R2F1':<8}"
           f"{'dF1':<8}")
    print(hdr)
    print("-" * len(hdr))
    for r1d, r2d in zip(result_r1['per_doc'], result_r2['per_doc']):
        df1 = round(r2d['f1'] - r1d['f1'], 4)
        print(f"{r1d['doc']:<5}{r1d['gold_n']:<6}"
              f"{r1d['pred_n']:<6}{r1d['matched']:<6}{r1d['covered']:<6}"
              f"{r1d['precision']:<8.4f}{r1d['recall']:<8.4f}{r1d['f1']:<8.4f}"
              f"{r2d['pred_n']:<6}{r2d['matched']:<6}{r2d['covered']:<6}"
              f"{r2d['precision']:<8.4f}{r2d['recall']:<8.4f}{r2d['f1']:<8.4f}"
              f"{df1:+.4f}")

    # 生成匹配明细 CSV（每篇文档每轮一个，文件名与抽取结果 JSON 同名）
    for j in range(len(gold_common)):
        i = common_indices[j]
        # R1
        rows_r1 = generate_match_rows([gold_common[j]], [pred_r1[j]], "R1")
        for r in rows_r1:
            r['doc'] = i
        csv_name_r1 = extracted_files[2 * i].replace('.json', '.csv')
        write_match_csv(rows_r1, result_dir / csv_name_r1)
        # R2
        rows_r2 = generate_match_rows([gold_common[j]], [pred_r2[j]], "R2")
        for r in rows_r2:
            r['doc'] = i
        csv_name_r2 = extracted_files[2 * i + 1].replace('.json', '.csv')
        write_match_csv(rows_r2, result_dir / csv_name_r2)
    print(f"\n[CSV] 匹配明细已生成 {len(gold_common) * 2} 个文件（与抽取结果 JSON 同名）")

    out_path = result_dir / "eval_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "round1": result_r1,
            "round2": result_r2,
            "delta_micro": {
                "precision": d(result_r1['micro'], result_r2['micro'], 'precision'),
                "recall": d(result_r1['micro'], result_r2['micro'], 'recall'),
                "f1": d(result_r1['micro'], result_r2['micro'], 'f1'),
            },
            "delta_macro": {
                "precision": d(result_r1['macro'], result_r2['macro'], 'precision'),
                "recall": d(result_r1['macro'], result_r2['macro'], 'recall'),
                "f1": d(result_r1['macro'], result_r2['macro'], 'f1'),
            },
        }, f, ensure_ascii=False, indent=2)
    print(f"\n 详细结果: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
