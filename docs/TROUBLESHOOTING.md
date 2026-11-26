# Troubleshooting

The short version of everything the app and the adapter can tell you. Each item states the
symptom, what it means, and the fix. Numbers (quotas, sizes) are not repeated here — they are
in [docs/TOOLS.md](TOOLS.md), generated from the tool schema.

## `--selftest` says something other than `OK`

| Exit code | Meaning | Fix |
|---|---|---|
| **2** | Endpoint file not found | Open the app: Settings → AI agent (MCP), confirm the service is on, then pass the path that page shows: `facenest-mcp --selftest --endpoint "<absolute path>"` |
| **3** | Nothing is listening on that port | The app is closed, or the MCP switch is off. Start the app / turn the switch on |
| **1** | Reached the app, and it refused | The token was reset, or the switch was turned off after the endpoint file was written. Re-open MCP in the app, then re-run `--selftest` |

`OK` is the target line: `OK  http://127.0.0.1:<port>  api=…  images=…  write_allowed=…`.

## The adapter starts with "not ready yet"

You may see:

```
[facenest-mcp] not ready yet: …
[facenest-mcp] serving anyway: tools are listed now; every call re-reads …
```

That is by design: the adapter starts, publishes the tool list, and re-reads the endpoint file
on every call. Calls fail until the app is reachable; once the app is running, the same client
session works again — you do not have to restart the client.

## A call answers `ERR_MCP_NOT_READY`

The app's **Expose MCP service** switch is off, or the app is closed. Turn it on. This is not a
token problem.

## A call answers `ERR_MCP_WRITE_OFF`

The app's **Allow writes** switch is off. It is a second, separate switch: turning MCP on does
not turn writes on. Read tools are unaffected — they never write.

## HTTP 401 / 403

The token in `mcp_endpoint.json` no longer matches the app (it was reset in the app's settings,
or the file is an old copy). Re-open MCP in the app and point the client at the current
endpoint file.

## Works in the terminal, not in the client

Almost always the endpoint path:

- Use an **absolute** path in `--endpoint`. Auto-detection depends on the process working
  directory, and GUI clients do not have a predictable one — it only ever hits when the
  adapter is started inside the FaceNest install folder.
- On Windows, paths inside JSON / TOML must be written with `\\`.
- The environment variable `FACENEST_ENDPOINT` is also read (so is the app's own
  `FACE_DATA_DIR`).
- The client must run the same Python that has the adapter installed. `facenest-mcp --selftest`
  in a terminal proves the adapter side; if the terminal works and the client does not, the
  client's `command` points at a different Python.

## The app was restarted and the port changed

The adapter re-reads the endpoint file on every call, so a new port/token is picked up without
restarting the client. If the client keeps showing a stale connection, restart that client's MCP
server entry (its own reload / toggle), not the app.

## The assistant quotes file names instead of ids

It is inventing them. Every tool takes ids, not file names. Make it run `facenest_search` (or
`facenest_query_photos`) first and use the `image_id` from the reply. The app rejects invented
ids — that is a feature, not a bug.

## Several references given at once for faces / frames

`facenest_find_similar_faces`, `facenest_similar_photos` and the video pickers accept exactly
one reference. The order the app uses is:

`person` > `image_id` > `face_id` > `image_path`

(`face_id` is looked up in the photo library first, then in the video index.) The `reference`
field in the reply says which one was used, and `reference.ambiguous` tells you the app had to
choose between several faces in one photo — show them to the user and ask which one.

## "Album creation failed" / "copy failed"

Writes are switched off in the app (see `ERR_MCP_WRITE_OFF` above). Also check the target
folder rules of the copy tool in [docs/TOOLS.md](TOOLS.md): the target must already exist and
must be outside the photo library.

## An album / search returns nothing

Not an error. Rules are combined with AND by default; one impossible rule empties the result.
The reply carries per-rule counts and says which rule emptied it. Relax one rule at a time.
If a count is 0 but `max_similarity` is greater than 0, the best candidate is **below your
sensitivity threshold** — that is not "no such photos".

## A number you need (per-call / per-session limits, sizes, counts)

Look it up in [docs/TOOLS.md](TOOLS.md). It is generated from the tool schema, so it is the
same number the app enforces; this page deliberately does not repeat those numbers.

## Something is broken and the docs did not help

Open an issue: <https://github.com/eclgo/facenest-mcp/issues>. Paste the tool name, the exact
reply text (the `ERR_…` code in particular), and the output of `facenest-mcp --selftest`.
