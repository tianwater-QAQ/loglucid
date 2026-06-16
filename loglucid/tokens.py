"""Token estimation for the feed budget.

Uses ``tiktoken`` if it happens to be installed (accurate), otherwise a
characters/4 heuristic — good enough to keep a paste under a model's limit.
"""
from __future__ import annotations


def estimate(text: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return max(1, (len(text) + 3) // 4)
