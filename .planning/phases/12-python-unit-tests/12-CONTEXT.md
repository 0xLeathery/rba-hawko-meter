# Phase 12: Python Unit Tests - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Guard the mathematical core and data pipeline with a fast, deterministic test suite. Covers: z-score calculations (rolling window, median/MAD), gauge mapping, zone classification, hawk score computation, YoY ratio normalization (including hybrid Cotality/ABS handling), CSV read/write operations, and status.json schema validation. All tests run without real file I/O or HTTP calls, completing in under 10 seconds.

</domain>

<decisions>
## Implementation Decisions

### Coverage depth
- Thorough edge cases for z-score: empty input, single-row data, all-identical values (MAD=0), NaN in series, window larger than dataset
- Gauge/hawk score: known-answer tests with hand-verified indicator combinations AND zone boundary precision tests (exact threshold values like 50.0, 33.3)
- YoY ratios: standard ratios, hybrid Cotality-to-ABS data source transition, AND missing/partial/gapped prior-year data
- CSV handler: read/write happy path plus defensive coverage — missing columns, empty file, duplicate timestamps, encoding edge cases
- The live `data/` directory must remain untouched by all tests

### Test data strategy
- Primarily lean on Phase 11 fixture CSVs as main test data source
- Add small inline data only for edge cases the fixtures don't cover
- Hand-calculated expected values for core formulas (MAD, median) — tests verify the code matches the math
- Use scipy/numpy as reference oracle for complex rolling-window scenarios
- Use `@pytest.mark.parametrize` where natural — especially for functions with clear input/output pairs (score-to-zone mapping, multiple CSV scenarios)

### Test file organization
- All tests as top-level functions, no test classes for grouping
- File structure, naming conventions, and docstring approach at Claude's discretion — pick what best fits the actual source code layout and Phase 11's existing test infrastructure

### Schema validation strictness
- `additionalProperties: false` — no extra keys allowed in status.json; catches drift early
- `hawk_score` must be an integer in [0, 100] — no decimals, no values outside range
- Zone enum values strictly validated — unknown zone strings must fail validation
- Validation library/approach at Claude's discretion (jsonschema available in requirements-dev.txt)

### Claude's Discretion
- Test file directory structure (tests/python/unit/ vs flat)
- Floating-point tolerance strategy per function
- Test naming and docstring conventions
- Schema validation implementation approach (jsonschema vs hand-written)
- Exact file-to-module mapping

</decisions>

<specifics>
## Specific Ideas

- Success criterion explicitly requires: a deliberate regression in zscore.py (e.g., returning 0.0) must cause at least one test to fail with a clear assertion message
- The 10-second time budget for the full suite means tests must stay fast — no slow I/O
- Phase 11 already provides fixture CSVs and conftest.py with autouse fixtures and network blocker

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-python-unit-tests*
*Context gathered: 2026-02-25*
