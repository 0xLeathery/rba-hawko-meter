# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| D001 | M001/S01 | arch | Sparkline rendering engine | Canvas 2D (new sparklines.js IIFE) | 8 Plotly instances already; Firefox freezes above ~15. Canvas 2D is ~40 lines, no library needed | No |
| D002 | M001/S01 | convention | Delta badge threshold | \|delta\| ≥ 5 gauge points (frontend display concern) | Suppresses daily ASX futures noise; pipeline provides raw deltas | Yes — if user feedback says threshold too high/low |
| D003 | M001/S01 | convention | Delta direction field name | delta_direction (not direction) | Avoids collision with business_confidence's existing direction field (RISING/FALLING/STEADY) | No |
| D004 | M001/S01 | pattern | Colour application | element.style with hex from getZoneColor() | Tailwind CDN drops dynamically concatenated classes; established project convention | No |
| D005 | M001/S01 | convention | Sparkline dimensions | 40px max height, full card width, no axes/labels, stroke-only with end-dot | Glanceable trend indicator, not a data exploration tool | Yes — if users want more detail |
| D006 | M001/S02 | arch | Historical chart rendering | Plotly.js (reuse existing library) | Already loaded for gauges; line chart is a different chart type, not another gauge instance | No |
| D007 | M001/S02 | convention | Change narrative generation | Template-based Python (not LLM) | No hallucination risk on numerical data, ASIC compliant, zero cost, deterministic | No |
| D008 | M001/S04 | library | Newsletter delivery service | MailerLite | Free plan: 1,000 subs / 12,000 emails/month. Mailchimp slashed to 500 contacts Jan 2026 | Yes — if scale requires migration |
| D009 | M001/S04 | convention | Email consent model | Unchecked checkbox + double opt-in | Australian Spam Act 2003 requirement — unchecked consent, double opt-in, functional unsubscribe mandatory | No |
