# Contributing

Small project, few rules, and the checks are the rules. Everything below is enforced by the test
suite, so a contribution that follows it merges without a discussion about style.

## Set up

```bash
git clone https://github.com/eclgo/facenest-mcp.git
cd facenest-mcp
python -m pip install -e .

python -m unittest discover -s tests        # the whole suite, no app needed
facenest-mcp --selftest --endpoint "<path from the app's Settings page>"   # needs the app running on this machine
```

Python 3.9 or newer. **The suite does not need the app running** — that is deliberate: a
contributor (and CI) can prove the code is sound without a photo library. The suite runs on
3.9, 3.12 and 3.13 on every push and pull request.

## Before you write code

- [Quick start](docs/QUICKSTART.md) — install and client configuration.
- [Troubleshooting](docs/TROUBLESHOOTING.md) — every `ERR_` code, its cause and its fix.
- [Tool reference](docs/TOOLS.md) — what each tool takes and returns, read/write, per-tool limits.
- [Architecture](docs/ARCHITECTURE.md) — which file owns which job, and where each number's
  single source is.

If a change adds or renames a tool, the tool reference, the guide and the counts in the README all
move with it. The gates tell you which page is out of step; fix the page, never the gate.

## The generator rules (the most common source of failed checks)

Some pages are **generated**, so editing them by hand is always wrong:

| Page | Generator | Gate |
| --- | --- | --- |
| `docs/TOOLS.md` | `python scripts/gen_tools_doc.py` (reads `server.TOOLS`) | the file must equal the generator's output |
| the contents block in both guides | `python scripts/gen_doc_toc.py` | the block must match the file's own `## ` headings |

Numbers (frame quotas, per-call and per-session limits, error-code count, tool count) live in the
tool descriptions and in `docs/TOOLS.md`. Prose pages link there instead of repeating them; a gate
fails when prose carries a stale number.

The pages come in language pairs (`X.md` + `X.zh-CN.md`). The pair must keep the same structure,
and the Chinese page is the authority for examples — when the Chinese page has a fuller example,
the English page mirrors it. A gate compares the two structures.

## Making a change

- **One intent per commit.** Message form: `type(scope): summary`, with `type` one of
  `feat` `fix` `refactor` `test` `docs` `chore`.
- **Behaviour changes come with a test** — including a failure path: a missing file, an empty
  library, writes switched off, a bad argument. A test that passes without your change proves
  nothing; run it before and after.
- **Python 3.9 compatible, zero dependencies.** No dependency additions, please — staying
  installable with nothing but the standard library is a feature we protect.
- Add a bullet to `CHANGELOG.md` under the unreleased heading. After the pull request merges
  (it merges squashed), the bullet carries the commit hash and date.
- Keep `mcp_endpoint.json` out of the repository; it is a token file and it is in `.gitignore`.

## Pull requests

Write the PR title as the commit you want to exist: `type(scope): summary`. Pull requests merge
**squashed**, so title = the commit message in the history.

CI has to be green. If a gate fails, read its assertion message first — it names the file, the
line and the pattern. A gate that fails because your change is real is a gate doing its job.

## Questions

- Bugs and feature requests: open an issue (the templates ask for the few things we need).
- Security problems: [SECURITY.md](SECURITY.md) — private email, not an issue.
