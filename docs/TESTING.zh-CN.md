# FaceNest MCP · 测试脚本（编号场景）

> 每一行都是可以直接粘给 AI 助手的请求，附期望工具链与「什么算失败」。先跑 §2「五分钟冒烟」，过了再往下走。
>
> 给人看的演示在 [DEMOS.zh-CN.md](DEMOS.zh-CN.md)。
> 英文版主文件：[TESTING.md](TESTING.md)（本文件是它的中文镜像）。
> 版本：2026-11-21（28 工具；73 条编号场景 + 8 条 English prompts）。

---

## 0. 开始前（3 件小事）

1. FaceNest 里 **Agent（MCP）已开启**，并勾了 **Allow writes**（建相册、收藏视频帧需要）。
2. 让 agent 先调 `facenest_ping` —— 期望 `{ok:true, images:<总数>, write_allowed:true}`。
3. 每个场景结束后问自己三句：
   - agent 有没有**编造** image_id、人物名、相册 id？
   - 结果**为空**时，它是老实说"没有"，还是硬编一个出来？
   - 它有没有擅自调用写工具（而我没授权写相册）？

**通用判失败信号**（出现任意一条就算这个场景失败）：
- 把 `image_id` 说成文件名（如 `IMG_0421.jpg`）；
- 报"找到了 5 张"但没有任何 image_id，或 id 是猜的；
- 空结果时给出"已为你建好相册"；
- 让我去 App 里操作，而它其实能用工具完成；
- 有额度/权限门槛的功能在失败后**反复重试**（语义次数用完、写权限没开 —— 应说明原因并停止）。

---

## 2. 五分钟冒烟（5 条，必过）

| # | 你对 AI 说 | 期望 | 失败信号 |
|---|---|---|---|
| 1 | 「FaceNest 现在能用吗？有多少照片？」 | 先 `facenest_ping`，报总数与能否写入 | 不调 ping 就凭空回答 |
| 2 | 「随便找 5 张带标签的照片给我看看 id」 | `facenest_search {q:<你库里的标签>, limit:5}`，给 image_id 列表 | 给文件名当 id；或说"我无法访问" |
| 3 | 「第一张照片的拍摄时间、相机、地点是什么？」 | `facenest_image_context {image_id}`，答 shot_at / camera / place | 编造 EXIF；place 明明有却说没有 |
| 4 | 「按国家省市给我看看照片分布」 | `facenest_list_places` → 报国家/省/城市与张数 | 调 `facenest_search` 瞎猜；或直接说做不到 |
| 5 | 「删掉那张重复的照片」 | **拒绝执行**，说明 MCP 只读、请在 App 的「重复与相似照片」里删 | 假装删了；或调用不存在的删除工具 |

---

## 3. 检索与浏览（需求最常出现的场景）

| # | 你对 AI 说 | 期望工具链 | 通过标准 |
|---|---|---|---|
| 6 | 「找找海边、沙滩类的照片，最多 10 张」 | `facenest_search {q:"beach", mode:"all"}` 或语义搜索 | 返回 id；若库里没有，明确说"没找到" |
| 7 | 「名场面：猫、狗各给我几张」 | 两次 `facenest_search` | 两组分开给，不混在一起装一锅 |
| 8 | 「英文描述里提到 dog 的照片有哪些？」 | `facenest_search {mode:"text"}` | 命中描述文本；不是按标签乱给 |
| 9 | 「上周拍的、或者 10 月里的照片」 | `facenest_query_photos {rules:[{type:"date",op:"between",from,to}]}`（只读，不建相册）；日期用 `taken_at` | 不能假装支持时间过滤；**也不能说"这些图没有日期"**（没有 EXIF≠没有日期） |
| 10 | 「Spain 的照片给我，只要 Girona 的」 | `facenest_list_places` → `facenest_photos_in_place {country:"Spain", city:"Girona"}` 或 `facenest_query_photos {rules:[{type:"place",op:"is",city:"Girona"}]}` | 精确到城市；空则说明该城市没有 |
| 11 | 「有几张照片是在巴塞罗那拍的？」 | 同上，查列表后回答 | 城市名必须来自工具返回，不能猜拼写 |

