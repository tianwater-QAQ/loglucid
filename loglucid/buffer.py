"""A bounded in-memory ring buffer of recent records, for feed_ai()."""
from __future__ import annotations

from collections import deque
from typing import Optional

from .record import Record


class RingBuffer:
    def __init__(self, capacity: int = 2000):
        self._dq: deque[Record] = deque(maxlen=capacity)

    def append(self, record: Record) -> None:
        self._dq.append(record)

    def snapshot(self, last: Optional[int] = None) -> list[Record]:
        items = list(self._dq)
        return items[-last:] if last else items

    def __len__(self) -> int:
        return len(self._dq)
