# Phase 24: Pipeline Temporal Layer - Context

**Generated:** 2026-02-26
**Method:** Synthetic discuss (5 agents)
**Status:** Ready for planning

<domain>
## Phase Boundary

**Goal:** status.json contains direction-of-change data that all frontend momentum features can consume.

Phase 24 introduces a temporal/snapshot layer to the Python pipeline. Before each weekly run overwrites status.json, the previous version is archived as a dated snapshot. The new status.json gains delta fields (previous_value, delta, direction per gauge; previous_hawk_score, hawk_score_delta in overall) computed by comparing against the archived snapshot. A rolling cap of 52 snapshots (1 year) prevents unbounded growth. This phase is pure backend -- no frontend changes, but it defines the data contract that Phases 25 (delta badges), 27 (historical chart), and 28 (newsletter) will consume.

**Requirements:** SNAP-01, SNAP-02, SNAP-03, SNAP-04, SNAP-05
**Depends on:** Phase 23 (v4.0 complete)
**Downstream consumers:** Phase 25 (delta badges + sparklines), Phase 27 (historical chart + narrative)
</domain>

<decisions>
## Implementation Decisions

### 1. Archive hook location: main.py orchestration with optional param into generate_status()
**Consensus: 5/5 -- Locked Decision**

All agents agree: the archive step belongs in `main.py` at the orchestration level. The sequence is:
1. `archive.load_previous()` reads current `public/data/status.json` BEFORE normalization
2. `generate_status(previous_status=prev)` accepts an optional dict, computes deltas inline, and writes the enriched status.json
3. `archive.save_snapshot(status)` saves a copy to `public/data/snapshots/YYYY-MM-DD.json`
4. `archive.prune_snapshots(max_entries=52)` enforces the rolling cap

**Critical constraint:** The archive step MUST be non-fatal. If loading the previous snapshot fails (first run, corrupted file, permission error), the pipeline proceeds without delta injection. Log a warning, do not crash. This matches the tiered failure handling pattern already in main.py.

**Rationale:** engine.py owns the status.json schema and should be the single writer. main.py is the orchestrator and handles the "before/after" coordination. archive.py is a pure I/O utility.

### 2. Snapshot format: full status.json copy with ISO date naming
**Consensus: 5/5 -- Locked Decision**

All agents agree: store a full copy of status.json as `public/data/snapshots/YYYY-MM-DD.json`.
- Full copy preserves maximum optionality for Phase 27 (historical chart) and future features
- ISO date naming sorts lexicographically = chronologically
- Same-day collision (manual trigger): overwrite, do not create duplicates
- Use UTC date from `generated_at` field, NOT local time
- File size: ~5KB x 52 = ~260KB/year -- trivial

### 3. Delta computation: archive.py for I/O, engine.py for math
**Consensus: 5/5 -- Locked Decision**

All agents agree on the separation of concerns:
- `archive.py` provides: `load_previous() -> dict | None`, `save_snapshot(status_dict)`, `prune_snapshots(max_entries)`
- `engine.py` computes deltas when `previous_status` is provided:
  - Per gauge: `delta = current_value - previous_value`, `direction` derived from delta sign
  - Overall: `hawk_score_delta = hawk_score - previous_hawk_score`
- `archive.py` should validate the loaded snapshot has the expected schema (at minimum: `overall.hawk_score` and `gauges` dict exist). Return None if invalid.

### 4. First-run cold-start: omit delta keys entirely
**Consensus: 5/5 -- Locked Decision**

All agents agree: when no previous snapshot exists, delta fields are ABSENT (key omission), not present with null values.
- Matches success criteria verbatim: "all delta fields are absent"
- Frontend uses `if ('delta' in gaugeEntry)` -- no badge rendered on absence
- JSON schema validation is simpler: delta fields are optional, not nullable
- Null values create ambiguity ("no change" vs "no data") -- absence is unambiguous

**Cold-start scenarios to test (from QA agent):**
1. No `public/data/snapshots/` directory exists
2. Directory exists but is empty
3. `index.json` exists but is empty array `[]`
4. Previous snapshot exists but individual gauge entry is missing (new indicator added)
5. Previous snapshot has gauge that no longer exists (indicator removed)

