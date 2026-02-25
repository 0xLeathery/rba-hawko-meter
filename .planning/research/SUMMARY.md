# Project Research Summary

**Project:** RBA Hawk-O-Meter — v5.0 Direction & Momentum
**Domain:** Australian economic data dashboard — momentum tracking, social sharing, newsletter monetization
**Researched:** 2026-02-26
**Confidence:** HIGH

## Executive Summary

v5.0 adds direction and momentum signals to a live, working dashboard. The milestone has two distinct layers: a pipeline temporal layer (snapshot archiving and `previous_value` injection) that all delta-related features depend on, and a frontend presentation layer (delta badges, sparklines, historical chart, OG sharing, newsletter capture) that consumes the new data. The critical insight from research is that **snapshot archiving is the single unblocking dependency** — every meaningful new feature either requires it or is enhanced by it. The one exception is sparklines, which can ship immediately using the `history[]` arrays already present in `status.json`, and OG tags + share button, which are pure frontend additions.

The recommended approach is to build the pipeline temporal layer first, then the frontend features in dependency order. No new major libraries are required: sparklines use the Canvas 2D API (hand-rolled, no CDN), the historical hawk score chart reuses the existing Plotly.js instance, the share button uses the native Web Share API, and snapshot archiving uses only Python stdlib. The newsletter capture uses Netlify Forms (free, zero JS) for MVP with MailerLite as the delivery platform. The stack remains entirely within the established no-build-system, CDN-only, vanilla JS IIFE pattern — no npm, no bundler, no new frameworks.

The key risks are: (1) git repository bloat if snapshot files are committed naively — use a JSONL append pattern or per-file snapshots with a hard 52-entry cap; (2) Plotly performance collapse if sparklines reuse Plotly — use Canvas 2D API strictly (page already has 8 Plotly charts; adding 7 more causes Firefox freeze); (3) ASIC compliance exposure if affiliate monetization ships without legal review — defer affiliate links to a gated future decision with legal sign-off; (4) Australian Spam Act violations if newsletter capture launches with a pre-ticked consent checkbox or without a functional unsubscribe link — these are binary compliance requirements enforced by ACMA with fines up to $2.1M per subsequent breach.

## Key Findings

### Recommended Stack

v5.0 requires zero new major library dependencies for its core features. All new JS is hand-rolled vanilla in the existing IIFE pattern. The Python pipeline is extended with one new stdlib-only module (`archive.py`). MailerLite (free plan: 500 subscribers, 12,000 emails/month) is recommended over Buttondown for newsletter delivery because it offers API access on the free plan and a higher email-volume ceiling. Netlify Forms handles the email capture form at zero cost for MVP (100 submissions/month free tier).

The one optional future addition is Pillow (Python, `>=11.0,<12.0`) for dynamic OG image generation from the pipeline — viable but deferred to v5.x since a static branded PNG is sufficient for v5.0 launch. Note: FEATURES.md recommended `@fnando/sparkline` but STACK.md correctly identifies it as ESM-only (incompatible with the no-bundler architecture); Canvas 2D is the confirmed approach.

**Core technologies (new additions only):**
- `pipeline/normalize/archive.py` (new Python module): snapshot archiving and `previous_value` injection — stdlib only (`json`, `pathlib`, `datetime`), zero new dependencies
- `public/js/sparklines.js` (new IIFE): Canvas 2D API sparklines — browser-native, zero CDN dependency
- `public/js/share.js` (new IIFE): Web Share API + `navigator.clipboard` fallback — browser-native, zero CDN dependency
- MailerLite embed JS snippet: newsletter delivery — free plan, copy-paste HTML/JS, no API key exposed in frontend
- Netlify Forms: email capture — `data-netlify="true"` HTML attribute, zero JS, 100 submissions/month free
- Plotly.js 2.35.2 (existing, no change): reused for historical hawk score chart

**What NOT to add:**
- `@fnando/sparkline` — ESM-only; no UMD/IIFE build; incompatible with no-build-system architecture
- Plotly instances for sparklines — 15+ Plotly charts causes page freeze; WebGL cap is 8 instances
- Netlify Edge Functions for dynamic OG images — requires paid tier; overkill for weekly-updating metric
- Any npm package — no build system; npm packages are not loadable without a bundler
- Mailchimp — free plan slashed to 500 contacts/500 emails/month as of January 26, 2026; not viable

### Expected Features

Research confirms the feature set is well-scoped with clear priority ordering. No competitor (Finder, Canstar/RateCity, Mozo, Craggle, ASX Rate Tracker) offers a composite pressure score, auto-generated factual narrative summaries, or a weekly data-driven digest — these three together are the genuine differentiating position.

