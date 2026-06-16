"""The immutable structured log record that flows through sinks and the buffer."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .errors import CapturedError
from .levels import level_name


@dataclass(frozen=True)
class Record:
    ts: float                       # epoch seconds
    level: int
    logger: str
    msg: str
    fields: dict = field(default_factory=dict)
    error: Optional[CapturedError] = None

    @property
    def level_name(self) -> str:
        return level_name(self.level)

    @staticmethod
    def now(level: int, logger: str, msg: str, fields: dict,
            error: Optional[CapturedError] = None) -> "Record":
        return Record(ts=time.time(), level=level, logger=logger, msg=msg,
                      fields=dict(fields), error=error)
