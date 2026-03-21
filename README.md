# Reddit Leads Research

这个仓库用来把 Reddit 里的电商需求线索，整理成可阅读、可实施的研究文档。

当前提供：

- `docs/reddit-client-research-playbook.md`：找客户、识别需求、总结共性的中文实施手册
- `config/reddit_targets.json`：默认抓取版块和关键词配置
- `scripts/reddit_intel_pipeline.py`：自动抓取 + 自动出报告的一键流水线
- `scripts/reddit_browser_pipeline.py`：旧版浏览器抓取脚本，只抓搜索结果卡片
- `scripts/discover_threads.py`：先发现值得跟踪的 Reddit thread
- `scripts/harvest_threads.py`：进入 thread 详情页，抓主帖正文和评论
- `scripts/reddit_thread_pipeline.py`：新的两段式浏览器流水线，负责 `discover -> harvest -> report`
- `scripts/hot_thread_policy.py`：高价值 thread 选择策略，负责决定哪些 thread 该进入增量刷新
- `scripts/refresh_hot_threads.py`：只刷新高价值 thread，而不是每次全量重跑
- `scripts/reddit_research_report.py`：把抓取结果整理成 Markdown 报告
- `.env.example`：Reddit OAuth 凭证示例
- `data/examples/reddit_posts_demo.jsonl`：本地演示数据
- `docs/reports/`：脚本输出的研究报告目录
- `docs/product/`：需求情报决策台原型与 MVP 页面
- `scripts/build_demand_intelligence_payload.py`：把 Reddit 样本映射成决策台 payload
- `scripts/build_study_entity_store.py`：把原始帖子样本升级成 thread / comment / snapshot / signal 实体底座
- `scripts/demand_intelligence_server.py`：最小后端服务，提供 API + 托管 MVP 页面
- `scripts/run_study_pipeline.py`：按 study id 重建某个研究任务的 payload / pipeline，支持 `seeded / browser / hot_threads / adaptive`

## 完整交付文档

如果你要把这个项目作为一个完整系统交付、归档或对外转交，优先阅读：

- `docs/delivery/00-project-delivery-index.md`：完整交付总索引
- `docs/delivery/01-business-requirements-brd.md`：业务需求文档
- `docs/delivery/02-product-requirements-prd.md`：产品需求文档
- `docs/delivery/03-ui-design-spec.md`：UI 设计与交互规范
- `docs/delivery/04-technical-system-design.md`：技术系统设计
- `docs/delivery/05-test-plan-and-acceptance.md`：测试与验收文档
- `docs/delivery/06-release-and-handoff.md`：发布与交接文档
- `docs/delivery/07-reusable-project-delivery-workflow.md`：下一次项目可复用的标准工作流
- `docs/delivery/08-executive-delivery-summary.md`：老板汇报版交付摘要源文档
- `docs/delivery/08-executive-delivery-summary.pptx`：老板汇报版 PPT 成品
- `docs/delivery/09-project-acceptance-checklist.xlsx`：表格版项目验收清单
- `templates/project-delivery-template/`：下个项目可直接复制的空白模板目录

## 适用版块

- `r/dropship`
- `r/dropshipping`
- `r/ecommerce`
- `r/shopify`
- `r/woocommerce`

## 推荐工作流

1. 优先运行 `scripts/reddit_thread_pipeline.py`
2. 先发现目标版块与关键词下值得跟踪的 thread
3. 再进入 thread 详情页抓主帖正文和评论
4. 输出 enriched JSONL 到 `data/raw/`
5. 自动生成 Markdown 研究报告到 `docs/reports/`
6. 人工阅读并筛选高意向帖子

如果你后面补了 Reddit OAuth 凭证，也可以使用 `scripts/reddit_intel_pipeline.py`

如果你已经有自己的抓取结果：

1. 把数据保存到 `data/raw/`
2. 用 `scripts/reddit_research_report.py` 生成研究报告
3. 阅读 `docs/reports/*.md`，优先跟进高意向问题和高频痛点

