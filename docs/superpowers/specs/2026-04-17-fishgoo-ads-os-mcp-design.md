# Fishgoo Ads OS MCP + Project Memory System Design

日期：2026-04-17
作者：Codex
状态：Draft for review

---

## 1. Goal

把当前依赖单一对话窗口和人工串联的 FISHGOO 广告审计工作流，升级成一个可远程访问、可跨模型复用、可长期继承项目背景的系统。

目标不是“把脚本暴露出去”，而是做一个能被 Claude、Gemini 等客户端直接调用的远程 MCP 服务，并让它同时具备：

1. 广告审计能力
2. 项目长期记忆能力
3. 文档与看板更新能力
4. 老板汇报与学习成长输出能力

最终效果应当是：

- 未来即使当前对话中断，或当前模型不可用
- 只要客户端接入 Fishgoo MCP
- 就能读取项目历史、理解当前真相，并继续执行我们的既有工作流

---

## 2. Non-Goals

第一版明确不做以下能力：

1. 不通过 Google Ads API 修改任何广告设置
2. 不做自动调价、自动改预算、自动改素材
3. 不尝试“自动继承聊天平台原始逐字记忆”
4. 不在第一版做复杂多租户 SaaS
5. 不在第一版做完整 BI 仓库重建

第一版是“远程可访问的审计与记忆中枢”，不是自动投放机器人。

---

## 3. Problem Statement

当前系统已经形成了稳定的方法论，但存在 4 个关键风险：

1. **记忆依赖聊天窗口**
   当前很多背景知识存在于对话本身，而不是系统可读的长期资产里。

2. **工具分散**
   Google Ads 日审、变更历史、业务侧报表、成长档案、看板更新分散在脚本和文档中，没有统一协议层。

3. **跨模型不可迁移**
   即使 Claude 或 Gemini 能帮忙，也无法天然继承当前项目上下文。

4. **工作流缺少标准入口**
   现在更像“人知道怎么做”，不是“系统知道怎么做”。

所以第一原则不是做一个“更方便的脚本”，而是做一个“可继承的系统资产”。

---

## 4. Design Principles

### 4.1 记忆优先于对话

我们不追求让其他模型读这个对话框，而是追求让其他模型读到**结构化项目记忆**。

### 4.2 只读优先，安全优先

Google Ads 相关能力继续坚持只读，避免远程 MCP 被误用成自动操盘器。

### 4.3 双出口设计

系统不仅要提供 MCP，还要保留 HTTP bridge，避免未来被某个平台的 MCP 支持状态卡住。

### 4.4 Vercel 只做展示壳

远程 MCP 主体放在云服务器，不放在 Vercel 函数环境里。Vercel 继续只负责静态看板和展示页面。

### 4.5 项目背景作为一等公民

Tools 解决“能做什么”，Memory Resources 解决“为什么这么做”和“当前真相是什么”。

---

## 5. Approaches Considered

### Approach A：只做远程 MCP 工具层

做一个纯工具型 MCP Server，只暴露广告查询、档案读取、看板更新等工具。

优点：

- 开发最快
- 协议最纯
- 易于接入 Claude

缺点：

- 仍然缺少长期记忆层
- 客户端每次都得重新拼接背景
- 很难做到真正“接班式”协作

### Approach B：远程 MCP + 项目记忆系统

做一个完整的远程 MCP Server，同时提供：

- tools
- resources
- prompts
- 一个可持续更新的项目记忆目录

优点：

- 最符合“Claude 无缝接班”的目标
- 长期可维护
- 最能保留方法论和项目真相

缺点：

- 第一版设计复杂度更高

### Approach C：只做 HTTP API，不做 MCP

做 REST 服务，让未来不同模型通过自定义集成使用。

优点：

- 平台兼容面广
- 部署简单

缺点：

- 无法直接利用 MCP 生态
- Claude 接入体验不如原生 MCP
- 需要额外包装提示词和上下文协议

### Recommendation

选择 **Approach B**，但第一阶段实现方式采用“单实例远程服务”。

也就是：

- 对外：按 MCP 标准暴露能力
- 对内：先以单服务部署，避免过早拆分
- 同时保留 HTTP bridge，确保兼容性

---

## 6. Target User Experience

### 6.1 Claude / Gemini 接入后的理想流程

客户端第一次连接 Fishgoo MCP 时，应能：

1. 先读取项目总览资源
2. 再读取当前真相资源
3. 必要时读取最近审计和业务报告索引
4. 最后调用工具执行具体操作

例如：

- “今天的广告审计做一下”
- 模型先读 `current_truth`
- 再调 `ads_daily_audit`
- 再结合 `audit_timeline`
- 最后产出和我们当前风格一致的负责人判断

### 6.2 项目记忆不是聊天记录，而是项目知识库

系统不会保存“原始聊天逐句流水”，而是维护一套结构化记忆：

- 项目背景
- 决策日志
- 审计时间线
- 业务报告索引
- 当前真相
- 学习进度
- 未决问题

