"""Sentence provenance and grouping shared by extraction and feedback.

IDs are document-local. Legacy triples without reliable provenance remain visible
in an unassigned group; lexical similarity alone never assigns a source sentence.
"""

import re


def source_sentences(text, supplied=None):
    """Prefer dataset sentence boundaries; otherwise split ordinary prose locally."""
    if supplied is not None:
        parts = [s.strip() for s in supplied if isinstance(s, str) and s.strip()]
        if " ".join(" ".join(parts).split()) != " ".join(text.split()):
            raise ValueError("Source sentence list does not match extraction text")
    else:
        # Protect decimals, initials, and common abbreviations from period splitting.
        protected = re.sub(
            r"\b(?:e\.g\.|i\.e\.|Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Fig\.|Figs\.|No\.|Nos\.|vs\.|etc\.|(?:[A-Z]\.){2,}|[A-Z]\.(?=\s+[A-Z]))",
            lambda m: m.group().replace('.', '\ue000'), text,
        )
        parts = re.split(r'(?<=[。！？!?])\s*|(?<=\.)\s+|\n+', protected)
        parts = [p.replace('\ue000', '.').strip() for p in parts if p.strip()]
    return [{"sentence_id": f"S{i + 1}", "text": part} for i, part in enumerate(parts)]


def valid_ids(value, sentences):
    allowed = {s['sentence_id'] for s in sentences}
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(x for x in value if isinstance(x, str) and x in allowed))


def infer_ids(triple, sentences, evidence=""):
    """Use exact evidence or exact SPO containment, never best-overlap guesses."""
    norm = lambda s: " ".join(s.split())
    evidence = norm(evidence)
    if evidence:
        matches = [s['sentence_id'] for s in sentences if evidence in norm(s['text'])]
        if matches:
            return matches
    fields = [norm(getattr(triple, key)) for key in ('head', 'relation', 'tail')]
    return [s['sentence_id'] for s in sentences
            if all(value and value in norm(s['text']) for value in fields)]


def attach_sources(triple, sentences, item=None, parent=None):
    """Validate model IDs; recover old exact matches or retain parent provenance."""
    item = item or {}
    evidence = item.get('evidence', item.get('context', ''))
    if not isinstance(evidence, str):
        evidence = ''
    ids = valid_ids(item.get('source_sentence_ids', triple.source_sentence_ids), sentences)
    if not ids:
        ids = infer_ids(triple, sentences, evidence or triple.evidence)
    if not ids and parent is not None:
        ids = valid_ids(parent.source_sentence_ids, sentences)
    triple.source_sentence_ids = ids
    triple.evidence = evidence or triple.evidence or (parent.evidence if parent else '')
    return triple


def group_triples(sentences, triples):
    """Include every sentence, including empty groups; indices stay document-wide."""
    groups = [dict(s, triples=[]) for s in sentences]
    lookup = {g['sentence_id']: g for g in groups}
    unassigned = []
    for index, triple in enumerate(triples):
        record = {"index": index, "head": triple.head, "relation": triple.relation,
                  "tail": triple.tail, "source_sentence_ids": list(triple.source_sentence_ids)}
        ids = valid_ids(triple.source_sentence_ids, sentences)
        if ids:
            for sid in ids:
                lookup[sid]['triples'].append(record)
        else:
            unassigned.append(record)
    if unassigned:
        groups.append({"sentence_id": "UNASSIGNED", "text": "", "triples": unassigned})
    return groups


def grouped_difference_context(diff):
    """Keep sentence identity in both entity and relationship feedback prompts."""
    import json
    diff = diff if isinstance(diff, dict) else {}
    keys = ('unique_to_text_a', 'unique_to_text_b', 'sentence_differences')
    data = {key: diff[key] for key in keys if key in diff}
    return """文本A是源文本，文本B由当前三元组重建。源句指带 sentence_id 的原文句子。
unique_to_text_a 提示可能遗漏的信息，unique_to_text_b 提示可能缺乏源文支持的信息。
sentence_differences 按源句提供重建、差异及相关三元组的全局 index；重建失败、
比较失败或来源未定位均不代表没有问题。UNASSIGNED 表示来源尚未确定的条目。
差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。
<text_difference_json>
""" + json.dumps(data, ensure_ascii=False, indent=2) + "\n</text_difference_json>"