## 数据格式

支持 `json`、`jsonl`、`csv`。

建议字段：

- `title`
- `body`
- `subreddit`
- `author`
- `url`
- `created_utc`
- `score`
- `num_comments`
- `search_term`

## 运行示例

```bash
/usr/bin/python3 scripts/reddit_thread_pipeline.py \
  --config config/studies/fishgoo-us-dropshipping.json \
  --raw-output data/raw/studies/fishgoo-us-dropshipping.jsonl \
  --report-output docs/reports/studies/fishgoo-us-dropshipping.md \
  --continue-on-error
```

这个脚本会：

- 调起本机 `Google Chrome`
- 打开 Reddit 搜索页并发现 thread
- 进入每个 thread 的详情页
- 抓主帖正文、评论和基础互动数
- 保存 enriched JSONL
- 自动输出 Markdown 报告

注意：

- 需要你本机浏览器能正常访问 Reddit
- 第一次运行时，macOS 可能会要求你授权“终端/应用控制 Chrome”
- 如果 Chrome 打开的仍然是 `You've been blocked by network security`，那说明当前网络本身被 Reddit 风控拦截，脚本也无法强行绕过

如果你只想保留旧版的“搜索卡片快速抓取”，仍然可以运行：

```bash
/usr/bin/python3 scripts/reddit_browser_pipeline.py --continue-on-error
```

旧版模式会：

- 遇到单个搜索页失败时跳过继续
- 每抓完一个页面就刷新 `data/raw/*.jsonl`
- 同步更新 `docs/reports/*.md`

API 版本命令：

```bash
/usr/bin/python3 scripts/reddit_intel_pipeline.py
```

如果公开 JSON 抓取被 Reddit 拦截，脚本会自动尝试读取环境变量里的 OAuth 凭证：

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USERNAME`（可选）
- `REDDIT_PASSWORD`（可选）

也可以指定输出路径：

```bash
/usr/bin/python3 scripts/reddit_intel_pipeline.py \
  --raw-output data/raw/latest_reddit_posts.jsonl \
  --report-output docs/reports/latest_reddit_report.md
```

只对已有原始数据生成报告：

```bash
/usr/bin/python3 scripts/reddit_research_report.py \
  --input data/examples/reddit_posts_demo.jsonl \
  --output docs/reports/demo-report.md
```

生成后的报告会包含：

- 子版块分布
- 高频需求标签
- 高意向客户线索
- 共性问题总结
- 建议优先切入的话题

## Demand Intelligence MVP

如果你想把 Reddit 样本直接喂给“需求情报决策台”，先生成 payload：

```bash
/usr/bin/python3 scripts/build_demand_intelligence_payload.py \
  --input /Users/perrilee/raddit/data/raw/fishgoo_dropshipping_expanded.jsonl \
  --json-output docs/product/data/fishgoo-dashboard-payload.json \
  --js-output docs/product/data/fishgoo-dashboard-payload.js
```

然后启动最小后端：

```bash
/usr/bin/python3 scripts/demand_intelligence_server.py --port 8765
```

打开：

- `http://127.0.0.1:8765/`

当前已提供的接口：

- `/api/health`
- `/api/studies/fishgoo-us-dropshipping/dashboard`
- `/api/studies/fishgoo-us-dropshipping/data-foundation`
- `/api/studies/fishgoo-us-dropshipping/threads`
- `/api/studies/fishgoo-us-dropshipping/threads/<threadId>`
- `/api/studies/fishgoo-us-dropshipping/comments`
- `/api/studies/fishgoo-us-dropshipping/signals`
- `/api/studies/fishgoo-us-dropshipping/segments`
- `/api/studies/fishgoo-us-dropshipping/segments/<segmentId>`
- `/api/studies/fishgoo-us-dropshipping/packages`
- `/api/studies/fishgoo-us-dropshipping/weekly-brief`
- `/api/auth/me`
- `/api/auth/login`
- `/api/auth/logout`
- `/api/worker/health`
- `/api/worker/claim`
- `/api/worker/jobs/<jobId>/complete`
- `/api/worker/jobs/<jobId>/fail`
- `/api/jobs`
- `/api/jobs/<jobId>`
- `/api/jobs/<jobId>/retry`
- `/api/jobs/<jobId>/cancel`
- `/api/studies/<studyId>/jobs`
- `/api/studies/<studyId>/schedule`
- `/api/studies/<studyId>/operations`

