# Demand Intelligence Platform

## 基于当前仓库的重构实施路线图

日期：2026-03-19  
目标：把现有 `静态样本驱动的展示型 MVP` 重构为 `持续刷新、评论驱动、可支撑经营决策的需求情报系统`

---

## 1. 这次重构到底要解决什么

当前仓库已经证明了三件事：

- 你们需要一个面向业务负责人的 Demand Intelligence 产品
- Reddit 数据能帮助验证客群和产品包装
- 前端决策界面已经有可用雏形

这次重构不再解决“有没有产品方向”，而是解决：

1. 数据如何持续刷新
2. 评论如何成为决策证据
3. Dashboard 如何不再依赖存量样本
4. 系统如何从 demo 升级为内部可运营产品

---

## 2. 当前仓库应该保留什么、替换什么

## 2.1 建议保留

### 前端产品壳

保留原因：

- 首页、MVP app、Dashboard、Weekly Brief 已经建立了管理层视图
- Study、Operations、Schedule、Weekly Brief 等产品概念已经成型

保留文件：

- [mvp-app.html](/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.html)
- [mvp-app.js](/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.js)
- [prototype.css](/Users/perrilee/Desktop/探索/raddit/docs/product/prototype.css)
- [index.html](/Users/perrilee/Desktop/探索/raddit/docs/product/index.html)

### 后端服务壳

保留原因：

- 已有 study、jobs、schedule、operations 的基本接口
- 有任务队列和调度器雏形

保留文件：

- [demand_intelligence_server.py](/Users/perrilee/Desktop/探索/raddit/scripts/demand_intelligence_server.py)

### Study 配置与持久化

保留原因：

- Study 概念已经适合作为产品主对象

保留目录：

- [data/studies](/Users/perrilee/Desktop/探索/raddit/data/studies)
- [config/studies](/Users/perrilee/Desktop/探索/raddit/config/studies)

## 2.2 建议重写或降级

### `reddit_browser_pipeline.py`

当前问题：

- 面向搜索页
- 产出的是帖子卡片，而不是 thread
- 没有评论

建议：

- 重写成两段式：
  - `discover_threads.py`
  - `harvest_thread.py`

### `build_demand_intelligence_payload.py`

当前问题：

- 基于 `title + body`
- 与评论层脱节
- 趋势层仍有样本顺序近似

建议：

- 保留“聚合器角色”
- 重写其输入结构和评分指标

### `run_study_pipeline.py`

当前问题：

- 仍以 `seeded / browser` 作为核心模式
- 更像一次性重跑脚本

建议：

- 降级为运维脚本
- 真正生产任务改由 job queue 驱动

---

## 3. 目标仓库结构

建议最终结构如下：

```text
scripts/
  discover_threads.py
  harvest_thread.py
  extract_signals.py
  rebuild_aggregates.py
  publish_brief.py
  demand_intelligence_server.py

data/
  studies/
  threads/
  comments/
  snapshots/
  signals/
  jobs/
  aggregates/

docs/product/
  mvp-app.html
  mvp-app.js
  prototype.css
```

如果第一阶段不引入数据库，也应该按实体拆目录，不再只靠单个 JSONL 文件做输入。

---

## 4. 重构分期

## Phase 0：产品转向确认

时间：0.5 周

目标：

- 不再把它定义成“Reddit 爬虫工具”
- 统一定义成“需求情报决策台”
- 明确浏览器为主链路时的产品边界

交付物：

- 当前这两份文档
- 关键 KPI 和成功标准

## Phase 1：数据底座升级

时间：1 周

目标：

- 把数据对象从 `post` 升级为 `thread`
- 把文件结构从 `raw jsonl` 升级为实体目录

要做：

1. 新建实体目录和 schema
2. 增加 `threads` / `thread_snapshots` / `comments` / `comment_snapshots`
3. 把 study 与 source query 解耦
4. 为每个 thread 增加状态和刷新字段

验收标准：

- 任意 study 都能看到 tracked threads 列表
- 每个 thread 都有 `first_seen_at`、`last_seen_at`、`last_harvest_at`

## Phase 2：Discovery 与 Thread Harvest

时间：1.5 周

目标：

- 不再只抓搜索卡片
- 新增 thread 发现与详情抓取

要做：

1. 实现 `discover_threads.py`
2. 实现 `harvest_thread.py`
3. 定义高价值 thread 的跟踪规则
4. 增加失败截图、HTML 快照、selector version

验收标准：

- discovery 能发现新 thread
- harvest 能抓主帖全文和前 N 条评论
- 热门 thread 可被重复刷新

## Phase 3：评论语义层

时间：1.5 周

目标：

- 把评论变成决策证据

要做：

1. 新建 `extract_signals.py`
2. 对 thread 和 comment 分别抽信号
3. 抽取：
   - pain
   - stance
   - decision_stage
   - solution_mention
   - objection_type
   - buying_signal

验收标准：

- 每个高价值 thread 至少能展示 3-5 条评论级信号
- Dashboard 可显示 comment-based insight

## Phase 4：增量刷新与聚合重构

时间：1 周

目标：

- 从全量 materialize 切成增量刷新

要做：

1. 增加 `discover_threads` job
2. 增加 `harvest_thread` job
3. 增加 `extract_signals` job
4. 增加 `rebuild_aggregates` job
5. 优化 scheduler，只刷新有变化的对象

