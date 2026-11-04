"""Compatibility scores assigned by code, not assessed by the language model."""
import copy

FIXED_TRIPLE_SCORE = 0.8
SCORE_FIELDS = ('confidence', 'clarity', 'relevance')


def fixed_score_copy(triples):
    result = copy.deepcopy(triples)
    for triple in result:
        for name in SCORE_FIELDS:
            setattr(triple, name, FIXED_TRIPLE_SCORE)
    return result


def prompt_triple(triple):
    """Only facts and their source evidence belong in a model's input."""
    return {key: value for key, value in triple.to_dict().items()
            if key in ('head', 'relation', 'tail', 'source_sentence_ids', 'evidence')}