现在还支持 study 持久化：

- `GET /api/studies`
- `GET /api/study-template`
- `POST /api/studies/draft`
- `POST /api/studies`
- `GET /api/studies/<studyId>/config`
- `POST /api/studies/<studyId>/rebuild`
- `POST /api/studies/<studyId>/schedule`

study 会写到：

- `data/studies/*.json`
- `config/studies/*.json`
- `docs/product/data/studies/*`
- `data/entities/studies/<studyId>/*`

其中新的数据底座实体包括：

- `manifest.json`
- `threads.json`
- `thread_snapshots.json`
- `comments.json`
- `comment_snapshots.json`
- `signals.json`

这意味着你现在可以：

1. 在前端 `Study Setup` 里新建研究任务
2. 让服务把它保存成本地 study
3. 在 study 列表里切换不同研究任务
4. 查看每个 study 的任务历史、调度状态和数据来源映射
5. 在 Dashboard / Weekly Brief 里查看趋势时间序列，而不只是静态快照
6. 通过 `threads/comments/signals` API 检查当前 study 的数据新鲜度、评论覆盖率和实体底座状态

## Solution A / A2：Mac Worker 联通

如果前端和 API 已经部署到公网服务器，但 Reddit 采集仍然依赖 `Chrome + AppleScript`，可以启用混合部署：

- 公网 API：队列、study、聚合与发布
- Mac Worker：只负责 `discover / harvest / refresh_hot`

Mac Worker 轮询的核心接口：

- `POST /api/worker/claim`
- `POST /api/worker/jobs/<jobId>/complete`
- `POST /api/worker/jobs/<jobId>/fail`
- `GET /api/worker/health`

Worker 认证配置在：

- `config/workers.json`

默认内置的 worker：

- `id`: `fishgoo-mac-worker`
- `token`: `fishgoo-mac-worker-token`

启动 Mac Worker：

```bash
/usr/bin/python3 scripts/mac_worker_agent.py \
  --api-base-url http://43.162.90.26 \
  --worker-token fishgoo-mac-worker-token \
  --worker-id fishgoo-mac-worker \
  --continue-on-error
```

如果要在 Mac 上常驻运行：

```bash
./scripts/install_mac_worker_launch_agent.sh
./scripts/status_mac_worker_launch_agent.sh
```

其中：

- `scripts/start_mac_worker_agent.sh`：Worker 启动脚本
- `scripts/install_mac_worker_launch_agent.sh`：安装 LaunchAgent
- `scripts/status_mac_worker_launch_agent.sh`：查看 Worker 状态
- `scripts/uninstall_mac_worker_launch_agent.sh`：卸载 Worker LaunchAgent

## Solution A / A3：团队正式工作流

当公网 API 和 Mac Worker 都在线后，系统会进入默认的团队工作流：

- 云上 API 负责发任务、保存 study、聚合结果、发布前端 payload
- Mac Worker 负责 `discover / harvest / refresh_hot`
- `rebuild_aggregates / publish_brief` 留在 API 节点本地执行

新增运行时接口：

- `GET /api/runtime`

这个接口会返回：

- 当前是否 `hybrid_ready`
- 在线 Worker 数量
- 默认首跑模式：`browser`
- 默认自动调度模式：`adaptive`
- 当前工作流说明：`云上发任务，Mac 自动执行浏览器采集，结果聚合后自动回写前端`

工作流规则：

