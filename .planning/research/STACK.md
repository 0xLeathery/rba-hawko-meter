# Technology Stack

**Project:** RBA Hawk-O-Meter — v3.0 Full Test Coverage
**Researched:** 2026-02-25
**Scope:** NEW capabilities only — HTTP response mocking, PDF/HTML fixture patterns, coverage enforcement. Does NOT re-research what v2.0 already established.
**Confidence:** HIGH (all versions verified against PyPI/official docs)

---

## Context: What v2.0 Already Established (Do NOT Re-research or Change)

| Layer | Technology | Version | Status |
|-------|------------|---------|--------|
| Test runner | pytest | 9.0.2 | Installed, configured in pyproject.toml |
| Coverage plugin | pytest-cov | 7.0.0 | Installed locally, NOT yet in requirements-dev.txt |
| Linting | ruff | 0.15.2 | Installed, configured in pyproject.toml |
| Schema validation | jsonschema | 4.26.0 | Installed |
| Data libraries | pandas, numpy, requests, beautifulsoup4, pdfplumber, lxml | see requirements.txt | Installed |
| Test isolation | socket-level network blocker, DATA_DIR monkeypatch | — | conftest.py autouse fixtures |
| Git hooks | lefthook | — | Pre-push: lint + unit tests |
| Mock stdlib | unittest.mock (MagicMock, patch, call) | Python 3.13 stdlib | Available, no install needed |

**Current coverage baseline (2026-02-25):**

| Module | Coverage | Gap |
|--------|----------|-----|
| pipeline/ingest/abs_data.py | 17% | 83pp to 85% |
| pipeline/ingest/asx_futures_scraper.py | 13% | 72pp to 85% |
| pipeline/ingest/corelogic_scraper.py | 19% | 66pp to 85% |
| pipeline/ingest/nab_scraper.py | 14% | 71pp to 85% |
| pipeline/ingest/rba_data.py | 24% | 61pp to 85% |
| pipeline/main.py | 0% | 85pp to 85% |
| pipeline/normalize/engine.py | 0% | 85pp to 85% |
| pipeline/utils/http_client.py | 42% | 43pp to 85% |
| pipeline/normalize/gauge.py | 81% | 4pp to 85% |
| pipeline/normalize/ratios.py | 68% | 17pp to 85% |

---

## Recommended Stack Additions for v3.0

### 1. pytest-mock — Mocking Convenience Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest-mock** | `>=3.15,<4` | `mocker` fixture for patching | Not installed. Provides `mocker.patch()`, `mocker.MagicMock()` as pytest fixtures that auto-reset after each test — cleaner than `@patch` decorators or `monkeypatch.setattr` chains for complex mock trees. 3.15.1 current (Sep 2025). Python 3.9+ compatible. |

**Why not raw `unittest.mock` + `monkeypatch`?** For tests with 3+ mock targets (e.g., `http_client.create_session`, `session.get`, `pdfplumber.open`, `pipeline.config.DATA_DIR`), decorator stacking with `@patch` becomes hard to read. `mocker.patch()` keeps mocks inline where they are used, and they auto-reset without needing `addCleanup`. For single-target mocks, `monkeypatch.setattr` (already in conftest) is fine and stays.

**Integration:** Works alongside existing `monkeypatch` fixtures — they solve different problems. `mocker` for third-party call interception; `monkeypatch` for attribute/module-level patches that need to survive fixture teardown ordering.

---

### 2. responses — HTTP Response Mocking for requests.Session

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **responses** | `>=0.26,<1` | Intercept `requests.Session.get()` calls | 0.26.0 released 2026-02-19. Intercepts at the transport adapter layer — works transparently with the project's `create_session()` which mounts a custom `HTTPAdapter` with `urllib3.Retry`. Tests do not need to replace `create_session` itself. |

