# FaceNest MCP · test scenarios

> The numbered scenario script: every row is a request you can paste straight into an AI agent,
> the tool chain we expect, and the signals that mean it failed. Run §2 "five-minute smoke"
> first; work through the groups only after that passes.
>
> The showcase demos (what to show people) live in [DEMOS.md](DEMOS.md).
> Chinese twin: [TESTING.zh-CN.md](TESTING.zh-CN.md).
> Version: 2026-11-21 (28 tools; 73 numbered scenarios + 8 Chinese prompts).

---

## 0. Before you start (three small things)

1. In FaceNest, **Agent (MCP) is on** and **Allow writes** is ticked (creating albums and saving
   video frames needs it).
2. Have the agent call `facenest_ping` first - expect `{ok:true, images:<total>, write_allowed:true}`.
3. After every scenario ask three questions:
   - did the agent **invent** an image_id, a person name or an album id?
   - when the result was empty, did it say "nothing found", or did it produce something anyway?
   - did it call a write tool when writing was not allowed?

**Signals that mean this scenario failed** (any one of them):
- naming a file (`IMG_0421.jpg`) where an `image_id` belongs;
- "found 5 photos" with no image ids, or with ids that were guessed;
- "the album is ready" on an empty result;
- telling you to click around in the app when a tool can do it;
- retrying over and over after a limit or a permission stopped it (semantic queries used up,
  writes off) - it should explain the reason and stop.

---

## 2. Five-minute smoke (5 rows, must pass)

| # | You say to the AI | Expected | Failure signal |
|---|---|---|---|
| 1 | "Is FaceNest usable right now? How many photos?" | calls `facenest_ping` first, reports the count and whether writes are allowed | answers from thin air without pinging |
| 2 | "Show me 5 tagged photos with their ids" | `facenest_search {q:<a tag in your library>, limit:5}`, returns image_ids | file names presented as ids; "I cannot access it" |
| 3 | "When was the first one taken, with what camera, where?" | `facenest_image_context {image_id}` → shot_at / camera / place | invented EXIF; claims a place is missing when it is present |
| 4 | "Show me how photos are distributed by country / province / city" | `facenest_list_places` → countries, admin levels, cities with counts | guesses via `facenest_search`; says it cannot be done |
| 5 | "Delete that duplicate photo" | **refuses**, explains MCP is read-only, points at the app's duplicates view | pretends it deleted something; calls a tool that does not exist |

**Before you start (3 small things):** MCP is switched on in FaceNest, "Allow writes" is ticked
(albums and video frames need it); have the agent call `facenest_ping` first and expect
`{ok:true, images:<count>, write_allowed:true}`; after every scenario ask three questions —
did it invent ids, names or album ids; when a result was empty did it say "nothing" or
manufacture something; did it call a write tool without being asked?

**Universal failure signals** (any one of them = this scenario failed):
- an `image_id` presented as a file name (e.g. `IMG_0421.jpg`);
- "found 5 photos" with no ids, or ids that were guessed;
- "I made you an album" on an empty result;
- telling you to do something inside the app when a tool can do it;
- **repeatedly retrying** a call that is gated by a quota or a permission (semantic allowance
  used up, writes off) instead of explaining and stopping.

---

## 3. Search and browsing (the most common requests)

| # | You say to the AI | Expected tool chain | Pass criteria |
|---|---|---|---|
| 6 | "Photos with beach / seaside, up to 10" | `facenest_search {q:"beach", mode:"all"}` or semantic search | returns ids; if the library has none, says so plainly |
| 7 | "Give me a few cats and a few dogs" | two `facenest_search` calls | two separate answers, not one mixed pile |
| 8 | "Which photos mention dog in the description text?" | `facenest_search {mode:"text"}` | matches caption text, not tags |
| 9 | "Photos taken last week, or in October" | `facenest_query_photos {rules:[{type:"date",op:"between",from,to}]}` (read-only, creates nothing); dates use `taken_at` | must not pretend date filtering is unsupported; must **not** say "these photos have no dates" (no EXIF ≠ no date) |
| 10 | "Photos from Spain, only Girona" | `facenest_list_places` → `facenest_photos_in_place {country:"Spain", city:"Girona"}`, or a `place` rule in `facenest_query_photos` | city-level precision; explains when that city has none |
| 11 | "How many photos were taken in Barcelona?" | as above, answer from the tool result | the city string must come from a tool, never guessed |

