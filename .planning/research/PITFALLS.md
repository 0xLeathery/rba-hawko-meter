# Pitfalls Research

**Domain:** Direction & Momentum tracking, social sharing, and newsletter monetization on existing vanilla JS / Plotly.js / Tailwind CDN economic dashboard
**Researched:** 2026-02-26
**Confidence:** HIGH (official ASIC sources, Plotly community confirmed patterns, Australian Spam Act 2003 official text, verified against existing codebase)

---

## Critical Pitfalls

### Pitfall 1: Git Repository Bloat from Snapshot Archiving

**What goes wrong:**
Committing `status.json` snapshots to the repository on every pipeline run (weekly + daily ASX) compounds indefinitely. Git stores full snapshots of binary-similar JSON files rather than meaningful diffs — even small numeric changes cause near-full-file re-storage. After 12 months of weekly pipeline runs plus daily ASX commits, the repository grows by hundreds of megabytes. GitHub free tier has a 1GB repository soft limit and a 5GB hard limit; Netlify re-clones on every deploy, meaning larger repos slow down deploy times.

The current repository already auto-commits `data/abs_cpi.csv`, `data/asx_futures.csv`, and `public/data/status.json` on every pipeline run. Adding a `snapshots/` directory of JSON files with a weekly cadence will accelerate this growth substantially.

**Why it happens:**
The simplest implementation of "archive the previous status.json" is to copy it into a `snapshots/YYYY-MM-DD.json` folder on each pipeline run and commit everything. This works for many months before becoming painful, so no one fixes it until the repo is already bloated. Git LFS or alternative storage is perceived as over-engineering for "just a few JSON files."

**How to avoid:**
- Do **not** commit snapshot files to the repository. Store snapshots outside Git.
- Option A (recommended for zero-cost): Write snapshots to a single append-only `data/snapshots.jsonl` (newline-delimited JSON) file. One line per weekly run. Git diffs JSONL files efficiently since only the new line is added. This keeps the full history in a single tracked file.
- Option B: Store snapshots as a GitHub Actions artifact (90-day retention) or in a free R2/S3-compatible store — but this adds external dependency.
- Option C: Write `previous_value` directly into `status.json` by reading the current values before overwriting — no separate archive file needed at all. This is the minimal approach for DELT-01 (delta badges only).
- **Define a retention policy upfront:** If committing snapshots at all, enforce a maximum count (e.g., 52 weeks = 52 files). Add a pipeline step that deletes files older than the retention window before committing.

**Warning signs:**
- `git count-objects -vH` shows pack-size above 200MB.
- Netlify deploy times increase from ~30s to >2 minutes.
- `git clone` of the repository takes more than 60 seconds on a standard connection.
- `data/snapshots/` directory contains more than 30 JSON files.

**Phase to address:**
Phase 1 (snapshot archiving / pipeline temporal layer). The retention strategy and storage mechanism must be decided before writing a single snapshot. Retrofitting this after 20+ snapshots have been committed requires `git filter-repo`, which rewrites history and breaks all forks/clones.

---

### Pitfall 2: `history` Array Has No Timestamps — Sparklines Are Misleading

**What goes wrong:**
The existing `status.json` `history` arrays are gauge-score sequences (e.g., `[100.0, 100.0, 87.2, 39.0, 10.3, 0.0, 26.4, 30.2]` for inflation). These 12 values are not equally spaced in time — quarterly ABS data, monthly Cotality HVI, weekly ASX futures, and monthly NAB surveys all update at different cadences. Rendering all `history` arrays as sparklines of the same visual width implies equal time intervals between points, which is false. A sparkline of 12 quarterly CPI values looks the same width as 12 monthly housing values, but represents 3 years vs. 1 year.

Additionally, the history arrays have no timestamps attached. The frontend cannot know what time period each point covers, so it cannot label axes, show tooltips with dates, or warn users about gaps.

**Why it happens:**
The history was designed for the rolling z-score window (last N observations), not for display. It captures "gauge scores over past observations" rather than "gauge scores over a time axis." This is correct for the pipeline's mathematical purpose but wrong for user-facing sparklines.

**How to avoid:**
- Add timestamped history to `status.json` alongside (not replacing) the existing unlabelled arrays: `"history_dated": [{"date": "2024-10-01", "value": 26.4}, ...]`.
- Set a fixed display window for sparklines (e.g., last 12 observations) and document this as "approximately N years" not a specific time axis.
- Render sparklines without x-axis labels or ticks — sparklines are trend indicators, not charts. A line going up or down is the only signal.
- Do **not** mix indicators on the same sparkline scale. Each indicator's sparkline must auto-scale to its own min/max, but communicate clearly that scales differ between cards.
- Use a lightweight SVG sparkline (e.g., `@fnando/sparkline` or a 30-line inline SVG path generator) rather than Plotly for sparklines, to avoid the performance trap described in Pitfall 3.

