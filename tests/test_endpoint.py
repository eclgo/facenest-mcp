# -*- coding: utf-8 -*-
"""Endpoint discovery and the quality of its error messages."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facenest_mcp.endpoint import EndpointError, load_endpoint  # noqa: E402


class EndpointTest(unittest.TestCase):
    def test_load_explicit_path(self):
        d = tempfile.mkdtemp()
        p = Path(d) / "mcp_endpoint.json"
        p.write_text(json.dumps({"host": "127.0.0.1", "port": 1992,
                                 "token": "abc", "api_version": "1"}), encoding="utf-8")
        ep = load_endpoint(str(p))
        self.assertEqual(ep.base_url, "http://127.0.0.1:1992")
        self.assertEqual(ep.token, "abc")

    def test_missing_file_message_tells_user_what_to_do(self):
        with self.assertRaises(EndpointError) as ctx:
            load_endpoint(str(Path(tempfile.mkdtemp()) / "nope.json"))
        msg = str(ctx.exception)
        self.assertIn("mcp_endpoint.json", msg)
        self.assertIn("Expose the MCP service", msg)

    def test_incomplete_file_is_rejected(self):
        d = tempfile.mkdtemp()
        p = Path(d) / "mcp_endpoint.json"
        p.write_text(json.dumps({"host": "127.0.0.1"}), encoding="utf-8")
        with self.assertRaises(EndpointError) as ctx:
            load_endpoint(str(p))
        self.assertIn("port/token", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
