"""loglucid — a logging library that's pretty for humans and friendly for LLMs.

    from loglucid import get_logger
    log = get_logger("myapp")
    log.info("user signed in", user_id=42)
    print(log.feed_ai(last=50))   # compact, redacted, paste-into-an-LLM block

Brand: Lucid.
"""
from __future__ import annotations

from .levels import CRITICAL, DEBUG, ERROR, INFO, WARNING
from .logger import Logger, configure, get_logger
from .stdlib_bridge import install as install_stdlib_bridge

__version__ = "0.2.0"
__all__ = [
    "get_logger", "configure", "Logger", "install_stdlib_bridge",
    "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "__version__",
]
