# 04 · Pmax- 切 MAX_CONVERSION_VALUE（纯 value bidding，不加 tROAS）

**目标**：把 Pmax- 的 bidding 策略从 `Maximize conversions`（或 `Target CPA`）改成 **`Maximize conversion value`**，让 Google Ads 优化"拿到多少 $"，而不是"拿到多少单"。**不要一上来就加 tROAS** —— 先让系统自由跑 7-14 天把真实 value 学稳，再考虑加上 tROAS=3.0 做下限保护。

**预期效果**：
- Ads 开始学"有钱的用户"而不是"会点击的用户" · 按真实成交金额优化
- 理论上 ROAS 应该从 3.41 → 4.0-4.5（+15-30%）· 保守估计
- 对代购业务特别合适 —— 你的客单差距大（$50 vs $400 都有），value 优化会偏向大单用户

**风险**：中低 · 会进学习期 7-14 天 · 期间数据波动
- 如果学习期内 ROAS 低于 1.5 连续 3 天，回滚到 `Maximize conversions` 或回到 tCPA $13（见 01 手册）

**预计时长**：10 分钟

---

## 🧠 先做这个决策（❗必看）

**你今天在哪一步？**

| 你现在的状态 | 我的建议 |
|---|---|
| A. **还没改 01 tCPA $13** | ✅ **直接跳过 01，做 04**（value bidding 更 align 你真正关心的"赚多少钱"）|
| B. **01 改完不到 24 小时** | ⚠️ 先停，观察 tCPA 学习期 3 天 · 04 先缓着 |
| C. **01 改完 3+ 天但 ROAS 不稳** | ✅ 切 04 废掉 tCPA（value-based 比 CPA-based 学得更快）|
| D. **01 改完 1+ 周且 ROAS 稳 > 3** | 🚫 不切，保留 01 |

如果你是状态 A 或 C → 继续往下做手册。如果是 B 或 D → 今天不用做这个，本周做别的（02/03）。

**为什么现在能切 value bidding**（Day 27 晚的新发现）：

- 之前 block 切 value-based 的理由是"Ads 看到的 value 不准"
- Day 27 晚打通 GA4 Data API 后验证：**Ads 侧 value $1,218 vs Metabase 真实 $1,107 = 1.1× 差**（可接受）
- 原因：Ads 原生会过滤掉没带 transaction_id 的 purchase event，自动帮我们屏蔽 GA4 侧 65% 的噪声
- 所以 **value-based bidding 可以用** · 不必等 GTM 修

---

## 🎯 开始前确认（2 分钟）

1. 登录 Google Ads，确认右上角账户 **FISHGOO / 157-311-3113**
2. 确认 Pmax- campaign 还 Enabled（Campaigns 列表筛选 Enabled）
3. 如果你刚做完 01 (tCPA) 不到 24 小时 · 别做这个 · 回去等学习期

---

## 🗺️ 路径

```
左侧菜单「Campaigns」
  → 点 Pmax-
  → 左侧菜单「Settings」
  → 找到「Bidding」栏
  → 点「Change bid strategy」（更改出价策略）或铅笔 icon
```

---

## 📝 具体改动

### 在 Bidding 设置页面

1. **Bid strategy 下拉** → 当前显示 `Maximize conversions` 或 `Target CPA`（如果你做过 01）
2. 下拉 → 选 **`Maximize conversion value`**（最大化转化价值）
3. ⚠️ **下面会弹出一个 "Set a target ROAS" 选项 · 不要填 · 留空 / 不勾选**
   - 为什么不填：tROAS 对小预算账户太紧 · Google 会"不敢出价"
   - 正确节奏：先让 Maximize conversion value 自由跑 7-14 天 · 数据稳了再加 tROAS
4. 勾选 **"I understand the bid strategy change may require a learning period"**（确认学习期）
5. 点 **「Save」** 保存

### 特别提醒

- 如果 Google Ads UI 弹警告 "No conversion value data in last 30 days" → 说明你 conversion action 的 value 字段没数据（不太可能，Day 27 审计看到有 $1,218）
- 如果弹警告 "Insufficient data for value-based bidding" → 回到 `Maximize conversions`，告诉 Claude 再决策

---

## ✅ 验证改成功了

保存后：

- Pmax- 的 Settings 页面 `Bidding` 区显示 **`Maximize conversion value`**（没有 target ROAS 数字）
- 顶部出现黄色提示条："Your campaign is in learning period for approximately 7-14 days"（正常）
- Campaign primary status 可能短暂变成 "Learning" · 这是预期

---

## 📊 学习期 1-2 周观察重点

**前 3 天**（4/22-4/24）：
- 数据会非线性 · 每日 cost / clicks / conversions 波动大 · 别乱动
- 看「当前驾驶舱」Tab 的「真实 ROAS 日报」· 单日 ROAS 不是决策依据
- **不要再改 bid strategy**

**4-7 天**（4/25-4/28）：
- 看 7 日滚动 ROAS（不是单日）· 如果连续 3 天 ROAS < 1.5，说明系统学偏了
- 如果真出现 ROAS 连续 3 天 < 1.5 · 不要慌 · 给我截图，我判断是否回滚

**7-14 天后**（4/29-5/5）：
- 7 日滚动 ROAS 稳定 · 这时候才能判断 Pmax 表现
- 如果 ROAS > 3 稳定 → 考虑加 tROAS=3.0 做下限保护（那是手册 04b，下次写）
- 如果 ROAS 在 2-3 区间 → 保持现状 · 别急着加 tROAS
- 如果 ROAS < 2 → 回滚到 01 tCPA 或手动调

---

## ❌ 出问题了怎么办

### 情况 1：弹 "Insufficient conversion value data"

Google 说你账户最近 value 数据不够。

**解决**：
- 取消这次切换（点"Cancel"）
- 保持当前 bid strategy 不变
- 告诉 Claude："04 切不动，提示 Insufficient value data" · 我帮你查 conversion action 配置

### 情况 2：切完 24 小时 · 看起来"不跑了"

正常。Pmax 切 bid strategy 头 24-48 小时可能 cost 骤降 50-80% · 这是 Google 在收缩出价观察。

**不要**：以为是自己改坏了然后切回去。切回去会重置学习期，更糟。

**要做**：保持原样等 72 小时 · 如果第 3 天仍然 0 spend，截图发我排查。

### 情况 3：切完 1 周 · cost 起来了但 conversions 0

可能是 Google 学偏了，把量拉给低 value 人群。

**做法**：保持不动再观察 2-3 天 · 第 10 天仍 0 转化 → 回滚（下拉选回 `Maximize conversions`）。

### 情况 4：切完 1 周 · ROAS 好 · 想加预算

**不要加**。让学习期完整跑完 14 天。加预算会再次触发学习期，前功尽弃。

---

## 📌 做完告诉 Claude

**截图 Pmax- Settings 页面的 Bidding 栏**（显示 `Maximize conversion value`，没有 target ROAS 数字）发过来，我会：
- 更新 todo list
- 帮你在看板加一条"04 已改 · learning 进行中"
- 从 4/22 开始每天看一眼 learning 健康度，第 7 天给你中期复盘

---

## 📎 相关
- 如果你是状态 A / C：建议顺手把 02（Presence）+ 03（brand exclusion）也做了 · 一共 25 分钟
- 如果你状态 B / D：这周主做 02 + 03 · 04 下周决定
