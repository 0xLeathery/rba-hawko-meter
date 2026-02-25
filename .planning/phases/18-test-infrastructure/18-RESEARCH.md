# Phase 18: Test Infrastructure - Research

**Researched:** 2026-02-25
**Domain:** pytest-cov configuration, scraper fixture files, coverage enforcement script
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Fixture file content:**
- Production snapshots: capture real responses from each source, trimmed to relevant sections but structurally identical to production data
- One error variant per source (e.g., empty response, malformed HTML) alongside the happy-path fixture
- Cover all 5 data sources: ASX JSON, RBA CSV, NAB HTML, ABS XML/JSON, CoreLogic HTML — not just the 3 specified in the roadmap
- Flat directory structure at `tests/python/fixtures/` with clear naming (e.g., `asx_response.json`, `rba_cashrate.csv`, `nab_article.html`)

**Coverage script output:**
- Summary table showing each pipeline/ module with its coverage % on success
- On failure: diff table with columns for module, actual %, target %, and gap (e.g., `abs_data.py  72%  85%  -13%`)
- Color output with auto-detect: ANSI colors when outputting to terminal, plain text when piped or in CI
- Single `--min` flag only — no per-module filtering. YAGNI.

**Coverage artifacts:**
- JSON only — no HTML coverage reports
- `.coverage` and `.coverage.json` in project root (pytest default location)
- Add both to `.gitignore` — coverage data is ephemeral, not committed
- Clean up existing untracked `.coverage` file by gitignoring it

**Dev dependency location:**
- Declare pytest-cov, pytest-mock, and responses in `requirements-dev.txt` (matches existing project pattern)
- Use minimum version bounds (e.g., `pytest-cov>=4.0`) — allows patch updates, avoids old version breakage
- Add `--cov=pipeline` to pytest addopts so only production code is measured, not test files

### Claude's Discretion
- Exact fixture file content selection (which parts of production responses to include)
- pytest-cov addopts configuration details beyond --cov=pipeline
- check_coverage.py internal implementation (JSON parsing, table formatting library choice)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | pytest-cov wired into pyproject.toml addopts with term-missing and JSON report output | pytest-cov 7.0.0 already installed; addopts configuration pattern verified; JSON output to `.coverage.json` confirmed working via `--cov-report=json:.coverage.json` |
| INFRA-02 | pytest-mock and responses added to dev dependencies (requirements-dev.txt + installed) | Both absent from requirements-dev.txt and not installed; latest available: pytest-mock 3.15.1, responses 0.26.0 |
| INFRA-03 | Test fixtures directory with sample HTML, PDF text, and CSV data for scraper tests | `tests/python/fixtures/` exists with 7 processed-output CSVs; needs 10 new scraper-input fixture files (5 sources × happy-path + error variant); PDF fixture: mock pdfplumber not binary (per REQUIREMENTS.md out-of-scope decision) |
| INFRA-04 | Per-module coverage check script enforcing 85% minimum per file in pipeline/ | `.coverage.json` schema verified (files → summary → percent_covered); script reads JSON, computes pass/fail per pipeline/ module, formats table, uses sys.stdout.isatty() for color auto-detect |
</phase_requirements>

## Summary

This phase wires pytest-cov into pyproject.toml so coverage runs automatically on every `pytest` invocation, installs two missing test helper libraries (pytest-mock and responses), creates scraper fixture files for all 5 data sources, and writes a `scripts/check_coverage.py` enforcement script. The project already has pytest 9.0.2 and pytest-cov 7.0.0 installed; the gap is configuration only for INFRA-01, and missing entries in requirements-dev.txt plus missing fixture files and the coverage script.

The existing `tests/python/fixtures/` directory contains 7 processed-output CSVs (abs_cpi.csv, abs_employment.csv, etc.). Those are post-pipeline data that existing tests consume. The new fixtures for Phase 18 are raw HTTP response fixtures — the input side of each scraper — used by Phase 19 unit tests. They need to live in the same directory (flat structure, per locked decision).

