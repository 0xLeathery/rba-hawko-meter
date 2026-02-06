# Phase 6: UX & Plain English Overhaul

## Phase Goal
Transform the dashboard from economist-speak to everyday Australian English so that a homeowner, renter, or small business owner can understand "are interest rates going up or down?" within 5 seconds of landing on the page.

## Origin
Three parallel UX audit agents reviewed https://rbahawk.xyz/ on 2026-02-06 focusing on:
1. **Data Clarity & Layman Comprehension** - jargon, missing explanations, data presentation
2. **Information Architecture & User Journey** - page structure, flow, empty states, mobile
3. **Plain English Copywriting** - specific rewrites with code-level suggestions

## Key Findings Summary

### P0 - Critical (Trust & Comprehension Breakers)
1. **Building Approvals shows "-99.9% YoY"** - data quality artifact displayed to users, destroys credibility
2. **No explanation of 0-100 score** - hero gauge shows "46" with no units, scale, or context
3. **"Hawkish"/"Dovish" never explained** - central banking jargon is the core labeling system
4. **No onboarding** - zero "What is this?" context between header and gauge

### P1 - High Priority (Usability & Trust)
5. **5 of 8 indicators missing with no warning** - only 45% of model weight is represented
6. **Verdict text is academic** - "broadly balanced" means nothing to mortgage holders
7. **Jargon throughout** - YoY, CPI, target band, weight %, ASX Futures, implied rate, stale
8. **No score trend/direction** - 46 without knowing if it's rising or falling is useless

### P2 - Medium Priority (Experience & Polish)
9. **Calculator buried at bottom** - most personally relevant tool requires ~2800px scroll
10. **Calculator disconnected from hawk score** - no narrative bridge between analysis and impact
11. **ISO date format** - "2025-12-01" instead of "1 December 2025"
12. **Mobile experience** - ~3500px scroll depth, empty ASX panel wastes space
13. **No "why it matters" per indicator** - data without personal relevance

### P3 - Low Priority (Polish)
14. Cash rate visual competes with hawk score
15. No call to action after calculator
16. "Capacity" label for business_confidence is unclear
17. Meta title/description written for SEO, not humans

## Files Requiring Changes

| File | Scope |
|------|-------|
| `public/js/gauges.js` | Zone labels (dovish→plain English), add `/100` suffix, rename "Capacity" |
| `public/js/interpretations.js` | Rewrite interpretation templates, expand "YoY", format dates, weight badges, data quality guard, "(stale)" text, verdict rewrite, per-indicator "why it matters" lines |
| `public/index.html` | Onboarding section, score explainer, section reordering consideration, mobile improvements, meta tags, missing-indicator notice, ASX retitle |
| `public/js/gauge-init.js` | Render placeholder cards for missing indicators, data coverage notice |
| `public/js/calculator.js` | Bridge to hawk score context (optional P2) |

## Constraints
- ASIC RG 244 compliance must be maintained - no language that constitutes financial advice
- No build toolchain - vanilla JS, CDN libraries only
- All DOM manipulation uses safe methods (no innerHTML)
- Conventional commits: `type(06-plan): description`

## Proposed Plan Structure
- **Plan 06-01**: Plain English Labels & Onboarding (P0 items)
- **Plan 06-02**: Interpretation Rewrites & Data Quality Guards (P0/P1 items)
- **Plan 06-03**: Information Architecture & UX Polish (P1/P2 items)