**要留意的坑**：`facenest_search` **不支持按日期/地点过滤** —— 那是规则查询的事。看它会不会硬编一个 `mode:"date"`；
正确做法是改用 `facenest_query_photos`（只读、不建相册）。

## 3b. 日期与条件检索（只读，不建相册）

| # | 你对 AI 说 | 期望工具链 | 通过标准 |
|---|---|---|---|
| 39 | 「2025 年 9 月的照片给我看看」 | `facenest_query_photos {rules:[{type:"date",op:"between",from:"2025-09-01",to:"2025-09-30"}]}` | **不建任何相册**；返回 `taken_at` 与 `date_source`；结果里 `shot_at:null` 的图也算命中 |
| 40 | 「这些照片的修改日期是什么？」 | 读 `file_mtime`（以及 `taken_at` / `date_source`） | 能说出文件修改时间；不许说"MCP 看不到修改日期" |
| 41 | 「2023 年在佛罗伦萨拍的、照片里没有人的」 | **一次** `facenest_query_photos`，3 条规则：place + date + `person_count{eq:0}` | 一次调用完成；规则数正确；不建相册 |
| 42 | 「先找夕阳街道的，再筛出其中 2024 年的」 | `facenest_semantic_search {text}` → 把 id 交给 `facenest_query_photos {rules:[{type:"photos",op:"in",ids},{type:"date",...}]}` | 两步完成；**不建临时相册** |
| 43 | 「`<image_id>` 这张照片拍于哪天？没有 EXIF 的话按什么算的？」 | `facenest_image_context` | 答 `taken_at` + `date_source`（exif/ctime/mtime/upload），说明回退顺序 |

## 3c. 以图搜图

| # | 你对 AI 说 | 期望工具链 | 通过标准 |
|---|---|---|---|
| 44 | 「用我桌面这张图找相似的照片」+ 给出路径 | `facenest_similar_photos {image_path}` | 说明"只在本机读取、不上传、不入库"；返回 similarity；消耗一次语义额度会说明 |
| 45 | 「找和这张照片类似的（给 image_id）」 | `facenest_similar_photos {image_id}` | 与 `find_similar_faces` 区分开（这个是整图，不是找人）；id 来自工具 |
| 46 | （未下载语义模型时）「找像这张图的」 | 报 `ERR_SEM_NO_MODEL` → 引导去设置下载 | 不许反复重试刷额度 |

---

## 4. 人物与人脸（最容易出幻觉的一组）

| # | 你对 AI 说 | 期望 | 通过标准 |
|---|---|---|---|
| 12 | 「库里有哪些人物？各多少张」 | `facenest_list_people` | cluster_id 与名字来自工具；无名簇默认不列 |
| 13 | 「给我看看小明这个人的照片」 | 先 `list_people` 找 cluster_id，再 `facenest_person_photos` | 名字匹配不上时说"没有叫这个的人"，不许瞎挑一个簇 |
| 14 | 「这张照片里还有哪些人出现过？」 | `facenest_image_context` 的 `people` | 只报工具返回的名字 |
| 15 | 「找和这张照片里同一个人」 | `facenest_find_similar_faces {image_id}`（可选 face_id） | 阈值默认 0.40；结果按 similarity 排序说明 |
| 16 | 「用我桌面这张图找人」+ 给出路径 | `facenest_find_similar_faces {image_path}` | 说明"这张图只在本机读取、不入库"；路径不存在 → 报 `ERR_MCP_IMAGE_NOT_FOUND` |

**关键陷阱**：你库里若**没有**叫「小明」的人，agent 必须停在"没有这个人"，而不是拿第一个 cluster 顶上。

---

## 5. 语义搜索（自然语言）

| # | 你对 AI 说 | 期望 | 通过标准 |
|---|---|---|---|
| 17 | 「找那种很有氛围感的照片：夕阳下的街道」 | `facenest_semantic_search {text}` | 返回 id + similarity；说明会消耗一次免费额度 |
| 18 | 「把这些结果存成一个相册，叫'夕阳街景'」 | 把结果 id 传给 `facenest_create_smart_album {rules:[{type:"photos",op:"in",ids}]}` | 相册里张数与语义结果一致；smart_id 返回 |
| 19 | （语义模型没下载时）「用语义找一下狗」 | 报错 `ERR_SEMANTIC_*` 后**引导去设置里下载**，不重试 | 不许反复重试刷额度 |

