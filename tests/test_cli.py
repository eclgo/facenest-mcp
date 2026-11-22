# -*- coding: utf-8 -*-
"""CLI contract: the --selftest exit codes must separate "cannot connect" from "refused" (defect A3)."""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from facenest_mcp import server  # noqa: E402


def _endpoint_file(port, token="t"):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"host": "127.0.0.1", "port": port, "token": token,
                   "api_version": "1", "allow_write": False}, fh)
    return path


class SelftestExitCodeTest(unittest.TestCase):
    def test_unreachable_is_3(self):
        path = _endpoint_file(1)          # nothing is listening on port 1
        try:
            self.assertEqual(server.main(["--endpoint", path, "--selftest"]), 3)
        finally:
            os.unlink(path)

    def test_missing_file_is_2(self):
        self.assertEqual(server.main(["--endpoint", "no-such-endpoint.json", "--selftest"]), 2)

    def test_agent_prompt_and_tools_exit_zero(self):
        self.assertEqual(server.main(["--agent-prompt"]), 0)
        self.assertEqual(server.main(["--list-tools"]), 0)

    def test_call_unknown_tool_is_2(self):
        self.assertEqual(server.main(["--call", "nope_tool"]), 2)

    def test_call_unreachable_is_1(self):
        path = _endpoint_file(1)
        try:
            self.assertEqual(server.main(["--endpoint", path, "--call", "facenest_ping"]), 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