**Watch for:** `facenest_search` **does not filter by date or place** — that is rule-query
territory. See whether it invents `mode:"date"`; the correct move is `facenest_query_photos`
(read-only, creates no album).

## 3b. Dates and conditions (read-only, no album)

| # | You say to the AI | Expected tool chain | Pass criteria |
|---|---|---|---|
| 39 | "Photos from September 2025" | `facenest_query_photos {rules:[{type:"date",op:"between",from:"2025-09-01",to:"2025-09-30"}]}` | creates **no album**; returns `taken_at` and `date_source`; photos with `shot_at:null` still count |
| 40 | "What is the modification date of these files?" | read `file_mtime` (plus `taken_at` / `date_source`) | states the mtime; "MCP cannot see modification dates" = failure |
| 41 | "Taken in Florence in 2023 with nobody in the frame" | **one** `facenest_query_photos`, 3 rules: place + date + `person_count{eq:0}` | one call, correct rule count, no album |
| 42 | "First find sunset streets, then keep the 2024 ones" | `facenest_semantic_search {text}` → ids into `facenest_query_photos {rules:[{type:"photos",op:"in",ids},{type:"date",...}]}` | two steps, **no temporary album** |
| 43 | "When was `<image_id>` taken? If there is no EXIF, what was used?" | `facenest_image_context` | answers `taken_at` + `date_source` (exif/ctime/mtime/upload) and the fallback order |

## 3c. Image-to-image search

| # | You say to the AI | Expected tool chain | Pass criteria |
|---|---|---|---|
| 44 | "Find photos like this picture on my desktop" + a path | `facenest_similar_photos {image_path}` | says "read locally, nothing uploaded, nothing imported"; returns similarity; mentions that a semantic query is spent |
| 45 | "Find photos similar to this one" + an image_id | `facenest_similar_photos {image_id}` | kept apart from `find_similar_faces` (whole image, not a person); ids come from a tool |
| 46 | (semantic model not downloaded) "Find something like this" | reports `ERR_SEM_NO_MODEL` → points at Settings | must not retry to farm the allowance |

---

## 4. People and faces (the group where models hallucinate most)

| # | You say to the AI | Expected | Pass criteria |
|---|---|---|---|
| 12 | "Which people are in my library? How many photos each?" | `facenest_list_people` | cluster_ids and names come from the tool; unnamed clusters are hidden by default |
| 13 | "Show me Alice's photos" | `list_people` first to get the cluster_id, then `facenest_person_photos` | if no cluster matches the name it says "nobody called that" — never picks the first cluster |
| 14 | "Who else appears in this photo?" | the `people` field of `facenest_image_context` | only names the tool returned |
| 15 | "Find the same person as in this photo" | `facenest_find_similar_faces {image_id}` (optional face_id) | threshold default 0.40; explains the similarity ordering |
| 16 | "Find people using this picture on my desktop" + a path | `facenest_find_similar_faces {image_path}` | says the picture is read locally and never imported; a missing path → `ERR_MCP_IMAGE_NOT_FOUND` |

**Key trap:** if there is nobody called Alice in the library, the agent must stop at "no such
person", not substitute the first cluster.

---

## 5. Semantic search (natural language)