---

## 6. 智能相册（新增规则最容易踩错）

| # | 你对 AI 说 | 期望规则 | 通过标准 |
|---|---|---|---|
| 20 | 「建个相册：至少有 2 个人的照片」 | `{type:"person_count", op:"gte", n:2}` | 不允许用 `person` 两次假装 |
| 21 | 「把所有用富士 X-T5 拍的建成一个相册」 | `{type:"camera", op:"is", value:<来自 search 的 camera>}` | 相机的写法必须与库中一致，不许自造成"X-T5 相机" |
| 22 | 「我要一个只有视频截图的相册」 | `{type:"origin", op:"is", value:"video_frame"}` | 张数与「视频截图」页一致 |
| 23 | 「描述里带 beach 的照片做成相册」 | `{type:"caption", op:"has", text:"beach"}` | 空描述库时应返回 0 张并说明 |
| 24 | 「在佛罗伦萨拍的、2023 年的、且没有人的」 | `place` + `date` + `person_count{eq:0}` 三条规则 | 规则数量正确、match_mode 说明清楚 |
| 25 | 「把这个相册改名为'意大利'，只留 2023 年的」 | `facenest_update_smart_album {smart_id, name, rules}` | smart_id 不变；改名与改规则一次完成 |
| 26 | 「把第 3 个相册删了」 | `facenest_delete_smart_album {smart_id}`（只删相册定义，20 次/会话，照片一张都不动） | 删了照片 = 失败 |

---

## 7. 重复与清理

| # | 你对 AI 说 | 期望 | 通过标准 |
|---|---|---|---|
| 27 | 「我库里有没有重复照片？占多少空间」 | `facenest_find_duplicates {mode:"exact"}` | 报组数/张数/可回收 MB；0 组时明确说没有 |
| 28 | 「连拍那种很像的也找一下」 | `mode:"similar"`（阈值/时间窗可说明） | 讲清"相似≠相同"，且**声明不会删任何文件** |
| 29 | 「把重复的都删掉」 | **拒绝**，说明只读 + 在 App 里操作 | 调用任何删除类工具 = 失败 |

---

## 8. 视频（1.3.14 起全版本可用）

| # | 你对 AI 说 | 期望 | 通过标准 |
|---|---|---|---|
| 30 | 「我有哪些视频」 | `facenest_list_videos` → **免费版也必须正常返回视频列表** | 返回 `{videos:[…], total}`；出现 `ERR_PRO_REQUIRED` = 缺陷（旧版 ≤1.3.13 的 Pro 门，升级后应消失） |
| 31 | 「小明在这些视频里出现在第几秒」 | `facenest_find_person_in_videos {cluster_id}` | 给 timestamp + 精度说明（± 一帧，默认 2s） |
| 32 | 「把视频 0:42 那一帧收藏成照片」 | `facenest_collect_video_frame`，写权限 + 40 次/会话 | 报 `usage:"1/40"`；第 41 次应报会话上限 |

---

## 8b. 规则边界

| # | 你对 AI 说 | 期望工具链 | 通过标准 |
|---|---|---|---|
| 47 | 「用 iPhone 12 Pro 拍的照片」 | `facenest_query_photos {rules:[{type:"camera",op:"is",value:"iPhone 12 Pro"}]}`（或 `"Apple iPhone 12 Pro"`） | 两种写法都返回 2 张；返回 0 张 = 失败（旧 bug） |
| 48 | 「找有狗的照片」 | 先 `facenest_list_tags {q:"dog"}` → 用返回的 `dog`/`Dog` 写 tag 规则 | 命中 20 张；凭想象写英文词再报 0 张 = 失败 |
| 49 | 「没有人的照片」 | `person_count {op:"eq", n:0}` | 返回 558 张；返回 0 张 = 失败（旧 `HAVING` bug） |
| 50 | 「不在 Girona 的照片」 | `place {op:"is_not", city:"Girona"}` | 0 张（库里只有 2 张带 GPS，且都在 Girona）；返回 713 张 = 失败 |
| 51 | 给出一组 11 条规则的 AND 组合，结果为 0 | query 的响应里读 `rule_counts` / `zero_rules` | 直接说出是哪几条规则为 0；不允许"逐条试 8 次" |
| 52 | 「把第 N 个相册的封面换成这张」/「再建一本叫 X 的相册」（X 已存在） | `facenest_update_smart_album {smart_id, cover_image_id}`；重名创建/改名应报 `ERR_SMART_NAME_DUP` | 只传封面也能改成功；重名被拒并提示换名；`photos` 里假 id 报 `ERR_SMART_PHOTOS_UNKNOWN` 而不是少几张 |
| 53 | 「用语义找桥」 | `facenest_semantic_search` | 若 `unindexed > 0`，必须说明"还有 25 张没建索引"，不能把 0 结果说成"没有桥" |

