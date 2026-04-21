# 03 · Pmax- 加 Brand Exclusion（品牌排除）

**目标**：在 Pmax- campaign 上加 **brand exclusion 列表**，包含 `fishgoo` 相关关键词，让 Pmax- 不再参与你品牌词的竞价。

**预期效果**：
- Pmax- 不再蚕食 brand search 的流量 · 你不再同时为同一个搜到 "fishgoo" 的用户付两次钱
- Brand search 会拿回它本该有的流量份额（之前 Day 26 审计说"IS lost to rank 86%"，有一部分是被你自己的 Pmax 抢的）
- 预计月省 $30-50，且 brand search CPC 可能下降

**风险**：极低 · 是 Google 官方推荐的最佳实践

**预计时长**：10 分钟

---

## 🧠 先理解一下问题

当前情况：
- 你有 `search -品牌-0925` 这个 brand campaign · 专门接 "fishgoo" 类关键词
- 你有 `Pmax-` 这个 Performance Max campaign · 本应接**非品牌**流量（repfashion、wholesale 等）
- **但** Pmax 默认会 target 所有 keyword 包括品牌词 · 所以当用户搜 "fishgoo" 时，**Pmax 和 brand search 同时抢这个流量**
- 结果：Pmax 拿走一部分 brand 流量 · 你为同一个用户在两个 campaign 分别付 CPC · 很傻

**解决**：在 Pmax 里加"brand exclusion"，告诉 Google "这些词属于我的 brand，Pmax 不要抢"。

---

## 🗺️ 路径（有 2 种，选你 UI 里有的那个）

### 路径 A（新版 UI，2024+）

```
左侧菜单「Campaigns」
  → 点 Pmax-
  → 左侧菜单 「Asset groups」或「Insights」
  → 找不到的话，回到 Campaigns 列表
  → 顶部菜单点「Tools」(工具 · 扳手图标)
  → 「Shared library」(共享库)
  → 「Brand lists」(品牌列表)
```

### 路径 B（老版 UI）

```
Campaigns → 点 Pmax-
  → Settings
  → 向下滚，找到「Brand exclusions」或「Exclude brands」
  → 点 Edit
```

---

## 📝 具体操作（路径 A 新版 · 推荐）

### 步骤 1：先建一个「品牌列表」

1. 在 `Tools → Shared library → Brand lists`
2. 点 **「+ New brand list」** 或 **「+ Create brand list」**
3. 名字填：`FISHGOO Own Brand`（你自己的品牌列表）
4. **添加品牌**：
   - 搜 `fishgoo` → 如果搜到 Google 官方已收录 FISHGOO 品牌 → 点选
   - 搜不到 → 手动输入 · 名字填 `FISHGOO`，网址填 `fishgoo.com`
5. 保存

### 步骤 2：把这个列表挂到 Pmax-

1. 回到 Campaigns → 点 Pmax-
2. Settings → 找 **「Brand exclusions」** 或 **「Excluded brands」** 栏
3. 点 Edit → 选刚建的 **FISHGOO Own Brand** 列表
4. 保存

---

## 📝 具体操作（路径 B 老版 / Fallback · 直接加 negative keywords）

如果你的 UI 找不到 Brand lists，用"加 negative keyword"兜底：

```
Pmax- → Settings → 最底部「Additional settings」展开
  → 找「Negative keywords」
  → Add
  → 输入下面 5 个 keyword（每行一个）
```

**要加的 5 个 negative keyword**（都用 Phrase match · "词组匹配"）：

```
"fishgoo"
"fishgoo shoes"
"fishgoo app"
"fishgoo com"
"fishgoo reviews"
```

**注意 match type 选 Phrase（词组）不是 Broad（广泛）**。Phrase 的符号是双引号 `"..."`。

---

## ✅ 验证改成功了

保存后：

- Pmax- Settings 区现在显示 "Brand exclusions: FISHGOO Own Brand"（路径 A）
- 或 Negative keywords 区多了 5 个 fishgoo 相关词（路径 B）
- **Brand search campaign 在未来 3-7 天内 IS（impression share）应该上升**（之前被 Pmax 抢的流量回来了）

---

## 📊 之后一周观察

看「当前驾驶舱」Tab 的品牌词 IS：

- 之前 brand search 的 "Search IS lost to rank" = **86%**
- 一周后期望：降到 **50-60%**（不会一次降到 0，但会有明显改善）
- brand search 的点击数应该上升 · CPC 可能下降

---

## ❌ 出问题了怎么办

### 情况 1：Brand lists 里找不到 FISHGOO

Google 没有收录你的品牌 · 继续用路径 B（negative keyword）即可。以后 Google 收录了再切过来。

### 情况 2：Shared library → Brand lists 不存在

你的账户 UI 版本还没上这个功能 · 用路径 B。

### 情况 3：5 个 negative keyword 加错了 match type

如果你加成了 Broad（没加引号），会 block 掉所有含 fishgoo 的词组合 · 影响太大。

**修正方法**：
- Negative keywords 列表里找到加错的那行
- 删掉，重新加，match type 明确选 Phrase

---

## 📌 做完告诉 Claude

**截图 Pmax- 设置里的 Brand exclusions / Negative keywords 区**，显示 FISHGOO 相关词已经在里面了 · 发过来。