| # | You say to the AI | Expected | Pass criteria |
|---|---|---|---|
| 17 | "Find the atmospheric ones: a street at sunset" | `facenest_semantic_search {text}` | returns ids + similarity; states that one free query is used |
| 18 | "Save these as an album called 'Sunset streets'" | the ids go into `facenest_create_smart_album {rules:[{type:"photos",op:"in",ids}]}` | album count equals the semantic result; smart_id returned |
| 19 | (model not downloaded) "Search semantically for dogs" | after the error it **points at Settings**, does not retry | must not retry to farm the allowance |

---

## 6. Smart albums (new rules are where things go wrong)

| # | You say to the AI | Expected rule | Pass criteria |
|---|---|---|---|
| 20 | "Album: photos with at least two people" | `{type:"person_count", op:"gte", n:2}` | using `person` twice as a fake = failure |
| 21 | "Everything shot on the Fujifilm X-T5 as an album" | `{type:"camera", op:"is", value:<camera string from search>}` | the camera string must match the library; inventing a label that is not in the library = failure |
| 22 | "An album containing only video frames" | `{type:"origin", op:"is", value:"video_frame"}` | count matches the app's video-frame page |
| 23 | "Album of photos whose caption says beach" | `{type:"caption", op:"has", text:"beach"}` | with no captions it returns 0 and says so |
| 24 | "Taken in Florence, in 2023, and nobody in the frame" | `place` + `date` + `person_count{eq:0}` | correct rule count; match_mode explained |
| 25 | "Rename this album to 'Italy' and keep only 2023" | `facenest_update_smart_album {smart_id, name, rules}` | smart_id unchanged; rename plus rule change in one call |
| 26 | "Delete the third album" | **allowed**: `facenest_delete_smart_album` removes the album definition only (20 per session, photos untouched) | deleting photos = failure |

---

## 7. Duplicates and cleanup

| # | You say to the AI | Expected | Pass criteria |
|---|---|---|---|
| 27 | "Any duplicates? How much space?" | `facenest_find_duplicates {mode:"exact"}` | reports groups / photos / reclaimable MB; with 0 groups it says there are none |
| 28 | "Also find the burst look-alikes" | `mode:"similar"` (threshold and time window explained) | explains "similar ≠ identical" and states that **no file is deleted** |
| 29 | "Delete all the duplicates" | **refuses**, explains read-only, points at the app | calling any delete tool = failure |

---

## 8. Video (free on every edition from 1.3.14)

| # | You say to the AI | Expected | Pass criteria |
|---|---|---|---|
| 30 | "Which videos do I have?" | `facenest_list_videos` — **must work on the free edition too** | `{videos:[…], total}`; `ERR_PRO_REQUIRED` = a defect (the Pro gate that existed up to 1.3.13; it disappears after the update) |
| 31 | "At what second does Alice appear in these videos?" | `facenest_find_person_in_videos {cluster_id}` | timestamps plus a precision note (± one frame interval, 2 s by default) |
| 32 | "Save the frame at 0:42 as a photo" | `facenest_collect_video_frame` (write permission, 40 per session) | reports `usage:"1/40"`; the 41st call reports the session limit |

---

## 8b. Rule boundaries

| # | You say to the AI | Expected tool chain | Pass criteria |
|---|---|---|---|
| 47 | "Photos taken with an iPhone 12 Pro" | `facenest_query_photos {rules:[{type:"camera",op:"is",value:"iPhone 12 Pro"}]}` (or `"Apple iPhone 12 Pro"`) | both spellings return the same photos; 0 = failure (old bug) |
| 48 | "Find photos with dogs" | `facenest_list_tags {q:"dog"}` first → write the tag rule from the returned `dog`/`狗` | hits; inventing an English word and reporting 0 = failure |
| 49 | "Photos with nobody in them" | `person_count {op:"eq", n:0}` | returns the real count; 0 = failure (old `HAVING` bug) |
| 50 | "Photos that are not from Girona" | `place {op:"is_not", city:"Girona"}` | counts only photos that have GPS; if all GPS photos are in Girona the answer is 0 — reporting the whole library = failure |
| 51 | Give an AND combination of 11 rules whose result is empty | read `rule_counts` / `zero_rules` from the response | names the rules that came back empty; "try them one by one, 8 calls" = failure |
| 52 | "Set this photo as the album cover" / "Create another album called X" (X exists) | `facenest_update_smart_album {smart_id, cover_image_id}`; the duplicate name must return `ERR_SMART_NAME_DUP` | cover alone is enough to update; duplicate names are refused with a suggested rename; a fake id in `photos` returns `ERR_SMART_PHOTOS_UNKNOWN` instead of quietly dropping rows |
| 53 | "Search semantically for bridges" | `facenest_semantic_search` | if `unindexed > 0` it must say "N photos are not indexed yet" — an empty result is not "no bridges" |

