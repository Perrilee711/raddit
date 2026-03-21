# Demand Intelligence Platform

## 老板汇报版交付摘要

日期：2026-03-21  
版本：v1.0

---

## Slide 1｜项目定义

**Demand Intelligence Platform**  
把公开市场信号转化为客群、产品与增长决策的需求情报系统

- 面向用户：CEO、业务线负责人、战略负责人
- 当前状态：第一阶段完整闭环已交付
- 当前形态：云上 API + Mac Worker + 在线工作台

---

## Slide 2｜为什么要做

当前业务判断市场机会，依赖的是：

- 零散社媒观察
- 手工搜帖
- 静态快照式报告
- 个人经验判断

这会导致：

- 市场变化发现太慢
- 客群判断不稳定
- 产品包装脱离用户原话
- 决策依据不可复盘、不可复用

---

## Slide 3｜本次交付了什么

本次交付不是一个单点爬虫，而是一套可运行的需求情报系统：

- Study 创建、关键词推荐与首跑
- Dashboard、Weekly Brief、Operations 三大核心界面
- 线程级与评论级实体底座
- browser / hot_threads / adaptive 调度模式
- stop、retry、worker 状态、运维告警
- GitHub、Vercel、腾讯云 API、Mac Worker 混合部署

---

## Slide 4｜产品与体验成果

本次已经形成完整业务工作流：

- 选客群：高价值客群榜、热力图、机会分
- 定产品：Packaging Studio、推荐产品包、价值主张
- 看趋势：时间序列趋势图、异常波动、变化解释
- 看执行：队列、任务、Worker 在线状态、停止当前爬取

页面入口：

- 团队工作台：`http://43.162.90.26/`
- 展示壳：`https://skill-deploy-jr9bh4v87v.vercel.app`

---

## Slide 5｜技术闭环

当前架构已形成一条完整闭环：

1. 云上 API 管理 Study、任务、调度与结果
2. Mac Worker 认领 browser / hot_threads 任务
3. 结果回写 raw / entities / payload
4. Dashboard 与 Weekly Brief 自动读取最新结果

关键能力：

- 多级队列与优先级编排
- thread/comment 实体模型
- 增量刷新与评论驱动评分
- 停止、重试、异常告警

---

## Slide 6｜测试与验收结果

核心链路已验证通过：

- 系统可访问
- Study 可创建
- 任务可入队
- Mac Worker 可认领任务
- 结果可回写
- 停止当前爬取
- 失败任务重试
- Worker 在线状态可感知

当前结论：

**第一阶段交付已达到“团队可用、可演示、可持续扩展”的门槛。**

---

## Slide 7｜当前上线资产

代码与系统入口：

- GitHub：`https://github.com/Perrilee711/raddit`
- 团队工作台：`http://43.162.90.26/`
- API 健康检查：`http://43.162.90.26/api/health`
- Vercel 展示版：`https://skill-deploy-jr9bh4v87v.vercel.app`

运维入口：

- 主服务状态：`scripts/status_launch_agent.sh`
- Worker 状态：`scripts/status_mac_worker_launch_agent.sh`

---

## Slide 8｜下一阶段建议

建议按两个层次继续推进：

### 生产化增强

- HTTPS API 与正式域名
- 更正式鉴权与权限
- 文件存储升级为数据库
- 更稳的告警与自动恢复

### 方法论复用

- 把本项目作为标准交付样板
- 复用 BRD / PRD / UI / Technical / QA / Release 全套结构
- 用模板目录支持下一次项目快速启动

---

## 一句话管理层结论

本项目已经从“单次研究脚本”升级为“可被团队复用、可持续刷新、可支撑决策的需求情报系统雏形”，并具备继续生产化的基础。
