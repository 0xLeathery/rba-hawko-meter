# Phase 16: Verify Linting Baseline - Research

**Researched:** 2026-02-25
**Domain:** Verification / linting infrastructure (ruff + ESLint v10)
**Confidence:** HIGH

## Summary

Phase 16 is a gap-closure verification phase. Phase 13 (Linting Baseline) implemented ruff Python linting and ESLint v10 JavaScript linting across the project, but it was never verified by `gsd-verifier` — the v2.0 milestone audit found the VERIFICATION.md missing. The linting infrastructure is already in place and actively running in the pre-push hook (Phase 15).

The verification work is primarily: run the three lint commands, observe they exit 0, inspect the configuration artifacts, and write a VERIFICATION.md in the standard format used by all other completed phases (see Phase 12 and Phase 15 for the template). This is not an implementation phase — there is nothing new to build.

Live verification confirms the linting baseline is clean today: `npm run lint:py` (ruff exits 0), `npm run lint:js` (ESLint exits 0), `npm run lint` (both in sequence, exits 0). The VERIFICATION.md must document this state with evidence, map all four LINT requirements, and reference the key artifacts.

**Primary recommendation:** Run all three lint commands, capture output, inspect artifact contents (pyproject.toml ruff config, eslint.config.js, package.json scripts), and write 13-VERIFICATION.md in the format established by 12-VERIFICATION.md and 15-VERIFICATION.md.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LINT-01 | Python code passes ruff checks (E/F/W/B/I/UP rules) | `npm run lint:py` executes `ruff check pipeline/ tests/` — verified clean today (0 violations); ruff config in pyproject.toml [tool.ruff] |
| LINT-02 | Existing Python violations cleaned up in baseline commit | 145 violations fixed in commit `66c3c02` (46 auto-fix, 1 B904, 87 E501 manual wraps) — documented in 13-01-SUMMARY.md; no noqa suppressions present |
| LINT-03 | JavaScript code passes ESLint v10 checks (IIFE sourceType, browser globals) | `npm run lint:js` executes `npx eslint public/js/` — verified clean today (0 violations); flat config in eslint.config.js with sourceType: 'script' |
| LINT-04 | Linting runnable via npm scripts (`lint:py`, `lint:js`, `lint`) | All three scripts defined in package.json; `lint` = `npm run lint:py && npm run lint:js` |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | (via .venv, target py313) | Python linting (E/F/W/B/I/UP rule sets) | Already installed, configured in pyproject.toml; project baseline |
| eslint | ^10.0.2 | JavaScript linting | Already installed; flat config in eslint.config.js |
| @eslint/js | ^10.0.1 | ESLint recommended rule bundle | Required separately in ESLint v10 (not bundled) |
| globals | ^17.3.0 | Browser/node global definitions for ESLint | Provides `globals.browser` for public/js/ files |

### No new installations required

All tooling is already installed. This phase only verifies existing infrastructure — no `npm install` or `pip install` actions needed.

## Architecture Patterns

### Verification Phase Pattern

Phase 16 follows the same pattern as all other completed v2.0 verification phases. The output is a single `13-VERIFICATION.md` file in `.planning/phases/13-linting-baseline/`. It is NOT named after Phase 16 — the convention is that a verification phase writes its VERIFICATION.md into the phase directory it is verifying.

Reference: `.planning/phases/12-python-unit-tests/12-VERIFICATION.md` and `.planning/phases/15-pre-push-hook/15-VERIFICATION.md` for the exact document structure.

### VERIFICATION.md Structure (from codebase examples)

```
---
phase: 13-linting-baseline
verified: [ISO timestamp]
status: passed
score: 4/4 requirements verified
re_verification: true    ← NOTE: this IS a re-verification (gap closure)
---

# Phase 13: Linting Baseline Verification Report

**Phase Goal:** [from ROADMAP.md]
**Verified:** [ISO timestamp]
**Status:** PASSED / FAILED
**Re-verification:** Yes — gap closure from v2.0 audit

## Goal Achievement

### Observable Truths
| # | Truth | Status | Evidence |
...

### Required Artifacts
| Artifact | Expected | Status | Details |
...

### Key Link Verification
| From | To | Via | Status | Details |
...

### Requirements Coverage
| Requirement | Source Plan | Description | Status | Evidence |
...

### Anti-Patterns Found
...

### Human Verification Required
...

### Summary
...

_Verified: [timestamp]_
_Verifier: Claude (gsd-verifier)_
```

### Key artifact locations

All artifacts already exist — verification reads them, it does not create them:

```
pyproject.toml                    # [tool.ruff] config: select E/F/W/B/I/UP, line-length 88
eslint.config.js                  # ESLint flat config: sourceType script, IIFE globals, max-len 88
package.json                      # scripts: lint:py, lint:js, lint
.planning/phases/13-linting-baseline/
├── 13-01-PLAN.md                 # Ruff cleanup plan
├── 13-01-SUMMARY.md              # Evidence: 145 violations fixed, commit 66c3c02
├── 13-02-PLAN.md                 # ESLint setup plan
└── 13-02-SUMMARY.md              # Evidence: 60+ max-len fixes, commit cb40ef4
```