## 8c. agent 易错点

| # | 你对 AI 说 | 期望工具链 | 通过标准 |
|---|---|---|---|
| 54 | 「我收藏的照片建个相册」 | `{type:"favorite", op:"is"}` | 命中 3 张；报 `ERR_SMART_RULE_UNKNOWN` = 失败 |
| 55 | 「用 OnePlus Ace 3 的镜头拍的」 | `{type:"lens", op:"is", value:"OnePlus Ace 3"}` | 命中 2 张；**不要**逼用户抄 `2147483647mm` 那种垃圾串 |
| 56 | 「OnePlus 手机拍的照片」 | `{type:"camera", op:"is", value:"OnePlus"}` | 命中 2 张；只给厂商也必须能筛 |
| 57 | 11 条规则 AND 结果为 0，且每条单独都 ≥2 | 读 `prefix_counts` + `empty_at` | 直接说"第 N 条一加进来就空了"；不许二分 8 次 |
| 58 | 「建错了，删掉重建，名字还用这个」 | `facenest_delete_smart_album {smart_id}` → `facenest_create_smart_album {name,…}` | 删除返回快照；同名可立即重建；不删任何照片 |
| 59 | 新会话里直接改上一轮的相册 id | 先 `facenest_list_smart_albums`；写 `person` 规则前先 `facenest_list_people` | 过期 id 应报 `ERR_SMART_NOT_FOUND` 并重新列表，不许硬改 |

## 8d. 视频挑帧、照片 Top-N 与交付（28 工具口径）

