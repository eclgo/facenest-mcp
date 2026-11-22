# Security policy

This repository holds the **MCP adapter**: a small stdio process that a chat client starts, and
that talks to the FaceNest app running on the same machine. It has no third-party dependencies and
it does not open a network port of its own.

## Reporting a vulnerability

**Send it to support@facenest.net, subject starting with `mcp:`.**
Please do **not** open a public issue for a security problem — an open issue is a working
report to everyone, including people who have not patched anything.

Tell us:

- the adapter version (the line printed by `facenest-mcp --selftest`) and the app version it names;
- your operating system, Python version, and the MCP client you used;
- what you saw, and the shortest set of steps that reproduces it;
- whether photos, the endpoint file, or the app's token were involved.

What you get back: an acknowledgement within three business days, a fix in a release, and credit
in the release notes if you want it. The report stays private until the fix is out.

## What is in scope

- Adapter code in this repository, and everything it ships.
- Handling of `mcp_endpoint.json` — the plain-text token file the app writes. It is listed in
  `.gitignore`; treat it like a password.
- The adapter only ever connects to the app on `127.0.0.1`. The app decides the port at run time.
- The write gate: tools that change the library are off by default, and every one of them answers
  with a clear refusal when writes are off.
- What the adapter puts into error text, logs and tool results — paths and tokens should not be
  echoed wider than they already are.

## What is out of scope

- The FaceNest app itself, its web interface, and anything reached from outside `127.0.0.1`.
- Third-party MCP clients and their own configuration files.
- Physical access to the machine, and any photo library you hand to someone else.

## Defaults you can rely on

- Your photos are read from the local library and stay local; the adapter uploads nothing.
- No telemetry, no analytics, no network calls except to the app on this machine.
- The adapter is a single Python file tree with zero dependencies, so the code you run is the code
  in this repository.
