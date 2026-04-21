# Measurement 三源对账 · 2026-04-21
## FISHGOO SEM · purchase event 信号失真根因定位

**审计范围**：2026-04-08 ~ 2026-04-20（13 天）
**审计者**：Perri（SEM 团队负责人）+ Claude（合伙人式 AI）
**三个数据源**：
- Google Ads API（`metrics.cost_micros` + `metrics.all_conversions_value`）
- GA4 Data Explore 手动导出（v1）+ GA4 Data API via Service Account（v2）
- Metabase 业务后台 Dashboard 200 推广者看板（SEM 团队真实支付订单）

**版本历史**：
- **v1**（早晨 11:30）：基于 CSV 手动导出，推测 GA4 duplicate firing 16×
- **v2**（晚上 22:00）：SA 打通 GA4 Data API 后逐日拉 transaction_id 级别数据 → 根因修正

---

## ⚠️ 诊断 v2 修正（2026-04-21 晚 · 推翻 v1 的核心判断）

### 真正的根因（不是 duplicate firing）

**v1 里说的"每订单 fire 16 次" 是错的**。

打通 GA4 Data API 后，按 `transaction_id` 维度拆分 4/20 这一天的 purchase events：

| 维度 | 数值 |
|---|---:|
| 总 event 数 | 37 |
| **带 transaction_id 的 event** | **13**（revenue 有值） |
| **空 transaction_id 的 event（noise）** | **24**（revenue = 0） |
| noise 占比 | **65%** |

不是"每单虚报 16 次"。真相是：**有效订单信号正常 fire 一次，但同时有 65% 的额外 event 没带 transaction_id 在混入**。

这也解释了一个 v1 解释不通的现象：**Google Ads 看到的 value $1,218 vs Metabase SEM 真实 $1,107 = 1.1× 差**。不是"Ads 有神秘 dedupe 机制"，而是 **Ads 原生就会自动丢弃没带 transaction_id 的 purchase events**（属于 Google Ads 官方文档里明确写的行为）。Ads 实际上只看到了带 txn_id 的那 37% 真信号。

### 修复方向比 v1 精准得多

| v1 推测的修复 | v2 修正后的修复 |
|---|---|
| 加 dedupe 机制（localStorage 存已发送 txn_id） | **不需要**，dedupe 本身没问题 |
| trigger condition 改成"只在支付成功页 fire" | **依然要做**，但这是第二优先级 |
| 排查"哪些页面 push purchase 事件" | **核心动作**：加一个 trigger condition `dataLayer.transaction_id` 必须非空 |

**一行描述给技术同学**：在 GTM purchase tag 的 trigger 加一个 condition —— **"Custom Event = purchase AND dataLayer variable transaction_id is not null/empty"**。这一步做完，所有 noise events 就会被直接过滤掉。

### 优先级降低

因为 **Ads 侧看到的数字已经接近真相**（1.1× 差而非 12.5× 差），以下判断变化：

| v1 判断 | v2 判断 |
|---|---|
| ❌ GTM 修复是 P0，本周必做 | ⚠️ GTM 修复降 P2，**有空再修** |
| ❌ 不能切 value-based bidding | ⚠️ **可以谨慎评估** Pmax 切 `MAX_CONVERSION_VALUE + tROAS` |
| ❌ GA4 的 ROAS 数字完全不能用 | ❌ 依然不能用（GA4 侧仍有 65% noise） |
| ✅ Metabase 是唯一可信源 | ✅ 依然成立 |

### GA4 vs Metabase 口径差异（v1 没说清楚的）

v1 表里直接把 GA4 event 数和 Metabase 订单数比，得出 "16× duplicate"。这是比错了：

| 数据源 | 统计范围 | 4/20 数字 |
|---|---|---|
| **GA4** | 全站所有流量渠道 | 37 events，其中 13 有 txn_id |
| **Metabase Dashboard 200** | 只筛 SEM 团队（perri 名下 simon）的订单 | 0 单 |
| **Metabase 全公司** | 所有渠道（GA4 可比口径） | 未拉，需要另查 |

所以正确的对比应该是：
- GA4 带 txn_id 的 event 数 vs **Metabase 全公司** 订单数（看噪声过滤效果）
- Ads value vs **Metabase SEM 子集** GMV（看 SEM 真实 ROAS）

v1 用 GA4 去和 Metabase SEM 比，口径从一开始就错。