- 新建 study：默认 `browser` 首跑，后续自动调度切回 `adaptive`
- 已开启但仍是 `seeded` 的旧 study：当 Mac Worker 连上后，会自动升级到 `adaptive`
- 如果 Mac Worker 不在线，`adaptive` 会自动回退成 `seeded`，避免把远程任务卡死在队列里

## Phase 2：Thread + Comment 采集

当前浏览器链路已经升级成两段式：

1. `discover_threads.py`
   先在 subreddit 搜索结果页发现候选 thread。
2. `harvest_threads.py`
   再进入每个 thread 详情页，抓取主帖正文与评论。
3. `reddit_thread_pipeline.py`
   串起 `discover -> harvest -> report`，并作为 study browser 模式的默认入口。

这意味着 browser 模式不再只是标题级样本，而会尽量把评论也接进：

- `data/raw/studies/*.jsonl`
- `data/entities/studies/<studyId>/comments.json`
- `data/entities/studies/<studyId>/signals.json`
- Dashboard 的评论覆盖率与数据新鲜度指标

## Phase 3：Incremental Refresh + Comment-Driven Scoring

当前实体底座已经支持：

- 同一个 study 多次重建时，合并已有 `threads/comments`
- 追加新的 `thread_snapshots/comment_snapshots/signals`
- 在 `manifest.json` 里记录增量刷新状态：
  - `build_number`
  - `incremental_mode`
  - `new_threads`
  - `refreshed_threads`
  - `new_comments`

评论信号现在也会进入决策分，而不再只是展示评论数量：

- `comment_confirmation_score`
- `recommendation_density`
- `objection_density`

这些信号会影响：

- Opportunity Score
- Packaging Readiness

## 方案 A：前端接公网 API

如果你要让同事通过 Vercel 前端访问完整系统，而不是依赖本机 `127.0.0.1`，当前仓库已经补了 A1 所需的最小能力：

- 前端运行时配置：
  - `docs/product/runtime-config.js`
  - `docs/product/runtime-config.example.js`
- 公网 API 启动脚本：
  - `scripts/start_public_api.sh`
- 云服务器部署模板：
  - `deploy/solution-a/demand-intelligence-api.service`
  - `deploy/solution-a/nginx-api.conf`
- 上线手册：
  - `docs/product/2026-03-20-solution-a-a1-public-api-runbook.md`

前端跨域访问时，当前服务支持：

- `X-User-Token`
- `Authorization: Bearer`
- CORS preflight

最简单的使用方式是把 `docs/product/runtime-config.js` 改成：

```js
window.__DEMAND_INTEL_CONFIG__ = {
  API_BASE_URL: "https://api.fishgoo.com",
};
```

然后把后端服务部署到 Ubuntu 服务器并开启：

```bash
./scripts/start_public_api.sh
```
- Weekly Brief 的结论文案
- Dashboard 的数据映射与评论驱动信号模块

## Phase 4：Hot Thread Refresh

现在系统已经支持四种运行模式：

- `seeded`
- `browser`
- `hot_threads`
- `adaptive`

其中 `adaptive` 会根据当前 study 的新鲜度、评论覆盖率和 hot-thread 候选情况自动选择最合适的执行模式。

它不是重新 discover 全量 thread，而是：

1. 从 `data/entities/studies/<studyId>/threads.json` 里挑出高价值、已 stale、或评论还不完整的 thread
2. 只对这些 thread 进入详情页做增量 harvest
3. 把新的正文 / 评论 / 互动数据合并回现有 raw dataset
4. 再重建 entity store、payload、Dashboard 和 Weekly Brief

当前 hot-thread 策略会综合这些因素：

- `tracking_priority`
- `current_comment_count`
- `current_score`
- `comment_capture_state`
- `hours_since_harvest`
- `hours_since_activity`

你可以直接 dry-run 看当前会选中哪些 thread：