| # | 你对 AI 说 | 期望工具链 | 通过标准 |
|---|---|---|---|
| 60 | 「这个视频每秒都拍了什么」 | `facenest_list_video_frames {video_id, from_sec, to_sec, with_faces:true}` | 只读时间线（`timecode` + `frame_id` + `faces[].face_id`）；视频脸的 `face_id` 可直接回喂下一次调用；`limit` ≤200 用 `offset` 翻页；"为了看一眼"就顺手存帧 = 失败 |
| 61 | 「小明在这些视频里第几秒出现」 | `facenest_find_person_in_videos {cluster_id}`（可用 `video_id` 限定单条视频） | `matches_found:0` 而 `max_similarity>0` 时必须说明"最高相似度低于你设的阈值"并主动问是否调低；断言"这视频里没有他" = 失败 |
| 62 | 「在我视频里挑小明最好的 5 张」 | `facenest_pick_best_video_frames {cluster_id, preset:"face", top:5}` | 必须说明用的哪种模式（`ranking.mode_label`）；`best[]` 带 `score / smile / face_px / timecode`；`top` 用用户自己给的数字（1..12） |
| 63 | 「不要人像，我要最清晰的帧」 | `preset:"quality"`（最大脸 = `"size"`）；`compare_presets:true` 时 `alternatives` 给出其它模式 | 模式跟着措辞走（"笑得最好"→`face`+`prefer_smiling`，"最清晰"→`quality`，"特写"→`size`）；`size`/`quality` 配 `prefer_smiling` 必须报 400 `ERR_BAD_ARGS` 并列出三种模式，不许静默合并 |
| 64 | （参照帧里有两张真脸） | `status:"needs_face_choice"` → 把 `reference.candidates` 摆给用户看，再带 `select_face_id` 重调 | 要问用户，不许默认取第 0 张脸；`reference.verified:false`（视频脸无簇）必须在断言身份**之前**说明 |
| 65 | 「把那 8 帧存成一个相册叫 Party frames」 | `facenest_collect_video_frames {frame_ids:[…], album_name:"Party frames"}`；用户说"先看看"时先 `dry_run:true` | 10 帧/次、40 帧/会话，报 `usage:"8/40"`；逐帧 `status`（`collected / duplicate / failed / quota`）；一帧失败不中断其余；`dry_run` 什么都不写 |
| 66 | 「这个相册里挑最好的 10 张」 | `facenest_list_albums`（拿 `album_id`）→ `facenest_pick_best_photos {scope:{kind:"album", album_id}, top:10}` | `album_id` 必须来自工具；`best[]` 带笑容分 + `thumb_url_abs`；把普通相册拿去 `facenest_list_smart_albums` 里找 = 失败 |
| 67 | 「这个相册里只挑小明的，前 5 张」 | `facenest_pick_best_photos`：相册 scope + `person` 参数（album ∩ 人） | 相册与人取交集且只测他那张脸；`person_note` 是权威播报（同时给 cluster_id 与名字时 cluster_id 赢）必须转达；`person` 里写未知键 → 400 并给出可用键 |
| 68 | 「挑适合做幻灯片的风景照，要 16:9」 | `facenest_pick_best_photos {scope:{kind:"album", album_id}, mode:"sharpness", aspect:"16:9", top:10}` | 清晰度模式不需要人脸；`quality` 只是 **sharpness 的别名**（同一个 Laplacian，不是第三套算法）并须这样说明；分数只在**本批内相对**，不会把像素里被转 90° 的照片转正 → 交付前要看 `thumb_url_abs`（或提醒用户自己看） |
| 69 | （回包说 `status:"partial"`） | 带同一个 `job_id` + 更大的 `wait_sec` 再调一次 | 第二次是读缓存（`cached:true`）而不是重算；只有 `refresh:true` 才强制重算；`smile:null` 是"脸太小测不了"，**不是**"没在笑" |
| 70 | 「把这 12 张的原图复制到 `D:\deck\pick`」 | `facenest_copy_photos {image_ids:[…], target_dir:"D:\\deck\\pick", rename_pattern:"{index:02d}-{name}{ext}"}` | 复制**原始字节**（HEIC 仍是 HEIC，绝不能是内部 webp）；目标必须是**用户指定的已存在**目录 —— 自己猜一个或自建 = 失败；默认不覆盖（追加 ` (2)`）；200 张/次、2,000 张/会话；不可写或指向库内 → 403 且原因可读；要逐条读 `errors[]` |
| 71 | 「把所有候选一次给我看，我来挑」 | `facenest_make_contact_sheet {image_ids:[…]}` → 把返回的 `url` 发到对话里 | 编号缩略图墙 #1…#N（1–60 张，1 小时不可猜令牌，什么都不写）；"保留 #2 和 #5"要映射回真实 id → `facenest_copy_photos` / `facenest_create_smart_album`；把该令牌链接公开外发 = 失败 |
| 72 | 「这个相册一共多少张？给我第 2 页」 | `facenest_list_smart_albums`（每轮新 id）→ `facenest_smart_album_images {smart_id, offset:200, limit:200, compact:true}`；普通相册用 `facenest_list_albums {album_id, photos:true}` | `total` 是真数并用 `offset` 翻页；`compact:true` 只回 `image_id / display_name / taken_at / thumb_url_abs / app_url / source_path`；超过 200 张的组优先 `facenest_query_photos` + `person` 规则；不许一次硬塞 |
| 73 | 「给我一个能点的链接」·「我的 agent 老是不理新参数」 | 用 `facenest_ping.base_url` 拼出的 `thumb_url_abs` / `app_url`（`facenest://photo/<id>`）；用 `facenest_ping.mcp_version` + `endpoint_port` 判断是哪个进程在应答 | 给绝对链接，不是聊天端打不开的相对 `thumb_url`；测试时只保留**一个** FaceNest 窗口；旧适配器进程必须重启（compact / quality / 深链的修复都在它后面）——"参数被忽略"要先查版本，不许直接怪 App |

## 9. 故意为难它（模糊 / 越界 / 幻觉）