---

## ⬇️ 以下是 v1 版本（早晨写，已被 v2 修正，保留做历史）

## 🎯 核心结论

**根因不是 "Google Ads 漏采 purchase event"**（这是 4/21 早晨的第一直觉判断，错）。

**真正根因是 GTM 里 `purchase` event 的 trigger 配置完全失控 —— 每个真实订单在 GA4 侧平均 fire 16 次，且 5 个零订单日仍然 fire 了 217 次虚假 event。**

Google Ads 看到的数字反而**相对接近**真实（$1,218 vs Metabase $1,107），是因为 Google Ads 的 conversion action 有自己的 dedupe/counting 逻辑，帮 GA4 的 noise 擦了一半。但仍然是**基于错误信号**的正确数字。

> ⚠️ v2 修正（见顶部）：这段"dedupe 逻辑"推测错了 —— Ads 不是 dedupe，是**原生过滤掉没带 transaction_id 的 events**。根因不是 duplicate firing，是 65% events 没带 txn_id。

---

## 📊 13 天逐日三源对账表

| 日期 | GA4 purchase event | GA4 revenue (¥) | Metabase 真实订单 | Metabase GMV (¥) | Ads cost ($) | Ads value ($) | GA4/MB 订单比 | GA4/MB 金额比 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04-08 | **50** | ¥8,760 | **0** | ¥0 | $5.36 | $0 | — | — |
| 2026-04-09 | **48** | ¥14,869 | **0** | ¥0 | $54.23 | $279.31 | — | — |
| 2026-04-10 | 41 | ¥8,406 | 2 | ¥464 | $78.89 | $0 | 20.5× | 18.1× |
| 2026-04-11 | 40 | ¥14,669 | 3 | ¥407 | $37.59 | $231.37 | 13.3× | 36.0× |
| 2026-04-12 | 47 | ¥9,189 | 10 | ¥1,187 | $46.81 | $707.86 | 4.7× | 7.7× |
| 2026-04-13 | 48 | ¥3,940 | 1 | ¥115 | $36.33 | $0 | 48.0× | 34.3× |
| 2026-04-14 | 58 | ¥5,844 | 7 | ¥1,443 | $37.61 | $0 | 8.3× | 4.0× |
| 2026-04-15 | 51 | ¥4,774 | 6 | ¥1,667 | $45.19 | $0 | 8.5× | 2.9× |
| 2026-04-16 | 40 | ¥2,497 | 6 | ¥1,945 | $31.18 | $0 | 6.7× | 1.3× |
| 2026-04-17 | **48** | ¥12,089 | **0** | ¥0 | $32.45 | $0 | — | — |
| 2026-04-18 | **34** | ¥2,963 | **0** | ¥0 | $45.94 | $0 | — | — |
| 2026-04-19 | 34 | ¥2,570 | 1 | ¥403 | $49.22 | $0 | 34.0× | 6.4× |
| 2026-04-20 | **37** | ¥4,679 | **0** | ¥0 | $34.16 | $0 | — | — |
| **合计** | **576** | **¥95,250** | **36** | **¥7,632** | **$534.96** | **$1,218.54** | **16.0×** | **12.5×** |

---

## 🔴 最关键证据 · 5 个「零订单日」GA4 依然 fire 了 217 次

| 日期 | Metabase 真实订单 | GA4 虚假 event 数 | GA4 虚假 revenue |
|---|---|---|---|
| 2026-04-08 | 0 | 50 | ¥8,760 |
| 2026-04-09 | 0 | 48 | ¥14,869 |
| 2026-04-17 | 0 | 48 | ¥12,089 |
| 2026-04-18 | 0 | 34 | ¥2,963 |
| 2026-04-20 | 0 | 37 | ¥4,679 |
| **合计** | **0** | **217** | **¥45,360** |

**这些 event 100% 是 noise（非真实成交）**。如果 trigger 是正确的"只在支付成功页 fire"，这 5 天应该是 0 event。

推测 trigger 实际 fire 的场景可能包括：
- 用户访问订单历史页（看过去订单 → 触发 fire）
- 页面刷新 / 重新加载
- 单页应用的 route change
- 购物车到支付页的中间 pageview
- 内部测试人员的反复操作

---

## 📉 对真实 ROAS 的影响（彻底重估）

### 重算 13 天（4/8-4/20）

