# -*- coding: utf-8 -*-
"""Insert / refresh the table of contents inside the two agent guides.

Run from the repo root:  python scripts/gen_doc_toc.py

Why generated: the guides grow in every round (new rule shapes, new limits). A hand-written
contents list drifts the moment a section is renamed, and a reader following a stale entry
lands on the wrong section. The entries here are taken from the `## ` headings of the file
itself, skipping fenced code blocks (the copy-paste system prompt inside section 7 is data,
not structure).

The block lives between the markers `<!-- TOC:START -->` and `<!-- TOC:END -->` so re-running
the script is a no-op when nothing changed. The gate
tests/test_docs.py::test_guide_toc_matches_headings recomputes the same list and fails when the
block is stale.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FILES = [os.path.join("docs", "AGENT_GUIDE.md"),
         os.path.join("docs", "AGENT_GUIDE.zh-CN.md")]

START = "<!-- TOC:START -->"
END = "<!-- TOC:END -->"
LABEL = {"docs/AGENT_GUIDE.md": "Contents", "docs/AGENT_GUIDE.zh-CN.md": "目录"}


def slug(title):
    """GitHub-style anchor: lowercase, drop punctuation, spaces to dashes. CJK is kept."""
    s = title.strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff \-]", "", s)
    return s.replace(" ", "-")


def headings(text):
    """The `## ` headings of the file, in order, ignoring fenced code blocks."""
    out = []
    fence = None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if fence is None:
                fence = stripped[:3]
            elif stripped[:3] == fence:
                fence = None
            continue
        if fence is not None:
            continue
        if line.startswith("## "):
            title = line[3:].strip()
            out.append(title)
    return out


def render_entries(text):
    hs = headings(text)
    seen = {}
    lines = []
    for title in hs:
        base = slug(title)
        n = seen.get(base, 0)
        seen[base] = n + 1
        anchor = base if n == 0 else "%s-%d" % (base, n)
        lines.append("- [%s](#%s)" % (title, anchor))
    return lines


def render_block(text, rel_path):
    label = LABEL[rel_path.replace("\\", "/")]
    return "\n".join([START, "**%s**" % label] + render_entries(text) + [END])


def main():
    for rel in FILES:
        path = os.path.join(ROOT, rel)
        text = io.open(path, encoding="utf-8").read()
        block = render_block(text, rel)
        if START in text and END in text:
            new = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S)
        else:
            lines = text.split("\n")
            # place it after the last line of the header block (the first '---' separator)
            at = next((i for i, l in enumerate(lines) if l.strip() == "---"), 1)
            lines.insert(at, block + "\n")
            new = "\n".join(lines)
        if new != text:
            io.open(path, "w", encoding="utf-8", newline="\n").write(new)
            print("updated", rel, "| entries:", len(render_entries(text)))
        else:
            print("no change", rel, "| entries:", len(render_entries(text)))


if __name__ == "__main__":
    main()
