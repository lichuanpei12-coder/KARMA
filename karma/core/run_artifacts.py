"""Versioned, source-preserving handoff between baseline and revision runs."""

import hashlib
import json
import math
from pathlib import Path

from .data_structures import KGEntity, KnowledgeTriple


def fingerprint(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_json(path, value):
    """Replace a completed JSON file atomically; never expose half a document."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def save_baseline(path, config, documents):
    payload = {"format": "karma_baseline", "version": 1,
               "config": config, "documents": documents}
    payload["sha256"] = fingerprint(payload)
    # A baseline is immutable. Choose a new path for a new baseline version.
    if Path(path).exists():
        raise FileExistsError(f"Baseline already exists: {path}")
    write_json(path, payload)
    return payload


def load_baseline(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != "karma_baseline" or data.get("version") != 1:
        raise ValueError("Unsupported baseline package; generate it with --stage baseline")
    payload = {key: value for key, value in data.items() if key != "sha256"}
    if data.get("sha256") != fingerprint(payload):
        raise ValueError("Baseline checksum mismatch; the baseline was changed or damaged")
    config = data.get("config", {})
    threshold = config.get("integration_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold):
        raise ValueError("Baseline integration threshold is missing or invalid")
    documents = data.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("Baseline contains no documents")
    ids, indices = set(), set()
    for doc in documents:
        if not isinstance(doc, dict):
            raise ValueError('Baseline document must be an object')
        doc_id, index = doc.get("doc_id"), doc.get("source_index")
        if not isinstance(doc_id, str) or not doc_id or doc_id in ids:
            raise ValueError("Baseline document IDs must be nonempty and unique")
        if type(index) is not int or index < 0 or index in indices:
            raise ValueError("Baseline source indices must be nonnegative and unique")
        ids.add(doc_id)
        indices.add(index)
        if not isinstance(doc.get("raw_text"), str) or not isinstance(doc.get("extraction_text"), str):
            raise ValueError(f"Missing source text for document {doc_id}")
        for key, constructor in (("initial_entities", KGEntity.from_dict),
                                 ("baseline_triples", KnowledgeTriple.from_dict),
                                 ("initial_relationships", KnowledgeTriple.from_dict),
                                 ("conflict_context", KnowledgeTriple.from_dict)):
            if not isinstance(doc.get(key), list):
                raise ValueError(f"Missing {key} for document {doc_id}")
            for item in doc[key]:
                constructor(item)
        preparation = doc.get("preparation", {})
        if not isinstance(preparation, dict) or not all(k in preparation for k in
                ('metadata', 'segments', 'relevant_segments', 'summaries')):
            raise ValueError(f"Missing preprocessing state for document {doc_id}")
        if (not isinstance(preparation['summaries'], list)
                or not all(isinstance(x, str) for x in preparation['summaries'])
                or "\n".join(preparation["summaries"]) != doc["extraction_text"]):
            raise ValueError(f"Extraction text does not match summaries for document {doc_id}")
    return data


def select_documents(documents, doc_ids=None, limit=None):
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError("--limit must be a positive integer")
    selected = documents
    if doc_ids is not None:
        wanted = set(doc_ids)
        missing = wanted - {d["doc_id"] for d in documents}
        if missing:
            raise ValueError(f"Unknown document IDs: {sorted(missing)}")
        selected = [d for d in documents if d["doc_id"] in wanted]
    if limit is not None:
        selected = selected[:limit]
    if not selected:
        raise ValueError("No documents selected")
    return selected