The coverage script reads `.coverage.json` (written by `--cov-report=json:.coverage.json` in addopts). The JSON schema is `{files: {<path>: {summary: {percent_covered: float}}}}`. Only `pipeline/` files need enforcing; `__init__.py` files with 0 statements count as 100% and should be excluded from the diff table to avoid noise.

**Primary recommendation:** Three sequential tasks — (1) wire pyproject.toml addopts + update requirements-dev.txt + install, (2) create the 10 scraper fixture files, (3) write scripts/check_coverage.py.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest-cov | 7.0.0 (installed) | Coverage measurement integrated into pytest | Official pytest plugin; addopts pattern avoids manual --cov flags |
| pytest-mock | 3.15.1 (latest) | `mocker` fixture wrapping unittest.mock | Cleaner syntax than monkeypatch for complex mocks; standard for scraper tests |
| responses | 0.26.0 (latest) | HTTP request interception at transport layer | Complements MagicMock; intercepts `requests.Session.send` without patching `create_session` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| coverage.py | 7.13.4 (installed, pytest-cov dependency) | Underlying coverage engine | Never call directly — pytest-cov drives it |
| sys (stdlib) | — | `sys.stdout.isatty()` for color auto-detect in check_coverage.py | Standard approach; no third-party color library needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `responses` library | `unittest.mock` + patch | `responses` is more natural for URL-based interception; `mock` is primary (per STATE.md decision), `responses` is optional |
| pytest-cov addopts | `.coveragerc` file | addopts in pyproject.toml keeps all tool config in one file; .coveragerc is redundant |
| stdlib `json` + manual table | `rich` or `tabulate` | YAGNI; stdlib is zero-dependency and sufficient for a simple diff table |

**Installation:**
```bash
pip install pytest-mock>=3.15 responses>=0.26
```

## Architecture Patterns

### Recommended Project Structure
```
tests/python/fixtures/        # already exists
├── abs_cpi.csv               # existing — post-pipeline processed output
├── abs_employment.csv        # existing
├── abs_household_spending.csv # existing
├── abs_wage_price_index.csv  # existing
├── abs_building_approvals.csv # existing
├── corelogic_housing.csv     # existing
├── nab_capacity.csv          # existing
├── asx_response.json         # NEW — raw MarkitDigital API JSON (happy path)
├── asx_response_empty.json   # NEW — empty items list (error variant)
├── rba_cashrate.csv          # NEW — raw RBA CSV with metadata headers (happy path)
├── rba_cashrate_empty.csv    # NEW — CSV with no data rows after header (error variant)
├── nab_article.html          # NEW — NAB article HTML with capacity utilisation % (happy path)
├── nab_article_no_data.html  # NEW — NAB article HTML with no capacity text (error variant)
├── abs_response.csv          # NEW — ABS SDMX CSV response (happy path, CPI format)
├── abs_response_empty.csv    # NEW — ABS response with header only, no data rows (error variant)
├── corelogic_article.html    # NEW — Cotality page listing PDF link (happy path)
└── corelogic_article_no_pdf.html # NEW — Cotality page with no PDF link (error variant)

scripts/
└── check_coverage.py         # NEW — reads .coverage.json, enforces 85% per pipeline/ module
```

### Pattern 1: pytest-cov addopts in pyproject.toml
**What:** Wire `--cov=pipeline --cov-report=term-missing --cov-report=json:.coverage.json` into addopts so every `pytest` invocation produces coverage automatically.
**When to use:** Always — this is the locked decision.
**Example:**
```toml
# pyproject.toml [tool.pytest.ini_options]
addopts = [
    "--strict-markers",
    "--cov=pipeline",
    "--cov-report=term-missing",
    "--cov-report=json:.coverage.json",
]
```

The `--cov=pipeline` flag scopes coverage to the production module only — test files are excluded from measurement. The `:DEST` suffix on `json:.coverage.json` controls the output filename (verified: `--cov-report=json:.coverage.json` writes `.coverage.json` at the project root).

