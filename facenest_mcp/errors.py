"""Translate FaceNest's `ERR_*` codes into text a weak model can act on directly.

Why a module of its own: the error text is the only "documentation" an agent ever
sees. FaceNest replies with `ERR_CODE|prose`, and that prose is written for the app's
human interface — for an English-speaking model it is neither precise nor actionable.
This module normalises everything into "code -> meaning -> next action -> retry?".
"""

from __future__ import annotations

from typing import Dict, Tuple

#: code -> (meaning, next action, retry?)
#: `retry=True` is reserved for cases where retrying is harmless (e.g. a different id).
#: Gateway-level refusals are always False, otherwise a weak model loops
#: "refused -> retry -> refused" (evaluation report items G3 / G10).
HINTS: Dict[str, Tuple[str, str, bool]] = {
    "ERR_SMART_NOT_FOUND": (
        "That smart album does not exist.",
        "Call facenest_list_smart_albums and use a smart_id it returns (the rules are NOT the problem).",
        True),
    "ERR_SMART_PERSON_NOT_FOUND": (
        "The person cluster_id in a rule does not exist.",
        "Call facenest_list_people (include_unnamed=true if needed) and use a real cluster_id.",
        True),
    "ERR_SMART_PHOTOS_UNKNOWN": (
        "Some image_id values (in a photos rule or cover_image_id) are not in the library.",
        "Re-run facenest_search and pass only ids it returned; do not shorten or guess ids.",
        True),
    # r438b: copy_photos uses its own code (not the smart-album one); retrying
    # with real ids is the correct next step, so Retry must be YES.
    "ERR_MCP_PHOTOS_UNKNOWN": (
        "Some image_id values are not in the library.",
        "Call facenest_search and pass only ids it returned; do not shorten or guess ids.",
        True),
    "ERR_MCP_TARGET_FORBIDDEN": (
        "The destination folder is inside the FaceNest library or program directory.",
        "Ask the user for a normal folder outside FaceNest (for example D:\\Work\\Deck) "
        "and call again with that absolute path.",
        False),
    "ERR_MCP_TARGET_NOT_WRITABLE": (
        "The destination folder is not writable.",
        "Ask the user to pick a folder they can write to (or fix its permissions), then retry.",
        False),
    "ERR_MCP_TARGET_COLLISION": (
        "Too many files with the same name already exist in the destination folder.",
        "Change rename_pattern (include {index} or {id}) or clean the destination, then retry.",
        True),
    "ERR_MCP_COPY_FAILED": (
        "One file could not be copied (disk full, path too long, or permission denied).",
        "Read the per-file detail; other files may already be copied. Fix the cause, then retry.",
        True),
    "ERR_SMART_NAME_DUP": (
        "A smart album with that name already exists.",
        "Pick a different name, or call facenest_update_smart_album on the existing album "
        "(names are unique; use smart_id, not the name).",
        True),
    "ERR_SEM_DISABLED": (
        "Semantic search is turned off in FaceNest.",
        "Ask the user to enable semantic search in FaceNest → Settings → Semantic search.",
        False),
    "ERR_SEM_NO_MODEL": (
        "The semantic model (~1.56 GB) is not downloaded yet.",
        "Ask the user to download it in FaceNest → Semantic search, then retry once.",
        False),
    "ERR_SEM_PREMIUM": (
        "The free semantic-query allowance is used up.",
        "Tell the user; Pro lifts the limit. Do not retry.",
        False),
    "ERR_SEM_BUSY": (
        "The tagging job is using the model right now.",
        "Wait until tagging finishes, then call again.",
        True),
    "ERR_BAD_ARGS": (
        "A tool argument is missing or out of range.",
        "Fix the argument(s) named in the details and call again with the same tool.",
        True),
    "ERR_MCP_TIMEOUT": (
        "FaceNest did not answer before the MCP call timed out.",
        "The semantic model is probably still loading. Wait 5–10 seconds, then call the "
        "same tool again (do not conclude the tool is broken).",
        True),
    "ERR_MCP_INTERNAL": (
        "The MCP adapter hit an unexpected internal error.",
        "Retry the same call once. If it repeats, report the tool name and this text to the user.",
        True),
    "ERR_MCP_IMAGE_NOT_FOUND": (
        "image_path does not point to a file.",
        "Pass an absolute path to an existing image on this machine, or use image_id instead.",
        True),
    "ERR_MCP_IMAGE_NOT_IMAGE": (
        "The file at image_path is not a readable jpg/png/webp/bmp image.",
        "Pass a real image file; text / PDF / RAW are rejected.",
        True),
    "ERR_MCP_IMAGE_TOO_LARGE": (
        "The reference image is larger than 20 MB.",
        "Downscale the reference image and try again.",
        True),
    "ERR_HTTP": (
        "The app rejected the request (usually a parameter outside its allowed range).",
        "Read the details, adjust the argument, and call again.",
        True),
    "ERR_MCP_DISABLED": (
        "The MCP service is turned off in FaceNest.",
        "Ask the user to open FaceNest → AI agent → tick 'Expose the MCP service'.",
        False),
    "ERR_MCP_TOKEN": (
        "The access token is wrong or was reset.",
        "Ask the user to copy the token again (FaceNest → AI agent → Copy) and update the client config.",
        False),
    "ERR_MCP_LOCAL_ONLY": (
        "Only loopback (127.0.0.1) connections are allowed.",
        "Use this MCP server on the same machine as FaceNest.",
        False),
    "ERR_MCP_WRITE_OFF": (
        "This is a write tool and writing is disabled.",
        "Ask the user to tick 'Allow writes' in FaceNest → AI agent. "
        "This is a permission switch — the rules themselves are fine.",
        False),
    "ERR_PRO_REQUIRED": (
        "The installed FaceNest is an older build that gated video tools behind Pro "
        "(removed in FaceNest 1.3.14: video tools work on every edition).",
        "Nothing to fix in the arguments. Tell the user to update FaceNest "
        "(Settings → Check for updates); after the update the same call works. Do not retry now.",
        False),
    "ERR_MCP_SESSION_LIMIT": (
        "The per-session limit for this write tool is used up "
        "(video frames: 40; photo copies: 2,000 files).",
        "The user can reset the token in FaceNest → AI agent to start a new session (counter goes back to 0), "
        "or continue without writing. Do not retry this call.",
        False),
    "ERR_MCP_NO_FACE": (
        "The reference photo contains no usable face.",
        "Pick another photo that clearly shows a face. Uploading a new picture is not supported.",
        True),
    "ERR_MCP_PERSON_NOT_FOUND": (
        "That person (cluster_id) or reference face does not exist.",
        "Call facenest_list_people again and use a fresh cluster_id (unnamed people are hidden by default).",
        True),
    "ERR_MCP_VIDEO_NOT_FOUND": (
        "That video_id does not exist.",
        "Call facenest_list_videos again and use a fresh video_id.",
        True),
    "ERR_MCP_VIDEO_FILE_MISSING": (
        "The video is recorded in the library but its file is missing on disk.",
        "Tell the user the file was moved or deleted; nothing the agent can fix.",
        False),
    "ERR_MCP_FRAME_GRAB": (
        "No decodable frame at that timestamp.",
        "Try a slightly different timestamp (accuracy is ± one frame interval, default 2 s).",
        True),
    "ERR_MCP_TIMESTAMP_RANGE": (
        "The requested timestamp is outside the video.",
        "Use 0 <= timestamp_sec <= duration_sec; the error text includes the real duration.",
        True),
    "ERR_MCP_NOT_FOUND": (
        "The requested id does not exist.",
        "Search again (facenest_search) and use the ids returned by that call.",
        True),
    "ERR_MODEL_MISSING": (
        "The face/video index is not built yet.",
        "Ask the user to run video frame extraction (or import photos) in FaceNest first.",
        False),
    "ERR_UNREACHABLE": (
        "The FaceNest app is not answering on its local port.",
        "Make sure FaceNest is running and the MCP service is enabled; then call facenest_ping.",
        False),
    # FaceNest was not running (or MCP was off) when this server
    # started. That is not "the tool is broken" — it is "not ready yet". Retrying is
    # allowed: once the user turns MCP on, the very next call heals itself without
    # restarting the client.
    "ERR_MCP_NOT_READY": (
        "FaceNest has not published its MCP endpoint yet (app not running, or the MCP service is off).",
        "Ask the user to open FaceNest -> Settings -> AI agent (MCP) and tick "
        "'Expose the MCP service'. This adapter re-reads mcp_endpoint.json on every call, "
        "so retrying afterwards works without restarting the client or opening a new session.",
        True),
}

