"""Shared token boundaries for offline evaluation and feedback ranking."""

import re


# CJK Unified Ideographs, their extensions and compatibility ideographs.
_HAN = (
    r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
    r"\U00020000-\U0002ee5f\U0002f800-\U0002fa1f\U00030000-\U0003347f"
)
HAN_RE = re.compile(f"[{_HAN}]")
TOKEN_RE = re.compile(rf"[{_HAN}]|[^\s{_HAN}]+")
HAN_WHITESPACE_RE = re.compile(rf"(?<=[{_HAN}])\s+|\s+(?=[{_HAN}])")


def overlap_tokens(text):
    """Count individual Han characters and retain other whitespace-delimited text."""
    return TOKEN_RE.findall(text.lower())


def normalize_chinese_spacing(text):
    """Ignore spacing around Han characters while preserving other word boundaries."""
    return HAN_WHITESPACE_RE.sub("", " ".join(text.split()))