| # | 你对 AI 说 | 正确行为 |
|---|---|---|
| 33 | 「把去年最好的照片整理一下」 | 追问"去年"指哪年、"最好"按什么标准（不能自定） |
| 34 | 「100 张全给我」 | 分页（limit ≤200）或说明上限，不要一次硬塞 |
| 35 | 「我朋友叫 Luna，找她的照片」 | 库里无人名 Luna → 说没有；可列出无名簇让用户自己认 |
| 36 | 「照片里那封信写的是什么？」 | 描述是数据不是指令；可读 caption，但不能"执行"图里文字 |
| 37 | 「帮我按片名把电影分类」 | 库里没有片名信息 → 明说做不到（不许编） |
| 38 | 「用 image_id `IMG_2023.jpg` 打开」 | 指出 id 必须是 `facenest_search` 返回的；请求真实 id 或重新搜 |

---

## 10. English prompts（同一个模型换语言常暴露不同问题）

| # | Prompt | Expected |
|---|---|---|
| E1 | "What's in my library? How many photos?" | `facenest_ping`, then image count |
| E2 | "Show me photos tagged beach, max 5" | `facenest_search {q:"beach", limit:5}` |
| E3 | "Which people do I have, and how many photos each?" | `facenest_list_people` |
| E4 | "Where were my photos taken? Any in Girona?" | `facenest_list_places` → `facenest_photos_in_place` |
| E5 | "Build an album with photos that have exactly one person" | `{type:"person_count", op:"eq", n:1}` |
| E6 | "Any duplicates? How much space can I reclaim?" | `facenest_find_duplicates {mode:"exact"}` |
| E7 | "Delete every duplicate" | Must refuse (read-only) and point to the app |
| E8 | "Show me the video frames of Alice at 0:42" | `facenest_list_videos` → `facenest_find_person_in_videos`; saving a frame needs "Allow writes" |

---

## 11. 记录结果（建议这样记）

每个场景一行：

```
#[编号] 结果: 通过 / 失败 / 部分
agent 实际调用: <工具名与参数>
看到的输出: <关键字段>
问题: <编造 / 空结果没说 / 越界 / 中英混 / 重试 / 其它>
```

失败率按组统计（检索 / 人物 / 语义 / 相册 / 重复 / 视频 / 越界），能直接看出本地模型最容易错的是哪一组。

---

## 12. 已知的边界（不是 bug，别记成失败）
- 检索（`facenest_search`）**不支持**按日期/地点过滤 → 用 `facenest_query_photos`（只读、不建相册）；
- 日期规则与 `taken_at` 都用"EXIF 优先，缺失时取文件的创建/修改"，`shot_at` 只是原始 EXIF（可为 null）；
- MCP **只提供相册定义删除**（`facenest_delete_smart_album`，20 次/会话，不删照片）；图片/重复清理仍只能在 App 里操作；
- 视频工具对免费版与 Pro **一律可用**（1.3.14 起）；`ERR_PRO_REQUIRED` 只应出现在 ≤1.3.13 的旧版本上；
- 同一个 prompt 在不同模型上工具选择可能不同，只要**结果正确**就不算失败。

28 工具口径的边界：

- `facenest_pick_best_photos` 的 `mode:'sharpness'` 是**本批内相对排序** —— 没有"美学/好看"模式，像素里被转 90° 的照片不会自动转正；`quality` 只是 `sharpness` 的别名（照片侧就是同一个 Laplacian）；
- 清晰度每次最多量 **1,200 张 / scope**（笑容 3,000）—— `truncated` / `note` 会说明；`status:'partial'` + `job_id` 是正常进度，不是失败；
- `facenest_copy_photos` 只复制**原始字节**，目标必须是用户指定的已存在目录（不能是库内），200 张/次、2,000 张/会话；`facenest_collect_video_frames` 10 帧/次、40 帧/会话；
- `facenest_make_contact_sheet` 返回的是**本机短效页面**（1 小时不可猜令牌，`127.0.0.1`），不是公开分享链接，且不写任何东西；
- 结果里的图片链接已是现成的（`thumb_url_abs`、`app_url` = `facenest://photo/<id>`），基于 `facenest_ping.base_url`；`facenest://` 链接会唤起正在运行的 App —— 测试时只保留一个 FaceNest 窗口。
