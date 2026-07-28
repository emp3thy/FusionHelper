"""Minimal MCP client over stdlib urllib (httpx/requests deliberately absent --
this client is test-only, see docs/detailed-design.md "Dependencies").

Envelope, measured against live Fusion 2026-07-28 (verified twice that session,
re-verified at the start of this task):
- `initialize` returns 200 with `serverInfo`, and the response carries an
  `MCP-Session-Id` header that must be captured and echoed on every later
  request.
- `notifications/initialized` returns 202 with a 0-byte body -- a client that
  JSON-parses every response crashes on the handshake.
- `result.content[0].text` is a JSON STRING containing either
  `{"message": <stdout>, "success": true}` or
  `{"error": <stdout + traceback>, "success": false}`. Script failures are
  HTTP 200 + success:false, never a JSON-RPC error.
"""
import json
import urllib.request
from dataclasses import dataclass
from typing import Any

FH_RESULT_PREFIX = "FH_RESULT "


@dataclass
class ExecResult:
    success: bool
    message: str
    error: str


class McpClient:
    def __init__(self, url: str):
        self.url = url
        self._id = 0
        self._session: str | None = None   # MCP-Session-Id, captured at initialize

    def _post(self, payload: dict[str, Any], expect_json: bool = True) -> Any:
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if self._session:
            headers["MCP-Session-Id"] = self._session
        req = urllib.request.Request(self.url, json.dumps(payload).encode(), headers)
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            sid = r.headers.get("MCP-Session-Id")
            if sid:
                self._session = sid
            return json.loads(body) if expect_json and body else None

    def initialize(self) -> Any:
        self._id += 1
        out = self._post({"jsonrpc": "2.0", "id": self._id, "method": "initialize",
                          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "fusionhelper-tests",
                                                    "version": "0.1.0"}}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"},
                   expect_json=False)   # 202, EMPTY body -- do not parse
        return out

    def execute(self, script_text: str) -> ExecResult:
        self._id += 1
        out = self._post({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                          "params": {"name": "fusion_mcp_execute",
                                     "arguments": {"featureType": "script",
                                                   "object": {"script": script_text}}}})
        inner = json.loads(out["result"]["content"][0]["text"])
        return ExecResult(bool(inner.get("success")),
                          inner.get("message", ""), inner.get("error", ""))

    def undo(self) -> Any:
        self._id += 1
        return self._post({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                           "params": {"name": "fusion_mcp_update",
                                      "arguments": {"operation": "undo"}}})


def parse_fh_result(text: str) -> dict[str, Any]:
    """Parse the last `FH_RESULT {json}` line out of a script's stdout.

    Task 17's probe scripts print exactly one such line as their final
    output; assertions target this parsed data, never surrounding prose
    (the probe run itself caught a script whose pre-written summary
    contradicted its own data -- see docs/probe-results.md). Raises
    ValueError when no such line is present, so a broken probe script fails
    loudly instead of every assertion silently comparing against None.
    """
    for line in reversed(text.splitlines()):
        if line.startswith(FH_RESULT_PREFIX):
            return json.loads(line[len(FH_RESULT_PREFIX):])
    raise ValueError(f"no {FH_RESULT_PREFIX!r} line found in: {text!r}")
