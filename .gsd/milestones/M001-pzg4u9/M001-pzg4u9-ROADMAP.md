# M001-pzg4u9: Direction & Momentum

**Vision:** Complete v5.0 — transform the Hawk-O-Meter from a point-in-time snapshot into a momentum tracker with organic distribution and newsletter-based re-engagement.

## Success Criteria

- User sees delta badges (▲/▼) on indicator cards when gauge value changed by ≥5 points since previous run
- User sees Canvas 2D sparklines on indicator cards with ≥3 history data points
- User sees hawk score delta in hero section ("▲ +2.1 since last update")
- Pasting the dashboard URL into any social platform produces a branded 1200×630 preview card
- Share button triggers native share sheet on mobile, clipboard + toast on desktop
- Historical hawk score chart renders from snapshot archive (or placeholder when <4 points)
- "What changed this week" section displays factual template-generated sentences
- Email signup form submits via Netlify Forms with unchecked consent checkbox
- MailerLite double opt-in confirmation flow works end to end
- All existing tests pass (431+ pytest, 28+ Playwright), coverage ≥85%

## Key Risks / Unknowns

- OG image is a design deliverable — must exist before social sharing ships
- MailerLite requires account setup + API credentials — external dependency
- Historical chart needs ≥4 weekly snapshots to render meaningfully — only 2 exist today
- Spam Act 2003 compliance is a legal requirement gating newsletter launch

## Proof Strategy

- OG image requirement → retire in S03 by creating a static branded image and verifying link previews render
- MailerLite dependency → retire in S04 by completing account setup and verifying double opt-in flow
- Snapshot accumulation → retire in S02 by shipping chart with placeholder state and verifying it renders correctly when sufficient data exists
- Spam Act compliance → retire in S04 by verifying unchecked consent, double opt-in, and unsubscribe link

## Verification Classes

- Contract verification: pytest unit tests (pipeline change_summary generation), Playwright E2E (delta badges, sparklines, hero delta, chart, share button, signup form), ESLint + ruff zero violations, per-module coverage ≥85%
- Integration verification: Netlify Forms receives test submission, MailerLite double opt-in flow completes, OG tags render in link preview validators
- Operational verification: pipeline run produces change_summary in status.json, weekly digest email sends after pipeline run
- UAT / human verification: OG image quality on actual social platforms, newsletter content readability, sparkline visual clarity on mobile

## Milestone Definition of Done

This milestone is complete only when all are true:

- All 4 slices delivered and verified
- Indicator cards display delta badges and sparklines with correct zone colours
- Hero section displays hawk score delta with correct directional arrow
- Historical chart and change narrative section render correctly (or show placeholder)
- Link previews verified on at least one social platform
- Share button works on both mobile and desktop
- Netlify Forms receives email submissions
- MailerLite double opt-in configured and tested
- All existing tests pass, coverage ≥85% maintained
- New Playwright tests cover delta badges, sparklines, hero delta, share button, signup form

## Requirement Coverage

- Covers: R001, R002, R003, R004, R005, R006, R007, R008, R009
- Partially covers: none
- Leaves for later: R012 (dynamic OG), R013 (Twitter bot), R014 (affiliate CTA), R015 (momentum Z-score)
- Orphan risks: none

## Slices

- [ ] **S01: Indicator Card Momentum UI** `risk:high` `depends:[]`
  > After this: every indicator card shows delta badges (▲/▼ with magnitude) and Canvas 2D sparklines; hero displays hawk score delta. Verified via Playwright tests with fixture data containing delta fields.

- [ ] **S02: Historical Chart & Change Narrative** `risk:medium` `depends:[]`
  > After this: dashboard shows hawk score trajectory chart with zone colour bands (or placeholder when <4 snapshots), and a "What changed this week" section with factual template-generated sentences. Verified with test fixtures.

- [ ] **S03: Social Sharing** `risk:low` `depends:[]`
  > After this: pasting the dashboard URL produces a branded preview card on social platforms; share button triggers native share sheet on mobile or clipboard copy + toast on desktop. Verified via Playwright and OG tag inspection.

- [ ] **S04: Newsletter Capture & Delivery** `risk:medium` `depends:[S03]`
  > After this: users subscribe via email form with Spam Act 2003 compliant consent; weekly digest auto-sends via MailerLite with double opt-in. Verified via Netlify Forms test submission and MailerLite configuration check.

## Boundary Map

### S01 (Indicator Card Momentum UI)

Produces:
- `public/js/sparklines.js` → SparklineModule.draw(canvasElement, historyArray, color) — Canvas 2D sparkline rendering IIFE
- `public/js/interpretations.js` → createDeltaBadge(metricData) helper — returns DOM element or null
- `public/js/gauge-init.js` → renderHeroDelta(overall) — hero delta DOM insertion
- `public/js/gauge-init.js` → sparkline rendering integration in initGauges() flow
- `public/js/gauge-init.js` → sparkline resize handler in setupResizeHandler()

Consumes:
- `public/data/status.json` → gauges.*.delta, gauges.*.delta_direction, gauges.*.previous_value, gauges.*.history[], overall.hawk_score_delta (from Phase 24)
- `public/js/gauges.js` → GaugesModule.getZoneColor(value), GaugesModule.getDisplayLabel(id) (existing)

### S02 (Historical Chart & Change Narrative)

Produces:
- `pipeline/normalize/engine.py` → change_summary array generation in generate_status()
- `public/js/history-chart.js` → HistoryChartModule — Plotly line chart from snapshot data (new IIFE)
- `public/js/interpretations.js` → renderChangeSummary(changeSummary) — "What changed this week" section
- `public/index.html` → historical chart section + change summary section DOM containers

Consumes:
- `public/data/snapshots/index.json` → snapshot date list (from Phase 24)
- `public/data/snapshots/*.json` → individual snapshot files (from Phase 24)
- `public/data/status.json` → overall.change_summary array (new field)
- `public/js/gauges.js` → GaugesModule.getZoneColor() for zone band colours (existing)

### S03 (Social Sharing)

Produces:
- `public/index.html` → OG meta tags (og:title, og:description, og:image, og:url, og:type) + Twitter Card meta tags
- `public/og-image.png` → static branded 1200×630 OG image
- `public/js/main.js` or `public/js/gauge-init.js` → share button with Web Share API + clipboard fallback + toast

Consumes:
- nothing from other slices (standalone)

### S04 (Newsletter Capture & Delivery)

Produces:
- `public/index.html` → email signup form (Netlify Forms) + confirmation page reference
- `public/thank-you.html` → post-submission confirmation page
- MailerLite account configuration (double opt-in, digest template, unsubscribe)

Consumes from S03:
- Social sharing establishes organic traffic before asking for email signups (sequencing dependency)
