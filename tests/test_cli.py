import io

from loglucid.cli import main


def test_cli_feed_on_a_plain_log_file(tmp_path, capsys):
    log = tmp_path / "app.log"
    log.write_text(
        "2026-06-16 INFO starting up\n"
        "2026-06-16 INFO connecting token=sk-proj-" + "A" * 40 + "\n"
        "2026-06-16 ERROR connection refused\n",
        encoding="utf-8",
    )
    rc = main(["feed", str(log), "--last", "10", "--max-tokens", "500"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "ERROR" in out and "connection refused" in out
    assert "[REDACTED]" in out          # secrets in an arbitrary file get masked
    assert "sk-proj-AAAA" not in out


def test_cli_no_redact_flag(tmp_path, capsys):
    log = tmp_path / "a.log"
    log.write_text("INFO hello me@example.com\n", encoding="utf-8")
    main(["feed", str(log), "--no-redact"])
    out = capsys.readouterr().out
    assert "me@example.com" in out
