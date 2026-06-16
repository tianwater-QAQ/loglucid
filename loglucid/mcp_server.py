"""A Model Context Protocol (MCP) server for loglucid.

This is loglucid's headline integration: point Claude Code / Cursor / any MCP
client at it and the agent can pull your logs as a compact, **redacted**,
token-budgeted block on its own — no copy-paste. It exposes two tools:

  * ``lucid_feed_file`` — read a log file and pack it.
  * ``lucid_feed_text`` — pack raw log text passed inline.

It speaks the MCP stdio transport (newline-delimited JSON-RPC 2.0) with no third
-party dependency, so the request handling is plain and unit-testable. Launch it
with ``loglucid mcp`` and register that command with your MCP client.
"""
from __future__ import annotations

import json
import sys

from . import __version__
from .cli import _records_from_lines
from .feed import build_feed
from .levels import parse_level

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "loglucid", "version": __version__}

_ARGS_SCHEMA_COMMON = {
    "last": {"type": "integer", "default": 80, "description": "How many recent lines to consider."},
    "max_tokens": {"type": "integer", "default": 2000, "description": "Token budget for the block."},
    "level": {"type": "string", "default": "INFO", "description": "Minimum level to include."},
    "redact": {"type": "boolean", "default": True, "description": "Redact secrets/PII (recommended)."},
}

TOOLS = [
    {
        "name": "lucid_feed_file",
        "description": "Read a log file and return a compact, de-noised, redacted, "
                       "token-budgeted block ready for an LLM to debug. Errors are always kept.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the log file."},
                           **_ARGS_SCHEMA_COMMON},
            "required": ["path"],
        },
    },
    {
        "name": "lucid_feed_text",
        "description": "Same as lucid_feed_file but for raw log text passed inline.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Raw log text."},
                           **_ARGS_SCHEMA_COMMON},
            "required": ["text"],
        },
    },
]


def _pack(text: str, args: dict, app: str) -> str:
    records = _records_from_lines(text.splitlines(), app)
    return build_feed(
        records,
        last=int(args.get("last", 80)),
        min_level=parse_level(args.get("level", "INFO")),
        max_tokens=int(args.get("max_tokens", 2000)),
        do_redact=bool(args.get("redact", True)),
        app=app,
    )


def _result(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _error(rid, code, message):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _text_content(text, is_error=False):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def handle(req: dict):
    """Pure JSON-RPC handler. Returns a response dict, or None for notifications."""
    method = req.get("method")
    rid = req.get("id")

    if method == "initialize":
        return _result(rid, {"protocolVersion": PROTOCOL_VERSION,
                             "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO})
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return _result(rid, {})
    if method == "tools/list":
        return _result(rid, {"tools": TOOLS})
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            if name == "lucid_feed_file":
                path = args["path"]
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                app = path.rsplit("/", 1)[-1]
                return _result(rid, _text_content(_pack(text, args, app)))
            if name == "lucid_feed_text":
                return _result(rid, _text_content(_pack(args.get("text", ""), args, "logs")))
            return _result(rid, _text_content(f"unknown tool: {name}", is_error=True))
        except Exception as e:  # report tool errors to the client, don't crash
            return _result(rid, _text_content(f"error: {e}", is_error=True))

    if rid is not None:
        return _error(rid, -32601, f"method not found: {method}")
    return None


def serve(stdin=None, stdout=None) -> int:
    """Run the stdio MCP loop (newline-delimited JSON-RPC)."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req)
        if resp is not None:
            stdout.write(json.dumps(resp) + "\n")
            stdout.flush()
    return 0
