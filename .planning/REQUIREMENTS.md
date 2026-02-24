# Requirements: RBA Hawk-O-Meter

**Defined:** 2026-02-24
**Core Value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

## v2.0 Requirements

Requirements for v2.0 Local CI & Test Infrastructure. Each maps to roadmap phases.

### Test Foundation

- [x] **FOUND-01**: Developer can configure pytest and ruff from a single `pyproject.toml`
- [ ] **FOUND-02**: Unit tests are isolated from production data via autouse DATA_DIR fixture
- [ ] **FOUND-03**: Test fixtures provide deterministic CSV data for reproducible test runs
- [x] **FOUND-04**: Tests are tiered via `@pytest.mark.live` so fast and live tests run separately
- [x] **FOUND-05**: Dev dependencies managed separately in `requirements-dev.txt`

### Python Unit Tests

- [ ] **UNIT-01**: Z-score calculations verified (rolling window, median/MAD, gauge mapping)
- [ ] **UNIT-02**: Zone classification and hawk score computation verified
- [ ] **UNIT-03**: YoY ratio normalization verified (including hybrid Cotality/ABS handling)
- [ ] **UNIT-04**: CSV read/write operations verified (dedup, timestamp handling)
- [ ] **UNIT-05**: status.json validated against schema (required keys, value ranges [0-100], valid zone enums)

### Linting

- [ ] **LINT-01**: Python code passes ruff checks (E/F/W/B/I/UP rules)
- [ ] **LINT-02**: Existing Python violations cleaned up in baseline commit
- [ ] **LINT-03**: JavaScript code passes ESLint v10 checks (IIFE sourceType, browser globals)
- [ ] **LINT-04**: Linting runnable via npm scripts (`lint:py`, `lint:js`, `lint`)

### Live Verification

- [ ] **LIVE-01**: Developer can verify ABS, RBA, ASX API ingestion works with real endpoints
- [ ] **LIVE-02**: Developer can verify Cotality and NAB scrapers work against live pages
- [ ] **LIVE-03**: Full pipeline run produces valid status.json with all indicators
- [ ] **LIVE-04**: Live test failures are non-blocking warnings (graceful degradation preserved)

### Pre-Push Hook

- [ ] **HOOK-01**: Pre-push git hook automatically runs fast test suite before push
- [ ] **HOOK-02**: Fast test suite completes in under 10 seconds
- [ ] **HOOK-03**: Developer can run fast tests manually via `npm run test:fast`
- [ ] **HOOK-04**: Developer can run full verification manually via `npm run verify`

## Future Requirements

### Test Coverage Expansion

- **TEST-01**: Pipeline orchestrator (main.py) integration tests
- **TEST-02**: Code coverage measurement with minimum threshold
- **TEST-03**: Playwright tests running in pre-push hook (currently too slow)
- **TEST-04**: GitHub Actions CI running tests on PR

## Out of Scope

| Feature | Reason |
|---------|--------|
| GitHub Actions test workflow | v2.0 focuses on local CI; GHA test integration is a future milestone |
| Code coverage enforcement | Adding coverage gates before having tests is premature |
| Type checking (mypy) | Adds complexity; ruff catches most issues for this codebase |
| Python formatter (black/ruff format) | Formatting is lower priority than linting; can add later |
| Integration tests for pipeline.main | Orchestration logic is tested implicitly by live verification |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 11 | Complete (11-01) |
| FOUND-02 | Phase 11 | Pending |
| FOUND-03 | Phase 11 | Pending |
| FOUND-04 | Phase 11 | Complete (11-01) |
| FOUND-05 | Phase 11 | Complete (11-01) |
| UNIT-01 | Phase 12 | Pending |
| UNIT-02 | Phase 12 | Pending |
| UNIT-03 | Phase 12 | Pending |
| UNIT-04 | Phase 12 | Pending |
| UNIT-05 | Phase 12 | Pending |
| LINT-01 | Phase 13 | Pending |
| LINT-02 | Phase 13 | Pending |
| LINT-03 | Phase 13 | Pending |
| LINT-04 | Phase 13 | Pending |
| LIVE-01 | Phase 14 | Pending |
| LIVE-02 | Phase 14 | Pending |
| LIVE-03 | Phase 14 | Pending |
| LIVE-04 | Phase 14 | Pending |
| HOOK-01 | Phase 15 | Pending |
| HOOK-02 | Phase 15 | Pending |
| HOOK-03 | Phase 15 | Pending |
| HOOK-04 | Phase 15 | Pending |

**Coverage:**
- v2.0 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-25 after Plan 11-01 execution (FOUND-01, FOUND-04, FOUND-05 complete)*
