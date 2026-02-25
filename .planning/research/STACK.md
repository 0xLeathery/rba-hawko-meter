# Technology Stack

**Project:** RBA Hawk-O-Meter — v5.0 Direction & Momentum
**Researched:** 2026-02-26
**Scope:** NEW capabilities only — snapshot archiving, previous_value injection, delta badges, sparklines, OG image generation, share button, newsletter infrastructure, affiliate link patterns. Does NOT re-research v1–v4 stack (see v4.0 STACK.md for that baseline).
**Confidence:** HIGH (versions verified against CDN registries, official docs, and official GitHub repos)

---

## Context: What v1–v4 Already Established (Do NOT Re-research or Change)

| Layer | Technology | Version | Status |
|-------|------------|---------|--------|
| CSS framework | Tailwind CSS CDN (v3 Play CDN) | cdn.tailwindcss.com | LOCKED — v4 format incompatible |
| Charts | Plotly.js | 2.35.2 | LOCKED — v3 has breaking title API changes |
| Precision math | Decimal.js | 10.x | LOCKED — calculator unaffected |
| Animation | CountUp.js | 2.9.0 (UMD) | LOCKED — hero score animation |
| Typography | Inter (Google Fonts) | Variable wght 300..900 | LOCKED — loaded in `<head>` |
| JS pattern | Vanilla JS IIFE modules | — | LOCKED — 8 modules in `public/js/` |
| Python pipeline | pandas, numpy, requests, beautifulsoup4, pdfplumber | see requirements.txt | LOCKED |
| CI/CD | GitHub Actions + stefanzweifel/git-auto-commit-action@v5 | — | LOCKED — already writing to repo |
| Hosting | Netlify (static, auto-deploy from git) | — | LOCKED |
| Test tooling | pytest, pytest-cov, pytest-mock, responses, ruff, ESLint v10, Playwright | — | LOCKED |

---

## New Stack Additions for v5.0

### 1. Snapshot Archiving — Git-Based Append Pattern

**Approach:** Python script appends each run's `status.json` snapshot to a growing JSONL (newline-delimited JSON) file `public/data/history.jsonl`. The weekly GitHub Actions workflow already commits files back to the repo via `stefanzweifel/git-auto-commit-action@v5` — extend the `file_pattern` to include `public/data/history.jsonl`.

**No new library.** Uses only standard library `json`, `pathlib`, and `datetime` — all already available in the pipeline Python environment.

| Component | Approach | Why |
|-----------|----------|-----|
| Storage format | `public/data/history.jsonl` — one JSON object per line | JSONL allows O(1) append without loading full file; git diff is line-level so each snapshot is one commit line |
| Storage location | `public/data/` (same as `status.json`) | Netlify serves it statically; pipeline already writes here |
| Commit mechanism | `stefanzweifel/git-auto-commit-action@v5` | Already used in both workflows — zero new GHA configuration |
| Archive trigger | End of weekly pipeline run, after `status.json` is written | Snapshot reflects what was just published |
| `previous_value` injection | Computed in `pipeline/normalize/engine.py`: load last line of `history.jsonl`, inject `previous_value` into each gauge before writing `status.json` | Single source of truth; no new module needed |

**Why NOT GitHub Actions artifacts:** Artifacts have a default 90-day retention, are not publicly accessible without the GH API, and cannot be served as static files to the browser. The git-commit approach stores history in the repo itself — permanently, publicly, and free — and Netlify serves it without any server logic.

**Why NOT a separate `snapshots/` directory with one file per run:** Git history doesn't help the frontend; a single JSONL file is fetched once by the browser and parsed in JS with a single `fetch()` call. One file = one CDN cache entry = minimal Netlify bandwidth.

**Implementation sketch (Python):**
```python
# pipeline/archive.py — called at end of engine.py
import json
from pathlib import Path
from datetime import datetime, timezone

def append_snapshot(status: dict, history_path: Path) -> None:
    snapshot = {
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "hawk_score": status["overall"]["hawk_score"],
        "zone": status["overall"]["zone"],
        "gauges": {
            k: {"value": v["value"], "raw_value": v["raw_value"]}
            for k, v in status["gauges"].items()
        }
    }
    with history_path.open("a") as f:
        f.write(json.dumps(snapshot) + "\n")
```