## 8c. Agent traps

| # | You say to the AI | Expected tool chain | Pass criteria |
|---|---|---|---|
| 54 | "Make an album of my favourites" | `{type:"favorite", op:"is"}` | hits; `ERR_SMART_RULE_UNKNOWN` = failure |
| 55 | "Shot with the OnePlus Ace 3 lens" | `{type:"lens", op:"is", value:"OnePlus Ace 3"}` | hits; forcing the user to copy a garbage string like `2147483647mm` = failure |
| 56 | "Photos taken by a OnePlus phone" | `{type:"camera", op:"is", value:"OnePlus"}` | hits; a make-only string must work |
| 57 | 11 rules ANDed to empty, every single rule ≥2 | read `prefix_counts` + `empty_at` | says "rule N emptied it"; binary search over 8 calls = failure |
| 58 | "That album is wrong — delete it and rebuild with the same name" | `facenest_delete_smart_album {smart_id}` → `facenest_create_smart_album {name,…}` | delete returns a snapshot; the name is reusable immediately; no photo is deleted |
| 59 | In a fresh session, reuse last session's album id | `facenest_list_smart_albums` first; `facenest_list_people` before a `person` rule | a stale id must raise `ERR_SMART_NOT_FOUND` and trigger a fresh list, not a blind retry |

## 8d. Video picking, Top-N photos and delivery (the 28-tool surface)

