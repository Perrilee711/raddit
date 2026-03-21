# Demand Intelligence Platform

## 项目完整交付总索引

日期：2026-03-21  
项目类型：需求情报决策系统 / 混合部署产品  
交付状态：已完成第一阶段可用交付

---

## 1. 项目一句话定义

这不是一个“Reddit 爬虫工具”，而是一套把公开市场信号转化为 **客群判断、产品包装、趋势预警与业务动作建议** 的需求情报系统。

它的核心价值是帮助 CEO、业务线负责人和战略负责人更快回答：

- 现在最值得打的客群是谁？
- 他们最痛的点是什么？
- 我们该怎么包装产品？
- 最近哪些需求在升温、衰减或需要立即跟进？

---

## 2. 交付范围

本次交付包含 8 类核心资产：

1. `BRD`：业务需求文档
2. `PRD`：产品需求文档
3. `UI Spec`：界面与交互规范
4. `Technical Design`：技术系统设计
5. `QA/Test`：测试、验收与回归方案
6. `Release & Handoff`：上线、部署、交接手册
7. `Project Workflow`：可复用项目交付工作流
8. `Live System`：代码仓库、在线地址、运行环境

---

## 3. 本次交付物清单

### 3.1 项目级交付文档

- [01-business-requirements-brd.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/01-business-requirements-brd.md)
- [02-product-requirements-prd.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/02-product-requirements-prd.md)
- [03-ui-design-spec.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/03-ui-design-spec.md)
- [04-technical-system-design.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/04-technical-system-design.md)
- [05-test-plan-and-acceptance.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/05-test-plan-and-acceptance.md)
- [06-release-and-handoff.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/06-release-and-handoff.md)
- [07-reusable-project-delivery-workflow.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/07-reusable-project-delivery-workflow.md)

### 3.2 已有补充文档

- [需求情报原始 PRD](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-18-demand-intelligence-prd.md)
- [生产级数据架构方案](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-19-demand-intelligence-production-data-architecture.md)
- [重构实施路线图](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-19-demand-intelligence-rebuild-roadmap.md)
- [混合部署方案 A](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-20-solution-a-hybrid-deployment-implementation-plan.md)
- [A1 公网 API Runbook](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-20-solution-a-a1-public-api-runbook.md)
- [A2 Mac Worker Runbook](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-20-solution-a-a2-mac-worker-runbook.md)
- [Mac LaunchAgent 手册](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-19-macos-launchagent-runbook.md)

---

## 4. 当前上线地址

### 4.1 主工作台

- 团队在线工作台：[`http://43.162.90.26/`](http://43.162.90.26/)
- API 健康检查：[`http://43.162.90.26/api/health`](http://43.162.90.26/api/health)

说明：

- 这是当前真正支持队列、Study、Worker 联通和任务调度的工作入口。
- 适合内部团队在线使用。

### 4.2 展示版前端

- Vercel 展示版：[`https://skill-deploy-jr9bh4v87v.vercel.app`](https://skill-deploy-jr9bh4v87v.vercel.app)

说明：

- 该地址更适合对外展示产品界面、首页、演示壳。
- 因当前 API 仍为 `HTTP`，完整交互仍以 `43.162.90.26` 为主。

### 4.3 代码仓库

- GitHub 仓库：[`https://github.com/Perrilee711/raddit`](https://github.com/Perrilee711/raddit)

---

## 5. 系统当前组成

### 5.1 前端

- 首页：[`/Users/perrilee/Desktop/探索/raddit/docs/product/index.html`](/Users/perrilee/Desktop/探索/raddit/docs/product/index.html)
- 工作台：[`/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.html`](/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.html)
- 前端逻辑：[`/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.js`](/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.js)
- 样式系统：[`/Users/perrilee/Desktop/探索/raddit/docs/product/prototype.css`](/Users/perrilee/Desktop/探索/raddit/docs/product/prototype.css)

### 5.2 后端 API

- 入口：[`/Users/perrilee/Desktop/探索/raddit/scripts/demand_intelligence_server.py`](/Users/perrilee/Desktop/探索/raddit/scripts/demand_intelligence_server.py)

### 5.3 Mac Worker

- Worker 主进程：[`/Users/perrilee/Desktop/探索/raddit/scripts/mac_worker_agent.py`](/Users/perrilee/Desktop/探索/raddit/scripts/mac_worker_agent.py)
- 安装脚本：[`/Users/perrilee/Desktop/探索/raddit/scripts/install_mac_worker_launch_agent.sh`](/Users/perrilee/Desktop/探索/raddit/scripts/install_mac_worker_launch_agent.sh)
- 状态脚本：[`/Users/perrilee/Desktop/探索/raddit/scripts/status_mac_worker_launch_agent.sh`](/Users/perrilee/Desktop/探索/raddit/scripts/status_mac_worker_launch_agent.sh)

### 5.4 数据与调度

- 实体构建：[`/Users/perrilee/Desktop/探索/raddit/scripts/build_study_entity_store.py`](/Users/perrilee/Desktop/探索/raddit/scripts/build_study_entity_store.py)
- payload 构建：[`/Users/perrilee/Desktop/探索/raddit/scripts/build_demand_intelligence_payload.py`](/Users/perrilee/Desktop/探索/raddit/scripts/build_demand_intelligence_payload.py)
- pipeline 入口：[`/Users/perrilee/Desktop/探索/raddit/scripts/run_study_pipeline.py`](/Users/perrilee/Desktop/探索/raddit/scripts/run_study_pipeline.py)

---

## 6. 推荐阅读顺序

如果是第一次接手这个项目，建议按下面顺序阅读：

1. [01-business-requirements-brd.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/01-business-requirements-brd.md)
2. [02-product-requirements-prd.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/02-product-requirements-prd.md)
3. [03-ui-design-spec.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/03-ui-design-spec.md)
4. [04-technical-system-design.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/04-technical-system-design.md)
5. [05-test-plan-and-acceptance.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/05-test-plan-and-acceptance.md)
6. [06-release-and-handoff.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/06-release-and-handoff.md)
7. [07-reusable-project-delivery-workflow.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/07-reusable-project-delivery-workflow.md)

---

## 7. 当前闭环是否成立

当前项目已经具备一套可运行闭环：

- 业务目标定义
- 产品结构定义
- UI 原型与在线工作台
- 线程级 + 评论级数据模型
- 云上 API + Mac Worker 混合部署
- 队列、调度、停止任务、运维状态
- 测试与交接资料
- 线上地址与仓库地址

这意味着它已经不仅是一个脚本集合，而是一个 **可交付、可演示、可扩展、可复用** 的项目样板。

---

## 8. 下一次项目怎么复用

下一次做别的项目时，不要从代码开始，而应直接复用：

- [07-reusable-project-delivery-workflow.md](/Users/perrilee/Desktop/探索/raddit/docs/delivery/07-reusable-project-delivery-workflow.md)

它定义了：

- 标准项目阶段
- 每一阶段的产物
- 交付检查点
- 上线前验收门槛
- 文档结构建议
- 团队协作方式

这会是后续提升效率的核心抓手。
