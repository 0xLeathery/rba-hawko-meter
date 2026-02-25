# Feature Research

**Domain:** Australian economic/financial dashboard — v5.0 Direction & Momentum (subsequent milestone)
**Researched:** 2026-02-26
**Confidence:** HIGH (pipeline architecture/ASIC compliance), MEDIUM (competitor landscape — direct inspection limited by CSS-heavy pages)

---

## Context: Subsequent Milestone

This is v5.0 research on a live v4.0 product. Research covers ONLY new features being added. Existing shipped features are documented in PROJECT.md.

**Key structural facts affecting new features (verified directly from codebase):**

| Fact | Value | Impact |
|------|-------|--------|
| `history[]` exists in status.json | 12 quarterly data points per gauge (6/7 indicators); `business_confidence` = 1 point only | Sparklines can ship without pipeline changes |
| `previous_value` does NOT exist | Not in current status.json schema | Delta badges require pipeline change |
| `previous_hawk_score` does NOT exist | Not in overall block | Hero delta requires pipeline change |
| No build system | CDN-only (Tailwind CDN v3, Plotly 2.35.2, CountUp.js 2.9.0) | Library choices constrained to CDN-loadable, zero-dep packages |
| Tailwind CDN silently drops dynamic class strings | Confirmed architectural constraint | Colours must be set via `element.style` with hex, not Tailwind classes |
| JS is IIFE module pattern | No ES modules, no bundler | New JS must follow same IIFE pattern |
| Static hosting (Netlify) | No server-side rendering, no serverless functions in scope | OG image must be static; no dynamic meta generation |

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist on modern financial dashboards. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Delta badges showing direction of change | Every major financial dashboard (Bloomberg, FactSet, Finder) shows arrows/deltas. Users scan for "up/down" not just absolute numbers. Table stakes for any data dashboard updated on a cadence. | MEDIUM | Requires `previous_value` in status.json (pipeline change). Badge: ▲/▼/— arrow + magnitude in gauge units. Cannot use `history[-2]` as proxy without misleading users — quarterly steps don't reflect weekly change. |
| OG meta tags for social sharing | Any link shared on Slack, iMessage, Twitter/X, LinkedIn without OG renders as a bare URL. For a tool users want to share with friends/family before rate decisions, this is effectively broken sharing. Finance sites report 78% traffic lift from proper OG implementation. | LOW | `og:title`, `og:description`, `og:image`, `og:url`, `og:type` + Twitter Card tags. Static tags in `<head>` of `public/index.html`. Static 1200x630 branded PNG in `public/`. No dynamic generation needed. |
| Share button | "Share this page" is expected on any information tool. Without it, sharing happens anyway but with worse URLs. The expectation is one button, native OS share sheet on mobile. | LOW | Web Share API: `navigator.share({title, text, url})` with feature detection. Desktop fallback: clipboard copy + toast. Zero third-party scripts. No social SDK needed. Well-supported on iOS/Android Safari/Chrome (2026). |
| Sparklines showing trend history | Industry-standard component in financial data UIs since Bloomberg Terminal. FactSet specifically uses sparklines to show "whether metrics are trending up, down, or stable within a single KPI card." Users expect trend signal alongside point-in-time value. | MEDIUM | `history[]` already exists (12 quarterly points). Library: `@fnando/sparkline` (CDN-loadable, zero deps, SVG output, 362 npm dependents). Exception: `business_confidence` has 1 history point — show "Building history..." placeholder. Colour via `getZoneColor()` on SVG `stroke` attribute directly (not Tailwind). |

### Differentiators (Competitive Advantage)

