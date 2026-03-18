# Demand Intelligence Decision Desk

## Product Definition

### One-line Positioning

This is not a crawler dashboard. It is a decision product for CEOs and business-line leaders to choose target segments, shape offers, and spot high-value demand shifts before they become obvious.

### Primary User

- Business-line leader

### Secondary User

- CEO
- Strategy / market research lead

### Core Jobs To Be Done

1. Understand which customer segment is worth prioritizing now.
2. Understand what pain is strong enough to become a sellable product.
3. Decide how to package that product in language the market already uses.
4. Monitor whether a demand pocket is rising, flattening, or cooling.

## First-Principles Product View

The user does not want:

- raw posts
- keyword lists
- crawler settings
- hundreds of filters

The user wants:

- clarity
- prioritization
- evidence
- a recommended action

The smallest meaningful unit in this product is not a post.

It is a **decision-ready market conclusion** supported by evidence.

## Product Principles

1. Conclusion first. Evidence second.
2. Show change, not just volume.
3. Every insight must lead to an action.
4. Raw data is a support layer, not the home screen.
5. Make it usable in 3 minutes for daily review and 15 minutes for weekly decisions.

## Product Scope For MVP

### Product Goal

Help a business-line leader answer:

- Which segment should we target?
- What pain is strongest?
- What product package should we lead with?
- What changed this week?

### Output Types

- daily view
- weekly strategy brief
- deep-dive market workspace

### Data Sources In MVP

- Reddit first

MVP should support more sources later, but the product structure must already assume multiple sources.

## Information Architecture

### 1. Dashboard

Purpose:

- daily review
- weekly meeting prep

Modules:

- Today Changed
- High-value Segment Ranking
- Segment x Pain Heatmap
- Recommended Product Packages
- Evidence Wall
- This Week's Suggested Actions

### 2. Segment Explorer

Purpose:

- compare segments
- inspect one segment in depth

Views:

- segment overview
- pain composition
- trend chart
- buying readiness
- recommended entry offer

### 3. Packaging Studio

Purpose:

- turn demand into sellable offers

Outputs:

- product name
- target segment
- core problem
- one-line promise
- best entry format
- message angles
- what not to lead with

### 4. Evidence Wall

Purpose:

- prove conclusions
- allow fast drill-down without turning the whole product into a feed reader

## Dashboard Module Definitions

### Module 1: Today Changed

Question answered:

- What deserves attention today?

Fields:

- demand theme
- affected segment
- direction
- change rate
- urgency
- one-line explanation
- suggested action

### Module 2: High-value Segment Ranking

Question answered:

- Who should we prioritize now?

Fields:

- segment name
- opportunity score
- packaging readiness score
- confidence
- core pain
- recommended product
- action mode

### Module 3: Segment x Pain Heatmap

Question answered:

- Which segment hurts where?

Rows:

- segment

Columns:

- acquisition and conversion
- supplier and sourcing
- fulfillment and shipping
- quality and risk
- cost and margin
- systems and process

### Module 4: Recommended Product Packages

Question answered:

- What exactly should we sell?

Fields:

- recommended product name
- target segment
- problem to lead with
- one-line value proposition
- entry format
- message angle
- reasons
- do-not-lead-with

### Module 5: Evidence Wall

Question answered:

- Why should we trust this conclusion?

Fields:

- quote summary
- source
- date
- segment tag
- pain tag
- product relevance
- original link

### Module 6: This Week's Suggested Actions

Question answered:

- What should the team do this week?

Fields:

- priority segment
- priority product
- key message to test
- deprioritized direction
- watchlist trend
- weekly objective

## Segment Framework

Do not segment first by platform or industry label.

Segment first by:

### Layer 1: Business Stage

- exploration
- validation
- operating
- expansion
- restructure

### Layer 2: Buying State

- becoming aware
- comparing
- replacing
- actively seeking help

### Layer 3: Problem Context

- acquisition and conversion
- supplier and sourcing
- fulfillment and shipping
- quality and risk
- cost and margin
- systems and process

Example segment:

- operating / replacing / fulfillment and shipping

That is far more decision-useful than just "dropshipper".

## Pain Taxonomy

### Level 1

- acquisition and conversion
- supplier and sourcing
- fulfillment and shipping
- quality and risk
- cost and margin
- systems and process

### Level 2 Examples

Supplier and sourcing:

- unreliable supplier
- private supplier search
- sourcing agent selection
- MOQ mismatch
- communication failure

Fulfillment and shipping:

- shipping delays
- 3PL confusion
- refund pressure
- delivery inconsistency
- shipping cost pressure

Quality and risk:

- QC instability
- fake supplier
- wrong item
- sample mismatch
- high trust risk

## Scoring Model

### Opportunity Score

Question answered:

- Is this worth prioritizing now?

Dimensions:

- pain intensity 25%
- demand density 15%
- trend momentum 20%
- commercial value 20%
- strategic fit 20%

### Packaging Readiness Score

Question answered:

- Can this be turned into a clear sellable offer quickly?

Dimensions:

- problem clarity 25%
- result definability 25%
- value proposition clarity 20%
- delivery certainty 15%
- evidence strength 15%

### Confidence

Separate from the score.

Confidence is based on:

- sample volume
- source diversity
- evidence consistency
- freshness

Values:

- high
- medium
- low

### Action Mode

Derived from scores plus confidence.

Values:

- test now
- monitor
- defer

## Required Structured Fields

To support the product, each collected item must be normalized into:

- source platform
- source community
- publish time
- author id
- title
- body summary
- original url
- segment tags
- pain tags
- market tag
- region tag
- intent tag
- commercial signal tag
- emotional intensity
- specificity score
- evidence quality score

## Packaging Output Template

For every strong demand pocket, the system should output:

1. Recommended product name
2. Target segment
3. Core problem
4. One-line promise
5. Best entry format
6. Recommended message angle
7. Why this package now
8. What not to lead with

Example:

- product name: 3PL and Fulfillment Audit
- target segment: operating / replacing / fulfillment and shipping
- core problem: delays and refund pressure caused by unstable fulfillment structure
- one-line promise: identify the bottleneck before fulfillment chaos eats margin
- entry format: light audit
- do not lead with: generic sourcing

## Weekly Brief Template

The weekly brief should not read like a report. It should read like a decision memo.

Sections:

1. Most important change this week
2. Top 3 segments worth attention
3. Product package we should test now
4. What is rising but not yet mature
5. What to deprioritize
6. Recommended action for next week

## MVP Boundaries

### In

- single business line
- Reddit as first source
- executive dashboard
- segment explorer
- packaging studio
- evidence wall
- daily and weekly summary output

### Out

- complex workflow automation
- CRM sync
- multi-tenant billing
- advanced role permissions
- fully self-serve source configuration
- giant post management interface

## Product Risks

1. Too much raw data, not enough conclusion.
2. Keyword-tool thinking leaking into the main experience.
3. Overcomplicated segmentation in V1.
4. High score without enough confidence.
5. Product recommendations that are not tied to actual delivery capability.

## Product Decision

This MVP should be built as:

- a single-business-line decision product
- used daily by the business-line leader
- reviewed weekly before strategy meetings
- optimized for selecting segments and shaping product packaging

It should not be built as a generic crawler dashboard.

## Next Build Artifacts

1. dashboard wireframe
2. segment card component spec
3. package recommendation card spec
4. weekly brief view
5. scoring pipeline definition