**The core problem it solves:** The existing `block_network` conftest fixture blocks at `socket.socket` level. Scraper tests need to call the actual scraper functions (testing real parsing logic) but return controlled HTTP responses. The approach is:

1. `@responses.activate` intercepts at the `requests` transport layer, before the socket blocker fires.
2. Register mock URLs: `responses.add(responses.GET, url, body=b"...", status=200)`.
3. The scraper's `session.get(url)` returns the mocked response — no socket is opened.
4. The network blocker remains effective for any code that bypasses `responses`.

**Why not `requests-mock`?** `requests-mock` (latest: 1.12.1, March 2024) has equivalent functionality and also intercepts at the adapter layer. Both work. `responses` is chosen because:
- More active maintenance (0.26.0 released Feb 2026 vs requests-mock last updated Mar 2024).
- Cleaner `@responses.activate` decorator pattern integrates well with pytest without a separate fixture parameter.
- Native pytest fixture available via `responses` context manager.

**Why not `unittest.mock.patch('requests.Session.get')`?** Patching at the method level requires knowing exactly where the session is created and used. The project's `create_session()` is called inside each scraper function — patching at the right import path is fragile across refactors. `responses` intercepts at the network layer regardless of where the session object lives.

**Integration with socket blocker:** The `block_network` fixture in conftest.py patches `socket.socket`. The `responses` library intercepts at the `HTTPAdapter.send()` level, before any socket is created. No conflict. Both can be active simultaneously — `responses` handles registered URLs; the socket blocker catches anything that falls through unregistered.

---

### 3. pytest-cov in requirements-dev.txt + pyproject.toml addopts

pytest-cov 7.0.0 is already installed locally. It is NOT in requirements-dev.txt and is NOT wired into pyproject.toml `addopts`. This means coverage is not measured on `npm run test:fast` or the pre-push hook.

**Change needed:** Add to `requirements-dev.txt`:

```
pytest-cov>=7.0,<8
```

**Change needed:** Add to `pyproject.toml` `[tool.pytest.ini_options]`:

```toml
addopts = ["--strict-markers", "--cov=pipeline", "--cov-report=term-missing"]
```

This runs coverage on every `pytest` invocation (including the pre-push hook). The `--cov-report=term-missing` output shows exactly which lines are uncovered — essential during active test development.

**Do NOT add `--cov-fail-under` to addopts.** Coverage enforcement belongs in a separate script (see section 4 below). Wiring it into `addopts` means every test run fails until 85% is achieved globally — which penalizes iterative development of tests for individual modules.

---

### 4. Per-Module Coverage Enforcement Script

`coverage.py`'s `--cov-fail-under` is a global threshold only — it cannot enforce per-module minimums. This is a documented limitation (GitHub issue #444 in pytest-dev/pytest-cov). Coverage.py does not support per-file `fail_under` in pyproject.toml configuration.

**Solution:** A small Python script (`scripts/check_coverage.py`) that:

1. Reads `--cov-report=json` output (`.coverage.json`)
2. Iterates per-file coverage percentages
3. Asserts each `pipeline/` module meets 85%
4. Exits non-zero on failure with a clear diff table

This is the standard pattern used in the Python ecosystem when per-file thresholds are needed. It is NOT a third-party library — it is a ~30-line project script.

**Wire into `pyproject.toml` addopts:**

```toml
addopts = [
    "--strict-markers",
    "--cov=pipeline",
    "--cov-report=term-missing",
    "--cov-report=json:.coverage.json",
]
```

**Wire into Lefthook pre-push** after pytest:

```yaml
commands:
  unit-tests:
    run: python -m pytest tests/python/ -m "not live"
  coverage-check:
    run: python scripts/check_coverage.py --min 85
```

**Why a script vs. a plugin?** The only third-party plugin for per-file thresholds is `pytest-cov-threshold` (unmaintained, last commit 2020). Writing 30 lines of JSON-parsing logic is safer and requires no additional dependency.

---

### 5. PDF and HTML Test Fixtures

