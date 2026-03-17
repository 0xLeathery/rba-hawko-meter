# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R001 — Indicator card delta badges
- Class: primary-user-loop
- Status: active
- Description: Each indicator card displays a directional badge (▲/▼) with magnitude when |delta| ≥ 5 gauge points. Cards with no previous value show no badge.
- Why it matters: Users see at a glance which indicators are moving and by how much — the core "momentum" value proposition.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Delta threshold of 5 is a frontend display concern. Pipeline provides raw deltas. Zone colour via element.style hex.

### R002 — Indicator card sparklines
- Class: primary-user-loop
- Status: active
- Description: Each indicator card displays a Canvas 2D sparkline from the existing history[] array in status.json, coloured by zone. Indicators with fewer than 3 history points show "Building history..." placeholder.
- Why it matters: Sparklines give instant trend context without requiring users to interpret numbers.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Canvas 2D (not Plotly) — 8 Plotly instances already, Firefox freezes above ~15. New sparklines.js IIFE module. 40px max height, full card width, no axes.

### R003 — Hero hawk score delta
- Class: primary-user-loop
- Status: active
- Description: Hero section displays the hawk score delta since the previous pipeline run, with directional arrow and "since last update" wording.
- Why it matters: The most important momentum signal — "is the overall pressure rising or falling?"
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: No delta data (cold start) = no element rendered. Zero delta = "No change since last update" in gray.

### R004 — Historical hawk score chart
- Class: primary-user-loop
- Status: active
- Description: Dashboard displays a Plotly line chart of weekly hawk score values from the snapshot archive, with zone colour bands in the background.
- Why it matters: Shows score trajectory over time — the visual answer to "are things getting better or worse?"
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: When fewer than 4 data points exist, shows "Building history — check back next week" placeholder. Data accumulates automatically from Phase 24 snapshots.

### R005 — Change narrative in status.json
- Class: primary-user-loop
- Status: active
- Description: Pipeline generates a change_summary array of factual, template-generated sentences describing what moved since the previous run. Dashboard renders a "What changed this week" section from this data.
- Why it matters: Answers "what happened?" in plain English without requiring users to diff gauge values manually.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Template-based Python (not LLM). ASIC-compliant factual statements only. Absent when no previous snapshot exists.

### R006 — Open Graph and Twitter Card meta tags
- Class: launchability
- Status: active
- Description: index.html contains OG meta tags (og:title, og:description, og:image, og:url, og:type) and Twitter Card meta tags. Static 1200×630 branded OG image committed to public/.
- Why it matters: Link previews are the first impression for organic sharing — a bare URL with no preview card looks amateur.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: Static OG image is a design deliverable. Dynamic OG image deferred (R011).

### R007 — Share button
- Class: primary-user-loop
- Status: active
- Description: Share button in hero section uses Web Share API on mobile (native share sheet), falls back to clipboard copy + toast notification on desktop.
- Why it matters: Reduces friction from "I want to share this" to "shared" — critical for organic distribution.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: No external dependencies. Toast is a temporary DOM element, not a library.

### R008 — Email signup form (Netlify Forms)
- Class: launchability
- Status: active
- Description: Dashboard displays an email signup form that submits via Netlify Forms with an unchecked consent checkbox by default. Redirects to confirmation page.
- Why it matters: First step in the newsletter funnel — captures interested users for re-engagement.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: Australian Spam Act 2003 requires unchecked consent. data-netlify attribute on form. Honeypot field for spam prevention.

### R009 — MailerLite double opt-in and weekly digest
- Class: continuity
- Status: active
- Description: MailerLite configured with double opt-in. Weekly digest email template auto-assembles hawk score, zone, top movers, and change narrative from status.json data.
- Why it matters: The newsletter is the retention loop — turns one-time visitors into weekly readers.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: MailerLite account setup + API credentials required. Spam Act 2003: functional unsubscribe mandatory.

## Validated

