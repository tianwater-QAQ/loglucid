"""The Logger facade and the get_logger / configure entry points."""
from __future__ import annotations

import sys
from typing import Optional

from .buffer import RingBuffer
from .errors import capture
from .feed import build_feed
from .levels import (CRITICAL, DEBUG, ERROR, INFO, WARNING, parse_level)
from .record import Record
from .sinks import StreamSink

_DEFAULTS = {"level": INFO, "format": None, "capacity": 2000, "stream": None}
_LOGGERS: dict[str, "Logger"] = {}


class Logger:
    def __init__(self, name: str, level: int, sink: StreamSink, buffer: RingBuffer):
        self.name = name
        self.level = level
        self.sink = sink
        self.buffer = buffer

    # -- core ----------------------------------------------------------------
    def _log(self, level: int, msg: str, fields: dict, exc: Optional[BaseException] = None):
        if level < self.level:
            return
        err = capture(exc) if exc is not None else None
        record = Record.now(level, self.name, msg, fields, err)
        self.buffer.append(record)
        self.sink.emit(record)

    # -- level helpers -------------------------------------------------------
    def debug(self, msg: str, **fields): self._log(DEBUG, msg, fields)
    def info(self, msg: str, **fields): self._log(INFO, msg, fields)
    def warning(self, msg: str, **fields): self._log(WARNING, msg, fields)
    warn = warning
    def critical(self, msg: str, **fields): self._log(CRITICAL, msg, fields)

    def error(self, msg: str, exc: Optional[BaseException] = None, **fields):
        self._log(ERROR, msg, fields, exc=exc)

    def exception(self, msg: str, **fields):
        """Log an ERROR with the exception currently being handled."""
        self._log(ERROR, msg, fields, exc=sys.exc_info()[1])

    # -- the killer feature --------------------------------------------------
    def feed_ai(self, last: int = 50, level="INFO", max_tokens: int = 1500,
                prompt: bool = False, redact: bool = True) -> str:
        return build_feed(self.buffer.snapshot(), last=last,
                          min_level=parse_level(level), max_tokens=max_tokens,
                          prompt=prompt, do_redact=redact, app=self.name)


def configure(level=None, format=None, capacity=None, stream=None):
    """Set process-wide defaults and re-apply them to existing loggers."""
    if level is not None:
        _DEFAULTS["level"] = parse_level(level)
    if format is not None:
        _DEFAULTS["format"] = format
    if capacity is not None:
        _DEFAULTS["capacity"] = capacity
    if stream is not None:
        _DEFAULTS["stream"] = stream
    for lg in _LOGGERS.values():
        lg.level = _DEFAULTS["level"]
        lg.sink = StreamSink(_DEFAULTS["stream"] or sys.stderr, _DEFAULTS["format"])


def get_logger(name: str = "app") -> Logger:
    if name not in _LOGGERS:
        _LOGGERS[name] = Logger(
            name=name,
            level=_DEFAULTS["level"],
            sink=StreamSink(_DEFAULTS["stream"] or sys.stderr, _DEFAULTS["format"]),
            buffer=RingBuffer(_DEFAULTS["capacity"]),
        )
    return _LOGGERS[name]
