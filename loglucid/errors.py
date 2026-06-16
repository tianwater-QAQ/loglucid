"""Turn a raised exception into a small, stable, LLM-parseable structure.

We keep `err.type` / `err.msg` and a trimmed traceback (frames in *your* code,
folding noisy library frames) so a model — or a grep — can reliably read what
failed and where.
"""
from __future__ import annotations

import os
import traceback
from dataclasses import dataclass, field


@dataclass
class Frame:
    file: str
    line: int
    func: str


@dataclass
class CapturedError:
    type: str
    msg: str
    frames: list[Frame] = field(default_factory=list)

    def as_fields(self) -> dict:
        return {"err.type": self.type, "err.msg": self.msg}


def _is_library_frame(filename: str) -> bool:
    parts = filename.replace("\\", "/").split("/")
    return any(p in ("site-packages", "dist-packages", "lib") for p in parts)


def capture(exc: BaseException, max_frames: int = 6) -> CapturedError:
    """Capture [exc] as a [CapturedError]. Prefers frames in the user's own code."""
    tb = traceback.extract_tb(exc.__traceback__)
    user = [f for f in tb if not _is_library_frame(f.filename)]
    chosen = (user or tb)[-max_frames:]
    frames = [Frame(file=os.path.relpath(f.filename) if os.path.exists(f.filename) else f.filename,
                    line=f.lineno or 0, func=f.name) for f in chosen]
    return CapturedError(type=type(exc).__name__, msg=str(exc), frames=frames)