```bash
/usr/bin/python3 scripts/refresh_hot_threads.py \
  --config config/studies/fishgoo-us-dropshipping.json \
  --entity-root data/entities/studies/fishgoo-us-dropshipping \
  --input data/raw/studies/fishgoo-us-dropshipping.jsonl \
  --output /tmp/fishgoo-hot-refresh.jsonl \
  --dry-run
```

也可以直接按 study 运行：

```bash
/usr/bin/python3 scripts/run_study_pipeline.py \
  --study-id fishgoo-us-dropshipping \
  --mode hot_threads \
  --continue-on-error
```

也可以让系统自己判断当前该走哪条链路：

```bash
/usr/bin/python3 scripts/run_study_pipeline.py \
  --study-id fishgoo-us-dropshipping \
  --mode adaptive \
  --continue-on-error
```

Study config 里新增了这些参数：

- `hot_thread_max_count`
- `hot_thread_min_comments`
- `hot_thread_min_score`
- `hot_thread_max_age_hours`
- `hot_thread_stale_after_hours`
- `hot_thread_min_refresh_gap_minutes`

在前端里，这些模式也已经接进：

- 顶部手动刷新模式选择器
- Study Setup 调度配置
- Operations 页面里的 study 快捷运行按钮

## Demo 账号与权限

本地 MVP 默认带 3 个演示账号，配置文件在：

- `config/users.json`

默认账号：

- `admin@local / admin123`
- `analyst@local / analyst123`
- `viewer@local / viewer123`

权限分层：

- `viewer`：只能看 dashboard / studies / jobs
- `analyst`：可以创建 study、生成 draft、手动 rebuild
- `admin`：额外可以配置 schedule、触发 browser 模式重建

前端在本地 HTTP 模式下会自动用 `admin demo` 登录，方便直接演示。

## 任务队列与自动调度

任务会落盘到：

- `data/jobs/*.json`

study 的调度配置会保存在：

- `data/studies/*.json`

典型流程：

1. `POST /api/studies/<studyId>/rebuild` 把一次重建加入任务队列
2. 后台 worker 会按多级队列顺序处理 `queued -> running -> completed/failed`
3. `POST /api/studies/<studyId>/schedule` 可以开启定时更新
4. 调度线程会在到点后自动 enqueue 新任务
5. 任务失败或需要复跑时，可以通过 `/api/jobs/<jobId>/retry` 重新入队
6. 排队中的任务可以通过 `/api/jobs/<jobId>/cancel` 取消

Phase 5 之后，任务不再只是简单排队，而是进入 3 条队列车道：

- `realtime`：优先刷新 hot threads
- `discovery`：完整浏览器发现与 harvest
- `maintenance`：轻量 seeded 重建

每条任务还会带：

- `requested_mode`
- `resolved_mode`
- `queue_lane`
- `priority_score`
- `priority_label`
- `strategy_reason`

默认规则：

- `hot_threads` 会进入 `realtime`
- `browser` 会进入 `discovery`
- `seeded` 会进入 `maintenance`
- `adaptive` 会根据当前 study 状态自动 resolve 到上面三者之一

如果同一个 study 已经有一条 queued 任务，系统会优先：

- 复用这条 queued 任务
- 或在必要时把它升级成更高优先级 / 更高价值的模式

这样可以避免 study 被重复入队，队列也更接近真实的生产编排。

## Phase 6：Thread / Comment Job Orchestration

现在多级队列已经进一步升级成真正的阶段化 pipeline。

不同模式会被拆成这些 stage：

- `browser`
  - `discover`
  - `harvest`
  - `rebuild_aggregates`
  - `publish_brief`
- `hot_threads`
  - `refresh_hot`
  - `rebuild_aggregates`
  - `publish_brief`
- `seeded`
  - `rebuild_aggregates`
  - `publish_brief`

这意味着一个刷新动作不再是单个大 job，而是一串可跟踪的任务链。

每条 job 现在都会带：

- `pipeline_id`
- `stage_kind`
- `stage_label`
- `pipeline_progress`
- `parent_job_id`

