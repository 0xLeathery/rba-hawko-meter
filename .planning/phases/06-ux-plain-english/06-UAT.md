---
status: testing
phase: 06-ux-plain-english
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md]
started: 2026-02-06T09:00:00Z
updated: 2026-02-06T09:00:00Z
---

## Current Test

number: 1
name: Plain English zone labels on hero gauge
expected: |
  Visit https://rbahawk.xyz/ (or open public/index.html locally).
  The hero gauge label should say "HOLDING STEADY" (not "NEUTRAL").
  No trace of "DOVISH" or "HAWKISH" anywhere on the page.
awaiting: user response

## Tests

### 1. Plain English zone labels on hero gauge
expected: Hero gauge shows "HOLDING STEADY" label (not "NEUTRAL"). No "DOVISH" or "HAWKISH" text visible anywhere on the page.
result: [pending]

### 2. Score displays /100 suffix
expected: Hero gauge shows "46/100" (not bare "46"). Each bullet gauge in the Economic Indicators section also shows "/100" suffix (e.g., "47/100", "46/100").
result: [pending]

### 3. Onboarding explainer visible
expected: Between the header and the hero gauge, there is a collapsible section titled "What is the Hawk-O-Meter?" that is expanded by default. It explains the 0-100 score meaning and includes "This is not a prediction or financial advice." Clicking the title collapses/expands it.
result: [pending]

### 4. Scale explainer beneath verdict
expected: Below the verdict text (e.g., "HOLDING STEADY — The economy is giving mixed signals..."), there is a muted gray line: "Score out of 100. Below 50 = pressure to cut rates. Above 50 = pressure to raise rates."
result: [pending]

### 5. Plain English verdict text
expected: The verdict text says something like "The economy is giving mixed signals. Interest rates are likely to stay where they are for now." — NOT "Economic indicators are broadly balanced."
result: [pending]

### 6. Metric card interpretations in plain English
expected: The Inflation card says something like "Prices up 1.4% over the past year — within the RBA's 2-3% target" (not "CPI at 1.4% YoY"). Each card has an italic "why it matters" line below the interpretation.
result: [pending]

### 7. Building approvals data quality guard
expected: The Building Approvals card does NOT show "-99.9% YoY". It either shows "Building approvals data is currently being updated" or a qualitative description like "New building approvals are below average."
result: [pending]

### 8. Weight badges and stale data labels
expected: Each metric card shows an importance label (e.g., "High importance" for Inflation, "Lower importance" for Building Approvals) instead of "25% weight". The Wages card shows something like "(7 months old — newer data not yet available)" in amber text instead of just "(stale)". Hovering over the importance label shows a tooltip with the actual percentage.
result: [pending]

### 9. Australian date format and coverage notice
expected: Source citations on metric cards show Australian date format (e.g., "Data as of 1 Jul 2025" not "2025-07-01"). Above the metric cards grid, a notice reads "Based on 3 of 8 indicators (more data coming soon)".
result: [pending]

### 10. Placeholder cards for missing indicators
expected: After the 3 active metric cards (Inflation, Wages, Building Approvals), there are 4 greyed-out placeholder cards for Jobs, Spending, Housing, and Capacity. Each shows the indicator name, its weight percentage, and "Data coming soon" in italic. No ASX Futures placeholder card.
result: [pending]

### 11. Calculator bridge and jump link
expected: In the hero section after the verdict, there is a small blue link "See what this means for your mortgage ↓". Clicking it scrolls to the calculator. Above the calculator form, a contextual paragraph reads something like "The Hawk-O-Meter reads 46/100 (holding steady). Here's what current and potential rate changes could mean for a typical mortgage."
result: [pending]

### 12. Mobile collapsible chart and "What to Do Next"
expected: On a narrow screen (or browser resized to ~375px), the "Cash Rate History" chart section is collapsible — shows a toggle to show/hide the chart. Before the footer, there is a "What to Do Next" section with 3 cards: "Bookmark this page", "Check back after the next RBA meeting", and "Speak to a licensed financial adviser".
result: [pending]

## Summary

total: 12
passed: 0
issues: 0
pending: 12
skipped: 0

## Gaps

[none yet]
