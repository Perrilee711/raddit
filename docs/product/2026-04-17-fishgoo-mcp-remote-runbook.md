# Fishgoo Ads OS MCP Remote Runbook

日期：2026-04-17

---

## 1. 目标

把 `apps/fishgoo_mcp/` 部署到远程 Ubuntu 服务器，作为可被 Claude 或其他客户端接入的远程广告审计与项目记忆服务。

第一版目标：

- 提供远程 HTTP bridge
- 提供远程 MCP server
- 保持 Google Ads 严格只读
- 读取本仓库的 `FISHGOO_广告成长档案/` 与 `memory/`

---

## 2. 服务器要求

- Ubuntu 22.04 或更新版本
- Python 3.11+
- Git
- 可访问 GitHub
- 可安全保存 Google Ads 相关环境变量

推荐：

- `2 vCPU / 4GB RAM`
- 独立域名或二级域名
- `nginx` 做反向代理

说明：

- 当前开发机的系统 Python 是 `3.9.6`。
- 这足够完成骨架开发、memory 生成和 bridge smoke test，但不应作为正式 MCP 运行时基线。
- 远程生产环境统一按 `Python 3.11+` 准备。

---

## 3. 代码部署

```bash
git clone https://github.com/Perrilee711/raddit.git
cd raddit
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/fishgoo_mcp/requirements.txt
```

---

## 4. 必填环境变量

```bash
export FISHGOO_MCP_HOST=0.0.0.0
export FISHGOO_MCP_PORT=8766
export FISHGOO_MCP_HTTP_PORT=8767
export FISHGOO_GOOGLE_ADS_CUSTOMER_ID=1573113113
export FISHGOO_PYTHON_BIN=/usr/bin/python3
export FISHGOO_ADS_VENDOR_PATH=/path/to/ads_vendor_if_needed
export FISHGOO_MCP_AUTH_TOKEN=replace_me
```

Google Ads 相关认证变量建议由服务器安全配置注入，不写死在仓库里。

---

## 5. 首次初始化

生成项目记忆投影：

```bash
source .venv/bin/activate
python -m apps.fishgoo_mcp.memory.builder
```

本地验证：

```bash
python -m unittest discover -s apps/fishgoo_mcp/tests -v
python -m py_compile apps/fishgoo_mcp/server.py apps/fishgoo_mcp/bridge/app.py
```

---

## 6. 启动方式

### 启动 HTTP bridge

```bash
source .venv/bin/activate
python apps/fishgoo_mcp/bridge/app.py
```

默认地址：

- `http://0.0.0.0:8767/health`
- `http://0.0.0.0:8767/memory/current-truth`
- `http://0.0.0.0:8767/tools/ads-daily-audit?date=2026-04-17`

### 启动 MCP server

```bash
source .venv/bin/activate
python apps/fishgoo_mcp/server.py
```

如果 `mcp` SDK 已正确安装，服务会按该 SDK 默认传输层运行。

---

## 7. 反向代理建议

建议用 `nginx` 暴露两个入口：

- `mcp.fishgoo.com`
- `mcp-api.fishgoo.com`

其中：

- `mcp.fishgoo.com` 指向 MCP server
- `mcp-api.fishgoo.com` 指向 HTTP bridge

---

## 8. Claude 接入目标

最终接入逻辑：

1. Claude 连接远程 Fishgoo MCP
2. 先读取：
   - `project://overview`
   - `project://current-truth`
   - `project://audit-timeline`
3. 再调用工具：
   - `ads_daily_audit`
   - `ads_change_history`

这意味着 Claude 继承的不是原始聊天窗口，而是结构化项目记忆。

---

## 9. 安全要求

- 不暴露任何 Google Ads 写操作
- 不把原始密钥写入仓库
- 对外网入口增加 token 或反代层鉴权
- 限制写入目录，只允许：
  - `memory/`
  - `FISHGOO_广告成长档案/`
  - `fishgoo-ad-board.html`

---

## 10. 当前状态

截至本 runbook 编写时，已完成：

- `apps/fishgoo_mcp/` 独立代码骨架
- 只读 Google Ads 工具 wrapper
- `memory/` 项目记忆投影生成器
- HTTP bridge
- MCP server 入口
- 本地 smoke tests

下一步重点：

1. 安装并验证 MCP SDK 实际运行
2. 增加文档更新工具
3. 增加看板刷新工具
4. 部署到远程 Ubuntu 并做 Claude 接入验证
