# Requirements: RBA Hawk-O-Meter

**Defined:** 2026-02-26
**Core Value:** "Data, not opinion." — Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

## v4.0 Requirements

Requirements for v4.0 Dashboard Visual Overhaul milestone. Each maps to roadmap phases starting at Phase 21.

### Hero Section

- [x] **HERO-01**: User sees the verdict label ("RATES LIKELY FALLING") as the dominant above-the-fold element — large, zone-coloured, immediately legible without scrolling
- [x] **HERO-02**: User sees the hawk score as a prominent number (e.g. "38/100") in the hero card alongside the verdict
- [x] **HERO-03**: User sees the scale explainer ("0 = Strongly Dovish → 100 = Strongly Hawkish") adjacent to the verdict in the hero card, not below the fold
- [x] **HERO-04**: User sees a data freshness badge inside the hero card showing when the data was last updated
- [x] **HERO-05**: User sees a zone-coloured accent border on the hero card that reflects the current hawk/dove/neutral zone
- [x] **HERO-06**: User sees the hero card animate in with a fadeSlideIn entry effect when page data loads

### Verdict Explanation

- [x] **EXPL-01**: User sees a plain-English list of the top hawkish indicators driving the score up (top 3 by contribution)
- [x] **EXPL-02**: User sees a plain-English list of the top dovish indicators driving the score down (top 2 by contribution)
- [x] **EXPL-03**: Neutral indicators (near 50, low contribution) are omitted from the explanation section to avoid clutter
- [x] **EXPL-04**: All explanation copy uses ASIC-compliant hedged language ("tends to", "historically associated with", "the data is consistent with") — no predictions or recommendations

### Visual Polish

- [x] **POLX-01**: User perceives a consistent typography hierarchy across the dashboard: large verdict/score in hero, clear secondary labels, readable body text, subtle metadata
- [x] **POLX-02**: Zone colour (blue/grey/red) is applied consistently and only to: verdict label, hero card border, and explanation section headings — no other elements
- [x] **POLX-03**: User perceives consistent spacing and padding across all dashboard sections (no tight or misaligned elements)
- [x] **POLX-04**: User on a 375px-wide phone sees the hero verdict and score above the fold with no layout congestion

### Animations

- [x] **ANIM-01**: User sees the hawk score count up from 0 to the live value on page load using CountUp.js 2.9.0 (with `prefers-reduced-motion` guard for accessibility)
- [x] **ANIM-02**: User sees the Plotly hawk gauge sweep from 0 to the live score on page load via `requestAnimationFrame` workaround (with `prefers-reduced-motion` guard)

## Future Requirements

Tracked but not in v4.0 roadmap.

### Indicator Deltas

- **DELT-01**: User sees a direction delta badge on each indicator card showing change from previous period
  *(Requires `previous_value` field in status.json — backend pipeline change needed)*

### Historical Trend

- **HIST-01**: User can view a historical chart of the hawk score over time
  *(Requires archiving status.json snapshots — no current mechanism)*

## Out of Scope

| Feature | Reason |
|---------|--------|
| Dark/light theme toggle | Requires dual Tailwind class definitions and Plotly style rewrites across all modules — high complexity, low value against finance-terminal aesthetic |
| Tailwind v4 CDN upgrade | Incompatible config format (breaks existing JS `tailwind.config` object); no feature benefit for this milestone |
| Plotly.js v3 upgrade | Breaking changes to `title` API; would require auditing all `getDarkLayout()` calls with no feature benefit |
| Inline tooltips / help icons | Not in scope — hero + verdict explanation addresses the "what is this?" gap more directly |
| Real-time polling | ABS/RBA data is monthly/quarterly; polling is theatre |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| HERO-01 | Phase 21 | Done |
| HERO-02 | Phase 21 | Done |
| HERO-03 | Phase 21 | Done |
| HERO-04 | Phase 21 | Done |
| HERO-05 | Phase 21 | Done |
| HERO-06 | Phase 21 | Done |
| EXPL-01 | Phase 22 | Done |
| EXPL-02 | Phase 22 | Done |
| EXPL-03 | Phase 22 | Done |
| EXPL-04 | Phase 22 | Done |
| POLX-01 | Phase 23 | Done |
| POLX-02 | Phase 23 | Done |
| POLX-03 | Phase 23 | Done |
| POLX-04 | Phase 23 | Done |
| ANIM-01 | Phase 23 | Done |
| ANIM-02 | Phase 23 | Done |

**Coverage:**
- v4.0 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-26*
*Last updated: 2026-02-26 after v4.0 roadmap creation*
