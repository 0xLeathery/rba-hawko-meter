---
phase: 06-ux-plain-english
plan: 03
subsystem: ui
tags: [ux, information-architecture, accessibility, mobile-responsive, html5-details]

# Dependency graph
requires:
  - phase: 04-gauges-visualization
    provides: GaugesModule with gauge rendering, getStanceLabel(), getDisplayLabel()
  - phase: 05-calculator-compliance
    provides: Calculator section and ASIC RG 244 compliant language patterns
provides:
  - SEO-optimized meta tags with plain English titles and descriptions
  - Graceful missing-data handling (greyed-out placeholder cards, hidden empty panels)
  - Information architecture linking hawk score to mortgage calculator impact
  - Mobile-friendly UX with collapsible chart and optimized layout
  - "What to do next" guidance section with actionable next steps
affects: [future-content-updates, seo-strategy, mobile-ux-patterns]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HTML5 details/summary for collapsible sections without JavaScript"
    - "Placeholder card rendering for missing data indicators"
    - "Dynamic calculator bridge text linking analytical data to personal impact"
    - "display:none for completely hiding unavailable data panels"

key-files:
  created: []
  modified:
    - public/index.html
    - public/js/gauge-init.js
    - public/js/interpretations.js

key-decisions:
  - "Hide ASX panel completely when data unavailable (no residual heading or unavailable message)"
  - "Exclude asx_futures from placeholder cards since it's a benchmark, not an indicator"
  - "Use HTML5 details/summary for collapsible chart instead of custom JavaScript"
  - "Calculator bridge uses neutral ASIC-compliant language: 'could mean' not 'will mean'"

patterns-established:
  - "Placeholder cards pattern: greyed-out with name, weight, and 'Data coming soon' for missing indicators"
  - "Calculator bridge pattern: dynamic contextual text connecting hawk score to mortgage impact"
  - "Jump-to-section pattern: anchor link in hero smooth-scrolls to related content"
  - "What to do next pattern: 3-card grid with actionable next steps before footer"

# Metrics
duration: 3min
completed: 2026-02-06
---

# Phase 6 Plan 3: Information Architecture & Mobile UX Summary

**Plain English meta tags, graceful missing-data UX, calculator bridging text, and mobile-optimized collapsible chart with actionable CTA section**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T08:42:57Z
- **Completed:** 2026-02-06T08:46:12Z
- **Tasks:** 4
- **Files modified:** 3

## Accomplishments
- SEO-optimized meta tags answer user intent: "Are Australian interest rates going up or down?"
- Missing indicators show honest placeholder cards with weights instead of empty space
- Calculator bridge connects hawk score to personal mortgage impact with dynamic contextual text
- Empty ASX panel completely hidden when data unavailable (no visual clutter)
- Mobile UX improved with native collapsible chart and responsive layout
- "What to Do Next" section provides actionable guidance before footer

## Task Commits

Each task was committed atomically:

1. **Task 1: Meta tags, jump-to-calculator link, and ASX heading retitle** - `5094622` (feat)
2. **Task 2: Placeholder cards for missing indicators** - `b092e57` (feat)
3. **Task 3: Calculator bridge text, jump link, and what-to-do-next section** - `24ce219` (feat)
4. **Task 4: Mobile UX improvements — collapsible chart** - `0fdb88f` (feat)

## Files Created/Modified
- `public/index.html` - Updated meta tags, added calculator jump link placeholder, ASX heading retitle, What to Do Next section, collapsible chart with details/summary
- `public/js/gauge-init.js` - Added renderMissingIndicatorCards() function, renderCalculatorBridge() function, populated jump link in hero
- `public/js/interpretations.js` - Updated renderASXTable() to hide container when data null, retitled heading to "What Markets Expect" with subline

## Decisions Made

**1. Hide ASX panel completely when unavailable**
- Rationale: Empty "unavailable" messages create visual clutter and don't provide value. Complete hiding is cleaner UX than showing disabled panels.

**2. Exclude asx_futures from placeholder cards**
- Rationale: ASX futures is a benchmark indicator (excluded from hawk score via exclude_benchmark), not a core indicator. Showing it as "missing" would be misleading.

**3. Use HTML5 details/summary for collapsible chart**
- Rationale: Native browser element provides accessibility, keyboard navigation, and no-JS fallback. Simpler than custom JavaScript accordion.

**4. Calculator bridge uses neutral language**
- Rationale: ASIC RG 244 compliance requires avoiding advice language. "Could mean" is illustrative, "will mean" implies prediction.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed smoothly with no blocking issues.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Information architecture complete.** The dashboard now:
- Clearly communicates purpose via SEO-optimized meta tags
- Handles missing data gracefully with honest placeholders
- Connects analytical hawk score to personal mortgage impact
- Provides actionable guidance on what to do with the information
- Optimized for mobile with collapsible chart and responsive layout

**Remaining UX work:** Future phases could add:
- Onboarding tutorial or first-visit walkthrough
- Share/bookmark features
- Print-friendly version
- Accessibility audit for screen readers

---
*Phase: 06-ux-plain-english*
*Completed: 2026-02-06*

## Self-Check: PASSED

All key files verified:
- public/index.html (modified)
- public/js/gauge-init.js (modified)
- public/js/interpretations.js (modified)

All commits verified:
- 5094622 (Task 1)
- b092e57 (Task 2)
- 24ce219 (Task 3)
- 0fdb88f (Task 4)
