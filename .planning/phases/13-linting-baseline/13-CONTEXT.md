# Phase 13: Linting Baseline - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Python (ruff) and JavaScript (ESLint v10) linting runs clean on the entire codebase with zero pre-existing violations. Linting is runnable via npm scripts (`lint:py`, `lint:js`, `lint`). No new linting rules beyond E/F/W/B/I/UP for Python and eslint:recommended for JS. Pre-push hook integration is Phase 15.

</domain>

<decisions>
## Implementation Decisions

### Baseline cleanup strategy
- Auto-fix everything ruff and ESLint can handle automatically
- Manually fix any violations that can't be auto-fixed (no inline suppressions like noqa or eslint-disable)
- One commit per linter: separate commit for ruff fixes, separate commit for ESLint fixes
- Quick sanity check of diffs before committing (review for surprises, trust standard fixes)

### Line length & formatting scope
- Max line length: 88 characters for both Python and JavaScript (consistent across languages)
- Ruff: lint only, no formatting enforcement (no ruff format)
- Import sorting enforced via ruff's I rules (auto-fix enabled)

### ESLint configuration
- Base ruleset: eslint:recommended
- Config format: CommonJS (`eslint.config.js` with `module.exports`)
- Source type: `script` (IIFE pattern, no ES modules)
- Browser globals: Plotly, Decimal declared; Claude scans JS files for additional globals actually in use
- Semicolons and style conventions: Claude matches existing code style

### Ruff configuration
- Target Python version: 3.10 (enables modern syntax via UP rules)
- Rule categories: E, F, W, B, I, UP — all sub-rules enabled, no exclusions
- No docstring rules (D-rules excluded)
- Same rules apply everywhere including test files (tests/python/)

### Claude's Discretion
- Additional browser globals beyond Plotly/Decimal (scan and declare what's used)
- Semicolon enforcement convention (match existing JS style)
- Any ruff per-file overrides if edge cases arise during cleanup

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

*Phase: 13-linting-baseline*
*Context gathered: 2026-02-25*