### Pattern 2: Scraper fixture file content
**What:** Raw HTTP response snapshots, structurally identical to production but trimmed to 3-5 rows of data.
**When to use:** Phase 19 ingest unit tests request these as file reads; Phase 18 only creates the files.

**ASX fixture (`asx_response.json`):**
```json
{
  "data": {
    "items": [
      {
        "dateExpiry": "2026-02-25",
        "datePreviousSettlement": "2026-02-25",
        "pricePreviousSettlement": 96.18,
        "volume": 260,
        "xid": "928464846",
        "symbol": "IBG2026"
      },
      {
        "dateExpiry": "2026-03-29",
        "datePreviousSettlement": "2026-02-25",
        "pricePreviousSettlement": 96.135,
        "volume": 5387,
        "xid": "928464847",
        "symbol": "IBH2026"
      }
    ]
  }
}
```
Error variant (`asx_response_empty.json`): `{"data": {"items": []}}`.

**RBA fixture (`rba_cashrate.csv`):**
```
A2 RESERVE BANK OF AUSTRALIA – CHANGES IN MONETARY POLICY AND ADMINISTERED RATES
Title,Change in Cash Rate Target,New Cash Rate Target,...
Description,...
Frequency,...
Type,...
Units,...

Source,...
Publication date,...
Series ID,ARBAMPCCCR,ARBAMPCNCRT,...
23-Jan-1990,-0.50 to -1.00,17.00 to 17.50
04-Feb-2025,-0.25,4.10
03-Feb-2026,-0.25,4.10
```
The `rba_data.py` parser skips rows until it finds `Series ID` — fixture must include that landmark row. Error variant: fixture with metadata headers but no data rows after `Series ID`.

**NAB fixture (`nab_article.html`):**
Minimal HTML with `<p>` tag containing the real phrase pattern: `"Even as activity eased in November capacity utilisation rose further to 83.6%"`. Also include a `<a href="report.pdf">` link for PDF fallback path testing. Error variant: HTML with no capacity utilisation text and no PDF link.

**ABS fixture (`abs_response.csv`):**
ABS SDMX CSV format (the API returns `application/vnd.sdmx.data+csv;labels=both`):
```
DATAFLOW,MEASURE,INDEX,TSEST,REGION,TIME_PERIOD,OBS_VALUE,OBS_STATUS,OBS_COMMENT,...
ABS:CPI(1.0.0),Index Numbers,All groups CPI,Original,Australia,2024-Q1,139.6,,
ABS:CPI(1.0.0),Index Numbers,All groups CPI,Original,Australia,2024-Q2,141.1,,
```
Error variant: header row only, no data rows.

**CoreLogic fixture (`corelogic_article.html`):**
Minimal HTML with a PDF link: `<a href="https://discover.cotality.com/hubfs/Article-Reports/COTALITY%20HVI%20Feb%202026%20FINAL.pdf">Download PDF</a>`. Note: corelogic_scraper.py downloads the PDF directly, not from article HTML — the test fixture is for `get_candidate_urls()` + `download_cotality_pdf()`. The PDF content fixture is handled by mocking `pdfplumber.open()` at the extract_text level (per REQUIREMENTS.md out-of-scope decision: "Real PDF binary fixtures" are out of scope). Error variant: HTML with no PDF link.

### Pattern 3: check_coverage.py enforcement script
**What:** Reads `.coverage.json`, extracts `percent_covered` per pipeline/ module, compares against `--min` threshold, exits non-zero on any failure.
**When to use:** `python scripts/check_coverage.py --min 85`