## Mac 常驻运行（LaunchAgent）

如果你希望这套系统在 Mac 本机登录后自动拉起、常驻运行，并依靠内部 schedule 持续刷新 study，直接看这份运行手册：

- [2026-03-19-macos-launchagent-runbook.md](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-19-macos-launchagent-runbook.md)

已经配好的脚本有：

- [start_demand_intelligence_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/start_demand_intelligence_agent.sh)
- [install_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/install_launch_agent.sh)
- [uninstall_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/uninstall_launch_agent.sh)
- [status_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/status_launch_agent.sh)
- [configure_study_schedule.sh](/Users/perrilee/Desktop/探索/raddit/scripts/configure_study_schedule.sh)

如果仓库位于 `Desktop` 路径下，安装脚本会自动把实际运行时同步到：

```text
~/raddit-service
```

这是为了避开 macOS 对 Desktop 目录下 LaunchAgent/自动化脚本的权限限制。状态脚本也会优先显示 LaunchAgent 当前真实使用的运行目录和日志路径，而不是只看工作区里的相对路径。

因此你在 Operations 里能直接看到：

- 当前跑到 `discover` 还是 `harvest`
- 这条 pipeline 现在是 `1/4`、`2/4` 还是 `4/4`
- 哪些 job 是 follow-up job，而不是用户手动触发

这对后面的 thread/comment 增量刷新非常关键，因为真正有商业价值的不是“跑过一次”，而是“知道这条研究管线当前在抓什么、缺什么、下一步会自动做什么”。

## Operations 视图

前端现在还多了一个 `Operations` 视图，用来做这些事情：

- 看全局任务统计
- 看每个 study 的调度状态
- 直接触发 `adaptive / seeded / browser / hot_threads`
- 暂停/启用某个 study 的自动调度
- 查看任务详情、队列车道、优先级、编排原因
- 重跑任务、取消排队中的任务

## 趋势时间序列

Dashboard 和 Weekly Brief 现在都支持 `trendSeries` 视图，用来回答：

- 最近 6 个窗口里，哪个主题在升温
- 哪个主题虽然整体机会高，但最近窗口在回落
- 第二主产品是不是正在接近主产品
- 近 7 天、近 30 天和全量样本下，判断会不会发生变化

前端交互：

- 点击时间窗口 chip：切换 `近7天 / 近30天 / 近90天 / 全量样本`
- 点击图例：聚焦某一条机会线，其他线会降权显示
- 鼠标悬停折线点：查看该窗口的具体值
- 图上橙色异常标记：表示该窗口出现异常上冲或异常回落
- 图例和下方卡片里的“较上一周期...”说明：用于周会里直接解释变化方向，而不需要人工再口头翻译

当前规则：

- 如果原始数据里有足够多可解析的 `created_utc`，系统会按时间窗口聚合
- 如果时间戳不稳定，系统会退化成按样本顺序窗口近似趋势

这个视图的目的不是替代机会分，而是补充“变化方向”。

手动测试立即排队一轮：

```bash
/usr/bin/curl -s -X POST http://127.0.0.1:8765/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@local","password":"admin123"}' \
  -c /tmp/demand-intel.cookie

/usr/bin/curl -s -b /tmp/demand-intel.cookie \
  -X POST http://127.0.0.1:8765/api/studies/fishgoo-us-dropshipping/schedule \
  -H 'Content-Type: application/json' \
  -d '{"enabled":true,"mode":"adaptive","interval_hours":24,"start_now":true}'
```

如果你想按 study id 重建一次：

```bash
/usr/bin/python3 scripts/run_study_pipeline.py --study-id fishgoo-us-dropshipping
```

如果你想让某个 study 走浏览器抓取再重建：

```bash
/usr/bin/python3 scripts/run_study_pipeline.py \
  --study-id fishgoo-us-dropshipping \
  --mode browser \
  --continue-on-error
```
