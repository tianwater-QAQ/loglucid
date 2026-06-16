import io
import json

from loglucid.mcp_server import handle, serve


def test_initialize_reports_protocol_and_server():
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert r["result"]["serverInfo"]["name"] == "loglucid"
    assert "protocolVersion" in r["result"]
    assert "tools" in r["result"]["capabilities"]


def test_initialized_notification_has_no_response():
    assert handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_tools_list_exposes_feed_tools():
    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in r["result"]["tools"]}
    assert names == {"lucid_feed_file", "lucid_feed_text"}
    for t in r["result"]["tools"]:
        assert "inputSchema" in t


def test_tools_call_feed_text_redacts_and_keeps_error():
    req = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
           "params": {"name": "lucid_feed_text",
                      "arguments": {"text": "INFO ok token=ghp_" + "a" * 36 +
                                            "\nERROR boom",
                                    "max_tokens": 500}}}
    r = handle(req)
    text = r["result"]["content"][0]["text"]
    assert "[REDACTED]" in text and "ghp_aaaa" not in text
    assert "ERROR" in text and "boom" in text
    assert r["result"].get("isError") is False


def test_unknown_method_returns_jsonrpc_error():
    r = handle({"jsonrpc": "2.0", "id": 9, "method": "no/such"})
    assert r["error"]["code"] == -32601


def test_serve_loop_over_stdio():
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ]
    stdin = io.StringIO("\n".join(json.dumps(m) for m in msgs) + "\n")
    stdout = io.StringIO()
    serve(stdin, stdout)
    responses = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    assert [r["id"] for r in responses] == [1, 2]   # notification produced no response