**Confidence:** HIGH. Pattern verified against existing workflow files (both workflows already use git-auto-commit-action@v5 with `file_pattern`). No third-party library needed.

---

### 2. Sparklines — Hand-Rolled SVG Path (No Library)

**Approach:** Pure vanilla JS that generates an inline `<svg>` element with a `<polyline>` from the `history` array already present in `status.json` for each gauge. Added as a method in the existing `GaugesModule` IIFE or a new lightweight `sparklines.js` IIFE.

**No new library.** The `history` arrays (12 data points, gauge-scale 0–100) already exist in `status.json` and are fetched by `DataModule`. Drawing a polyline over a small SVG viewBox is ~20 lines of JS.

**Why NOT fnando/sparkline (`@fnando/sparkline` v0.3.10):** The library is ESM-only (confirmed on jsDelivr — `["esm"]` module types). Without a bundler (which this project explicitly avoids), ESM can only be loaded with `<script type="module">`. That is technically possible, but it creates a module/non-module hybrid with the existing IIFE scripts and loses access to the global scope that IIFEs rely on. The library is also 4KB overhead for ~20 lines of equivalent logic.

**Why NOT Plotly.js sparklines:** Plotly initialises a full WebGL/SVG canvas with axis machinery per chart. 7 sparklines × Plotly = 7 full layout calculations. The existing gauges already load Plotly; adding more Plotly instances for sparklines bloats DOM and slows paint.

**Implementation pattern:**
```js
// Inside GaugesModule or new sparklines.js IIFE
function renderSparkline(container, points) {
  var W = 80, H = 28, pad = 2;
  var min = Math.min.apply(null, points);
  var max = Math.max.apply(null, points);
  var range = max - min || 1;
  var coords = points.map(function(v, i) {
    var x = pad + (i / (points.length - 1)) * (W - pad * 2);
    var y = H - pad - ((v - min) / range) * (H - pad * 2);
    return x.toFixed(1) + ',' + y.toFixed(1);
  }).join(' ');
  var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);
  var polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  polyline.setAttribute('points', coords);
  polyline.setAttribute('fill', 'none');
  polyline.setAttribute('stroke', '#60a5fa'); // Tailwind blue-400
  polyline.setAttribute('stroke-width', '1.5');
  svg.appendChild(polyline);
  container.appendChild(svg);
}
```

**Confidence:** HIGH. `status.json` already contains `history` arrays (verified from `public/data/status.json` — 12 data points per gauge, scale 0–100). SVG `<polyline>` has universal browser support. Zero CDN dependency, zero library surface area.

---

### 3. OG Meta Tags — Static HTML (No Generation Tool Needed for MVP)

**Approach:** A single static OG image (`public/og-image.png`, 1200×630px) created once and committed to the repo. Netlify serves it. Meta tags are hardcoded in `public/index.html` `<head>`. The hawk score is a weekly number — a static "RBA Hawk-O-Meter" branded card is sufficient for MVP social sharing without dynamic generation.

**No new library for MVP.** Static approach is appropriate because:
- OG image scrapers (Twitter/X, LinkedIn, Telegram, iMessage) cache images aggressively; dynamic images require cache-busting headers not available on Netlify's static CDN without a function
- A branded static card with logo + tagline conveys the product value without showing a specific score (score changes weekly; cached OG images often show week-old data anyway)

**If dynamic OG image is required in a future phase:**
Use Python `Pillow` (already available in the Python ecosystem, trivially installed via `pip install Pillow`) to generate `og-image.png` at the end of each weekly pipeline run, committed alongside `status.json`. This requires no server, no edge function, and no Node.js tooling.

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| **Pillow** (future, optional) | `>=11.0,<12.0` | Generate `og-image.png` with current hawk score text overlay at pipeline run time | Pure Python, no Node.js required; ImageDraw text overlay is ~15 lines; MIT license; available on PyPI; compatible with existing Python 3.11 environment |

**Pillow version:** 11.1.0 is current as of Feb 2026 (verify at pypi.org/project/Pillow before adding). Supported on Python 3.11.

