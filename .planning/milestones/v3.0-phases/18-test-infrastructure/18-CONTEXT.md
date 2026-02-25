# Phase 18: Test Infrastructure - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire up test coverage measurement and enforcement infrastructure for the pipeline/ modules. This includes pytest-cov configuration, test library dependencies (pytest-mock, responses), scraper fixture files for all data sources, and a per-module coverage check script. No actual ingest/orchestration tests are written — those are Phase 19 and 20.

</domain>

<decisions>
## Implementation Decisions

### Fixture file content
- Production snapshots: capture real responses from each source, trimmed to relevant sections but structurally identical to production data
- One error variant per source (e.g., empty response, malformed HTML) alongside the happy-path fixture
- Cover all 5 data sources: ASX JSON, RBA CSV, NAB HTML, ABS XML/JSON, CoreLogic HTML — not just the 3 specified in the roadmap
- Flat directory structure at `tests/python/fixtures/` with clear naming (e.g., `asx_response.json`, `rba_cashrate.csv`, `nab_article.html`)

### Coverage script output
- Summary table showing each pipeline/ module with its coverage % on success
- On failure: diff table with columns for module, actual %, target %, and gap (e.g., `abs_data.py  72%  85%  -13%`)
- Color output with auto-detect: ANSI colors when outputting to terminal, plain text when piped or in CI
- Single `--min` flag only — no per-module filtering. YAGNI.

### Coverage artifacts
- JSON only — no HTML coverage reports
- `.coverage` and `.coverage.json` in project root (pytest default location)
- Add both to `.gitignore` — coverage data is ephemeral, not committed
- Clean up existing untracked `.coverage` file by gitignoring it

### Dev dependency location
- Declare pytest-cov, pytest-mock, and responses in `requirements-dev.txt` (matches existing project pattern)
- Use minimum version bounds (e.g., `pytest-cov>=4.0`) — allows patch updates, avoids old version breakage
- Add `--cov=pipeline` to pytest addopts so only production code is measured, not test files

### Claude's Discretion
- Exact fixture file content selection (which parts of production responses to include)
- pytest-cov addopts configuration details beyond --cov=pipeline
- check_coverage.py internal implementation (JSON parsing, table formatting library choice)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-test-infrastructure*
*Context gathered: 2026-02-25*
