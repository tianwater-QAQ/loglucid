"""Bridge the standard library `logging` into loglucid.

Call `install()` once and every existing `logging.getLogger(...).info(...)` in
your app (and its dependencies) flows through loglucid's sinks and buffer — so
you get the pretty/compact output and `feed_ai()` with **zero changes** to your
existing log statements.
"""
from __future__ import annotations

import logging

from .logger import get_logger


class LucidHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            lg = get_logger(record.name or "app")
            exc = record.exc_info[1] if record.exc_info else None
            # logging levels share numeric values with loglucid's.
            lg._log(record.levelno, record.getMessage(), {}, exc=exc)
        except Exception:
            self.handleError(record)


def install(level: int = logging.INFO, replace: bool = True) -> LucidHandler:
    """Route the root stdlib logger through loglucid. Returns the handler."""
    handler = LucidHandler()
    root = logging.getLogger()
    if replace:
        root.handlers = [handler]
    else:
        root.addHandler(handler)
    root.setLevel(level)
    return handler
