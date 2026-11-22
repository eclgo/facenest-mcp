# -*- coding: utf-8 -*-
"""Regenerate `docs/_generated/_tools.txt` from the live tool schema, and expose the same
rendering to the test gate (`tests/test_docs.py`), so the published tool list can never drift
from the code.

Run from the repo root:  python scripts/_dump_tools.py

Why this exists: a hand-maintained tool list drifts silently - `_tools.txt` stayed at 21 tools
through four adapter versions. The file is generated; the test asserts file == render(TOOLS).
(`docs/TOOLS.md` has its own generator, `scripts/gen_tools_doc.py`, gated the same way.)
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "_generated", "_tools.txt")


def render(tools):
    """The exact text of `_tools.txt` for a tool list (one block of 3 lines per tool)."""
    lines = ["count=%d" % len(tools)]
    for t in tools:
        desc = (t.get("description") or "").replace("\n", " ")
        schema = t.get("inputSchema") or {}
        props = list((schema.get("properties") or {}).keys())
        req = schema.get("required") or []
        lines.append("- %s\n    params=%s required=%s\n    desc=%s" % (t["name"], props, req, desc))
    return "\n".join(lines)


def main():
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    out = subprocess.run([sys.executable, "-m", "facenest_mcp", "--list-tools"],
                         capture_output=True, cwd=ROOT, env=e)
    data = json.loads(out.stdout.decode("utf-8"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(render(data["tools"]))
    print("ok", len(data["tools"]), "->", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
