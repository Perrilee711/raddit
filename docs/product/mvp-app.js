const fallbackData = {
  study: {
    topic: "美国 dropshipping / 履约与 supplier 问题",
    market: "美国 dropshipping",
    dateRange: "近 30 天",
    updatedAt: "今天 09:20",
    confidence: "High",
  },
  summary: {
    headline: "优先打“已出单但履约混乱”的卖家，主推 `Fulfillment Audit`。",
    explanation:
      "最近 14 天里，和 shipping delays、3PL confusion、supplier handoff 相关的高意向表达明显上升。这类问题更具体、离付费更近，也更适合被包装成审查型产品。",
    metrics: [
      { value: "86", label: "Opportunity Score", note: "市场值得优先打" },
      { value: "82", label: "Packaging Readiness", note: "很适合做清晰 offer" },
      { value: "+38%", label: "趋势动量", note: "近 14 天升温" },
      { value: "Test Now", label: "Action Mode", note: "本周适合直接测试" },
    ],
  },
  todayChanged: [
    {
      title: "履约类需求升温",
      body: "“need a 3PL” 和 “shipping delays” 相关表达显著上升，已经从抱怨开始转向求推荐。",
    },
    {
      title: "supplier 需求依然强",
      body: "private supplier 仍然是稳定高位主题，但包装成熟度仍然低于 Fulfillment 主题。",
    },
    {
      title: "成本优化仍偏次级",
      body: "cost-down 需求存在，但问题定义不够锋利，当前不适合做第一主打。",
    },
  ],
  weeklyActions: [
    { title: "主推产品", body: "统一推 `3PL & Fulfillment Audit`" },
    { title: "主攻客群", body: "运营期 / 替换中 / 履约与发货" },
    { title: "测试话术", body: "先找出退款和延迟背后的真正 bottleneck" },
    { title: "暂缓投入", body: "泛 sourcing、泛 cost-down 主题" },
  ],
  segments: [
    {
      id: "operating-replacing-fulfillment",
      name: "运营期 / 替换中 / 履约与发货",
      pain: "发货慢、退款增加、3PL 不清楚",
      opportunity: 86,
      packaging: 82,
      confidence: "High",
      trend: "上升",
      actionMode: "Test Now",
      recommendedProduct: "3PL & Fulfillment Audit",
      rationale:
        "问题已经影响经营结果，表达具体，离成交近，并且 Fishgoo 适配度高。",
      signals: [
        "Shipping delays directly tied to refund pressure",
        "Users explicitly asking for 3PL and fulfillment help",
        "Supplier-to-shipping handoff issues repeatedly mentioned",
      ],
    },
    {
      id: "expansion-seeking-sourcing",
      name: "扩张期 / 求解中 / 供应商与采购",
      pain: "想找 private supplier，但担心稳定性和执行能力",
      opportunity: 74,
      packaging: 67,
      confidence: "High",
      trend: "持续升温",
      actionMode: "Secondary Test",
      recommendedProduct: "Supplier Match Sprint",
      rationale:
        "需求很明确，但交付波动比 Fulfillment Audit 更大，适合第二优先级。",
      signals: [
        "Looking for reliable private supplier",
        "Need sourcing partner in China",
        "Unhappy with current supplier communication",
      ],
    },
    {
      id: "operating-aware-risk",
      name: "运营期 / 认知中 / 质量与风险",
      pain: "QC 不稳、错发漏发、fake supplier 风险",
      opportunity: 59,
      packaging: 55,
      confidence: "Medium",
      trend: "平稳",
      actionMode: "Monitor",
      recommendedProduct: "China Buying Risk Check",
      rationale:
        "问题真实存在，但还没有形成足够强的一致购买语言，更适合作为支持型服务。",
      signals: [
        "Mentions of fake supplier and quality mismatch",
        "Risk awareness is rising but not dominant",
      ],
    },
  ],
  packages: [
    {
      name: "3PL & Fulfillment Audit",
      stage: "第一主产品",
      targetSegment: "运营期 / 替换中 / 履约与发货",
      problem: "发货慢、退款增加、3PL 结构不清楚",
      promise: "先找出延迟和退款背后的真正 bottleneck，再决定该不该换方案。",
      format: "轻审查 / 诊断型服务",
      angle: "不是先换 supplier，而是先找出到底哪一段在拖慢发货。",
      avoid: "不要先卖泛 sourcing、泛供应链优化。",
    },
    {
      name: "Supplier Match Sprint",
      stage: "第二主产品",
      targetSegment: "扩张期 / 求解中 / 供应商与采购",
      problem: "想找 private supplier，但担心稳定性和中国端执行能力",
      promise: "不是给你一堆名单，而是给你适合当前阶段的 supplier 路径。",
      format: "匹配建议 / 结构化评估",
      angle: "先判断你到底需要 supplier、agent，还是 supplier + fulfillment 组合。",
      avoid: "不要包装成“万能 sourcing 代办”。",
    },
  ],
  evidence: [
    {
      quote: "Looking for a 3PL fulfillment service",
      source: "r/dropshipping",
      segment: "扩张期 / 求解中 / 履约与发货",
      pain: "3PL selection",
    },
    {
      quote: "Shipping delays are killing conversions",
      source: "r/ecommerce",
      segment: "运营期 / 替换中 / 履约与发货",
      pain: "shipping delays",
    },
    {
      quote: "Need a reliable private supplier in China",
      source: "r/dropship",
      segment: "扩张期 / 求解中 / 供应商与采购",
      pain: "private supplier",
    },
    {
      quote: "Refunds keep going up because delivery times are inconsistent",
      source: "r/shopify",
      segment: "运营期 / 替换中 / 履约与发货",
      pain: "refund pressure",
    },
  ],
  heatmap: {
    columns: ["供应商与采购", "履约与发货", "质量与风险", "成本与利润"],
    rows: [
      {
        label: "运营期 / 替换中",
        values: [
          { score: 72, note: "supplier 不稳", level: "mid" },
          { score: 91, note: "发货慢 / 3PL 混乱", level: "high" },
          { score: 58, note: "QC 连带问题", level: "mid" },
          { score: 36, note: "成本不是第一痛点", level: "low" },
        ],
      },
      {
        label: "扩张期 / 求解中",
        values: [
          { score: 84, note: "private supplier 需求强", level: "high" },
          { score: 63, note: "履约结构开始复杂", level: "mid" },
          { score: 42, note: "风险次级", level: "low" },
          { score: 33, note: "利润议题偏次级", level: "low" },
        ],
      },
      {
        label: "验证期 / 比较中",
        values: [
          { score: 51, note: "在看 supplier", level: "mid" },
          { score: 40, note: "履约痛感未完全形成", level: "low" },
          { score: 28, note: "风险认知不足", level: "low" },
          { score: 49, note: "对成本敏感", level: "mid" },
        ],
      },
    ],
  },
  trendSeries: {
    defaultKey: "30d",
    views: [
      {
        key: "7d",
        label: "近7天",
        recordCount: 34,
        mode: "dated",
        labels: ["3/11", "3/12", "3/13", "3/14", "3/15", "3/17"],
        headline: "近 7 天里，供应商与采购的末端信号在回升。",
        note: "演示数据会在真实 payload 到位后自动替换。",
        series: [
          { id: "fulfillment_setup", label: "履约与发货", values: [3, 4, 6, 5, 4, 4], latest: 4, delta: 0 },
          { id: "supplier_match", label: "供应商与采购", values: [1, 2, 2, 3, 4, 5], latest: 5, delta: 1 },
          { id: "china_risk_control", label: "质量与风险", values: [0, 1, 1, 1, 1, 1], latest: 1, delta: 0 },
        ],
      },
      {
        key: "30d",
        label: "近30天",
        recordCount: 126,
        mode: "dated",
        labels: ["2/20", "2/24", "2/28", "3/4", "3/9", "3/17"],
        headline: "近 30 天里，履约与发货仍是主线，但 supplier 在后段抬头。",
        note: "当前为演示趋势；接入真实时间戳后会自动切换到日期窗口。",
        series: [
          { id: "fulfillment_setup", label: "履约与发货", values: [8, 9, 11, 12, 15, 18], latest: 18, delta: 3 },
          { id: "supplier_match", label: "供应商与采购", values: [6, 7, 8, 10, 10, 11], latest: 11, delta: 1 },
          { id: "china_risk_control", label: "质量与风险", values: [3, 4, 5, 5, 4, 4], latest: 4, delta: 0 },
        ],
      },
      {
        key: "all",
        label: "全量样本",
        recordCount: 564,
        mode: "sample_sequence",
        labels: ["窗口 1", "窗口 2", "窗口 3", "窗口 4", "窗口 5", "窗口 6"],
        headline: "全量样本里，履约与 supplier 两条线都值得持续跟踪。",
        note: "用于看长期结构，不代表短期窗口变化。",
        series: [
          { id: "fulfillment_setup", label: "履约与发货", values: [8, 9, 11, 12, 15, 18], latest: 18, delta: 3 },
          { id: "supplier_match", label: "供应商与采购", values: [6, 7, 8, 10, 10, 11], latest: 11, delta: 1 },
          { id: "china_risk_control", label: "质量与风险", values: [3, 4, 5, 5, 4, 4], latest: 4, delta: 0 },
        ],
      },
    ],
    mode: "sample_sequence",
    labels: ["窗口 1", "窗口 2", "窗口 3", "窗口 4", "窗口 5", "窗口 6"],
    headline: "最近 6 个窗口里，履约与发货的末端信号最强。",
    note: "当前为演示趋势；接入真实时间戳后会自动切换到日期窗口。",
    series: [
      { id: "fulfillment_setup", label: "履约与发货", values: [8, 9, 11, 12, 15, 18], latest: 18, delta: 3 },
      { id: "supplier_match", label: "供应商与采购", values: [6, 7, 8, 10, 10, 11], latest: 11, delta: 1 },
      { id: "china_risk_control", label: "质量与风险", values: [3, 4, 5, 5, 4, 4], latest: 4, delta: 0 },
    ],
  },
  weeklyBrief: {
    topChange: "履约问题热度和具体度同时上升",
    topSegments: [
      "运营期 / 替换中 / 履约与发货",
      "扩张期 / 求解中 / 供应商与采购",
      "运营期 / 认知中 / 质量与风险",
    ],
    leadPackage: "3PL & Fulfillment Audit",
    avoid: [
      "不要主打泛 sourcing",
      "不要把成本议题当主入口",
      "不要把首页变回帖子流",
    ],
    nextWeek: [
      "统一测试 Fulfillment Audit 的主话术",
      "保留 Supplier Match Sprint 作为第二优先级",
      "继续追踪 shipping delays 和 3PL 相关信号增速",
    ],
  },
};

