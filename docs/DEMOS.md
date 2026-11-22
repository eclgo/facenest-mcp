# FaceNest MCP · application examples

> Five application examples: one sentence of plain language in, an agent doing real work on a
> local library, no cloud upload anywhere. Numbers depend on your own library; nothing here is a
> benchmark claim.
>
> The test script (the numbered scenarios) lives in [TESTING.md](TESTING.md).
> Chinese twin: [DEMOS.zh-CN.md](DEMOS.zh-CN.md).
> Version: 2026-11-21 (28 tools; 5 application examples).

---

## 1. Application examples

| # | The sentence you type | What the agent actually does | What you get / the limits that matter |
|---|---|---|---|
| S1 | "Find every clip where Mia appears in my videos, and save the three best-smiling frames as photos." | `facenest_list_videos` → `facenest_list_people` → `facenest_find_person_in_videos {cluster_id}` → `facenest_pick_best_video_frames {cluster_id, video_id?, preset:"face", prefer_smiling:true, top:3}` → `facenest_collect_video_frames {frame_ids}` | 3 new photos; **10 frames per call, 40 frames per session (counted per frame)**; the single-frame tool `facenest_collect_video_frame` shares the same **40 per session** budget (the batch tool adds a ≤10-per-call cap); timestamps are accurate to ±1 frame interval |
| S2 | "From my asset library, find the large landscape shots that work as an 'Autumn drop' cover, give me a numbered preview, and after I choose, copy them into `D:\Deck\assets`." | `facenest_semantic_search` or `facenest_query_photos` → `facenest_pick_best_photos {scope:{kind:"image_ids", image_ids:[…]}, mode:"sharpness", aspect:"16:9"}` → `facenest_make_contact_sheet {image_ids}` → you reply "keep #2 and #7" → `facenest_copy_photos {target_dir, rename_pattern}` | Original bytes copied into a folder you name (HEIC stays HEIC); ≤200 per call, 2,000 per session; the target folder must already exist. The numbered preview wall takes 1–60 photos and the link lasts 1 hour |
| S3 | "From the '2025 Kyoto' album, pick the ten best smiles and build them into a 'Kyoto picks' album." | `facenest_list_albums` → `facenest_pick_best_photos {scope:{kind:"album", album_id}, mode:"smile", top:10}` → `facenest_create_smart_album {name:"Kyoto picks", rules:[{type:"photos",op:"in",ids}]}` | One smart album of 10 photos; faces smaller than 64 px return `smile:null` (that is not "not smiling"); at most 30 rules |
| S4 | "In the people list, find solo front-facing photos of Alex, pick the 5 sharpest, and copy them to `D:\ComfyUI\input\refs`." | `facenest_list_people` → `facenest_person_photos` → `facenest_pick_best_photos {scope:{kind:"image_ids", image_ids}, mode:"sharpness", top:5}` → `facenest_make_contact_sheet` → `facenest_copy_photos` | `refs` holds the originals. **sharpness mode does not accept `scope.person`** - get the ids with `person_photos` first, then pick by `image_ids` |
| S5 | "Split the AI-generated images in this folder into two albums: 'with people' and 'everything else'." | Two `facenest_query_photos` calls: `{rules:[{type:"person_count",op:"gte",n:1}]}` → `facenest_create_smart_album {name:"with people", rules:[…]}`; `{rules:[{type:"person_count",op:"eq",n:0}]}` → `facenest_create_smart_album {name:"everything else", rules:[…]}` | Two smart albums. `origin` only has `photo` / `video_frame` — **there is no "AI generated" value**; AI images usually carry no EXIF, but `taken_at` falls back to the file time, so date rules still work |

S1–S5 map one to one onto the five scenarios in `README.md`.

All of these run on the free edition; the free tier is 500 photos in the library and 200
semantic queries, and Pro lifts the semantic limit. Website: [facenest.net](https://facenest.net).

---
