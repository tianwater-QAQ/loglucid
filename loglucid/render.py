"""Pure rendering: a Record -> a human line, a machine line, or a JSON line.

The machine renderer is shared by the machine sink *and* `feed_ai`, so what you
grep, what you ship to a log pipeline, and what you paste into an LLM are the
same compact, stable, ANSI-free format.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from .levels import (CRITICAL, DEBUG, ERROR, INFO, WARNING)
from .record import Record

# ---- ANSI (human mode only) ------------------------------------------------
_RESET = "\033[0m"
_DIM = "\033[2m"
_LEVEL_COLOR = {DEBUG: "\033[90m", INFO: "\033[32m", WARNING: "\033[33m",
                ERROR: "\033[31m", CRITICAL: "\033[1;37;41m"}
_ICON = {DEBUG: "·", INFO: "✓", WARNING: "⚠", ERROR: "✗", CRITICAL: "‼"}


def _needs_quote(s: str) -> bool:
    return s == "" or any(c in s for c in ' \t"=\n')


def kv(key: str, value) -> str:
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    if _needs_quote(s):
        s = '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    return f"{key}={s}"


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fields_str(record: Record) -> str:
    parts = []
    if record.error:
        parts.append(kv("err.type", record.error.type))
        parts.append(kv("err.msg", record.error.msg))
    for k in sorted(record.fields):
        parts.append(kv(k, record.fields[k]))
    return " ".join(parts)


def format_machine(record: Record) -> str:
    """Compact, stable, ANSI-free, greppable, single record (+ error block)."""
    head = f"{_iso(record.ts)} {record.level_name} {record.logger} {kv('msg', record.msg)}"
    fields = _fields_str(record)
    line = head + (" " + fields if fields else "")
    if record.error and record.error.frames:
        for f in record.error.frames:
            line += f"\n  at {f.file}:{f.line} in {f.func}()"
    return line


def format_json(record: Record) -> str:
    obj = {"ts": _iso(record.ts), "level": record.level_name,
           "logger": record.logger, "msg": record.msg, "fields": record.fields}
    if record.error:
        obj["err"] = {"type": record.error.type, "msg": record.error.msg,
                      "frames": [f"{f.file}:{f.line} in {f.func}" for f in record.error.frames]}
    return json.dumps(obj, ensure_ascii=False, default=str)


def format_human(record: Record, color: bool = True) -> str:
    t = datetime.fromtimestamp(record.ts, timezone.utc).strftime("%H:%M:%S")
    icon = _ICON.get(record.level, " ")
    lvl = record.level_name
    fields = _fields_str(record)
    if color:
        c = _LEVEL_COLOR.get(record.level, "")
        lvl_s = f"{c}{lvl:<5}{_RESET}"
        fields_s = f"{_DIM}{fields}{_RESET}" if fields else ""
    else:
        lvl_s = f"{lvl:<5}"
        fields_s = fields
    msg = f"{record.msg:<34}" if fields else record.msg
    line = f"{t} {icon} {lvl_s} {record.logger}  {msg}  {fields_s}".rstrip()
    if record.error and record.error.frames:
        for f in record.error.frames:
            line += f"\n         at {f.file}:{f.line} in {f.func}()"
    return line