let appData = fallbackData;
const STUDY_ID = "fishgoo-us-dropshipping";
let currentStudyId = STUDY_ID;
let currentViewId = "dashboard";
let studyTemplate = {
  business_lines: ["Dropshipping 供应链服务"],
  regions: ["美国"],
  primary_goals: ["选客群 + 定产品包装"],
  recommended_outputs: ["Dashboard 每日看板"],
};
let latestStudyDraft = null;
let studyList = [];
let authUser = null;
let studyJobs = [];
let allJobs = [];
let currentSchedule = {
  enabled: false,
  mode: "seeded",
  interval_hours: 24,
  last_run_at: null,
  next_run_at: null,
};
let refreshMode = "seeded";
let pollTimer = null;
let lastKnownActiveJobCount = 0;
let lastJobCompletionKey = "";
let selectedOperationsStudyId = "all";
let selectedJobId = null;
let selectedTrendViewKey = null;
let selectedTrendSeriesId = "all";
let apiAvailable = false;

const views = [
  { id: "dashboard", label: "Dashboard" },
  { id: "operations", label: "Operations" },
  { id: "setup", label: "Study Setup" },
  { id: "segments", label: "Segment Explorer" },
  { id: "packaging", label: "Packaging Studio" },
  { id: "weekly", label: "Weekly Brief" },
];

function isHttpMode() {
  return window.location.protocol.startsWith("http");
}

function getVisibleViews() {
  if (apiAvailable) return views;
  return views.filter((view) => !["operations", "setup"].includes(view.id));
}

function formatDateTime(value, empty = "未运行") {
  if (!value) return empty;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function activeJobCount() {
  return (studyJobs || []).filter((job) => ["queued", "running"].includes(job.status)).length;
}

function showToast(title, body = "", tone = "") {
  const stack = document.getElementById("toast-stack");
  if (!stack) return;
  const item = document.createElement("div");
  item.className = `toast ${tone}`.trim();
  item.innerHTML = `<strong>${title}</strong>${body ? `<div>${body}</div>` : ""}`;
  stack.appendChild(item);
  window.setTimeout(() => {
    item.style.opacity = "0";
    item.style.transform = "translateY(8px)";
  }, 3200);
  window.setTimeout(() => item.remove(), 3800);
}

function syncJobNotifications() {
  const activeCount = activeJobCount();
  if (activeCount > lastKnownActiveJobCount) {
    showToast("新任务已进入队列", `当前有 ${activeCount} 个任务在排队或运行。`, "warn");
  }

  const completed = (studyJobs || []).find((job) => job.status === "completed");
  if (completed) {
    const completionKey = `${completed.id}:${completed.finished_at || ""}`;
    if (completionKey !== lastJobCompletionKey) {
      lastJobCompletionKey = completionKey;
      showToast("Study 已更新", `${completed.mode} 任务已完成，Dashboard 已刷新。`, "success");
    }
  }

  const failed = (studyJobs || []).find((job) => job.status === "failed");
  if (failed && failed.error) {
    const failureKey = `${failed.id}:${failed.finished_at || ""}:failed`;
    if (failureKey !== lastJobCompletionKey) {
      lastJobCompletionKey = failureKey;
      showToast("任务运行失败", failed.error, "error");
    }
  }

  lastKnownActiveJobCount = activeCount;
}

function primeJobNotificationState() {
  lastKnownActiveJobCount = activeJobCount();
  const latestFinished = (studyJobs || []).find((job) => job.status === "completed" || job.status === "failed");
  if (latestFinished) {
    lastJobCompletionKey = `${latestFinished.id}:${latestFinished.finished_at || ""}${latestFinished.status === "failed" ? ":failed" : ""}`;
  }
}

async function apiFetchJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  if (response.status === 403) {
    throw new Error("forbidden");
  }
  if (!response.ok) {
    throw new Error(`API failed: ${response.status}`);
  }
  apiAvailable = true;
  return response.json();
}

function renderMeta() {
  const meta = document.getElementById("meta-pills");
  meta.innerHTML = [
    `研究主题：${appData.study.topic}`,
    `数据范围：${appData.study.dateRange}`,
    `上次更新：${appData.study.updatedAt}`,
    `Confidence：${appData.study.confidence}`,
  ]
    .map((text) => `<div class="pill">${text}</div>`)
    .join("");
}

function renderAuthPanel() {
  const panel = document.getElementById("auth-panel");
  if (!panel) return;
  if (!apiAvailable) {
    panel.innerHTML = `<div class="auth-card">Production Demo · 静态快照版</div>`;
    return;
  }
  if (!authUser) {
    panel.innerHTML = `<div class="auth-card">未登录</div>`;
    return;
  }
  panel.innerHTML = `
    <div class="auth-card">
      <span>当前角色</span>
      <strong>${authUser.name}</strong>
      <span>${authUser.role}</span>
    </div>
  `;
}

function renderStudyRail() {
  const rail = document.getElementById("study-rail");
  if (!rail) return;

  if (!studyList.length) {
    if (!apiAvailable) {
      rail.innerHTML = `
        <div class="card section-card">
          <div class="label orange">公开演示版</div>
          <h2>当前展示的是一份可直接给管理层查看的线上快照</h2>
          <p class="copy">这版聚焦 Dashboard、Segment Explorer、Packaging Studio 和 Weekly Brief，不暴露本地任务队列、Study 配置和内部 API 才能使用的操作入口。</p>
        </div>
      `;
      return;
    }
    rail.innerHTML = `
      <div class="card section-card">
        <div class="label">研究任务</div>
        <h2>还没有可切换的 study</h2>
        <p class="copy">先去 Study Setup 新建一个研究任务，系统会把它保存下来并加入列表。</p>
      </div>
    `;
    return;
  }

  rail.innerHTML = studyList
    .map(
      (study) => `
        <div class="study-card ${study.id === currentStudyId ? "is-active" : ""} ${study.active_job_count ? "is-running" : ""}" data-study-id="${study.id}">
          <div class="label ${study.id === currentStudyId ? "orange" : ""}">${study.status || "study"}</div>
          <h3>${study.title}</h3>
          <div class="small">${study.market}</div>
          <div class="small">${study.headline || "等待研究结论"}</div>
          <div class="study-meta">
            <span class="mini-pill">${study.lead_package || "No package yet"}</span>
            <span class="mini-pill">${study.primary_goal || "未设置目标"}</span>
            <span class="mini-pill">${study.schedule?.enabled ? `Auto ${study.schedule.interval_hours}h` : "Manual only"}</span>
            ${study.active_job_count ? `<span class="mini-pill up">${study.active_job_count} running</span>` : ""}
          </div>
        </div>
      `
    )
    .join("");
}

function renderFilterChips() {
  const marketChip = document.getElementById("market-chip");
  const rangeChip = document.getElementById("range-chip");
  const confidenceChip = document.getElementById("confidence-chip");
  const refreshButton = document.getElementById("refresh-study-button");
  const refreshModeSelect = document.getElementById("refresh-mode-select");
  const refreshModeWrapper = refreshModeSelect?.closest(".inline-select");

  if (marketChip) marketChip.textContent = `市场：${appData.study.market}`;
  if (rangeChip) rangeChip.textContent = `周期：${appData.study.dateRange}`;
  if (confidenceChip) confidenceChip.textContent = `Confidence：${appData.study.confidence}`;
  if (refreshModeWrapper) {
    refreshModeWrapper.style.display = apiAvailable ? "" : "none";
  }
  if (refreshButton) {
    refreshButton.disabled = !apiAvailable;
    refreshButton.textContent = apiAvailable ? "刷新当前 Study" : "静态演示版";
  }
  if (refreshModeSelect) {
    refreshModeSelect.disabled = !apiAvailable;
  }
}

