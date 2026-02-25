# Phase 17: Fix DATA_DIR Wiring & npm verify Chain - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the import-time DATA_DIR binding bug across all 5 ingestors so they use late-bound `pipeline.config.DATA_DIR`, and wire `verify_summary.py` into the `npm run verify` chain so all three tiers (fast tests, live pytest, Playwright) run cleanly without DATA_DIR assertion failures.

</domain>

<decisions>
## Implementation Decisions

### Verify chain behavior
- Tiers run sequentially: fast → live → Playwright (cheapest first)
- Fail-fast: stop at first failing tier, don't run subsequent tiers
- `verify_summary.py` runs after all three tiers pass as a final aggregation step
- `npm run verify` is the single entry point — pre-push hooks call this one command
- Individual tier scripts available: `verify:fast`, `verify:live`, `verify:playwright` for dev convenience
- `npm run verify` always runs all three tiers — no `--quick` mode, use individual scripts instead
- Summary report: simple pass/fail table (tier name, status, duration)
- Colored terminal output (green pass / red fail) with auto-detect for CI/no-TTY (strip ANSI automatically)
- Tests passing is sufficient proof that DATA_DIR wiring is correct — no separate lint-style wiring check
- `verify_summary.py` outputs to stdout only — no file artifacts

### DATA_DIR override visibility
- Silent override in tests — no logging about which DATA_DIR is active unless something fails
- Ingestors log DATA_DIR once at startup — useful for debugging, not noisy
- Environment variable override supported: `DATA_DIR=/custom/path` takes precedence over config
- Clean break: fix all 5 ingestors at once, no backward-compatibility shim for old import-time pattern

### Failure handling
- `verify_summary.py` crash = verify chain failure (not just a warning)
- Exit code: 0 = all passed, 1 = any failure (simple, standard for CI)
- Tier output passthrough — let pytest/vitest format their own failure output
- Pre-push hook blocks push on verify failure
- Bypass via git's built-in `--no-verify` flag — no custom escape hatch

### Claude's Discretion
- Late-binding implementation approach (function call, property access, or config accessor pattern)
- `isolate_data_dir` fixture implementation details
- Exact summary table formatting
- Test runner invocation details within npm scripts

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

*Phase: 17-fix-datadir-verify-chain*
*Context gathered: 2026-02-25*
