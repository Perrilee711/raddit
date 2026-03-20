# Solution A / A2：Mac Worker 联通 Runbook

这一步的目标不是把浏览器抓取迁云，而是把“公网 API + 本地 Mac 采集器”真正打通。

## 1. 架构

- 公网 API：运行在云服务器，负责 `study / jobs / aggregates / publish`
- Mac Worker：运行在本机或专用 Mac mini，负责：
  - `discover`
  - `harvest`
  - `refresh_hot`

浏览器阶段不再由云服务器执行。

## 2. 关键文件

- Worker 配置：
  - [config/workers.json](/Users/perrilee/Desktop/探索/raddit/config/workers.json)
- Worker 主程序：
  - [scripts/mac_worker_agent.py](/Users/perrilee/Desktop/探索/raddit/scripts/mac_worker_agent.py)
- 启动脚本：
  - [scripts/start_mac_worker_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/start_mac_worker_agent.sh)
- 安装 LaunchAgent：
  - [scripts/install_mac_worker_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/install_mac_worker_launch_agent.sh)
- 查看状态：
  - [scripts/status_mac_worker_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/status_mac_worker_launch_agent.sh)

## 3. Worker Token

默认 worker：

- `id`: `fishgoo-mac-worker`
- `token`: `fishgoo-mac-worker-token`

如果你后面要加第二台 Mac，可以继续在 `config/workers.json` 里追加。

## 4. 手动启动

```bash
cd '/Users/perrilee/Desktop/探索/raddit'
/usr/bin/python3 scripts/mac_worker_agent.py \
  --api-base-url http://43.162.90.26 \
  --worker-token fishgoo-mac-worker-token \
  --worker-id fishgoo-mac-worker \
  --continue-on-error
```

## 5. 常驻启动

```bash
cd '/Users/perrilee/Desktop/探索/raddit'
./scripts/install_mac_worker_launch_agent.sh
./scripts/status_mac_worker_launch_agent.sh
```

## 6. 运行前提

Mac Worker 要稳定工作，需要满足：

1. Mac 保持登录
2. 不要休眠
3. Chrome 可访问 Reddit
4. 已开启：
   - `View -> Developer -> Allow JavaScript from Apple Events`

## 7. 数据流

1. 用户在公网前端创建或刷新 study
2. 公网 API 入队 `browser` 或 `hot_threads`
3. 云端 job 进入 `discover / harvest / refresh_hot`
4. Mac Worker 调 `POST /api/worker/claim` 领取任务
5. Mac 本地跑 Chrome 采集
6. Mac 调 `POST /api/worker/jobs/:id/complete`
7. 公网 API 入队后续：
   - `rebuild_aggregates`
   - `publish_brief`

## 8. 验证标准

当 A2 正常工作时，应看到：

1. `Operations` 里 `discover / harvest / refresh_hot` 的执行方式显示为 `Mac Worker`
2. job 详情出现 `执行节点`
3. 云端 API 不再尝试直接在 Linux 上跑浏览器阶段
4. 完成一次 `browser` 后，Study 的：
   - `thread_count`
   - `comment_count`
   - `comment_coverage`
   会更新