### 5. index.json: metadata array with hawk_score, delete old files on prune
**Consensus: 4/5 -- Locked Decision** (Devil's Advocate conceded after counter-argument)

Include metadata in index.json for Phase 27 consumption:
```json
[
  {"date": "2026-02-24", "hawk_score": 52.0, "zone": "neutral"},
  {"date": "2026-02-17", "hawk_score": 48.3, "zone": "cool"}
]
```
- Sorted newest-first (most recent at index 0)
- Phase 27 historical chart can render from index.json alone (one fetch, no 52-file load)
- Prune DELETES old snapshot files AND removes them from index
- index.json should be reconstructable from the snapshot directory as a safety mechanism (self-healing on corruption)

**Devil's Advocate concern:** Including hawk_score could be considered Phase 27 scope creep. Counter: Phase 24's goal says "all frontend momentum features can consume" and adding hawk_score is 2 lines of code. The group agreed this is sensible data design, not scope creep.

### Claude's Discretion

#### Direction field values and threshold
The Engineer and Devil's Advocate debated whether `direction` should be a separate field or derived by the frontend. Consensus was to include it (5/5), but the exact values and threshold need a decision:

**Decision (Claude's discretion):** Use `"up"`, `"down"`, `"unchanged"` as direction values. No threshold applied at the pipeline level -- direction is the raw sign of delta. The |delta| >= 5 noise threshold from DELT-01 is a FRONTEND display concern (Phase 25 decides whether to show the badge). The pipeline provides raw delta; the frontend filters.

**Rationale:** Separating "compute" from "display threshold" keeps Phase 24 focused on data and Phase 25 focused on UX. If the threshold changes, only frontend code changes.
</decisions>

<specifics>
## Specific Ideas

### From Engineer
- **generate_status() signature:** Add `previous_status: dict | None = None` parameter. This is backward-compatible -- existing tests pass None implicitly.
- **Module location:** `pipeline/normalize/archive.py` alongside engine.py, gauge.py, ratios.py, zscore.py. Follows existing normalize package structure.
- **UTC date extraction:** Parse `generated_at` field from previous status.json to get the snapshot date. `datetime.fromisoformat(status['generated_at'].rstrip('Z'))`.

### From QA
- **Schema validation in load_previous():** Before returning the previous status dict, verify it has `overall.hawk_score` (number) and `gauges` (dict with at least one entry). Return None if validation fails. This prevents delta computation from crashing on malformed data.
- **Test matrix (5 cold-start + 3 hot-path scenarios):**
  1. No snapshots dir -> creates dir, no deltas
  2. Empty snapshots dir -> no deltas
  3. Empty index.json -> no deltas
  4. Valid previous, new gauge added -> delta only for existing gauges
  5. Valid previous, gauge removed -> no delta for removed gauge
  6. Normal weekly run -> all deltas computed
  7. Same-day re-run -> snapshot overwritten, index updated
  8. 53rd run -> oldest snapshot deleted, index pruned to 52

### From UX Designer
- **Pipeline log output:** Add a visible "ARCHIVING" phase to the pipeline console output for debugging. Show: "Archived snapshot: 2026-02-24.json (52/52 entries)" or "First run: no previous snapshot".
- **Snapshot directory in git-auto-commit-action:** The `file_pattern` in weekly-pipeline.yml must be updated to include `public/data/snapshots/*.json public/data/snapshots/index.json` so snapshots are committed alongside status.json.

### From Product Owner
- **Non-fatal archiving as explicit design principle:** Document that archive failures produce warnings, never errors. The pipeline's primary job is to produce status.json. Archiving is a bonus. This matches the existing tiered failure model (critical/important/optional).

### From Devil's Advocate
- **Avoid post-processing pattern:** Do NOT read-modify-rewrite status.json after generate_status(). Pass previous_status INTO generate_status() so deltas are computed before the single write. This eliminates a race condition if two processes read status.json simultaneously.
</specifics>

<deferred>
## Deferred Ideas

### Sequence numbers in snapshot filenames
The Devil's Advocate suggested `001-2026-02-24.json` naming with sequence numbers for easier cap enforcement. The group rejected this: ISO dates sort correctly, index.json provides ordering, and sequence numbers add complexity for no gain. **Deferred: not needed.**

### Momentum Z-score (second derivative)
MOMENT-01 in REQUIREMENTS.md defines acceleration/deceleration per indicator. This is explicitly a future requirement (v5.x+). Phase 24 provides the delta data that MOMENT-01 would build on, but computing second derivatives is out of scope. **Deferred to v5.x+.**

### Dynamic threshold in pipeline
The Devil's Advocate raised whether the |delta| >= 5 display threshold should be configurable in status.json (e.g., `metadata.delta_threshold: 5`). The group agreed this is a Phase 25 UI concern and should not be in the pipeline. If it becomes configurable, it belongs in frontend config, not status.json. **Deferred to Phase 25.**

### Snapshot compression
At ~5KB per file and 52-entry cap, compression (gzip) adds complexity for negligible savings (~260KB -> ~50KB). Not worth the pipeline complexity. **Deferred: not needed.**

### Rebuild index from directory as startup step
The QA agent suggested rebuilding index.json from the directory listing on every run as a self-healing mechanism. The group agreed this is good defensive programming but not required for Phase 24. The save_snapshot function should build index.json correctly each time. A rebuild utility could be added later if corruption becomes an issue. **Deferred to maintenance backlog.**
</deferred>
