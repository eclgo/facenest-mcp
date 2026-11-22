"""Find + parse FaceNest's `mcp_endpoint.json`."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class EndpointError(RuntimeError):
    """A one-line message meant for the user — never a traceback."""


@dataclass
class Endpoint:
    host: str
    port: int
    token: str
    api_version: str = "1"
    allow_write: bool = False

    @property
    def base_url(self) -> str:
        host = self.host or "127.0.0.1"
        return f"http://{host}:{int(self.port)}"


def _candidate_paths() -> List[Path]:
    """Ordered most likely to least likely: explicit env var, then common install locations."""
    out: List[Path] = []
    env_file = os.environ.get("FACENEST_ENDPOINT")
    if env_file:
        out.append(Path(env_file))
    data_dir = os.environ.get("FACENEST_DATA_DIR")
    if data_dir:
        out.append(Path(data_dir) / "mcp_endpoint.json")

    home = Path.home()
    local = os.environ.get("LOCALAPPDATA")
    roaming = os.environ.get("APPDATA")
    for base in (local, roaming):
        if base:
            out.append(Path(base) / "FaceNest" / "data" / "mcp_endpoint.json")
    out += [
        Path.cwd() / "data" / "mcp_endpoint.json",
        Path.cwd() / "mcp_endpoint.json",
        # Common dev layout: the FaceNest app checkout sits next to this repo.
        Path.cwd().parent / "FaceNest" / "data" / "mcp_endpoint.json",
        home / "FaceNest" / "data" / "mcp_endpoint.json",
    ]
    return out


def load_endpoint(path: Optional[str] = None) -> Endpoint:
    """Read the endpoint file; on failure raise EndpointError with an actionable message."""
    tried: List[str] = []
    if path:
        candidates = [Path(path)]
    else:
        candidates = _candidate_paths()

    for cand in candidates:
        tried.append(str(cand))
        try:
            if not cand.is_file():
                continue
            data = json.loads(cand.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise EndpointError(f"Could not read {cand}: {exc}") from exc
        host = str(data.get("host") or "127.0.0.1")
        port = int(data.get("port") or 0)
        token = str(data.get("token") or "")
        if not port or not token:
            raise EndpointError(
                f"{cand} has no port/token — open FaceNest and turn the service on under "
                "Settings → AI agent (MCP), then try again.")
        return Endpoint(host=host, port=port, token=token,
                        api_version=str(data.get("api_version") or "1"),
                        allow_write=bool(data.get("allow_write")))

    raise EndpointError(
        "FaceNest's mcp_endpoint.json was not found. Do one of these:\n"
        "  1) Open FaceNest → Settings → AI agent (MCP) → tick \"Expose the MCP service\";\n"
        "  2) Set the environment variable FACENEST_ENDPOINT=<full path to that file>.\n"
        "Locations already tried:\n  - " + "\n  - ".join(tried))
