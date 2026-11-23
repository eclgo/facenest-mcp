# Quick start

Install the adapter, prove it reaches the app, then wire it into a client.
This page is the single home for install and client configuration; the README keeps a short
version and links here, so the same instructions are not maintained in two places.

## What you need

- **FaceNest running on this machine**, with MCP switched on. The free tier is enough
  (its photo and semantic-query limits are stated on the [README](../README.md) and the
  website). [Download](https://facenest.net/download).
- **Python 3.9 or newer** (the adapter has no third-party dependencies).
- The **endpoint file** the app writes: `mcp_endpoint.json`. In the app:
  Settings → AI agent (MCP) → turn on "Expose MCP service", then copy the file path shown.

## Install

```bash
# Option A - install from PyPI (recommended)
python -m pip install facenest-mcp
facenest-mcp --selftest

# Option B - one command, nothing installed (uv/uvx fetches it from PyPI and runs it)
uvx facenest-mcp --selftest

# Option C - from GitHub (no PyPI, or you want to edit the adapter)
uvx --from git+https://github.com/eclgo/facenest-mcp facenest-mcp --selftest
git clone https://github.com/eclgo/facenest-mcp.git
cd facenest-mcp
python -m pip install -e .
facenest-mcp --selftest
```

A successful self-test prints one line like:

```
OK  http://127.0.0.1:<port>  api=1  images=1234  write_allowed=false
```

`OK` means the adapter reached the app. The **port is decided by the app at run time** —
`1992` is only an example in some config files, so trust the self-test output.
Any other result (exit code 1 / 2 / 3) is covered in
[Troubleshooting](TROUBLESHOOTING.md).

> 🔒 `mcp_endpoint.json` holds a plain-text token. Treat it like a password; it is in
> `.gitignore`, never commit it.

## Verify without a client

```bash
facenest-mcp --selftest        # reachability + app version + write state
facenest-mcp --list-tools      # the tool schema the adapter publishes
facenest-mcp --agent-prompt    # the system prompt to paste into your agent
facenest-mcp --call facenest_ping                 # call one tool directly
facenest-mcp --call facenest_search --arg q=beach --arg mode=text
```

`facenest_ping` answers with the app version, how many photos it sees, and whether writes are
allowed — that is the fastest way to tell "the adapter works" from "the app is closed".

## Connect a client

Any client that speaks **stdio MCP** works. Only two things matter: the command
`python -m facenest_mcp` and the argument `--endpoint <absolute path>`.

**Claude Desktop** — `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "facenest": {
      "command": "python",
      "args": ["-m", "facenest_mcp", "--endpoint",
               "C:\\Users\\you\\AppData\\Roaming\\FaceNest\\mcp_endpoint.json"]
    }
  }
}
```

**Cursor** — `~/.cursor/mcp.json` (or `.cursor/mcp.json` in the project)

```json
{
  "mcpServers": {
    "facenest": {
      "command": "python",
      "args": ["-m", "facenest_mcp", "--endpoint", "C:\\path\\to\\mcp_endpoint.json"]
    }
  }
}
```

**OpenCode** — `opencode.json`

```json
{
  "mcp": {
    "facenest": {
      "type": "local",
      "command": ["python", "-m", "facenest_mcp", "--endpoint", "C:\\path\\to\\mcp_endpoint.json"],
      "enabled": true
    }
  }
}
```

**Codex CLI** — `~/.codex/config.toml`

```toml
[mcp_servers.facenest]
command = "python"
args = ["-m", "facenest_mcp", "--endpoint", "C:\\path\\to\\mcp_endpoint.json"]
```

**DSH / any other client** — copy `command` and `args` from any block above into that client's
MCP config.

> On Windows write JSON / TOML paths as `\\`.
> Prefer an **absolute** `--endpoint`: auto-detection depends on the process working
> directory, which is unreliable in GUI clients. `FACENEST_ENDPOINT` works as an environment
> variable.

## The two switches in the app

| Switch | What it does |
|---|---|
| Expose MCP service | Lets the adapter connect at all. Off → every call answers `ERR_MCP_NOT_READY`. |
| Allow writes | Lets the write tools change anything. Off → they answer `ERR_MCP_WRITE_OFF`. |

They are independent. The read tools never write, whatever the second switch says.
Each tool is labelled read or write in [docs/TOOLS.md](TOOLS.md), which is generated from the
tool schema — so the split shown there cannot disagree with the code.

## Next

- What to ask for, with the tool chain for each: [README](../README.md)
  ([简体中文](../README.zh-CN.md)).
- Every parameter and quota, on one page: [docs/TOOLS.md](TOOLS.md).
- Building an agent: [docs/AGENT_GUIDE.md](AGENT_GUIDE.md).
- Something failed: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
