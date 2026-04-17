# Fishgoo Ads OS MCP

这个目录承载 Fishgoo 广告审计与项目记忆系统的第一版独立服务。

## 第一版范围

- 只读 Google Ads 日审
- 广告变更历史查询
- 项目记忆层投影
- HTTP bridge
- 远程 MCP server 入口

## 运行前提

1. 当前仓库完整存在
2. `FISHGOO_广告成长档案/` 已经是最新
3. 本机或远程环境可访问 Google Ads 认证材料

## 本地安装

注意：

- 官方 Python MCP SDK 建议使用较新的 Python 版本。
- 当前这台机器的系统 Python 是 `3.9.6`，可用于大部分骨架开发与测试，但不建议作为正式远程运行时。
- 正式远程环境请使用 `Python 3.11+`。

```bash
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/fishgoo_mcp/requirements.txt
```

## 主要命令

生成项目记忆：

```bash
/usr/bin/python3 -m apps.fishgoo_mcp.memory.builder
```

启动 HTTP bridge：

```bash
/usr/bin/python3 apps/fishgoo_mcp/bridge/app.py
```

启动 MCP server：

```bash
/usr/bin/python3 apps/fishgoo_mcp/server.py
```
