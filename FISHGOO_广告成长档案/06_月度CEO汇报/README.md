# 月度 CEO 汇报

每月 1-2 号给 CEO 的 SEM 渠道月度汇报。

## 命名规范

```
YYYY-MM_SEM月报_给CEO.md
```

## 目录说明

- 每月一份 md，存为**正式归档**（git 版本追溯 + CEO 回复可以 issue 跟进）
- 产物类型：Markdown 优先，需要 PDF 时用 `pandoc` 或 `marked` 现场生成
- 数据口径：统一 **6.8921 CNY/USD 管理汇率**，与[广告看板](https://mcp.perrilee.com/ad-board/)同源
- 内容范围：只 SEM 渠道（Google Ads + Metabase · SEM 团队）

## 标准结构（7 段 · 给 CEO 3-5 分钟读完）

1. **Executive Summary**（30 秒版本）· 一句话 + 3 个关键数字 + 3 个决策建议
2. **核心指标** · 本月 vs 上月 vs benchmark 对照
3. **账户结构/关键变化** · 发生了什么、为什么
4. **团队/推广者拆分** · 归因到人
5. **3 件做得好 / 3 件没做好**
6. **下月 3 件关键动作 + 预算建议**
7. **需要 CEO 决策/支持的事项**

附录放原始数据（Campaigns、明细表、数据源声明）。

## 自动化 roadmap

| 阶段 | 状态 |
|---|---|
| Phase 1 · 手工跑通流程 | ✅ 2026-03 月报 v1（MVP） |
| Phase 2 · 写 `scripts/generate_monthly_report.py` 半自动生成 | 🎯 5 月开干 |
| Phase 3 · systemd 每月 1 号 10:00 自动跑 | 🎯 6 月开干（依赖 Metabase API key） |
| Phase 4 · md → PDF + 邮件发给 CEO | 🎯 Q3 评估 |

## 相关文档

- [2026-03 SEM 月报 · v1](./2026-03_SEM月报_给CEO.md)
- [Day26 深度审计 · 合伙人视角 v3.1](../03_后续观测计划/Day26_深度审计_合伙人视角_2026-04-20.md)
- [广告负责人看板 V3](../05_30天广告成长看板/README.md)
