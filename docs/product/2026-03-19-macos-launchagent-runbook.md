# Demand Intelligence Mac 常驻运行方案

这套系统在 Mac 上要想“自动运转”，推荐用 `LaunchAgent`，而不是 `LaunchDaemon`。

原因很简单：

- 当前 `browser / hot_threads` 模式依赖本机 `Google Chrome + AppleScript`
- 这类任务必须运行在**已登录的图形会话**里
- 所以应该用 **LaunchAgent（用户态）**，而不是 **LaunchDaemon（系统态）**

## 你会得到什么

这套方案已经配好了 5 个脚本：

- [start_demand_intelligence_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/start_demand_intelligence_agent.sh)
- [install_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/install_launch_agent.sh)
- [uninstall_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/uninstall_launch_agent.sh)
- [status_launch_agent.sh](/Users/perrilee/Desktop/探索/raddit/scripts/status_launch_agent.sh)
- [configure_study_schedule.sh](/Users/perrilee/Desktop/探索/raddit/scripts/configure_study_schedule.sh)

## 它是怎么自动跑的

1. `LaunchAgent` 开机登录后自动拉起 [demand_intelligence_server.py](/Users/perrilee/Desktop/探索/raddit/scripts/demand_intelligence_server.py)
2. 服务内部会自动启动：
   - `worker_loop`
   - `scheduler_loop`
3. `scheduler_loop` 根据 study 的 schedule 到点自动 enqueue job
4. `worker_loop` 会按队列优先级执行阶段化 pipeline
5. 每次运行结束后自动更新：
   - `data/studies/*.json`
   - `data/entities/studies/*`
   - `docs/product/data/studies/*payload.json`

## 第一次安装

```bash
cd '/Users/perrilee/Desktop/探索/raddit'
chmod +x scripts/start_demand_intelligence_agent.sh \
  scripts/install_launch_agent.sh \
  scripts/uninstall_launch_agent.sh \
  scripts/status_launch_agent.sh \
  scripts/configure_study_schedule.sh

./scripts/install_launch_agent.sh
```

安装完成后，服务会自动常驻，并且登录后自动恢复。

如果你的仓库放在 `Desktop` 下，安装脚本会自动把运行时副本同步到：

```text
~/raddit-service
```

这是为了避开 macOS 对 `Desktop` 路径下 LaunchAgent/守护脚本的权限限制。

## 给某个 study 打开自动刷新

例如给 `fishgoo-us-dropshipping` 开启 24 小时一轮的自适应调度：

```bash
cd '/Users/perrilee/Desktop/探索/raddit'
./scripts/configure_study_schedule.sh fishgoo-us-dropshipping 24 adaptive true
```

参数顺序是：

```text
configure_study_schedule.sh <study_id> <interval_hours> <mode> <start_now>
```

例子：

- `./scripts/configure_study_schedule.sh fishgoo-us-dropshipping 24 adaptive true`
- `./scripts/configure_study_schedule.sh shopify-3pl 12 hot_threads true`

## 查看运行状态

```bash
cd '/Users/perrilee/Desktop/探索/raddit'
./scripts/status_launch_agent.sh
```

它会输出：

- LaunchAgent 是否已加载
- 实际运行目录
- 实际 stderr 日志路径
- `launchctl print` 状态
- `127.0.0.1:8765` 是否响应
- 最近错误日志

## 卸载

```bash
cd '/Users/perrilee/Desktop/探索/raddit'
./scripts/uninstall_launch_agent.sh
```

## 生产注意事项

要让 `browser / hot_threads` 真正自动跑，Mac 还需要满足这几个条件：

1. 用户必须保持登录状态
2. 机器不能睡眠
3. Chrome 必须允许：
   - `View -> Developer -> Allow JavaScript from Apple Events`
4. 第一次运行时要允许系统自动化权限：
   - `osascript / Python / shell -> Google Chrome`

## 现实边界

这套方案已经足够让系统在 Mac 本机上“常驻 + 定时自动跑”，但它仍然属于：

- **私有化本机运行**
- **依赖图形会话**
- **浏览器采集优先**

如果未来要做真正 24/7 的线上产品，下一步应该把：

- 队列
- 调度
- 浏览器采集
- 数据刷新

迁移到一台持续在线、可控的专用机器或服务上。
