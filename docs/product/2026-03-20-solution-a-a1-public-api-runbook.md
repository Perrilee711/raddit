# Demand Intelligence Platform

## A1：公网 API 上线 Runbook

日期：2026-03-20

---

## 目标

把当前本地 API 服务部署到一台 Ubuntu 服务器，使 Vercel 前端可以通过公网域名访问：

- `https://api.fishgoo.com`

---

## 1. 服务器准备

建议环境：

- Ubuntu 22.04
- 2C4G
- 开放 80 / 443

安装依赖：

```bash
sudo apt update
sudo apt install -y nginx python3
```

---

## 2. 拉取项目

```bash
cd /opt
sudo git clone https://github.com/Perrilee711/raddit.git demand-intelligence
sudo chown -R $USER:$USER /opt/demand-intelligence
cd /opt/demand-intelligence
```

---

## 3. 启动脚本

项目已内置：

- [scripts/start_public_api.sh](/Users/perrilee/Desktop/探索/raddit/scripts/start_public_api.sh)

它默认会：

- 绑定 `0.0.0.0:8765`
- 开启 `cookie secure`
- 允许 Vercel 前端跨域访问

手工测试：

```bash
cd /opt/demand-intelligence
chmod +x scripts/start_public_api.sh
./scripts/start_public_api.sh
```

检查：

```bash
curl http://127.0.0.1:8765/api/health
```

---

## 4. systemd 常驻

项目已提供模板：

- [deploy/solution-a/demand-intelligence-api.service](/Users/perrilee/Desktop/探索/raddit/deploy/solution-a/demand-intelligence-api.service)

安装：

```bash
sudo cp deploy/solution-a/demand-intelligence-api.service /etc/systemd/system/demand-intelligence-api.service
sudo systemctl daemon-reload
sudo systemctl enable demand-intelligence-api
sudo systemctl start demand-intelligence-api
sudo systemctl status demand-intelligence-api
```

---

## 5. Nginx 反代

模板：

- [deploy/solution-a/nginx-api.conf](/Users/perrilee/Desktop/探索/raddit/deploy/solution-a/nginx-api.conf)

安装：

```bash
sudo cp deploy/solution-a/nginx-api.conf /etc/nginx/sites-available/demand-intelligence-api
sudo ln -s /etc/nginx/sites-available/demand-intelligence-api /etc/nginx/sites-enabled/demand-intelligence-api
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. 前端连接公网 API

Vercel 前端这边使用：

- [docs/product/runtime-config.js](/Users/perrilee/Desktop/探索/raddit/docs/product/runtime-config.js)

把它改成：

```js
window.__DEMAND_INTEL_CONFIG__ = {
  API_BASE_URL: "https://api.fishgoo.com",
};
```

然后重新部署前端。

---

## 7. 验收清单

### API

```bash
curl https://api.fishgoo.com/api/health
curl https://api.fishgoo.com/api/studies
```

### 前端

打开：

- `https://your-app-domain/mvp-app.html`

确认：

- 不再请求 `127.0.0.1`
- 登录成功
- Study 列表可加载
- Dashboard 可加载

---

## 8. 当前边界

A1 完成后：

- 同事可以通过公网前端使用系统
- 公网 API 可稳定提供 Dashboard / Studies / Jobs / Weekly Brief

但 Reddit 浏览器采集链路还没有迁云，仍需要：

- 一台 Mac Worker

这部分属于方案 A 的下一阶段。