这比“原始聊天继承”更稳，也更容易长期维护。

---

## 7. Architecture

### 7.1 High-Level Architecture

```text
Claude / Gemini / Other MCP Clients
                |
                v
     Fishgoo Ads OS MCP Server
                |
      -------------------------
      |           |           |
      v           v           v
   Tool Layer  Memory Layer  HTTP Bridge
      |           |           |
      v           v           v
 Google Ads   Project Docs   External Integrations
 Scripts      / Board        / Uploads / Webhooks
```

### 7.2 Runtime Topology

```text
Remote Ubuntu Server
  - MCP Server (primary)
  - HTTP API bridge
  - File ingest service
  - Scheduler / cron runner
  - Secure credentials

GitHub Repository
  - Source of truth for docs
  - Board source files
  - Memory snapshots

Vercel
  - Static board publishing
  - Read-only presentation layer
```

### 7.3 Why Not Vercel-First

Vercel 不适合作为这套系统的主执行层，因为第一版就需要：

- 访问长期文件系统资产
- 管理 Google Ads 认证
- 执行本地脚本
- 处理文档写入
- 可能触发 git / deploy / ingest 工作流

这些都更适合放在一台稳定的远程服务器上。

---

## 8. Core System Components

### 8.1 MCP Control Server

职责：

- 暴露标准 MCP tools/resources/prompts
- 处理客户端认证
- 编排底层模块调用
- 输出统一结构化结果

建议技术：

- Python FastMCP

理由：

- 当前项目已有 Python 脚本资产
- Google Ads 审计脚本已经是 Python
- 第一版迁移成本最低

### 8.2 Audit Tool Modules

职责：

- 包装现有脚本
- 提供稳定输入输出 schema
- 把脚本结果变成 MCP 友好的 structured content

第一版直接复用：

- [google_ads_daily_audit.py](/Users/perrilee/Desktop/探索/raddit/scripts/google_ads_daily_audit.py)
- [google_ads_change_history.py](/Users/perrilee/Desktop/探索/raddit/scripts/google_ads_change_history.py)

### 8.3 Project Memory Builder

职责：

- 把档案、日报、业务报告、看板结论提炼成结构化 memory
- 生成索引文件和摘要文件
- 提供给 MCP resources 使用

这是第一版最关键的新模块。

### 8.4 Document Update Engine

职责：

- 更新 DayN 学习文档
- 更新业务侧分析文档
- 更新主看板 Markdown / HTML

### 8.5 HTTP Bridge

职责：

- 对外提供 REST 接口
- 为不稳定支持 MCP 的客户端兜底

### 8.6 Deploy Publisher

职责：

- 推送 GitHub
- 触发 Vercel 部署
- 验证线上页面是否已更新

---

## 9. MCP Surface Design

### 9.1 Tools

第一版工具集：

#### `ads_daily_audit`

输入：

- `date`
- `customer_id`（可选）

输出：

- account today
- campaigns today
- yesterday summary
- last 7d summary
- search terms today
- measurement health

#### `ads_change_history`

输入：

- `from_datetime`
- `to_datetime`
- `customer_id`（可选）

输出：

- change events
- operator summary
- likely adjustment categories

#### `memory_overview`

输入：

- `section`（可选）

输出：

- 项目背景摘要
- 当前阶段
- 核心结论

#### `memory_timeline`

输入：

- `date_from`
- `date_to`
- `topic`（可选）

输出：

- 审计时间线
- 关键转折点

#### `biz_report_ingest`

输入：

- `file_path`
- `report_type`

输出：

- 解析摘要
- 核心业务指标
- 可写入看板的结论块

#### `learning_update`

输入：

- `day`
- `date`
- `source_refs`

输出：

- 更新后的学习文档路径
- 关键信息摘要

#### `board_refresh`

输入：

- `sections`
- `publish`（bool）

输出：

- 变更摘要
- 线上链接

#### `boss_brief_generate`

输入：

- `period`
- `compare_mode`

输出：

- 正式汇报摘要
- 谈判版要点

### 9.2 Resources

第一版资源集：

- `project://overview`
- `project://current-truth`
- `project://decision-log`
- `project://audit-timeline`
- `project://business-reports-index`
- `project://learning-progress`
- `project://open-questions`

### 9.3 Prompts

第一版内置 prompt 模板：

- `run-daily-audit`
- `analyze-adjustment-impact`
- `generate-boss-brief`
- `update-learning-plan`
- `review-buyer-performance`

---

## 10. Project Memory Model

### 10.1 Memory Categories

#### `project_overview`

记录：

- FISHGOO 项目定位
- 广告目标
- 业务转化链路
- 关键角色和分工

#### `decision_log`

记录：

- 每次重要判断
- 为什么这么判断
- 结论何时被更新

#### `audit_timeline`

记录：

- Day1-DayN 审计结果
- 阶段变化
- 投手调整与效果对照

#### `business_reports_index`

记录：

- 每个 PDF / Excel / CSV 报表的路径
- 时间范围
- 关键指标
- 与广告侧的关系

