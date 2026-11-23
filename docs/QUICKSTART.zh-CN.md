# 快速上手

装适配器 → 证明它连得上 App → 接进客户端。
安装与客户端配置**只在这一页维护**；README 只留摘要并链到这里，避免同一份指令在两处各写一遍。

## 你需要什么

- **本机有 FaceNest 且在运行**，MCP 开关打开。免费版就够（图库张数与语义搜索次数的上限，
  以 [README 中文版](../README.zh-CN.md) 和官网的说法为准）。[下载](https://facenest.net/download)。
- **Python 3.9 或更新**（适配器没有第三方依赖）。
- App 生成的 **endpoint 文件**：`mcp_endpoint.json`。在 App 里：
  设置 → AI agent(MCP) → 打开「开放 MCP 服务」，把显示的 endpoint 文件路径复制出来。

## 安装

```bash
# 方案 A - 从 PyPI 装（推荐）
python -m pip install facenest-mcp
facenest-mcp --selftest

# 方案 B - 不装，一行命令直接跑（uv/uvx 从 PyPI 拉下来就跑）
uvx facenest-mcp --selftest

# 方案 C - 从 GitHub 跑（不想用 PyPI，或要改适配器代码）
uvx --from git+https://github.com/eclgo/facenest-mcp facenest-mcp --selftest
git clone https://github.com/eclgo/facenest-mcp.git
cd facenest-mcp
python -m pip install -e .
facenest-mcp --selftest
```

自检成功会打印一行，形如：

```
OK  http://127.0.0.1:<port>  api=1  images=1234  write_allowed=false
```

看到 `OK` 就是通了。**端口由 App 运行时决定**，`1992` 只是某些配置文件里的示例——以自检输出为准。
其他结果（退出码 1 / 2 / 3）见[排错](TROUBLESHOOTING.md)。

> 🔒 `mcp_endpoint.json` 里是明文令牌，等同密码；它已在 `.gitignore` 里，**绝对不要提交**。

## 不启动客户端也能验

```bash
facenest-mcp --selftest        # 通不通 + App 版本 + 写入状态
facenest-mcp --list-tools      # 适配器对外发布的工具 schema
facenest-mcp --agent-prompt    # 给 agent 的系统提示，可直接粘贴
facenest-mcp --call facenest_ping                 # 直接调一个工具
facenest-mcp --call facenest_search --arg q=beach --arg mode=text
```

`facenest_ping` 会回答 App 版本、看到多少张照片、写入是否允许——这是区分「适配器没问题」和
「App 没开」最快的办法。

## 接入客户端

任何支持 **stdio MCP** 的客户端都能用。要写的只有两样：命令 `python -m facenest_mcp`，
参数 `--endpoint <绝对路径>`。

**Claude Desktop** — `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "facenest": {
      "command": "python",
      "args": ["-m", "facenest_mcp", "--endpoint",
               "C:\\Users\\you\\AppData\\Roaming\\FaceNest\\mcp_endpoint.json"]
    }
  }
}
```

**Cursor** — `~/.cursor/mcp.json`（或项目内 `.cursor/mcp.json`）

```json
{
  "mcpServers": {
    "facenest": {
      "command": "python",
      "args": ["-m", "facenest_mcp", "--endpoint", "C:\\path\\to\\mcp_endpoint.json"]
    }
  }
}
```

**OpenCode** — `opencode.json`

```json
{
  "mcp": {
    "facenest": {
      "type": "local",
      "command": ["python", "-m", "facenest_mcp", "--endpoint", "C:\\path\\to\\mcp_endpoint.json"],
      "enabled": true
    }
  }
}
```

**Codex CLI** — `~/.codex/config.toml`

```toml
[mcp_servers.facenest]
command = "python"
args = ["-m", "facenest_mcp", "--endpoint", "C:\\path\\to\\mcp_endpoint.json"]
```

**DSH / 其他客户端** —— 把上面任一段里的 `command` / `args` 照抄到该客户端的 MCP 配置里。

> Windows 的 JSON / TOML 路径都要写成 `\\`。
> 请优先写**绝对路径**的 `--endpoint`：自动查找依赖进程的工作目录，在 GUI 客户端里不可靠。
> 也可以用环境变量 `FACENEST_ENDPOINT`。

## App 里的两个开关

| 开关 | 作用 |
|---|---|
| 开放 MCP 服务 | 决定适配器能不能连。关掉时所有调用回 `ERR_MCP_NOT_READY`。 |
| 允许写入 | 决定写工具能不能改东西。关掉时写工具回 `ERR_MCP_WRITE_OFF`。 |

两个开关互相独立。读工具永远不写，跟第二个开关无关。
每个工具是读还是写，看 [docs/TOOLS.md](TOOLS.md)：它由工具 schema 生成，那里的标注不会和代码对不上。

## 接下来

- 能问什么、每一步走哪条工具链：[README 中文版](../README.zh-CN.md)
  （[English](../README.md)）。
- 所有参数与额度一页可查：[docs/TOOLS.md](TOOLS.md)。
- 写 agent / 做整合：[docs/AGENT_GUIDE.md](AGENT_GUIDE.md)。
- 出问题了：[TROUBLESHOOTING.md](TROUBLESHOOTING.md)。
