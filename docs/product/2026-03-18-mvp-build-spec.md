# MVP Build Spec

## Build Goal

Turn the decision-product prototype into a build-ready MVP for one business line.

The MVP must help a business-line leader:

- select high-value segments
- choose the best product package
- monitor what changed this week

## Frontend Views

### 1. Dashboard

Purpose:

- daily review
- fast prioritization

Key blocks:

- summary hero
- today changed
- high-value segment ranking
- recommended packages
- heatmap
- evidence highlights

### 2. Segment Explorer

Purpose:

- inspect one segment in depth

Key blocks:

- selected segment summary
- segment comparison table
- key pain signals
- recommended actions

### 3. Packaging Studio

Purpose:

- convert demand signals into sellable product packaging

Key blocks:

- recommended package cards
- messaging angles
- alternative naming comparison

### 4. Weekly Brief

Purpose:

- direct weekly strategy readout

Key blocks:

- weekly conclusion
- top 3 segments
- lead package
- do not do list
- next week actions

## Core Entities

### Study

Represents one research workspace.

Fields:

- id
- title
- market
- business_line
- region
- date_range
- updated_at
- confidence

### SourceItem

Normalized raw content item from a source platform.

Fields:

- id
- source_platform
- source_community
- author_id
- published_at
- url
- title
- body_summary
- language
- region_tags[]
- market_tags[]
- intent_tags[]
- commercial_signal_tags[]
- segment_tags[]
- pain_tags[]
- emotional_intensity
- specificity_score
- evidence_quality_score

### Segment

Decision-ready audience cluster.

Fields:

- id
- name
- stage
- buying_state
- problem_context
- core_pain
- opportunity_score
- packaging_readiness_score
- confidence
- trend_label
- action_mode
- recommended_package_id
- rationale
- signal_count

### PackageRecommendation

Suggested product package generated from segment + pain signals.

Fields:

- id
- name
- rank
- target_segment_id
- core_problem
- one_line_promise
- entry_format
- message_angle
- why_now
- do_not_lead_with

### EvidenceHighlight

Representative proof item shown in dashboard and weekly brief.

Fields:

- id
- source_item_id
- quote_summary
- source_platform
- source_community
- segment_id
- pain_tag
- relevance_package_id

### WeeklyBrief

Prebuilt strategy summary.

Fields:

- id
- study_id
- generated_at
- top_change
- lead_segment_ids[]
- lead_package_id
- avoid_list[]
- next_actions[]

## API Shape

### GET /api/studies/:id/dashboard

Returns:

- study
- summary
- today_changed[]
- top_segments[]
- package_recommendations[]
- evidence_highlights[]
- heatmap
- weekly_actions[]

### GET /api/studies/:id/segments

Returns:

- segment list with scores and recommendation references

### GET /api/studies/:id/segments/:segmentId

Returns:

- segment
- key_signals[]
- comparison_rows[]
- recommended_actions[]

### GET /api/studies/:id/packages

Returns:

- package_recommendations[]
- packaging_comparisons[]

### GET /api/studies/:id/weekly-brief

Returns:

- weekly_brief
- lead_segments[]
- lead_package

## Example JSON Contracts

### Dashboard Response

```json
{
  "study": {
    "id": "fishgoo-us-dropshipping",
    "title": "美国 dropshipping / 履约与 supplier 问题",
    "market": "美国 dropshipping",
    "date_range": "30d",
    "updated_at": "2026-03-18T09:20:00+08:00",
    "confidence": "high"
  },
  "summary": {
    "headline": "优先打已出单但履约混乱的卖家，主推 Fulfillment Audit",
    "explanation": "shipping delays 和 3PL confusion 的高意向表达明显升温",
    "metrics": [
      { "key": "opportunity_score", "value": 86, "note": "市场值得优先打" },
      { "key": "packaging_readiness", "value": 82, "note": "很适合做清晰 offer" }
    ]
  },
  "today_changed": [],
  "top_segments": [],
  "package_recommendations": [],
  "evidence_highlights": [],
  "heatmap": {
    "columns": [],
    "rows": []
  },
  "weekly_actions": []
}
```

### Segment Response

```json
{
  "segment": {
    "id": "operating-replacing-fulfillment",
    "name": "运营期 / 替换中 / 履约与发货",
    "opportunity_score": 86,
    "packaging_readiness_score": 82,
    "confidence": "high",
    "recommended_package_id": "fulfillment-audit"
  },
  "key_signals": [
    "shipping delays tied to refund pressure",
    "users explicitly asking for 3PL help"
  ],
  "comparison_rows": [],
  "recommended_actions": [
    "主推 3PL & Fulfillment Audit"
  ]
}
```

## Scoring Pipeline Notes

### Opportunity Score

Inputs:

- pain intensity
- demand density
- trend momentum
- commercial value
- strategic fit

### Packaging Readiness Score

Inputs:

- problem clarity
- result definability
- value proposition clarity
- delivery certainty
- evidence strength

### Confidence

Inputs:

- source count
- source diversity
- language consistency
- freshness

## Engineering Guidance

### Frontend

- Start with a single-page app or server-rendered page using one route and one dataset.
- Treat Dashboard as the default view.
- Keep evidence as a secondary layer, not the primary surface.

### Backend

- Start with one source ingestion pipeline.
- Normalize everything into SourceItem first.
- Run classification and scoring after normalization.

### Product Logic

- Do not let users configure large keyword matrices in the main flow.
- Main user input should be study intent, market, and business line.
- Keyword expansion and clustering belong behind the scenes.

## First Engineering Milestone

1. Build one backend route that returns a dashboard payload.
2. Replace mock data in `mvp-app.js` with live payload loading.
3. Add one deep-dive segment route.
4. Generate a weekly brief payload from the same scoring pipeline.
