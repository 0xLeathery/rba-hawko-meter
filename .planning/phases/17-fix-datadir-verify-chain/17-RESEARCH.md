# Phase 17: Fix DATA_DIR Wiring & npm verify Chain - Research

**Researched:** 2026-02-25
**Domain:** Python import-time binding fix + npm script wiring
**Confidence:** HIGH

## Summary

Phase 17 closes two integration bugs discovered during the v2.0 milestone audit: (1) all 5 ingestors bind `DATA_DIR` at import time via `from pipeline.config import DATA_DIR`, making the `isolate_data_dir` monkeypatch fixture invisible to them, and (2) `scripts/verify_summary.py` is orphaned from the `npm run verify` chain.

The fix is straightforward: change each ingestor (and any normalize module with the same pattern) to access `pipeline.config.DATA_DIR` at call time instead of binding it as a local name at import time. The `npm run verify` script needs `verify_summary.py` appended as a final step.

**Primary recommendation:** Replace `from pipeline.config import DATA_DIR` with `import pipeline.config` (or use `pipeline.config.DATA_DIR` inline) in all 7 affected modules, then add `python scripts/verify_summary.py` to the npm verify chain.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Tiers run sequentially: fast -> live -> Playwright (cheapest first)
- Fail-fast: stop at first failing tier, don't run subsequent tiers
- `verify_summary.py` runs after all three tiers pass as a final aggregation step
- `npm run verify` is the single entry point -- pre-push hooks call this one command
- Individual tier scripts available: `verify:fast`, `verify:live`, `verify:playwright` for dev convenience
- `npm run verify` always runs all three tiers -- no `--quick` mode, use individual scripts instead
- Summary report: simple pass/fail table (tier name, status, duration)
- Colored terminal output (green pass / red fail) with auto-detect for CI/no-TTY (strip ANSI automatically)
- Tests passing is sufficient proof that DATA_DIR wiring is correct -- no separate lint-style wiring check
- `verify_summary.py` outputs to stdout only -- no file artifacts
- Silent override in tests -- no logging about which DATA_DIR is active unless something fails
- Ingestors log DATA_DIR once at startup -- useful for debugging, not noisy
- Environment variable override supported: `DATA_DIR=/custom/path` takes precedence over config
- Clean break: fix all 5 ingestors at once, no backward-compatibility shim for old import-time pattern
- `verify_summary.py` crash = verify chain failure (not just a warning)
- Exit code: 0 = all passed, 1 = any failure (simple, standard for CI)
- Tier output passthrough -- let pytest/vitest format their own failure output
- Pre-push hook blocks push on verify failure
- Bypass via git's built-in `--no-verify` flag -- no custom escape hatch

### Claude's Discretion
- Late-binding implementation approach (function call, property access, or config accessor pattern)
- `isolate_data_dir` fixture implementation details
- Exact summary table formatting
- Test runner invocation details within npm scripts

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LIVE-01 | Developer can verify ABS, RBA, ASX API ingestion works with real endpoints | DATA_DIR late-binding fix enables isolate_data_dir to redirect ingestor writes to tmp_path; live tests can assert files land in correct directory |
| LIVE-02 | Developer can verify Cotality and NAB scrapers work against live pages | Same DATA_DIR fix applies to corelogic_scraper.py and nab_scraper.py |
| LIVE-03 | Full pipeline run produces valid status.json with all indicators | verify_summary.py wired into npm verify chain validates status.json after pipeline run |
| HOOK-04 | Developer can run full verification manually via `npm run verify` | verify chain updated: fast + live + Playwright + verify_summary.py, fail-fast sequential |
</phase_requirements>

## Standard Stack

### Core
No new libraries needed. This phase modifies existing Python modules and npm scripts only.

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python | 3.x (existing) | Import pattern change | Module attribute access is idiomatic Python |
| npm scripts | package.json | Verify chain wiring | Already used for all test/lint orchestration |
| pytest | existing | Test validation | Already configured in pyproject.toml |

### Supporting
None needed. All infrastructure is in place from Phases 11-15.

## Architecture Patterns

### Pattern 1: Late-Bound Module Attribute Access

**What:** Replace `from pipeline.config import DATA_DIR` with accessing `pipeline.config.DATA_DIR` at the point of use inside functions.

**When to use:** Any module that needs `DATA_DIR` to be patchable by monkeypatch in tests.