function renderTabs(activeId) {
  const tabs = document.getElementById("view-tabs");
  const visibleViews = getVisibleViews();
  tabs.innerHTML = visibleViews
    .map(
      (view) =>
        `<a href="#" class="${view.id === activeId ? "active" : ""}" data-view="${view.id}">${view.label}</a>`
    )
    .join("");
}

function metricMarkup(metric) {
  return `
    <div class="metric">
      <strong>${metric.value}</strong>
      <span>${metric.label}<br>${metric.note}</span>
    </div>
  `;
}

function itemMarkup(item) {
  return `
    <div class="item">
      <strong>${item.title}</strong>
      <div class="small">${item.body}</div>
    </div>
  `;
}

function segmentCardMarkup(segment) {
  return `
    <div class="item">
      <strong>${segment.name}</strong>
      <div class="small">核心痛点：${segment.pain}</div>
      <div class="kpi-line">
        <span class="mini-pill">Opportunity ${segment.opportunity}</span>
        <span class="mini-pill">Packaging ${segment.packaging}</span>
        <span class="mini-pill up">${segment.trend}</span>
        <span class="mini-pill">${segment.recommendedProduct}</span>
      </div>
    </div>
  `;
}

function packageMarkup(pkg) {
  return `
    <div class="package">
      <div class="label orange">${pkg.stage}</div>
      <h3>${pkg.name}</h3>
      <p><strong>目标客群：</strong>${pkg.targetSegment}</p>
      <p><strong>核心问题：</strong>${pkg.problem}</p>
      <p><strong>一句话承诺：</strong>${pkg.promise}</p>
      <p><strong>推荐入口：</strong>${pkg.format}</p>
      <p><strong>推荐话术角度：</strong>${pkg.angle}</p>
      <p><strong>不建议先卖：</strong>${pkg.avoid}</p>
    </div>
  `;
}

function evidenceMarkup(item) {
  return `
    <div class="quote">
      <strong>“${item.quote}”</strong>
      <div class="evidence-meta">来源：${item.source} · 客群：${item.segment} · 痛点：${item.pain}</div>
    </div>
  `;
}

function heatmapMarkup() {
  const cols = appData.heatmap.columns
    .map((col) => `<div class="heat-head">${col}</div>`)
    .join("");
  const rows = appData.heatmap.rows
    .map(
      (row) => `
        <div class="heat-label">${row.label}</div>
        ${row.values
          .map(
            (value) => `
              <div class="heat-cell ${value.level}">
                <strong>${value.score}</strong>
                <span>${value.note}</span>
              </div>
            `
          )
          .join("")}
      `
    )
    .join("");

  return `<div class="heatmap"><div class="heat-head"></div>${cols}${rows}</div>`;
}

function trendDeltaMarkup(delta) {
  const numeric = Number(delta || 0);
  const tone = numeric > 0 ? "up" : numeric < 0 ? "down" : "warn";
  const text = numeric > 0 ? `+${numeric}` : `${numeric}`;
  return `<span class="mini-pill ${tone}">末端变化 ${text}</span>`;
}

function trendPeriodMarkup(comparison) {
  if (!comparison) {
    return `<span class="mini-pill">暂无上周期比较</span>`;
  }
  const tone = comparison.delta > 0 ? "up" : comparison.delta < 0 ? "down" : "warn";
  return `<span class="mini-pill ${tone}">${comparison.explanation}</span>`;
}

function getTrendViews() {
  const trend = appData.trendSeries || {};
  if (trend.views && trend.views.length) return trend.views;
  return [
    {
      key: trend.defaultKey || "default",
      label: "当前窗口",
      recordCount: 0,
      mode: trend.mode,
      labels: trend.labels || [],
      series: trend.series || [],
      headline: trend.headline || "",
      note: trend.note || "",
    },
  ];
}

function getCurrentTrendView() {
  const views = getTrendViews();
  const fallbackKey = appData.trendSeries?.defaultKey || views[0]?.key;
  if (!selectedTrendViewKey) selectedTrendViewKey = fallbackKey;
  return views.find((view) => view.key === selectedTrendViewKey) || views[0];
}

