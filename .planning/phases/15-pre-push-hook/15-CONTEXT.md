# Phase 15: Pre-Push Hook - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Automated quality gate that blocks `git push` when the fast test suite fails, plus unified npm scripts (`test:fast`, `verify`) for manual invocation. The hook runs lint + unit tests in parallel and rejects before reaching GitHub on failure.

</domain>

<decisions>
## Implementation Decisions

### Hook mechanism
- Use **Lefthook** as the hook manager
- Install as npm devDependency (`@evilmartians/lefthook`)
- Auto-install hook via `postinstall` script in package.json
- Standard `--no-verify` bypass allowed for emergencies
- Config lives in `lefthook.yml` at project root

### Fast gate composition
- Gate runs **lint + unit tests in parallel** (lefthook parallel commands)
- Lint: `ruff check pipeline/ tests/` + `eslint public/js/`
- Tests: `pytest tests/python/ -m "not live"` (non-live only)
- Full project scope (not incremental/changed-files-only)
- **30 second hard timeout** — gate killed and push rejected if exceeded

### npm script design
- `npm run test:fast` — Same as pre-push gate: lint + unit tests (exact same commands, same exit codes)
- `npm run verify` — Full suite in sequence: fast gate + live pytest + Playwright
- **Replace** existing `verify` script entirely (old pipeline/verify commands can be run directly)
- Keep existing scripts (`lint`, `test`, `lint:py`, `lint:js`, `test:python:live`) as-is — minimal disruption
- Add `test:fast` as the new script; update `verify` to the full tiered suite

### Failure experience
- **Show failing output only** — suppress passing check output
- **Clear failure banner** on blocked push (e.g., "Push blocked: lint errors found. Run npm run test:fast to see details.")
- **Silent on success** — no extra output, push just goes through
- **Show all failures together** — since lint and tests run in parallel, display both lint errors and test failures so developer can fix everything in one pass

### Claude's Discretion
- Exact lefthook.yml configuration syntax
- Banner formatting and exact wording
- How to compose parallel commands in lefthook
- Timeout implementation details

</decisions>

<specifics>
## Specific Ideas

- Success criteria #2 requires the hook to complete in under 10 seconds on a clean codebase — the 30s timeout is a safety net, not the target
- `npm run test:fast` must produce the exact same result as the pre-push hook (same gate, same exit code) per success criteria #3
- `npm run verify` must run all three tiers: fast tests + live pytest + Playwright per success criteria #4

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 15-pre-push-hook*
*Context gathered: 2026-02-25*