```python
#!/usr/bin/env python3
"""
Per-module coverage check for pipeline/ modules.

Usage:
    python scripts/check_coverage.py --min 85

Exit codes:
    0  All pipeline/ modules at or above MIN%
    1  One or more modules below MIN%, or .coverage.json not found
"""

import argparse
import json
import sys
from pathlib import Path

COVERAGE_JSON = Path(".coverage.json")
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def colorize(text, color):
    if sys.stdout.isatty():
        return f"{color}{text}{RESET}"
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=float, default=85.0, dest="min_pct")
    args = parser.parse_args()

    if not COVERAGE_JSON.exists():
        print("ERROR: .coverage.json not found. Run pytest first.")
        sys.exit(1)

    data = json.loads(COVERAGE_JSON.read_text())
    files = data.get("files", {})

    # Filter to pipeline/ modules that have executable statements
    pipeline_files = {
        path: info
        for path, info in files.items()
        if path.startswith("pipeline/") and info["summary"]["num_statements"] > 0
    }

    failures = []
    passes = []

    for path, info in sorted(pipeline_files.items()):
        pct = info["summary"]["percent_covered"]
        module = Path(path).name
        if pct < args.min_pct:
            gap = pct - args.min_pct
            failures.append((module, pct, args.min_pct, gap))
        else:
            passes.append((module, pct))

    if failures:
        # Diff table
        print(f"\nCoverage below {args.min_pct:.0f}% threshold:\n")
        print(f"  {'Module':<40} {'Actual':>7}  {'Target':>7}  {'Gap':>7}")
        print(f"  {'-'*40} {'-'*7}  {'-'*7}  {'-'*7}")
        for module, actual, target, gap in failures:
            row = f"  {module:<40} {actual:>6.0f}%  {target:>6.0f}%  {gap:>6.0f}%"
            print(colorize(row, RED))
        print()
        sys.exit(1)
    else:
        # Summary table on success
        print(f"\nAll pipeline/ modules at or above {args.min_pct:.0f}%:\n")
        for module, pct in passes:
            row = f"  {module:<40} {pct:>6.0f}%"
            print(colorize(row, GREEN))
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
```

### Anti-Patterns to Avoid
- **Adding `--cov-fail-under` to addopts:** This enforces total coverage, not per-module. The locked decision calls for per-module enforcement via check_coverage.py. Do not conflate the two.
- **Committing `.coverage` or `.coverage.json`:** Both are ephemeral artifacts. The git status already shows `.coverage` as an untracked file — add both to `.gitignore`.
- **Including `__init__.py` files in failure table:** They have 0 statements and report 100% — including them pollutes the failure diff. Filter on `num_statements > 0`.
- **Using `--cov-report=json` without `:DEST`:** Without `:DEST`, pytest-cov writes `coverage.json` (no dot prefix). The locked decision specifies `.coverage.json`. Always use `--cov-report=json:.coverage.json`.
- **Checking pipeline/ by path prefix in coverage.json:** The coverage.json keys use the relative path from the project root (e.g., `pipeline/ingest/abs_data.py`), not the module name. The `startswith("pipeline/")` filter is correct.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP mock in scraper tests | Custom socket patching | `pytest-mock` MagicMock + `create_session` patch (primary) or `responses` library (transport-layer) | Block network fixture already patches `socket.socket`; scraper mocking happens at the session level, not the socket level |
| Coverage measurement | Custom line counting | pytest-cov / coverage.py | Edge cases with branches, decorators, and conditionals |
| Color detection in scripts | Custom terminal detection | `sys.stdout.isatty()` | POSIX standard; handles pipe, CI, and terminal correctly |

**Key insight:** The `block_network` autouse fixture in conftest.py already blocks socket.socket for all non-live tests. Scraper unit tests in Phase 19 will need to patch `pipeline.ingest.<module>.create_session` — not socket — because the session object is created before any socket call. The `responses` library intercepts at `requests.adapters.HTTPAdapter.send`, bypassing the socket patch entirely, making it useful for tests that can't easily patch create_session.

## Common Pitfalls

### Pitfall 1: Wrong JSON output filename
**What goes wrong:** `--cov-report=json` writes `coverage.json`; the locked decision requires `.coverage.json`.
**Why it happens:** The `:DEST` suffix is not well-documented.
**How to avoid:** Always specify `--cov-report=json:.coverage.json` in addopts.
**Warning signs:** `ls coverage.json` exists but `.coverage.json` does not after test run.