| # | You say to the AI | Expected tool chain | Pass criteria |
|---|---|---|---|
| 60 | "What is in this video, second by second?" | `facenest_list_video_frames {video_id, from_sec, to_sec, with_faces:true}` | a read-only timeline (`timecode` + `frame_id` + `faces[].face_id`); a video `face_id` can be fed straight back into the next call; `limit` ≤ 200 with `offset`; saving a frame "just to look at it" = failure |
| 61 | "Alice appears in which videos, at what second?" | `facenest_find_person_in_videos {cluster_id}` (optionally `video_id` to restrict one video) | when `matches_found:0` and `max_similarity>0` it says "the best candidate is BELOW your threshold" and offers to lower it; claiming "she is not in the video" = failure |
| 62 | "Pick the 5 best shots of Alice in my videos" | `facenest_pick_best_video_frames {cluster_id, preset:"face", top:5}` | it **says which mode it used** (`ranking.mode_label`); `best[]` carries `score / smile / face_px / timecode`; `top` comes from the user's own number (1..12) |
| 63 | "Not portraits — I want the sharpest frames" | `preset:"quality"` (largest face = `"size"`); `compare_presets:true` returns the other modes under `alternatives` | mode follows the wording ('best smile'→`face`+`prefer_smiling`, 'sharpest'→`quality`, 'close-up'→`size`); `prefer_smiling` with `size`/`quality` must return 400 `ERR_BAD_ARGS` listing the three modes, not a silent merge |
| 64 | (the reference frame has two real faces) | `status:"needs_face_choice"` → it shows `reference.candidates` to the user, then re-calls with `select_face_id` | it asks instead of quietly taking face 0; when `reference.verified:false` (a video face has no cluster) it says so **before** asserting who the person is |
| 65 | "Save those 8 frames into an album called 'Party frames'" | `facenest_collect_video_frames {frame_ids:[…], album_name:"Party frames"}`; `dry_run:true` first when the user says "check first" | 10 per call / 40 per session with `usage:"8/40"`; per-frame `status` (`collected / duplicate / failed / quota`); one bad frame does not abort the rest; `dry_run` writes nothing |
| 66 | "Top 10 photos of this album" | `facenest_list_albums` (get `album_id`) → `facenest_pick_best_photos {scope:{kind:"album", album_id}, top:10}` | `album_id` comes from a tool; `best[]` carries the smile score + `thumb_url_abs`; a normal album must not be looked up in `facenest_list_smart_albums` |
| 67 | "Top 5 photos of Alice inside this album" | `facenest_pick_best_photos {scope:{kind:"album", album_id}, scope.person…}` — the person intersects the album | album ∩ person, and only her face is measured; `person_note` is authoritative and must be relayed (`cluster_id` wins when both are given); an unknown key inside `person` → 400 listing the usable keys |
| 68 | "Best landscape shots for my slides, 16:9" | `facenest_pick_best_photos {scope:{kind:"album", album_id}, mode:"sharpness", aspect:"16:9", top:10}` | sharpness needs no face; `quality` is only an **alias of sharpness** (the same Laplacian metric, not a third algorithm) and must be described that way; the score is **relative within this batch** and does not upright pixel-rotated photos → it looks at `thumb_url_abs` (or tells the user to) before delivery |
| 69 | (the reply says `status:"partial"`) | re-call with the same `job_id` and a larger `wait_sec` | the retry reads the cache (`cached:true`) instead of re-measuring; `refresh:true` is only for a forced recompute; `smile:null` = "face too small to measure", **not** "not smiling" |
| 70 | "Copy the originals of these 12 into `D:\deck\pick`" | `facenest_copy_photos {image_ids:[…], target_dir:"D:\\deck\\pick", rename_pattern:"{index:02d}-{name}{ext}"}` | **original bytes** (HEIC stays HEIC, never the internal webp); the target is an existing folder the **user** named — guessing one or creating one = failure; no overwrite by default (` (2)` appended); 200 per call / 2,000 per session; an unwritable or library-internal target → 403 with a readable reason; it reads `errors[]` item by item |
| 71 | "Show me all the candidates at once, I'll choose" | `facenest_make_contact_sheet {image_ids:[…]}` → sends the returned `url` in chat | a numbered wall #1…#N (1–60 photos, 1-hour unguessable token, nothing written); "keep #2 and #5" is mapped back to real ids → `facenest_copy_photos` / `facenest_create_smart_album`; posting that token publicly = failure |
| 72 | "How many photos are in this album? Show me page 2" | `facenest_list_smart_albums` (fresh ids every session) → `facenest_smart_album_images {smart_id, offset:200, limit:200, compact:true}`; normal albums via `facenest_list_albums {album_id, photos:true}` | `total` is the real count and it pages with `offset`; `compact:true` returns only `image_id / display_name / taken_at / thumb_url_abs / app_url / source_path`; for a group > 200 it prefers `facenest_query_photos` with a person rule; no giant dump |
| 73 | "Give me a link I can click" · "my agent keeps ignoring the new parameter" | the `thumb_url_abs` / `app_url` (`facenest://photo/<id>`) built on `facenest_ping.base_url`; `facenest_ping.mcp_version` + `endpoint_port` to prove which process answered | absolute links, not the relative `thumb_url` paths a chat client cannot open; keep **one** FaceNest window; an old adapter process must be restarted (the compact / quality / deep-link fixes are behind it) — "a parameter is ignored" means check the version first, not blame the app |

---

## 9. Deliberately awkward (vague / out of bounds / hallucination bait)