**Current (broken) pattern:**
```python
# At module level -- binds DATA_DIR as local name at import time
from pipeline.config import DATA_DIR

def save_data():
    output_path = DATA_DIR / "output.csv"  # Uses stale local binding
```

**Fixed pattern:**
```python
import pipeline.config

def save_data():
    output_path = pipeline.config.DATA_DIR / "output.csv"  # Reads module attribute at call time
```

**Why this works:** `monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)` replaces the module attribute. Code that reads `pipeline.config.DATA_DIR` at call time sees the patched value. Code that bound `DATA_DIR` as a local name at import time does not.

### Pattern 2: Environment Variable Override

**What:** Support `DATA_DIR=/custom/path` environment variable taking precedence over the default.

**Implementation in pipeline/config.py:**
```python
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
```

This is a simple addition to config.py. The monkeypatch still overrides it in tests (setattr replaces regardless of how the initial value was computed).

### Pattern 3: Startup Logging

**What:** Each ingestor logs `DATA_DIR` once at startup for debugging.

**Implementation:** Add a single log line at the start of each ingestor's main function:
```python
import logging
logger = logging.getLogger(__name__)

def fetch_and_save():
    logger.info("DATA_DIR: %s", pipeline.config.DATA_DIR)
    # ... rest of function
```

### Anti-Patterns to Avoid
- **Importing DATA_DIR as a local name:** `from pipeline.config import DATA_DIR` creates a snapshot that cannot be monkeypatched
- **Module-level Path computations using DATA_DIR:** e.g. `OUTPUT_PATH = DATA_DIR / "file.csv"` at module level -- this freezes the path at import time
- **Per-module monkeypatching in tests:** Adding separate monkeypatch calls for each ingestor's local DATA_DIR binding is fragile and scales poorly

## Affected Files Analysis

### Ingestors (5 files -- import-time DATA_DIR binding)

| File | Line | Current Import | DATA_DIR Usages |
|------|------|---------------|-----------------|
| `pipeline/ingest/abs_data.py` | 14 | `from pipeline.config import ... DATA_DIR` | lines 296, 305 |
| `pipeline/ingest/rba_data.py` | 10 | `from pipeline.config import DATA_DIR, ...` | line 91 |
| `pipeline/ingest/asx_futures_scraper.py` | 25 | `from pipeline.config import ... DATA_DIR` | lines 42, 278, 330 |
| `pipeline/ingest/corelogic_scraper.py` | 18 | `from pipeline.config import ... DATA_DIR` | lines 167, 240 |
| `pipeline/ingest/nab_scraper.py` | 20 | `from pipeline.config import ... DATA_DIR` | lines 190, 270, 361, 370 |

### Normalize modules (2 files -- also affected)

| File | Line | Current Import | DATA_DIR Usages |
|------|------|---------------|-----------------|
| `pipeline/normalize/ratios.py` | 13 | `from pipeline.config import DATA_DIR` | line 125 |
| `pipeline/normalize/engine.py` | 16 | `from pipeline.config import DATA_DIR, ...` | lines 152, 228 (line 188 already late-bound) |

### Config module (1 file -- needs env var support)

| File | Change |
|------|--------|
| `pipeline/config.py` | Add `os.environ.get("DATA_DIR", "data")` for env override |

### npm scripts (1 file)

| File | Change |
|------|--------|
| `package.json` | Add `verify_summary.py` to verify chain; add individual tier scripts |

**Total: 9 files modified**

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config accessor pattern | Custom getter/setter for DATA_DIR | Direct `pipeline.config.DATA_DIR` attribute access | Python module attributes are already the accessor pattern; adding a function adds complexity with no benefit |
| Colored terminal output | Custom ANSI formatting | verify_summary.py already handles formatting | Script exists and works; just needs wiring into npm chain |
| Test isolation | Per-module monkeypatch | Single `isolate_data_dir` autouse fixture | Already exists in conftest.py; the fix is making production code responsive to it |

## Common Pitfalls

### Pitfall 1: Missing a DATA_DIR Usage
**What goes wrong:** Fix the import but miss a `DATA_DIR` reference deeper in the file.
**Why it happens:** Some files use DATA_DIR in multiple functions.
**How to avoid:** `grep -n "DATA_DIR" pipeline/ingest/*.py pipeline/normalize/*.py` after changes; ensure zero `from pipeline.config import.*DATA_DIR` remains.
**Warning signs:** Tests pass locally but fail in specific ingestor paths.