**Must have (table stakes for v5.0):**
- OG meta tags (`og:title`, `og:description`, `og:image`, `og:url`, Twitter Card) — without these, every shared link is a bare URL; table stakes for any shareable web tool
- Share button (`navigator.share()` + clipboard fallback) — standard on any information tool; zero third-party scripts
- Sparklines on indicator cards — industry-standard on financial data UIs; `history[]` arrays already exist in `status.json`; ships with no pipeline changes
- Delta badges on indicator cards (▲/▼/— + magnitude) — requires `previous_value` from pipeline archive; must be threshold-gated at `|delta| >= 5` to suppress noise

**Should have (competitive differentiators):**
- Historical hawk score chart (Plotly.js line chart over weekly snapshots) — unique in the competitor landscape; gates on 4+ weeks of archived data
- "What changed this week" auto-generated narrative summary (template-based Python, no LLM) — auto-generated factual diff shipped as `change_summary[]` in status.json
- Newsletter signup form + weekly digest delivery (MailerLite) — niche data-driven newsletter; differentiates on neutrality and zero editorial overhead

**Defer to v5.x+:**
- Affiliate/monetization CTA — requires ASIC legal review; meaningful only once newsletter audience is established
- Dynamic OG image generation (Pillow) — static PNG sufficient for v5.0; revisit when branding stabilises
- Twitter/X bot auto-posting — API write access costs $100/month minimum in 2026
- Push notifications — requires service worker + VAPID backend; high friction, low open rate vs email

### Architecture Approach

v5.0 follows a clean extension of the existing architecture. The Python pipeline gains one new module (`archive.py`) and one modification to `engine.py`. The frontend gains two new IIFE modules (`sparklines.js`, `share.js`) and targeted modifications to `interpretations.js`, `gauge-init.js`, and `chart.js`. The `status.json` contract gains optional new fields (`previous_value`, `delta`, `direction` per gauge; `previous_hawk_score`, `hawk_score_delta` in overall) that are absent on the first pipeline run, ensuring graceful degradation from day one. All new frontend modules follow the existing `var ModuleName = (function() { 'use strict'; ... })();` pattern with no exceptions.

**Major components (new/modified):**
1. `pipeline/normalize/archive.py` (new) — writes `public/data/snapshots/YYYY-MM-DD.json` per weekly run; maintains `public/data/snapshots/index.json`; reads prior snapshot for `previous_value` computation via `read_previous_snapshot(min_age_days=5)` guard
2. `pipeline/normalize/engine.py` (modified) — imports archive.py; injects `previous_value`, `delta`, `direction` into each gauge entry before writing status.json; calls `snapshot_current()` after
3. `public/js/sparklines.js` (new IIFE) — Canvas 2D sparklines from `history[]` arrays; called from `gauge-init.js` after bullet gauge creation in the existing rAF chain
4. `public/js/share.js` (new IIFE) — Web Share API + clipboard fallback; button created via `createElement`/`textContent`
5. `public/js/chart.js` (modified) — adds `renderHawkScoreHistory()` function fetching `index.json` + last 26 snapshot files via `Promise.all()`
6. `public/index.html` (modified) — static OG/Twitter meta tags; Netlify Form markup; `<script>` tags for new modules; historical chart container

**Key architectural patterns to follow:**
- Optional fields in status.json: frontend checks `metricData.delta != null` before rendering badge — graceful on first run
- One snapshot file per date in `public/data/snapshots/` with `index.json` manifest — avoids git merge conflicts and unbounded growth
- Canvas 2D for sparklines, not Plotly — keeps Plotly chart count at 8 (1 hero + 7 bullets)
- `element.style.color` with hardcoded hex for delta badge color — never concatenated Tailwind class strings
- `min_age_days=5` guard in `read_previous_snapshot()` — prevents same-week double-runs treating current snapshot as previous

### Critical Pitfalls

1. **Git repository bloat from naive snapshot archiving** — Use a JSONL append pattern (`public/data/history.jsonl`) with a 52-line retention cap, OR per-file snapshots with a 52-file maximum enforced by the pipeline. Decide the storage strategy before writing the first snapshot — retrofitting requires `git filter-repo` history rewrite. Warning signs: `git count-objects -vH` pack-size above 200MB; Netlify deploy times above 2 minutes.

2. **Plotly used for sparklines triggers performance collapse** — The page already has 8 Plotly instances; adding 7 more causes Firefox to freeze and Chrome to show multi-second blanks; WebGL mode caps at 8. Use Canvas 2D API exclusively. Verify with `document.querySelectorAll('.js-plotly-plot').length === 8` after sparklines are added.

