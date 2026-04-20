# Claude × Fishgoo Ads OS MCP 接入手册

日期：2026-04-20
适用对象：任何一个要用 Claude 接入 Fishgoo 广告审计系统的人（Perri 自己、合作方、新的 Claude 会话）

---

## 1. 30 秒填表

| 字段 | 值 |
| --- | --- |
| Remote MCP URL | `https://mcp.perrilee.com/fishgoo-mcp` |
| Auth | `Authorization: Bearer <找 Perri 要 token>` |
| Bridge Health（公开） | `https://mcp.perrilee.com/fishgoo-bridge/health` |
| Bridge Memory（需 token） | `https://mcp.perrilee.com/fishgoo-bridge/memory/overview` |
| Ad Board（需 Basic Auth） | `https://mcp.perrilee.com/ad-board/` |

---

## 2. Claude 里怎么加

1. 打开 Claude → Settings → Connectors → **Add Custom Remote MCP**
2. URL 填：`https://mcp.perrilee.com/fishgoo-mcp`
3. 鉴权选 **Bearer**，粘 token（不要带引号、不要带多余空格）
4. 保存 → Claude 会自动握手，看到连接器变绿即成功

> 浏览器直接打开 MCP URL 会看到 `406 Not Acceptable`，**这是正常的**。MCP 协议要求客户端带特定 header，浏览器不会带。只要 Claude 里显示已连接就行。

---

## 3. 接上之后的第一句话（直接复制）

```
请先读取 Fishgoo Ads OS 的 project://overview、project://current-truth、project://audit-timeline，
然后继续今天的广告审计，并给出下一步建议。
```

这一句话会让 Claude 把"结构化项目记忆"读进去，而不是重新解释整个账户。读完之后它就能直接接手最近一天的审计结论（比如 Day26 的"早盘未启动"判断）。

---

## 4. Claude 能干什么

**资源（只读项目记忆）：**

- `project://overview` — 项目总览
- `project://current-truth` — 当前真相快照（最新审计结论）
- `project://audit-timeline` — 每日审计时间线

**工具（只读 Google Ads）：**

- `ads_daily_audit(date, customer_id?)` — 某一天的账户快照
- `ads_change_history(from_datetime, to_datetime, customer_id?)` — 某时间窗内的账户改动记录

**不做的事：**

- 不写 Google Ads（任何 mutate/update 都不支持）
- 不动账户设置
- 只输出分析 + 建议，执行还是人工

---

## 5. 常见现象速查

| 现象 | 判断 |
| --- | --- |
| `curl https://mcp.perrilee.com/fishgoo-mcp` 返 `406` | **正常**，协议握手等 header，不是坏了 |
| `curl https://mcp.perrilee.com/fishgoo-bridge/health` 返 `{"ok": true}` | 服务活着 |
| 任意 bridge 路径不带 token → `401 missing_bearer` | 鉴权在工作，说明放 token 位置对了 |
| 任意路径带错 token → `401 invalid_token` | token 过期或填错，找 Perri 要最新的 |
| Claude 里连上后资源列表为空 | bridge 活着但 MCP server 可能挂了，看下一节 |

---

## 6. Token 管理

- **存放位置**：远程服务器 `/root/raddit/.env.fishgoo-mcp` 里的 `FISHGOO_MCP_AUTH_TOKEN`
- **生成**：`openssl rand -hex 32`
- **轮换步骤**：
  1. `ssh root@<server>`
  2. 改 `/root/raddit/.env.fishgoo-mcp` 里的 `FISHGOO_MCP_AUTH_TOKEN`
  3. `sudo systemctl restart fishgoo-mcp fishgoo-mcp-bridge`
  4. 通知所有 Claude 客户端重填新 token
- **轮换触发条件**：token 疑似泄露、接入方离场、每 90 天例行轮换

---

## 7. 出问题就按这个顺序查

```bash
# 1) bridge 是否活着
curl https://mcp.perrilee.com/fishgoo-bridge/health
# 期望：{"ok": true, "service": "fishgoo-mcp-bridge"}

# 2) 鉴权是否生效
curl -i https://mcp.perrilee.com/fishgoo-bridge/memory/overview
# 期望：HTTP/1.1 401 + {"ok": false, "message": "missing_bearer"}

# 3) 带正确 token 能读到记忆
curl -s -H "Authorization: Bearer $TOKEN" \
     https://mcp.perrilee.com/fishgoo-bridge/memory/overview | head -30
# 期望：JSON 数据

# 4) 以上都通但 Claude 还是连不上
ssh root@<server>
sudo journalctl -u fishgoo-mcp -n 100
sudo journalctl -u fishgoo-mcp-bridge -n 100
```

**典型误区**：

- Claude 客户端有时会把 Bearer 后面多带一个空格 → 401。删了空格重存。
- token 粘贴时被自动转成了"智能引号" → 401。重新从明文复制。
- 服务器 systemd 重启后环境变量没重新加载 → `sudo systemctl daemon-reload && sudo systemctl restart fishgoo-mcp fishgoo-mcp-bridge`。

---

## 8. 相关文档

- [Fishgoo Ads OS MCP Remote Runbook](./2026-04-17-fishgoo-mcp-remote-runbook.md) — 部署/运维细节
- [Day26 反馈](../../FISHGOO_广告成长档案/03_后续观测计划/Day26反馈_2026-04-20.md) — 最近一次审计结论
- [apps/fishgoo_mcp/README](../../apps/fishgoo_mcp/README.md) — 代码目录说明