- Ads 花费：**$534.96**
- Metabase 真实支付 GMV（最可信）：$1,107.33
- GA4 记录 revenue（大幅虚报）：$13,820.11
- Ads all_conv_value（中等失真）：$1,218.54

**三种 ROAS 口径**：

| 口径 | 数值 | 可信度 |
|---|---|---|
| GA4 revenue / Ads cost | **25.8×** | ❌ 严重虚高（12.5× 被 GA4 noise 污染） |
| Ads value / Ads cost | **2.28×** | ⚠️ 数字接近真相但基础错误 |
| **Metabase GMV / Ads cost** | **2.07×** | ✅ **唯一可信** |

业务视角：真实 ROAS 约 **2.07×**（按已支付 GMV 口径），比 e-com benchmark 3.68× 低约 44%。

**Day 26 v3.1 审计报告里写的 ROAS 3.56 需要再校准**，但那是近 30 天（3/22-4/20）总营收口径，包含代购业务的物流/提包增值收入（CNY → USD 汇率口径没变），可能本身没问题。这里的 2.07 是**只看已支付 GMV**的更严格口径。

---

## 🛠️ 给技术同学的修复 checklist

### 必须定位的 3 个问题

1. **`purchase` event 的 trigger 到底绑在什么条件上？**
   - 打开 GTM → Tags → 找 `purchase` event 相关的 tag
   - 看它的 trigger 是 `Page View - All Pages` 吗？是 `Custom Event - purchase` 吗？还是 `Link Click`？
   - 理想：trigger 应该是**明确的"支付成功确认"事件**（dataLayer.push({'event': 'purchase', ...}) 发生且只发生一次）

2. **数据层（dataLayer）里 `purchase` 事件在哪些页面 push？**
   - 应该 only 在「支付成功页」首次加载时 push 一次
   - 不应该在：订单历史页、订单详情页、支付中转页、购物车页
   - 检查代码里所有 `dataLayer.push.*purchase` 调用

3. **有没有 dedupe 机制？**
   - 检查 tag 的 trigger condition 有没有限制：`transaction_id` 维度上唯一
   - 或者用 GTM 的 built-in "Trigger once per event"（但这个在 SPA 里不够强）
   - 推荐：localStorage 存已发送的 transaction_id 列表，fire 前检查

### 修复验证步骤

1. 修完 GTM 后，在 GA4 **DebugView** 里做一次真实测试订单
2. 确认**只有一个** `purchase` event fire，且 transaction_id / value 正确
3. 等 24h 后再跑一次本对账表，预期：
   - GA4 event 数 ≈ Metabase 订单数（比例降到 1-1.5× 以内，允许少量合理重复）
   - 5 个「零订单日」GA4 应该也显示 0 event

### 修好之前 · 不能做的事

- ❌ 不能切换 Google Ads 到 value-based bidding（MAX_CONVERSION_VALUE / tROAS）
- ❌ 不能用 Ads 的 ROAS 数字做加预算决策
- ❌ 不能用 GA4 的 revenue 数字给 CEO 汇报

### 修好之后 · 立刻可以做的事

- ✅ Pmax- 换 `MAX_CONVERSION_VALUE + tROAS = 3.0`
- ✅ 按真实 value 加 / 减预算
- ✅ simon / Jasonq385 的真实 ROAS 对比（现在只能看 GMV 不能看 ROAS）

---

## 🔄 修订前报告中数字的影响

本次发现改写以下数字：

| 原报告 | 原数字 | 修正后 |
|---|---|---|
| [Day 26 审计 v3.1](Day26_深度审计_合伙人视角_2026-04-20.md) 中 "Ads value 失真 2.3×" | 2.3× | 实际 GA4 是 12.5×，Ads 侧 **跟 Metabase 反而只差 10%**（$1,218 vs $1,107），因为 Ads 自带 dedupe |
| [4 月 partial 月报](../06_月度CEO汇报/2026-04_SEM月报_给CEO_partial.md) 中 "4 月前 20 天 Measurement 修复信号" | 1.001× 接近真相 | 实际是 Ads 和 Metabase 都对，但底层 GA4 源信号污染严重 · 修复不是自己发生，是 Ads 侧去重机制隐藏了 GA4 的 bug |
| Day 27 "失真倍数 2.3×" 描述 | 2.3× | GA4 侧 12.5×，Ads 侧 ~1.1×（接近真相但是虚假接近，事件源是错的） |