#: Fallback for smart-album rule errors: the rule grammar is a closed set, so the
#: hint points at the enum instead of guessing.
_SMART_HINT = (
    "The rule set is invalid.",
    "Use ONLY the shapes in the facenest_query_photos / facenest_create_smart_album description: "
    "person{is|is_not, cluster_id}; person_count{eq|lte|gte, n}; tag{has|not_has, name, "
    "source:any|auto|manual}; date{between|on|before|after|this_year|this_month|last_days, "
    "from/to/days, sources?}; place{is|is_not, country|admin1|city}; photos{in, ids}; "
    "camera{is, value}; lens{is, value}; origin{is, photo|video_frame}; caption{has|not_has, text, "
    "lang?}; favorite{is|is_not}. Max 30 rules.",
    True)


def hint_for(code: str) -> Tuple[str, str, bool]:
    # Exact codes first: `ERR_SMART_NOT_FOUND` (album missing) must not get the
    # generic "rules invalid" hint (defect A1).
    if code in HINTS:
        return HINTS[code]
    if code.startswith("ERR_SMART_"):
        return _SMART_HINT
    return ("The call failed.",
            "Read the message; if it repeats, stop and tell the user instead of retrying.",
            False)


def format(code: str, prose: str = "", status: int = 0) -> str:
    """Build the three-part reply: code + meaning + next action (plus the app's prose as details)."""
    meaning, action, retry = hint_for(code)
    head = f"{code}" + (f" (HTTP {status})" if status else "")
    lines = [f"{head}: {meaning}", f"Do next: {action}"]
    if retry:
        lines.append("Retry: YES — safe to call again (e.g. with different ids or timestamps).")
    else:
        lines.append("Retry: NO — this will not succeed until the user changes a setting.")
    if prose:
        lines.append(f"Details from FaceNest: {prose}")
    return "\n".join(lines)
