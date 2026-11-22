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

## [0.2.12] - 2026-11-22

First public release. Development began in 2026-10 as a private project; the public changelog starts here.

## Not released: PyPI

The package is not published on PyPI, so `uvx facenest-mcp` fails. Use
`uvx --from git+https://github.com/eclgo/facenest-mcp facenest-mcp` (no clone needed) or an
editable install. Publishing is on the roadmap; when it happens, client configs shrink to
`uvx facenest-mcp`.
