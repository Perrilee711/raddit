# Reddit 电商需求找客实施手册

## 目标

你不是去 Reddit 上“硬找客户”，而是去找三类人：

1. 已经明确在求解问题的人
2. 正在换工具、换服务商、换运营方法的人
3. 因为增长、投放、建站、履约、转化出问题而愿意付费的人

对你给出的版块来说，重点不是流量大，而是“问题表达够具体”。

## 先看哪些帖子

优先看下面这几类标题或正文：

- “How do I...”
- “Need help with...”
- “Why is my store not converting”
- “Shopify / WooCommerce migration”
- “App recommendation”
- “Best way to find suppliers”
- “Facebook ads not working”
- “Abandoned carts”
- “My CPA is too high”
- “How to improve conversion rate”
- “Any tool for...”

这些帖子比泛讨论帖更有成交价值，因为它们已经暴露了明确需求。

## 在这些版块里分别找什么

### `r/dropship` 和 `r/dropshipping`

重点找：

- 选品焦虑
- 供应商不稳定
- 广告亏损
- 支付、物流、退货问题
- 新手不知道从哪里开始

这类用户的典型需求：

- 低成本起盘
- 爆款验证
- 供应链稳定
- 广告代投或投放诊断
- 店铺搭建模板

### `r/ecommerce`

重点找：

- 经营瓶颈
- 多渠道运营
- 转化率优化
- 邮件营销
- 客服与履约问题

这类用户的典型需求：

- 增长咨询
- 数据分析
- 自动化流程
- 转化优化
- 复购提升

### `r/shopify`

重点找：

- 主题、插件、结账流程
- 页面速度
- 转化问题
- 订阅、电邮、Upsell
- Shopify App 选型

这类用户的典型需求：

- Shopify 店铺搭建
- 主题修改
- App 集成
- CRO 优化
- 技术支持

### `r/woocommerce`

重点找：

- 插件冲突
- 页面加载慢
- 结账报错
- 支付网关问题
- WordPress 维护与安全

这类用户的典型需求：

- WooCommerce 技术开发
- 性能优化
- 故障排查
- 迁移改版
- 长期维护

## 怎么判断是不是“高意向客户”

给每条帖子打分，优先跟进总分高的。

### 高意向信号

- 明确说出问题已经持续一段时间
- 提到具体指标，比如 ROAS、CPA、CVR、AOV
- 提到自己已经试过几种方案但没解决
- 问“推荐谁”“用什么服务”“有没有人做过”
- 帖子下有持续互动，说明问题真实且急

### 低意向信号

- 纯讨论、纯吐槽、纯观点
- 没有具体问题场景
- 明显只是新手泛问
- 跟你服务没有直接关联

### 建议打分

- 问题明确度：0-3
- 付费可能性：0-3
- 紧急程度：0-2
- 技术/运营复杂度：0-2

总分 7 分以上，建议进入重点阅读池。

## 你真正要提炼的“共性”

不是简单统计词频，而是把需求整理成下面几类：

### 1. 阶段共性

- 刚起店
- 已经有单但不稳定
- 广告放量失败
- 准备迁移平台
- 店铺技术负担过重

### 2. 平台共性

- Shopify 更偏增长、插件、页面、转化
- WooCommerce 更偏技术、维护、兼容性、性能

### 3. 业务共性

- 获客成本过高
- 站内转化偏低
- 履约和供应链不稳
- 数据追踪不完整
- 工具太多但没有统一流程

### 4. 决策共性

- 他们不想学完整套技术
- 他们想要更快的解决方案
- 他们愿意为“省时间”和“少踩坑”付费

## 推荐抓取字段

为了后面能做阅读和筛选，原始抓取至少保留这些字段：

- `subreddit`
- `title`
- `body`
- `author`
- `url`
- `created_utc`
- `score`
- `num_comments`
- `search_term`

建议再补几个分析字段：

- `problem_type`
- `business_stage`
- `platform`
- `intent_score`
- `pain_tags`
- `suggested_offer`

## 推荐搜索词

你可以在每个版块里围绕这些词去搜：

- `need help`
- `looking for`
- `recommend`
- `agency`
- `freelancer`
- `developer`
- `marketing`
- `conversion`
- `theme`
- `plugin`
- `speed`
- `supplier`
- `ads`
- `checkout`
- `abandoned cart`
- `email flows`
- `migration`

## 抓下来后怎么整理

建议分成三层：

### 第一层：原始池

不做判断，只保存原始帖子。

目录建议：

- `data/raw/YYYY-MM-DD_reddit_posts.jsonl`

### 第二层：清洗池

把广告帖、无关帖、重复帖去掉，并补充标签。

目录建议：

- `data/processed/YYYY-MM-DD_reddit_posts_enriched.json`

### 第三层：阅读报告

把“值得看”的帖子、人群共性、需求分布整理成 Markdown。

目录建议：

- `docs/reports/YYYY-MM-DD_reddit-research.md`

## 报告应该怎么写

每份阅读报告建议固定这 5 块：

1. 今日抓取概况
2. 高频需求与痛点
3. 高意向客户线索
4. 共性总结
5. 下一步实施动作

## 下一步实施动作怎么落地

你拿到报告后，不要停在“阅读”，要继续变成动作：

1. 挑出 10 条高意向帖子，手工二次阅读
2. 把他们的问题映射到你的服务清单
3. 总结 3 个最常见的 offer
4. 反推你的内容选题、落地页、私信话术、产品化服务

## 最适合转化的 offer 方向

从这些版块看，最容易切入的通常是：

- Shopify / WooCommerce 店铺问题诊断
- 页面速度和结账流程优化
- 广告亏损排查与漏斗诊断
- 邮件自动化和弃单挽回
- 供应链与履约问题梳理
- 平台迁移或技术维护

## 实操建议

- 不要只抓热门帖，也要抓新帖，因为新帖里更容易出现真实、急迫的问题
- 不要只按点赞排序，也要看评论数，因为评论数更能反映问题被共鸣的程度
- 不要把所有问题混在一起，要按“阶段 + 平台 + 问题类型”三层来读
- 不要直接把帖子当客户名单，而是把帖子当需求雷达

## 你在这个仓库里的最小流程

1. 把 Reddit 数据保存到 `data/raw/`
2. 运行脚本生成 Markdown 报告
3. 阅读 `docs/reports/`
4. 手工挑选高意向需求，进入你的销售或内容实施流程
