"""`loglucid feed <file>` — pack an existing log file into an AI-ready block.

Works on *any* text log, not just loglucid's: each line becomes a record (its
level guessed from a level word if present), then the same denoise + redact +
token-budget pipeline as `feed_ai()` runs over it.
"""
from __future__ import annotations

import argparse
import re
import sys
import time

from .feed import build_feed
from .levels import INFO, NAME_TO_LEVEL
from .record import Record

_LEVEL_RE = re.compile(r"\b(CRITICAL|ERROR|WARNING|WARN|DEBUG|INFO)\b")


def _guess_level(line: str) -> int:
    m = _LEVEL_RE.search(line)
    return NAME_TO_LEVEL[m.group(1)] if m else INFO


def _records_from_lines(lines, logger_name: str) -> list[Record]:
    now = time.time()
    out = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        out.append(Record(ts=now + i * 1e-3, level=_guess_level(line),
                           logger=logger_name, msg=line, fields={}, error=None))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="loglucid")
    sub = ap.add_subparsers(dest="cmd", required=True)
    fp = sub.add_parser("feed", help="Pack a log file into an AI-ready context block.")
    fp.add_argument("file", help="Log file ('-' for stdin).")
    fp.add_argument("--last", type=int, default=80)
    fp.add_argument("--max-tokens", type=int, default=2000)
    fp.add_argument("--level", default="INFO")
    fp.add_argument("--no-redact", action="store_true")
    fp.add_argument("--prompt", action="store_true", help="Prepend a question for the LLM.")
    a = ap.parse_args(argv)

    if a.cmd == "feed":
        text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8", errors="replace").read()
        name = "stdin" if a.file == "-" else a.file.rsplit("/", 1)[-1]
        records = _records_from_lines(text.splitlines(), name)
        from .levels import parse_level
        out = build_feed(records, last=a.last, min_level=parse_level(a.level),
                         max_tokens=a.max_tokens, prompt=a.prompt,
                         do_redact=not a.no_redact, app=name)
        sys.stdout.write(out)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