3. **Delta badges show noisy daily ASX fluctuations** — ASX futures update daily and can swing 5-10 gauge points on market sentiment. Gate delta badges at `|delta| >= 5` gauge points; compute delta only from the weekly pipeline run (not the daily ASX run); suppress badges for low-confidence indicators.

4. **ASIC compliance — affiliate links may constitute "arranging" a financial product** — Performance-based affiliate links (cost-per-lead, per-conversion) likely require an Australian Credit Licence under the Corporations Act 2001. Do not ship any affiliate link without legal review. Safe structure: a "mere referral" with disclosed referral fee, neutral framing, no implied product recommendation.

5. **Australian Spam Act 2003 non-compliance** — Fines up to $2.1M for subsequent breaches, enforced by ACMA. Express consent required (unchecked checkbox by default), unsubscribe link in every email, functional unsubscribe honored within 5 business days, sender identification in every email. Use MailerLite's double opt-in; never pre-tick the consent checkbox; never import external email lists.

## Implications for Roadmap

Based on the dependency graph derived from research, a 5-phase sequence is recommended. The pipeline temporal layer must come first. Sparklines and OG/share are independent and can run in parallel with Phase 1 or be batched as their own phases. Historical chart and narrative summary wait on both Phase 1 completion and real data accumulation time.

### Phase 1: Pipeline Temporal Layer

**Rationale:** Snapshot archiving is the hard dependency that gates delta badges, historical chart, and narrative summary. It has zero frontend dependencies and can be built, tested, and shipped completely independently. Starting here means delta fields are live in `status.json` before any frontend work touches indicator cards. This is also the phase with the highest-consequence architectural decision (storage format) — make it first.
**Delivers:** `pipeline/normalize/archive.py` with `snapshot_current()` and `read_previous_snapshot(min_age_days=5)`; `previous_value`, `delta`, `direction` fields in status.json per gauge; `previous_hawk_score`, `hawk_score_delta` in overall block; `public/data/snapshots/` directory and `index.json`; extended `file_pattern` in `weekly-pipeline.yml`; unit tests for archive.py; updated engine.py tests for new fields
**Addresses:** DELT-01 (delta infrastructure), HIST-01 (snapshot storage)
**Avoids:** Git repository bloat (enforce JSONL or per-file cap from day one — pitfall 1); `previous_value` pointing to stale data (`min_age_days` guard prevents same-week double-run issues)
**Research flag:** Standard Python patterns — no research phase needed

### Phase 2: Indicator Card UI — Delta Badges + Sparklines

**Rationale:** Delta badges depend on Phase 1's `previous_value` being in status.json. Sparklines are independent (history[] already exists) but co-located in the same card DOM structure — batching them avoids touching `renderMetricCard()` twice. The card mobile layout (375px) must be designed for both elements simultaneously, not sequentially, or the second element will require layout rework.
**Delivers:** Delta badges (▲/▼/— + threshold-gated magnitude at `|delta| >= 5`) on each indicator card; Canvas 2D sparklines from `history[]` on each indicator card; `sparklines.js` IIFE module; modifications to `interpretations.js` (badge element, canvas element) and `gauge-init.js` (sparkline wiring)
**Uses:** Canvas 2D API (no library); `element.style.color` hex pattern; Unicode arrow literals (`\u25b2`, `\u25bc`, `\u2014`)
**Implements:** SparklinesModule (new IIFE), delta badge rendering in InterpretationsModule
**Avoids:** Plotly sparkline performance collapse; delta badge mobile layout overflow; Tailwind class concatenation; noisy daily ASX delta; `innerHTML` ESLint violation
**Research flag:** Standard patterns — no research phase needed; run Playwright at 375px after every card element addition

### Phase 3: Social Sharing — OG Meta Tags + Share Button

**Rationale:** OG tags must precede or accompany the share button — sharing without OG produces bare URL previews that actively deter engagement. These features are entirely independent of the pipeline and indicator card changes, making this phase clean and low-risk. Batching them ensures the `og:image` cache-buster strategy is in place before any URLs are shared publicly.
**Delivers:** Static OG/Twitter Card meta tags in `index.html`; `public/og-image.png` (1200x630 static branded PNG — design prerequisite); `share.js` IIFE module; share button in hero card (via `createElement`/`textContent`); `?v=YYYYMMDD` cache-buster on `og:image` URL; Facebook re-scrape step in GitHub Actions post-deploy
**Uses:** `navigator.share()` + `navigator.clipboard.writeText()` (browser-native); static PNG asset committed to repo
**Avoids:** Missing `og:image` causing text-only link previews; relative URL on `og:image` (social crawlers reject relative paths); stale OG cache after weekly score change
**Research flag:** Standard web patterns — no research phase needed; validate with Facebook Sharing Debugger and Twitter Card Validator before merge

