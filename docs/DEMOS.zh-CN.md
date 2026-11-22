# FaceNest MCP · 应用场景演示

> 五个应用场景例子：一句人话进去，agent 在**本机真实照片库**上干活，**全程不上传云端**。
> 下面的数字取决于你自己的库，不是跑分。
>
> 编号场景测试脚本在 [TESTING.zh-CN.md](TESTING.zh-CN.md)。
> 英文版：[DEMOS.md](DEMOS.md)。
> 版本：2026-11-21（28 工具；5 个应用例子）。

---

## 1. 五个应用场景例子

| # | 你对 AI 说的那句话 | agent 实际做了什么 | 产出物 / 关键边界 |
|---|---|---|---|
| S1 | 「找出小雨在我所有视频里出现的片段，把笑得最好的 3 帧收藏成照片」 | `facenest_list_videos` → `facenest_list_people` → `facenest_find_person_in_videos {cluster_id}` → `facenest_pick_best_video_frames {cluster_id, video_id?, preset:"face", prefer_smiling:true, top:3}` → `facenest_collect_video_frames {frame_ids}` | 3 张新照片；**批量 10 帧/次、40 帧/会话（按帧计数）**；单帧工具 `facenest_collect_video_frame` 同为 **40 次/会话**（会话预算相同，批量另有一次 ≤10 帧的限制）；时间点误差约 ±1 个取帧间隔 |
| S2 | 「从素材库找适合当『秋季新品』封面的大图，横构图，给我编号预览，我选完再放进 `D:\Deck\assets`」 | `facenest_semantic_search` 或 `facenest_query_photos` → `facenest_pick_best_photos {scope:{kind:"image_ids", image_ids:[…]}, mode:"sharpness", aspect:"16:9"}` → `facenest_make_contact_sheet {image_ids}` → 用户回「留 #2、#7」→ `facenest_copy_photos {target_dir, rename_pattern}` | 原图字节复制到用户指定文件夹（HEIC 仍是 HEIC）；≤200 张/次、2000 张/会话；目标文件夹必须已存在。编号预览墙 1–60 张、URL 1 小时 |
| S3 | 「从『2025 冲绳』这本相册里挑 10 张笑容最好的，建成『冲绳精选』」 | `facenest_list_albums` → `facenest_pick_best_photos {scope:{kind:"album", album_id}, mode:"smile", top:10}` → `facenest_create_smart_album {name:"冲绳精选", rules:[{type:"photos",op:"in",ids}]}` | 一本 10 张的智能相册；脸小于 64px 回 `smile:null`（不是「没笑」）；规则最多 30 条 |
| S4 | 「在人物里找阿明的单人正面照，挑 5 张最清晰的，复制到 `D:\ComfyUI\input\refs`」 | `facenest_list_people` → `facenest_person_photos` → `facenest_pick_best_photos {scope:{kind:"image_ids", image_ids}, mode:"sharpness", top:5}` → `facenest_make_contact_sheet` → `facenest_copy_photos` | `refs` 文件夹里是原图。**sharpness 模式不接受 `scope.person`**，必须先用 `person_photos` 取 ids 再按 `image_ids` 挑 |
| S5 | 「把这个文件夹里 AI 生成的图分成『有人物』和『其他』两本相册」 | 两次 `facenest_query_photos`：`{rules:[{type:"person_count",op:"gte",n:1}]}` → `facenest_create_smart_album {name:"有人物", rules:[…]}`；`{rules:[{type:"person_count",op:"eq",n:0}]}` → `facenest_create_smart_album {name:"其他", rules:[…]}` | 两本智能相册。`origin` 只有 `photo` / `video_frame`，**没有「AI 生成」这个值**；AI 图通常没有 EXIF，但 `taken_at` 会回退到文件时间，日期规则照样有效 |

S1–S5 与 `README.zh-CN.md` 的「五个真能用的场景」一一对应。

以上应用例子都能在免费版跑；免费版是图库 500 张、语义搜索 200 次，Pro 解除语义次数限制。官网：[facenest.net](https://facenest.net)。

---