**Static meta tags (add to `public/index.html` `<head>`):**
```html
<!-- Open Graph / social sharing -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://your-site.netlify.app/">
<meta property="og:title" content="RBA Hawk-O-Meter — Rate pressure at a glance">
<meta property="og:description" content="Weekly Australian interest rate pressure index. Data, not opinion.">
<meta property="og:image" content="https://your-site.netlify.app/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="RBA Hawk-O-Meter">
<meta name="twitter:description" content="Weekly Australian interest rate pressure index.">
<meta name="twitter:image" content="https://your-site.netlify.app/og-image.png">
```

**Confidence:** HIGH for static approach. MEDIUM for Pillow dynamic generation (well-established pattern but not yet verified against this project's pipeline integration).

---

### 4. Share Button — Web Clipboard API (No Library)

**Approach:** A share button calls `navigator.clipboard.writeText(window.location.href)` with a fallback for older browsers. Implemented as a vanilla JS event listener added in `main.js` or a new `share.js` IIFE (10 lines). No library needed.

| API | Browser Support | Notes |
|-----|----------------|-------|
| `navigator.clipboard.writeText()` | Chrome 66+, Firefox 63+, Safari 13.1+, Edge 79+ | Requires HTTPS (Netlify provides this). As of June 2024, all major browsers support it. |
| Web Share API (`navigator.share()`) | Chrome 61+ (mobile), Safari 12.1+ | Desktop support varies; iOS/Android work well. Use as progressive enhancement over clipboard. |

**Implementation pattern:**
```js
// share.js IIFE — or add to main.js
(function() {
  var btn = document.getElementById('share-btn');
  if (!btn) return;
  btn.addEventListener('click', function() {
    var url = window.location.href;
    if (navigator.share) {
      // Web Share API (mobile-first, opens native share sheet)
      navigator.share({ title: 'RBA Hawk-O-Meter', url: url }).catch(function() {});
    } else if (navigator.clipboard) {
      // Clipboard API fallback (desktop)
      navigator.clipboard.writeText(url).then(function() {
        btn.textContent = 'Copied!';
        setTimeout(function() { btn.textContent = 'Share'; }, 2000);
      });
    }
    // Silent no-op if neither API available (very old browsers)
  });
}());
```

**No CDN dependency. No library. HTTPS provided by Netlify. Pattern is ASIC-safe (sharing URL, not financial advice).**

**Confidence:** HIGH. `navigator.clipboard.writeText()` verified at MDN as fully supported across modern browsers since June 2024. `navigator.share()` verified at MDN as supported on mobile Chrome/Safari.

---

### 5. Newsletter Infrastructure — MailerLite (Recommended)

**Recommendation: MailerLite Free Plan** — embed form via copy-paste JS snippet, no API call from the frontend, no backend required.

**Comparison:**

| Service | Free Subscribers | Free Emails/mo | Embed Form (Static HTML) | API on Free | Why Consider |
|---------|-----------------|----------------|--------------------------|-------------|--------------|
| **MailerLite** | 500 | 12,000 | Yes — copy-paste JS snippet | Yes (API key required) | Best free limits for a growing audience; embedded form works on static sites with a JS snippet pasted into `index.html` |
| **Kit (ConvertKit)** | 10,000 | Unlimited | Yes — embed via JS snippet | Partial (limited automation on free) | Best free subscriber cap; but landing pages are off-domain (less integrated) |
| **Buttondown** | 100 | Unlimited | Yes — HTML form endpoint | No (API is paid only) | Developer-friendly, markdown-native; but 100 subscriber cap is too low for launch |
| **beehiiv** | 2,500 | Unlimited | Yes — copy-paste HTML snippet | No (API is paid only) | Newsletter-native, growth features; API gated behind paid plan |
| **Mailchimp** | 500 | 500 | Yes | Limited | Free plan slashed to 500 contacts, 500 emails/mo (as of Jan 26, 2026). Not viable. |

**Recommendation rationale:** MailerLite wins because:
1. **12,000 emails/month free** — sufficient for weekly sends to 500 subscribers for a year
2. **Embedded form via JS snippet** — drop-in on static HTML, no backend, no API key exposed in frontend
3. **Automation on free plan** — weekly digest can be templated and scheduled
4. **API available on free plan** — if future automation is needed (e.g., trigger send from GHA after pipeline run), the REST API is accessible with an account API key (stored as GHA secret)

**Kit alternative:** If subscriber count growth is the priority metric, Kit's 10,000 subscriber free cap is unbeatable. The form embed works similarly. Trade-off: less email volume control, landing pages are off-domain.

**Integration (static HTML — no backend required):**

MailerLite provides two code snippets:
1. A universal JS snippet for the `<head>` (loads the MailerLite embed runtime)
2. A form HTML snippet positioned in the page where the capture form appears

Both are pure HTML/JS — no server required. Paste into `public/index.html`.

```html
<!-- 1. In <head> — MailerLite universal script (copy from MailerLite dashboard) -->
<!-- ml("account", "XXXXXXXX"); style of snippet -->

<!-- 2. In page body — form div (copy from MailerLite dashboard) -->
<div class="ml-embedded" data-form="FORM_ID"></div>
```

**Affiliate link integration:** Add plain text + clearly labeled affiliate links in newsletter body and/or in a "Resources" section of the dashboard. Australian AANA Code of Ethics requires clear disclosure ("Paid partnership" / "Affiliate link") in a prominent position. Static HTML: add a `data-affiliate="true"` convention on `<a>` tags and a visible disclosure paragraph in the page footer.

**ASIC note:** Affiliate links for mortgage brokers are referral relationships, not financial advice (no product recommendation, no rate comparison). Link text must be neutral ("Compare your options with [Broker]", not "Get the best rate"). This is distinct from financial advice and within scope for a data-only dashboard.

**Confidence:** MEDIUM-HIGH. MailerLite free plan limits verified from official free plan page (500 subscribers, 12,000 emails/month). Embed form JS snippet pattern verified from official MailerLite documentation. API on free plan is documented but specific endpoint limits not fully verified — LOW confidence on automation via API without further testing.

---

### 6. Historical Hawk Score Chart — Plotly.js (Already Loaded)

**No new library.** The historical hawk score chart (HIST-01) reads from `public/data/history.jsonl` (created by the snapshot archive above) and renders using the existing Plotly.js 2.35.2 instance already loaded on the page.

A Plotly `scatter` trace with `mode: 'lines'` over the `hawk_score` values from `history.jsonl` is the correct approach. This is consistent with the existing chart pattern in `public/js/chart.js` (rate history chart).

```js
// Inside a new history-chart.js IIFE or extending chart.js
fetch('/data/history.jsonl').then(function(r) { return r.text(); }).then(function(text) {
  var snapshots = text.trim().split('\n').map(JSON.parse);
  var dates = snapshots.map(function(s) { return s.archived_at.slice(0, 10); });
  var scores = snapshots.map(function(s) { return s.hawk_score; });
  Plotly.newPlot('history-chart', [{
    x: dates, y: scores, type: 'scatter', mode: 'lines+markers',
    line: { color: '#60a5fa' }
  }], getDarkLayout('Hawk Score History'));
});
```

**Confidence:** HIGH. Plotly scatter/line traces are stable in 2.35.2. JSONL fetch-and-parse pattern is standard JS. No new dependency.

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Netlify Edge Functions for dynamic OG images** | Requires server-side JS runtime, adds complexity, changes deployment posture from pure static. Overkill for a weekly-updating metric. | Static `og-image.png` committed to repo (MVP), or Pillow generation at pipeline build time |
| **Satori / @vercel/og** | Node.js-only, requires a bundler or edge runtime. Incompatible with no-build-system constraint. | Pillow (Python) at pipeline run time if dynamic OG is needed |
| **@fnando/sparkline ESM library** | ESM-only — no UMD/IIFE build available. Cannot be loaded via `<script>` tag without `type="module"`, which creates a module/IIFE hybrid and complicates the existing architecture. | Hand-rolled SVG polyline (~20 lines of vanilla JS) |
| **D3.js for sparklines** | 60KB+ library for what is a 20-line SVG calculation. Already ruled out in v4.0 STACK.md. | Hand-rolled SVG polyline |
| **Mailchimp** | Free plan slashed to 500 contacts / 500 emails per month as of January 26, 2026. Sends cap makes weekly newsletters impractical beyond year 1. | MailerLite (500 contacts, 12,000 emails/month) |
| **Buttondown** | API is paywalled; free plan capped at 100 subscribers. Too restrictive for launch. | MailerLite or Kit |
| **npm install for any new JS dependency** | No build system — npm packages are not loadable without a bundler. Pattern established in all prior milestones. | CDN-loaded UMD/IIFE builds OR native JS/SVG |
| **GitHub Actions artifacts for snapshot storage** | 90-day default retention, not publicly accessible as static files, cannot be Netlify-served, require GH API to download. | Git-committed JSONL file (serves via Netlify CDN, permanent, free) |
| **React/Vue for share button or newsletter form** | Introduces a framework where 10 lines of vanilla JS suffice. Contradicts the architectural decision in PROJECT.md. | Vanilla JS event listener |
| **Web Push Notifications** | Requires a service worker, VAPID keys, and user permission flow. High friction, low open rate vs email. | Email newsletter (MailerLite) |

---

## Stack Patterns by Feature

**Snapshot archiving + `previous_value`:**
- New Python module `pipeline/archive.py` — append to `public/data/history.jsonl`
- Modify `pipeline/normalize/engine.py` — load last JSONL line before computing `status.json`, inject `previous_value` per gauge
- Extend `file_pattern` in both GitHub Actions workflows to include `public/data/history.jsonl`
- No new Python dependency, no new GHA action

**Delta badges:**
- Read `previous_value` from `status.json` in the existing `GaugesModule` (already fetches `status.json`)
- Add badge HTML via `createElement`/`textContent` consistent with ESLint `no-innerHTML` rule
- CSS: Tailwind utility classes for up/down/steady arrow styling — no new library

**Sparklines:**
- New `public/js/sparklines.js` IIFE module OR extend `gauges.js`
- Input: `status.json` `gauges.{metric}.history` array (already fetched)
- Output: inline `<svg>` with `<polyline>` appended to each indicator card

**Historical hawk score chart:**
- New IIFE or extend `chart.js`
- Input: `fetch('/data/history.jsonl')` — one network request, browser-cached
- Output: Plotly scatter trace in a new `<div id="history-chart">` section

**OG meta tags:**
- Edit `public/index.html` `<head>` — add `<meta property="og:*">` and `<meta name="twitter:*">` tags
- Create `public/og-image.png` — 1200×630 static branded card (design tool of choice)
- No code change to any JS module

**Share button:**
- New `<button id="share-btn">` in `index.html`
- New `public/js/share.js` IIFE (10 lines) OR inline in `main.js`
- Uses `navigator.share()` → `navigator.clipboard.writeText()` cascade

**Newsletter capture:**
- MailerLite JS snippet in `<head>` of `index.html`
- MailerLite form `<div>` in page body (below calculator or footer)
- No backend. No API key in frontend (MailerLite embed uses form ID, not account API key)

---

## Version Compatibility

| Package | Current Version | Status | Notes |
|---------|----------------|--------|-------|
| Tailwind CSS CDN | v3 (cdn.tailwindcss.com) | STAY | v4 format incompatible |
| Plotly.js | 2.35.2 | STAY | Used for historical hawk chart too; v3 breaking changes not worth migration |
| CountUp.js | 2.9.0 (UMD) | STAY | Already in production |
| Inter (Google Fonts) | Variable wght 300..900 | STAY | Already loaded |
| Pillow (Python, optional) | `>=11.0,<12.0` | ADD (future, if dynamic OG needed) | Python 3.11 compatible; adds ~3MB to Docker layer but pipeline runs in GHA ubuntu-latest |
| stefanzweifel/git-auto-commit-action | @v5 | STAY | Already used; extend `file_pattern` only |
| actions/upload-artifact | @v4 | NOT ADDED | Artifact approach rejected; git-commit is the strategy |

---

## Installation

No new npm packages. No new CDN scripts for core features. All new JS is hand-rolled vanilla.

**If dynamic OG image generation is added (future milestone):**
```bash
# Add to requirements.txt
Pillow>=11.0,<12.0
```

**Python archive module — no additional install.** Uses only `json`, `pathlib`, `datetime` from stdlib.

**MailerLite embed — no install.** Paste JS snippet from MailerLite dashboard into `public/index.html`.

---

## Integration Points

| Change | File | How |
|--------|------|-----|
| Snapshot archiving | `pipeline/archive.py` (new) | Called at end of `pipeline/normalize/engine.py`; appends to `public/data/history.jsonl` |
| `previous_value` injection | `pipeline/normalize/engine.py` | Load last line of `history.jsonl` before writing `status.json`; add `previous_value` field per gauge |
| Extend GHA file_pattern | `.github/workflows/weekly-pipeline.yml` | Add `public/data/history.jsonl` to `file_pattern` in git-auto-commit step |
| Delta badges | `public/js/gauges.js` | Read `previous_value` from fetched `status.json`; append badge element to each gauge card |
| Sparklines | `public/js/sparklines.js` (new IIFE) | Called from `gauge-init.js` after data load; reads `gauges.{metric}.history` arrays |
| Historical hawk chart | `public/js/chart.js` or new `history-chart.js` | `fetch('/data/history.jsonl')`, parse JSONL, Plotly scatter trace |
| OG meta tags | `public/index.html` `<head>` | Static `<meta>` tags + `public/og-image.png` asset |
| Share button | `public/index.html` + `public/js/share.js` (new) | `<button id="share-btn">` + IIFE event listener |
| Newsletter embed | `public/index.html` | MailerLite JS snippet in `<head>` + form `<div>` in body |

---

## Sources

- **stefanzweifel/git-auto-commit-action** — [github.com/stefanzweifel/git-auto-commit-action](https://github.com/stefanzweifel/git-auto-commit-action) — v5 confirmed, already in use in both GHA workflows (HIGH confidence, verified from repo's own workflow files)
- **GitHub Actions artifact retention** — [docs.github.com/en/actions/writing-workflows](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/storing-and-sharing-data-from-a-workflow) — 90-day default retention, upload-artifact@v4, download-artifact@v5 (HIGH confidence)
- **@fnando/sparkline ESM-only** — [jsdelivr.com/package/npm/@fnando/sparkline](https://www.jsdelivr.com/package/npm/@fnando/sparkline) — v0.3.10, `["esm"]` module types only, no UMD/IIFE build (HIGH confidence, verified from jsDelivr package listing)
- **navigator.clipboard.writeText() browser support** — [MDN Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText) — Chrome 66+, Firefox 63+, Safari 13.1+; full support since June 2024 (HIGH confidence)
- **Navigator.share() browser support** — [MDN Navigator.share()](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share) — mobile Chrome/Safari well-supported; desktop varies (MEDIUM confidence)
- **MailerLite free plan** — [mailerlite.com/free-plan](https://www.mailerlite.com/free-plan) — 500 subscribers, 12,000 emails/month, embedded forms included (HIGH confidence, verified from official page)
- **Kit (ConvertKit) free plan** — [emailtooltester.com](https://www.emailtooltester.com/en/blog/free-email-marketing-services/) — 10,000 subscribers, unlimited emails (MEDIUM confidence, third-party review)
- **Mailchimp free plan reduction** — [blog.groupmail.io/mailchimp-free-plan-changes-2026](https://blog.groupmail.io/mailchimp-free-plan-changes-2026/) — reduced to 500 contacts / 500 emails/mo as of Jan 26, 2026 (HIGH confidence)
- **Buttondown free plan** — [buttondown.com/pricing](https://buttondown.com/pricing) — 100 subscribers free; API is paid-only (HIGH confidence, verified from official pricing page)
- **beehiiv free plan** — [beehiiv.com/pricing](https://www.beehiiv.com/pricing) — 2,500 subscribers free; API is paid-only (HIGH confidence)
- **Pillow for OG image generation** — [pypi.org/project/Pillow](https://pypi.org/project/Pillow/) — Python 3.11 compatible; pattern verified in multiple static site implementations (MEDIUM confidence — library well-established; integration with this pipeline not yet tested)
- **SVG polyline browser support** — MDN — universal; no polyfill needed (HIGH confidence)
- **AANA affiliate disclosure requirements Australia** — [termsfeed.com/blog/australia-affiliate-links-disclaimer](https://www.termsfeed.com/blog/australia-affiliate-links-disclaimer/) — AANA Code of Ethics requires clear, prominent disclosure (MEDIUM confidence — legal context, consult ASIC RG 234 for financial services specifics)
- **GitHub Actions git commit pattern** — [github.com/orgs/community/discussions/25234](https://github.com/orgs/community/discussions/25234) — `permissions: contents: write` + git config + commit pattern (HIGH confidence, already validated in this project's existing workflows)

---

*Stack research for: RBA Hawk-O-Meter v5.0 Direction & Momentum*
*Researched: 2026-02-26*