### Phase 4: Historical Hawk Score Chart + Narrative Summary

**Rationale:** The historical chart requires at least 4 weeks of Phase 1 snapshots to display a meaningful line. The "what changed this week" narrative summary also requires `previous_value` from Phase 1. Batching these together means one phase waits the same real-calendar time for data accumulation. Build the chart UI with an "Insufficient data" placeholder state from day one — never ship a flat-line or single-dot chart.
**Delivers:** Historical hawk score Plotly line chart in `chart.js`; fetch of `index.json` + last 26 snapshots in `gauge-init.js` via `Promise.all()`; "Insufficient data" placeholder state (gate on 4+ snapshots); template-based `change_summary[]` array in status.json (Python engine.py modification); historical chart container in `index.html`
**Uses:** Plotly.js 2.35.2 (existing); standard JS `fetch` + `Promise.all()`
**Avoids:** Chart shipping with fewer than 4 data points (enforce minimum data gate); fetching all 52 snapshot files on page load (cap at 26); backfilling from CSVs without documenting approximation
**Research flag:** Plotly scatter/line traces are stable — no research phase needed; verify "Insufficient data" state in Playwright before merging; decide whether to attempt historical backfill during planning

### Phase 5: Newsletter Capture + Delivery

**Rationale:** Newsletter infrastructure requires an external account (MailerLite), legal compliance review of consent form design, and real audience time to accumulate before delivery is meaningful. Placing this last means the dashboard is fully featured for organic sharing (Phase 3) before asking users to subscribe. The Spam Act and ASIC compliance requirements make this phase higher-stakes than its technical complexity suggests — compliance review is a gating requirement, not a post-launch fix.
**Delivers:** Netlify Form email capture in `index.html` (below hero, above indicators — after delivering value); `public/thanks.html` confirmation page; MailerLite account configured with double opt-in; weekly digest template in MailerLite; consent form with unchecked checkbox by default
**Uses:** Netlify Forms (`data-netlify="true"` attribute); MailerLite JS embed snippet; no custom backend
**Avoids:** Pre-ticked consent checkbox (Spam Act violation); missing unsubscribe link; missing sender identification; affiliate links without legal sign-off
**Research flag:** Needs deliberate compliance review — verify Netlify Form configuration, MailerLite double opt-in setting, and consent form HTML against Spam Act checklist before shipping any emails

### Phase Ordering Rationale

- Phase 1 first because it is the hard dependency that unlocks delta badges, historical chart, and narrative summary — and it carries the highest-consequence irreversible decision (storage format); get it right before any frontend work assumes the schema
- Phases 2 and 3 are independent of each other but both depend on Phase 1 completing; Phase 2 depends on status.json delta fields; Phase 3 is entirely independent but benefits from knowing the final URL before baking it into OG tags
- Phase 4 is gated by real calendar time (4 weeks of data accumulation) as well as Phase 1 completion — building it in parallel with Phase 2/3 means the data will be ready by the time the chart UI is merged
- Phase 5 is last because newsletter value compounds with audience, compliance review takes calendar time, and the dashboard must deliver clear value before asking for email sign-ups; affiliate monetization is explicitly excluded from v5.0

### Research Flags

Phases likely needing deliberate compliance review during planning:
- **Phase 5 (Newsletter):** Australian Spam Act and ASIC compliance requirements must be verified against the specific MailerLite configuration before shipping any emails — these are regulatory obligations, not best practices