## Known Facts for the Verification

### Lint commands and expected output

| Command | npm script | Underlying command | Expected output |
|---------|-----------|-------------------|-----------------|
| `npm run lint:py` | `ruff check pipeline/ tests/` | ruff | "All checks passed!" + exit 0 |
| `npm run lint:js` | `npx eslint public/js/` | ESLint | (no output) + exit 0 |
| `npm run lint` | `npm run lint:py && npm run lint:js` | both | both pass + exit 0 |

### Ruff configuration (pyproject.toml)

```toml
[tool.ruff]
target-version = "py313"
line-length = 88
exclude = [".git", ".venv", "__pycache__", "node_modules", ".pytest_cache"]

[tool.ruff.lint]
select = ["E", "F", "W", "B", "I", "UP"]
ignore = []
fixable = ["ALL"]
```

### ESLint configuration (eslint.config.js)

```javascript
// CommonJS format (non-module project)
const js = require("@eslint/js");
const { defineConfig } = require("eslint/config");
const globals = require("globals");

module.exports = defineConfig([{
  files: ["public/js/**/*.js"],
  plugins: { js },
  extends: ["js/recommended"],
  languageOptions: {
    sourceType: "script",   // IIFE modules, not ES modules
    globals: {
      ...globals.browser,
      Plotly: "readonly",
      Decimal: "readonly",
      GaugesModule: "writable",    // IIFE module globals
      ChartModule: "writable",
      DataModule: "writable",
      CountdownModule: "writable",
      CalculatorModule: "writable",
      InterpretationsModule: "writable",
    },
  },
  rules: {
    "max-len": ["error", { code: 88 }],
    "no-redeclare": ["error", { builtinGlobals: false }],
    "no-unused-vars": ["error", {
      varsIgnorePattern: "^(GaugesModule|ChartModule|DataModule|CountdownModule|CalculatorModule|InterpretationsModule)$",
      caughtErrorsIgnorePattern: "^_",
      argsIgnorePattern: "^_",
    }],
  },
}]);
```

### Key decisions recorded in STATE.md (v2.0 decisions Phase 13)

- `sourceType: 'script'` — IIFE module pattern, not ES modules
- `@eslint/js` installed separately — not bundled with ESLint v10 despite common assumption
- `builtinGlobals: false` for `no-redeclare` — IIFE pattern re-declares global var names across files
- `varsIgnorePattern` for module names — prevents no-unused-vars false positives on `var ModuleName = (function(){...})()`
- `caughtErrorsIgnorePattern: "^_"` — catch params prefixed with `_e`
- `max-len 88` — matches Python ruff convention for cross-language consistency
- No noqa suppressions in Python, no eslint-disable in JS — all violations fixed at source

### Baseline cleanup evidence (from SUMMARY files)

**Python (13-01-SUMMARY.md, commit 66c3c02):**
- 46 auto-fixed (unused imports, import sorting, UP007 type annotations)
- 1 B904 manual fix (from e clause in abs_data.py)
- 87 E501 manual line wraps across all pipeline files
- All 119 tests pass after cleanup
- 20 files modified: all pipeline/ files + 7 test files

**JavaScript (13-02-SUMMARY.md, commit cb40ef4):**
- 60+ max-len violations fixed across 8 JS files
- no-unused-vars violations fixed (catch params renamed to `_e`, unused vars removed)
- 11 files modified: eslint.config.js (created) + package.json + 8 public/js/ files
- One deviation from plan: `@eslint/js` not bundled — required separate `npm install --save-dev @eslint/js`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Verifying exit codes | Custom bash scripts to check lint output | Run commands directly and observe exit code | The npm scripts already do this correctly |
| Re-implementing lint checks | Inspecting source files manually | Run `npm run lint` and trust the tools | Tools are already configured and verified against actual source |

**Key insight:** This is a verification phase — run the commands, observe the output, write the document. No new code, no new config.

## Common Pitfalls

### Pitfall 1: Writing VERIFICATION.md in wrong directory

**What goes wrong:** Naming the file `16-VERIFICATION.md` and placing it in `.planning/phases/16-verify-linting-baseline/`
**Why it happens:** Following phase number convention literally
**How to avoid:** The convention is phase-named: verification output goes in the VERIFIED PHASE's directory as `13-VERIFICATION.md` in `.planning/phases/13-linting-baseline/`
**Evidence:** 12-VERIFICATION.md lives in `12-python-unit-tests/`, 15-VERIFICATION.md in `15-pre-push-hook/`

### Pitfall 2: Marking re_verification incorrectly

**What goes wrong:** Setting `re_verification: false` when Phase 13 was previously implemented but never verified
**Why it happens:** Treating it as a fresh verification
**How to avoid:** Set `re_verification: true` — Phase 13 was completed (plans + summaries exist) but the VERIFICATION.md was missing per the audit. This is gap-closure re-verification.

