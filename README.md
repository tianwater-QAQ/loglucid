# loglucid

A logging library that's **pretty for humans and friendly for LLMs**. Same logs,
two faces: colorful and aligned in your terminal, compact and structured for
machines — and one call, `feed_ai()`, packs your recent logs into a clean block
you can paste straight into ChatGPT/Claude to debug.

> Built by an AI that reads logs all day.

## The problem it solves

You hit a bug, so you copy your terminal logs into an LLM and ask "what's wrong?"
But that paste is full of ANSI color codes, 40 lines of debug noise, and — oops —
an API key. `loglucid` makes that one clean, **redacted**, token-budgeted call.

### Before → after

What you'd paste today (colored terminal output, secrets and all) vs.
`log.feed_ai()` — measured by [`examples/demo.py`](examples/demo.py) on the same run:

```
raw terminal logs : 4660 chars  ~1165 tokens
feed_ai() block   :  593 chars  ~149 tokens
                    → ~87% smaller (debug noise dropped, ANSI stripped, compact format)
```

The `feed_ai()` output:

```
# checkout — last 5 log lines (03:37:53Z–03:37:53Z) · 2 INFO 2 WARNING 1 ERROR
2026-06-16T03:37:53Z INFO checkout msg="server started" port=8080 workers=4
2026-06-16T03:37:53Z INFO checkout msg="request received" method=POST path=/orders req_id=r-1001
2026-06-16T03:37:53Z WARNING checkout msg="upstream slow" ms=812 url=https://pay.internal/charge
2026-06-16T03:37:53Z WARNING checkout msg="retrying upstream" attempt=2
2026-06-16T03:37:53Z ERROR checkout msg="payment failed" err.type=ValueError err.msg="amount must be positive" order_id=99 req_id=r-1001
  at services/pay.py:88 in charge()
```

(Numbers are from one demo run — reproduce them yourself with `examples/demo.py`;
your reduction depends on how noisy your logs are.)

## Quick start

```python
from loglucid import get_logger

log = get_logger("checkout")              # human in a TTY, compact otherwise
log.info("user signed in", user_id=42, ip="10.0.0.5")
log.warn("retrying upstream", attempt=2)

try:
    charge(order)
except Exception as e:
    log.error("payment failed", exc=e, order_id=99)   # structured exception capture

print(log.feed_ai(last=50, prompt=True))  # paste this into your favourite LLM
```

## Dual output, auto-switching

- **Human (a TTY):** colored levels, aligned columns, `✓ ⚠ ✗` icons, dimmed `key=value`.
- **Machine / LLM (not a TTY):** one compact, ANSI-free, **stable & greppable** line
  per record (sorted fields, self-describing) — token-lean by design.
- **`json`:** NDJSON for log pipelines.

It auto-detects (`stderr.isatty()`), and you can force it with
`LOGLUCID_FORMAT=human|machine|json` (or `configure(format=...)`). In CI, Docker and
pipes you automatically get the compact format — which is exactly what an LLM wants.

## `feed_ai()` — the one-call AI handoff

`log.feed_ai(last=50, level="INFO", max_tokens=1500, prompt=False, redact=True)`:

- pulls the last N records from an in-memory ring buffer,
- **collapses repeated lines** (`… (×37)`),
- **keeps every ERROR/CRITICAL** (with a little preceding context) and WARNING, fills
  the rest of the **token budget** with the most recent lines, and **elides the gaps**
  with a counted summary — the triggering error is never dropped,
- **redacts secrets/PII** (uses our [`logscrub`](https://github.com/tianwater-QAQ/logscrub)
  if installed, a built-in fallback otherwise),
- optionally prepends a question prompt.

## Structured errors

`log.error("...", exc=e)` (or `log.exception("...")`) captures `err.type`, `err.msg`
and a trimmed traceback (your frames, library frames folded) — rendered as a stable,
parseable block so a model can pinpoint the failure and suggest a fix.

## Drop into an existing app (zero changes)

```python
import logging, loglucid
loglucid.install_stdlib_bridge()          # route stdlib logging through loglucid
logging.getLogger("anything").info("works")   # now pretty + buffered for feed_ai()
```

## CLI — works on any log file

```bash
loglucid feed app.log --last 80 --max-tokens 2000 | pbcopy
cat app.log | loglucid feed -            # even logs not produced by loglucid
```

## Install

```bash
pip install loglucid
# optional extras:
pip install "loglucid[redact]"   # fuller redaction via logscrub
pip install "loglucid[tokens]"   # accurate token counts via tiktoken
```

Zero required dependencies; the extras are graceful fallbacks if absent.

## Scope (v0.1) & roadmap

**In v0.1:** dual sinks + auto-switch + NDJSON · `feed_ai()` (ring buffer, denoise,
redact, token budget, elision) · structured exception capture · stdlib `logging`
bridge · `loglucid feed` CLI · tests.

**Later:** accurate token counting by default, file/HTTP/async sinks, trace-id
correlation, `loglucid watch` (tail + auto-feed), Rust/Go ports, an editor
"ask AI about this log" action.

## License

[Apache 2.0](LICENSE) © Tianwater
