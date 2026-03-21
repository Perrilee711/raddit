# Demand Intelligence Platform

## 发布、上线与交接文档

日期：2026-03-21  
版本：v1.0

---

## 1. 本次交付的正式入口

### 代码仓库

- GitHub：[`https://github.com/Perrilee711/raddit`](https://github.com/Perrilee711/raddit)

### 在线地址

- 团队工作台：[`http://43.162.90.26/`](http://43.162.90.26/)
- API 健康检查：[`http://43.162.90.26/api/health`](http://43.162.90.26/api/health)
- Vercel 展示版：[`https://skill-deploy-jr9bh4v87v.vercel.app`](https://skill-deploy-jr9bh4v87v.vercel.app)

---

## 2. 谁应该用哪个地址

### 团队真实操作

请使用：

- [`http://43.162.90.26/`](http://43.162.90.26/)

原因：

- 这里接的是公网 API
- 有真实队列、Study、Worker、stop、retry、runtime

### 对外展示或演示产品界面

请使用：

- [`https://skill-deploy-jr9bh4v87v.vercel.app`](https://skill-deploy-jr9bh4v87v.vercel.app)

---

## 3. 运行构成

### 公网 API 服务器

- 服务器：腾讯云
- 地址：`43.162.90.26`
- 应用目录：`/opt/demand-intelligence`

### Mac Worker

- 运行方式：LaunchAgent
- 标签：`com.fishgoo.demand-intelligence.mac-worker`

### 本机辅助服务

- 本机运行时根目录：`~/raddit-service`

---

## 4. 运维入口

### Mac 端状态

- 主服务状态：
  [status_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/status_launch_agent.sh)
- Worker 状态：
  [status_mac_worker_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/status_mac_worker_launch_agent.sh)

### 安装/重装脚本

- 主服务：
  [install_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/install_launch_agent.sh)
- Worker：
  [install_mac_worker_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/install_mac_worker_launch_agent.sh)

---

## 5. 团队日常操作说明

### 5.1 创建新研究任务

1. 打开工作台
2. 进入 `Study Setup`
3. 输入市场、客群、问题空间
4. 确认系统推荐关键词
5. 点击创建并首跑

### 5.2 刷新现有 Study

在 Dashboard 顶部可以手动刷新：

- seeded
- browser
- hot_threads
- adaptive

### 5.3 停止当前爬取

当当前 Study 正在执行浏览器抓取任务时：

- 点击 `停止当前爬取`
- 系统会切到 `停止中...`
- Worker 会停止对应任务

### 5.4 异常处理

优先查看：

- Dashboard 的 `异常与重试`
- Operations
- Worker 状态卡
- 本机 status 脚本

---

## 6. 当前交付边界

### 已交付

- 在线工作台
- Study 生命周期
- 评论驱动实体底座
- Mac Worker 联通
- stop / retry / alerts / runtime

### 暂未完全收口

- HTTPS API
- 正式域名
- 更强的鉴权与安全
- 数据库化持久层
- 无 Mac 依赖的全云采集器

---

## 7. 交接给下一位同事时，必须说明的事情

1. 这不是纯 Vercel 前端项目，真实可操作入口是 `43.162.90.26`
2. 浏览器抓取依赖 Mac Worker，不是腾讯云服务器本地抓
3. 如果 Mac 睡眠或 Chrome 权限异常，browser/hot_threads 会受影响
4. status 脚本是排查第一入口
5. stop 现在已经接通，不用再强杀整套系统

---

## 8. 推荐交接顺序

1. 讲清业务目标
2. 讲清产品入口
3. 讲清架构分工
4. 演示一次 Study 创建与 stop
5. 演示 Worker 状态排查
6. 交付本目录全部文档

---

## 9. 推荐的下一阶段工作

1. HTTPS + 正式 API 域名
2. 更正式登录与权限
3. 数据库存储
4. 更完整的告警与自动恢复
5. 更多数据源
