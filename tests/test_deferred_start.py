# -*- coding: utf-8 -*-
"""The server must NOT exit when FaceNest is not running (or MCP is off).

Measured 2026-10-31 (build 1.3.8): MCP was left off, so the session showed 0 tools;
turning "Expose the MCP service" on afterwards and restarting OpenCode still gave 0
tools - only toggling the switch plus opening a new session worked.
Root cause: `main()` returned 2 when it could not read `mcp_endpoint.json`; the
process died, the client recorded this server as FAILED and retried nothing.

The contract now:
1. no endpoint file => initialize / tools/list still answer (tools appear immediately);
2. every call re-reads the file => a file that shows up later heals itself, no restart;
3. `--selftest` still fails strictly (exit code 2) - scripts and CI branch on that.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from facenest_mcp import server  # noqa: E402
from facenest_mcp.api import Client, FaceNestError  # noqa: E402
from facenest_mcp.endpoint import Endpoint  # noqa: E402

TOOLS = server.TOOLS


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = json.dumps({"ok": True, "path": self.path}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep the test harness quiet
        pass


class DeferredStartTest(unittest.TestCase):
    def test_stdio_starts_without_endpoint_and_lists_tools(self):
        d = tempfile.mkdtemp()
        missing = str(Path(d) / "mcp_endpoint.json")
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        stdin = "\n".join(json.dumps(m) for m in msgs) + "\n"
        proc = subprocess.run(
            [sys.executable, "-m", "facenest_mcp", "--endpoint", missing],
            input=stdin, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60, cwd=ROOT)
        self.assertEqual(proc.returncode, 0,
                         "server must not exit when the endpoint file is absent; "
                         f"stderr={proc.stderr}")
        out = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(out), 2, proc.stdout)
        self.assertEqual(out[0]["id"], 1)
        self.assertEqual(out[0]["result"]["serverInfo"]["name"], "facenest-mcp")
        self.assertEqual(out[1]["id"], 2)
        self.assertEqual(len(out[1]["result"]["tools"]), len(TOOLS))
        self.assertIn("not ready", proc.stderr)

    def test_selftest_still_fails_fast(self):
        d = tempfile.mkdtemp()
        missing = str(Path(d) / "mcp_endpoint.json")
        proc = subprocess.run(
            [sys.executable, "-m", "facenest_mcp", "--endpoint", missing, "--selftest"],
            input="", capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60, cwd=ROOT)
        # Exit-code contract from the docs: 2 = endpoint file not found (scripts/CI branch on it; do not quietly change it to 3)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("ERR_MCP_NOT_READY", proc.stderr)

    def test_late_endpoint_file_heals_on_next_call(self):
        d = tempfile.mkdtemp()
        path = Path(d) / "mcp_endpoint.json"
        srv = HTTPServer(("127.0.0.1", 0), _Handler)
        port = srv.server_address[1]
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        try:
            client = Client(Endpoint(host="127.0.0.1", port=0, token=""),
                            endpoint_path=str(path))
            with self.assertRaises(FaceNestError) as ctx:
                client._request("GET", "/ping")
            self.assertEqual(ctx.exception.code, "ERR_MCP_NOT_READY")

            # the user enables MCP in the app => the file appears => the next call in the same process works
            path.write_text(json.dumps({"host": "127.0.0.1", "port": port,
                                        "token": "tok", "api_version": "1"}),
                            encoding="utf-8")
            data = client._request("GET", "/ping")
            self.assertTrue(data["ok"], data)
        finally:
            srv.shutdown()
            srv.server_close()
            th.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
