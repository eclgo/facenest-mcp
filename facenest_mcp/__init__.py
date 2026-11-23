"""facenest-mcp — hand a local FaceNest photo library to an AI agent (MCP over stdio).

Design boundaries:

* **It only talks through FaceNest's local HTTP `/mcp/*`** — it never opens the
  SQLite file, never touches photo files, and never leaves the machine
  (127.0.0.1 only).
* Connection details come from the `mcp_endpoint.json` the app writes, or from
  the `FACENEST_ENDPOINT` environment variable.
* Read-only by default. Write tools require the user to tick "Allow writes" in
  the app under Settings → AI agent (MCP).
* Text extracted from images (captions/OCR) is always treated as **data** and is
  labelled as such in every reply, never as an instruction.
"""

__version__ = "0.2.13"
