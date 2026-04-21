# 02 · Pmax- 改地域为「Presence」

**目标**：把 Pmax- 的地域定位从 **"Presence or interest"**（在该地区，或对该地区感兴趣）改成 **"Presence"**（只在该地区）。

**预期效果**：不再烧"对你的产品感兴趣但不在你目标市场"的流量 · 预计每月省 **$75-150** 或等价 ROAS 提升 15-30%。

**风险**：极低。这个设置的"宽松模式"（Presence or interest）已被 Google 自己 2023 年起列为 G11 FAIL，不应用于 e-com 账户。

**预计时长**：5 分钟

**为什么必须改**：同账户 search -品牌-0925 已经是 `Presence`（对的），只有 Pmax- 是 `Presence or interest`（错的）· 说明历史上建 campaign 时没统一。

---

## 🎯 开始前确认

你在 Google Ads 里能看到 Pmax- campaign（Status = Enabled）。如果不能，先看 `01_Pmax-设置-Target-CPA.md` 里的"找不到 Pmax-"小节。

---

## 🗺️ 路径

```
左侧菜单「Campaigns」
  → 点 Pmax-
  → 左侧菜单「Settings」
  → 找到「Locations」(地区) 这一栏
  → 点「Edit」(编辑) 或 铅笔 icon 展开
  → 继续向下找到「Location options」(地区选项)
```

**注意 · Location options 区经常被折叠**：看到 "Location options" 文字后，如果内容是折叠的，点它旁边的小三角或 "Show more" 展开。

---

## 📝 具体改动

在 Location options 展开后，你会看到 3 个单选项（或类似表述）：

```
○ Presence or interest（在该地区，或对该地区感兴趣） ← 当前被选中
● Presence（在该地区或经常访问） ← 选这个
○ Search interest（仅搜索过该地区的人）
```

1. 点选 **「Presence」**（只保留你目标市场的真正用户）
2. 页面底部可能会有 **「Save」**，点它

**注意**：Google Ads 有时候把 3 个选项简化成 2 个，只有：
```
○ Presence or interest ← 宽松（当前被选中）
● Presence ← 精准（选这个）
```

都一样 · 选 **Presence** 就对。

---

## ✅ 验证改成功了

保存后：

- Pmax- 的 Locations 区现在应该显示 "Presence" 而不是 "Presence or interest"
- **不会进入 learning period**（地域定位改动不触发 bid 学习）
- 点击量可能立即下降 10-20%（预期 · 那部分流量本来就不该买）
- **但 ROAS 会变好**（因为你现在只给真正的目标市场花钱）

---

## 📊 之后一周观察

改完后看 Pmax- 这 7 天的 **真实 ROAS**（看板「真实 ROAS 日报」模块）：

- 如果 ROAS 从 2× 提升到 2.5-3.0 → **成功，配合 tCPA $13 效果显现**
- 如果 ROAS 没变或下降 → 可能你的目标市场本身流量紧缺，下周再看

---

## ❌ 出问题了怎么办

### 情况 1：找不到 Location options 区

有时 Google Ads UI 把这个选项藏得很深。尝试：
- 顶部搜索 "Location options"
- 或：Settings → 最底部 **「Additional settings」** 展开 → 就能找到

### 情况 2：保存后提示 "No changes detected"

可能你之前的值已经是 "Presence"（那 Day 26 审计里的信息可能过时了）。截图发我，我帮你 double-check。

### 情况 3：提示"This will reduce your reach"

正常 · 点继续保存。"reach 下降" 正是我们要的 —— 那部分 reach 是无用 reach。

---

## 📌 改完以后告诉 Claude

**截图 Pmax- Settings → Locations → Location options 现在是 "Presence"** 的状态，发我。

做完 01 + 02 → 今天这一组动作可以收工。剩下 03-07 之后几天再做。
