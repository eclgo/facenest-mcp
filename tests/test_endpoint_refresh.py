"""Endpoint self-heal: after the app restarts on a new port, a long-lived MCP
process must re-read the endpoint file by itself."""
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from facenest_mcp.api import Client, FaceNestError  # noqa: E402
from facenest_mcp.endpoint import Endpoint  # noqa: E402


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path.startswith('/mcp/ping'):
            body = json.dumps({"ok": True, "api_version": "1", "images": 7,
                               "write_allowed": True}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


class TimeoutMappingTest(unittest.TestCase):
    """When the semantic model's first load exceeds the normal timeout this must
    become a structured ERR_MCP_TIMEOUT, never a bare TimeoutError (which turns into -32603)."""

    def test_timeout_becomes_structured_error(self):
        from unittest.mock import patch
        c = Client(Endpoint(host='127.0.0.1', port=1, token='tok'))
        with patch('facenest_mcp.api.urllib.request.urlopen',
                   side_effect=TimeoutError('timed out')):
            with self.assertRaises(FaceNestError) as ctx:
                c.ping()
        self.assertEqual(ctx.exception.code, 'ERR_MCP_TIMEOUT')
        self.assertIn('did not answer', str(ctx.exception))

    def test_semantic_calls_use_60s_timeout(self):
        """Measured 4 s cold start (17.3 s upper bound), so 60 s is about 15x
        headroom; ordinary endpoints stay at 20 s."""
        import inspect
        src = inspect.getsource(Client.similar_photos)
        self.assertIn('timeout=60', src)
        src = inspect.getsource(Client.semantic_search)
        self.assertIn('timeout=60', src)


class EndpointRefreshTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(('127.0.0.1', 0), _Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        tmp = socket.socket()
        tmp.bind(('127.0.0.1', 0))
        cls.dead_port = tmp.getsockname()[1]
        tmp.close()
        cls.dir = Path(tempfile.mkdtemp(prefix='fn_r267_'))
        cls.ep = cls.dir / 'mcp_endpoint.json'
        cls.ep.write_text(json.dumps({"host": "127.0.0.1", "port": cls.port, "token": "tok",
                                      "api_version": "1", "allow_write": True}), encoding='utf-8')

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_self_heal_on_dead_port(self):
        c = Client(Endpoint(host='127.0.0.1', port=self.dead_port, token='tok'),
                   endpoint_path=str(self.ep))
        data = c.ping()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('images'), 7)
        self.assertEqual(c.endpoint.port, self.port, "the client must pick up the live port from the file")

    def test_no_path_fails_fast(self):
        """Hermetic: auto-discovery deliberately searches the sibling
        FaceNest checkout, so with a dev app running this client self-heals and the test
        would "pass by accident". Here every search root points at an empty directory.
        """
        empty = Path(tempfile.mkdtemp(prefix="fn_r361_"))
        env = {"FACENEST_ENDPOINT": "", "FACENEST_DATA_DIR": "",
               "LOCALAPPDATA": str(empty), "APPDATA": str(empty)}
        with mock.patch.dict(os.environ, env), \
                mock.patch("pathlib.Path.home", return_value=empty), \
                mock.patch("os.getcwd", return_value=str(empty)):
            c = Client(Endpoint(host='127.0.0.1', port=self.dead_port, token='tok'))
            with self.assertRaises(Exception) as ctx:
                c.ping()
        shutil.rmtree(empty, ignore_errors=True)
        exc = ctx.exception
        code = getattr(exc, 'code', '') or ''
        self.assertIn('UNREACHABLE', f'{code} {exc}')

    def test_broken_file_fails_fast(self):
        bad = self.dir / 'bad.json'
        bad.write_text('{not json', encoding='utf-8')
        c = Client(Endpoint(host='127.0.0.1', port=self.dead_port, token='tok'),
                   endpoint_path=str(bad))
        with self.assertRaises(Exception) as ctx:
            c.ping()
        exc = ctx.exception
        code = getattr(exc, 'code', '') or ''
        self.assertIn('UNREACHABLE', f'{code} {exc}')