验收标准：

- 新 thread 出现后 1 小时内能进入 Dashboard
- 热门 thread 评论变化能反映到 next refresh

## Phase 5：决策层升级

时间：1 周

目标：

- 让 Dashboard 变成“可信决策界面”

要做：

1. 首页显示：
   - last refreshed
   - freshness score
   - comment coverage
   - evidence count
2. Weekly Brief 新增：
   - new objections
   - new solution patterns
   - top confirmed pain
3. Evidence Wall 区分 thread/comment/OP reply

验收标准：

- 负责人能分辨旧信号和新变化
- 每条主要结论都能看到评论证据

## Phase 6：运营化与预警

时间：0.5-1 周

目标：

- 让产品适合日常使用，而不是只适合演示

要做：

1. 异常波动预警
2. 热门 thread 追踪列表
3. job 错误详情
4. 失败重试策略
5. daily / weekly brief 导出

验收标准：

- 能主动提示“值得开会讨论的变化”
- 任务失败可定位、可重试

---

## 5. 当前仓库具体改造建议

## 5.1 替换路线

### 现有 `reddit_browser_pipeline.py`

当前角色：

- 一次性采样脚本

新角色：

- 仅保留为 fallback discovery 脚本

替代：

- `discover_threads.py`
- `harvest_thread.py`

### 现有 `build_demand_intelligence_payload.py`

当前角色：

- 样本聚合器

新角色：

- 决策聚合器

改造方向：

- 输入从 posts 改为 threads + comments + signals
- 输出增加 freshness、coverage、comment confirmation

### 现有 `run_study_pipeline.py`

当前角色：

- 手动重跑 study

新角色：

- 运维和 debug 入口

真正生产流程：

- 交给 job queue 和 scheduler

---

## 6. MVP 仍然不该做什么

为了控制复杂度，下面这些不建议现在就做。

### 不建议 1：多平台一起上

先把 Reddit 的 thread + comments + refresh 做透，再考虑 X、Quora、LinkedIn、Discord。

### 不建议 2：开放式 SaaS 多租户

浏览器主链路下，先做内部工作台或高价值服务交付平台。

### 不建议 3：复杂权限与计费

先把决策价值做出来，再做商业化外壳。

### 不建议 4：过早引入大而全数据库架构

第一阶段可以先用结构化文件或轻量 DB，只要实体边界清晰即可。

---

## 7. 风险与应对

## 风险 1：浏览器链路不稳定

应对：

- selector version
- HTML snapshot
- screenshot on failure
- retry/backoff
- 部分成功写入

## 风险 2：评论展开成本高

应对：

- 只对高价值 thread 展开深抓
- 普通 thread 只抓浅层评论

## 风险 3：趋势仍然不够可信

应对：

- 强制使用真实时间戳
- 禁止在 production 里使用样本顺序近似

## 风险 4：抓得很多但仍然没有决策价值

应对：

- 所有输出必须服务 3 个问题：
  - 打谁
  - 卖什么
  - 为什么现在做

---

## 8. 推荐开发顺序

如果只选最有价值的先做，我建议顺序是：

1. thread 数据模型
2. thread 发现与刷新
3. 评论抓取
4. 评论语义抽取
5. freshness / coverage / confirmation 指标
6. Dashboard 升级
7. 预警与周报

这个顺序的原因很简单：

- 没有 thread，就没有评论
- 没有评论，就没有真正的决策差异化
- 没有 freshness，就没有管理层信任

---

## 9. 最小可商用版本定义

如果要定义“什么时候这套系统开始具备商业价值”，我建议标准是：

### 负责人每天打开能回答这 5 个问题

1. 过去 24 小时新增了哪些高价值 thread
2. 当前主痛点是否被评论进一步确认
3. 评论里新出现了哪些解决方案模式
4. 评论里新出现了哪些 objection
5. 推荐产品包装是否仍然成立

### 负责人每周开会能回答这 4 个问题

1. 哪个客群是本周最值得打的
2. 哪个产品包装应该主推
3. 哪个次产品正在升温
4. 哪些方向暂时不要投入

如果做不到这些，它仍然只是分析工具，不是决策产品。

---

## 10. 建议的立即执行清单

下面这 10 项建议按优先级直接推进。

1. 新建 `threads / comments / snapshots / signals` 目录结构
2. 增加 `discover_threads.py`
3. 增加 `harvest_thread.py`
4. 增加 `extract_signals.py`
5. 改 `demand_intelligence_server.py` 的 job 类型
6. 改 `build_demand_intelligence_payload.py` 的输入模型
7. 在 Dashboard 加 freshness / coverage 字段
8. 在 Evidence Wall 区分 comment 与 thread 证据
9. 在 Weekly Brief 加 objection / solution pattern
10. 禁止 production 使用样本顺序趋势近似

---

## 11. 最终判断

这套系统不是没价值，而是目前还停在“方向正确、底层不足”的阶段。

真正的护城河不是：

- 抓到更多帖子
- 做更漂亮的图

而是：

- 稳定抓到值得跟踪的 thread
- 持续刷新评论层
- 把评论语义翻译成可执行决策

如果按这份路线图推进，当前仓库完全可以从演示型产品升级成真正可用于经营判断的需求情报系统。
