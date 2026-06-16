from loglucid.record import Record
from loglucid.errors import capture
from loglucid.levels import ERROR, INFO, WARNING
from loglucid.render import format_human, format_json, format_machine, kv
import json


def rec(level=INFO, msg="hello", **fields):
    return Record(ts=1_780_000_000.0, level=level, logger="t", msg=msg, fields=fields)


def test_kv_quotes_only_when_needed():
    assert kv("a", "b") == "a=b"
    assert kv("a", "b c") == 'a="b c"'
    assert kv("n", 5) == "n=5"


def test_machine_format_is_compact_and_sorted():
    line = format_machine(rec(user_id=42, ip="1.2.3.4"))
    assert "\033" not in line  # no ANSI
    assert line.split(" ", 1)[0].endswith("Z")               # ISO-8601 UTC stamp
    assert line.endswith("INFO t msg=hello ip=1.2.3.4 user_id=42")  # fields sorted


def test_machine_format_includes_error_block():
    try:
        raise ValueError("bad amount")
    except ValueError as e:
        err = capture(e)
    line = format_machine(Record(ts=1_780_000_000.0, level=ERROR, logger="t",
                                 msg="boom", fields={}, error=err))
    assert 'err.type=ValueError' in line
    assert 'err.msg="bad amount"' in line
    assert "\n  at " in line


def test_json_format_roundtrips():
    obj = json.loads(format_json(rec(WARNING, "warn", k="v")))
    assert obj["level"] == "WARNING" and obj["fields"] == {"k": "v"}


def test_human_format_has_icon_no_color_when_disabled():
    line = format_human(rec(ERROR, "oops"), color=False)
    assert "\033" not in line
    assert "✗" in line and "ERROR" in line