Features that set Hawk-O-Meter apart from Finder, Canstar, Mozo, Craggle, and the ASX Rate Tracker. Must align with "Data, not opinion" core value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Historical hawk score chart | No competitor shows a composite "rate pressure trajectory." Finder/Canstar/Mozo show raw cash rate history only (backward-looking). This shows where the composite pressure score has been trending — "we've been moving dovish for 3 months" — which is genuinely more useful for anticipating the next move. | HIGH | Requires snapshot archiving pipeline step (weekly row to `data/hawk_score_history.csv`). Frontend: Plotly.js line chart (already a dep). Blocking: chart needs 4+ weeks of real data to look meaningful. Can ship with placeholder "Building history — check back next week." |
| "What changed this week" auto-narrative | Mozo/Finder do manual editorial articles per RBA decision. An auto-generated plain-English diff summary ("Wages fell from 6.4% to 5.45% YoY — easing slightly. Inflation steady.") pre-built into status.json by the pipeline adds immediate insight with zero manual effort — and is available every week, not just on RBA decision days. | MEDIUM | Python template-based generation in engine.py. Compare `previous_value` vs `current_value` per indicator, emit factual sentences. NO LLM needed. ASIC-compliant: "X moved from A to B" not "This means you should..." Output as `change_summary` array in status.json overall block. |
| Newsletter digest with weekly data snapshot | Canstar/Finder have broad financial newsletters for millions of subscribers. A niche weekly "Hawk-O-Meter Report" with zero product recommendations differentiates on neutrality and specificity. The digest IS the data update — auto-assembled, no editorial effort. | HIGH | Platform: Buttondown (free ≤100 subscribers, $29/mo for API). Pipeline sends email via Buttondown API post-weekly-run in GitHub Actions. Signup form on dashboard (simple fetch to Buttondown subscribe endpoint). ASIC constraint: factual/educational only, no recommendations, affiliate footer must be disclosed. |
| Mortgage broker affiliate CTA | Finder/Canstar earn revenue from sponsored product placement and referral fees. Hawk-O-Meter can offer a single neutral CTA: "Thinking about refinancing? Compare brokers →" without ranking or recommending specific products. Disclosed affiliate referrals: $200-$350 per settled loan (Mates Rates benchmark) or 0.33% commission (Unloan model). | MEDIUM | Single link, clearly disclosed. No product table, no ranking. Disclosure: "We may receive a referral fee if you contact a broker via this link." See ASIC compliance section. Revenue meaningful only at scale — treat as Phase 4 / future milestone. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| LLM-generated narrative summary | "AI summary" sounds sophisticated; marketing hook | Adds OpenAI API cost, latency, hallucination risk on numerical data, secret management in GitHub Actions. Potential ASIC concern about AI-generated financial statements. Overkill when template-based generation covers 95% of the value. | Template-based Python in engine.py using existing interpretation strings. Same readability, zero cost, deterministic, ASIC-safe. |
| "Best mortgage rate" comparison table | Obvious monetization; high conversion | Requires AFS license or credit licensee sponsorship under ASIC RG 234/RG 244. Rate tables go stale within hours. Crosses from macro education to lead gen — violates "Data, not opinion" core value. | Single neutral CTA: "Ready to act on this data? Find a broker →" with disclosed referral. |
| Real-time sparklines / live price feeds | Users want "live" data | Weekly cadence is the actual data refresh rate. Macro indicators (CPI, wages) update quarterly. "Live" sparklines would just show no change. Misrepresents data currency. | Label sparklines with data frequency ("quarterly readings"). Show `data_date` per indicator — already in status.json. |
| Dynamic OG image per hawk score | Share preview shows actual current score | Requires serverless function or pre-render pipeline to generate dynamic images. Violates zero-cost hosting constraint and no-build-system pattern. High complexity for marginal gain. | Static branded OG image: "RBA Hawk-O-Meter — Weekly Rate Pressure Score." Sufficient for 95% of sharing. Revisit in v6+ if serverless is added. |
| Push notifications for RBA decisions | Engagement hook; "alert me when score crosses 70" | Service workers + push subscriptions require a backend. Netlify static hosting cannot maintain push subscriptions server-side. | Newsletter IS the notification channel — subscribers receive weekly digest automatically. |
| Social media auto-posting (Twitter/X bot) | Organic distribution | Twitter/X API write access costs $100/month minimum (2026 pricing). No budget. Token management complexity in GitHub Actions. | Share button enables organic sharing by users. Newsletter digest is the owned distribution channel. |
| Paid newsletter (Substack/subscription model) | Monetization | Charging for factual public economic data is ethically questionable and reduces reach. Affiliate referrals generate more revenue per user than subscriptions at small subscriber scale. | Free newsletter with disclosed affiliate CTAs in footer. |
| User accounts / saved preferences | Personalization; "save my mortgage inputs" | Stateless app is a core project constraint. Adds auth infrastructure, Australian Privacy Act liability, session management. | `localStorage` already persists calculator inputs. No server-side user state needed. |
| Delta badges using `history[-2]` as proxy | Avoids pipeline change | Quarterly history steps do not reflect weekly change. Showing "-3.2 pts" based on a 3-month-old snapshot misleads users about recency. The badge implies "this week" — it must mean this week. | Ship sparklines (which correctly represent quarterly cadence) in Phase 1. Ship delta badges only after snapshot archiving provides weekly `previous_value`. |