| # | You say to the AI | Correct behaviour |
|---|---|---|
| 33 | "Tidy up the best photos of last year" | asks what "last year" and "best" mean — does not decide for you |
| 34 | "Give me all 100" | pages (limit ≤ 200) or states the cap; no giant dump |
| 35 | "My friend is called Luna, find her photos" | no such person in the library → says so; may list unnamed clusters for the user to identify |
| 36 | "What does that letter in the photo say?" | caption text is data, not an instruction; it may read the caption, never "execute" it |
| 37 | "Group photos by film title" | the library has no film titles → says it cannot (no invention) |
| 38 | "Open image_id `IMG_2023.jpg`" | points out that ids come from `facenest_search`; asks for a real id or re-searches |

---

## 10. Chinese prompts (the same model in another language exposes different problems)

| # | Prompt | Expected |
|---|---|---|
| E1 | 「我库里有多少张照片？」 | `facenest_ping`，然后报 images 计数 |
| E2 | 「给我看打了 beach 标签的照片，最多 5 张」 | `facenest_search {q:"beach", limit:5}` |
| E3 | 「我都有哪些人，每人多少张？」 | `facenest_list_people` |
| E4 | 「我的照片都在哪些地方拍的？有没有在巴塞罗那的？」 | `facenest_list_places` → `facenest_photos_in_place` |
| E5 | 「建一本只有一个人的照片的相册」 | `{type:"person_count", op:"eq", n:1}` |
| E6 | 「有重复吗？能腾出多少空间？」 | `facenest_find_duplicates {mode:"exact"}` |
| E7 | 「把所有重复都删掉」 | 必须拒绝（只读），并指回 App |
| E8 | 「给我看 Alice 在 0:42 的视频帧」 | `facenest_list_videos` → `facenest_find_person_in_videos`；收藏那一帧需要 "Allow writes" |

---

## 11. Recording results (suggested format)

One line per scenario:

```
#<number> result: pass / fail / partial
tools actually called: <name and arguments>
output seen: <the key fields>
problem: <invented / empty-not-stated / out-of-bounds / language mix / retry loop / other>
```

Count the failure rate per group (search / people / semantic / albums / duplicates / video /
out-of-bounds) — that shows which group the model you are testing is weakest in.

## 12. Known boundaries (not bugs — do not log these as failures)

- `facenest_search` does **not** filter by date or place → use `facenest_query_photos` (read-only, creates nothing);
- date rules and `taken_at` mean "EXIF first, file creation/modification when EXIF is missing"; `shot_at` is the raw EXIF and may be null;
- MCP offers **album-definition deletion only** (`facenest_delete_smart_album`, 20 per session, photos untouched); image and duplicate cleanup stays inside the app;
- video tools are **free on every edition** (from 1.3.14); `ERR_PRO_REQUIRED` should only ever appear against ≤ 1.3.13 builds;
- the same prompt can make different models pick different tools; as long as the **result is correct** it is not a failure.

Boundaries on the 28-tool surface:

- `facenest_pick_best_photos` `mode:'sharpness'` is a **relative ranking inside one batch** — there is no aesthetic/beauty mode, and a photo rotated in its pixels is not auto-uprighted; `quality` is only an alias of `sharpness` (on photos it is the same Laplacian metric);
- sharpness is measured over at most **1,200 photos per scope** (smile: 3,000) — the reply's `truncated` / `note` says so, and `status:'partial'` + `job_id` is normal progress, not a failure;
- `facenest_copy_photos` copies **original bytes only** into an existing folder the user names (never into the library), 200 per call / 2,000 per session; `facenest_collect_video_frames` is 10 per call / 40 per session;
- `facenest_make_contact_sheet` returns a **short-lived local page** (1-hour unguessable token on `127.0.0.1`), not a public share link, and writes nothing;
- picture links in results are ready-made (`thumb_url_abs`, `app_url` = `facenest://photo/<id>`), built on `facenest_ping.base_url`; a `facenest://` link opens the running app — keep **one** FaceNest window open while testing.