function trendLinePath(values, chartWidth, chartHeight, maxValue) {
  const safeValues = values && values.length ? values : [0];
  const stepX = safeValues.length > 1 ? chartWidth / (safeValues.length - 1) : 0;
  return safeValues
    .map((value, index) => {
      const x = Math.round(index * stepX);
      const y = Math.round(chartHeight - (Number(value || 0) / Math.max(maxValue, 1)) * chartHeight);
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");
}

function trendSeriesMarkup() {
  const trend = getCurrentTrendView();
  const trendViews = getTrendViews();
  if (!trend || !trend.series || !trend.series.length) {
    return `
      <div class="empty-state">
        <strong>暂无趋势数据</strong>
        <div class="small">当前 study 还没有足够的窗口数据来生成趋势视图。</div>
      </div>
    `;
  }

  const colors = ["#2d63d6", "#ea7b25", "#18896b", "#8c5ae8"];
  const values = trend.series.flatMap((item) => item.values || []);
  const maxValue = Math.max(...values, 1);
  const chartWidth = 640;
  const chartHeight = 220;
  const focusedSeriesId =
    selectedTrendSeriesId !== "all" && trend.series.some((item) => item.id === selectedTrendSeriesId)
      ? selectedTrendSeriesId
      : "all";
  const yTicks = [maxValue, Math.round(maxValue * 0.66), Math.round(maxValue * 0.33), 0]
    .filter((value, index, list) => list.indexOf(value) === index)
    .sort((a, b) => b - a);
  const grid = yTicks
    .map((tick) => {
      const y = Math.round(chartHeight - (tick / Math.max(maxValue, 1)) * chartHeight);
      return `
        <line x1="0" y1="${y}" x2="${chartWidth}" y2="${y}" class="trend-grid-line"></line>
        <text x="-12" y="${y + 4}" text-anchor="end" class="trend-y-label">${tick}</text>
      `;
    })
    .join("");

  const lineSeries = trend.series
    .map((item, index) => {
      const color = colors[index % colors.length];
      const path = trendLinePath(item.values || [], chartWidth, chartHeight, maxValue);
      const stepX = (item.values || []).length > 1 ? chartWidth / ((item.values || []).length - 1) : 0;
      const muted = focusedSeriesId !== "all" && focusedSeriesId !== item.id;
      const anomalies = item.anomalies || [];
      const points = (item.values || [])
        .map((value, pointIndex) => {
          const x = Math.round(pointIndex * stepX);
          const y = Math.round(chartHeight - (Number(value || 0) / Math.max(maxValue, 1)) * chartHeight);
          const anomaly = anomalies.find((entry) => entry.index === pointIndex);
          return `
            ${
              anomaly
                ? `<circle cx="${x}" cy="${y}" r="9" fill="rgba(234, 123, 37, 0.15)" class="trend-point-anomaly"></circle>`
                : ""
            }
            <circle cx="${x}" cy="${y}" r="4.5" fill="${color}" class="trend-point"></circle>
            <title>${item.label} · ${trend.labels[pointIndex] || `窗口 ${pointIndex + 1}`}：${value}${anomaly ? ` · ${anomaly.explanation}` : ""}</title>
            <text x="${x}" y="${y - 10}" text-anchor="middle" class="trend-point-label">${value}</text>
            ${
              anomaly
                ? `<text x="${x}" y="${y + 4}" text-anchor="middle" class="trend-anomaly-marker">!</text>`
                : ""
            }
          `;
        })
        .join("");
      return `
        <g class="trend-line-group ${muted ? "is-muted" : ""}">
          <path d="${path}" fill="none" stroke="${color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"></path>
          ${points}
        </g>
      `;
    })
    .join("");

  const xLabels = trend.labels
    .map((label, index) => {
      const x =
        trend.labels.length > 1
          ? Math.round((index * chartWidth) / (trend.labels.length - 1))
          : Math.round(chartWidth / 2);
      return `<text x="${x}" y="${chartHeight + 26}" text-anchor="middle" class="trend-x-label">${label}</text>`;
    })
    .join("");

  return `
    <div class="trend-block">
      <div class="item">
        <strong>${trend.headline}</strong>
        <div class="small">${trend.note}</div>
        <div class="kpi-line">
          <span class="mini-pill">${trend.comparisonSummary || "暂无上周期变化解释"}</span>
          <span class="mini-pill warn">${trend.anomalySummary || "暂无异常波动"}</span>
        </div>
        <div class="kpi-line" style="margin-top:10px;">
          ${trendViews
            .map(
              (view) => `
                <button type="button" class="chip ${view.key === trend.key ? "is-active" : ""}" data-trend-view="${view.key}">
                  ${view.label} · ${view.recordCount}
                </button>
              `
            )
            .join("")}
        </div>
      </div>
      <div class="trend-legend">
        <button type="button" class="trend-legend-item ${focusedSeriesId === "all" ? "is-active" : ""}" data-trend-series="all">
          <span class="trend-swatch" style="background:linear-gradient(135deg,#2d63d6,#ea7b25)"></span>
          <strong>全部机会线</strong>
          <span class="small">看交叉和拐点</span>
        </button>
        ${trend.series
          .map((item, index) => {
            const color = colors[index % colors.length];
            return `
              <button type="button" class="trend-legend-item ${focusedSeriesId === item.id ? "is-active" : ""}" data-trend-series="${item.id}">
                <span class="trend-swatch" style="background:${color}"></span>
                <strong>${item.label}</strong>
                <span class="small">最近窗口 ${item.latest}</span>
                ${trendDeltaMarkup(item.delta)}
                ${trendPeriodMarkup(item.periodComparison)}
              </button>
            `;
          })
          .join("")}
      </div>
      <div class="trend-chart-shell">
        <svg class="trend-chart" viewBox="-48 0 700 260" role="img" aria-label="趋势时间序列图">
          ${grid}
          ${lineSeries}
          ${xLabels}
        </svg>
      </div>
      <div class="trend-series">
        ${trend.series
          .map(
            (item, index) => `
              <div class="trend-card">
                <div class="trend-card-head">
                  <div>
                    <strong>${item.label}</strong>
                    <div class="small">${trend.label} · 最近窗口：${item.latest} 条 · 全序列：${(item.values || []).join(" / ")}</div>
                  </div>
                  ${trendDeltaMarkup(item.delta)}
                </div>
                <div class="small">${item.periodComparison?.explanation || "暂无周期解释"}</div>
                ${
                  item.anomalies?.length
                    ? `<div class="kpi-line">${item.anomalies
                        .map(
                          (anomaly) =>
                            `<span class="mini-pill warn">${anomaly.label} · ${anomaly.explanation}（${anomaly.value}）</span>`
                        )
                        .join("")}</div>`
                    : `<div class="small">本周期没有明显异常波动。</div>`
                }
              </div>
            `
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderDashboard() {
  const sourceBreakdown = (appData.sourceBreakdown || [])
    .map((item) => `<div class="mini-row"><strong>${item.name}</strong><div class="small">${item.count} 条样本</div></div>`)
    .join("");
  const keywordBreakdown = (appData.keywordBreakdown || [])
    .slice(0, 6)
    .map((item) => `<span class="mini-pill">${item.name} · ${item.count}</span>`)
    .join("");
  const jobsMarkup = (studyJobs || []).length
    ? studyJobs
        .slice(0, 4)
        .map(
          (job) => `
            <div class="job-row is-${job.status}">
              <strong>${job.mode} · ${job.status}</strong>
              <div class="small">触发：${job.trigger} · 创建：${formatDateTime(job.created_at, "刚刚")}</div>
              <div class="small">完成：${formatDateTime(job.finished_at, "处理中")}</div>
            </div>
          `
        )
        .join("")
    : `<div class="job-row"><strong>还没有任务历史</strong><div class="small">当前 study 还没有触发过重建或定时抓取。</div></div>`;

  document.getElementById("view-dashboard").innerHTML = `
    <section class="hero">
      <div class="card hero-main">
        <p class="eyebrow">本周最重要的判断</p>
        <h1>${appData.summary.headline}</h1>
        <p class="copy">${appData.summary.explanation}</p>
        <div class="metric-row">
          ${appData.summary.metrics.map(metricMarkup).join("")}
        </div>
      </div>
      <div class="side-stack">
        <div class="card side-card">
          <div class="label">今日变化</div>
          <div class="stack">${appData.todayChanged.map(itemMarkup).join("")}</div>
        </div>
        <div class="card side-card">
          <div class="label orange">本周动作</div>
          <div class="stack">${appData.weeklyActions.map(itemMarkup).join("")}</div>
        </div>
      </div>
    </section>

    <section class="grid two">
      <div class="card section-card">
        <div class="section-head">
          <div>
            <div class="label">高价值客群榜</div>
            <h2>谁最值得优先打</h2>
          </div>
          <p>首页只保留业务负责人真正要看的：客群、痛点、机会分、包装分和建议产品。</p>
        </div>
        <div class="stack">${appData.segments.map(segmentCardMarkup).join("")}</div>
      </div>
      <div class="card section-card">
        <div class="section-head">
          <div>
            <div class="label orange">推荐产品包装</div>
            <h2>现在应该怎么卖</h2>
          </div>
          <p>不是展示一堆功能，而是直接给出主产品和次产品建议。</p>
        </div>
        <div class="package-grid">${appData.packages.map(packageMarkup).join("")}</div>
      </div>
    </section>

    <section class="grid equal">
      <div class="card section-card">
        <div class="section-head">
          <div>
            <div class="label">趋势时间序列</div>
            <h2>最近到底在变强还是变弱</h2>
          </div>
          <p>让负责人看到变化方向，而不是只看到静态强弱。</p>
        </div>
        ${trendSeriesMarkup()}
      </div>
      <div class="card section-card">
        <div class="section-head">
          <div>
            <div class="label orange">证据摘要墙</div>
            <h2>为什么可以相信这个判断</h2>
          </div>
          <p>原始帖子不做首页主角，但所有结论都要能追溯到代表性证据。</p>
        </div>
        <div class="stack">${appData.evidence.slice(0, 3).map(evidenceMarkup).join("")}</div>
      </div>
    </section>

    <section class="grid equal">
      <div class="card section-card">
        <div class="section-head">
          <div>
            <div class="label">客群 x 痛点热力图</div>
            <h2>哪个客群最痛在哪里</h2>
          </div>
          <p>热度不是帖子数，而是痛感、密度和趋势动量的组合。</p>
        </div>
        ${heatmapMarkup()}
      </div>
    </section>

    <section class="ops-grid">
      <div class="card section-card">
        <div class="section-head">
          <div>
            <div class="label">任务队列与调度</div>
            <h2>这个 study 怎么持续更新</h2>
          </div>
          <p>让负责人知道现在是静态结论，还是会自动刷新的一条业务情报管线。</p>
        </div>
        <div class="ops-list">
          <div class="ops-stat">
            <div>
              <strong>${currentSchedule.enabled ? "已开启自动调度" : "尚未开启自动调度"}</strong>
              <div class="small">模式：${currentSchedule.mode || "seeded"}</div>
            </div>
            <div class="small">
              下次运行：${formatDateTime(currentSchedule.next_run_at, "未设置")}<br>
              上次运行：${formatDateTime(currentSchedule.last_run_at, "暂无")}
            </div>
          </div>
          <div class="item">
            <strong>当前手动刷新模式</strong>
            <div class="small">${refreshMode}</div>
          </div>
          <div class="job-list">${jobsMarkup}</div>
        </div>
      </div>

      <div class="card section-card">
        <div class="section-head">
          <div>
            <div class="label orange">数据映射与来源</div>
            <h2>为什么系统会得出这个判断</h2>
          </div>
          <p>把来源分布、关键词驱动和机会驱动显式展示出来，避免结论像黑箱。</p>
        </div>
        <div class="mini-list">${sourceBreakdown || `<div class="mini-row"><strong>暂无来源分布</strong></div>`}</div>
        <div class="item">
          <strong>高频关键词</strong>
          <div class="kpi-line">${keywordBreakdown || `<span class="mini-pill">暂无关键词</span>`}</div>
        </div>
        <div class="mini-list">
          ${(appData.opportunityDrivers || [])
            .slice(0, 3)
            .map(
              (driver) => `
                <div class="mini-row">
                  <div class="label">${driver.count} 条样本</div>
                  <strong>${driver.name} → ${driver.offer}</strong>
                  <div class="small">${driver.segment} · 高意向 ${driver.high_intent} 条 · Opportunity ${driver.opportunity_score}</div>
                </div>
              `
            )
            .join("")}
        </div>
      </div>
    </section>
  `;
}

function renderStudySetup() {
  const businessLineOptions = studyTemplate.business_lines
    .map((item) => `<option value="${item}">${item}</option>`)
    .join("");
  const regionOptions = studyTemplate.regions
    .map((item) => `<option value="${item}">${item}</option>`)
    .join("");
  const goalOptions = studyTemplate.primary_goals
    .map((item) => `<option value="${item}">${item}</option>`)
    .join("");

  document.getElementById("view-setup").innerHTML = `
    <section class="hero">
      <div class="card hero-main">
        <p class="eyebrow">Study Setup</p>
        <h1>先定义研究任务，再让系统帮你缩小客群、产品和关键词范围。</h1>
        <p class="copy">这一步不让业务负责人手工配置大矩阵，而是先把业务问题讲清楚：研究哪个市场、哪条业务线、哪类客户、想支持什么决策。</p>
      </div>
      <div class="side-stack">
        <div class="card side-card">
          <div class="label orange">为什么先做这一步</div>
          <div class="stack">
            <div class="item"><strong>避免爬太多无用数据</strong><div class="small">先定义业务问题，系统再反推关键词和来源。</div></div>
            <div class="item"><strong>让输出更像决策产品</strong><div class="small">不是给你帖子列表，而是给你推荐客群、机会假设和包装方向。</div></div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid two">
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label">研究任务配置</div><h2>让系统理解你要判断什么</h2></div>
          <p>先收集最少但足够的业务信息，再自动生成推荐研究范围。</p>
        </div>
        <form id="study-setup-form" class="form-grid">
          <label class="field">
            <span>研究标题</span>
            <input type="text" name="title" value="美国 / Dropshipping 供应链服务 / 履约与 supplier 问题">
          </label>
          <label class="field">
            <span>市场</span>
            <input type="text" name="market" value="美国 dropshipping">
          </label>
          <label class="field">
            <span>业务线</span>
            <select name="business_line">${businessLineOptions}</select>
          </label>
          <label class="field">
            <span>地区</span>
            <select name="region">${regionOptions}</select>
          </label>
          <label class="field">
            <span>目标客群</span>
            <input type="text" name="target_customer" value="已出单但履约混乱的卖家">
          </label>
          <label class="field">
            <span>主要目标</span>
            <select name="primary_goal">${goalOptions}</select>
          </label>
          <label class="field full">
            <span>问题空间</span>
            <textarea name="problem_space" rows="4">履约与发货、private supplier、3PL 切换、shipping delays、退款压力</textarea>
          </label>
          <label class="field">
            <span>时间窗口</span>
            <input type="text" name="time_window" value="近 30 天">
          </label>
          <div class="cta full">
            <button type="submit" class="button primary">生成并保存 Study</button>
          </div>
        </form>
      </div>

      <div class="card section-card">
        <div class="section-head">
          <div><div class="label orange">系统建议</div><h2>自动生成研究范围</h2></div>
          <p>系统会回一份 study draft，帮助负责人更快决定该研究什么，而不是先陷入抓取细节。</p>
        </div>
        <div id="study-draft-panel">
          ${studyDraftMarkup(latestStudyDraft)}
        </div>
        <div class="section-head" style="margin-top: 18px;">
          <div><div class="label">自动调度</div><h2>把研究任务变成持续运行的情报管线</h2></div>
          <p>给业务负责人一个简单的开关：是否自动更新，多久更新一次，要不要立即跑一轮。</p>
        </div>
        <form id="schedule-form" class="form-grid">
          <label class="field">
            <span>Study ID</span>
            <input type="text" name="study_id" value="${currentStudyId}" readonly>
          </label>
          <label class="field">
            <span>运行模式</span>
            <select name="mode">
              <option value="seeded" ${currentSchedule.mode === "seeded" ? "selected" : ""}>seeded</option>
              <option value="browser" ${currentSchedule.mode === "browser" ? "selected" : ""}>browser</option>
            </select>
          </label>
          <label class="field">
            <span>更新间隔（小时）</span>
            <input type="number" min="1" name="interval_hours" value="${currentSchedule.interval_hours || 24}">
          </label>
          <label class="field inline-toggle">
            <input type="checkbox" name="enabled" ${currentSchedule.enabled ? "checked" : ""}>
            <span>启用自动调度</span>
          </label>
          <label class="field inline-toggle full">
            <input type="checkbox" name="start_now">
            <span>保存后立即排队跑一次</span>
          </label>
          <div class="cta full">
            <button type="submit" class="button primary">保存调度配置</button>
          </div>
        </form>
      </div>
    </section>
  `;
}

function renderSegments() {
  const segment = appData.segments[0];
  document.getElementById("view-segments").innerHTML = `
    <section class="hero">
      <div class="card hero-main">
        <p class="eyebrow">当前重点客群</p>
        <h1>${segment.name}</h1>
        <p class="copy">${segment.rationale}</p>
        <div class="metric-row">
          <div class="metric"><strong>${segment.opportunity}</strong><span>Opportunity Score<br>市场值得优先打</span></div>
          <div class="metric"><strong>${segment.packaging}</strong><span>Packaging Readiness<br>产品很容易讲清楚</span></div>
          <div class="metric"><strong>${segment.confidence}</strong><span>Confidence<br>判断稳不稳</span></div>
          <div class="metric"><strong>${segment.actionMode}</strong><span>Action Mode<br>建议如何推进</span></div>
        </div>
      </div>
      <div class="side-stack">
        <div class="card side-card">
          <div class="label">关键市场信号</div>
          <div class="stack">
            ${segment.signals.map((signal) => `<div class="item"><strong>${signal}</strong><div class="small">${segment.pain}</div></div>`).join("")}
          </div>
        </div>
      </div>
    </section>

    <section class="grid two">
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label">客群比较</div><h2>为什么它排第一</h2></div>
          <p>这页要帮助负责人理解，不是所有高热度主题都值得先打。</p>
        </div>
        <table class="table">
          <thead>
            <tr>
              <th>客群</th>
              <th>Opportunity</th>
              <th>Packaging</th>
              <th>推荐产品</th>
            </tr>
          </thead>
          <tbody>
            ${appData.segments
              .map(
                (item) => `
                  <tr>
                    <td>${item.name}<br><span class="small">${item.pain}</span></td>
                    <td>${item.opportunity}</td>
                    <td>${item.packaging}</td>
                    <td>${item.recommendedProduct}</td>
                  </tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label orange">动作建议</div><h2>针对这个客群怎么打</h2></div>
          <p>Segment Explorer 必须让分析自然落到产品和动作。</p>
        </div>
        <div class="stack">
          <div class="item"><strong>推荐产品</strong>${segment.recommendedProduct}</div>
          <div class="item"><strong>推荐承诺</strong>先找出延迟和退款背后的真正 bottleneck</div>
          <div class="item"><strong>推荐入口</strong>Audit 型轻产品</div>
          <div class="item"><strong>不建议主打</strong>泛 sourcing、泛降本</div>
        </div>
      </div>
    </section>
  `;
}

function renderOperations() {
  const visibleJobs = getVisibleOperationsJobs();
  if (!selectedJobId && visibleJobs.length) {
    selectedJobId = visibleJobs[0].id;
  }
  if (selectedJobId && !visibleJobs.some((job) => job.id === selectedJobId)) {
    selectedJobId = visibleJobs[0]?.id || null;
  }
  const selectedJob = (visibleJobs || []).find((job) => job.id === selectedJobId) || null;

  const statusSummary = {
    queued: allJobs.filter((job) => job.status === "queued").length,
    running: allJobs.filter((job) => job.status === "running").length,
    completed: allJobs.filter((job) => job.status === "completed").length,
    failed: allJobs.filter((job) => job.status === "failed").length,
    canceled: allJobs.filter((job) => job.status === "canceled").length,
  };

  const scheduleCards = studyList
    .map(
      (study) => `
        <div class="mini-row ${study.active_job_count ? "is-running" : study.schedule?.enabled ? "is-completed" : ""}">
          <strong>${study.title}</strong>
          <div class="small">${study.market}</div>
          <div class="small">调度：${study.schedule?.enabled ? `开启 / ${study.schedule.interval_hours}h / ${study.schedule.mode}` : "未开启"}</div>
          <div class="small">下次运行：${formatDateTime(study.schedule?.next_run_at, "未设置")}</div>
          <div class="cta">
            <button type="button" class="button secondary" data-run-study-id="${study.id}" data-run-mode="seeded">跑 seeded</button>
            <button type="button" class="button secondary" data-run-study-id="${study.id}" data-run-mode="browser">跑 browser</button>
            <button type="button" class="button secondary" data-toggle-schedule-study-id="${study.id}">
              ${study.schedule?.enabled ? "暂停调度" : "启用调度"}
            </button>
          </div>
        </div>
      `
    )
    .join("");

  const filterTabs = [
    `<button type="button" class="chip ${selectedOperationsStudyId === "all" ? "is-active" : ""}" data-operations-study="all">全部任务</button>`,
    ...studyList.map(
      (study) =>
        `<button type="button" class="chip ${selectedOperationsStudyId === study.id ? "is-active" : ""}" data-operations-study="${study.id}">${study.title}</button>`
    ),
  ].join("");

  const jobRows = visibleJobs
    .slice(0, 12)
    .map(
      (job) => `
        <div class="job-row is-${job.status} ${selectedJobId === job.id ? "is-selected" : ""}" data-open-job-id="${job.id}">
          <strong>${job.study_title || job.study_id}</strong>
          <div class="small">${job.mode} · ${job.status} · ${job.trigger}</div>
          <div class="small">创建：${formatDateTime(job.created_at, "刚刚")} · 完成：${formatDateTime(job.finished_at, "处理中")}</div>
          ${job.error ? `<div class="small">错误：${job.error}</div>` : ""}
        </div>
      `
    )
    .join("");

  document.getElementById("view-operations").innerHTML = `
    <section class="hero">
      <div class="card hero-main">
        <p class="eyebrow">Operations</p>
        <h1>把研究任务当成一条持续运行的情报管线来管理。</h1>
        <p class="copy">这里不是看结论，而是看系统有没有在稳定工作：哪些任务在跑、哪些 study 开了调度、失败了能不能快速重试。</p>
      </div>
      <div class="side-stack">
        <div class="card side-card">
          <div class="label">任务概览</div>
          <div class="stack">
            <div class="item"><strong>Queued</strong><div class="small">${statusSummary.queued}</div></div>
            <div class="item"><strong>Running</strong><div class="small">${statusSummary.running}</div></div>
            <div class="item"><strong>Completed</strong><div class="small">${statusSummary.completed}</div></div>
            <div class="item"><strong>Failed</strong><div class="small">${statusSummary.failed}</div></div>
            <div class="item"><strong>Canceled</strong><div class="small">${statusSummary.canceled}</div></div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid two">
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label">Study 调度总览</div><h2>哪些研究任务在自动刷新</h2></div>
          <p>业务负责人不需要看脚本，只要一眼知道哪些 study 是“活的”。</p>
        </div>
        <div class="mini-list">${scheduleCards || `<div class="mini-row"><strong>暂无 Study</strong></div>`}</div>
      </div>

      <div class="card section-card">
        <div class="section-head">
          <div><div class="label orange">全局任务中心</div><h2>最近 12 条任务</h2></div>
          <p>失败任务可以直接重跑，或者打开对应 Study 深挖。</p>
        </div>
        <div class="filters">${filterTabs}</div>
        <div class="split" style="margin-top: 14px;">
          <div class="job-list">${jobRows || `<div class="job-row"><strong>还没有任务记录</strong></div>`}</div>
          <div class="card side-card">
            <div class="label">任务详情</div>
            ${
              selectedJob
                ? `
                  <div class="stack">
                    <div class="item"><strong>${selectedJob.study_title}</strong><div class="small">${selectedJob.mode} · ${selectedJob.status}</div></div>
                    <div class="item"><strong>触发方式</strong><div class="small">${selectedJob.trigger}</div></div>
                    <div class="item"><strong>创建时间</strong><div class="small">${formatDateTime(selectedJob.created_at, "刚刚")}</div></div>
                    <div class="item"><strong>开始时间</strong><div class="small">${formatDateTime(selectedJob.started_at, "未开始")}</div></div>
                    <div class="item"><strong>结束时间</strong><div class="small">${formatDateTime(selectedJob.finished_at, "处理中")}</div></div>
                    ${selectedJob.error ? `<div class="item"><strong>错误信息</strong><div class="small">${selectedJob.error}</div></div>` : ""}
                    <div class="cta">
                      <button type="button" class="button secondary" data-retry-job-id="${selectedJob.id}">重跑这条任务</button>
                      ${
                        selectedJob.status === "queued"
                          ? `<button type="button" class="button secondary" data-cancel-job-id="${selectedJob.id}">取消排队</button>`
                          : ""
                      }
                      <button type="button" class="button secondary" data-open-study-id="${selectedJob.study_id}">打开对应 Study</button>
                    </div>
                  </div>
                `
                : `<div class="item"><strong>请选择一条任务</strong><div class="small">右侧会展示更完整的执行信息和操作按钮。</div></div>`
            }
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderPackaging() {
  document.getElementById("view-packaging").innerHTML = `
    <section class="hero">
      <div class="card hero-main">
        <p class="eyebrow">Packaging Studio</p>
        <h1>把需求翻译成可卖的产品，而不是把帖子翻译成标签。</h1>
        <p class="copy">这页的输出对象不是研究员，而是业务负责人和销售负责人。系统最终给出的不是“发现了什么”，而是“该卖什么、怎么讲、先不要卖什么”。</p>
      </div>
      <div class="side-stack">
        <div class="card side-card">
          <div class="label">包装判断原则</div>
          <div class="stack">
            <div class="item"><strong>问题要具体</strong>用户能不能一眼觉得“这就是我现在的问题”</div>
            <div class="item"><strong>结果要清楚</strong>能不能一句话说清楚买完得到什么</div>
            <div class="item"><strong>入口要轻</strong>先卖审查和诊断，不先卖重交付</div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid equal">
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label">推荐包装</div><h2>主产品与次产品</h2></div>
          <p>Packaging Studio 的输出要足够具体，能直接搬进销售页或周会。</p>
        </div>
        <div class="package-grid">${appData.packages.map(packageMarkup).join("")}</div>
      </div>
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label orange">替代方案比较</div><h2>为什么不用更大的名字</h2></div>
          <p>避免把产品包装成“听起来高级，但实际打不动用户”的空话。</p>
        </div>
        <div class="insight-grid">
          <div class="insight-card">
            <h3>Supply Chain Optimization</h3>
            <p class="small">太大、太虚，不够接近用户原话。</p>
          </div>
          <div class="insight-card">
            <h3>China Shipping Support</h3>
            <p class="small">有一点接近，但缺少诊断型切入感。</p>
          </div>
          <div class="insight-card">
            <h3>3PL & Fulfillment Audit</h3>
            <p class="small">问题具体，结果可讲，和需求语言最接近。</p>
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderWeekly() {
  document.getElementById("view-weekly").innerHTML = `
    <section class="hero">
      <div class="card hero-main">
        <p class="eyebrow">Weekly Brief</p>
        <h1>下周继续聚焦履约问题，不扩散到泛 sourcing。</h1>
        <p class="copy">Weekly Brief 的目标不是复述数据，而是让负责人 5 分钟内定下周打谁、卖什么、先不做什么。</p>
      </div>
      <div class="side-stack">
        <div class="card side-card">
          <div class="label">本周摘要</div>
          <div class="stack">
            <div class="item"><strong>最重要变化</strong>${appData.weeklyBrief.topChange}</div>
            <div class="item"><strong>主推产品</strong>${appData.weeklyBrief.leadPackage}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid two">
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label">趋势摘要</div><h2>本周不是静态判断，而是方向判断</h2></div>
          <p>周会前先看“最近 6 个窗口里谁在升、谁在平、谁在回落”。</p>
        </div>
        ${trendSeriesMarkup()}
      </div>

      <div class="card section-card">
        <div class="section-head">
          <div><div class="label orange">下周任务</div><h2>团队应该怎么做</h2></div>
          <p>周报不只讲“发现”，还要直接落成行动。</p>
        </div>
        <div class="stack">
          ${appData.weeklyBrief.nextWeek.map((task) => `<div class="item"><strong>${task}</strong><div class="small">作为下周执行清单进入周会。</div></div>`).join("")}
        </div>
      </div>
    </section>

    <section class="grid two">
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label">Top 3 客群</div><h2>本周最值得看的客群</h2></div>
          <p>把分散的热度和证据压缩成一个周会能直接讨论的优先级列表。</p>
        </div>
        <div class="stack">
          ${appData.weeklyBrief.topSegments
            .map((segment, index) => `<div class="item"><strong>${index + 1}. ${segment}</strong><div class="small">${appData.segments[index].recommendedProduct}</div></div>`)
            .join("")}
        </div>
      </div>
    </section>

    <section class="grid equal">
      <div class="card section-card">
        <div class="section-head">
          <div><div class="label">不要做什么</div><h2>需要主动约束的方向</h2></div>
          <p>真正好的周报会告诉团队什么先不要做。</p>
        </div>
        <div class="stack">
          ${appData.weeklyBrief.avoid.map((item) => `<div class="item"><strong>${item}</strong><div class="small">避免资源被分散，保持主打法聚焦。</div></div>`).join("")}
        </div>
      </div>
      <div class="footer-note">
        周报视图的最终目的，是帮助业务负责人在每周决策会前，把“市场变化”和“下周动作”连接起来。<br>
        所以这里不展示原始帖子流，只展示变化、优先级、产品包装和行动建议。
      </div>
    </section>
  `;
}

function listMarkup(items, empty = "暂无数据") {
  if (!items || !items.length) {
    return `<div class="item"><strong>${empty}</strong></div>`;
  }
  return `<div class="stack">${items
    .map((item) => `<div class="item"><strong>${item}</strong></div>`)
    .join("")}</div>`;
}

function studyDraftMarkup(draft) {
  if (!draft) {
    return `
      <div class="empty-state">
        <strong>还没有生成 study draft</strong>
        <div class="small">提交左侧表单后，这里会显示推荐的 subreddit、关键词、机会假设和建议输出。</div>
      </div>
    `;
  }

  return `
    <div class="stack">
      <div class="item">
        <strong>${draft.study.title}</strong>
        <div class="small">${draft.focus_statement}</div>
      </div>
      <div class="panel-grid">
        <div class="item">
          <strong>推荐来源</strong>
          <div class="small">${draft.recommended_sources.join(" / ")}</div>
        </div>
        <div class="item">
          <strong>推荐 Subreddit</strong>
          <div class="small">${draft.recommended_subreddits.join(" / ")}</div>
        </div>
      </div>
      <div class="item">
        <strong>推荐关键词</strong>
        <div class="kpi-line">
          ${draft.recommended_keywords
            .map((keyword) => `<span class="mini-pill">${keyword}</span>`)
            .join("")}
        </div>
      </div>
      <div class="item">
        <strong>推荐机会假设</strong>
        <div class="stack">
          ${draft.recommended_hypotheses
            .map(
              (item) => `
                <div class="item">
                  <strong>${item.name}</strong>
                  <div class="small">${item.description}</div>
                </div>
              `
            )
            .join("")}
        </div>
      </div>
      <div class="item">
        <strong>建议输出</strong>
        <div class="small">${draft.recommended_outputs.join(" / ")}</div>
      </div>
      <div class="item">
        <strong>决策检查清单</strong>
        <div class="small">${draft.decision_checks.join(" / ")}</div>
      </div>
    </div>
  `;
}

function setActiveView(viewId) {
  const visibleViews = getVisibleViews();
  const nextViewId = visibleViews.some((view) => view.id === viewId) ? viewId : "dashboard";
  currentViewId = nextViewId;
  renderTabs(nextViewId);
  views.forEach((view) => {
    const el = document.getElementById(`view-${view.id}`);
    el.classList.toggle("hidden", view.id !== nextViewId);
  });
}

function bindEvents() {
  document.getElementById("view-tabs").addEventListener("click", (event) => {
    const link = event.target.closest("[data-view]");
    if (!link) return;
    event.preventDefault();
    setActiveView(link.dataset.view);
  });

  document.getElementById("study-rail").addEventListener("click", async (event) => {
    const card = event.target.closest("[data-study-id]");
    if (!card) return;
    const nextId = card.dataset.studyId;
    if (!nextId || nextId === currentStudyId) return;
    await hydrateStudy(nextId);
  });

  document.addEventListener("click", async (event) => {
    const trendViewButton = event.target.closest("[data-trend-view]");
    if (trendViewButton) {
      selectedTrendViewKey = trendViewButton.dataset.trendView;
      renderDashboard();
      renderWeekly();
      return;
    }

    const trendSeriesButton = event.target.closest("[data-trend-series]");
    if (trendSeriesButton) {
      selectedTrendSeriesId = trendSeriesButton.dataset.trendSeries;
      renderDashboard();
      renderWeekly();
      return;
    }

    const operationsFilter = event.target.closest("[data-operations-study]");
    if (operationsFilter) {
      selectedOperationsStudyId = operationsFilter.dataset.operationsStudy;
      selectedJobId = null;
      renderOperations();
      return;
    }

    const retryButton = event.target.closest("[data-retry-job-id]");
    if (retryButton) {
      const jobId = retryButton.dataset.retryJobId;
      retryButton.disabled = true;
      try {
        const response = await retryJob(jobId);
        showToast("任务已重跑", `${response.job.study_id} 已重新进入队列。`, "success");
        await new Promise((resolve) => setTimeout(resolve, 800));
        await pollCurrentStudy();
      } catch (error) {
        console.warn("Retry job failed:", error);
        showToast("任务重跑失败", "请检查权限或当前任务模式。", "error");
      } finally {
        retryButton.disabled = false;
      }
      return;
    }

    const cancelButton = event.target.closest("[data-cancel-job-id]");
    if (cancelButton) {
      const jobId = cancelButton.dataset.cancelJobId;
      cancelButton.disabled = true;
      try {
        await cancelJob(jobId);
        showToast("任务已取消", "该任务已从队列中移除。", "warn");
        await new Promise((resolve) => setTimeout(resolve, 600));
        await pollCurrentStudy();
      } catch (error) {
        console.warn("Cancel job failed:", error);
        showToast("取消失败", "当前任务可能已经开始运行。", "error");
      } finally {
        cancelButton.disabled = false;
      }
      return;
    }

    const openStudyButton = event.target.closest("[data-open-study-id]");
    if (openStudyButton) {
      const studyId = openStudyButton.dataset.openStudyId;
      await hydrateStudy(studyId);
      setActiveView("dashboard");
      selectedOperationsStudyId = studyId;
      return;
    }

    const openJobButton = event.target.closest("[data-open-job-id]");
    if (openJobButton) {
      selectedJobId = openJobButton.dataset.openJobId;
      renderOperations();
      return;
    }

    const runStudyButton = event.target.closest("[data-run-study-id]");
    if (runStudyButton) {
      const studyId = runStudyButton.dataset.runStudyId;
      const mode = runStudyButton.dataset.runMode || "seeded";
      runStudyButton.disabled = true;
      try {
        await rebuildStudy(studyId, mode);
        showToast("Study 已入队", `${studyId} 已按 ${mode} 模式进入队列。`, "success");
        await new Promise((resolve) => setTimeout(resolve, 800));
        await pollCurrentStudy();
      } catch (error) {
        console.warn("Run study failed:", error);
        showToast("Study 启动失败", "请检查权限或 browser 模式环境。", "error");
      } finally {
        runStudyButton.disabled = false;
      }
      return;
    }

    const toggleScheduleButton = event.target.closest("[data-toggle-schedule-study-id]");
    if (toggleScheduleButton) {
      const studyId = toggleScheduleButton.dataset.toggleScheduleStudyId;
      const study = getStudyById(studyId);
      if (!study) return;
      toggleScheduleButton.disabled = true;
      try {
        await updateScheduleForStudy({
          study_id: studyId,
          mode: study.schedule?.mode || "seeded",
          interval_hours: study.schedule?.interval_hours || 24,
          enabled: !study.schedule?.enabled,
          start_now: false,
        });
        showToast("调度状态已更新", `${study.title} 现在${study.schedule?.enabled ? "暂停" : "启用"}自动刷新。`, "success");
        await new Promise((resolve) => setTimeout(resolve, 600));
        await pollCurrentStudy();
      } catch (error) {
        console.warn("Toggle schedule failed:", error);
        showToast("调度更新失败", "请检查当前账号权限。", "error");
      } finally {
        toggleScheduleButton.disabled = false;
      }
      return;
    }
  });

  const refreshButton = document.getElementById("refresh-study-button");
  const refreshModeSelect = document.getElementById("refresh-mode-select");
  if (refreshModeSelect) {
    refreshModeSelect.value = refreshMode;
    refreshModeSelect.addEventListener("change", (event) => {
      refreshMode = event.target.value;
      renderDashboard();
    });
  }
  if (refreshButton) {
    refreshButton.addEventListener("click", async () => {
      refreshButton.disabled = true;
      refreshButton.textContent = "刷新中...";
      try {
        await rebuildStudy(currentStudyId, refreshMode);
        showToast("已提交刷新任务", `${currentStudyId} 已按 ${refreshMode} 模式进入队列。`, "warn");
        await new Promise((resolve) => setTimeout(resolve, 1600));
        await refreshStudyList();
        await hydrateStudy(currentStudyId);
      } catch (error) {
        console.warn("Rebuild study fallback:", error);
        showToast("刷新失败", "当前任务没有成功进入队列。", "error");
      } finally {
        refreshButton.disabled = false;
        refreshButton.textContent = "刷新当前 Study";
      }
    });
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest("#study-setup-form");
    if (form) {
      event.preventDefault();

      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());

      try {
        const created = await createStudy(payload);
        latestStudyDraft = created.draft;
        document.getElementById("study-draft-panel").innerHTML = studyDraftMarkup(created.draft);
        await refreshStudyList();
        await hydrateStudy(created.study.id);
      } catch (error) {
        console.warn("Study create fallback:", error);
        latestStudyDraft = buildLocalStudyDraft(payload);
        document.getElementById("study-draft-panel").innerHTML = studyDraftMarkup(latestStudyDraft);
      }
      return;
    }

    const scheduleForm = event.target.closest("#schedule-form");
    if (scheduleForm) {
      event.preventDefault();
      const formData = new FormData(scheduleForm);
      const payload = {
        study_id: formData.get("study_id"),
        mode: formData.get("mode"),
        interval_hours: Number(formData.get("interval_hours") || 24),
        enabled: formData.get("enabled") === "on",
        start_now: formData.get("start_now") === "on",
      };
      try {
        const response = await updateScheduleForStudy(payload);
        if (response?.queued_job) {
          showToast("已保存调度配置", "调度已开启，并已立即排队一轮更新。", "success");
        } else {
          showToast("已保存调度配置", "新的调度规则已生效。", "success");
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await hydrateStudy(currentStudyId);
      } catch (error) {
        console.warn("Schedule update fallback:", error);
        showToast("调度保存失败", "请检查当前账号权限或接口状态。", "error");
      }
    }
  });
}

async function loadApiData() {
  if (!isHttpMode()) {
    return null;
  }
  return apiFetchJson(`/api/studies/${STUDY_ID}/dashboard`);
}

async function loadStudyTemplate() {
  if (!isHttpMode()) {
    return null;
  }
  return apiFetchJson("/api/study-template");
}

async function loadStudyList() {
  if (!isHttpMode()) {
    return null;
  }
  return apiFetchJson("/api/studies");
}

async function createStudyDraft(payload) {
  if (!isHttpMode()) {
    return buildLocalStudyDraft(payload);
  }
  return apiFetchJson("/api/studies/draft", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function createStudy(payload) {
  if (!isHttpMode()) {
    return {
      study: {
        id: "local-demo-study",
        title: payload.title || "本地临时 Study",
      },
      draft: buildLocalStudyDraft(payload),
      payload: fallbackData,
    };
  }
  return apiFetchJson("/api/studies", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function rebuildStudy(studyId, mode = refreshMode) {
  if (!isHttpMode()) {
    return { ok: true };
  }
  return apiFetchJson(`/api/studies/${studyId}/rebuild`, {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
}

async function loadCurrentUser() {
  if (!isHttpMode()) return null;
  const response = await apiFetchJson("/api/auth/me");
  return response.user || null;
}

async function loginDemoAdmin() {
  if (!isHttpMode()) return null;
  const response = await apiFetchJson("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email: "admin@local", password: "admin123" }),
  });
  return response.user || null;
}

async function loadJobsForStudy(studyId) {
  if (!isHttpMode()) return [];
  const response = await apiFetchJson(`/api/studies/${studyId}/jobs`);
  return response.jobs || [];
}

async function loadAllJobs() {
  if (!isHttpMode()) return [];
  const response = await apiFetchJson("/api/jobs");
  return response.jobs || [];
}

async function retryJob(jobId) {
  if (!isHttpMode()) return { queued: true };
  return apiFetchJson(`/api/jobs/${jobId}/retry`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

async function cancelJob(jobId) {
  if (!isHttpMode()) return { canceled: true };
  return apiFetchJson(`/api/jobs/${jobId}/cancel`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

function getStudyById(studyId) {
  return (studyList || []).find((study) => study.id === studyId) || null;
}

function getVisibleOperationsJobs() {
  if (selectedOperationsStudyId === "all") return allJobs || [];
  return (allJobs || []).filter((job) => job.study_id === selectedOperationsStudyId);
}

async function loadScheduleForStudy(studyId) {
  if (!isHttpMode()) return currentSchedule;
  const response = await apiFetchJson(`/api/studies/${studyId}/schedule`);
  return response.schedule || currentSchedule;
}

async function updateScheduleForStudy(payload) {
  if (!isHttpMode()) return { schedule: payload, queued_job: null };
  return apiFetchJson(`/api/studies/${payload.study_id}/schedule`, {
    method: "POST",
    body: JSON.stringify({
      enabled: payload.enabled,
      mode: payload.mode,
      interval_hours: payload.interval_hours,
      start_now: payload.start_now,
    }),
  });
}

function buildLocalStudyDraft(form) {
  const businessLine = form.business_line || "Dropshipping 供应链服务";
  const market = form.market || "美国 dropshipping";
  const targetCustomer = form.target_customer || "已出单但履约混乱的卖家";
  return {
    study: {
      title: form.title || `${market} / ${businessLine}`,
      market,
      business_line: businessLine,
      region: form.region || "美国",
      target_customer: targetCustomer,
      primary_goal: form.primary_goal || "选客群 + 定产品包装",
      problem_space: form.problem_space || "",
      time_window: form.time_window || "近 30 天",
    },
    focus_statement: `围绕 ${market} 的 ${businessLine}，用公开需求信号支持“${form.primary_goal || "选客群 + 定产品包装"}”判断。`,
    recommended_sources: ["Reddit"],
    recommended_subreddits: ["dropship", "dropshipping", "ecommerce", "shopify"],
    recommended_keywords: ["3PL", "fulfillment service", "private supplier", "shipping delays", "sourcing agent", "refunds"],
    recommended_hypotheses: [
      { name: "Fulfillment 主线", description: "优先验证 shipping delays 与 3PL confusion 是否是最值得先打的痛点。" },
      { name: "Supplier 第二主线", description: "保留 private supplier / sourcing agent 作为第二优先级产品方向。" },
    ],
    recommended_outputs: ["Dashboard 每日看板", "Weekly Brief 周会简报", "Packaging Studio 产品包装建议"],
    decision_checks: [
      "哪个客群最值得先打？",
      "该主推 Fulfillment 还是 Supplier？",
      "本周应该先验证哪个 offer？",
    ],
  };
}

function resolveAppData() {
  if (window.__MVP_PAYLOAD__ && typeof window.__MVP_PAYLOAD__ === "object") {
    return window.__MVP_PAYLOAD__;
  }
  return fallbackData;
}

async function hydrateStudy(studyId) {
  currentStudyId = studyId;
  selectedTrendViewKey = null;
  selectedTrendSeriesId = "all";
  appData = await loadApiDataForStudy(studyId);
  try {
    studyJobs = await loadJobsForStudy(studyId);
  } catch (error) {
    console.warn("Job list fallback:", error);
    studyJobs = [];
  }
  try {
    currentSchedule = await loadScheduleForStudy(studyId);
  } catch (error) {
    console.warn("Schedule fallback:", error);
  }
  try {
    allJobs = await loadAllJobs();
  } catch (error) {
    console.warn("Global jobs fallback:", error);
  }
  syncJobNotifications();
  renderMeta();
  renderAuthPanel();
  renderFilterChips();
  renderStudyRail();
  renderDashboard();
  renderStudySetup();
  renderSegments();
  renderPackaging();
  renderWeekly();
  renderOperations();
  setActiveView(currentViewId);
}

async function loadApiDataForStudy(studyId) {
  if (!isHttpMode()) {
    return resolveAppData();
  }
  return apiFetchJson(`/api/studies/${studyId}/dashboard`);
}

async function refreshStudyList() {
  try {
    const response = await loadStudyList();
    if (response?.studies) {
      studyList = response.studies;
    }
  } catch (error) {
    console.warn("Study list fallback:", error);
  }
  renderStudyRail();
}

async function pollCurrentStudy() {
  if (!isHttpMode()) return;
  try {
    const previousActiveCount = lastKnownActiveJobCount;
    appData = await loadApiDataForStudy(currentStudyId);
    studyJobs = await loadJobsForStudy(currentStudyId);
    currentSchedule = await loadScheduleForStudy(currentStudyId);
    allJobs = await loadAllJobs();
    await refreshStudyList();
    renderMeta();
    renderAuthPanel();
    renderFilterChips();
    renderDashboard();
    renderStudySetup();
    renderSegments();
    renderPackaging();
    renderWeekly();
    renderOperations();
    setActiveView(currentViewId);
    syncJobNotifications();
    if (previousActiveCount > 0 && activeJobCount() === 0) {
      showToast("后台任务已完成", `${currentStudyId} 的最新结论已经刷新。`, "success");
    }
  } catch (error) {
    console.warn("Polling current study failed:", error);
  }
}

function startLivePolling() {
  if (!isHttpMode()) return;
  if (pollTimer) window.clearInterval(pollTimer);
  pollTimer = window.setInterval(() => {
    if (activeJobCount() > 0 || currentSchedule.enabled) {
      pollCurrentStudy();
    }
  }, 5000);
}

function boot() {
  renderMeta();
  renderAuthPanel();
  renderFilterChips();
  renderStudyRail();
  renderDashboard();
  renderStudySetup();
  renderSegments();
  renderPackaging();
  renderWeekly();
  renderOperations();
  setActiveView(currentViewId);
  bindEvents();
  startLivePolling();
}

async function init() {
  if (isHttpMode()) {
    try {
      authUser = await loadCurrentUser();
      if (!authUser) {
        authUser = await loginDemoAdmin();
      }
    } catch (error) {
      apiAvailable = false;
      console.warn("Auth bootstrap fallback:", error);
    }
  }

  try {
    const liveData = await loadApiDataForStudy(currentStudyId);
    appData = liveData || resolveAppData();
    selectedTrendViewKey = null;
    selectedTrendSeriesId = "all";
  } catch (error) {
    apiAvailable = false;
    console.warn("Falling back to local payload:", error);
    appData = resolveAppData();
  }

  try {
    const template = await loadStudyTemplate();
    if (template) {
      studyTemplate = template;
    }
  } catch (error) {
    apiAvailable = false;
    console.warn("Falling back to local study template:", error);
  }

  try {
    const response = await loadStudyList();
    if (response?.studies?.length) {
      studyList = response.studies;
      currentStudyId = response.active_study_id || response.studies[0].id;
      appData = await loadApiDataForStudy(currentStudyId);
      studyJobs = await loadJobsForStudy(currentStudyId);
      currentSchedule = await loadScheduleForStudy(currentStudyId);
      allJobs = await loadAllJobs();
      primeJobNotificationState();
    }
  } catch (error) {
    apiAvailable = false;
    console.warn("Falling back to single study mode:", error);
  }

  boot();
}

init();
