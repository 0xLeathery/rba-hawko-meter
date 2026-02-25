# Requirements: RBA Hawk-O-Meter

**Defined:** 2026-02-25
**Core Value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

## v3.0 Requirements

Requirements for 85%+ per-module test coverage across all pipeline/ modules.

### Test Infrastructure

- [ ] **INFRA-01**: pytest-cov wired into pyproject.toml addopts with term-missing and JSON report output
- [ ] **INFRA-02**: pytest-mock and responses added to dev dependencies (requirements-dev.txt + installed)
- [ ] **INFRA-03**: Test fixtures directory with sample HTML, PDF text, and CSV data for scraper tests
- [ ] **INFRA-04**: Per-module coverage check script enforcing 85% minimum per file in pipeline/

### Ingest Tests

- [ ] **INGEST-01**: abs_data.py unit tests covering fetch, parse, and error paths at 85%+
- [ ] **INGEST-02**: rba_data.py unit tests covering fetch, parse, and error paths at 85%+
- [ ] **INGEST-03**: asx_futures_scraper.py unit tests covering fetch, parse, probability derivation, and error paths at 85%+
- [ ] **INGEST-04**: corelogic_scraper.py unit tests covering fetch, PDF parse, URL candidates, and error paths at 85%+
- [ ] **INGEST-05**: nab_scraper.py unit tests covering fetch, HTML/PDF parse, backfill, and error paths at 85%+
- [ ] **INGEST-06**: http_client.py unit tests covering session creation and configuration at 85%+

### Orchestration Tests

- [ ] **ORCH-01**: engine.py unit tests covering normalization pipeline, gauge entry building, and status generation at 85%+
- [ ] **ORCH-02**: main.py unit tests covering pipeline orchestration, partial failure, and critical failure paths at 85%+

### Coverage Enforcement

- [ ] **ENFORCE-01**: Per-module 85% coverage check integrated into npm test scripts
- [ ] **ENFORCE-02**: Coverage check wired into pre-push hook or test:fast command

## Future Requirements

### Extended Coverage

- **ECOV-01**: Integration tests for full pipeline end-to-end with mocked external APIs
- **ECOV-02**: GitHub Actions CI test workflow
- **ECOV-03**: Code coverage badge in README

## Out of Scope

| Feature | Reason |
|---------|--------|
| GitHub Actions CI test workflow | Local CI covers pre-push; GHA integration is a future milestone |
| Code coverage enforcement in CI | No CI test workflow yet; enforce locally first |
| Mutation testing | Overkill for current codebase size |
| Property-based testing (Hypothesis) | Unit tests sufficient for coverage goals |
| VCR cassettes | MagicMock + responses library is lighter and more maintainable |
| Real PDF binary fixtures | Mock pdfplumber at extract_text() level; avoids binary blobs in repo |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 18 | Pending |
| INFRA-02 | Phase 18 | Pending |
| INFRA-03 | Phase 18 | Pending |
| INFRA-04 | Phase 18 | Pending |
| INGEST-01 | Phase 19 | Pending |
| INGEST-02 | Phase 19 | Pending |
| INGEST-03 | Phase 19 | Pending |
| INGEST-04 | Phase 19 | Pending |
| INGEST-05 | Phase 19 | Pending |
| INGEST-06 | Phase 19 | Pending |
| ORCH-01 | Phase 20 | Pending |
| ORCH-02 | Phase 20 | Pending |
| ENFORCE-01 | Phase 20 | Pending |
| ENFORCE-02 | Phase 20 | Pending |

**Coverage:**
- v3.0 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-25 — traceability mapped during roadmap creation*