#### `current_truth`

记录：

- 当前最新可信状态
- 当前阶段判断
- 当前最重要风险
- 当前建议动作

#### `learning_progress`

记录：

- 当前学习阶段
- 已掌握能力
- 下一步训练重点

#### `open_questions`

记录：

- 还没确认的问题
- 待补的数据口径
- 需要技术或投手进一步解释的问题

### 10.2 Storage Strategy

第一版建议使用 Git 可读的 Markdown + JSON 双格式：

- Markdown：便于人读
- JSON：便于程序和模型稳定读取

建议目录：

```text
memory/
  overview.json
  current_truth.json
  decision_log.jsonl
  audit_timeline.jsonl
  business_reports_index.json
  learning_progress.json
  open_questions.json
```

文档仍保留在现有 `FISHGOO_广告成长档案/` 中，memory 目录是“可机读投影层”。

---

## 11. Security and Permissions

### 11.1 Google Ads

继续坚持只读策略：

- 远程 MCP 不暴露任何写操作
- 所有 Google Ads 工具都标记为 read-only

### 11.2 File Writes

第一版只允许写入：

- `FISHGOO_广告成长档案/`
- `memory/`
- `fishgoo-ad-board.html`

### 11.3 Publish Actions

`board_refresh(publish=true)` 这类能力需要单独权限控制，避免客户端误触发频繁发布。

### 11.4 Secrets

服务器端保存：

- Google Ads 凭证
- GitHub / deploy 凭证
- 可选 Vercel token

不在客户端暴露任何原始密钥。

---

## 12. Error Handling

系统需要优先提供“可操作错误”，不是技术堆栈。

例如：

- Google Ads 凭证失效
  - 返回“Google Ads 认证失效，需要重新授权”
- 业务报表格式不兼容
  - 返回“无法识别该报表口径，请指定 report_type 或补充字段说明”
- 看板发布失败
  - 返回“本地文件已更新，但线上发布未完成”

---

## 13. Testing Strategy

### 13.1 Unit Tests

验证：

- memory builder 解析逻辑
- tool schema
- output formatting

### 13.2 Integration Tests

验证：

- daily audit tool 是否能包装现有脚本
- business ingest 是否能解析真实 PDF / CSV / XLSX
- board refresh 是否能更新目标文件

### 13.3 End-to-End Tests

目标问题示例：

- “做一下今天的广告审计”
- “补一下 Day23 并同步到看板”
- “基于本周业务报告更新负责人判断”
- “输出一版给老板的正式摘要”

---

## 14. MVP Scope

### 14.1 In Scope

第一版必须交付：

1. 远程 MCP Server
2. 只读 Google Ads 审计工具
3. 项目记忆系统
4. 业务报表导入
5. 学习文档更新
6. 看板更新
7. HTTP bridge

### 14.2 Out of Scope

第一版暂不交付：

1. 自动广告修改
2. 多项目多租户
3. 权限后台 UI
4. 自动 BI 数据仓库
5. 完整 Slack / Feishu 通知中心

---

## 15. Proposed File Structure

```text
apps/fishgoo_mcp/
  server.py
  auth.py
  config.py
  schemas.py
  tools/
    ads_daily_audit.py
    ads_change_history.py
    biz_report_ingest.py
    learning_update.py
    board_refresh.py
    boss_brief_generate.py
  resources/
    registry.py
  memory/
    builder.py
    readers.py
    writers.py
  bridge/
    app.py
  tests/
    ...

memory/
  overview.json
  current_truth.json
  decision_log.jsonl
  audit_timeline.jsonl
  business_reports_index.json
  learning_progress.json
  open_questions.json
```

---

## 16. Rollout Plan

### Phase 1

先把远程 MCP 主体跑起来，并暴露：

- `ads_daily_audit`
- `ads_change_history`
- `memory_overview`
- `memory_timeline`

### Phase 2

补上：

- `biz_report_ingest`
- `learning_update`
- `board_refresh`

### Phase 3

补上：

- `boss_brief_generate`
- HTTP bridge
- 发布与验证链路

---

## 17. Open Questions

当前还需要后续在实现阶段明确的点：

1. 远程服务器部署位置选哪台机器
2. Google Ads 凭证如何从本机迁移到远程
3. Claude 侧最终接入形式是直接 remote MCP 还是通过中转配置
4. Gemini 的 MCP 支持状态是否需要 HTTP bridge 优先
5. 业务报表 ingest 的最小标准口径是否需要统一模板

这些问题不阻塞设计成立，但会影响具体落地顺序。

---

## 18. Final Recommendation

正式按以下目标推进：

**Fishgoo Ads OS MCP + Project Memory System**

第一版采用：

- 远程 Ubuntu 单实例部署
- Python FastMCP
- Git 管理的项目记忆层
- Vercel 只做展示壳
- Google Ads 严格只读

这是当前最符合你目标的方案：  
**不是做一个“新工具”，而是做一个未来任何模型都能接班的项目中枢。**
