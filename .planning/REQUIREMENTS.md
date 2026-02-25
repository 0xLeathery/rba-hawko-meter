# Requirements: RBA Hawk-O-Meter

**Defined:** 2026-02-26
**Core Value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

## v5.0 Requirements

Requirements for v5.0 Direction & Momentum. Each maps to roadmap phases.

### Snapshot & Temporal

- [ ] **SNAP-01**: Pipeline archives current status.json as snapshot before each weekly run
- [ ] **SNAP-02**: Pipeline injects `previous_value` and `delta` fields into each gauge entry in status.json
- [ ] **SNAP-03**: Pipeline injects `previous_hawk_score` and `hawk_score_delta` into overall block in status.json
- [ ] **SNAP-04**: Snapshot storage enforces rolling retention cap (max 52 entries)
- [ ] **SNAP-05**: Archive module has unit tests at 85%+ coverage matching existing enforcement

### Delta Badges

- [ ] **DELT-01**: Each indicator card displays direction badge (▲/▼/—) with magnitude when |delta| >= 5 gauge points
- [ ] **DELT-02**: Hero section displays hawk score delta since previous pipeline run
- [ ] **DELT-03**: Delta badges use zone colours via element.style hex values (not Tailwind class concatenation)
- [ ] **DELT-04**: Indicators with no previous value display gracefully with no badge shown

### Sparklines

- [ ] **SPRK-01**: Each indicator card displays Canvas 2D sparkline from existing history[] array in status.json
- [ ] **SPRK-02**: Sparklines use zone colour for stroke via getZoneColor()
- [ ] **SPRK-03**: Indicators with fewer than 3 history points show "Building history..." placeholder
- [ ] **SPRK-04**: Sparklines render at max 40px height, full card width, with no axes or labels

### Social Sharing

- [ ] **SHARE-01**: index.html contains Open Graph meta tags (og:title, og:description, og:image, og:url, og:type)
- [ ] **SHARE-02**: index.html contains Twitter Card meta tags (twitter:card, twitter:title, twitter:description, twitter:image)
- [ ] **SHARE-03**: Static 1200x630 branded OG image committed to public/og-image.png
- [ ] **SHARE-04**: Share button in hero section uses Web Share API with clipboard fallback and toast notification

### Historical & Narrative

- [ ] **HIST-01**: Dashboard displays historical hawk score line chart from archived snapshots
- [ ] **HIST-02**: Historical chart shows zone background colour bands (cold/cool/neutral/warm/hot)
- [ ] **HIST-03**: Chart displays "Building history — check back next week" placeholder when fewer than 4 data points exist
- [ ] **NARR-01**: Pipeline generates change_summary array in status.json with factual template-based narrative sentences
- [ ] **NARR-02**: Dashboard displays "What changed this week" section rendered from change_summary array

### Newsletter

- [ ] **NEWS-01**: Dashboard displays email signup form using Netlify Forms (data-netlify attribute)
- [ ] **NEWS-02**: Signup form uses unchecked consent checkbox by default (Australian Spam Act 2003 compliance)
- [ ] **NEWS-03**: MailerLite account configured with double opt-in for email delivery
- [ ] **NEWS-04**: Weekly digest email auto-assembled from status.json data (hawk score, zone, top movers, change narrative)

## Future Requirements

Deferred to v5.x+ or later. Tracked but not in current roadmap.

### Monetization

- **AFFIL-01**: Single disclosed "find a broker" affiliate CTA with ASIC RG 244 compliant framing
- **AFFIL-02**: Newsletter affiliate CTA in email footer with referral fee disclosure

### Visual Enhancements

- **DYNIMG-01**: Dynamic OG image generation showing current hawk score (requires Pillow pipeline integration)
- **MOMENT-01**: Momentum Z-score (second derivative) showing acceleration/deceleration per indicator

### Distribution

- **SOCIAL-01**: Twitter/X bot auto-posting weekly score ($100/mo API cost — defer until revenue)
- **PWA-01**: Progressive Web App manifest + service worker for "Add to Home Screen"

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| LLM-generated narrative summary | Template-based Python covers 95% of value; LLM adds cost, latency, hallucination risk on numerical data, ASIC concerns |
| "Best mortgage rate" comparison table | Requires AFS license; violates "Data, not opinion" core value |
| Real-time sparklines / live price feeds | Weekly cadence is actual data refresh; quarterly indicators show no change "live" |
| Push notifications | Requires service worker backend; Netlify static hosting incompatible |
| Paid newsletter (subscription model) | Reduces reach; affiliate referrals generate more revenue per user at small scale |
| User accounts / saved preferences | Stateless app constraint; Privacy Act liability; localStorage already persists calculator |
| Delta badges using history[-2] as proxy | Quarterly steps do not represent weekly change; misleads users about recency |
| Affiliate links without ASIC legal review | Performance-based links may constitute "arranging" under Corporations Act 2001 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SNAP-01 | — | Pending |
| SNAP-02 | — | Pending |
| SNAP-03 | — | Pending |
| SNAP-04 | — | Pending |
| SNAP-05 | — | Pending |
| DELT-01 | — | Pending |
| DELT-02 | — | Pending |
| DELT-03 | — | Pending |
| DELT-04 | — | Pending |
| SPRK-01 | — | Pending |
| SPRK-02 | — | Pending |
| SPRK-03 | — | Pending |
| SPRK-04 | — | Pending |
| SHARE-01 | — | Pending |
| SHARE-02 | — | Pending |
| SHARE-03 | — | Pending |
| SHARE-04 | — | Pending |
| HIST-01 | — | Pending |
| HIST-02 | — | Pending |
| HIST-03 | — | Pending |
| NARR-01 | — | Pending |
| NARR-02 | — | Pending |
| NEWS-01 | — | Pending |
| NEWS-02 | — | Pending |
| NEWS-03 | — | Pending |
| NEWS-04 | — | Pending |

**Coverage:**
- v5.0 requirements: 26 total
- Mapped to phases: 0
- Unmapped: 26

---
*Requirements defined: 2026-02-26*
*Last updated: 2026-02-26 after initial definition*
