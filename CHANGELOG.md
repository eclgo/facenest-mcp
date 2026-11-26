# Changelog

All notable changes to this adapter. Format: Keep a Changelog.
The version here is the `version` field of [pyproject.toml](pyproject.toml) — it is one number,
kept in two places (`pyproject.toml` and `facenest_mcp/__init__.py`), and the app it talks to has its
own version (`FaceNest 1.4.x`).

Every entry is dated; the dates are commit dates.

## [Unreleased]

### Added

- A security policy, a contributor guide and issue forms: [SECURITY.md](SECURITY.md),
  [CONTRIBUTING.md](CONTRIBUTING.md) and `.github/ISSUE_TEMPLATE/` (bug report, feature request,
  and a contact list that sends security reports to email instead of a public issue).
  `tests/test_docs.py` now asserts those files exist, that the links in them point at pages that
  are in the tree, and that the contributor guide names the real test command and the two
  documentation generators.
- A code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Conduct reports go to the same
  address as security reports, with a different subject prefix, and stay private.
- The package metadata now carries the contact address the documentation already names, so
  someone who installs with `pip` can reach a person without opening a GitHub issue.
  `tests/test_docs.py` asserts the address in `pyproject.toml` is the same one the docs use.
- On the index, the published 0.2.12 files were deleted the same day, so the index carries
  **only 0.2.13**. PyPI does not let a deleted file name be uploaded again and deleting is
  allowed within 72 hours of an upload ([PEP 763](https://peps.python.org/pep-0763/)), which is
  why the fixed description went out as a new version. The two sections below describe the index
  as it stood on 2026-11-23 at 15:26 (UTC+8), when 0.2.12 was published; this entry is the
  current record.

## [0.2.14] - 2026-11-26

The endpoint-file failure path used to end in a wall of tried paths and no next step. The
not-found message now names the flag and the page that shows the path (`--endpoint "<path
copied from Settings → AI agent (MCP)>"`); auto-detection also reads `FACE_DATA_DIR` (the
data-folder variable FaceNest itself uses) next to `FACENEST_DATA_DIR`; and the
`<cwd>/../FaceNest/data` guess is gone - it matched only one developer's checkout layout and
could pick up a stale copy and connect to the wrong target. Every self-test line on the
install pages (README, Quick start, Contributing) now passes the absolute `--endpoint`, the
install pages lead with the config the app's own Settings page generates - that config runs
on the Python inside the FaceNest folder, so nothing has to be installed to use it - and the
pages state where auto-detection can and cannot hit. `tests/test_endpoint.py` gained gates
for both environment names, for the message naming `--endpoint`, and for the removed guess.

## [0.2.13] - 2026-11-23

The page on the package index is part of the release, and 0.2.12's page showed two broken images:
both READMEs embedded `<img>` with a repo-relative `src`, which an index renders away from the
repository, so it resolves outside it. The `src`s are absolute URLs now; the install pages lead
with `python -m pip install facenest-mcp` and `uvx facenest-mcp --selftest` and keep the GitHub
route as a third option; `pyproject.toml` names the repository, the install page and this file
under `[project.urls]`.

`tests/test_docs.py` gained two gates — the install pages must name both PyPI commands, and every
README `<img src>` must be an absolute `https` URL — and the stale-claim rule was inverted, so a
page that says the adapter is *not* on PyPI now fails the gate.

0.2.12 stays on the index as it is. PyPI does not let a deleted file name be uploaded again, so a
release with a fixed description needs a new version number, and this is that version.

## [0.2.12] - 2026-11-22

First public release. Development began in 2026-10 as a private project; the public changelog starts here.

## Published on PyPI - 2026-11-23

`facenest-mcp` 0.2.12 is on PyPI: <https://pypi.org/project/facenest-mcp/>. Install with
`python -m pip install facenest-mcp`; a client config can now use `uvx facenest-mcp`, which is what
the install pages say. The published wheel was installed from the index on this machine and its
`facenest-mcp` entry point ran: `--help` printed the option list, and `--selftest` reported the two
app-off cases as designed (no endpoint file → exit 2, a refused port → exit 3).
