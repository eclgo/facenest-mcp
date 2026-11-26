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

    # -- what the auto-detection consults, and what its failure message offers ----------

    def _write_endpoint_in(self, d, port):
        (Path(d) / "mcp_endpoint.json").write_text(
            json.dumps({"host": "127.0.0.1", "port": port, "token": "abc"}), encoding="utf-8")

    def test_facenest_data_dir_env_var_is_consulted(self):
        """Control: the adapter's own data-dir variable puts that folder into the search."""
        d = tempfile.mkdtemp()
        self._write_endpoint_in(d, 1992)
        os.environ["FACENEST_DATA_DIR"] = d
        try:
            self.assertEqual(load_endpoint().port, 1992)
        finally:
            os.environ.pop("FACENEST_DATA_DIR", None)

    def test_face_data_dir_env_var_is_consulted(self):
        """FACE_DATA_DIR is the variable FaceNest itself uses for its data folder; a user
        who set it for the app expects the adapter to follow the same folder."""
        d = tempfile.mkdtemp()
        self._write_endpoint_in(d, 1993)
        os.environ["FACE_DATA_DIR"] = d
        try:
            self.assertEqual(load_endpoint().port, 1993)
        finally:
            os.environ.pop("FACE_DATA_DIR", None)

    def test_sibling_folder_guess_is_gone(self):
        """The old <cwd>/../FaceNest/data candidate guessed one developer's checkout
        layout and could pick up a stale copy and connect to the wrong target, so it is
        out of the list and stays out."""
        from facenest_mcp import endpoint
        guess = str(Path.cwd().parent / "FaceNest" / "data" / "mcp_endpoint.json")
        self.assertNotIn(guess, [str(p) for p in endpoint._candidate_paths()])

    def test_not_found_message_names_the_endpoint_flag(self):
        """A list of tried paths with no next step dead-ends the terminal user: the
        message must name the flag and the page that shows the path."""
        with self.assertRaises(EndpointError) as ctx:
            load_endpoint(str(Path(tempfile.mkdtemp()) / "nope.json"))
        msg = str(ctx.exception)
        self.assertIn("--endpoint", msg)
        self.assertIn("Settings", msg)


if __name__ == "__main__":
    unittest.main()
