"""Output sinks and format selection (human / machine / json), with TTY auto-switch."""
from __future__ import annotations

import os
import sys
from typing import Optional

from .record import Record
from .render import format_human, format_json, format_machine

VALID_FORMATS = ("human", "machine", "json")


def resolve_format(explicit: Optional[str], stream) -> str:
    """Pick a format: explicit arg > env (LOGLUCID_FORMAT / LOGLM_FORMAT) > TTY auto."""
    fmt = explicit or os.environ.get("LOGLUCID_FORMAT") or os.environ.get("LOGLM_FORMAT")
    if fmt:
        fmt = fmt.strip().lower()
        if fmt not in VALID_FORMATS:
            fmt = None
    if not fmt:
        is_tty = bool(getattr(stream, "isatty", lambda: False)())
        fmt = "human" if is_tty else "machine"
    return fmt


class StreamSink:
    """Writes each record to a stream using the chosen format."""

    def __init__(self, stream=None, fmt: Optional[str] = None):
        self.stream = stream or sys.stderr
        self.format = resolve_format(fmt, self.stream)
        self._color = self.format == "human" and bool(
            getattr(self.stream, "isatty", lambda: False)())

    def render(self, record: Record) -> str:
        if self.format == "json":
            return format_json(record)
        if self.format == "human":
            return format_human(record, color=self._color)
        return format_machine(record)

    def emit(self, record: Record) -> None:
        try:
            self.stream.write(self.render(record) + "\n")
            self.stream.flush()
        except Exception:
            pass  # logging must never crash the app
