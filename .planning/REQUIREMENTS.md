# Requirements: RBA Hawk-O-Meter v1.1

**Defined:** 2026-02-24
**Core Value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

## v1.1 Requirements

Requirements for milestone v1.1 — Full Indicator Coverage. Each maps to roadmap phases.

### ASX Futures

- [ ] **ASX-01**: ASX MarkitDigital endpoint verified working in GitHub Actions CI environment
- [ ] **ASX-02**: Dashboard "What Markets Expect" section displays fresh implied rate and cut/hold/hike probabilities
- [ ] **ASX-03**: Pipeline warns if `asx_futures.csv` has no rows newer than 14 days
- [ ] **ASX-04**: Dashboard shows probability for next 3-4 upcoming RBA meetings, not just the next one

### Housing Prices

- [ ] **HOUS-01**: ABS RPPI data ingested via existing SDMX API pattern, activating the housing gauge
- [ ] **HOUS-02**: Housing gauge displays YoY % change with staleness metadata label when data is older than 90 days
- [ ] **HOUS-03**: Cotality HVI PDF scraped monthly for current dwelling price data
- [ ] **HOUS-04**: Housing gauge uses Cotality data when available, falls back to ABS RPPI when not

### NAB Capacity Utilisation

- [ ] **NAB-01**: Capacity utilisation percentage scraped from NAB Monthly Business Survey HTML article body
- [ ] **NAB-02**: Survey URL discovered via tag archive page, not constructed from date templates
- [ ] **NAB-03**: Business confidence gauge activated with capacity utilisation data
- [ ] **NAB-04**: Gauge shows trend label indicating above/below long-run average (~81%)
- [ ] **NAB-05**: PDF fallback extracts capacity utilisation if HTML extraction fails for a given month

## Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Data Enrichment

- **DATA-01**: NAB PDF historical table parsing for full backseries
- **DATA-02**: Alternative dwelling price sources (PropTrack, Domain) if ABS staleness or Cotality compliance proves unacceptable
- **DATA-03**: Real-time (sub-daily) ASX futures updates

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Daily Cotality scraping | ToS Clause 8.4d prohibits automated scraping; monthly PDF media releases only |
| NAB PDF-only approach | Capacity utilisation is available in HTML; PDF is fallback only |
| Selenium/Playwright for scraping | All target sites render server-side HTML; browser automation is unnecessary overhead |
| camelot-py / tabula-py for PDFs | System-level dependencies (Ghostscript/JVM) block GitHub Actions free tier |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ASX-01 | Phase 8 | Pending |
| ASX-02 | Phase 8 | Pending |
| ASX-03 | Phase 8 | Pending |
| ASX-04 | Phase 8 | Pending |
| HOUS-01 | Phase 9 | Pending |
| HOUS-02 | Phase 9 | Pending |
| HOUS-03 | Phase 9 | Pending |
| HOUS-04 | Phase 9 | Pending |
| NAB-01 | Phase 10 | Pending |
| NAB-02 | Phase 10 | Pending |
| NAB-03 | Phase 10 | Pending |
| NAB-04 | Phase 10 | Pending |
| NAB-05 | Phase 10 | Pending |

**Coverage:**
- v1.1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after roadmap creation (traceability complete)*