No new library needed. The approach for testing scraper parsing functions:

**PDF fixtures (corelogic_scraper, nab_scraper):** Create minimal real PDFs using `pdfplumber` + `reportlab` — OR use `io.BytesIO` with pre-captured real PDF bytes stored as fixture files.

**Recommended approach:** Store binary fixture files in `tests/python/fixtures/`:
- `cotality_hvi_sample.pdf` — 1-page PDF with "Australia 0.8% 2.4% 9.4%" pattern
- `nab_survey_sample.pdf` — 1-page PDF with "Capacity utilisation 82.1%"

These are created once by running the scraper against live sources and saving the bytes. They are small (<100KB), committed to git, and never change unless the source format changes.

**HTML fixtures:** Store as `.html` files in `tests/python/fixtures/`:
- `nab_tag_archive.html` — mock tag archive page with a `monthly-business-survey` link
- `nab_article.html` — mock article with capacity utilisation inline text
- `nab_article_no_capacity.html` — article without the pattern (tests PDF fallback path)

These are used by passing `Path("tests/python/fixtures/nab_article.html").read_bytes()` directly to parsing functions — no HTTP call needed for the parsing layer.

**Why not `reportlab` for generating PDFs?** reportlab is a ~4MB dependency for generating PDFs programmatically. Saving real PDF bytes as binary fixtures accomplishes the same goal with zero new dependencies.

---

## Complete Installation Delta

### requirements-dev.txt additions

```
# v3.0 additions — full test coverage milestone
pytest-mock>=3.15,<4
responses>=0.26,<1
pytest-cov>=7.0,<8
```

### No package.json changes needed.

