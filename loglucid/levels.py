"""Log levels — kept compatible (same numeric values) with the stdlib `logging`."""
from __future__ import annotations

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

NAME_TO_LEVEL = {
    "DEBUG": DEBUG, "INFO": INFO, "WARNING": WARNING, "WARN": WARNING,
    "ERROR": ERROR, "CRITICAL": CRITICAL,
}
LEVEL_TO_NAME = {DEBUG: "DEBUG", INFO: "INFO", WARNING: "WARNING",
                 ERROR: "ERROR", CRITICAL: "CRITICAL"}


def parse_level(value) -> int:
    """Accept an int or a name ('INFO', 'WARN', '>=WARNING' handled by caller)."""
    if isinstance(value, int):
        return value
    name = str(value).strip().upper()
    if name not in NAME_TO_LEVEL:
        raise ValueError(f"unknown level: {value!r}")
    return NAME_TO_LEVEL[name]


def level_name(level: int) -> str:
    return LEVEL_TO_NAME.get(level, str(level))
