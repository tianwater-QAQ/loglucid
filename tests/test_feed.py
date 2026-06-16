from loglucid.feed import build_feed
from loglucid.levels import DEBUG, ERROR, INFO
from loglucid.record import Record
from loglucid.errors import capture


def mk(level, msg, ts, **f):
    return Record(ts=ts, level=level, logger="app", msg=msg, fields=f)


def test_denoise_collapses_repeats():
    recs = [mk(INFO, "tick", 1000.0 + i) for i in range(5)]
    out = build_feed(recs, min_level=DEBUG, max_tokens=9999)
    assert "(×5)" in out          # 5 identical lines collapsed into one
    assert out.count("msg=tick") == 1


def test_redaction_runs_by_default():
    recs = [mk(INFO, "auth", 1000.0, token="sk-proj-" + "A" * 40)]
    out = build_feed(recs, max_tokens=9999)
    assert "[REDACTED]" in out and "sk-proj-AAAA" not in out


def test_error_kept_and_middle_elided_under_tiny_budget():
    recs = [mk(INFO, f"step {i}", 1000.0 + i, i=i) for i in range(40)]
    try:
        raise RuntimeError("kaboom")
    except RuntimeError as e:
        recs.append(Record(ts=1100.0, level=ERROR, logger="app",
                           msg="failed", fields={}, error=capture(e)))
    out = build_feed(recs, last=41, max_tokens=120)
    assert 'msg=failed' in out         # the error is never dropped
    assert "elided" in out             # the noisy middle is summarized


def test_header_counts_and_prompt():
    recs = [mk(INFO, "a", 1000.0), mk(ERROR, "b", 1001.0)]
    out = build_feed(recs, prompt=True)
    assert out.startswith("Here are my app's recent logs")
    assert "1 INFO" in out and "1 ERROR" in out


def test_empty_is_handled():
    assert "no log records" in build_feed([], max_tokens=100)


def test_error_grouping_story_line():
    recs = []
    for i in range(2):
        try:
            raise ValueError("bad")
        except ValueError as e:
            recs.append(Record(ts=1000.0 + i, level=ERROR, logger="app",
                               msg="boom", fields={}, error=capture(e)))
    out = build_feed(recs, max_tokens=9999)
    assert "# errors: ValueError ×2" in out