### pyproject.toml changes

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
    "unit: marks fast unit tests with no I/O (default tier)",
]
```

### New file: scripts/check_coverage.py

A ~30-line script parsing `.coverage.json` and asserting >=85% per `pipeline/` module. No third-party dependency.

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **vcrpy / betamax** | Record/replay HTTP cassettes — overkill for predictable API responses. Cassettes go stale when endpoints change. | `responses` with inline fixture data |
| **httpretty** | Older HTTP mocking library, patches at socket level. Conflicts with the existing socket blocker in conftest.py. | `responses` (transport-layer interception) |
| **pytest-httpserver** | Runs a real local HTTP server — requires port management, slower, more complex. | `responses` (no server, no ports) |
| **reportlab** | PDF generation library — heavy (4MB). Only needed if generating test PDFs programmatically. | Binary fixture files in tests/python/fixtures/ |
| **faker / factory_boy** | Data generation libraries for ORM-backed apps. Pipeline operates on DataFrames from CSVs, not model instances. | Inline DataFrames in test functions |
| **pytest-cov-threshold** | Third-party per-file threshold plugin, unmaintained since 2020. | Custom `scripts/check_coverage.py` parsing JSON report |
| **tox** | Multi-environment testing. One Python version target (3.13 local, 3.11 GHA). | Single pytest invocation |
| **pytest-xdist** | Parallel test execution. Test suite will be ~200-300 tests max — parallelism adds complexity with no payoff at this scale. | Single-process pytest |
| **mypy / pyright** | Type checking. Explicitly out of scope per PROJECT.md "Out of Scope" table. | ruff catches the relevant issues |
| **requests-mock** | Functionally equivalent to `responses` but last updated March 2024 vs `responses` Feb 2026. | `responses` |
| **pytest-recording (VCR)** | Wraps vcrpy with pytest — same cassette staleness problem. | `responses` with explicit mock data |

---

## Alternatives Considered

| Category | Recommended | Alternative | When Alternative Is Better |
|----------|-------------|-------------|---------------------------|
| HTTP mocking | `responses` 0.26.0 | `requests-mock` 1.12.1 | If team has existing requests-mock familiarity — functionally equivalent |
| HTTP mocking | `responses` 0.26.0 | `unittest.mock.patch('requests.Session.get')` | For tests that only call a single HTTP endpoint once — simpler to inline |
| Mock fixtures | `pytest-mock` mocker | `unittest.mock.patch` decorators | For tests with a single mock target — `@patch` is fine and has no extra dep |
| PDF fixtures | Binary fixture files | `reportlab` generated PDFs | If PDF structure needs to change frequently between tests — then programmatic generation wins |
| Per-module enforcement | Custom script | `--cov-fail-under` global | For projects that only need a global floor — one liner in pyproject.toml |

---

## Integration with Existing pyproject.toml / pytest Config

**Existing conftest.py is compatible.** The `block_network` fixture (socket-level) and `responses` library (transport-level) operate at different layers and co-exist without conflict. Tests using `@responses.activate` will have their HTTP calls intercepted before the socket blocker fires.

**Existing `isolate_data_dir` fixture is unaffected.** Scraper tests still need `pipeline.config.DATA_DIR` isolated — this remains an autouse fixture. Scraper tests using `responses` will additionally patch `pipeline.config.DATA_DIR` to a tmp_path (already handled automatically).

**Existing `--strict-markers` stays.** The new `unit` marker needs to be declared in `pyproject.toml` markers list if used.

**Coverage in the pre-push hook:** Adding `--cov` to `addopts` means the pre-push hook (which runs `pytest -m "not live"`) now produces coverage output. This is desirable — it surfaces gaps during active development. The lefthook 30s timeout is sufficient; the current 118-test suite runs in ~0.4s; 200-300 tests with coverage should complete in under 5s.

---

## Version Compatibility

| Package | Version | Python Compat | Conflicts |
|---------|---------|---------------|-----------|
| pytest-mock | 3.15.1 | >=3.9 | None with pytest 9.0.2 |
| responses | 0.26.0 | >=3.8 | None with requests 2.x |
| pytest-cov | 7.0.0 | >=3.8 | Requires coverage >=7.10.6 (installed: 7.13.4 — satisfied) |
| coverage | 7.13.4 | >=3.9 | Already installed, satisfies pytest-cov requirement |

**Python 3.13 local / 3.11 GitHub Actions:** All additions are compatible with both. `responses` 0.26.0 requires Python >=3.8. `pytest-mock` 3.15.1 requires Python >=3.9. Both satisfied by 3.11+.

---

## Sources

- **pytest-mock 3.15.1** — https://pypi.org/project/pytest-mock/ — version verified Feb 2026 (HIGH confidence)
- **responses 0.26.0** — https://pypi.org/project/responses/ — released 2026-02-19, verified (HIGH confidence)
- **responses + Session/HTTPAdapter** — https://github.com/getsentry/responses — intercepts at HTTPAdapter.send(), compatible with urllib3.Retry (MEDIUM confidence; docs confirm Session support for prepared requests)
- **pytest-cov 7.0.0** — https://pypi.org/project/pytest-cov/ — version verified, already installed locally (HIGH confidence)
- **coverage.py per-file thresholds** — https://coverage.readthedocs.io/en/latest/config.html — confirmed: no per-file fail_under, only global (HIGH confidence)
- **pytest-cov per-file threshold limitation** — https://github.com/pytest-dev/pytest-cov/issues/444 — open issue, confirmed as unimplemented feature (HIGH confidence)
- **requests-mock** — https://pypi.org/project/requests-mock/ — v1.12.1, last updated March 2024 — considered and deprioritized vs responses (HIGH confidence)
- **coverage.py JSON report format** — https://coverage.readthedocs.io/en/latest/config.html — --cov-report=json supported (HIGH confidence)
- **pytest-cov configuration** — https://pytest-cov.readthedocs.io/en/latest/config.html — addopts integration verified (HIGH confidence)

---

*Stack research for: RBA Hawk-O-Meter v3.0 Full Test Coverage milestone*
*Researched: 2026-02-25*