### Pitfall 2: pytest-cov slowing down test collection
**What goes wrong:** Adding `--cov=pipeline` to addopts runs coverage even during `-k` filter runs or `--collect-only`.
**Why it happens:** addopts applies globally; `--no-cov` flag lets users opt out.
**How to avoid:** Document that `pytest --no-cov` bypasses coverage for fast iterative runs. Do not add `--no-cov` to addopts (defeats the purpose).

### Pitfall 3: Fixture files too large
**What goes wrong:** Committing entire real API responses (ASX returns 12+ items with 20+ fields each) bloats the repo and makes fixtures fragile when response schemas change.
**Why it happens:** "Production snapshot" can be misread as "complete snapshot".
**How to avoid:** Trim to 2-3 items; include only fields that `asx_futures_scraper.py` actually reads (`dateExpiry`, `pricePreviousSettlement`). Preserve top-level JSON structure (`data.items` wrapper).

### Pitfall 4: RBA fixture missing the Series ID landmark
**What goes wrong:** `rba_data.py` scans for `Series ID` to find the header row. A fixture that omits the metadata rows will parse incorrectly.
**Why it happens:** The trimmed fixture looks like a normal CSV but the parser depends on the landmark.
**How to avoid:** Include all metadata rows verbatim (rows 1-10 of the real response) and only trim the data rows to 3-5 entries.

### Pitfall 5: check_coverage.py run before pytest
**What goes wrong:** `.coverage.json` not found → script exits 1 with misleading error.
**Why it happens:** Script invoked standalone without prior test run.
**How to avoid:** Add clear error message: "ERROR: .coverage.json not found. Run pytest first." Already covered in code example above.

### Pitfall 6: CoreLogic PDF fixture confusion
**What goes wrong:** Attempting to create a real PDF binary file as a fixture.
**Why it happens:** INFRA-03 says "sample HTML, PDF text, and CSV data" — "PDF text" means the text extracted from a PDF, not a binary PDF.
**How to avoid:** Per REQUIREMENTS.md Out of Scope: "Real PDF binary fixtures — Mock pdfplumber at extract_text() level". The CoreLogic fixture is HTML (the article page linking to the PDF); PDF content is mocked in Phase 19 tests using `mocker.patch("pdfplumber.open")`.

## Code Examples

Verified patterns from official sources and local testing:

### pyproject.toml addopts (verified locally)
```toml
[tool.pytest.ini_options]
minversion = "6.0"
testpaths = ["tests/python"]
pythonpath = ["."]
addopts = [
    "--strict-markers",
    "--cov=pipeline",
    "--cov-report=term-missing",
    "--cov-report=json:.coverage.json",
]
markers = [
    "live: marks tests that require live network access (deselect with '-m \"not live\"')",
]
```

### requirements-dev.txt additions (verified versions)
```
pytest>=9.0.2
pytest-cov>=4.0
pytest-mock>=3.15
responses>=0.26
ruff>=0.15.2
jsonschema>=4.23,<5.0
```

Note: pytest-cov 7.0.0 is already installed (satisfies `>=4.0`). pytest-mock 3.15.1 and responses 0.26.0 are the latest available (confirmed via `pip install --dry-run`).

### coverage.json schema (verified locally)
```python
# Reading per-module coverage from .coverage.json
import json
data = json.loads(Path(".coverage.json").read_text())
for path, info in data["files"].items():
    summary = info["summary"]
    pct = summary["percent_covered"]          # float, e.g. 17.094...
    stmts = summary["num_statements"]          # int; 0 means __init__.py with no code
    missing = summary["missing_lines"]         # int
```

### Verifying pytest-mock is importable
```python
# In any test file:
def test_something(mocker):
    mock_fn = mocker.patch("pipeline.ingest.rba_data.create_session")
    # mocker fixture is provided by pytest-mock automatically
```

