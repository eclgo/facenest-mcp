# 架构

一页讲清：适配器是什么、它碰什么、哪份文档管哪件事。
2026-11-21 按代码核对；凡涉及数字，本页指向**执行它的文件**，不把数字抄一遍。

## 形状

```
AI 客户端（Claude Desktop / Cursor / OpenCode / Codex / DSH …）
        │  MCP over stdio（tools/list、tools/call）
        ▼
facenest-mcp 适配器  —  Python，只用标准库
        │  HTTP 到 127.0.0.1（令牌取自 mcp_endpoint.json）
        ▼
FaceNest App  —  图库、模型、数据库、额度都在这儿
```

数据不出本机。适配器除了访问运行中 App 的 loopback 地址之外，不发起任何网络请求；App 也只监听 loopback。

## 各部分做什么

| 部分 | 文件 | 职责 |
|---|---|---|
| MCP 服务 + 工具注册表 | `facenest_mcp/server.py` | 在 stdio 上说 MCP 协议；持有 `TOOLS`（工具名、参数、说明）与 `AGENT_PROMPT`（系统提示）；实现 CLI（`--selftest`、`--list-tools`、`--agent-prompt`、`--call`） |
| App API 客户端 | `facenest_mcp/api.py` | 调用 App 的本地 HTTP 端点、解析 endpoint；**每次调用都重新读 endpoint 文件**，App 重启后端口/令牌变化会被自动跟上 |
| Endpoint 解析 | `facenest_mcp/endpoint.py` | 找 `mcp_endpoint.json`（先 `--endpoint`，再环境变量 `FACENEST_ENDPOINT` / `FACENEST_DATA_DIR` / `FACE_DATA_DIR`，再常见位置） |
| 错误目录 | `facenest_mcp/errors.py` | 每个 `ERR_…` 码的含义、下一步做什么、要不要重试 |
| App 侧（不在本仓库） | FaceNest 应用里的内嵌副本 | 适配器随 App 一起发布；FaceNest 侧有同步与校验脚本保证它与本仓库一致。会话额度与两个权限开关都由 App 强制执行 |

## 每个数字只有一个来源

参数与额度**只写在 `server.py` 的工具说明里**，凡是从它派生的东西都是生成的、有闸门的：

| 页面 | 由谁生成 | 闸门 |
|---|---|---|
| `docs/_generated/_tools.txt`（紧凑清单） | `scripts/_dump_tools.py` | 文件内容 == `render(TOOLS)` |
| [TOOLS.md](TOOLS.md)（参数、必填项、读写、额度） | `scripts/gen_tools_doc.py` | 文件内容 == `render(TOOLS)`；分组表必须正好覆盖代码公开的那些工具 |
| README 的工具表、工具数/场景数/错误码数 | 手写，**由闸门清点** | `tests/test_docs.py` 把每个被声称的数字与 `len(TOOLS)`、`len(errors.HINTS)` 以及 [TESTING.md](TESTING.md) 的编号行数相比较 |
| 两份指南里的系统提示 | 从 `AGENT_PROMPT` 拷贝 | 两份指南必须逐字包含它 |
| 指南的目录块 | `scripts/gen_doc_toc.py` | 条目 == 该文件自己的 `## ` 小节标题 |

手写进散文页的数字，就是唯一会漂的那个数字。所以额度待在工具说明里，散文页链到 [TOOLS.md](TOOLS.md)，不重复一遍。

## 读写与两个开关

- App 里有两个互相独立的开关：**开放 MCP 服务**（能不能连）与**允许写入**（写工具能不能改东西）。读工具永远不写。
- 哪些工具是写工具，由它们自己的说明文字派生（`server.py`）；派生出的集合与 App 侧的写入闸门一致（`App/app/api/routes_mcp.py` 里的 `_guard(..., require_write=True)`）。标注显示在 [TOOLS.md](TOOLS.md)。
- 每次调用 / 每个会话的额度由 App 执行，计数出现在工具返回里（`usage: "n/cap"`）。

## 文档分工：哪页管哪件事

| 页面 | 管什么 |
|---|---|
| `README.md` / `README.zh-CN.md` | 是什么、能问什么、给人看的工具表、退出码速查 |
| [QUICKSTART.md](QUICKSTART.md) | 安装、客户端配置、验证命令 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 现象 → 含义 → 怎么办、多参考时的取用顺序 |
| [TOOLS.md](TOOLS.md) | 参数、必填项、读写标注、逐工具额度（生成物） |
| [AGENT_GUIDE.md](AGENT_GUIDE.md)（+ 中文版） | agent 必须遵守的规则：规则形状、返回字段、错误处置、系统提示 |
| [DEMOS.md](DEMOS.md)（+ 中文版） | 应用场景演示 |
| [TESTING.md](TESTING.md)（+ 中文版） | 编号场景脚本（73 行） |
| [CHANGELOG.md](../CHANGELOG.md) | 改了什么，逐条带 commit 号 |

同一件事只在一页写一次，其他页给链接。

## 测试与 CI

```bash
python -m unittest discover -s tests     # 协议 / 错误文字 / 文档闸门，不需要 App 在跑
python tests/e2e_stdio.py <mcp_endpoint.json>   # 端到端，跑的是夹具，不是你的图库
```

文档闸门（`tests/test_docs.py`）的存在理由是：文档是模型唯一的「世界知识」，
所以「文档里必须列出每个工具、每个错误码、数字必须对得上」是一条可执行的断言，不是靠自觉。
CI（[`.github/workflows/test.yml`](../.github/workflows/test.yml)）在每次 push 时于
Python 3.9 / 3.12 / 3.13 上跑同一套测试，且不上传任何 artifact。

## 开源的是什么

本仓库里的这个适配器。App —— 图库、模型、数据库 —— 保持闭源，它是适配器通过 loopback 对话的对象。
