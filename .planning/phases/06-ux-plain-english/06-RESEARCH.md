# Phase 6 Research: Current Codebase State for UX Overhaul

## Zone Label System (Current State)

### gauges.js (ZONE_COLORS, lines 9-15)
Five-zone system used for both color and labels:
```js
{ range: [0, 20], color: '#1e40af', label: 'STRONGLY DOVISH' }
{ range: [20, 40], color: '#60a5fa', label: 'DOVISH' }
{ range: [40, 60], color: '#6b7280', label: 'NEUTRAL' }
{ range: [60, 80], color: '#f87171', label: 'HAWKISH' }
{ range: [80, 100], color: '#dc2626', label: 'STRONGLY HAWKISH' }
```

`getStanceLabel(value)` at line 47 iterates ZONE_COLORS to return the label for a given score.
`getZoneColor(value)` at line 32 returns the hex color.

Both functions are used by:
- `createHeroGauge()` line 116 (title.text = getStanceLabel)
- `updateHeroGauge()` line 161 (title.text = getStanceLabel)
- `renderVerdict()` in interpretations.js line 44 (via GaugesModule.getZoneColor)

### interpretations.js (ZONE_LABEL_MAP, lines 8-14)
Maps backend zone_label strings to display labels:
```js
'Strong dovish pressure': 'STRONGLY DOVISH'
'Mild dovish pressure': 'DOVISH'
'Balanced': 'NEUTRAL'
'Mild hawkish pressure': 'HAWKISH'
'Strong hawkish pressure': 'STRONGLY HAWKISH'
```

Used in `renderVerdict()` line 40: maps overallData.zone_label to stance display string.

## Number Suffix (Current State)

### Hero gauge (gauges.js line 119-122)
```js
number: {
    font: { size: 52, color: '#f3f4f6' },
    valueformat: '.0f'
    // No suffix property
}
```
Displays as bare "46" with no units.

### Bullet gauges (gauges.js line 207-211)
```js
number: {
    font: { size: 24, color: '#f3f4f6' },
    valueformat: '.0f',
    suffix: ''  // Explicitly empty
}
```
Also displays bare numbers with no units.

### updateHeroGauge (gauges.js line 164-167)
Same pattern, no suffix. Must be updated in sync.

## HTML Structure (Current State)

### index.html layout order (relevant sections):
1. **Line 49-59**: Disclaimer banner (ASIC RG 244)
2. **Line 62-67**: Header (`<header>` with h1 "RBA Hawk-O-Meter" + tagline)
3. **Line 70**: `<main>` opens
4. **Line 73-102**: Hero section (gauge + ASX + cash rate + verdict)
   - Line 99-101: `<div id="verdict-container">`
5. **Line 104-107**: Countdown section
6. **Line 109-118**: Chart section
7. **Line 121-128**: Individual gauges section
8. **Line 131-265**: Calculator section

### Insertion points identified:
- **Onboarding**: Between header close (line 67) and main open (line 70), or as first child of `<main>` before hero section (line 73)
- **Scale explainer**: After verdict-container (line 101), before section close (line 102)

## DOM Safety Patterns

The project uses safe DOM methods exclusively:
- `document.createElement()` + `textContent` for all dynamic content
- No `innerHTML` anywhere in JS modules
- All existing modules follow IIFE pattern with `'use strict'`

## Tailwind Classes Used for Cards/Sections

Common patterns in existing code:
- Section containers: `bg-finance-gray border border-finance-border rounded-xl px-6 py-5`
- Cards: `bg-finance-gray rounded-lg p-4 border border-finance-border`
- Text hierarchy: `text-gray-200` (headings), `text-gray-400` (body), `text-gray-500` (muted)
- Badges: `text-xs text-amber-400`

## Collapsible Pattern

No existing collapsible/accordion pattern in the codebase. Will need to implement with:
- A `<details>/<summary>` HTML5 element (simplest, no JS needed, progressive enhancement)
- OR a button + toggled div with vanilla JS

`<details>/<summary>` is preferred for simplicity and accessibility.

## ASIC RG 244 Compliance Notes

From Phase 5 audit (05-02):
- All language must be neutral framing
- "General information only" must be maintained
- No language that constitutes financial advice
- Onboarding text must describe what the tool does, not what users should do
