# M001-pzg4u9: Direction & Momentum

**Gathered:** 2026-03-17
**Status:** Ready for planning

## Project Description

Complete the v5.0 milestone for the RBA Hawk-O-Meter — transforming the dashboard from a point-in-time snapshot into a momentum tracker with organic distribution and newsletter re-engagement. Phase 24 (pipeline temporal layer) already shipped; this milestone covers the remaining four capabilities: indicator card momentum UI, historical chart with change narrative, social sharing, and newsletter capture + delivery.

## Why This Milestone

The dashboard answers "where are we?" but not "which direction are we heading?" — the most useful question for mortgage holders. Without momentum indicators, sparklines, and change narrative, users have to mentally diff values between visits. Without sharing and newsletter, the tool has no distribution loop — growth depends entirely on users remembering to come back.

## User-Visible Outcome

### When this milestone is complete, the user can:

- See at a glance which indicators are rising or falling (delta badges) and their trend shape (sparklines)
- See the hawk score delta in the hero section ("▲ +2.1 since last update")
- Share the dashboard URL and see a branded preview card on Facebook, LinkedIn, Twitter/X, iMessage
- Tap share on mobile to get the native share sheet, or click share on desktop to copy URL + see toast
- View a historical chart showing hawk score trajectory over time with zone colour bands
- Read "What changed this week" as factual plain-English sentences
- Subscribe to a weekly email digest that auto-delivers hawk score, zone, and top movers

### Entry point / environment

- Entry point: https://rbahawkometer.com.au (Netlify static site)
- Environment: browser (desktop + mobile responsive)
- Live dependencies involved: Netlify Forms (form submission), MailerLite (email delivery), GitHub Actions (pipeline runs)

## Completion Class

- Contract complete means: all frontend features render correctly with test data, pipeline generates change_summary, Playwright tests cover new UI elements, existing 431+ tests pass
- Integration complete means: Netlify Forms receives submissions, MailerLite double opt-in flow works, OG image renders in link previews
- Operational complete means: weekly pipeline run generates fresh change_summary and snapshots, newsletter digest auto-sends after pipeline run

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A user visiting the dashboard sees delta badges on moved indicators, sparklines on all cards with history, and a hawk score delta in the hero
- Pasting the URL into a social platform produces a branded preview card with title and description
- The historical chart renders (or shows placeholder when <4 data points)
- An email signup submits to Netlify Forms and the subscriber receives a double opt-in confirmation
- All existing tests pass (431+ pytest, 28+ Playwright), coverage ≥85% maintained

## Risks and Unknowns

- **OG image is a design deliverable** — must be created (designed or generated) before social sharing can ship. Cannot be automated without Pillow integration (deferred).
- **MailerLite setup requires account + API credentials** — external service dependency that can't be tested locally without real credentials.
- **Historical chart needs accumulated snapshots** — only 2 exist today. Chart ships with placeholder state; data accumulates automatically from Phase 24.
- **Spam Act 2003 compliance** — unchecked consent checkbox, double opt-in, functional unsubscribe are legal requirements, not nice-to-haves.
- **Housing and business_confidence scrapers failing** — 5 of 7 indicators active in production status.json. Pre-existing issue, not introduced by v5.0.

## Existing Codebase / Prior Art

- `pipeline/normalize/archive.py` — Phase 24 snapshot save/load/delta injection (100% coverage)
- `pipeline/normalize/engine.py` — generate_status() already calls archive functions, outputs status.json
- `public/js/gauges.js` — GaugesModule.getZoneColor(), getDisplayLabel(), Plotly gauge rendering
- `public/js/interpretations.js` — InterpretationsModule.renderMetricCard(), renderVerdict(), DOM construction patterns
- `public/js/gauge-init.js` — Orchestrator: fetches data, renders all modules, setupResizeHandler()
- `public/data/status.json` — Current pipeline output consumed by frontend
- `public/data/snapshots/` — Rolling snapshot archive (2 files so far)
- `.planning/phases/25-indicator-card-ui/25-CONTEXT.md` — Detailed Phase 25 decisions from prior discussion (delta badge placement, sparkline design, IIFE module structure)
- `.planning/phases/25-indicator-card-ui/25-RESEARCH.md` — Phase 25 domain research with code examples and pitfall analysis

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001-R003 — Indicator card momentum UI (delta badges, sparklines, hero delta)
- R004-R005 — Historical chart and change narrative
- R006-R007 — Social sharing (OG tags, share button)
- R008-R009 — Newsletter capture and delivery

## Scope

### In Scope

- Delta badges on indicator cards (▲/▼ with magnitude ≥5 points)
- Canvas 2D sparklines from history[] arrays (new sparklines.js IIFE module)
- Hero hawk score delta display
- Historical hawk score Plotly line chart with zone colour bands
- Pipeline-generated change_summary in status.json (template-based, not LLM)
- "What changed this week" dashboard section
- OG + Twitter Card meta tags with static branded image
- Share button (Web Share API + clipboard fallback + toast)
- Email signup form via Netlify Forms (unchecked consent checkbox)
- MailerLite double opt-in integration
- Weekly digest email template

### Out of Scope / Non-Goals

- Dynamic OG image generation (deferred — R012)
- Twitter/X auto-posting bot (deferred — R013)
- Affiliate CTA (deferred — R014)
- LLM-generated narratives (out of scope — R016)
- Push notifications (out of scope — R017)
- Fixing housing/business_confidence scraper failures (pre-existing, separate concern)
- Dark/light theme toggle
- Plotly.js or Tailwind version upgrades

## Technical Constraints

- No npm build step — all frontend JS is vanilla IIFE modules loaded via script tags
- All colours via element.style with hex values from getZoneColor() — never Tailwind class concatenation (CDN drops dynamic classes)
- No innerHTML — createElement/textContent/appendChild only (ESLint enforced)
- Canvas 2D for sparklines — NOT Plotly (8 Plotly instances already; Firefox freezes above ~15)
- Existing quality gate: ruff + ESLint zero violations, 85%+ per-module coverage, Playwright E2E
- delta_direction field (not direction) — avoids collision with business_confidence's existing direction field

## Integration Points

- **Netlify Forms** — data-netlify attribute on HTML form; submissions appear in Netlify dashboard
- **MailerLite** — API for subscriber management and email sending; double opt-in configuration
- **GitHub Actions** — existing weekly-pipeline.yml and daily-asx-futures.yml commit updated data files
- **Web Share API** — browser-native, progressive enhancement (fallback to clipboard)

## Open Questions

- **OG image creation method** — Will need a static 1200×630 image. Could be designed manually or generated with a simple script. Needs to exist before S03 ships.
- **MailerLite free tier limits** — Free plan supports 1,000 subscribers and 12,000 emails/month. Sufficient for launch but worth noting.