### Pitfall 3: Not capturing actual command output

**What goes wrong:** VERIFICATION.md states "exit 0" but provides no evidence string
**Why it happens:** Planner writes verification doc without running the commands
**How to avoid:** Run all three lint commands and capture exact output strings in the Observable Truths evidence column

### Pitfall 4: Missing the "introduce violation" test

**What goes wrong:** Verifying only that clean code passes, not that a violation is caught
**Why it happens:** Phase 13 success criteria #4 requires confirming that introducing an unused import causes lint:py to fail with a violation message
**How to avoid:** The verification should either (a) perform this test and document the result, or (b) note it as human-verifiable since the pre-push hook already confirmed rejection behavior in Phase 15 verification

### Pitfall 5: Checking wrong pipeline scope

**What goes wrong:** Running `ruff check .` instead of `ruff check pipeline/ tests/`
**Why it happens:** Wanting broader coverage
**How to avoid:** The npm script scopes to `pipeline/ tests/` — verify that scope only, consistent with LINT-01

## Code Examples

### Running the verification commands

```bash
# LINT-01 + LINT-02: Python ruff check
npm run lint:py
# Expected: "All checks passed!" exit 0

# LINT-03: ESLint JS check
npm run lint:js
# Expected: no output, exit 0

# LINT-04: Combined lint
npm run lint
# Expected: both linters run in sequence, both exit 0

# Confirm scripts are defined as expected
cat package.json | python3 -c "import sys,json; d=json.load(sys.stdin); [print(k+': '+v) for k,v in d['scripts'].items() if 'lint' in k]"
```

### Verifying ruff config scope

```bash
# Confirm ruff is scoped to pipeline/ and tests/
grep -n "lint:py" package.json
# Expected: "lint:py": "ruff check pipeline/ tests/"

# Show ruff config from pyproject.toml
python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['tool']['ruff'])"
```

### Verifying ESLint config

```bash
# Confirm ESLint flat config exists and targets correct files
cat eslint.config.js | head -5
# Expected: const js = require("@eslint/js"); ...

# Confirm files glob targets public/js/**/*.js
grep "files" eslint.config.js
```

### Confirming no inline suppressions

```bash
# Python: no noqa suppressions
grep -r "noqa" pipeline/ tests/ || echo "No noqa suppressions found"

# JavaScript: no eslint-disable inline comments
grep -r "eslint-disable" public/js/ || echo "No eslint-disable found"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `.eslintrc` JSON config | `eslint.config.js` flat config | ESLint v9+ | `.eslintrc` not supported in ESLint v10; must use flat config |
| `@eslint/js` bundled with ESLint | Must install `@eslint/js` separately | ESLint v10 | Explicit devDependency required |

## Open Questions

1. **Success Criteria #4: Introduce violation test**
   - What we know: Phase 15 verification marked Truth #1 (push rejection on lint violation) as UNCERTAIN pending human verification. Phase 16 success criteria also requires "introducing an unused import causes lint:py to fail."
   - What's unclear: Should Phase 16 verification perform this live test, or accept Phase 15's wiring evidence?
   - Recommendation: Perform the test in Phase 16 verification (it's simpler than a full git push test — just run `ruff check` after adding an unused import to a temp file, or temporarily add one and restore it). Document the result in the VERIFICATION.md.

2. **Test count may have changed**
   - What we know: Phase 13 summaries reference "119 tests pass" but later phases (12, 14, 15) show 118 tests.
   - What's unclear: Minor discrepancy — could be test count evolution.
   - Recommendation: Run pytest and record the actual current count in the verification evidence.

## Sources

### Primary (HIGH confidence)

- Direct inspection of codebase artifacts — `eslint.config.js`, `pyproject.toml`, `package.json` read and confirmed
- Live command execution — `npm run lint:py`, `npm run lint:js`, `npm run lint` run and confirmed passing
- `.planning/phases/13-linting-baseline/13-01-SUMMARY.md` — Phase 13 Plan 01 evidence
- `.planning/phases/13-linting-baseline/13-02-SUMMARY.md` — Phase 13 Plan 02 evidence
- `.planning/v2.0-MILESTONE-AUDIT.md` — audit confirmation that VERIFICATION.md is missing
- `.planning/phases/12-python-unit-tests/12-VERIFICATION.md` — VERIFICATION.md template/format reference
- `.planning/phases/15-pre-push-hook/15-VERIFICATION.md` — VERIFICATION.md template/format reference

### Secondary (MEDIUM confidence)

None — all findings verified directly from codebase.

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools installed and running; versions confirmed from package.json
- Architecture: HIGH — VERIFICATION.md format established by 3 preceding verification phases
- Pitfalls: HIGH — based on direct artifact inspection and audit findings, not speculation

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (stable domain — no external dependencies changing)
