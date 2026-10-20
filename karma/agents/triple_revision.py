"""Shared incremental triple operations; preserves extraction/revision semantics."""

from collections import Counter
from typing import Any, Dict, List, Tuple

from karma.core.data_structures import KnowledgeTriple
from karma.agents.extraction_support import parse_json_container, clean_string, safe_score


class TripleRevisionMixin:
    """Validate, apply and audit incremental operations without model calls."""

    def _parse_revision_response(self, response: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse the JSON object returned by the revision call."""
        data = parse_json_container(response, dict)
        if not all(key in data for key in ("add", "remove", "replace")):
            raise ValueError("revision requires add, remove and replace arrays")

        parsed: Dict[str, List[Dict[str, Any]]] = {}
        for operation in ("add", "remove", "replace"):
            items = data.get(operation, [])
            if not isinstance(items, list):
                raise ValueError(f"revision field '{operation}' must be a list")
            parsed[operation] = items
        return parsed

    def _apply_revision(
        self,
        previous_relationships: List[KnowledgeTriple],
        revision: Dict[str, List[Dict[str, Any]]],
        *,
        split_only: bool = False,
    ) -> Tuple[List[KnowledgeTriple], Dict[str, Any]]:
        """Apply feedback normally, or split with parent indices and inherited scores."""
        replacements: Dict[int, KnowledgeTriple] = {}
        removals = set()
        additions: List[KnowledgeTriple] = []
        accepted: Dict[str, List[Dict[str, Any]]] = {
            "add": [], "remove": [], "replace": []
        }
        rejected: List[Dict[str, Any]] = []

        targets = Counter(
            index
            for op in ("remove", "replace")
            for item in revision[op] if isinstance(item, dict)
            for index in [self._valid_revision_index(item.get("index"), previous_relationships)]
            if index is not None
        )
        for operation in ("replace", "remove", "add"):
            for item in revision[operation]:
                if not isinstance(item, dict):
                    rejected.append({"operation": operation, "reason": "item must be an object", "item": item})
                    continue
                index = None
                error = ""
                if split_only and operation == "remove":
                    error = "remove is not allowed during splitting"
                elif operation != "add" or split_only:
                    index = self._valid_revision_index(item.get("index"), previous_relationships)
                    if index is None:
                        error = "invalid index"
                    elif operation != "add" and targets[index] > 1:
                        error = "conflicting operations; original triple retained"
                if not error and not clean_string(item.get("reason")):
                    error = "missing reason"
                triple = None
                if not error and operation != "remove":
                    triple = self._triple_from_revision_item(item, "relationship_revision")
                    if triple is None:
                        error = "incomplete triple"
                    elif not split_only and not clean_string(item.get("evidence")):
                        error = "missing evidence"
                if error:
                    rejected.append({"operation": operation, "reason": error, "item": item})
                    continue
                # Snapshot the applied SPO values for reading the audit without
                # looking up baseline indices. These describe the accepted
                # operation, before deduplication and downstream filtering.
                before = previous_relationships[index] if operation != "add" and index is not None else None
                audit_item = item
                if split_only:
                    # Split children retain their original parent's scores. Do not
                    # invent quality scores or trust obsolete model score fields.
                    parent = previous_relationships[index]
                    scores = {key: getattr(parent, key) for key in ("confidence", "clarity", "relevance")}
                    for key, value in scores.items():
                        setattr(triple, key, value)
                    audit_item = {
                        **{key: value for key, value in item.items()
                           if key not in ("evidence", "confidence", "clarity", "relevance")},
                        "score_source_index": index,
                        "inherited_scores": scores,
                    }
                accepted[operation].append({
                    **audit_item,
                    "before": {
                        "head": before.head,
                        "relation": before.relation,
                        "tail": before.tail,
                    } if before is not None else None,
                    "after": {
                        "head": triple.head,
                        "relation": triple.relation,
                        "tail": triple.tail,
                    } if triple is not None else None,
                })
                if operation == "replace":
                    replacements[index] = triple
                elif operation == "remove":
                    removals.add(index)
                else:
                    additions.append(triple)

        revised: List[KnowledgeTriple] = []
        for index, triple in enumerate(previous_relationships):
            if index in replacements:
                revised.append(replacements[index])
            elif index not in removals:
                revised.append(triple)
        revised.extend(additions)
        revised = self._deduplicate_relationships(revised)

        audit: Dict[str, Any] = {
            "mode": "incremental_revision",
            "accepted": accepted,
            "rejected": rejected,
            "baseline_count": len(previous_relationships),
            "final_count": len(revised),
        }
        if split_only:
            audit["score_policy"] = "inherit_from_source_triple"
        return revised, audit

    @staticmethod
    def _valid_revision_index(value: Any, triples: List[KnowledgeTriple]):
        """Return a valid integer index, otherwise None."""
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            index = value
        elif isinstance(value, str) and value.strip().isascii() and value.strip().isdigit():
            index = int(value.strip())
        else:
            return None
        return index if 0 <= index < len(triples) else None

    @staticmethod
    def _safe_score(value: Any, default: float) -> float:
        return safe_score(value, default)

    def _triple_from_revision_item(
        self, item: Dict[str, Any], source: str
    ):
        head = clean_string(item.get("head"))
        relation = clean_string(item.get("relation"))
        tail = clean_string(item.get("tail"))
        if not head or not relation or not tail:
            return None
        return KnowledgeTriple(
            head=head,
            relation=relation,
            tail=tail,
            confidence=self._safe_score(item.get("confidence"), 0.5),
            clarity=self._safe_score(item.get("clarity"), 0.5),
            relevance=self._safe_score(item.get("relevance"), 0.5),
            source=source,
        )

    def _deduplicate_relationships(self, relationships: List[KnowledgeTriple]) -> List[KnowledgeTriple]:
        """
        Remove duplicate relationships.

        Args:
            relationships: List of relationships to deduplicate

        Returns:
            List of unique relationships
        """
        if not relationships:
            return []

        unique_rels = {}

        for rel in relationships:
            # Create key for deduplication
            key = f"{rel.head.lower()}__{rel.relation.lower()}__{rel.tail.lower()}"

            # Keep the one with higher confidence if duplicates exist
            if key not in unique_rels or rel.confidence > unique_rels[key].confidence:
                unique_rels[key] = rel

        return list(unique_rels.values())
