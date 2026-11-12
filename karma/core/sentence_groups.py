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


def infer_ids(triple, sentences):
    """Recover a unique exact SPO match in legacy records, never guess a source."""
    norm = lambda s: " ".join(s.split())
    values = [norm(getattr(triple, key)) for key in ('head', 'relation', 'tail')]
    matches = [s['sentence_id'] for s in sentences
               if all(value and value in norm(s['text']) for value in values)]
    return matches if len(matches) == 1 else []


def attach_sources(triple, sentences, item=None, parent=None):
    """Use declared sentence IDs, inherit a parent's source, or recover an exact match."""
    item = item or {}
    ids = valid_ids(item.get('source_sentence_ids', triple.source_sentence_ids), sentences)
    if not ids and parent is not None:
        ids = valid_ids(parent.source_sentence_ids, sentences)
    if not ids:
        ids = infer_ids(triple, sentences)
    triple.source_sentence_ids = ids
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


def unassigned_group_note(groups):
    """Explain the fallback label only when it occurs in this prompt's input."""
    if any(isinstance(g, dict) and g.get('sentence_id') == 'UNASSIGNED'
           for g in (groups or [])):
        return "UNASSIGNED 是来源句尚未确定的条目分组；按输入编号处理该组。\n"
    return ""


def grouped_difference_context(diff):
    """Keep sentence identity in both entity and relationship feedback prompts."""
    import json
    diff = diff if isinstance(diff, dict) else {}
    keys = ('unique_to_text_a', 'unique_to_text_b', 'sentence_differences')
    data = {key: diff[key] for key in keys if key in diff}
    source_group_note = unassigned_group_note(data.get('sentence_differences', []))
    return """文本A是源文本，文本B是由当前三元组生成的重建文本。源句指带 sentence_id 的原文句子。
unique_to_text_a 提示可能遗漏的信息，unique_to_text_b 提示可能缺乏源文支持的信息。
sentence_differences 按源句提供重建文本、差异及相关三元组的全局 index；重建文本生成失败、
比较失败或来源未定位均不代表没有问题。
差异只帮助定位，须结合全文核实；空差异仍需检查事实覆盖，不能仅凭差异增删。
""" + source_group_note + "<text_difference_json>\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n</text_difference_json>"