---

## Feature Dependencies

```
[Snapshot Archiving — new pipeline step]
    └──required by──> [Delta Badges on indicator cards]
    └──required by──> [Previous Hawk Score delta on hero]
    └──required by──> [Historical Hawk Score Chart] (needs ≥4 weeks data)
    └──required by──> ["What Changed This Week" narrative]
    └──required by──> [Newsletter Digest content] (diff needs previous values)

[history[] arrays — already exist in status.json]
    └──enables──> [Sparklines on indicator cards] (no pipeline change)

[OG Meta Tags]
    └──required by──> [Share Button] (preview needs OG content to be useful)
    └──enhances──> [Newsletter Digest] (shared links preview correctly)

[Newsletter Signup Form]
    └──required by──> [Newsletter Digest delivery]
    └──requires──> [Buttondown account + API key in GitHub Actions secrets]

[Affiliate CTA]
    └──enhances──> [Newsletter Digest] (CTA in email footer)
    └──conflicts with──> [AFS License boundary] (must stay disclosed, factual, non-ranking)
    └──meaningful only after──> [Newsletter audience exists]

[Sparklines]
    └──enhances──> [Delta Badges] (together: trend line + point-in-time direction)
    └──independent of all other new features]
```

### Dependency Notes

- **Snapshot archiving is the core unblocking dependency.** Delta badges, historical chart, and narrative summary all require a `previous_value` and/or `hawk_score_history.csv`. This is the most critical pipeline addition in the milestone.
- **Sparklines can ship in Phase 1 independently.** `history[]` with 12 quarterly data points exists for 6 of 7 indicators. No pipeline change. `business_confidence` (1 data point) shows a placeholder.
- **OG tags must precede share button.** A share button without OG tags produces bare URL previews that actively deter sharing. They are one phase.
- **Newsletter requires patience.** Buttondown integration is meaningful once an audience exists. Launch alongside share button to capture organic traffic from day one.
- **Affiliate monetization is last.** Revenue is negligible at low subscriber count. Build audience first; monetize second.

---

## MVP Definition for v5.0

### Phase 1: Visual Momentum (No Pipeline Changes)

Makes the dashboard feel "alive" and shareable. No pipeline dependencies. Pure frontend changes.

- [ ] Sparklines from existing `history[]` arrays on each indicator card — shows quarterly trend in-place using existing data
- [ ] OG meta tags in `<head>` of `public/index.html` — enables proper social link previews immediately
- [ ] Share button with `navigator.share()` + clipboard fallback + toast — enables organic distribution

**Why start here:** Zero backend risk. High visual/shareability impact. Can ship and verify in isolation.

### Phase 2: Pipeline Temporal Layer

Adds the data infrastructure everything else depends on.

