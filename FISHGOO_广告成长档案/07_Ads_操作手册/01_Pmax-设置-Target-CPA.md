# 01 · Pmax- 设置 Target CPA = $13

**目标**：把 Pmax- 的 bidding 策略从 `Maximize conversions` 改成 `Target CPA`（目标每次转化费用），值设为 **$13**。

**预期效果**：Google Ads 会自动把 CPA 压在 $13 以下 · 不会再疯狂加价追未必会支付的流量。

**风险**：低。任何时候都能改回来。

**预计时长**：10 分钟

**为什么是 $13**：真实 CPA = Ads $535 花费 / Metabase 36 真实支付订单 = **$14.86/单**（过去 13 天）· 设 $13 稍紧一点给系统压力 · 等系统学稳定后再看数据调。

---

## 🎯 开始前先做（2 分钟）

1. 打开浏览器，登录 Google Ads：<https://ads.google.com/>
2. 确认**右上角**显示的账户名是 **FISHGOO** 或客户 ID **157-311-3113**
3. 如果切到别的账户了，点账户切换器选回来

---

## 🗺️ 路径

进 Google Ads 后，按顺序点：

```
左侧菜单「Campaigns」(广告系列)
  → 点页面中间 Pmax- 这一行（不要点勾选框，点 campaign 名字蓝色链接）
  → 左侧菜单「Settings」(设置)
  → 找到「Bidding」(出价) 这一栏
  → 点「Change bid strategy」(更改出价策略) 或 蓝色铅笔 icon
```

---

## 📝 具体改动

在 bidding 设置页面：

1. **Bid strategy 下拉菜单** → 当前显示 `Maximize conversions`
2. 点下拉 → 选 **`Target CPA`**（目标每次转化费用）
3. **Set a target CPA** 弹出输入框 → 输入 **`13`**（不用加 $ 符号，会自动是 USD）
4. 勾选 **"I understand the bid strategy change may require a learning period"**（我理解切换 bid 策略需要学习期）
5. 点 **「Save」** 保存

---

## ✅ 验证改成功了

保存后你应该看到：

- Pmax- 的 Settings 页面 `Bidding` 区显示 **Target CPA · $13**
- 顶部可能出现黄色提示条："Your campaign is in learning period for approximately 7 days"（正常 · 说明设置生效了）
- Campaign primary status 可能短暂变成 "Learning"（学习中），7 天内稳定后自动变回 "Eligible"

---

## 📊 之后一周的观察重点

**设置 tCPA 后 Google Ads 要进入"学习期"约 7 天**。期间：

- 数据会比之前波动大（点击 / 转化 / 花费都可能非线性）
- 不要再改 bid strategy · 给系统时间学
- **每天早上开看板看「真实 ROAS 日报」** · 如果连续 3 天真实 ROAS 低于 1.5，说明 tCPA 13 可能太紧了（系统抢不到质量流量），可以下周再调到 15

---

## ❌ 出问题了怎么办

### 情况 1：保存时报错 "Insufficient conversion data"

Google Ads 在说这个 campaign 转化数太少，Target CPA 不建议现在切。

**解决办法**：
- 先退回 `Maximize conversions`（点一下 bid strategy 下拉切回去）
- 告诉 Claude："Target CPA 提示转化不够，怎么办" · 我给你备选（比如先改 max budget 或者改成 `Max conversion value` 保守用）

### 情况 2：找不到 Pmax- campaign

在 Campaigns 列表里筛选 Status = `Enabled`（已启用），再看还有没有。

如果真的没有 —— 可能 campaign 名字变了，找 Claude 帮你重新定位。

### 情况 3：设置保存后找不到 Bidding 栏

Google Ads UI 偶尔会重新排版。用顶部搜索框（小放大镜 icon）搜 "bidding" 或 "bid strategy"，会直接跳到对应设置。

---

## 📌 改完以后告诉 Claude

**截图 Pmax- Settings 页面的 Bidding 栏**（显示 Target CPA · $13）发过来，我帮你合上 todo、更新 Day 审计里的 "本周已做" 清单。