**Warning signs:**
- A developer draws sparklines using the raw `history` array and the line for housing (monthly) looks "flatter" than inflation (quarterly) just because of point density differences.
- Tooltip dates are missing or show "point 7 of 12" rather than an actual date.
- Users interpret the sparkline x-axis as uniform calendar time and draw incorrect conclusions about rate of change.

**Phase to address:**
Phase 1 (snapshot archiving / pipeline temporal layer). The pipeline must emit `history_dated` with timestamps before the frontend can render meaningful sparklines. If `history_dated` is deferred, sparklines must be deferred too — shipping unlabelled sparklines first creates a misleading user experience that is harder to walk back than to delay.

---

### Pitfall 3: Using Plotly.js for Sparklines Triggers a Multi-Chart Performance Collapse

**What goes wrong:**
The dashboard currently renders 1 hero gauge + 7 metric gauges = 8 Plotly charts. Adding 7 sparklines (one per indicator card) would bring the total to 15+ Plotly instances. Plotly.js is an SVG-based library by default — documented community reports show page render becomes noticeably slow with 10+ Plotly charts in DOM, causing Firefox to freeze and Chrome to show multi-second blanks. Additionally, WebGL mode (which is faster) is capped at a maximum of 8 charts simultaneously.

**Why it happens:**
Reusing the existing Plotly dependency is the path of least resistance. It avoids adding a new CDN dependency and uses a library the team already understands. But Plotly is designed for one or two complex charts per page, not for sparkline-style repetition.

**How to avoid:**
- Use inline SVG path generation for sparklines — zero additional CDN dependencies, ~30 lines of vanilla JS. The path is: compute min/max of the history array, map each value to an (x, y) coordinate in a fixed viewBox, render an SVG `<polyline>` or `<path>`.
- Alternatively, load a purpose-built micro-library via CDN (`@fnando/sparkline`: 1.2KB gzipped, zero dependencies) using the same CDN-with-fallback pattern already established for CountUp.js.
- The existing Plotly charts must keep their double-`requestAnimationFrame` stagger pattern. Sparklines must initialize completely separately and must not interfere with Plotly's render cycle.
- If Plotly must be used for sparklines despite this recommendation: use `Plotly.newPlot()` with `staticPlot: true` and `displayModeBar: false` to reduce overhead, and initialize only after all gauge charts have painted.

**Warning signs:**
- Adding sparkline Plotly instances causes the hero gauge to render at zero width (Plotly layout pass is interrupted by competing render calls).
- Page LCP (Largest Contentful Paint) increases from ~800ms to >2000ms after sparklines are added.
- Mobile devices (low-power CPUs) show visible jank or blank cards for 3+ seconds.
- Firefox DevTools shows "Unresponsive script" warning during initial render.

**Phase to address:**
Phase 2 (sparklines / delta badges on indicator cards). Use the inline SVG approach — decide this before any code is written. Retrofitting away from Plotly for sparklines after implementation is a complete rewrite of the sparkline rendering layer.

---

### Pitfall 4: Delta Badges Show Noisy Week-to-Week Changes That Mislead Users

**What goes wrong:**
Delta badges display the change between the current gauge score and the previous one. For indicators with high data volatility or low update frequency, this creates noise that misrepresents the actual trend:

- ASX futures update daily and can swing 5-10 gauge points in a day on market sentiment, even if underlying economic fundamentals haven't changed. A badge showing "↑ 8 points" on Monday and "↓ 6 points" on Thursday looks chaotic.
- Gauge scores for indicators with low confidence (e.g., NAB capacity utilisation — monthly, often with 45+ day staleness) may show large apparent changes when a new data point arrives after a staleness gap, not because of a genuine trend shift.
- The history arrays are gauge scores (0-100), which are non-linear transformations of raw data. A 5-point change at score 50 (neutral zone) is meaningless; the same change near 0 or 100 is significant. Treating all deltas as equally meaningful is misleading.

**Why it happens:**
The simplest delta implementation is `current_value - previous_value`. This is always computable once `previous_value` exists in status.json. The problem only becomes visible to users after the feature ships.

**How to avoid:**
- Threshold-gate delta display: only show a delta badge when `|current - previous| >= 5` gauge points, to suppress noise from minor fluctuations.
- Apply different badge logic per indicator: ASX futures badge should show "no change" unless the weekly pipeline confirms a persistent shift, not daily micro-movements.
- Consider showing direction (up/down arrow) without a numeric value. "This indicator moved up this week" is informative. "This indicator moved up 3.2 points" implies false precision on a derived metric.
- Add a tooltip explaining: "Change since last weekly data update" rather than ambiguously implying "change since last week."
- For LOW-confidence indicators, suppress delta badges entirely or show them with a muted style.
- Never show delta on the hawk score itself without explaining that the score is a weighted composite — a 3-point score change could reflect a single large indicator move, not broad consensus.