- [ ] Snapshot archiving: pipeline writes current gauge values + hawk score to `data/hawk_score_history.csv` each weekly run
- [ ] `previous_value` field added to each gauge in status.json (current vs prior weekly snapshot)
- [ ] `previous_hawk_score` field added to `overall` block in status.json
- [ ] Delta badge component on indicator cards (▲/▼/— + magnitude)
- [ ] Hawk score delta on hero section (e.g. "−3.2 since last week")

**Why second:** Pipeline changes need their own test coverage. Once archiving runs for one week, delta values populate immediately.

### Phase 3: Historical Chart + Narrative

- [ ] Historical hawk score chart (Plotly.js line chart reading `hawk_score_history.csv` or embedded in status.json)
- [ ] "What changed this week" auto-generated summary (template-based Python in engine.py, output as `change_summary[]` in status.json)
- [ ] Newsletter signup form embedded in dashboard footer/hero
- [ ] Buttondown integration: pipeline sends weekly digest email post-run via GitHub Actions

### Phase 4: Monetization Foundation (Future Consideration, v5.x+)

- [ ] Affiliate CTA section (single disclosed "find a broker" link, no product table or ranking)
- [ ] Newsletter affiliate CTA in email footer

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| OG meta tags | HIGH | LOW | P1 |
| Share button | HIGH | LOW | P1 |
| Sparklines on indicator cards | HIGH | MEDIUM | P1 |
| Delta badges on indicator cards | HIGH | MEDIUM (pipeline dep) | P1 |
| Historical hawk score chart | HIGH | HIGH (archive dep + wait time) | P2 |
| "What changed" narrative summary | MEDIUM | MEDIUM | P2 |
| Newsletter signup + weekly digest | MEDIUM | HIGH | P2 |
| Affiliate CTA | LOW | LOW (once audience exists) | P3 |

**Priority key:**
- P1: Must have for v5.0 launch — core milestone deliverables
- P2: Should have, add once Phase 2 pipeline layer is complete
- P3: Nice to have, defer until newsletter audience established

---

## Competitor Feature Analysis

Research method: Direct page inspection of Finder, Canstar (which absorbed RateCity via 301 redirect), Mozo, Craggle, ASX RBA Rate Tracker. Confidence: MEDIUM (CSS-heavy pages limit full feature visibility).

| Feature | Finder | Canstar/RateCity | Mozo | Craggle | ASX Rate Tracker | Our v5.0 Approach |
|---------|--------|------------------|------|---------|-----------------|-------------------|
| Composite hawk/dove score | Not present | Not present | Not present | Not present | Market probability % only | **Unique: multi-indicator composite 0-100** |
| Delta / change indicators | Cash rate only (basis points) | Not visible | Not visible | Table shows rate changes in basis points | Daily change in probability | Multi-indicator deltas per gauge card |
| Sparklines / micro-charts | Financial graph element confirmed (CSS) | Not visible | Not visible | Flourish chart (full-page, not inline) | Line chart (market-derived only) | In-card micro sparklines (12 quarterly points) |
| Social sharing | Share modal confirmed (Facebook, Twitter, WhatsApp, email) | Social icons footer only | Not visible | Not visible | Not visible | `navigator.share()` + clipboard (no SDK) |
| Newsletter signup | Email signup form confirmed | Present (Canstar brand) | Mozo Money Moves (weekly editorial) | Not visible | Not visible | Data-only digest, no editorial |
| OG meta tags | Confirmed (Optimizely tracking) | Present | Present | Not confirmed | Present | Static tags in `<head>` |
| Affiliate/monetization | Banner ads + sponsored product placement | Sponsored tables + star ratings | Sponsored product tables | Minimal visible | Not applicable | Single disclosed "find a broker" CTA |
| "What changed" narrative | Manual editorial per RBA decision | Manual editorial articles | Live blog on decision days | Manual article | Not applicable | **Auto-generated from status.json diff — no editorial** |
| Historical composite chart | Not present | Not present | Not present | 15-year raw rate chart | Short-term market curve | **Hawk score trajectory — unique: composite not raw rate** |
| Mortgage calculator | Present | Present | Present | Not visible | Not applicable | Already shipped v4.0 |

