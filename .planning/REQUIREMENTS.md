# Requirements: RBA Hawk-O-Meter

**Defined:** 2026-02-26
**Core Value:** "Data, not opinion." — Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

## v4.0 Requirements

Requirements for v4.0 Dashboard Visual Overhaul milestone. Each maps to roadmap phases starting at Phase 21.

### Hero Section

- [ ] **HERO-01**: User sees the verdict label ("RATES LIKELY FALLING") as the dominant above-the-fold element — large, zone-coloured, immediately legible without scrolling
- [ ] **HERO-02**: User sees the hawk score as a prominent number (e.g. "38/100") in the hero card alongside the verdict
- [ ] **HERO-03**: User sees the scale explainer ("0 = Strongly Dovish → 100 = Strongly Hawkish") adjacent to the verdict in the hero card, not below the fold
- [ ] **HERO-04**: User sees a data freshness badge inside the hero card showing when the data was last updated
- [ ] **HERO-05**: User sees a zone-coloured accent border on the hero card that reflects the current hawk/dove/neutral zone
- [ ] **HERO-06**: User sees the hero card animate in with a fadeSlideIn entry effect when page data loads

### Verdict Explanation

- [ ] **EXPL-01**: User sees a plain-English list of the top hawkish indicators driving the score up (top 3 by contribution)
- [ ] **EXPL-02**: User sees a plain-English list of the top dovish indicators driving the score down (top 2 by contribution)
- [ ] **EXPL-03**: Neutral indicators (near 50, low contribution) are omitted from the explanation section to avoid clutter
- [ ] **EXPL-04**: All explanation copy uses ASIC-compliant hedged language ("tends to", "historically associated with", "the data is consistent with") — no predictions or recommendations

### Visual Polish

- [ ] **POLX-01**: User perceives a consistent typography hierarchy across the dashboard: large verdict/score in hero, clear secondary labels, readable body text, subtle metadata
- [ ] **POLX-02**: Zone colour (blue/grey/red) is applied consistently and only to: verdict label, hero card border, and explanation section headings — no other elements
- [ ] **POLX-03**: User perceives consistent spacing and padding across all dashboard sections (no tight or misaligned elements)
- [ ] **POLX-04**: User on a 375px-wide phone sees the hero verdict and score above the fold with no layout congestion

### Animations

- [ ] **ANIM-01**: User sees the hawk score count up from 0 to the live value on page load using CountUp.js 2.9.0 (with `prefers-reduced-motion` guard for accessibility)
- [ ] **ANIM-02**: User sees the Plotly hawk gauge sweep from 0 to the live score on page load via `requestAnimationFrame` workaround (with `prefers-reduced-motion` guard)

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
| HERO-01 | — | Pending |
| HERO-02 | — | Pending |
| HERO-03 | — | Pending |
| HERO-04 | — | Pending |
| HERO-05 | — | Pending |
| HERO-06 | — | Pending |
| EXPL-01 | — | Pending |
| EXPL-02 | — | Pending |
| EXPL-03 | — | Pending |
| EXPL-04 | — | Pending |
| POLX-01 | — | Pending |
| POLX-02 | — | Pending |
| POLX-03 | — | Pending |
| POLX-04 | — | Pending |
| ANIM-01 | — | Pending |
| ANIM-02 | — | Pending |

**Coverage:**
- v4.0 requirements: 16 total
- Mapped to phases: 0
- Unmapped: 16 ⚠️

---
*Requirements defined: 2026-02-26*
*Last updated: 2026-02-26 after initial definition*