**Warning signs:**
- ASX futures delta badge changes daily (or multiple times per day).
- A user feedback or social comment asks "why is the indicator going up and down so much?" when macroeconomic data hasn't changed materially.
- Delta badges for NAB capacity utilisation spike large on the first weekly run after new monthly data arrives, looking alarming even when the underlying trend is stable.

**Phase to address:**
Phase 2 (delta badges / sparklines). Define the threshold-gating rules and per-indicator badge suppression logic as part of the feature specification, not as a follow-up refinement.

---

### Pitfall 5: Delta Badges Break the Indicator Card Mobile Layout

**What goes wrong:**
The indicator cards at mobile (375px) already contain: gauge score, zone label, indicator name, weight badge, staleness badge, and interpretation text. Adding a delta badge and a sparkline to this layout causes one of: (a) the card grows vertically to 220-280px and 7 cards means 1,500-2,000px of scrolling just to see indicators, (b) text elements wrap to two lines and truncate, or (c) the sparkline is squeezed below a readable size (meaningful sparklines need at least 80px wide).

**Why it happens:**
Card layout is usually designed at desktop first, where there is horizontal space to absorb the new elements. Mobile is tested last and by then the architecture of the card is set.

**How to avoid:**
- Design indicator card layout mobile-first for v5.0. Sketch the 375px card layout with all proposed elements before writing any code.
- Establish a card height budget: target 160px maximum per card at 375px. If the budget is exceeded, something must be removed or collapsed.
- Hide sparklines at mobile by default (CSS `hidden md:block`) if they cannot fit meaningfully. A sparkline squeezed to 40px wide communicates nothing.
- Place the delta badge inline with the zone label or gauge score, not as a separate row. A small arrow icon (`↑` / `↓`) next to the score number adds context without extra vertical space.
- Audit the existing card DOM structure in `interpretations.js` before adding new elements — understand what is currently rendered and where there is room.

**Warning signs:**
- At 375px viewport, indicator cards exceed 200px height.
- Weight badge or staleness badge wraps to a second line inside the card header.
- Playwright test at 375px shows card content overflowing its container (visible bottom border clipped).
- Sparkline SVG renders at less than 60px wide.

**Phase to address:**
Phase 2 (delta badges / sparklines). Run Playwright at 375px after every card element addition — not just at end of phase.

---

### Pitfall 6: OG Meta Tags Are Ignored Because the Page Has No `og:image`

**What goes wrong:**
Adding `og:title`, `og:description`, and `og:url` to `index.html` is straightforward, but without `og:image`, major platforms (Facebook, Twitter/X, iMessage, WhatsApp, Slack) either refuse to show a preview card at all, or show a link with no visual — just text. In 2025, link previews without images get significantly lower click-through rates and are sometimes collapsed to a single-line link by the platform.

Generating a dynamic OG image (showing the current hawk score and verdict) is valuable but adds complexity. Generating a static fallback image is easy but goes stale — a static OG image showing "Neutral — Score 50" becomes wrong when the score moves.

**Why it happens:**
Developers add the text OG tags first (easy) and defer the image (complex). The image requirement is only discovered when testing share previews on Facebook Debugger, by which time the architecture for image generation needs to be decided.

**How to avoid:**
- Decide the image strategy before implementing any OG tags:
  - **Static fallback (easiest):** A pre-designed 1200x630px PNG branded image ("RBA Hawk-O-Meter — Check today's rate pressure") that is always the OG image regardless of current score. Stale but always correct for branding.
  - **Pre-generated on pipeline run:** Python pipeline generates a new OG image (using Pillow/PIL) and commits it to `public/images/og.png` on each weekly run. Current score baked into the image. Suitable for this project's zero-cost constraint.
  - **Dynamic via Netlify Edge Function:** Generates image at request time using Satori or similar. Adds runtime infrastructure dependency. Overkill for a static site.
- For this project (zero-cost, static, weekly updates): the pipeline-generated static image is the right balance — it reflects the current score without adding runtime infrastructure.
- Always use absolute URLs for `og:image`: `https://domain.com/images/og.png` not `/images/og.png`. Social crawlers reject relative URLs.

**Warning signs:**
- Facebook Sharing Debugger shows "og:image not found" or "image too small."
- Twitter/X Card Validator shows a text-only preview without an image panel.
- Slack unfurl shows just the URL with no card.
- OG image URL is relative (`/images/og.png`) rather than absolute (`https://...`).

**Phase to address:**
Phase 3 (OG meta tags / share button). Decide the image strategy at the start of the phase — do not add `og:title`/`og:description` without also solving `og:image`.

---

### Pitfall 7: Social Platform OG Cache Serves Stale Previews After Score Changes

