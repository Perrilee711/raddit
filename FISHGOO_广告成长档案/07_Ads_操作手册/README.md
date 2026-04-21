# 07 · Google Ads 操作手册

> **适用对象**：Perri（零代码背景） · 在 Google Ads UI 里手动做改配置
> **为什么手动**：Google Ads MCP 是只读的，不能通过 API 改配置
> **编号**：按执行优先级排序 · 先做 01，再做 02，依次类推

## 操作手册目录

| 编号 | 动作 | 预期影响 | 风险 | 预计时长 |
|---|---|---|---|---|
| 01 | Pmax- 设置 Target CPA = $13 | 控制 waste，CPA 不超 $13 | 低（可随时关） | 10 分钟 |
| 02 | Pmax- 改地域为 "Presence" | 不再烧 "interested but not in" 流量 · 省 15-30% | 极低 | 5 分钟 |
| 03 | Pmax- 加 brand exclusion | Pmax 不再蚕食 brand search 流量 | 极低 | 10 分钟 |
| **04** | **Pmax- 切 MAX_CONVERSION_VALUE**（不加 tROAS） | **按真实 $ 优化 · ROAS 预期 +15-30%** | 中（7-14 天学习期） | 10 分钟 |
| 05 | 填 account-level negative list | 减少无关搜索词浪费 | 极低 | 20 分钟 |
| 06 | 挂 warning1 placement 列表到 Pmax | 排除低质展位 | 极低 | 5 分钟 |
| 07 | Brand search 换 TARGET_IMPRESSION_SHARE | 抢回 86% IS loss | 中（bid 会上升） | 10 分钟 |
| 08 | 开 non-brand search campaign MVP | 测试新增量 | 中（要监控每日支出） | 30 分钟 |

## 通用注意事项

1. **改配置前先看现状**：每次进 Google Ads UI，先记下你要改的页面当前数值（手机拍照也行），以防改错想回滚
2. **一次只改一个东西**：如果同时改多个，出问题后不知道是哪个动作造成的
3. **改完等 48 小时再评估**：Google Ads 的优化都有 learning period，48 小时内数据噪声大
4. **任何一步看不懂就停下**：截图发我，别硬改
5. **所有操作都可撤销**：除了"删除"外，设置类改动都能回退

## 本月推荐执行节奏（Day 27 晚更新 · v2 口径）

**战略调整**：Day 27 打通 GA4 Data API 确认 Ads 侧 value 数据可信（1.1× 误差）· **可以跳过 01 tCPA · 直接切 04 value bidding**。两条路径都给出，你二选一：

### 路径 A（合伙人首选 · 直接切 value bidding）

| 日期 | 做什么 | 为什么这天 |
|---|---|---|
| 今天（4/21 周二）| **04**（切 MAX_CONVERSION_VALUE）+ 02（Presence）| 一次性把 bid + geo 两个最大杠杆切到位 |
| 明天（4/22 周三）| 03（brand exclusion）| 防御性动作 · 低风险 |
| 4/23-4/25 | 观察 04 学习期前 3 天 · 不乱动 | 学习期不能再改 bid |
| 4/26-5/2 | 学习期稳定后做 05 + 06（negative list + placement）| 学习期内不上任何结构性改动 |
| 5/3 起 | 07（brand TIS）· 08（non-brand）| Value bidding 稳了再开新战线 |

### 路径 B（保守派 · 先 tCPA 后 value bidding）

| 日期 | 做什么 | 为什么这天 |
|---|---|---|
| 今天（4/21 周二）| **01**（tCPA $13）+ 02 | 最保守的 bid 策略 |
| 明天（4/22 周三）| 03（brand exclusion）| 防御 |
| 4/23-4/28 | 观察 01 tCPA 学习期 | 7 天学习期完整跑完 |
| 4/29 | 评估：若 ROAS 稳 > 3 · 切 04；若 < 2 · 保留 01 | 数据决策 |
| 5/2-5/5 | 05 + 06 | 结构防御 |
| 5/6 起 | 07 + 08 | 扩量 |

---

## 紧急联系

任何一步看不懂、改错了、或想撤销 → **截图发 Claude，立刻帮你**。