**Key insight:** No competitor offers (a) a composite pressure score from multiple economic indicators, (b) auto-generated factual narrative summaries, or (c) a weekly data-driven digest with zero editorial overhead. These three together are the genuine differentiating position.

---

## ASIC Compliance Constraints on Monetization Features

**Source:** ASIC INFO 269 (Discussing financial products online), RG 234 (Advertising), RG 244 (Advice obligations). Confidence: HIGH (direct ASIC source reading).

### Permitted Without an AFS License

- Display objective economic data and gauge values ("Wages grew 5.45% YoY — above the 10-year average")
- Auto-generate factual narrative summaries: "This week: Inflation moved from 4.1% to 3.76% YoY"
- Include a single "find a mortgage broker" link with clear adjacent disclosure
- Newsletter with factual weekly data updates — no recommendations about what subscribers should do
- Share button — sharing a URL is not financial advice

### Not Permitted Without an AFS License

- Recommend specific mortgage products or lenders (constitutes personal financial advice)
- State or imply that a user "should" refinance based on gauge readings
- Receive per-click affiliate payments without adequate disclosure — risks triggering "arranging" obligations
- Rank or score mortgage products by suitability for readers

### Affiliate Disclosure Pattern

Per RG 234 and INFO 269: adjacent disclosure is required near any commercial CTA. Industry pattern confirmed from Finder/Canstar inspection: "Sponsored" or "We may receive a referral fee" labels adjacent to commercial links. Apply this pattern to any affiliate CTA.

**Safe framing example:**
> "Thinking about your mortgage? [Find a broker →]"
> *Referral fee disclosure: We may receive a fee if you contact a broker through this link. This is not financial advice.*

---

## Implementation Notes by Feature

### Sparklines
- **Library:** `@fnando/sparkline` — CDN URL: `https://cdn.jsdelivr.net/npm/@fnando/sparkline@latest/dist/sparkline.js` — zero deps, SVG output, CDN-loadable without build system, actively maintained (546 GitHub stars, 362 npm dependents)
- **Data source:** `status.json gauges[indicator].history` — already 12 quarterly points for 6 of 7 indicators
- **Constraint:** `business_confidence.history` length = 1 — show "Building history..." placeholder text
- **Colour:** SVG `stroke` attribute set to `getZoneColor(gauge.value)` (existing function) — NOT Tailwind classes
- **Dimensions:** ~40px height, full card width, no axes, no labels — inline trend signal only
- **Usage pattern:** `sparkline(svgElement, historyArray, {stroke: zoneHex, strokeWidth: 1.5})`

### Delta Badges
- **Pipeline dependency:** Add `previous_value` to each gauge in engine.py by comparing current normalized value to last saved row in `hawk_score_history.csv`
- **Do NOT use `history[-2]` as proxy** — quarterly data points do not represent weekly change; misleads users
- **Badge visual:** ▲/▼/— icon + magnitude in gauge units (e.g. "+5.2 pts"), zone colour on icon
- **Edge cases:** `business_confidence` (1 history point) → show "—"; new indicators with no prior snapshot → show "—"
- **ASIC framing:** "Score changed +5.2 points since last week" — factual, not advisory

### OG Meta Tags
- **Required:** `og:title`, `og:description`, `og:image`, `og:url`, `og:type: website`
- **Twitter Card:** `twitter:card: summary_large_image`, `twitter:title`, `twitter:description`, `twitter:image`
- **Static image:** 1200x630px PNG in `public/og-image.png` — simple branded card (no dynamic generation)
- **Title:** "RBA Hawk-O-Meter — Rate Pressure at a Glance" (≤60 chars)
- **Description:** "7 economic indicators. One weekly score. No opinion." (~52 chars — Twitter truncates at ~70)
- **Netlify note:** Tags go in `<head>` of `public/index.html` — static HTML, no server-side rendering