**What goes wrong:**
Social platforms (Facebook, Twitter/X, LinkedIn, Slack) aggressively cache OG metadata. Once a URL has been shared, the platform stores the preview indefinitely. When the hawk score changes from "Dovish" to "Hawkish" the following week, any reshare of the same URL will show the cached (stale) preview. Facebook in particular is documented to cache previews "indefinitely" until a manual re-scrape is triggered.

For a dashboard whose value proposition is "current data," showing a week-old verdict in a social preview undermines trust.

**Why it happens:**
Developers test the OG tags once, see a correct preview, and ship. The caching problem only surfaces when the underlying data changes.

**How to avoid:**
- After each weekly pipeline run that updates status.json, trigger a Facebook cache-bust by hitting the [Facebook Sharing Debugger API](https://developers.facebook.com/tools/debug/) scrape endpoint via a GitHub Actions step. This forces a fresh crawl.
- For Twitter/X: use their Card Validator similarly, though X's cache TTL is typically shorter (hours vs. days).
- Add a `?v=YYYYMMDD` cache-buster query parameter to the `og:image` URL. Social crawlers treat different URLs as different resources: `og:image: https://domain.com/images/og.png?v=20260224` will bust the cached image on each weekly run.
- Add `og:updated_time` meta tag with the pipeline's `generated_at` timestamp.
- Accept that preview cache on already-shared URLs cannot be fully controlled — the best outcome is that new shares show current data.

**Warning signs:**
- Sharing the dashboard URL on Slack two weeks after a score change still shows the old verdict in the preview.
- Facebook Sharing Debugger shows "scraped time" as more than 7 days ago.
- `og:image` URL has no cache-busting parameter.

**Phase to address:**
Phase 3 (OG meta tags / share button). Bake the `?v=` query parameter strategy and Facebook scrape step into the implementation from day one.

---

### Pitfall 8: ASIC Compliance — Affiliate Links Constitute "Arranging" a Financial Product

**What goes wrong:**
Adding mortgage broker affiliate links to the dashboard (e.g., "Compare mortgage brokers here" with a referral link) likely constitutes "dealing by arranging" under the Corporations Act 2001, which requires an Australian Financial Services (AFS) licence or an Australian Credit Licence (ACL). This is not a grey area — ASIC's own published guidance explicitly states that "promoting a unique link to a trading platform where a payment is received... upon signing up" is "likely to be dealing by arranging."

The risk extends beyond the affiliate link itself: if the dashboard copy anywhere connects data to a recommendation (even implicitly), it strengthens the case that the site is providing general financial advice rather than factual information.

**Why it happens:**
Affiliate link programs (Lendi, Aussie, Finspo, etc.) have low barriers to entry and are presented as "just adding a link." The compliance implications of receiving referral fees for connecting users to financial product providers are not made clear in affiliate program terms.

**How to avoid:**
- Do **not** integrate performance-based affiliate links (cost-per-lead, cost-per-signup, per-click payments linked to financial product conversions) without seeking legal advice on ACL/AFSL requirements.
- The safest compliant structure is a "mere referral" that: (1) gives only the name of the broker and how to contact them, (2) does not make a recommendation ("use this broker"), and (3) discloses any referral benefit received.
- A newsletter sponsorship model (e.g., "This week's newsletter is supported by [Broker]") is lower risk than per-conversion affiliate links because the payment is for content placement, not for arranging a financial transaction.
- All monetization copy must pass the RG 244 factual information test: the dashboard provides data; any commercial relationship must be disclosed and must not influence the data presentation.
- Include a visible, prominent disclosure on any page containing referral links: "We may receive a referral fee if you contact a broker through this link. This does not constitute financial advice."
- Seek guidance from ASIC's INFO 265 ("Discussing financial products and services online") before shipping any affiliate arrangement.

**Warning signs:**
- The affiliate program pays per lead, per click, or per signup (conversion-based payments).
- The dashboard copy frames the affiliate link as a recommendation ("Talk to an expert") rather than neutral disclosure ("Mortgage brokers operate in this space — find one here").
- There is no disclosure of the commercial relationship anywhere on the page where the affiliate link appears.
- The link appears inside or adjacent to the hawk score verdict, implying the verdict is a signal to act.

**Phase to address:**
Phase 4 (newsletter / monetization foundation). This phase should not ship affiliate links without legal review. The newsletter capture (email, consent management) is lower risk and can ship independently. Affiliate links should be a separate, gated decision.

---

### Pitfall 9: Australian Spam Act 2003 — Newsletter Compliance Mistakes

**What goes wrong:**
Sending marketing emails without complying with the Australian Spam Act 2003 and Spam Regulations 2021 carries fines up to $220,000 per breach (single breach) and up to $2.1 million for subsequent breaches, enforced by ACMA (Australian Communications and Media Authority).

Common compliance failures:
- No clearly visible unsubscribe link in every email.
- Failing to honor unsubscribe requests within 5 business days.
- Sending to email addresses where explicit consent was not collected (implied consent rules in the Spam Act are narrow and generally require a pre-existing business relationship).
- Unclear sender identification (must clearly state who sent the email and their contact details).
- Using a third-party email service that has its own compliance obligations but not configuring it correctly.

**Why it happens:**
Developers focus on the capture form and ESP integration, assuming the email template will handle compliance. But compliance depends on configuration choices (unsubscribe link type, sender identification fields, list segmentation) that must be set deliberately.

**How to avoid:**
- Use an established ESP (Email Service Provider) with Australian Spam Act compliance built in: Mailchimp, ConvertKit, or Buttondown are all compliant by default when configured correctly.
- Collect **express consent** only: a checkbox that is unchecked by default saying "I want to receive the weekly hawk score newsletter." Do not pre-tick the box. Do not bundle consent into terms of service acceptance.
- Every email must include: sender name, sender contact address (physical address or PO Box is acceptable), and a functional unsubscribe link.
- Honor unsubscribe requests within 5 business days — most ESPs automate this.
- Store consent records (timestamp, IP, form version) in case of an ACMA audit.
- Do not import external email lists or purchase lists — this is prohibited under the Spam Act without verifiable consent records.

**Warning signs:**
- The email capture form has a pre-ticked checkbox.
- The unsubscribe link in sent emails leads to a broken or inaccessible page.
- No physical sender address appears in the email footer.
- The ESP account shows emails going to "imported contacts" rather than "subscribed contacts."

**Phase to address:**
Phase 4 (newsletter / monetization foundation). ESP selection and configuration must happen before the first test email is sent. The consent form design and storage mechanism are gating requirements, not afterthoughts.

---

### Pitfall 10: Historical Hawk Score Chart Without Snapshot Archive Produces Flat/Empty Line

**What goes wrong:**
HIST-01 (historical hawk score chart) requires a time-series of past hawk scores to draw a meaningful line chart. Without a snapshot archive, the pipeline has no historical record — `status.json` is overwritten on every run. Attempting to reconstruct the historical hawk score from the existing CSVs is possible (by re-running the Z-score pipeline against historical slices) but is complex and error-prone, especially for indicators with irregular data (Cotality HVI monthly PDF, NAB scraper failures, ASX daily).

Shipping the historical chart UI before the archive has populated at least 4-6 data points produces a chart with a single dot or a very short flat line — misleading and visually poor.

**Why it happens:**
Developers build the frontend chart first (it is the visible feature) and expect to backfill data later. Backfilling historical hawk scores from CSVs is underestimated in complexity because the pipeline's Z-score window and confidence calculations depend on the rolling window of data available at each historical date, not just the raw values.

**How to avoid:**
- Start the snapshot archive (Pipeline phase) before building the frontend chart (UI phase). The chart should only be activated once there are at least 4 weekly snapshots.
- Attempt a limited historical backfill: re-run the normalize pipeline against the last 12 quarters of CSV data to produce 12 historical hawk scores. This is feasible for ABS/RBA indicators but approximate for scraped sources with gaps.
- If backfill is attempted: document clearly that backfilled scores are approximate recalculations, not live pipeline outputs, and may differ slightly from scores that would have been emitted at the time.
- Show an "Insufficient history" placeholder in the chart UI when fewer than 4 snapshots exist, rather than rendering a degenerate chart.

**Warning signs:**
- The historical chart UI is built before the snapshot archive pipeline is implemented.
- The chart is shipped with fewer than 4 data points and looks like a flat line or single dot.
- Backfill code re-runs the pipeline against historical CSVs but the Z-score window produces different results than the live pipeline because the historical data slices don't match the rolling window boundaries.

**Phase to address:**
Phase 1 (snapshot archiving) must be complete before Phase 2+ can ship the historical chart. Gate the chart on data availability.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Commit snapshot JSON files to Git | Zero external dependencies | Repo bloat past GitHub limits within 12-24 months; slow Netlify deploys | Never — use JSONL append pattern or write `previous_value` directly into status.json |
| Draw sparklines using Plotly.js | Reuse existing library | 15+ Plotly instances causes render freeze on mobile; WebGL cap at 8 | Never for sparklines — use inline SVG or micro-library |
| Show raw `history` array as sparkline without timestamps | Simple to implement | Unequal time intervals imply false regularity; users draw incorrect trend conclusions | Never — add `history_dated` before rendering sparklines |
| Add affiliate links without legal review | Revenue potential | ASIC "arranging" violation; AFS/ACL licence required; fines and reputational damage | Never without legal sign-off |
| Pre-tick the newsletter consent checkbox | Higher signup rate | Australian Spam Act violation; express consent required | Never |
| Static OG image without cache-buster | Simple to deploy | Stale score in share previews after weekly pipeline run | Only acceptable for branding-only static images that do not contain live data |
| Import external email list to ESP | Fast list-building | Spam Act violation; no verifiable consent records | Never |
| Show delta badge without threshold-gating | Simpler code | Noisy daily swings in ASX data cause user confusion and trust erosion | Never — gate at `|delta| >= 5` minimum |
| Build historical hawk score chart before archive has data | Visible feature shipped early | Empty/flat chart undermines trust in the dashboard's data depth | Never — gate chart render on minimum 4 historical data points |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GitHub Actions + snapshot archive | Commit full JSON snapshot on every run | Append one line to `data/snapshots.jsonl` per weekly run; keep file in Git with meaningful diffs |
| Python pipeline + `previous_value` | Overwrite status.json without reading current values first | Read the current `value` fields from existing `status.json` before writing the new one; write `previous_value` as part of the same atomic operation |
| Plotly.js + sparklines | Use `Plotly.newPlot()` for each indicator card sparkline | Use inline SVG polyline — no Plotly for sparklines |
| Facebook OG cache + weekly pipeline | Add OG tags and never re-scrape | Add `?v=YYYYMMDD` cache-buster to `og:image` URL; call Facebook scrape endpoint from GitHub Actions post-deploy |
| ESP (Mailchimp/ConvertKit) + consent form | Use the ESP's default double opt-in setting without configuring it | Verify double opt-in is enabled; store timestamp + IP of consent; use unchecked checkbox for initial opt-in |
| Affiliate links + ASIC RG 244 | Frame affiliate link as "speak to an expert" recommendation | Frame as "find a licensed broker in your area" with prominent disclosure of referral relationship |
| Netlify + dynamic OG image generation | Use Netlify Edge Functions for image generation (runtime dependency) | Generate OG image in Python pipeline using Pillow; commit to `public/images/og.png`; reference with absolute URL |
| Tailwind CDN + new badge elements | Assemble badge classes with string concatenation | Use complete literal class strings in full, or use `element.style` for dynamic colors (established project pattern) |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| 15+ Plotly chart instances on page | Page freeze on Firefox; 3+ second blank on mobile; "Unresponsive script" warning | Use inline SVG for sparklines — zero Plotly instances added by v5.0 | Immediately on any low-power mobile device once sparklines use Plotly |
| Large `snapshots.jsonl` file growing unboundedly | Git push times increase; Netlify clone time grows | Cap JSONL at 104 lines (2 years of weekly snapshots); delete oldest lines when cap exceeded | At 52+ weeks if no retention policy is enforced |
| OG image generation in Python pipeline using unoptimized PNG | `og.png` grows to 500KB-1MB; slow social crawl; Netlify bandwidth use | Use Pillow's PNG optimize flag; target 1200x630px at 72dpi; aim for under 100KB | On first generation if image is created at print resolution |
| Email list growth triggering paid ESP tier | Monthly cost surprise; feature parity changes | Choose ESP with generous free tier (Mailchimp: 500 contacts free; ConvertKit: 1,000 subscribers free); monitor list size | At 500-1,000 subscribers depending on ESP |
| Daily ASX futures delta badge causing continuous DOM updates | Card re-renders on every daily ASX pipeline run; visual churn | Only compute delta on weekly pipeline run (not daily ASX run); daily run updates ASX card only, not delta badge | From day one if delta is computed from daily pipeline output |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Email capture form without CSRF protection | Spam submissions; list pollution | Use ESP-hosted embed forms (they handle this) rather than custom POST endpoints |
| Storing email addresses in status.json or public/ directory | Subscribers' emails exposed publicly on Netlify | Store email list only within the ESP; never write emails to any Git-tracked file |
| Affiliate link tracking via query parameters that reveal internal identifiers | Revenue data leakage; partner relationship disclosure | Use ESP-generated UTM parameters only; do not expose internal campaign IDs |
| Newsletter unsubscribe link with predictable token (`?email=user@example.com`) | Anyone can unsubscribe any address by guessing the URL | Use ESP-managed unsubscribe links with opaque tokens (all reputable ESPs do this by default) |
| `innerHTML` in new delta badge or sparkline rendering | XSS if status.json is tampered with (e.g., via a compromised pipeline) | Follow the established project pattern: `textContent` for text, `setAttribute` for SVG attributes, never `innerHTML` for data-driven content |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Delta badge on every indicator card simultaneously | Information overload; user doesn't know what changed matters | Show deltas only on indicators where `|delta| >= 5` gauge points this week; suppress low-signal changes |
| Sparkline and delta badge on the same card row compete visually | Neither element communicates clearly | Hierarchize: sparkline shows trend over time (bottom of card), delta badge shows recent change (inline with score) |
| Historical hawk score chart without a time axis explanation | User doesn't know if they're seeing 3 months or 3 years | Label x-axis with actual dates; add subtitle "Weekly since [start date]" |
| Share button opens native share sheet with just the URL | Shared post on social media has no preview because OG tags are missing or malformed | Verify OG preview in Facebook Debugger and Twitter Card Validator before shipping the share button |
| Newsletter signup widget positioned above indicator data | Users who landed for data feel interrupted before getting value | Place newsletter signup below the economic indicators section (after delivering value), not in the hero or header |
| "Compare brokers here" affiliate link adjacent to hawk score verdict | Implies verdict is a personal recommendation to act | Separate affiliate links from data sections; place in footer or a clearly marked "Resources" section |
| Delta badge shows direction but no magnitude | Users can't tell if it was a tiny or large move | Show direction arrow + numeric delta (when above threshold), e.g., "↑ 8 pts" |

---

## "Looks Done But Isn't" Checklist

- [ ] **Snapshot archive retention policy enforced:** Verify that the pipeline deletes or truncates snapshots beyond the defined retention window. Run the pipeline 3x in CI and confirm the JSONL file does not grow unboundedly.
- [ ] **`previous_value` written atomically:** The pipeline reads the current `status.json` values and writes `previous_value` in a single operation. Verify that a failed pipeline run does not result in `previous_value` pointing to itself.
- [ ] **Sparkline history is timestamped:** Confirm `history_dated` entries in `status.json` have ISO date strings, not just sequential index numbers.
- [ ] **Delta badge threshold-gated:** Verify that cards with `|delta| < 5` show no badge (or a "no change" indicator), not a delta of zero or a small noisy number.
- [ ] **OG image URL is absolute:** Confirm `og:image` contains `https://` not a relative path. Test with Facebook Sharing Debugger before launch.
- [ ] **OG image cache-buster present:** Confirm `og:image` URL includes a versioning parameter that changes with each pipeline run.
- [ ] **Newsletter consent checkbox unchecked by default:** Verify the HTML has `<input type="checkbox">` without a `checked` attribute. Spam Act requires unchecked default.
- [ ] **Unsubscribe link present and functional in every email template:** Send a test email and verify the unsubscribe link resolves and removes the test address from the list.
- [ ] **ASIC affiliate disclosure visible:** If any affiliate or referral link is present, a disclosure statement is visible without requiring the user to scroll or click — on the same viewport as the link.
- [ ] **Mobile card layout verified at 375px:** All indicator cards with sparklines and delta badges render within their card bounds without overflow or text wrapping to more than 2 lines.
- [ ] **Plotly chart count unchanged:** `document.querySelectorAll('.js-plotly-plot').length` still returns 8 after sparklines are added (confirming sparklines use SVG, not Plotly).
- [ ] **Historical hawk score chart shows "insufficient data" state:** Simulate fewer than 4 snapshots and confirm the chart renders a placeholder, not an empty Plotly div with broken axes.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Git repository bloated by snapshot files | HIGH | Use `git filter-repo --path snapshots/ --invert-paths` to remove snapshot directory from history; force-push; notify any collaborators; migrate to JSONL pattern |
| Stale OG preview on social platforms | LOW | Use platform debugger tools (Facebook Sharing Debugger, Twitter Card Validator) to force re-scrape; add `?v=` query parameter to `og:image` going forward |
| Affiliate link identified as potential ASIC violation | HIGH | Remove the link immediately; seek legal advice before re-adding in any form; add prominent disclosure if reinstating as a "mere referral" |
| Newsletter sent without unsubscribe link | MEDIUM | Immediately send a follow-up email with unsubscribe link; update ESP template; document the incident date and remediation for ACMA if ever queried |
| Sparklines implemented with Plotly causing page freeze | MEDIUM | Remove Plotly sparkline instances; reimplement as inline SVG `<polyline>` elements; test on low-power device before re-shipping |
| Delta badge showing noisy daily ASX fluctuations | LOW | Change delta computation to weekly pipeline only; suppress daily ASX run from delta calculations; deploy updated pipeline logic |
| `previous_value` pointing to stale data after pipeline failure | LOW | Add a `previous_value_date` field alongside `previous_value`; render badge as "data unavailable" if `previous_value_date` is more than 14 days old |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Git repository bloat from snapshot archiving | Phase 1: Pipeline temporal layer | Confirm JSONL or equivalent strategy; check `git count-objects -vH` shows minimal growth after 3 test runs |
| `history` array has no timestamps | Phase 1: Pipeline temporal layer | `status.json` contains `history_dated` with ISO date strings before sparkline frontend begins |
| Plotly performance collapse from sparklines | Phase 2: Indicator card UI (sparklines + delta) | `document.querySelectorAll('.js-plotly-plot').length === 8` after sparklines added |
| Delta badge noisy data | Phase 2: Indicator card UI | Delta badges hidden on cards where `|delta| < 5`; ASX daily run does not update badge |
| Delta badge mobile layout breakage | Phase 2: Indicator card UI | Playwright at 375px — all cards within bounds, no overflow |
| OG image missing or relative URL | Phase 3: Social sharing | Facebook Sharing Debugger shows image preview with absolute URL |
| OG cache serving stale previews | Phase 3: Social sharing | `og:image` URL includes `?v=YYYYMMDD`; Facebook re-scrape step in GitHub Actions post-deploy |
| ASIC affiliate compliance violation | Phase 4: Newsletter / monetization | Legal review completed before any affiliate link ships; disclosure visible on same viewport as link |
| Spam Act newsletter non-compliance | Phase 4: Newsletter / monetization | Test email contains unsubscribe link; consent form has unchecked checkbox; ESP configured for double opt-in |
| Historical chart with insufficient data | Phase 5 (if separate): Historical chart | Chart shows "Insufficient data" placeholder when fewer than 4 snapshots exist; minimum data gate enforced in frontend |

---

## Sources

- ASIC official guidance: "Discussing financial products and services online" — [https://www.asic.gov.au/regulatory-resources/financial-services/giving-financial-product-advice/discussing-financial-products-and-services-online/](https://www.asic.gov.au/regulatory-resources/financial-services/giving-financial-product-advice/discussing-financial-products-and-services-online/) (HIGH confidence — official ASIC)
- ASIC RG 244 "Giving information, general advice and scaled advice" — [https://www.asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-244-giving-information-general-advice-and-scaled-advice/](https://www.asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-244-giving-information-general-advice-and-scaled-advice/) (HIGH confidence — official ASIC regulatory guide)
- ASIC media release 12-304MR "ASIC warns comparison websites" — [https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2012-releases/12-304mr-asic-warns-comparison-websites/](https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2012-releases/12-304mr-asic-warns-comparison-websites/) (HIGH confidence — official ASIC enforcement action guidance)
- HN Law "Finfluencers, referrers and discussing financial products online" — [https://www.hnlaw.com.au/finfluencers-referrers-and-discussing-financial-products-online/](https://www.hnlaw.com.au/finfluencers-referrers-and-discussing-financial-products-online/) (MEDIUM confidence — legal commentary consistent with ASIC official position)
- ACMA "Email and SMS unsubscribe rules" fact sheet — [https://www.acma.gov.au/sites/default/files/2024-05/Fact%20sheet%20-%20email%20and%20SMS%20unsubscribe%20rules.pdf](https://www.acma.gov.au/sites/default/files/2024-05/Fact%20sheet%20-%20email%20and%20SMS%20unsubscribe%20rules.pdf) (HIGH confidence — official regulator fact sheet)
- ACMA "Avoid sending spam" — [https://www.acma.gov.au/avoid-sending-spam](https://www.acma.gov.au/avoid-sending-spam) (HIGH confidence — official ACMA guidance)
- Plotly Community Forum: "Plotly.js page render is super slow with 10 charts in DOM" — [https://community.plotly.com/t/plotly-js-page-render-is-super-slow-with-10-charts-in-dom-firefox-freezes-whats-wrong/40936](https://community.plotly.com/t/plotly-js-page-render-is-super-slow-with-10-charts-in-dom-firefox-freezes-whats-wrong/40936) (MEDIUM confidence — community confirmed; consistent with Plotly WebGL 8-chart cap)
- GitHub `mitjafelicijan/sparklines` — lightweight SVG sparkline library, zero dependencies: [https://github.com/mitjafelicijan/sparklines](https://github.com/mitjafelicijan/sparklines) (HIGH confidence — official repository)
- GitHub `fnando/sparkline` — SVG sparklines, zero dependencies: [https://github.com/fnando/sparkline](https://github.com/fnando/sparkline) (HIGH confidence — official repository)
- Netlify: "Generate dynamic Open Graph images using Netlify Edge Functions" — [https://developers.netlify.com/guides/generate-dynamic-open-graph-images-using-netlify-edge-functions/](https://developers.netlify.com/guides/generate-dynamic-open-graph-images-using-netlify-edge-functions/) (HIGH confidence — official Netlify docs)
- Perceptual Edge: "Best Practices for Scaling Sparklines" — [https://www.perceptualedge.com/articles/visual_business_intelligence/best_practices_for_scaling_sparklines.pdf](https://www.perceptualedge.com/articles/visual_business_intelligence/best_practices_for_scaling_sparklines.pdf) (HIGH confidence — authoritative data visualization source, Stephen Few)
- Direct codebase analysis: `public/data/status.json` — `history` arrays confirmed as unlabelled gauge-score sequences with no timestamps; 12 values per indicator at mixed cadences (quarterly ABS, monthly NAB/Cotality)
- Direct codebase analysis: `public/js/gauge-init.js` — 8 existing Plotly chart instances; double-rAF pattern for zero-width prevention
- Direct codebase analysis: `data/abs_cpi.csv`, `data/asx_futures.csv` — existing CSV schemas; no snapshot history directory exists yet

---
*Pitfalls research for: v5.0 Direction & Momentum — snapshot archiving, delta badges, sparklines, social sharing, newsletter monetization*
*Researched: 2026-02-26*
