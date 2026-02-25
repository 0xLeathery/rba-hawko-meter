# Project Research Summary

**Project:** RBA Hawk-O-Meter — v3.0 Full Test Coverage
**Domain:** Python unit test coverage — I/O-heavy scraper, ingest, and orchestration modules
**Researched:** 2026-02-25
**Confidence:** HIGH

## Executive Summary

The v3.0 milestone extends the test infrastructure built in v2.0 (pytest foundation, conftest autouse fixtures, 118 unit tests for pure math modules) to the I/O-heavy layer that was deliberately left uncovered: five ingest/scraper modules, the normalization engine, the pipeline orchestrator, and the HTTP client utility. These modules are currently at 0-42% coverage. The target is 85%+ per-module coverage enforced by a custom `scripts/check_coverage.py` script (since `coverage.py` offers no per-file threshold configuration natively). Three new packages are added: `pytest-mock` for clean multi-target mocking, `responses` for HTTP transport-layer interception (though research ultimately recommends `unittest.mock.MagicMock` with `create_session` patching as the primary pattern), and `pytest-cov` wired into `pyproject.toml addopts` so coverage is measured on every test run including the pre-push hook.

The recommended approach is an inside-out test writing sequence: pure functions first (zero mocking, immediate coverage gains), then file-I/O functions using the existing `isolate_data_dir` autouse fixture, then mock-session tests for the five ingest modules, and finally orchestration tests for `engine.py` and `main.py`. This order is critical because the mock session pattern must be established and verified in one module before being replicated across all five ingest modules. The single most important architectural rule — established in ARCHITECTURE.md and reinforced across all four research files — is that `create_session` must be patched in the module where it is used (e.g., `pipeline.ingest.abs_data.create_session`), not in the source module (`pipeline.utils.http_client.create_session`). Getting this wrong produces confusing `RuntimeError: Network access blocked in tests` failures that look like infrastructure problems.

Three categories of risk dominate the pitfalls research. First, the correct patch target for `create_session` is the most likely source of frustration during Phase 1. Second, error-path coverage is the primary reason modules plateau at 60-70% — every ingest function has 4-8 distinct error branches that each require their own test. Third, date-dependent logic in the CoreLogic and NAB scrapers causes non-deterministic CI failures unless `datetime.now()` is frozen or patched per-test. A fourth structural gap that is easy to miss: `pipeline.config.STATUS_OUTPUT` (pointing to `public/data/status.json`) is NOT patched by the `isolate_data_dir` autouse fixture, so any test calling `generate_status()` writes to the real output file unless explicitly patched.

---

## Key Findings

### Recommended Stack

The v2.0 test infrastructure (pytest 9.0.2, pytest-cov 7.0.0, ruff 0.15.2, jsonschema 4.26.0, lefthook, `unittest.mock` stdlib) requires only three additions for v3.0. All versions verified against PyPI as of 2026-02-25. No changes to `package.json`, the Playwright suite, or GitHub Actions workflows are required.

**Core technologies added:**

