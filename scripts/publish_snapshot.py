#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish a clean open-source snapshot of this repository.

Why this exists: the development history of this adapter lives in the private repository,
with the app's internal revision numbers, its progress notes and the commits that record
internal measurements. The public repository should start from one clean commit that
contains only what a reader needs.

What the script does, in order:
  1. exports the tree of --ref (default HEAD) with `git archive` - tracked files only;
  2. rewrites CHANGELOG.md in the snapshot: the development-history references (commit
     ids, app revision letters, the app repository's commit id) are replaced by the dates
     they belong to, so the release history stays readable and points at nothing private;
  3. swaps the third README badge for the GitHub workflow badge in both README languages,
     and drops the comment block that explains the private-repo badge workaround;
  4. checks the result and refuses to finish if any internal reference survived - a
     snapshot that was only eyeballed is not a checked snapshot.
It never pushes and it never touches this repository: everything is written into --out.

Usage:
    python scripts/publish_snapshot.py --out E:\\facenest-publish\\facenest-mcp
    python scripts/publish_snapshot.py --out E:\\facenest-publish\\facenest-mcp --verify-only

The file quotes the patterns it removes, so the documentation gate exempts it
(tests/test_docs.py, SHIPPED_EXEMPT).
"""
import argparse
import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_REPO = "eclgo/facenest-mcp"

# Anything matching these must not exist in the published tree. Backslashes appear both
# single (prose) and doubled (inside JSON examples), so the class allows 1-2. Paths written for
# the reader as examples - "C:\Users\you\...", "C:\path\to\..." - are placeholders, not leaks;
# what is a leak is this machine's own drive (H:) and its own account folder.
INTERNAL = (
    ("commit id", re.compile(r"`[0-9a-f]{7,40}`")),
    ("app revision letter", re.compile(r"\br\d{3,4}\b")),
    ("private-repo rule file", re.compile(r"AGENTS\.md")),
    ("app build script path", re.compile(r"_build/")),
    ("app source path", re.compile(r"App/mcp_server|mcp_gateway")),
    ("app gateway identifier", re.compile(r"_SESSION_TOOL_LIMIT|_SESSION_FILE_LIMIT")),
    ("progress note reference", re.compile(r"progress note|Progress/")),
    ("developer drive", re.compile(r"H:[\\]+[A-Za-z]")),
    ("developer account folder", re.compile(r"C:[\\]+Users[\\]+Administrator")),
    ("non-placeholder user folder", re.compile(r"C:[\\]+Users[\\]+(?!you\b|path\b|<|\{)")),
)
# These files quote the patterns above in order to remove them, so finding them there is not
# a leak: CHANGELOG keeps history written before the split, and the two tools below carry the
# patterns as their own match rules.
EXEMPT = {"CHANGELOG.md", "tests/test_docs.py", "scripts/publish_snapshot.py"}

COMMIT_TAIL = re.compile(r"\s*[-—]\s*`[0-9a-f]{7,40}`\s*(?:\((\d{4}-\d{2}-\d{2})\))?")
DATE_IN_PARENS = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")

# Sentences that describe how a claim was fixed inside this team (a caption we had to correct,
# a default we had to roll back). They are history for us, not information for a reader, so the
# snapshot drops them. Each pair must be found exactly once, otherwise the build stops - a rule
# that silently stops matching is worse than a rule that fails.
SNIPPETS = (
    ("  real speed — the old caption claimed the clip was uncut, which it is not — "
     "`5a15081` (2026-11-21).",
     "  real speed — `5a15081` (2026-11-21)."),
    ("; reverted to the 60 s default — `e439e42`.", "."),
    # The snapshot removes commit ids, so the page must not promise them.
    ("Every entry names the commit that did it, so any claim on this page is checkable with\n"
     "`git show <hash>`. Dates are commit dates.",
     "Every entry is dated; the dates are commit dates."),
)

BADGE = ('<a href="https://github.com/%s/actions/workflows/test.yml">'
         '<img src="https://github.com/%s/actions/workflows/test.yml/badge.svg" '
         'alt="unittest" height="20"></a>' % (PUBLIC_REPO, PUBLIC_REPO))
STATIC_BADGE_RE = re.compile(
    r'<a href="tests/test_docs\.py"><img '
    r'src="https://img\.shields\.io/badge/unittest-passing[^"]*" '
    r'alt="[^"]*" height="20"></a>')
COMMENT_RE = re.compile(
    r"<!--(?:(?!-->)[\s\S])*?(?:workflow badge|工作流徽章)(?:(?!-->)[\s\S])*?-->\n?", re.I)


def export_tree(ref, dest):
    """git archive -> tar -> files. Only what is tracked at that ref."""
    p = subprocess.run(["git", "archive", "--format=tar", ref], cwd=ROOT, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr.decode("utf-8", "replace"))
        raise SystemExit("git archive failed for %r" % ref)
    with tempfile.TemporaryFile() as fh:
        fh.write(p.stdout)
        fh.seek(0)
        with tarfile.open(fileobj=fh) as tar:
            try:
                tar.extractall(dest, filter="data")      # Python >= 3.12
            except TypeError:
                tar.extractall(dest)


def rewrite_changelog(path, strict_snippets=True):
    text = io.open(path, encoding="utf-8").read()
    # first the internal-history sentences (they quote hashes, so before the hash cleanup)
    for old, new in SNIPPETS:
        n = text.count(old)
        if n == 0 and not strict_snippets:
            continue  # already applied - the source tree is the public repository itself
        if n != 1:
            raise SystemExit("CHANGELOG snippet expected exactly once, found %d: %s"
                             % (n, old[:60]))
        text = text.replace(old, new)
    # "… — `c8be265` (2026-11-21)"  ->  "… (2026-11-21)"
    text = COMMIT_TAIL.sub(lambda m: " (%s)" % m.group(1) if m.group(1) else "", text)
    # a bare commit id inside a sentence -> drop it
    text = re.sub(r"\s*`[0-9a-f]{7,40}`", "", text)
    # "app revision r397, 2026-11-09" -> "the app build of 2026-11-09"
    text = re.sub(r"app revision r\d{3,4},\s*(\d{4}-\d{2}-\d{2})",
                  r"the app build of \1", text)
    # "FaceNest repo (2026-11-21)" (left by the two steps above) -> "the app release of …"
    text = re.sub(r"(?:the )?FaceNest repo \((\d{4}-\d{2}-\d{2})\)",
                  r"the app release of \1", text)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    return text


# Bullets whose whole content is "we corrected our own claims". They carry no information a
# reader of the public repository needs, so a public changelog can start without them. The list
# is opt-in (--changelog-drop-housekeeping); each key must match exactly one bullet.
HOUSEKEEPING = (
    "Quota prose now matches the app",
    "App-side comments/docstrings aligned with the same numbers",
    "Demo GIF caption made honest",
    "The English demo row that still said",
    "Docs rewritten for readers, not for the team",
    "Bilingual pages aligned, with the Chinese page as the authority",
)

RELEASE_HEADER = re.compile(r"## \[(\d+)\.(\d+)\.(\d+)\]")
UNRELEASED_HEADER = re.compile(r"## \[Unreleased\][^\n]*")


def _version(header):
    m = RELEASE_HEADER.match(header)
    return tuple(int(x) for x in m.groups()) if m else None


def trim_changelog(path, frm=None, drop_housekeeping=False, release_date=None,
                   empty_release=False):
    """Optional copy shaping: start the public changelog at a release, and/or drop the
    self-correction bullets. Both are off by default - a full dated history is a valid choice."""
    text = io.open(path, encoding="utf-8").read()
    parts = re.split(r"(?m)^(?=## )", text)
    intro, sections = parts[0], parts[1:]
    dropped_sections = 0
    if frm is not None:
        kept = []
        for s in sections:
            v = _version(s.split("\n", 1)[0])
            if v is not None and v < frm:
                dropped_sections += 1
                continue
            kept.append(s)
        if release_date:
            note = ("## [%s] - %s\n\nFirst public release. Development began in 2026-10 as a "
                    "private project; the public changelog starts here."
                    % (".".join(str(x) for x in frm), release_date))
            kept = [UNRELEASED_HEADER.sub(note, s, count=1) if UNRELEASED_HEADER.match(s) else s
                    for s in kept]
        text = "".join([intro] + kept)
    dropped_bullets = 0
    if empty_release:
        # The first public release page carries the heading and the note only: a list of
        # everything we fixed is our history, not something a reader on day one needs.
        parts = re.split(r"(?m)^(?=## )", text)
        intro, sections = parts[0], parts[1:]
        out = []
        for s in sections:
            if _version(s.split("\n", 1)[0]) == frm:
                lines = s.split("\n")
                keep = []
                for line in lines:
                    keep.append(line)
                    if line.startswith("First public release."):
                        break
                if not any(l.startswith("First public release.") for l in keep):
                    raise SystemExit("empty-release wants the 'First public release.' note "
                                     "(use --release-date)")
                dropped_bullets += sum(1 for l in lines if l.strip().startswith("- "))
                s = "\n".join(keep) + "\n\n"
            out.append(s)
        text = "".join([intro] + out)
    if drop_housekeeping:
        for key in HOUSEKEEPING:
            # one bullet, plus its indented continuation lines
            pat = re.compile(r"(?m)^- [^\n]*" + re.escape(key) + r"[^\n]*(?:\n[ \t]+\S[^\n]*)*\n")
            n = len(pat.findall(text))
            if n != 1:
                raise SystemExit("CHANGELOG housekeeping bullet expected exactly once, "
                                 "found %d: %s" % (n, key))
            text = pat.sub("", text)
            dropped_bullets += 1
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("CHANGELOG trimmed: sections dropped %d, bullets dropped %d"
          % (dropped_sections, dropped_bullets))
    return text


def swap_badge(path):
    text = io.open(path, encoding="utf-8").read()
    n = len(STATIC_BADGE_RE.findall(text))
    if n != 1:
        raise SystemExit("%s: expected exactly one static unittest badge, found %d"
                         % (path, n))
    text = COMMENT_RE.sub("", STATIC_BADGE_RE.sub(BADGE, text, count=1))
    io.open(path, "w", encoding="utf-8", newline="").write(text)


def scan(dest):
    bad = []
    for folder, subdirs, files in os.walk(dest):
        subdirs[:] = [d for d in subdirs if d not in (".git", "__pycache__")]
        for name in files:
            if not name.endswith((".py", ".md", ".yml", ".toml", ".txt", ".json", ".cfg")):
                continue
            p = os.path.relpath(os.path.join(folder, name), dest).replace(os.sep, "/")
            if p in EXEMPT:
                continue
            text = io.open(os.path.join(folder, name), encoding="utf-8").read()
            for i, raw in enumerate(text.splitlines(), 1):
                # JSON examples escape backslashes ("C:\\Users"), which would let a pattern eat
                # one of them and read a placeholder as a real account name. Collapse first.
                line = raw.replace("\\\\", "\\")
                for label, pat in INTERNAL:
                    if pat.search(line):
                        bad.append("%s:%d [%s] %s" % (p, i, label, line.strip()[:100]))
    return bad


def version_of(out):
    text = io.open(os.path.join(out, "pyproject.toml"), encoding="utf-8").read()
    m = re.search(r'version\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else "unknown"


def main():
    ap = argparse.ArgumentParser(description="build the public snapshot of this repo")
    ap.add_argument("--out", required=True, help="target directory for the snapshot")
    ap.add_argument("--ref", default="HEAD", help="git ref to publish (default HEAD)")
    ap.add_argument("--verify-only", action="store_true",
                    help="re-check an existing snapshot directory, write nothing")
    ap.add_argument("--changelog-from", metavar="VERSION",
                    help="public changelog starts at this release, e.g. 0.2.12 "
                         "(older release sections are dropped)")
    ap.add_argument("--release-date", metavar="YYYY-MM-DD",
                    help="date for the --changelog-from heading")
    ap.add_argument("--changelog-drop-housekeeping", action="store_true",
                    help="drop the bullets that only narrate how our own claims were corrected")
    ap.add_argument("--changelog-empty-release", action="store_true",
                    help="the release named by --changelog-from keeps its heading and the "
                         "\"First public release.\" note only: no Added/Changed/Fixed list")
    ap.add_argument("--changelog-already-public", action="store_true",
                    help="the source tree is the public repository: its CHANGELOG already "
                          "went through the SNIPPETS rewrites, so a missing snippet is "
                          "skipped instead of stopping the build (a snippet found twice "
                          "still stops it)")
    a = ap.parse_args()

    if a.verify_only:
        bad = scan(a.out)
        print("verify-only scan of", os.path.abspath(a.out))
        print("internal leftovers:", len(bad))
        for b in bad:
            print("  ", b)
        return 1 if bad else 0

    out = os.path.abspath(a.out)
    if os.path.exists(out) and os.listdir(out):
        raise SystemExit("refusing to write into a non-empty directory: %s" % out)
    os.makedirs(out, exist_ok=True)
    export_tree(a.ref, out)
    n_files = len(subprocess.run(["git", "-C", ROOT, "ls-files"],
                                 capture_output=True).stdout.decode("utf-8").split())

    changelog = rewrite_changelog(os.path.join(out, "CHANGELOG.md"),
                                  strict_snippets=not a.changelog_already_public)
    frm = None
    if a.changelog_from:
        parts = a.changelog_from.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise SystemExit("--changelog-from wants VERSION like 0.2.12")
        frm = tuple(int(p) for p in parts)
    if frm or a.changelog_drop_housekeeping or a.changelog_empty_release:
        if a.changelog_empty_release and not (frm and a.release_date):
            raise SystemExit("--changelog-empty-release wants --changelog-from and --release-date")
        trim_changelog(os.path.join(out, "CHANGELOG.md"), frm=frm,
                       drop_housekeeping=a.changelog_drop_housekeeping,
                       release_date=a.release_date,
                       empty_release=a.changelog_empty_release)
    for readme in ("README.md", "README.zh-CN.md"):
        swap_badge(os.path.join(out, readme))
    version = version_of(out)

    bad = scan(out)
    if bad:
        print("SNAPSHOT REJECTED - internal references survived:")
        for b in bad:
            print("  ", b)
        raise SystemExit(3)

    print("snapshot written to", out)
    print("files exported (git ls-files at %s):" % a.ref, n_files)
    print("version in the snapshot:", version)
    print("CHANGELOG rewritten, dated entries kept:", len(DATE_IN_PARENS.findall(changelog)))
    print("badges swapped: README.md, README.zh-CN.md")
    print("internal leftovers: 0")
    print()
    print("Next, from the snapshot directory (the push stays yours; set your own")
    print("author identity first - it becomes public):")
    print("  cd %s" % out)
    print("  git init -b main")
    print("  git add -A")
    print('  git commit -m "facenest-mcp %s: 28 tools, MCP over stdio"' % version)
    print("  git remote add origin https://github.com/%s.git" % PUBLIC_REPO)
    print("  git push -u origin main")


if __name__ == "__main__":
    sys.exit(main())
