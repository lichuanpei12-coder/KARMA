"""Shared JSON parsing and value validation; prompts live in the agent modules."""

import json
import math
import re


def parse_json_container(response, expected_type):
    """Accept JSON, fenced JSON or a prose wrapper, but never a nested wrong-root value."""
    if not isinstance(response, str):
        raise ValueError('model response must be text')
    value = response.strip()
    fence = re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```', value, re.IGNORECASE)
    if fence:
        value = fence.group(1).strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        positions = [p for p in (value.find('['), value.find('{')) if p >= 0]
        if not positions:
            raise ValueError('model response contains no JSON container')
        # Decode the first container, not an inner array of a wrong-root object.
        start = min(positions)
        parsed, end = json.JSONDecoder().raw_decode(value, start)
        if '[' in value[end:] or '{' in value[end:]:
            raise ValueError('model response contains multiple JSON containers')
    if not isinstance(parsed, expected_type):
        raise ValueError('unexpected JSON root type')
    return parsed


def clean_string(value):
    return value.strip() if isinstance(value, str) else ''


def safe_score(value, default=0.5):
    if isinstance(value, bool):
        return default
    try:
        score = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return min(1.0, max(0.0, score)) if math.isfinite(score) else default
