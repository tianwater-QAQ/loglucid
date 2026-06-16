"""Drop loglucid into an app that already uses the standard `logging` module —
no changes to the existing log statements.

    PYTHONPATH=. python examples/stdlib_app.py
"""
import logging

import loglucid

loglucid.install_stdlib_bridge(level=logging.DEBUG)   # one line

log = logging.getLogger("legacy.service")             # existing code, unchanged
log.info("started", extra={})
log.warning("disk almost full")
try:
    1 / 0
except ZeroDivisionError:
    log.exception("task crashed")

# and you still get feed_ai on the underlying loglucid logger:
print("\n--- feed_ai ---")
print(loglucid.get_logger("legacy.service").feed_ai(last=20, prompt=True))