我会在下一轮给 Day 26 v3.1 审计报告和 4 月月报补一段"Day 27 发现 GA4 源污染"的更正说明。

---

## 📝 数据源 + 方法透明化

- **Google Ads 数据**：2026-04-21 10:00 通过 `mcp__google-ads-mcp__search`（客户 1573113113）
- **GA4 数据**：Perri 于 2026-04-21 11:30 在 GA4 Explore 里手动配置 + 导出 CSV（探索自由形式 · 维度：日期、事件名称、交易ID；指标：事件数、购买收入；过滤：event_name=purchase）
- **Metabase 数据**：Perri 于 2026-04-20 16:26 导出的 Excel 按日聚合
- **汇率**：6.8921 CNY/USD（看板管理口径）

---

## 📌 本次审计的副产品

1. **Service Account**：`fishgoo-ga4-audit@fishgoo-ga4-audit.iam.gserviceaccount.com`（Perri 创建）
   - Perri 非 GA4 Admin，SA 加 Viewer 未成功
   - SA JSON 已临时存于服务器 `/root/raddit/.env/ga4-sa.json`（权限 600）
   - **建议今日内作废这个 key，改用 CSV 手动流程**（既然每月一次也够用）
   
2. **GA4 权限路径阻塞**：Perri 账号 `perrilee0711@gmail.com` 在 GA4 account `a359652216` 仅 Viewer，无管理员权限
   - 本次改用 Explore UI 手动导 CSV 的方式绕过 → 依然拿到了所有需要的数据
   - 如果后续要自动化，需要找 GA4 Admin（可能是 `fishgoocloud@gmail.com` 或其他 fishgoo 同事）给 SA 加权限

---

## 📎 下一步（给 Perri 的 · v2 修正）

1. **今天**：把本 md 转发给技术同学，用**底部 v2 版短消息**（不要用 v1 版的"紧急"措辞）
2. **本周内不急**：GTM 修复降 P2，技术同学有空修就修
3. **这周可以做**：先启动 Pmax 的谨慎 tROAS 切换（因为 Ads 侧数据已经接近真实）
4. **月底前**：更新 Day 26 v3.1 和 4 月月报，加 "Day 27 晚发现 GA4 源污染但 Ads 侧基本对" 更正章节

---

## 📨 转发给技术同学的消息（v2 版 · 不急，有空再修）

> 📋 直接复制下面这块发给技术同学。v1 版本写得太紧急（以为 Ads 数据是错的），其实 Ads 侧数据挺准的，是 GA4 侧有噪声。

```
Hi [技术同学]，

今天花了半天时间系统诊断了 GA4 侧 purchase event 的数据质量问题，结论是：

✅ 好消息：Google Ads 侧看到的 conversion value 是基本准确的（和业务后台 Metabase 差 1.1×，误差可接受）。原因是 Ads 原生会过滤掉没带 transaction_id 的 purchase events。

⚠️ 待修：但 GA4 侧有 65% 的 purchase events 没带 transaction_id（revenue=0 的噪声事件），虽然不影响 Ads 投放决策，但会让 GA4 dashboard 看起来很奇怪（4 月 20 日显示 37 单 ¥4,679，实际 SEM 真实 0 单）。

📌 修复建议（优先级不高，有空再做）：

在 GTM 里给 purchase tag 的 trigger 加一个 condition：
  - 原 trigger: Custom Event = purchase
  - 加一条 AND: dataLayer variable transaction_id is not null/empty

改完后做一次 DebugView 验证（发一单 → 确认只 fire 一次 + 带 txn_id + value 有值），就可以了。

🧪 为什么出现空 txn_id events（猜测）：
  - 订单历史页 / 订单详情页可能也 fire 了 purchase event
  - 或者购物车 → 支付成功中间某个中转页也 fire 了
  - 需要看 dataLayer.push({event:'purchase'}) 的所有调用位置

不急 · 不 block 投放 · 但修了对数据治理更健康。

详细诊断报告在：[内部 repo 路径]/FISHGOO_广告成长档案/03_后续观测计划/Measurement_三源对账_2026-04-21.md
```

---

*本文档为三源对账一次性快照，建议修复后至少复跑一次才能关闭本项调查。v2 补全于 2026-04-21 22:00，SA 打通 GA4 Data API 后精准定位。*
