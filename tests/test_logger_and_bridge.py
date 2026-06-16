import io
import logging

import loglucid
from loglucid.errors import capture
from loglucid.levels import ERROR, INFO
from loglucid.sinks import resolve_format


def test_resolve_format_env_and_tty(monkeypatch):
    class TTY(io.StringIO):
        def isatty(self): return True

    class NotTTY(io.StringIO):
        def isatty(self): return False

    monkeypatch.delenv("LOGLUCID_FORMAT", raising=False)
    monkeypatch.delenv("LOGLM_FORMAT", raising=False)
    assert resolve_format(None, TTY()) == "human"
    assert resolve_format(None, NotTTY()) == "machine"
    assert resolve_format("json", TTY()) == "json"
    monkeypatch.setenv("LOGLUCID_FORMAT", "machine")
    assert resolve_format(None, TTY()) == "machine"   # env overrides TTY


def test_logger_emits_and_buffers():
    buf = io.StringIO()
    loglucid.configure(format="machine", stream=buf, level="DEBUG")
    log = loglucid.get_logger("svc-test")
    log.info("hello", x=1)
    assert "msg=hello" in buf.getvalue()
    assert len(log.buffer) >= 1


def test_error_with_exc_captures_structure():
    log = loglucid.get_logger("svc-err")
    log.buffer._dq.clear()
    try:
        raise KeyError("missing")
    except KeyError as e:
        log.error("lookup failed", exc=e)
    rec = log.buffer.snapshot()[-1]
    assert rec.level == ERROR and rec.error is not None
    assert rec.error.type == "KeyError"


def test_stdlib_bridge_routes_into_loglucid():
    buf = io.StringIO()
    loglucid.configure(format="machine", stream=buf)
    loglucid.install_stdlib_bridge(level=logging.INFO)
    logging.getLogger("legacy.module").warning("from stdlib %s", "logging")
    out = buf.getvalue()
    assert "from stdlib logging" in out
    assert "WARNING" in out


def test_capture_folds_library_frames():
    try:
        raise ValueError("x")
    except ValueError as e:
        err = capture(e)
    assert err.type == "ValueError"
    assert all(":" not in f.file or "site-packages" not in f.file for f in err.frames)
