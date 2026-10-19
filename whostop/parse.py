"""Strict leading-word parser for a driving decision.

The scored token is the first word, after optional non-word characters and
markdown asterisks. ``STOP``, ``CAUTION``, and ``PROCEED`` are the only
actions. ``GO`` is read as ``PROCEED`` and ``PROCEED WITH CAUTION`` as
``CAUTION``, matching ``phase2/analysis/analyze_p2.py``. Anything else,
including a decision that is not the leading word, is ``UNPARSED``.

``strip_echo`` is copied from jaideep-aher/horn-ok-please (MIT),
``src/hornok/parse.py``. That repository was not modified.

Copyright (c) 2026 Jaideep Aher. MIT License. See NOTICE.
"""

from __future__ import annotations

import re

ACTIONS = ("STOP", "CAUTION", "PROCEED")

# Longer phrase first so "PROCEED WITH CAUTION" is not read as PROCEED.
_LEADING = re.compile(
    r"\W*(STOP|PROCEED WITH CAUTION|PROCEED|CAUTION|GO)\b",
    re.IGNORECASE,
)

_MAP = {
    "STOP": "STOP",
    "CAUTION": "CAUTION",
    "PROCEED": "PROCEED",
    "GO": "PROCEED",
    "PROCEED WITH CAUTION": "CAUTION",
}


def parse_action(text: str) -> str:
    """Return STOP, CAUTION, PROCEED, or UNPARSED."""
    raw = (text or "").replace("*", "").strip()
    if not raw:
        return "UNPARSED"
    match = _LEADING.match(raw)
    if not match:
        return "UNPARSED"
    return _MAP[match.group(1).upper()]


def strip_echo(raw: str, prompt: str) -> str:
    """Drop a echoed prompt so the parser sees only the completion."""
    text = raw or ""
    if prompt and prompt in text:
        text = text.split(prompt)[-1]
    text = re.sub(r"^\s*(assistant|response)\s*:\s*", "", text, flags=re.I)
    return text.strip()


def parse_completion(text: str, prompt: str = "") -> str:
    """Strip an echoed prompt, then parse the leading action word."""
    return parse_action(strip_echo(text, prompt))