- **pytest-mock 3.15.1**: `mocker` fixture for clean multi-target mock trees — auto-resets after each test; use for tests with 3+ simultaneous mock targets; `monkeypatch.setattr` remains for single-target patches
- **responses 0.26.0**: HTTP transport-layer interceptor (released 2026-02-19) — intercepts at `HTTPAdapter.send()` level before the socket blocker fires; HOWEVER, research determined `MagicMock` + `create_session` patching is simpler and sufficient for this codebase; `responses` is available if needed
- **pytest-cov wired into addopts**: Already installed but not wired; add `--cov=pipeline --cov-report=term-missing --cov-report=json:.coverage.json` to `pyproject.toml addopts` so coverage is measured on every `pytest` invocation
- **scripts/check_coverage.py**: ~30-line custom script parsing `.coverage.json` and asserting >=85% per `pipeline/` module; enforced in the lefthook pre-push sequence; necessary because `coverage.py` has no per-file `fail_under` configuration (GitHub issue #444, confirmed unimplemented)

**What NOT to add:** vcrpy/betamax (cassette staleness), httpretty (conflicts with socket blocker), pytest-httpserver (port management overhead), reportlab (4MB for PDF generation), pytest-cov-threshold (unmaintained 2020), pytest-xdist (no payoff at 200-300 test scale), mypy/pyright (explicitly out of scope per PROJECT.md), tox (one Python version target).

### Expected Features

The coverage gap is entirely in I/O-heavy modules. The path to 85% per module is systematic: cover pure functions first (highest effort-to-coverage ratio), then file-reading functions via `tmp_path`, then network-mocking tests for each scraper, then orchestration.

**Must have (table stakes — structurally required to reach 85%):**

- Pure function tests for all zero-I/O functions: `_parse_abs_date`, `_derive_probabilities`, `_find_meeting_for_contract`, `get_candidate_urls`, `generate_interpretation`, `_check_staleness` — fastest wins, zero mocking overhead
- `http_client.py` direct session inspection tests — call `create_session()` with custom params; assert adapter config; no mocking; gets module to 85%+
- `build_gauge_entry` direct tests with synthetic `pd.Series`/`pd.DataFrame` — covers large portion of `engine.py` with no mock setup
- HTML bytes fixture tests for NAB scraper (`extract_capacity_from_html`, `get_pdf_link`) — pure bytes in, value out, zero mocking
- Mock-session tests for all 5 ingest modules: `abs_data`, `rba_data`, `asx_futures_scraper`, `corelogic_scraper`, `nab_scraper` — must cover happy path AND all error branches
- `main.py` orchestration tests — patch all 4 ingest modules at `pipeline.main.*` level; test tier behavior and `sys.exit(1)` with `pytest.raises(SystemExit)`
- pdfplumber mock tests for `extract_cotality_yoy` and `extract_capacity_from_pdf` — mock at `page.extract_text()` level, never use real PDF files

**Should have (pushes coverage beyond 85%):**

- `abs_data.fetch_and_save` ABS filter-path tests (multi-dimensional CSV filter logic)
- `asx_futures_scraper.scrape_asx_futures` full flow with fixture JSON response body
- `engine.py:generate_status` assembly test with real fixture CSVs (not full mock of sub-functions)
- `nab_scraper.discover_latest_survey_url` with two-archive-URL fallback logic
- `nab_scraper.backfill_nab_history` month iteration logic

**Defer to v4+ (future milestone):**

- `engine.py:generate_status` full integration (more appropriate as a smoke test than a unit test)
- `asx_futures_scraper._get_rba_meeting_dates` (reads from `public/data/meetings.json`, not under `DATA_DIR` — needs additional isolation strategy)
- 100% coverage on `main.py` (the `if __name__ == '__main__':` guard is unreachable from pytest; 90-95% is the realistic ceiling)

### Architecture Approach

The v3.0 test expansion adds 8 new test files and 3 new fixture files to `tests/python/`. No existing test files or `conftest.py` are modified. The existing autouse fixtures (`isolate_data_dir`, `block_network`) handle all new ingest tests automatically. The only new shared fixture needed is `engine_data_dir` (patches `STATUS_OUTPUT` in addition to `DATA_DIR`, copies all fixture CSVs and `weights.json` to `tmp_path`).

**Major components:**

1. **8 new test files** — `test_http_client.py`, `test_ingest_abs.py`, `test_ingest_rba.py`, `test_ingest_asx.py`, `test_ingest_corelogic.py`, `test_ingest_nab.py`, `test_engine.py`, `test_main.py` — each owning tests for the named module
2. **`_make_mock_session` helper** — shared within each test file; builds `MagicMock` session/response object; patch target is always `pipeline.ingest.<module>.create_session`
3. **3 new fixture files** — `asx_futures_api_response.json` (MarkitDigital API mock), `rba_a2_data.csv` (RBA A2 with metadata header rows), `nab_article.html` (optional; inline HTML bytes preferred)
4. **`scripts/check_coverage.py`** — reads `.coverage.json`, iterates per-file coverage percentages, asserts each `pipeline/` module meets 85%, exits non-zero with diff table on failure
5. **Updated `pyproject.toml` addopts** — adds `--cov=pipeline --cov-report=term-missing --cov-report=json:.coverage.json` so coverage runs automatically
6. **Updated `requirements-dev.txt`** — adds `pytest-mock>=3.15,<4`, `responses>=0.26,<1`, `pytest-cov>=7.0,<8`
7. **Updated lefthook pre-push** — adds `coverage-check` command after `unit-tests`: `python scripts/check_coverage.py --min 85`

**Four isolation layers that must all be respected:**
- Layer 1: Socket level (`block_network` autouse — any real socket call raises `RuntimeError`)
- Layer 2: HTTP session level (`patch("pipeline.ingest.X.create_session")` in each ingest test)
- Layer 3: Data directory level (`isolate_data_dir` autouse — `DATA_DIR` → `tmp_path`)
- Layer 4: Status output level (must patch `pipeline.config.STATUS_OUTPUT` explicitly in engine tests — NOT covered by autouse)

### Critical Pitfalls

1. **Wrong patch target for `create_session`** — patch `"pipeline.ingest.abs_data.create_session"` (where it is USED), never `"pipeline.utils.http_client.create_session"` (where it is DEFINED). Patching the source has no effect on the already-bound name in the consuming module. Symptoms: `RuntimeError: Network access blocked in tests` even with a mock in place. Resolution: establish the correct target in the first test written for `test_ingest_abs.py` and replicate across all 5 ingest modules.

2. **Missing error-path coverage is the dominant coverage gap** — happy-path-only tests for ingest modules plateau at 60-70%. Each `fetch_abs_series()` has 7 distinct error branches; each `fetch_and_save()` has 4 exception types. Budget 3-6 tests per function, not 1. Symptoms: module stuck at 65% even after adding more tests; uncovered lines are all inside `except` blocks.

3. **Date-dependent logic causes non-deterministic CI failures** — `_current_month_already_scraped()` in CoreLogic and NAB scrapers compares fixture CSV dates against `datetime.now()`. A fixture with `date = 2026-01-01` behaves differently in January vs February. Fix: patch `datetime` at the module level (`pipeline.ingest.corelogic_scraper.datetime`) or use `freezegun` `@freeze_time` decorator. Never use fixture CSVs with the actual current month's date for idempotency tests.

4. **STATUS_OUTPUT not isolated by autouse** — `pipeline.config.STATUS_OUTPUT = Path("public/data/status.json")` is computed at import time and not patched by `isolate_data_dir`. Any test calling `generate_status()` without explicit `monkeypatch.setattr(pipeline.config, "STATUS_OUTPUT", tmp_path / "status.json")` writes to the real production file. Encapsulate in an `engine_data_dir` fixture.

5. **`sys.exit(1)` terminates the entire test runner** — `main.run_pipeline()` calls `sys.exit(1)` on critical failure. Without `pytest.raises(SystemExit)` wrapping, this kills the entire pytest process. All subsequent tests are skipped; their coverage is not recorded. Always wrap critical-failure path tests in `with pytest.raises(SystemExit) as exc_info:` and assert `exc_info.value.code == 1`.

---

## Implications for Roadmap

Based on combined research, the natural build sequence follows dependency order: no mocking needed → file I/O only → mock session → orchestration. This maps cleanly to two phases.

### Phase 1: Ingest Module Tests (HTTP mocking layer)

**Rationale:** Five ingest modules dominate the coverage gap (0-24% each). Covering them requires the mock-session pattern. This pattern must be established first in `test_http_client.py` and `test_ingest_abs.py` because it is reused verbatim across all five modules. Build order within this phase is critical: pure functions first (zero setup), then file-reading functions, then mock-session functions, then error paths.

**Delivers:** 85%+ coverage on `http_client.py`, `abs_data.py`, `rba_data.py`, `asx_futures_scraper.py`, `corelogic_scraper.py`, `nab_scraper.py`. `scripts/check_coverage.py` created and wired into lefthook.

**Features from FEATURES.md:** P1 pure function tests (7 functions), P1 http_client tests, P1 HTML bytes tests, P1 idempotency tests, P2 mock-session tests for abs/rba/asx/corelogic/nab, P2 pdfplumber mock tests.

**Pitfalls to avoid:** Pitfall 1 (wrong patch target), Pitfall 2 (error-path coverage), Pitfall 3 (date-dependent non-determinism), Pitfall 4 (binary PDF fixtures), Pitfall 8 (asx_futures dual path dependency for meetings.json).

**Build sequence within phase:**
1. `test_http_client.py` — establishes direct inspection pattern; zero mocking
2. `test_ingest_abs.py` — establishes `_make_mock_session` helper and correct patch target
3. `test_ingest_rba.py` — same pattern; key difference is metadata header row handling
4. `test_ingest_asx.py` — pure functions first; then mock session + meetings.json patch
5. `test_ingest_corelogic.py` — get_candidate_urls pure; then pdfplumber mock pattern
6. `test_ingest_nab.py` — most complex; HTML bytes first; pdfplumber last; backfill guard via pre-populated CSV

### Phase 2: Engine and Orchestration Tests (multi-module wiring)

**Rationale:** `engine.py` and `main.py` depend on all ingest modules being individually tested and their return contracts understood. Engine tests should use real sub-functions (normalize_indicator, compute_rolling_zscores) with fixture CSV data — not mocks of those functions — so wiring errors are caught. `main.py` tests mock entire ingest modules at `pipeline.main.*` level to test tier-failure behavior independently of ingest correctness.

**Delivers:** 85%+ coverage on `engine.py` and `main.py`. Full 85%+ per-module milestone confirmed by `scripts/check_coverage.py` passing in lefthook.

**Features from FEATURES.md:** P1 `build_gauge_entry` direct tests, P1 `build_asx_futures_entry` tmp_path tests, P2 `generate_status` assembly tests, P2 `main.py` orchestration tests.

**Pitfalls to avoid:** Pitfall 4 (STATUS_OUTPUT not isolated — use `engine_data_dir` fixture), Pitfall 5 (coverage gaming with trivial assertions), Pitfall 6 (over-mocking generate_status — use real sub-functions for integration-style tests), Pitfall 7 (`sys.exit(1)` must be wrapped in `pytest.raises(SystemExit)`), Pitfall 9 (housing auxiliary file gap — create corelogic_housing.csv and nab_capacity.csv for build_gauge_entry tests).

**Build sequence within phase:**
1. `generate_interpretation` parametrized — 35 combos (7 indicators × 5 zones), zero I/O
2. `build_asx_futures_entry` with tmp_path CSV — uses existing `isolate_data_dir`
3. `build_gauge_entry` with synthetic Series/DataFrame — standard, housing, and business_confidence enrichment branches
4. `process_indicator` with fixture CSVs in `engine_data_dir`
5. `generate_status` end-to-end with `engine_data_dir` fixture
6. `test_main.py` — all tier behaviors, sys.exit contract, result dict structure

### Phase Ordering Rationale

- Phase 1 before Phase 2: `main.py` orchestration tests require understanding what each scraper's `fetch_and_save()` returns on success and failure. Those return contracts are only verified by writing Phase 1 tests first.
- Pure functions before mock-session tests within Phase 1: pure function tests are zero-cost to write and immediately improve coverage percentages, confirming the module is importable and partially working before more complex setup is invested.
- Error paths within each module immediately after happy paths: attempting to write all happy paths first, then all error paths, leads to over-mocking and coverage gaming. Error paths are harder the longer you wait.
- Engine tests use real sub-functions (not mocked): avoids Pitfall 6 — mocking `normalize_indicator` in engine tests means wiring errors are invisible. Use real functions on fixture data.

### Research Flags

Phases with standard patterns (research already complete — no further research needed):
- **Phase 1 (Ingest tests):** All patterns are fully documented in ARCHITECTURE.md with production-ready code examples. The `_make_mock_session` helper, pdfplumber mock pattern, and HTML bytes fixture approach are all verified and ready to implement.
- **Phase 2 (Engine/main tests):** `engine_data_dir` fixture pattern fully specified in ARCHITECTURE.md. `pytest.raises(SystemExit)` pattern for `sys.exit` testing is documented with code examples in both FEATURES.md and PITFALLS.md.

Phases requiring attention during execution:
- **Phase 1 — ASX futures scraper specifically:** Has two implicit file dependencies (`public/data/meetings.json` under a hardcoded relative path outside `DATA_DIR`; `rba_cash_rate.csv` under `DATA_DIR`). Both must be addressed before writing `scrape_asx_futures()` tests. Patch `_get_rba_meeting_dates` directly; create `rba_cash_rate.csv` in `tmp_path`.
- **Phase 1 — NAB scraper specifically:** `backfill_nab_history()` is triggered if `nab_capacity.csv` has fewer than 3 rows. Pre-populate `tmp_path / "nab_capacity.csv"` with 5+ rows in any test for `scrape_nab_capacity()` to prevent inadvertent backfill execution that would make the test suite take 10-30 seconds.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All 3 new packages verified against PyPI at current stable versions. `pytest-mock 3.15.1`, `responses 0.26.0` (released 2026-02-19), `pytest-cov 7.0.0` already locally installed. Version compatibility cross-checked against Python 3.11/3.13. `coverage.py` per-file limitation confirmed via official docs and open GitHub issue #444. |
| Features | HIGH | Feature list derived entirely from direct codebase analysis of live `pipeline/` and `tests/python/` directories. Coverage percentages are real measurements, not estimates. Prioritization matrix is grounded in actual module structure. |
| Architecture | HIGH | All patterns verified against the live codebase. Import paths, autouse fixture behaviors, `STATUS_OUTPUT` isolation gap — all confirmed by direct code inspection. Code examples in ARCHITECTURE.md are production-ready, not illustrative. Build order dependencies are concrete and grounded in Python import semantics. |
| Pitfalls | HIGH | All 9 pitfalls derived from direct codebase analysis — not generic test-writing pitfalls. Specific line references (e.g., `asx_futures_scraper._get_rba_meeting_dates()` hardcoded `Path("public/data/meetings.json")`), confirmed in source. `conftest.py` gap for `STATUS_OUTPUT` verified by reading actual conftest implementation. |

**Overall confidence: HIGH**

### Gaps to Address

- **`freezegun` vs manual `datetime` patch:** PITFALLS.md documents both approaches for date-dependent tests. Neither `freezegun` is currently in `requirements-dev.txt` nor is manual `datetime` patching established in the existing test suite. Decision needed at implementation time: add `freezegun>=1.5,<2` to `requirements-dev.txt` (cleaner `@freeze_time` decorator) or use `monkeypatch.setattr("pipeline.ingest.MODULE.datetime", ...)` inline (no new dependency). Low risk — either approach works; consistent choice matters more than which choice.

- **FEATURES.md vs STACK.md on `responses` library:** STACK.md recommends using `responses` for HTTP mocking. FEATURES.md recommends `MagicMock` + `create_session` patching as primary, with `responses` listed as an anti-feature (VCR cassette staleness concern extends to `responses` when used with recorded fixtures). Resolution: use `MagicMock` + `create_session` patching as the primary pattern; install `responses` in `requirements-dev.txt` in case specific tests need transport-layer interception, but do not use it as the default.

- **`engine.py` deferred imports (`import pandas as _pd` inside function body):** PITFALLS.md identifies uncovered lines in `build_gauge_entry()` housing/business_confidence branches due to inline imports. Coverage tool may or may not count these import lines differently. Verify during implementation — the fix is simply to write tests that exercise those branches.

---

## Sources

### Primary (HIGH confidence)

- PyPI: pytest-mock 3.15.1 — https://pypi.org/project/pytest-mock/ (verified Feb 2026)
- PyPI: responses 0.26.0 — https://pypi.org/project/responses/ (released 2026-02-19, verified)
- PyPI: pytest-cov 7.0.0 — https://pypi.org/project/pytest-cov/ (already installed locally)
- coverage.py per-file threshold limitation — https://coverage.readthedocs.io/en/latest/config.html and https://github.com/pytest-dev/pytest-cov/issues/444 (confirmed unimplemented)
- Python unittest.mock "where to patch" — https://docs.python.org/3/library/unittest.mock.html#where-to-patch (fundamental mock patching rule)
- pytest.raises(SystemExit) — https://docs.pytest.org/en/stable/reference/reference.html (official docs)
- pytest monkeypatch — https://docs.pytest.org/en/stable/how-to/monkeypatch.html (official docs)
- Live codebase analysis: `/Users/annon/projects/rba-hawko-meter/pipeline/` — all modules read, coverage percentages confirmed, import structures verified
- Live codebase analysis: `/Users/annon/projects/rba-hawko-meter/tests/python/` — conftest.py, existing test files, fixture CSVs verified

### Secondary (MEDIUM confidence)

- responses + Session/HTTPAdapter: https://github.com/getsentry/responses — intercepts at HTTPAdapter.send(), confirmed Session support
- pytest-cov configuration: https://pytest-cov.readthedocs.io/en/latest/config.html — addopts integration pattern
- coverage.py JSON report format: https://coverage.readthedocs.io/en/latest/config.html — `--cov-report=json` supported
- Web scraper mocking patterns: https://datawookie.dev/blog/2025/01/test-a-web-scraper-using-mocking/ (Jan 2025, practitioner source)
- pdfplumber BytesIO/mock behaviour: https://github.com/jsvine/pdfplumber/issues/124 (confirms mock approach is correct)

### Tertiary (LOW confidence — needs validation during implementation)

- freezegun `@freeze_time` decorator — widely documented but not yet verified against this specific codebase's `datetime` import patterns; validate before committing to approach
- `requests-mock` 1.12.1 — considered and deprioritized vs `responses` due to March 2024 last update; if `responses` proves problematic, `requests-mock` is a drop-in alternative

---

*Research completed: 2026-02-25*
*Ready for roadmap: yes*
