# -*- coding: utf-8 -*-
"""Generate `docs/TOOLS.md` from the live tool schema - the one place a reader can look up
every tool's parameters, its read/write nature and its limits.

Run from the repo root:  python scripts/gen_tools_doc.py

Why generated: a hand-written tool page drifted before (the compact listing stayed at 21 tools
through four adapter versions). Nothing in the page is typed: parameters and descriptions come
from `--list-tools`, the write/read label is derived from the tool's own description, and the
group mapping is checked to cover exactly the tools the code exposes - add a tool without
adding it here and the gate fails.

The gate lives in tests/test_docs.py: it compares docs/TOOLS.md with this module's own
`render(tools)`, so the page can only ever say what the code says.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT = os.path.join("docs", "TOOLS.md")

# Group -> tool names. Must cover exactly the tools the code exposes (checked in render()).
GROUPS = [
    ("Start", ["facenest_ping"]),
    ("Find photos", ["facenest_search", "facenest_query_photos", "facenest_semantic_search",
                     "facenest_list_tags", "facenest_image_context"]),
    ("People and faces", ["facenest_list_people", "facenest_person_photos",
                          "facenest_find_similar_faces", "facenest_similar_photos"]),
    ("Albums", ["facenest_list_albums", "facenest_list_smart_albums",
                "facenest_smart_album_images", "facenest_create_smart_album",
                "facenest_update_smart_album", "facenest_delete_smart_album"]),
    ("Places and duplicates", ["facenest_list_places", "facenest_photos_in_place",
                               "facenest_find_duplicates"]),
    ("Video", ["facenest_list_videos", "facenest_list_video_frames",
               "facenest_find_person_in_videos", "facenest_pick_best_video_frames",
               "facenest_collect_video_frame", "facenest_collect_video_frames"]),
    ("Picking and delivery", ["facenest_pick_best_photos", "facenest_make_contact_sheet",
                              "facenest_copy_photos"]),
]

WRITE_MARKERS = ("Requires 'Allow writes'", "needs 'Allow writes'")


def is_write(description):
    """Derived, not typed. A tool is a write tool when its own description asks for the app's
    separate "Allow writes" switch: the write tools open with `WRITE` / `WRITE TOOL`, and
    `facenest_copy_photos` says "Requires 'Allow writes'".

    Do NOT match on the bare phrase "Allow writes": `facenest_query_photos` contains
    "no 'Allow writes' needed" and would be mislabelled as a write tool. The label set this
    rule produces is exactly the set of endpoints the app gates with
    `_guard(..., require_write=True)` in `App/app/api/routes_mcp.py` (verified 2026-11-21)."""
    d = (description or "").strip()
    return d.startswith("WRITE") or any(m in d for m in WRITE_MARKERS)


def _anchor(group):
    return group.lower().replace(" ", "-")


def render(tools):
    by_name = {t["name"]: t for t in tools}
    mapped = [n for _, names in GROUPS for n in names]
    missing = sorted(set(by_name) - set(mapped))
    extra = sorted(set(mapped) - set(by_name))
    if missing or extra:
        raise SystemExit("GROUPS does not cover the tool set: missing=%s extra=%s"
                         % (missing, extra))
    if len(mapped) != len(set(mapped)):
        raise SystemExit("GROUPS lists a tool twice: %s" % mapped)

    writes = [n for n in mapped if is_write(by_name[n].get("description"))]
    lines = [
        "# Tool reference",
        "",
        "<!-- Generated file. Do not edit by hand: run `python scripts/gen_tools_doc.py`.",
        "     The gate tests/test_docs.py::test_tools_md_equals_the_generated_doc compares this",
        "     file against the live tool schema, so a stale page fails the suite. -->",
        "",
        "> Generated from the live tool schema by `scripts/gen_tools_doc.py`.",
        "> %d tools: %d read, %d write. A write tool needs the app's separate **Allow writes**"
        % (len(tools), len(tools) - len(writes), len(writes)),
        "> switch - the two switches in the app are independent, and read tools never write.",
        "> Parameters marked *required* are the ones the tool refuses to run without.",
        "> Limits (per-call / per-session quotas, size caps) are quoted from each tool's own",
        "> description, so this page cannot advertise a number the app does not enforce.",
        "",
        "| Group | Tools |",
        "|---|---|",
    ]
    for group, names in GROUPS:
        lines.append("| [%s](#%s) | %d |" % (group, _anchor(group), len(names)))
    lines.append("")

    for group, names in GROUPS:
        lines.append("## %s" % group)
        lines.append("")
        for name in names:
            tool = by_name[name]
            schema = tool.get("inputSchema") or {}
            props = list((schema.get("properties") or {}).keys())
            required = schema.get("required") or []
            kind = "write" if is_write(tool.get("description")) else "read"
            lines.append("### `%s` · %s" % (name, kind))
            lines.append("")
            if props:
                shown = ["`%s`*" % p if p in required else "`%s`" % p for p in props]
                lines.append("- Parameters: %s" % ", ".join(shown))
                if required:
                    lines.append("- Required: %s" % ", ".join("`%s`" % p for p in required))
            else:
                lines.append("- Parameters: none")
            desc = " ".join((tool.get("description") or "").split())
            lines.append("- Description: %s" % desc)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    out = subprocess.run([sys.executable, "-m", "facenest_mcp", "--list-tools"],
                         capture_output=True, cwd=ROOT, env=env)
    data = json.loads(out.stdout.decode("utf-8"))
    text = render(data["tools"])
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8") as fh:
        fh.write(text)
    n_write = sum(1 for t in data["tools"]
                  if is_write(t.get("description")))
    print("ok %d tools (%d write) -> %s" % (len(data["tools"]), n_write, OUT))


if __name__ == "__main__":
    main()
