"""Rank every current triple pair by lexical overlap and directional containment."""
from collections import Counter
from fractions import Fraction


def rank_triple_overlap(triples, version):
    """Use evaluation's lower().split() and multiset counting over combined SPO.

    All n*(n-1)/2 pairs are returned once, in index order. Independent competition
    ranks share a rank for ties (1, 1, 3); neither scores nor ranks filter pairs.
    """
    words = [Counter(word for field in ('head', 'relation', 'tail')
                     for word in getattr(t, field).lower().split()) for t in triples]
    rows, overall_scores, containment_scores = [], [], []
    for left, a in enumerate(words):
        for right in range(left + 1, len(words)):
            b = words[right]
            size_a, size_b = sum(a.values()), sum(b.values())
            common = sum((a & b).values())
            overall = Fraction(2 * common, size_a + size_b) if size_a + size_b else Fraction(0)
            ca = Fraction(common, size_a) if size_a else Fraction(0)
            cb = Fraction(common, size_b) if size_b else Fraction(0)
            overall_scores.append(overall)
            containment_scores.append(max(ca, cb))
            rows.append({'indices': [left, right], 'overlap_f1': float(overall),
                         'left_containment': float(ca), 'right_containment': float(cb),
                         'left_only_words': dict(sorted((a - b).items())),
                         'right_only_words': dict(sorted((b - a).items()))})
    for key, scores in (('overall_rank', overall_scores), ('containment_rank', containment_scores)):
        ranks = {}
        for position, score in enumerate(sorted(scores, reverse=True), 1):
            ranks.setdefault(score, position)
        for row, score in zip(rows, scores):
            row[key] = ranks[score]
    return {'basis_version': version, 'pairs': rows}