### Pitfall 2: SOURCE_METADATA Import-Time Binding
**What goes wrong:** `config.py` defines `SOURCE_METADATA` with paths like `DATA_DIR / "abs_cpi.csv"` at module level. These are computed at import time and NOT affected by monkeypatch.
**Why it matters:** If any code uses `SOURCE_METADATA[key]["file_path"]`, it will still point to the original `data/` directory.
**How to avoid:** The conftest.py already documents this (lines 42-45). No production code currently uses SOURCE_METADATA for file I/O in a way that affects tests. Leave as-is; document in PLAN.md.

### Pitfall 3: Forgetting normalize modules
**What goes wrong:** Only fixing the 5 ingestors but not `ratios.py` and `engine.py`.
**Why it happens:** The roadmap says "5 ingestors" but the audit shows 7 files total.
**How to avoid:** Fix all 7 files. The success criteria says "All 5 ingestors" but the underlying goal is that `npm run verify` passes -- which requires normalize modules to also be fixed.

### Pitfall 4: verify_summary.py Running Before Pipeline
**What goes wrong:** verify_summary.py reads `public/data/status.json` which requires a fresh pipeline run.
**Why it matters:** The current verify chain runs tests but does not run the pipeline. verify_summary.py should only run after live tests confirm the pipeline works.
**How to avoid:** Per user decision: verify_summary.py runs AFTER all three tiers pass. The live tests themselves run the pipeline (via `pipeline/main.py`). So verify_summary.py at the end validates the status.json that was just produced.

### Pitfall 5: Individual Tier Scripts Not Added
**What goes wrong:** User decision says individual tier scripts should be available (`verify:fast`, `verify:live`, `verify:playwright`).
**Why it matters:** Dev convenience -- run a single tier without the full chain.
**How to avoid:** Add all three individual scripts to package.json alongside the unified `verify` script.

## Code Examples

### Example 1: Ingestor Import Fix (abs_data.py pattern)

**Before:**
```python
from pipeline.config import (
    ABS_API_BASE,
    ABS_CONFIG,
    DATA_DIR,
    DEFAULT_TIMEOUT,
    TIMEOUT_OVERRIDES,
)

def fetch_and_save_all():
    output_path = DATA_DIR / output_file
```

**After:**
```python
import pipeline.config
from pipeline.config import (
    ABS_API_BASE,
    ABS_CONFIG,
    DEFAULT_TIMEOUT,
    TIMEOUT_OVERRIDES,
)

def fetch_and_save_all():
    output_path = pipeline.config.DATA_DIR / output_file
```

### Example 2: npm verify Chain

**Before:**
```json
"verify": "npm run test:fast && python -m pytest tests/python/ -m live -v && npx playwright test"
```

**After:**
```json
"verify": "npm run verify:fast && npm run verify:live && npm run verify:playwright && python scripts/verify_summary.py",
"verify:fast": "npm run lint && pytest tests/python/ -m \"not live\"",
"verify:live": "python -m pytest tests/python/ -m live -v",
"verify:playwright": "npx playwright test"
```

### Example 3: config.py Environment Variable Override

**Before:**
```python
DATA_DIR = Path("data")
```

**After:**
```python
import os
DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
```

## Open Questions

1. **Should normalize modules also get DATA_DIR startup logging?**
   - What we know: User decided ingestors log DATA_DIR once at startup
   - What's unclear: Whether normalize modules (ratios.py, engine.py) should also log
   - Recommendation: Skip logging for normalize modules -- they're internal to the pipeline, not entry points. Ingestor logging covers the debugging use case.

2. **SOURCE_METADATA paths in config.py**
   - What we know: These are computed at import time and won't be affected by monkeypatch
   - What's unclear: Whether any test or production path actually uses them for file I/O
   - Recommendation: Leave as-is. Document the known limitation. No current test failure traced to SOURCE_METADATA paths.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: All 7 affected files read and verified
- v2.0 Milestone Audit: `.planning/v2.0-MILESTONE-AUDIT.md` -- documented root cause and affected files
- conftest.py lines 38-48: Documents the import pattern requirement and SOURCE_METADATA limitation
- package.json: Current verify script definition

### Secondary (MEDIUM confidence)
- Python documentation: Module attribute access vs local name binding is well-documented standard behavior

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, pure refactoring
- Architecture: HIGH - Python module import semantics are well-understood
- Pitfalls: HIGH - All pitfalls identified from codebase inspection, not speculation

**Research date:** 2026-02-25
**Valid until:** Indefinite (language semantics, not library versions)