### Verifying responses is importable
```python
import responses as responses_lib

@responses_lib.activate
def test_http_interception():
    responses_lib.add(responses_lib.GET, "https://example.com", json={"ok": True})
    # requests.get("https://example.com") will be intercepted
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `.coveragerc` separate file | `[tool.coverage.*]` in pyproject.toml | coverage.py 5.0+ | Single config file; `.coveragerc` is still supported but redundant |
| `--cov-report=html` for visual inspection | `--cov-report=term-missing` for terminal | Always standard | No HTML files to gitignore; terminal output is sufficient |
| pytest-cov `--cov-fail-under` for CI | Custom per-module script | Project choice | Total % enforcement misses low-coverage individual modules |

**Deprecated/outdated:**
- `setup.cfg` for pytest config: Use `pyproject.toml [tool.pytest.ini_options]` instead (project already uses this).
- `pytest-cov` versions below 4.0: Dropped Python 3.7 support; the `json:.coverage.json` `:DEST` syntax works from 4.0+.

## Open Questions

1. **ABS fixture format — which dataflow?**
   - What we know: `abs_data.py` fetches multiple ABS dataflows (CPI, LF, HSI_M, WPI, BA_GCCSA, RPPI) but they all use the same SDMX CSV format with different column values.
   - What's unclear: Should `abs_response.csv` be a generic fixture or CPI-specific?
   - Recommendation: Create one generic `abs_response.csv` using the CPI format (most commonly tested); Phase 19 tests can use it for all ABS module tests since the parser path is identical across dataflows.

2. **CoreLogic fixture — article HTML vs direct PDF URL testing?**
   - What we know: `corelogic_scraper.py` constructs PDF URLs directly via `get_candidate_urls()` and calls `download_cotality_pdf()` — it does NOT extract the PDF URL from article HTML. `get_pdf_link()` is a NAB function, not CoreLogic.
   - What's unclear: What does the CoreLogic "HTML fixture" test? The scraper doesn't parse HTML at all.
   - Recommendation: The CoreLogic fixture should be a minimal valid PDF bytes-like fixture (or skip corelogic HTML fixture entirely). For Phase 19, CoreLogic tests mock `create_session` to return a mock response with `.content = b"%PDF-..."` then mock `pdfplumber.open`. The `corelogic_article.html` and `corelogic_article_no_pdf.html` may be unnecessary unless get_candidate_urls is tested via HTML. Flag this for the planner — the corelogic fixture may be better served as a stub PDF bytes fixture rather than HTML.

## Sources

### Primary (HIGH confidence)
- Local codebase inspection — `pyproject.toml`, `requirements-dev.txt`, `tests/python/conftest.py`, all pipeline/ingest/*.py files
- Local test run: `pytest tests/python/ -m "not live" --cov=pipeline --cov-report=term-missing --cov-report=json:.coverage.json` — confirmed working, `.coverage.json` written at project root
- `pip show pytest-cov` — version 7.0.0 installed
- `pip install pytest-mock responses --dry-run` — versions 3.15.1 and 0.26.0
- Live ASX API response: `asx.api.markitdigital.com` — confirmed field names `dateExpiry`, `pricePreviousSettlement`
- Live RBA CSV: `rba.gov.au/statistics/tables/csv/a2-data.csv` — confirmed `Series ID` landmark row and metadata structure
- Live NAB HTML: `business.nab.com.au/tag/economic-commentary/nab-monthly-business-survey---november-2025` — confirmed `<p>` tag contains capacity utilisation % pattern

### Secondary (MEDIUM confidence)
- pytest-cov documentation — `:DEST` suffix for `--cov-report=json:.coverage.json` confirmed by `pytest --help` output locally

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pytest-cov 7.0.0 already installed and verified working; pytest-mock/responses versions confirmed via pip dry-run
- Architecture: HIGH — pyproject.toml addopts pattern verified locally; coverage.json schema inspected directly; fixture content verified against live API and HTTP responses
- Pitfalls: HIGH — all pitfalls derived from direct code inspection of pipeline modules and live test run observations

**Research date:** 2026-02-25
**Valid until:** 2026-03-27 (stable ecosystem — 30 days)