### R010 — Pipeline snapshot archiving with delta injection
- Class: core-capability
- Status: validated
- Description: Pipeline archives current status.json as dated snapshot before each run, injects previous_value/delta/delta_direction per gauge and previous_hawk_score/hawk_score_delta in overall block. Rolling 52-file cap enforced.
- Why it matters: Foundation for all momentum features — without archived snapshots, there's no "previous" to compare against.
- Source: user
- Primary owning slice: Phase 24
- Supporting slices: none
- Validation: validated
- Notes: Phase 24 complete. archive.py at 100% coverage. 441 tests passing.

### R011 — Archive module test coverage at 85%+
- Class: quality-attribute
- Status: validated
- Description: archive.py has unit test coverage enforced by existing coverage gate.
- Why it matters: Archive is a new critical path module — must be as guarded as existing pipeline modules.
- Source: user
- Primary owning slice: Phase 24
- Supporting slices: none
- Validation: validated
- Notes: Achieved 100% coverage. Enforced by check_coverage.py in pre-push hook.

## Deferred

### R012 — Dynamic OG image generation
- Class: differentiator
- Status: deferred
- Description: Generate OG image showing current hawk score dynamically (requires Pillow pipeline integration).
- Why it matters: Live score in link previews increases click-through from social platforms.
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred until static OG image proves the sharing concept works.

### R013 — Twitter/X auto-posting bot
- Class: differentiator
- Status: deferred
- Description: Automated weekly score posting to Twitter/X.
- Why it matters: Distribution channel — reaches users where they already are.
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: $100/mo API cost. Defer until revenue covers it.

### R014 — Mortgage broker affiliate CTA
- Class: differentiator
- Status: deferred
- Description: Single disclosed "find a broker" affiliate CTA with ASIC RG 244 compliant framing.
- Why it matters: Monetization path for a free tool.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Needs ASIC legal review. Performance-based links may constitute "arranging" under Corporations Act 2001.

### R015 — Momentum Z-score (second derivative)
- Class: differentiator
- Status: deferred
- Description: Show acceleration/deceleration per indicator as a momentum Z-score.
- Why it matters: Adds "is the change itself accelerating?" — a second layer of trend analysis.
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Requires sufficient snapshot history. Complex to present clearly to laypeople.

## Out of Scope

### R016 — LLM-generated narrative
- Class: anti-feature
- Status: out-of-scope
- Description: Using an LLM to generate change summaries instead of templates.
- Why it matters: Prevents hallucination risk on numerical data, ASIC compliance concerns, and unnecessary cost/latency.
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Template-based Python covers 95% of value.

### R017 — Push notifications
- Class: constraint
- Status: out-of-scope
- Description: Browser push notifications for score changes.
- Why it matters: Netlify static hosting is incompatible with the required service worker backend.
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Newsletter serves the re-engagement purpose without infrastructure requirements.

### R018 — Paid newsletter subscription model
- Class: anti-feature
- Status: out-of-scope
- Description: Charging for newsletter access.
- Why it matters: Reduces reach. Affiliate referrals generate more revenue per user at small scale.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Free newsletter maximises distribution; monetise via affiliate CTA in email footer.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | active | M001/S01 | none | unmapped |
| R002 | primary-user-loop | active | M001/S01 | none | unmapped |
| R003 | primary-user-loop | active | M001/S01 | none | unmapped |
| R004 | primary-user-loop | active | M001/S02 | none | unmapped |
| R005 | primary-user-loop | active | M001/S02 | none | unmapped |
| R006 | launchability | active | M001/S03 | none | unmapped |
| R007 | primary-user-loop | active | M001/S03 | none | unmapped |
| R008 | launchability | active | M001/S04 | none | unmapped |
| R009 | continuity | active | M001/S04 | none | unmapped |
| R010 | core-capability | validated | Phase 24 | none | validated |
| R011 | quality-attribute | validated | Phase 24 | none | validated |
| R012 | differentiator | deferred | none | none | unmapped |
| R013 | differentiator | deferred | none | none | unmapped |
| R014 | differentiator | deferred | none | none | unmapped |
| R015 | differentiator | deferred | none | none | unmapped |
| R016 | anti-feature | out-of-scope | none | none | n/a |
| R017 | constraint | out-of-scope | none | none | n/a |
| R018 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 9
- Mapped to slices: 9
- Validated: 2
- Unmapped active requirements: 0
