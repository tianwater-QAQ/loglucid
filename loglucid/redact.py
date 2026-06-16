"""Redact secrets/PII from text before it leaves the process (e.g. into an LLM).

Prefers our own `logscrub` library if it's installed (fuller detector set);
otherwise falls back to a small built-in scrubber so loglucid works standalone.
"""
from __future__ import annotations

import re

_FALLBACK = [
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[posru]_[A-Za-z0-9]{36,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{16,}=*"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
]


def _builtin(text: str) -> str:
    for rx in _FALLBACK:
        text = rx.sub("[REDACTED]", text)
    return text


def redact(text: str) -> str:
    try:
        from logscrub import scrub  # our own library, if installed
        return scrub(text).text
    except Exception:
        return _builtin(text)
