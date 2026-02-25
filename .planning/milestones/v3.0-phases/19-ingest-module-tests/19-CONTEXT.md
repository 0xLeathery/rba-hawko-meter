# Phase 19: Ingest Module Tests - Context

**Generated:** 2026-02-25
**Method:** Synthetic discuss (5 agents)
**Status:** Ready for planning

<domain>
## Phase Boundary

Unit tests for all 6 ingest/utility modules in `pipeline/` reaching 85%+ coverage each: `http_client.py`, `abs_data.py`, `rba_data.py`, `asx_futures_scraper.py`, `corelogic_scraper.py`, and `nab_scraper.py`. Tests use the mock-session pattern established in Plan 19-01, exercise all error paths (HTTP errors, parse failures, empty responses, stale data), and run deterministically under the socket-level network blocker with frozen datetime. No orchestration tests (Phase 20). No new fixture files beyond what Phase 18 created. No changes to production code.

</domain>

<decisions>
## Implementation Decisions

### 1. Mock Session Pattern
- **Decision:** Patch `create_session()` at the import site in each module under test. The patch returns a `MagicMock` session whose `.get()` method returns a mock `Response` object with pre-configured `.status_code`, `.text`, `.content`, `.json()`, and `.headers`. A shared `_make_mock_session(responses)` helper function (not a fixture) in each test file builds the mock from a list of response specs.
- **Rationale:** All 5 agents agreed. Patching `create_session()` is the simplest approach -- it avoids testing urllib3 retry internals and focuses on the module's own logic. A per-file helper keeps each test module self-contained while the pattern is consistent across modules. One dedicated test in `test_http_client.py` verifies the real session configuration (retries, user-agent, adapter mounting) separately.
- **Consensus:** 5/5 agents agreed

### 2. Patch Target (Where to Patch)
- **Decision:** Always patch at the import site, not the definition site. For example, patch `pipeline.ingest.abs_data.create_session`, NOT `pipeline.utils.http_client.create_session`. This is required because the modules use `from pipeline.utils.http_client import create_session`, which binds the name locally at import time.
- **Rationale:** All 5 agents agreed. This follows the canonical `unittest.mock` guidance: "patch where it's looked up, not where it's defined." Patching at the definition site would not intercept the already-bound local name, allowing real HTTP calls to leak through (and hit the socket blocker).
- **Consensus:** 5/5 agents agreed

