# Demand Intelligence Platform

## 测试方案、验收口径与当前结果

日期：2026-03-21  
版本：v1.0

---

## 1. 测试目标

本项目测试不是只看“页面能不能打开”，而是验证以下 5 条闭环是否成立：

1. 创建 Study
2. 生成和执行任务
3. Mac Worker 认领并执行抓取
4. 结果回写到 API 与前端
5. 出问题时可以停止、重试和观察

---

## 2. 测试范围

### 2.1 功能测试

- Study Setup
- Dashboard
- Operations
- Weekly Brief
- 停止当前爬取
- 失败任务重试

### 2.2 集成测试

- API 与前端
- API 与 Mac Worker
- Mac Worker 与 Chrome 抓取链路

### 2.3 运维测试

- health 检查
- LaunchAgent 状态
- Worker 在线/离线
- runtime alerts

### 2.4 发布测试

- GitHub 推送
- Vercel 自动发布
- 腾讯云 API 重启与回归

---

## 3. 核心验收用例

### 用例 1：系统可访问

预期：

- 工作台能打开
- health 正常

验收点：

- [`http://43.162.90.26/`](http://43.162.90.26/)
- [`http://43.162.90.26/api/health`](http://43.162.90.26/api/health)
- [`https://skill-deploy-jr9bh4v87v.vercel.app`](https://skill-deploy-jr9bh4v87v.vercel.app)

当前结果：通过

### 用例 2：Study 可创建

预期：

- Study Setup 可输入业务信息
- 系统自动推荐关键词
- 可创建 study 并首跑

当前结果：通过

### 用例 3：任务可入队

预期：

- browser / hot_threads / adaptive 能进入队列
- Operations 可看到状态

当前结果：通过

### 用例 4：Mac Worker 可认领任务

预期：

- cloud API 发出的 mac_worker 任务被认领
- job 进入 running

当前结果：通过

### 用例 5：结果可回写

预期：

- discover / harvest 结果进入 raw/entity/payload
- Dashboard 刷新

当前结果：通过

### 用例 6：停止当前爬取

预期：

- 点击 stop 后，任务进入 canceling/canceled
- Worker 主动停止子进程
- 前端有即时反馈

当前结果：通过

### 用例 7：失败重试

预期：

- 失败任务可重跑
- Dashboard 有异常与重试提示

当前结果：通过

### 用例 8：Worker 在线状态可感知

预期：

- 页面能显示 connected / stale / offline
- 状态脚本可清晰输出当前状态

当前结果：通过

---

## 4. 当前已做验证

### 4.1 本地

- Python 关键脚本编译检查
- LaunchAgent 状态检查
- Mac Worker 状态检查
- stop / retry / queue 逻辑验证

### 4.2 公网

- API health 验证
- jobs 验证
- browser 任务入队与 stop 验证
- 远程部署验证

### 4.3 前端

- Vercel 页面可访问
- 工作台页面可访问
- runtime alert / worker card / stop 按钮已接通

---

## 5. 当前验收结论

### 已通过

- 基础访问
- Study 创建
- 任务调度
- Mac Worker 联通
- Dashboard 渲染
- stop crawl
- 运维状态可视化

### 当前已知边界

1. Reddit 浏览器抓取依赖 Mac 环境
2. 公网工作台当前是 HTTP，不是 HTTPS
3. Vercel 更适合展示壳，不是当前完整主入口
4. 数据存储仍偏文件型，而不是数据库型

---

## 6. 上线验收门槛

本项目当前可以视为“第一阶段交付完成”，原因是：

- 团队可访问
- 任务能跑
- 结果能回写
- Worker 有状态
- 异常可观测
- 任务可停止

如果要进入“下一阶段正式生产化”，则需要新增门槛：

- HTTPS API
- 更正式认证
- 数据库
- 更稳的采集执行环境

---

## 7. 回归测试建议

每次重大改动后，至少回归以下 8 项：

1. 打开工作台
2. `/api/health`
3. `/api/studies`
4. 新建 Study
5. 发起 browser 任务
6. stop 当前任务
7. retry 失败任务
8. 查看 Worker 状态卡

---

## 8. 建议的后续测试增强

1. 自动化接口烟测脚本
2. 任务状态回归脚本
3. 前端交互 smoke checklist
4. 部署后验收 checklist
