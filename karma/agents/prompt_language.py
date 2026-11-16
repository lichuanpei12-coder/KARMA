"""Choose the language of prompt examples from the source being processed."""

import re

from lexical_tokens import HAN_RE


def uses_chinese_prompt(text):
    """Prefer Chinese when Han characters outnumber non-Han letter groups."""
    han_characters = HAN_RE.findall(text)
    other_words = re.findall(r"[^\W\d_]+", HAN_RE.sub(" ", text))
    return len(han_characters) > len(other_words)
