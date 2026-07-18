---
gsd_state_version: 1.0
milestone: v5.0
milestone_name: Direction & Momentum
status: recovering-complete-ready-for-product
last_updated: "2026-07-18"
progress:
  total_phases: 5
  completed_phases: 5
  recovery_plan: complete-pending-final-gate
---

# Project State

## Project Reference

See: .planning/PROJECT.md

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

**Current focus:** Pipeline recovery finished (Phases 1–5). Resume v5.0 product work at **Phase 25** once the Final Plan Completion Gate is green (two consecutive successful weeklies + CI on main).

## Recovery plan (2026-07) — done

Mid-2026 the weekly pipeline and ABS ingest had gone red (403 on old `/data` path, oversized `all` queries, frozen `meetings.json`, mixed CPI series, housing index/% mismatch). Recovery phases:

| Phase | Outcome |
|-------|---------|
| 1 ABS unblock | `ABS_API_BASE=…/rest/data`, targeted SDMX keys, quarterly CPI |
| 2 Calendar + frontend | `generate_frontend_data` / meetings + rates in weekly & daily jobs; fail-still-refresh |
| 3 Data contracts | WPI series, ABS RPPI + Cotality YoY overlay with >365d gap policy |
| 4 CI hardening | `ci.yml` (`verify:fast`), action major bumps, weekly failure issues, `live-canary.yml` |
| 5 Docs / ops | README + this STATE note (REST path, 3.11+, `gh workflow run`, generators) |

**Ops commands:**

```bash
gh workflow run weekly-pipeline.yml
gh workflow run live-canary.yml
npm run verify:fast
```

**ABS:** `https://data.api.abs.gov.au/rest/data` — never the retired `/data` path.

## Current Position

Phase: Recovery complete → next is **Phase 25** (Indicator Card UI) of v5.0  
Plan: Final Plan Completion Gate (live weeklies + CI)  
Status: Docs landed; push main + confirm green CI / weekly runs to close gate  
Last activity: 2026-07-18 — recovery Phases 1–5 implemented

Progress: Product roadmap still at Phase 24 complete / 25 pending; **data plane recovered**

## Performance Metrics

**v1.0 MVP:** Phases 1-7, 19 plans, 20 days, 81 commits  
**v1.1 Full Indicator Coverage:** Phases 8-10, 6 plans, 1 day  
**v2.0 Local CI & Test Infrastructure:** Phases 11-17, 11 plans, 2 days, 64 commits  
**v3.0 Full Test Coverage:** Phases 18-20, 6 plans, 1 day, 26 commits  
**v4.0 Dashboard Visual Overhaul:** Phases 21-23, 3 plans, 1 day, 9 commits  
**v5.0 Phase 24:** Pipeline temporal layer shipped; recovery 2026-07 restored weekly path

## Accumulated Context

### Decisions (recovery)

- ABS Data API **must** use `/rest/data` + targeted keys (not `all`)
- CPI history is **quarterly only** (monthly series too short for 10y Z-scores)
- Housing: ABS RPPI index in `abs_rppi.csv`; Cotality YoY sparse overlay in `corelogic_housing.csv` with gap > 365 days
- Critical ingest failure: still refresh meetings + last-known status, then `sys.exit(1)`
- CI: `npm run verify:fast` on every PR/push; live canary Mon/Thu

### Blockers/Concerns

- Final recovery gate still needs: push to origin, green `ci.yml` on main, ≥2 green weekly runs
- [Phase 27]: Historical chart needs 4+ weeks of snapshots after weekly is stable again
- [Phase 26]: 1200x630 OG image is a design deliverable before Phase 26 ships
- [Phase 28]: Spam Act 2003 compliance before any emails

## Session Continuity

Last session: 2026-07-18  
Stopped at: Recovery Phase 5 docs; ready to push and run Final Plan Completion Gate  
Resume: push main → watch CI + dispatch weekly/canary → Phase 25 product work