### Share Button
- **Implementation:** `if (navigator.share) { navigator.share({title, text, url}) } else { navigator.clipboard.writeText(url).then(() => showToast('Link copied!')) }`
- **Text payload:** "RBA Hawk-O-Meter: Score {hawkScore}/100 — {zone_label}. See what's driving rates: {url}"
- **Placement:** Hero section, near hawk score — primary sharing trigger location
- **Transient activation required:** Must be called directly from a click handler (Web Share API requirement)
- **No SDK, no third-party scripts:** Zero external dependencies

### Historical Hawk Score Chart
- **Library:** Plotly.js (already a dependency) — line chart, `paper_bgcolor: 'transparent'`
- **Data source:** New `data/hawk_score_history.csv` written by pipeline; OR embedded as `overall.history` array in status.json
- **Blocking note:** Meaningful only after 4+ weeks of archiving. Ship chart with "Building history — check back next week" placeholder until 4+ data points exist
- **Visual:** Single line, zone background bands (cold/cool/neutral/warm/hot), x-axis = weekly ISO dates, y-axis = 0-100
- **Mobile:** Use `<details>/<summary>` collapsible wrapper (pattern already used for rate chart in v3) for below-fold mobile

### Newsletter Digest
- **Platform:** Buttondown — REST API, developer-friendly, free ≤100 subscribers, $29/mo for API access (required for automated sends). Preferred over Mailchimp (500 sub free tier, complex API) and ConvertKit (free to 10k subscribers but API automation requires paid plan).
- **Automation:** GitHub Actions post-pipeline step calls Buttondown API to POST email after weekly run
- **Content:** Auto-assembled from status.json: overall score, zone label, top movers (gauges with largest delta), `change_summary` narrative sentences
- **Signup form:** Simple email input + submit → `fetch('https://api.buttondown.email/v1/subscribers', {method: 'POST', body: {email}})` with Buttondown API key
- **ASIC email footer:** Factual-only disclaimer, affiliate disclosure if applicable, unsubscribe link (Buttondown auto-inserts unsubscribe)

---

## Sources

- Canstar Rate Tracker (direct inspection): https://www.canstar.com.au/ratetracker/
- Finder RBA Cash Rate (direct inspection): https://www.finder.com.au/rba-cash-rate
- Craggle RBA Rate Tracker (direct inspection): https://www.craggle.com.au/blog/rba-cash-rate
- ASX RBA Rate Tracker: https://www.asx.com.au/markets/trade-our-derivatives-market/futures-market/rba-rate-tracker
- ASIC INFO 269 — Discussing financial products online: https://www.asic.gov.au/regulatory-resources/financial-services/giving-financial-product-advice/discussing-financial-products-and-services-online/
- ASIC RG 234 — Advertising financial products: https://download.asic.gov.au/media/rkzj5nxb/rg234-published-15-november-2012-20211008.pdf
- @fnando/sparkline library: https://github.com/fnando/sparkline
- MDN Web Share API: https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share
- Open Graph protocol: https://ogp.me/
- OG Tags complete guide (2026): https://share-preview.com/blog/og-tags-complete-guide.html
- Buttondown pricing: https://buttondown.com/pricing
- Eleken Fintech Design Guide 2026: https://www.eleken.co/blog-posts/modern-fintech-design-guide
- FactSet Sparkline usage: https://insight.factset.com/sparkline-charts-enhance-trend-analysis-in-factset-fundamentals-financial-reports
- Australian mortgage affiliate programs: https://www.authorityhacker.com/mortgage-affiliate-programs/
- Mates Rates referral fee benchmarks: https://matesratesmortgages.com.au/ambassador-program/
- Canstar mortgage broker fee disclosure: https://www.canstar.com.au/home-loans/mortgage-brokers-fees/
- Existing codebase (direct analysis — HIGH confidence): `/Users/annon/projects/rba-hawko-meter/public/data/status.json`, `/Users/annon/projects/rba-hawko-meter/pipeline/normalize/engine.py`

---

*Feature research for: RBA Hawk-O-Meter v5.0 Direction & Momentum milestone*
*Researched: 2026-02-26*
