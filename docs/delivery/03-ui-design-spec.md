# Demand Intelligence Platform

## UI 设计与交互规范

日期：2026-03-21  
版本：v1.0

---

## 1. 设计目标

本系统 UI 的目标不是“展示数据很多”，而是：

- 让高层快速看懂
- 让业务负责人快速判断
- 让运维状态足够直观
- 让抓取、调度、停止等动作不会带来不确定感

---

## 2. 设计原则

1. 结论优先  
2. 证据随后  
3. 趋势先于存量  
4. 动作先于配置  
5. 运维状态必须显性化  

---

## 3. 页面结构

### 3.1 首页 Landing

文件：

- [index.html](/Users/perrilee/Desktop/探索/raddit/docs/product/index.html)

目标：

- 介绍产品价值
- 说明适合谁
- 引导进入产品演示与工作台

关键区块：

- Hero
- 核心价值
- 产品界面展示
- 适合谁 / 解决什么 / 为什么现在做
- 联系与页脚

### 3.2 工作台

文件：

- [mvp-app.html](/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.html)

核心视图：

- Dashboard
- Operations
- Study Setup
- Segment Explorer
- Packaging Studio
- Weekly Brief

---

## 4. 核心视觉层级

### 4.1 Hero 区

要求：

- 标题明确表达“市场信号 -> 决策”
- 主 CTA 视觉最强
- 次 CTA 次之
- 展示系统当前状态摘要

建议呈现：

- 标题：40px 级别
- 副标题：20-24px
- 主按钮：品牌主色填充
- 次按钮：边框/次色

### 4.2 指标卡

用于：

- Opportunity Score
- Packaging Readiness
- Trend Lift

设计要求：

- 每个指标都有清晰颜色语义
- 卡片本身可快速扫读

颜色建议：

- 高机会：绿色
- 高包装成熟度：蓝色
- 趋势升温：橙色
- 风险/异常：红色

### 4.3 状态卡

用于：

- Worker 在线/离线/陈旧
- Runtime alerts

要求：

- 状态颜色强区分
- 文案直接说明问题与动作
- 不依赖用户看日志理解状态

---

## 5. 关键组件规范

### 5.1 顶部导航

目标：

- 突出产品品牌
- 明确演示/试用入口
- 不让导航过重

组件：

- 品牌 logo / mark
- 导航链接
- 主 CTA

### 5.2 Tabs

目标：

- 清晰区分不同工作模式

状态：

- default
- hover
- active

### 5.3 Jobs / Operations 卡片

必须显示：

- mode
- stage
- lane
- priority
- status
- trigger
- finished_at

### 5.4 Stop 按钮

目标：

- 用户明确知道当前可以停止什么
- 点击后立刻有反馈

状态：

- `停止当前爬取`
- `停止待运行任务`
- `停止中...`
- hidden

---

## 6. 交互反馈规范

### 6.1 Toast

用于：

- 任务入队
- 任务完成
- 任务失败
- 任务取消
- 停止指令已发送

### 6.2 立即反馈原则

凡是以下动作，前端必须立即反馈，不应仅依赖轮询：

- 停止任务
- 重试任务
- 切换调度
- 新建 Study
- 提交首跑

### 6.3 异常解释

如果任务没有被停止，系统要明确区分：

- 没有活动任务
- 任务已完成
- Worker 离线
- stop 请求失败

---

## 7. 页面级规范

### Dashboard

优先展示：

1. 最高价值结论
2. 关键客群
3. 推荐产品
4. 趋势变化
5. 证据
6. Worker 与异常

### Operations

优先展示：

1. 当前有效任务
2. 最近完成任务
3. 失败与重试
4. 任务详情

不应默认展示：

- 历史大量已过期失败任务

### Study Setup

优先展示：

- 业务语言输入
- 自动推荐关键词
- 抓取成本提示
- 首跑策略

---

## 8. 当前 UI 资产

- Landing：[`index.html`](/Users/perrilee/Desktop/探索/raddit/docs/product/index.html)
- App Shell：[`mvp-app.html`](/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.html)
- 交互逻辑：[`mvp-app.js`](/Users/perrilee/Desktop/探索/raddit/docs/product/mvp-app.js)
- 视觉样式：[`prototype.css`](/Users/perrilee/Desktop/探索/raddit/docs/product/prototype.css)
- 品牌资源：
  - [favicon.svg](/Users/perrilee/Desktop/探索/raddit/docs/product/favicon.svg)
  - [og-image.svg](/Users/perrilee/Desktop/探索/raddit/docs/product/og-image.svg)

---

## 9. 后续 UI 演进建议

1. 给 Dashboard 增加更成熟的数据卡层级
2. 给 Study Setup 增加更细的关键词贡献解释
3. 给 Operations 增加任务详情抽屉
4. 给 Landing 增加更标准 SaaS 的 social proof 区
