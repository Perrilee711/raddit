# Demand Intelligence Platform

## PRD：产品需求文档

日期：2026-03-21  
版本：v1.0

---

## 1. 产品定位

Demand Intelligence Platform 不是爬虫后台，也不是舆情监控面板。

它是一个面向业务负责人和 CEO 的 **需求情报决策台**，用于：

- 选客群
- 定产品包装
- 看趋势
- 跟踪执行

---

## 2. 核心用户与 JTBD

### 主用户

- 业务线负责人

### 次用户

- CEO
- 战略/研究负责人

### 用户要完成的任务

1. 判断现在应该服务谁
2. 判断应该主推什么产品
3. 判断最近什么需求在升温
4. 判断系统当前抓取与分析是否可信

---

## 3. 核心功能模块

### 3.1 Dashboard

目标：
用最短时间给出最高价值结论。

主要模块：

- Executive Hero
- 高价值客群榜
- 推荐产品包装
- 趋势时间序列
- 证据摘要墙
- 客群 x 痛点热力图
- Worker 在线状态
- 异常与重试
- 任务队列与调度

### 3.2 Study Setup

目标：
让用户通过业务语言而不是技术参数创建研究任务。

关键能力：

- 填写市场 / 客群 / 问题空间
- 自动推荐关键词和 subreddit
- 可编辑关键词标签
- 一键创建 Study 并首跑
- 首跑默认 browser，后续切回 adaptive

### 3.3 Operations

目标：
让团队看清任务是否在运行、失败、取消、重试。

关键能力：

- 任务列表
- 任务详情
- 阶段状态
- 停止当前爬取
- 重跑失败任务
- 过滤当前有效任务

### 3.4 Segment Explorer

目标：
把“泛市场”变成“可行动客群”。

关键能力：

- 客群排名
- 痛点
- 产品建议
- 决策理由

### 3.5 Packaging Studio

目标：
把需求翻译成产品包装。

关键能力：

- 产品名
- 客群
- 主问题
- 一句话价值承诺
- 不该主打的方向

### 3.6 Weekly Brief

目标：
作为周会前的简报视图。

关键能力：

- 本周最高优先级结论
- 本周客群与产品建议
- 趋势与风险
- 下周建议动作

---

## 4. 关键交互

### 4.1 新建 Study

流程：

1. 用户进入 Study Setup
2. 输入市场、客群、问题空间
3. 系统自动给出关键词建议
4. 用户可微调关键词
5. 用户点击创建并首跑
6. 系统自动创建 Study
7. 系统自动提交 `browser` 首跑
8. 系统将 schedule 设为 `adaptive`

### 4.2 手动刷新

支持模式：

- seeded
- browser
- hot_threads
- adaptive

### 4.3 停止当前爬取

目标：
避免浏览器抓取长期占用办公环境。

交互要求：

- 仅在有可中断任务时显示
- 点击后立即显示 `停止中...` / `取消中...`
- 系统提示：
  - 已发送停止指令
  - 当前没有可停止任务
  - 任务可能已完成

### 4.4 失败重试

目标：
降低运维成本。

交互要求：

- Dashboard 有异常与重试卡
- Operations 可重试失败任务
- 最近失败任务可直接重跑

---

## 5. 权限与角色

当前角色：

- viewer
- analyst
- admin

权限原则：

- viewer：看结果
- analyst：创建 Study、发起任务、停止任务、重试任务
- admin：改调度、改工作流模式、管理运行配置

---

## 6. 状态定义

### 6.1 Job 状态

- queued
- running
- canceling
- canceled
- completed
- failed

### 6.2 Worker 状态

- connected
- stale
- offline

### 6.3 Study 调度模式

- seeded
- browser
- hot_threads
- adaptive

---

## 7. 非功能需求

### 7.1 可用性

- 首页 3 分钟可看懂
- 周会前 15 分钟可完成判断

### 7.2 可观测性

必须具备：

- health
- job status
- worker status
- recent failures
- runtime alerts

### 7.3 可操作性

必须支持：

- 停止任务
- 重跑任务
- 查看任务状态
- 查看 Worker 在线情况

### 7.4 可扩展性

后续应支持：

- 新数据源
- HTTPS API
- 数据库
- 多 Worker
- 更标准的云端调度

---

## 8. 发布范围

### 当前已交付版本

- 云上 API：可用
- Mac Worker：可用
- 前端工作台：可用
- Dashboard / Operations / Setup / Weekly Brief：可用
- 停止当前爬取：可用
- Worker 在线/离线状态卡：可用
- 异常与重试：可用

### 下一阶段建议

- API 上 HTTPS 与正式域名
- 数据持久化升级
- 完整回放/审计日志
- 多源接入

---

## 9. 参考文档

- [原始产品 PRD](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-18-demand-intelligence-prd.md)
- [生产数据架构](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-19-demand-intelligence-production-data-architecture.md)
- [重构路线图](/Users/perrilee/Desktop/探索/raddit/docs/product/2026-03-19-demand-intelligence-rebuild-roadmap.md)
