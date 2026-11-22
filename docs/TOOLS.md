# Tool reference

<!-- Generated file. Do not edit by hand: run `python scripts/gen_tools_doc.py`.
     The gate tests/test_docs.py::test_tools_md_equals_the_generated_doc compares this
     file against the live tool schema, so a stale page fails the suite. -->

> Generated from the live tool schema by `scripts/gen_tools_doc.py`.
> 28 tools: 22 read, 6 write. A write tool needs the app's separate **Allow writes**
> switch - the two switches in the app are independent, and read tools never write.
> Parameters marked *required* are the ones the tool refuses to run without.
> Limits (per-call / per-session quotas, size caps) are quoted from each tool's own
> description, so this page cannot advertise a number the app does not enforce.

| Group | Tools |
|---|---|
| [Start](#start) | 1 |
| [Find photos](#find-photos) | 5 |
| [People and faces](#people-and-faces) | 4 |
| [Albums](#albums) | 6 |
| [Places and duplicates](#places-and-duplicates) | 3 |
| [Video](#video) | 6 |
| [Picking and delivery](#picking-and-delivery) | 3 |

## Start

### `facenest_ping` · read

- Parameters: none
- Description: Call this FIRST in every session. Returns {ok, api_version, images, write_allowed, mcp_version, base_url}. `base_url` is the live origin (http://127.0.0.1:<port>); photo results also carry ready-made `thumb_url_abs` links. If mcp_version is older than the app expects, restart the MCP process. `ms` on every JSON response is the adapter↔app round trip (RPC included), not pure compute. If ok is not true (or the call fails), stop and tell the user that FaceNest is not running or the MCP service is off — do not call other tools.

## Find photos

### `facenest_search` · read

- Parameters: `q`*, `mode`, `limit`, `compact`
- Required: `q`
- Description: Search the library by tag / caption / file name. mode: 'all' (default) | 'tag' | 'text' (captions + file names). Returns {query, mode, count, images:[{image_id, file_name, display_name, thumb_url, thumb_url_abs, taken_at, date_source, shot_at, file_mtime, file_ctime, uploaded_at, camera, camera_make, camera_model, lens, favorite, source_path}]}. `display_name` is the original file name (use it in UI text); `thumb_url` is a local path, `thumb_url_abs` is the clickable URL — use the absolute one. `lens` is cleaned of absurd EXIF focal values (lens rules still match the raw string by tokens). image_id is the ONLY valid input for the other tools — never invent ids. limit max 200. Every image also has `app_url` (`facenest://photo/<id>`). compact:true returns only image_id/display_name/taken_at/thumb_url_abs/app_url/source_path (no file_name/camera/lens). This tool has no offset: when hits exceed 200, use facenest_query_photos (it pages). This tool has NO date/place/people filters: for those (or any combination) use facenest_query_photos, which is read-only and saves nothing. For tag vocabulary use facenest_list_tags (auto tags are often Chinese; matching ignores case). Dates: taken_at = the date the app shows (EXIF first, else file ctime/mtime, else upload); date_source = 'exif'|'ctime'|'mtime'|'upload'; shot_at = RAW EXIF only and may be null; file_mtime = the file's modified time.

### `facenest_query_photos` · read

- Parameters: `rules`*, `match_mode`, `sort`, `sort_dir`, `group_by`, `limit`, `offset`, `explain`, `compact`
- Required: `rules`
- Description: READ-ONLY rule query — the same rule engine as a smart album, but NOTHING is saved (no album is created, no 'Allow writes' needed). Use it for every filtered search: a date range, a place, camera/lens, origin, a person, how many people, a tag, caption text, or a pinned id set — and combine rules with match_mode 'all' (AND) / 'any' (OR). Rule shapes (exactly the set the album UI offers): {type:'album', op:'is'|'is_not', album_id:int}; {type:'folder', op:'is'|'is_not'|'under', value:str} (value is the LEAF folder name in original_folder, e.g. '171109', not an absolute/UNC path; under = prefix); {type:'person', op:'is'|'is_not', cluster_id:int} — an unknown cluster_id is rejected with ERR_SMART_PERSON_NOT_FOUND; {type:'tag', op:'has'|'not_has', name:str, source:'any'|'auto'|'manual'} — matching ignores case; call facenest_list_tags first to get real names (auto tags are often Chinese in `name`, e.g. 狗 / Dog); {type:'date', op:'between'|'on'|'before'|'after'|'this_year'|'this_month'|'last_days', from:'YYYY-MM-DD', to:'YYYY-MM-DD', days:1..3650, sources:['exif'|'ctime'|'mtime'|'upload'] (optional: restrict which date source counts); {type:'place', op:'is'|'is_not', country/admin1/city} — is_not only matches photos that DO have GPS (no location ≠ 'not in Girona'); {type:'photos', op:'in', ids:[…]} to keep a previous result set (e.g. semantic hits) — unknown ids are rejected with ERR_SMART_PHOTOS_UNKNOWN, never silently dropped; {type:'person_count', op:'eq'|'lte'|'gte', n:0..50} — eq/lte 0 means 'no faces at all'; {type:'favorite', op:'is'|'is_not'} — the user's favorite flag; {type:'camera'|'lens', op:'is', value:str} — camera accepts model alone ('iPhone 12 Pro'), make+model ('Apple iPhone 12 Pro') OR just the make ('Apple'), case-insensitive; lens matches by tokens, so 'OnePlus Ace 3' finds 'OnePlus Ace 3 back camera 2147483647mm f/1.8'; {type:'origin', op:'is', value:'photo'|'video_frame'}; {type:'caption', op:'has'|'not_has', text:str, lang:'en'|'zh' (optional)}. Date rules use taken_at (EXIF first, else file time — the date the Dates page shows); add `sources:['exif']` when the user means 'actually shot in', not 'dated'. Returns {match_mode, rules, total, images:[{image_id, display_name, thumb_url, thumb_url_abs, taken_at, date_source, shot_at, file_mtime, camera, camera_make, camera_model, lens, …}], groups, group_by, limit, offset, rule_counts, zero_rules, prefix_counts, empty_at}. rule_counts (per-rule counts) and prefix_counts (running AND/OR count) are included automatically when total is 0 — empty_at is the rule index that first drove the intersection to zero, so read them instead of bisecting; pass explain:true to always get them. 1–30 rules; limit max 200; use offset to page; sort 'taken_at'|'uploaded'|'name'; group_by 'none'|'year'|'month'|'place'. Nothing is deleted, moved or created. Every image also has `app_url` (`facenest://photo/<id>`). compact:true returns only image_id/display_name/taken_at/thumb_url_abs/app_url/source_path.

### `facenest_semantic_search` · read

- Parameters: `text`*, `limit`, `compact`
- Required: `text`
- Description: Semantic (natural-language) search: 'photos with a dog on a beach'. Needs the semantic model downloaded and consumes one free-tier query (Pro: unlimited). Returns {text, count, images:[{image_id, similarity, display_name, thumb_url_abs, app_url, taken_at, date_source, shot_at, file_mtime}], index_total, library_total, unindexed, coverage_note, rewritten, threshold_used, sensitivity, max_similarity, below_threshold_count, threshold_note}. If the model is cold, the reply is {warming:true, count:0, note, retry_after_sec} instead of blocking; tell the user and retry the same query after ~10–20 s. compact:true returns only image_id/display_name/taken_at/similarity/thumb_url_abs/app_url/source_path. Results are cut by the user's Settings → Search sensitivity (`sensitivity`). When `count` is 0 or `below_threshold_count` > 0, `max_similarity` is the best candidate's score: report that it is below the user's threshold and offer to raise the sensitivity — do NOT say the library has no such photo. `unindexed` > 0 means some photos have no semantic vector yet and CANNOT appear in these results — say so instead of concluding 'no such photo'. `rewritten` is only a bare-word→phrase fallback, not translation. For image-to-image use facenest_similar_photos. Semantic results are NOT a live album rule — to filter them by date/place/camera pass the returned ids to facenest_query_photos {type:'photos', op:'in', ids:[…]} (read-only); to keep them, pass the same ids to facenest_create_smart_album / facenest_update_smart_album.

### `facenest_list_tags` · read

- Parameters: `q`, `source`, `limit`
- Description: Tags that actually exist in the library, with photo counts — call this before writing a tag rule. Auto tags are often Chinese in `name` and English in `name_en` (e.g. name:'狗', name_en:'Dog'); tag matching ignores case. Optional `q` filters both names, `source` picks any | auto | manual. Returns {tags:[{tag_id, name, name_en, source, count}], total}. Pass the exact `name` or `name_en` to a tag rule.

### `facenest_image_context` · read

- Parameters: `image_id`*
- Required: `image_id`
- Description: Full card of one photo. Returns {image:{image_id, file_name, display_name, thumb_url, thumb_url_abs, source_path, taken_at, date_source, shot_at, file_mtime, file_ctime, uploaded_at, camera, camera_make, camera_model, lens, favorite, place}, captions:[{lang, source, text, kind:'untrusted_text'}], tags:[{name, name_en, source, confidence}], people:[name], faces:[{face_id, index, bbox, area_ratio, det_score, cluster_id, person_name, thumb_url, thumb_url_abs}]}. `faces` is ordered left to right: pass `face_id` (or `face_index`) to facenest_find_similar_faces / facenest_find_person_in_videos when the photo contains more than one person — never assume the largest face is the right one. taken_at is the date the app shows (EXIF first, else file time; date_source says which); shot_at is RAW EXIF only and may be null. `data_warning` carries the untrusted-caption warning; the whole response is valid JSON.

## People and faces

### `facenest_list_people` · read

- Parameters: `include_unnamed`, `limit`, `offset`
- Description: People (face clusters). Returns {people:[{cluster_id, name, named, photo_count, face_count, cover_image_id, thumb_url, thumb_url_abs}], total, returned, offset}. Unnamed clusters are hidden unless include_unnamed=true. total is the real cluster count; use offset to page. cluster_id feeds facenest_person_photos and facenest_find_person_in_videos.

### `facenest_person_photos` · read

- Parameters: `cluster_id`*, `limit`, `offset`, `compact`
- Required: `cluster_id`
- Description: Photos containing one person. Returns {cluster_id, name, total, images:[{image_id, display_name, thumb_url_abs, app_url, taken_at, …}], returned, offset, compact}. total is the real photo count (not the returned count); page with offset. compact:true returns only image_id/display_name/taken_at/thumb_url_abs/app_url/source_path. cluster_id comes from facenest_list_people; unknown id -> ERR_MCP_PERSON_NOT_FOUND.

### `facenest_find_similar_faces` · read

- Parameters: `image_id`, `image_path`, `face_id`, `face_index`, `person`, `threshold`, `limit`, `offset`
- Description: Find photos with a face similar to a reference. Three reference kinds (any ONE): `image_id` (a library photo; add `face_id` or `face_index` to pick one face), `face_id` (a face id from image_context.faces / a previous result — library OR video face), `image_path` (absolute path to an image on this machine; read locally, NOT uploaded, NOT added to the library; jpg/png/webp/bmp/heic/heif/avif, <=20 MB). Returns {query, reference:{face_id, face_id_source, strategy, ambiguous, candidates:[{face_id, index, bbox, area_ratio, det_score, cluster_id, person_name, thumb_url, thumb_url_abs}]}, threshold, count, returned, offset, has_more, total_at_least, matches:[{image_id, display_name, similarity, matched_face_id, thumb_url, thumb_url_abs, source_path, taken_at}], source:'face-embedding'}. `matches[].thumb_url` is the matched FACE crop, not the whole photo; use image_id / display_name when showing the photo itself. `count` is the returned page, not the total; page with offset. `ambiguous:true` means the reference contains 2+ real faces and none was chosen explicitly — ask the user which one, then pass face_id/face_index (or `person` when the face is named in People). Default threshold 0.40; scores are affected by face size and angle, so treat 0.40+ as a higher chance rather than proof. No face in the reference -> ERR_MCP_NO_FACE.

### `facenest_similar_photos` · read

- Parameters: `image_id`, `image_path`, `limit`
- Description: Image-to-image semantic search — 'find photos that look like this picture'. Reference is either `image_id` (a library photo) or `image_path` (absolute path to a local image; read in place, NOT uploaded, NOT added to the library; jpg/png/webp/bmp/heic/heif/avif, <=20 MB). Unlike facenest_find_similar_faces (faces only) this compares the WHOLE picture's meaning/style, so it works for cities, bridges, objects and scenes. Needs the semantic model and consumes one semantic query (Pro: unlimited). Returns {query, count, images:[{image_id, similarity, display_name, thumb_url, thumb_url_abs, file_name, taken_at, date_source, shot_at, file_mtime, lens}], index_total, library_total, unindexed, coverage_note, threshold_used}. `display_name` is the original file name (use it in UI text) and `thumb_url_abs` can be shown directly. `unindexed` > 0 means some photos cannot appear in these results yet. Pass the ids to facenest_query_photos {type:'photos', op:'in', ids:[…]} to filter them further, or to facenest_create_smart_album to keep them.

## Albums

### `facenest_list_albums` · read

- Parameters: `limit`, `offset`, `album_id`, `photos`
- Description: Normal albums (the ones under Albums, including albums created by facenest_collect_video_frames). Returns {albums:[{album_id, name, desc, created_at, photo_count, kind:'normal'}], total, returned, offset}. total is the real album count; page with offset. This is NOT smart albums — use facenest_list_smart_albums for those. album_id / name feed facenest_pick_best_photos scope {kind:'album'}. With {album_id, photos:true} it returns {album_id, name, total, returned, offset, has_more, image_ids} — id-only pages (max 200/call) for enumerating a normal album.

### `facenest_list_smart_albums` · read

- Parameters: none
- Description: Saved smart albums (rule sets, evaluated live). Returns {albums:[{smart_id, name, photo_count, match_mode, duplicate_name, same_name_ids}], max_rules:30}. New/renamed albums must have a unique name (a collision is rejected with ERR_SMART_NAME_DUP); legacy duplicates created before 2026-10-25 may still be listed — always address an album by smart_id. smart_id is NOT stable across sessions: albums can be deleted or re-created, so re-list every session and never reuse an id from an earlier turn. Smart albums never delete or move photos.

### `facenest_smart_album_images` · read

- Parameters: `smart_id`*, `limit`, `offset`, `compact`
- Required: `smart_id`
- Description: Photos currently inside one smart album. Returns {smart_id, total, returned, offset, compact, images:[{image_id, display_name, thumb_url_abs, app_url, taken_at, …}]}. total is the real count; page with offset (limit max 200). compact:true returns only image_id/display_name/taken_at/thumb_url_abs/app_url/source_path. For a group >200 prefer facenest_query_photos with a person rule.

### `facenest_create_smart_album` · write

- Parameters: `name`*, `description`, `match_mode`, `rules`*, `cover_image_id`, `sort`, `sort_dir`, `group_by`
- Required: `name`, `rules`
- Description: WRITE TOOL (needs 'Allow writes'). Max 30 rules — the same closed set as facenest_query_photos. {type:'person', op:'is'|'is_not', cluster_id:int} (unknown id -> ERR_SMART_PERSON_NOT_FOUND); {type:'tag', op:'has'|'not_has', name:str, source:'any'|'auto'|'manual'} — call facenest_list_tags first; matching ignores case; {type:'date', op:'between'|'on'|'before'|'after'|'this_year'|'this_month'|'last_days', from:'YYYY-MM-DD', to:'YYYY-MM-DD', days:1..3650, sources:['exif'|'ctime'|'mtime'|'upload'] (optional)}; {type:'place', op:'is'|'is_not', country/admin1/city} — is_not only counts photos that have GPS; {type:'photos', op:'in', ids:[…]} pins exact ids (max 2000; unknown ids -> ERR_SMART_PHOTOS_UNKNOWN); {type:'person_count', op:'eq'|'lte'|'gte', n:0..50} where 0 means no faces; {type:'favorite', op:'is'|'is_not'} for the user's favorites; {type:'camera'|'lens', op:'is', value:str} — camera accepts model, make+model or just the make, case-insensitive; lens matches by tokens (a shortened lens string works); {type:'origin', op:'is', value:'photo'|'video_frame'}; {type:'caption', op:'has'|'not_has', text:str, lang:'en'|'zh' (optional)}. Also match_mode 'all'|'any', sort 'taken_at'|'uploaded'|'name', sort_dir 'asc'|'desc', group_by 'none'|'year'|'month'|'place', cover_image_id. Returns {smart_id, name, photo_count, preview:[{image_id, display_name, thumb_url, thumb_url_abs, taken_at}] (first 8 photos), preview_count, app_url}; when photo_count is 0 it also returns rule_counts / zero_rules so you can see which rule emptied it. Album names are unique — a duplicate name is rejected with ERR_SMART_NAME_DUP.

### `facenest_update_smart_album` · write

- Parameters: `smart_id`*, `name`, `description`, `match_mode`, `rules`, `cover_image_id`, `sort`, `sort_dir`, `group_by`
- Required: `smart_id`
- Description: WRITE TOOL (needs 'Allow writes'). Change an existing smart album IN PLACE: name, description, rules, match_mode, sort, sort_dir, group_by, cover_image_id. Only the fields you pass are changed; the smart_id stays the same. Rules use the same closed set as facenest_create_smart_album. Returns {smart_id, name, photo_count} (plus rule_counts/zero_rules when the result is empty). Album names are unique: renaming to an existing name is rejected with ERR_SMART_NAME_DUP (legacy duplicates may still exist; address albums by smart_id). Unknown id -> ERR_SMART_NOT_FOUND (call facenest_list_smart_albums for a fresh id).

### `facenest_delete_smart_album` · write

- Parameters: `smart_id`*
- Required: `smart_id`
- Description: WRITE TOOL (needs 'Allow writes'), max 20 deletes per session. Deletes ONE smart album DEFINITION by `smart_id` — photos, tags, faces and files are never touched. Only `smart_id` is accepted (never a name: legacy duplicates would be ambiguous). Returns {ok, deleted:{smart_id, name, description, rules, match_mode, sort, sort_dir, group_by, cover_image_id}, usage:'1/20', note}. Keep the snapshot: passing it back to facenest_create_smart_album restores the album. Unknown id -> ERR_SMART_NOT_FOUND. Use this to discard an album you just created with wrong rules instead of renaming it (a rename keeps the name occupied and a new album with that name is rejected).

## Places and duplicates

### `facenest_list_places` · read

- Parameters: none
- Description: Geographic tree of the library: country -> state/province -> city, with photo counts. Only photos carrying GPS data appear (usually phone photos with location on). Returns {total, countries:[{name, count, admins:[{name, count, cities:[{name, count}]}]}]}. Pass the names to facenest_photos_in_place to fetch the photos of a node.

### `facenest_photos_in_place` · read

- Parameters: `country`, `admin1`, `city`, `limit`, `offset`
- Description: Photos of one place node (exact match). Pass at least one of country / admin1 / city — names come from facenest_list_places (e.g. country:'Spain', admin1:'Catalonia', city:'Girona'). Returns {total, images:[{image_id, display_name, source_path, thumb_url, thumb_url_abs, taken_at, date_source, shot_at, width, height}]}. limit max 1000; use offset to page.

### `facenest_find_duplicates` · read

- Parameters: `mode`, `threshold`, `time_window`, `pixel_verify`
- Description: Find duplicate / look-alike photos. mode:'exact' (default) groups photos whose perceptual hash is IDENTICAL (zero false positives — this is what import-time dedup already blocks). mode:'similar' adds burst look-alikes: hash distance <= threshold (default 12), shot within time_window seconds (default 10), plus a 32x32 pixel check so different photos of the same scene are not grouped. Returns {groups:[{reason, count, members:[{image_id, file_size, source_path}]}], group_count, image_count, reclaimable_bytes}. READ-ONLY: nothing is deleted and no original file is touched — the user decides what to remove inside the app.

## Video

### `facenest_list_videos` · read

- Parameters: `limit`
- Description: Videos in the library and how many of their frames are face-indexed. Returns {videos:[{video_id, name, duration_sec, faces_indexed}], total}. Only frames indexed in FaceNest are searchable.

### `facenest_list_video_frames` · read

- Parameters: `video_id`*, `from_sec`, `to_sec`, `limit`, `offset`, `with_faces`
- Required: `video_id`
- Description: Timeline of one video's extracted frames — browse before picking, with no writes. Use it when the user asks what is at a timecode, or when you need a face id from the video without saving a frame. Returns {video_id, name, duration_sec, interval_sec, total_frames, offset, limit, returned, frames:[{frame_id, frame_index, timestamp_sec, timecode, frame_path, frame_url, frame_url_abs, faces:[{face_id, index, bbox, area_ratio, det_score, cluster_id, person_name}]}]}. `frame_id` is the file name and is accepted by facenest_pick_best_video_frames / facenest_collect_video_frames. limit max 200; use offset to page.

### `facenest_find_person_in_videos` · read

- Parameters: `cluster_id`, `face_id`, `video_id`, `threshold`, `limit`, `order`
- Description: Which videos a person appears in, and at what second. Give ONE of: cluster_id (from facenest_list_people), face_id (a library face OR a video face returned by this tool / facenest_image_context.faces), or a still of the person. Optional `video_id` limits the search to one video. Returns {person:{cluster_id, reference_face, reference_source, video_id}, threshold, total_faces, max_similarity, below_threshold_count, order, match_state, total_matches, no_comparable_faces, matches_found, frames:[{video_id, video_name, frame_id, face_id, timestamp_sec, timecode, similarity, bbox, det_score, frame_path, frame_url}]}. `face_id` in a frame can be fed straight back as `face_id` (no need to save the frame first). Results use the same same-person-across-frames grouping as the video page. `max_similarity` is the best score even when it is below `threshold`; if `matches_found` is 0 and `max_similarity` > 0, say the best candidate is BELOW the user's threshold (ask to lower it) — never claim the person does not appear. Time accuracy = ± one frame interval (default 2 s).

### `facenest_pick_best_video_frames` · read

- Parameters: `cluster_id`, `face_id`, `image_id`, `image_path`, `frame_id`, `select_face_id`, `person`, `face_index`, `position`, `frame_ids`, `video_id`, `threshold`, `preset`, `prefer_smiling`, `min_face_px`, `top`, `min_gap_sec`, `compare_presets`, `explain`
- Description: Pick the best N frames of a person in ONE call (read-only, no collection). Give ONE reference: cluster_id, face_id (library OR video face), image_id, image_path, frame_id, or frame_ids to rank an explicit set. Modes match the video page: preset='face' (portrait: frontality + sharpness), 'size' (largest face), 'quality' (sharpest whole frame). Use prefer_smiling=true only with preset='face' — wording guide: 'best smile' -> face+smile; 'best portrait' -> face; 'biggest face/close-up' -> size; 'sharpest/cleanest' -> quality; a vague 'best photos' -> face and SAY which mode you used. `top` comes from the user's number (1..12). Returns {status:'ok'|'needs_face_choice', reference:{face_id, face_id_source, strategy, ambiguous, candidates:[…]}, ranking:{preset, prefer_smiling, mode_label, order, weights, note}, best:[{rank, frame_id, face_id, video_id, video_name, timestamp_sec, timecode, similarity, score, smile, smile_bucket, face_px, face_ratio, bbox, det, marks, frame_path, frame_url, frame_url_abs}], alternatives:{size:[…], quality:[…]}, person_match:{max_similarity, threshold, below_threshold_count}, scored, candidates}. `reference.verified` is false when the face was picked geometrically (a video face has no cluster) — say so before asserting who it is. status='needs_face_choice' means the reference has 2+ real faces: show candidates to the user, then call again with select_face_id. Adjacent frames closer than min_gap_sec are never both picked. A 400 with ERR_BAD_ARGS lists the three modes when preset/prefer_smiling contradict each other.

### `facenest_collect_video_frame` · write

- Parameters: `video_id`*, `timestamp_sec`*
- Required: `video_id`, `timestamp_sec`
- Description: WRITE. Saves the frame at timestamp_sec as a new photo. `timestamp_sec` must be within 0..duration_sec (from facenest_list_videos); an out-of-range value is rejected with ERR_MCP_TIMESTAMP_RANGE (the text includes the real duration) — it is never silently clamped. Checks run in this order: write permission (403 ERR_MCP_WRITE_OFF) -> timestamp range (400) -> session limit 40 (429 ERR_MCP_SESSION_LIMIT). Returns {ok, requested_sec, duration_sec, usage:'1/40', collected, deduplicated, image_ids}. The saved photo goes through the normal pipeline (dedup / quota / tagging) and shows up in People later.

### `facenest_collect_video_frames` · write

- Parameters: `frame_ids`, `items`, `album_name`, `dry_run`
- Description: WRITE. Save up to 10 video frames in ONE call (40 frames per session, counted per frame). Pass `frame_ids` (from list/pick results — no re-encoding) or `items:[{video_id, timestamp_sec}]` for an exact moment. dry_run=true reports what would happen without writing. Returns {ok, dry_run, requested, collected, deduplicated, failed, limited, usage:'n/40', items:[{frame_id, video_id, timestamp_sec, ok, status:'collected|duplicate|failed|quota|would_collect', image_id, error}], image_ids, album_id, album_name, folder, tag_job_id}. One bad frame never aborts the batch; the free edition's 500-photo budget still applies.

## Picking and delivery

### `facenest_pick_best_photos` · read

- Parameters: `scope`*, `top`, `wait_sec`, `min_face_px`, `mode`, `aspect`, `job_id`, `refresh`
- Required: `scope`
- Description: Pick the Top-N photos from ONE scope (read-only; nothing is written to the library). mode:'smile' (default) ranks faces by measured smile; mode:'sharpness' ranks whole-image sharpness and needs NO face — use it for landscape / food / architecture / PPT material. Smile mode: optional `scope.person` (cluster_id, exact person_name, or object {cluster_id|person_name|name}) intersects ANY scope with that person and measures only their face, e.g. an album ∩ one person. cluster_id wins if both are given (person_note says so); unknown keys inside person return 400. scope.kind: album / folder / person / favorites / tag / date / smart_album / image_ids; for semantic results, call facenest_semantic_search first and pass its ids as image_ids (the picker does not run the semantic model). Sharpness mode is measured exactly like the album UI's 'Sort by sharpness' (Laplacian variance, longest edge 800 px); it rejects scope.person and accepts `aspect` ('any'|'16:9'|'4:3'|'3:2'|'1:1'|'9:16'|'4:5', ±8% of width/height) to filter PPT-friendly framing before scoring. Sharpness is only a RELATIVE ranking within this batch and does NOT detect a photo that is rotated 90° in its pixels; photos without EXIF Orientation cannot be auto-uprighted. Before delivery, inspect the returned thumb_url_abs visually (or tell the user to). There is NO aesthetic mode — beauty is subjective and has no reliable local score. `quality` is accepted as an ALIAS for sharpness (it is the video picker's word); on photos it is exactly the same Laplacian metric, NOT a third algorithm. `top` 1..20; `wait_sec` 0..60 bounds one call; sharpness is capped at 1,200 photos per scope (smile at 3,000) and the reply's `truncated`/`note` says so. Returns {status:'done'|'partial', mode, best:[{image_id, display_name, smile|sharpness, smile_bucket?, face_id?, face_px?, thumb_url, thumb_url_abs, source_path, taken_at, width, height, aspect_ratio, source}], total, total_scope, measured_cap, truncated, scored, pending, cached, computed, empty_reason, job_id, eta_sec, note}. If status is 'partial', call again with the same job_id (and a larger wait_sec) to finish; the work is cached, so a second call over the same scope is a read (see `cached`). smile=null means 'not measurable' (face smaller than 64 px), not 'not smiling'. refresh=true ignores the cache and recomputes (sharpness cache too).

### `facenest_make_contact_sheet` · read

- Parameters: `image_ids`*, `title`
- Required: `image_ids`
- Description: Build a READ-ONLY HTML contact sheet (thumbnail wall) for 1–60 photos and Returns {url, count, expires_in, hint}. Send `url` in chat: the user sees every candidate at once, numbered #1…#N, and answers 'keep #2 and #5'. Then use those ids with facenest_copy_photos / facenest_create_smart_album. The URL is a short-lived (1 hour) unguessable token — no MCP token needed in the browser; do not post it publicly. Nothing is written, moved or created.

### `facenest_copy_photos` · write

- Parameters: `image_ids`*, `target_dir`*, `rename_pattern`, `overwrite`
- Required: `image_ids`, `target_dir`
- Description: Copy the ORIGINAL bytes of selected photos into a folder the user names — the step after picking photos for a deck/video project. Requires 'Allow writes'. The target must be an EXISTING absolute folder outside the FaceNest library and program directories (ask the user for it; do not guess or create folders). Up to 200 photos per call and 2,000 per session. Existing files are kept and a new name gets ' (2)' unless overwrite=true. rename_pattern is optional and uses {name} {ext} {id} {index} {date}; {ext} INCLUDES the leading dot ('.jpg'), so both '{name}{ext}' and '{name}.{ext}' work (example: '{index:02d}-{name}{ext}' -> '01-city.jpg'). A name with no image extension gets the original one appended. Default keeps the original name. Original files are copied byte-for-byte: HEIC stays HEIC, never the internal webp. Returns {ok, target_dir, requested, copied, failed, total_bytes, items:[{image_id, display_name, target_path, bytes, overwrote}], errors, usage}. A single failed file does not abort the rest — read errors.
