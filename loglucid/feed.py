"""feed_ai(): pack recent records into a compact block ready to paste into an LLM.

Pipeline: filter by level -> take last N -> render to the machine format ->
collapse repeated lines -> keep all ERROR/CRITICAL (plus a little preceding
context) and WARNING, fill the rest of the token budget with the most recent
lines, elide the gaps with a counted summary -> redact secrets -> optional prompt.
The triggering error is never dropped.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from . import redact as _redact
from . import tokens
from .levels import ERROR, INFO, WARNING
from .record import Record
from .render import format_machine

_CONTEXT = 3  # records of context kept before each error


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%H:%M:%SZ")


def _denoise(records: list[Record]) -> list[dict]:
    """Collapse consecutive records that are identical apart from their timestamp
    (the usual shape of log spam)."""
    items: list[dict] = []
    for r in records:
        text = format_machine(r)
        sig = text.split(" ", 1)[1] if " " in text else text  # drop the timestamp
        if items and items[-1]["sig"] == sig:
            items[-1]["count"] += 1
        else:
            items.append({"text": text, "sig": sig, "level": r.level,
                          "level_name": r.level_name, "count": 1})
    return items


def build_feed(records: list[Record], *, last: int = 50, min_level: int = INFO,
               max_tokens: int = 1500, prompt: bool = False,
               do_redact: bool = True, app: str = "") -> str:
    recs = [r for r in records if r.level >= min_level][-last:]
    if not recs:
        return "(no log records)\n"

    counts = Counter(r.level_name for r in recs)
    app = app or recs[-1].logger
    rng = f"{_iso(recs[0].ts)}–{_iso(recs[-1].ts)}"
    items = _denoise(recs)
    n = len(items)

    # must-keep: errors (+ preceding context) and warnings
    must = [False] * n
    for i, it in enumerate(items):
        if it["level"] >= ERROR:
            must[i] = True
            for j in range(max(0, i - _CONTEXT), i):
                must[j] = True
        elif it["level"] >= WARNING:
            must[i] = True

    def line_text(it: dict) -> str:
        return it["text"] + (f"  (×{it['count']})" if it["count"] > 1 else "")

    tok = [tokens.estimate(line_text(it)) for it in items]
    keep = {i for i in range(n) if must[i]}
    used = sum(tok[i] for i in keep)
    # fill remaining budget with the most recent non-must lines
    for i in range(n - 1, -1, -1):
        if i in keep:
            continue
        if used + tok[i] <= max_tokens:
            keep.add(i)
            used += tok[i]

    # assemble in order, eliding the gaps
    out: list[str] = []
    i = 0
    while i < n:
        if i in keep:
            out.append(line_text(items[i]))
            i += 1
        else:
            j = i
            gap = Counter()
            while j < n and j not in keep:
                gap[items[j]["level_name"]] += items[j]["count"]
                j += 1
            total = sum(gap.values())
            dom = gap.most_common(1)[0][0]
            plural = "s" if total > 1 else ""
            out.append(f"… ({total} earlier {dom} line{plural} elided) …")
            i = j

    body = "\n".join(out)
    if do_redact:
        body = _redact.redact(body)

    summary = " ".join(f"{v} {k}" for k, v in counts.most_common())
    header = f"# {app} — last {len(recs)} log lines ({rng}) · {summary}"
    blocks = [header, body]
    if prompt:
        blocks.insert(0, "Here are my app's recent logs. What went wrong and how do I fix it?\n")
    return "\n".join(blocks) + "\n"
