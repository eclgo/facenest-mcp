# 排错

App 与适配器能告诉你的事，都收在这页：现象 → 含义 → 怎么办。
额度/体积/数量类数字**不在这里重复**——它们只写在 [docs/TOOLS.md](TOOLS.md)（由工具 schema 生成）。

## `--selftest` 打出来的不是 `OK`

| 退出码 | 含义 | 怎么办 |
|---|---|---|
| **2** | 找不到 endpoint 文件 | 打开 App：设置 → AI agent(MCP)，确认服务是开的；并显式给路径：`facenest-mcp --endpoint <mcp_endpoint.json 的绝对路径>` |
| **3** | 那个端口上没人监听 | App 没开，或 MCP 开关是关的。启动 App / 打开开关 |
| **1** | 连上了，但被拒绝 | 令牌被重置，或写 endpoint 文件之后开关被关掉。在 App 里重新打开 MCP，再跑一次 `--selftest` |

目标是这一行：`OK  http://127.0.0.1:<端口>  api=…  images=…  write_allowed=…`。

## 适配器启动时打印 "not ready yet"

可能看到：

```
[facenest-mcp] not ready yet: …
[facenest-mcp] serving anyway: tools are listed now; every call re-reads …
```

这是设计行为：适配器照常启动、照常发布工具清单，并在**每次调用时重新读 endpoint 文件**。
App 连不上期间调用会失败；App 起来之后，同一个客户端会话就能继续用，不用重启客户端。

## 调用回 `ERR_MCP_NOT_READY`

App 的**「开放 MCP 服务」开关**是关的，或 App 没在运行。打开即可。这跟令牌无关。

## 调用回 `ERR_MCP_WRITE_OFF`

App 的**「允许写入」开关**是关的。它是第二个、独立的开关：开了 MCP 不等于开了写入。
读工具不受影响——读工具永远不写。

## HTTP 401 / 403

`mcp_endpoint.json` 里的令牌已经和 App 不一致（在 App 设置里重置过，或这份文件是旧拷贝）。
在 App 里重新打开 MCP，并把客户端指向当前的 endpoint 文件。

## 终端里能用，客户端里不能用

几乎都是 endpoint 路径问题：

- `--endpoint` 请用**绝对路径**。自动查找依赖进程工作目录，而 GUI 客户端的工作目录不可预期。
- Windows 的 JSON / TOML 里路径要写成 `\\`。
- 环境变量 `FACENEST_ENDPOINT` 也会被读取。
- 客户端必须调用**装了适配器的那个 Python**。在终端跑 `facenest-mcp --selftest` 可以证明适配器这侧是通的；终端通、客户端不通，就是客户端的 `command` 指向了另一个 Python。

## App 重启后端口变了

适配器每次调用都重新读 endpoint 文件，所以新端口/新令牌会自动生效，不用重启客户端。
如果客户端一直显示一条失效连接，重启该客户端里的 MCP 服务条目（它自己的重载/开关），不要重启 App。

## 助手给的是文件名，不是 id

它在编造。所有工具都要 id，不要文件名。让它先跑 `facenest_search`（或 `facenest_query_photos`），
用返回里的 `image_id`。编出来的 id 会被 App 拒绝——这是保护，不是故障。

## 相似脸 / 挑帧同时给了好几个参考

`facenest_find_similar_faces`、`facenest_similar_photos` 和视频挑帧工具只取**一个**参考。
App 的取用顺序是：

`person` > `image_id` > `face_id` > `image_path`

（`face_id` 先查图库，再查视频索引。）返回里的 `reference` 会写明这次实际用的是哪一个；
`reference.ambiguous` 为真表示一张照片里有多张脸、App 自己替你选了一个——这时要把候选脸给用户看，问要用哪张。

## 「建相册失败」/「复制失败」

App 里写入是关的（见上面 `ERR_MCP_WRITE_OFF`）。另外按 [docs/TOOLS.md](TOOLS.md) 里复制工具的规则检查目标目录：目录必须**已经存在**，而且必须在图库之外。

## 相册 / 搜索搜出来是空的

这不是错误。规则默认按 AND 组合，一条不可能的规则就会让结果为空。
返回里带每条规则的计数，并指出是哪条规则把它清空了。一次只放宽一条。
如果计数是 0 而 `max_similarity` 大于 0，说明最佳候选**低于你的灵敏度阈值**——这不等于「没有这种照片」。

## 我需要一个数字（每次/每会话额度、体积、数量）

查 [docs/TOOLS.md](TOOLS.md)。它是从工具 schema 生成的，所以就是 App 真正执行的那个数字；
本页刻意不重复这些数字。

## 出问题、文档也没帮上

提 issue：<https://github.com/eclgo/facenest-mcp/issues>。请附上工具名、返回原文（尤其是 `ERR_…` 那个码），以及 `facenest-mcp --selftest` 的输出。