Phases with well-documented patterns (skip research-phase):
- **Phase 1 (Pipeline Archive):** Pure Python stdlib; pattern verified against existing GHA workflow files; no novel technology
- **Phase 2 (Indicator Card UI):** Canvas 2D API is browser-native and well-documented; delta badge follows existing ESLint-safe DOM patterns established in the codebase
- **Phase 3 (OG + Share):** Static meta tags and Web Share API are fully documented at MDN; validate with platform debuggers, not additional research
- **Phase 4 (Historical Chart):** Plotly scatter/line traces are stable in 2.35.2; fetch-and-parse pattern for JSONL/JSON is standard JS

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technology choices verified against official docs, CDN registries, and existing codebase. Zero novel dependencies for core features. `@fnando/sparkline` ESM-only status confirmed via jsDelivr. MailerLite free plan limits verified from official page. Pillow (optional, future) is MEDIUM — well-established library but not yet integrated with this pipeline. |
| Features | HIGH | Dependency graph verified by direct codebase inspection of `status.json` and `engine.py`. Competitor analysis is MEDIUM (CSS-heavy pages limit full feature visibility) but sufficient for positioning decisions. ASIC compliance research from official ASIC sources (HIGH). |
| Architecture | HIGH | All architectural decisions derived from direct codebase inspection of 8+ source files. Component boundaries, module patterns, and data flow verified against live code. Snapshot storage strategy (per-file with index.json) has clear documented rationale. Canvas 2D sparkline implementation is browser-native with no unknowns. |
| Pitfalls | HIGH | Critical pitfalls sourced from official ASIC/ACMA regulatory documents, Plotly community forum confirmed patterns (WebGL 8-chart cap), and direct codebase analysis. Technical debt patterns and recovery costs are concrete and specific. |

**Overall confidence:** HIGH

### Gaps to Address

- **`history[]` has no timestamps:** Existing `history[]` arrays have no date labels — sparklines must render without x-axis labels and communicate clearly that points represent observations at mixed cadences (quarterly ABS, monthly NAB/Cotality), not uniform calendar intervals. A `history_dated` pipeline enhancement is desirable but not required for v5.0 sparklines, which are trend-signal-only. Flag for Phase 2 planning: decide whether to add `history_dated` alongside sparklines or defer.
- **MailerLite API automation rate limits:** API endpoint limits on the free plan are not exhaustively documented — confirmed available on free plan but specific automation capabilities need testing once account is created. Low risk: newsletter delivery can fall back to manual sends if automation is restricted.
- **Historical backfill decision:** The historical chart will show only a "Building history" placeholder on launch until Phase 1 archives accumulate (4+ weeks). A limited backfill from existing CSVs is feasible for ABS/RBA indicators but approximate for scraped sources. Decide during Phase 4 planning whether to attempt backfill and document any approximation clearly.
- **OG image design:** A 1200x630 PNG needs to be designed and committed before Phase 3 ships. This is a design deliverable, not a code deliverable — flag it as a Phase 3 prerequisite that must be scheduled separately.
- **ASIC affiliate legal review:** No affiliate links should ship in v5.0 without legal sign-off. This is not a gap to resolve during implementation — it is an explicit gate that defers the feature to v5.x+.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `public/data/status.json` — live schema, `history[]` array structure, confirmed absence of `previous_value`
- Direct codebase analysis: `pipeline/normalize/engine.py` — `build_gauge_entry()`, `generate_status()`, history construction
- Direct codebase analysis: `public/js/gauge-init.js`, `interpretations.js`, `gauges.js` — existing DOM patterns, IIFE module structure, double-rAF pattern
- Direct codebase analysis: `.github/workflows/weekly-pipeline.yml` — `git-auto-commit-action@v5` `file_pattern`
- ASIC INFO 269 — discussing financial products online; ASIC RG 234 — advertising; ASIC RG 244 — giving information, general advice
- ACMA — Spam Act 2003, Spam Regulations 2021, unsubscribe rules fact sheet
- MDN: `navigator.share()`, `navigator.clipboard.writeText()`, Canvas 2D API — browser support verified
- MailerLite free plan page — 500 subscribers, 12,000 emails/month confirmed
- Plotly Community Forum — 10+ chart instances performance degradation, WebGL 8-chart cap confirmed
- jsDelivr: `@fnando/sparkline` — ESM-only module types confirmed; no UMD/IIFE build available
- `stefanzweifel/git-auto-commit-action` GitHub repo — v5 confirmed, already in use in both GHA workflows

### Secondary (MEDIUM confidence)
- Competitor direct inspection: Finder, Canstar, Mozo, Craggle, ASX Rate Tracker — CSS-heavy pages limit full feature visibility
- Kit (ConvertKit) free plan — 10,000 subscribers, unlimited emails (third-party review, not official source)
- MailerLite API automation on free plan — available but specific rate limits not fully verified
- HN Law "Finfluencers" commentary — consistent with ASIC official position on "arranging" obligations

### Tertiary (LOW confidence — needs validation)
- Pillow pipeline integration — library is well-established (pypi.org confirmed 11.1.0 as of Feb 2026) but integration with this specific pipeline not yet prototyped
- Historical backfill from existing CSVs — feasibility estimated; rolling Z-score window boundary effects not fully modeled

---
*Research completed: 2026-02-26*
*Ready for roadmap: yes*
