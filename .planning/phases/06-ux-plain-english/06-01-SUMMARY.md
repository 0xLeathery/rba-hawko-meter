---
phase: 06-ux-plain-english
plan: 01
subsystem: ui
tags: [tailwind, plotly, ux, plain-english, accessibility]

# Dependency graph
requires:
  - phase: 04-gauges
    provides: Gauge rendering system with ZONE_COLORS and ZONE_LABEL_MAP
  - phase: 05-calculator-compliance
    provides: ASIC RG 244 compliant disclaimers
provides:
  - Plain English zone labels: RATES LIKELY FALLING/RISING instead of DOVISH/HAWKISH
  - /100 suffix on all gauge numbers for clarity
  - Onboarding explainer section for first-time visitors
  - Scale context text beneath verdict
affects: [07-historical-trends, future-ux-enhancements]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Native HTML5 details/summary for collapsible onboarding (no JS, accessible)
    - Plain English labels synced across ZONE_COLORS and ZONE_LABEL_MAP

key-files:
  created: []
  modified:
    - public/js/gauges.js
    - public/js/interpretations.js
    - public/index.html

key-decisions:
  - "Plain English zone labels: RATES LIKELY FALLING through RATES LIKELY RISING"
  - "Native details/summary element for onboarding (no JS, accessible by default)"
  - "/100 suffix on all gauge numbers for immediate comprehension"

patterns-established:
  - "ZONE_COLORS labels must exactly match ZONE_LABEL_MAP values for consistency"
  - "Muted text-gray-500 styling for contextual explainers to avoid visual competition"

# Metrics
duration: 2min
completed: 2026-02-06
---

# Phase 6 Plan 01: Plain English UX Summary

**Economist jargon replaced with plain English labels, /100 suffixes added to all gauges, onboarding explainer and scale context added - dashboard now accessible to mortgage holders in 5 seconds**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-06T08:41:19Z
- **Completed:** 2026-02-06T08:43:19Z
- **Tasks:** 4
- **Files modified:** 3

## Accomplishments
- Removed all economist jargon (DOVISH/HAWKISH) and replaced with plain English labels
- All gauge numbers now display /100 suffix for immediate clarity
- Added collapsible onboarding explainer between header and hero gauge
- Added scale context text beneath verdict line

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace zone labels with plain English** - `f44565f` (feat)
2. **Task 2: Add /100 suffix to hero and bullet gauge numbers** - `f1662fd` (feat)
3. **Task 3: Add onboarding explainer section** - `ad4b202` (feat)
4. **Task 4: Add scale explainer beneath verdict** - `38a5915` (feat)

## Files Created/Modified
- `public/js/gauges.js` - Updated ZONE_COLORS labels to plain English, added /100 suffix to hero and bullet gauge number configs
- `public/js/interpretations.js` - Updated ZONE_LABEL_MAP values to match ZONE_COLORS labels
- `public/index.html` - Added onboarding section with details/summary, added scale explainer text beneath verdict

## Decisions Made

**Plain English zone labels:**
- STRONGLY DOVISH → RATES LIKELY FALLING
- DOVISH → LEANING TOWARDS CUTS
- NEUTRAL → HOLDING STEADY
- HAWKISH → LEANING TOWARDS RISES
- STRONGLY HAWKISH → RATES LIKELY RISING

Rationale: Removes economist jargon, makes meaning immediately clear to laypeople.

**Native HTML5 details/summary for onboarding:**
Used semantic HTML instead of custom JS accordion. Benefits:
- Zero JavaScript overhead
- Accessible by default (keyboard navigation, screen readers)
- Browser-native behavior (no custom event handling)

**/100 suffix on all gauges:**
Added to createHeroGauge, updateHeroGauge, and createBulletGauge. Makes "46/100" vs "46" clear the score is relative, not absolute.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all changes were straightforward label/text replacements and HTML additions.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Dashboard now ready for first-time visitors:
- Plain English throughout (no jargon)
- Score meaning clear (0-100 scale with /100 suffixes)
- Onboarding explains what the dashboard does
- Scale context beneath verdict reinforces meaning

Ready for Phase 06 Plan 02: Time context & visual hierarchy improvements.

**No blockers.** ASIC RG 244 compliance maintained (onboarding disclaimer: "not a prediction or financial advice").

## Self-Check: PASSED

All files modified as documented:
- public/js/gauges.js ✓
- public/js/interpretations.js ✓
- public/index.html ✓

All commits exist in git history:
- f44565f ✓
- f1662fd ✓
- ad4b202 ✓
- 38a5915 ✓

---
*Phase: 06-ux-plain-english*
*Completed: 2026-02-06*