### 3. Datetime Freezing Approach
- **Decision:** Use manual `monkeypatch.setattr()` to replace `datetime` on the specific module under test. Do NOT add `freezegun` as a dependency. For modules that call `datetime.now()` (ASX, CoreLogic, NAB), create a mock datetime class that returns a fixed value from `.now()` while delegating other methods (like `strptime`, `strftime`) to the real `datetime`.
- **Rationale:** 3 of 5 agents preferred manual monkeypatch over freezegun. The project philosophy favors minimal dependencies (REQUIREMENTS.md scopes out heavy test libraries). Manual patching is explicit about what is frozen and avoids freezegun's global patching which can interfere with pandas timestamp operations. The pattern is straightforward: `monkeypatch.setattr(pipeline.ingest.asx_futures_scraper, "datetime", MockDatetime)` where `MockDatetime.now()` returns a fixed value.
- **Consensus:** 3/5 agents agreed (Engineer, Devil's Advocate, Domain Expert)

### 4. Error Path Test Granularity
- **Decision:** Use a hybrid approach: `@pytest.mark.parametrize` for HTTP status code errors that share the same code path (e.g., 400, 404, 500 all trigger the same exception branch), and individual named test functions for structurally different error paths (parse failures, empty responses, missing fields, stale data). This follows the project's established parametrize-heavy convention (test_zscore.py) while keeping each distinct error scenario clearly named.
- **Rationale:** No clear majority -- Architect recommended hybrid, Engineer and Domain Expert favored parametrize, QA and Devil's Advocate favored individual tests. The hybrid approach captures the best of both: parametrize reduces boilerplate for similar paths, while individual tests ensure distinct failure modes have clear names in test output.
- **Consensus:** Claude's Discretion (no majority; hybrid combines both camps)

### 5. Fixture Data Usage
- **Decision:** Load fixture files from `tests/python/fixtures/` for all happy-path and standard error-case tests. Phase 18 created 17 fixture files specifically for Phase 19 consumption (asx_response.json, asx_response_empty.json, rba_cashrate.csv, rba_cashrate_empty.csv, nab_article.html, nab_article_no_data.html, corelogic_article.html, corelogic_article_no_pdf.html, abs_response.csv, abs_response_empty.csv, plus CSV fixtures for each ABS indicator). Add conftest fixture loaders for non-CSV files (JSON, HTML) following the existing `fixture_cpi_df` pattern.
- **Rationale:** All 5 agents agreed. The fixtures exist for this purpose. Loading from files keeps test functions focused on assertions rather than data setup. Conftest loaders provide a clean API (e.g., `fixture_asx_response` returns parsed JSON, `fixture_nab_html` returns bytes).
- **Consensus:** 5/5 agents agreed

### 6. pdfplumber Mock Strategy
- **Decision:** Mock `pdfplumber.open()` as a context manager that returns an object with a `.pages` list. Each mock page has an `.extract_text()` method returning a string containing the expected pattern (e.g., `"Australia 0.8% 2.4% 9.4%"` for CoreLogic, `"Capacity utilisation 83.2%"` for NAB). This exercises the real regex extraction logic while avoiding binary PDF blobs in the repo.
- **Rationale:** All 5 agents agreed, and this aligns with REQUIREMENTS.md which explicitly states "Mock pdfplumber at extract_text() level; avoids binary blobs in repo." The mock returns text that the production regex actually parses, so the extraction logic is genuinely tested. Error cases mock `extract_text()` returning text without the expected pattern, or raising exceptions.
- **Consensus:** 5/5 agents agreed

### Claude's Discretion
- **Error path granularity (Gray Area 4):** The split was 2-2-1 (parametrize vs. individual vs. hybrid). The hybrid approach is adopted: parametrize for same-codepath HTTP errors, individual tests for structurally different failures. This matches the project's existing test style.

</decisions>

<specifics>
## Specific Ideas

- **test_http_client.py as pattern establisher (Plan 19-01):** Write this module first since it validates the session configuration (retries, user-agent, adapter mounting) and establishes the `_make_mock_session` helper pattern that all other test modules will follow.
- **Conftest fixture loaders for non-CSV files:** Add `fixture_asx_response` (JSON dict), `fixture_nab_html` (bytes), `fixture_corelogic_html` (bytes), etc. to conftest.py, following the existing `fixture_cpi_df` pattern.
- **MockDatetime helper class:** Create a reusable `MockDatetime` class (in conftest or in each test file) that freezes `.now()` to a fixed date while passing through `.strptime()`, `.strftime()`, and constructor calls to real `datetime`. This avoids subtle breakage from incomplete datetime mocks.
- **Devil's Advocate warning on mock drift:** Tests verify behavior against fixture data, not against real API responses. Phase 14 live tests serve as the canary for API contract changes. If a scraper's output format changes, live tests will fail first, signaling that fixtures need updating.
- **NAB backfill test isolation:** The `backfill_nab_history()` function has 12 loop iterations. Test with a reduced `months=2` parameter to keep tests fast, and mock `MONTH_URL_PATTERNS` responses to return fixture HTML for known months.
- **ASX `_get_rba_meeting_dates()` reads from `public/data/meetings.json`:** This path is NOT affected by the DATA_DIR fixture (it uses a hardcoded `Path("public/data/meetings.json")`). Tests should mock `open()` or provide the file in `tmp_path` with a monkeypatch on the path.

</specifics>

<deferred>
## Deferred Ideas

- **freezegun dependency:** Two agents (Architect, QA) advocated for freezegun. If manual datetime mocking proves cumbersome across 3+ modules, revisiting this for a future phase is reasonable. Not adding it now per minimal-dependency principle.
- **Fixture validation script:** A script that compares fixture files against live API responses to detect drift. This is out of scope -- Phase 14 live tests implicitly serve this purpose.
- **Integration-level ingest tests:** Testing the full `fetch_and_save()` pipeline end-to-end with mocked HTTP but real CSV writes. These are more integration than unit tests. Could be valuable for Phase 20 or a future coverage phase, but unit tests at the function level are sufficient for 85% coverage.

</deferred>

---
*Phase: 19-ingest-module-tests*
*Context generated: 2026-02-25 via synthetic discuss*
