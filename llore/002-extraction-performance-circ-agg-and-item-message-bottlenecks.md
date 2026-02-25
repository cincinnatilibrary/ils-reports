---
id: "002"
title: "Extraction Performance: circ_agg and item_message Bottlenecks"
date: "2026-02-25"
status: "proposed"
tags: [performance, extraction, postgresql]
---

# Extraction Performance: circ_agg and item_message Bottlenecks

## Context

A sample build (500 rows/table, `scripts/build-sample-db.sh`) was run on 2026-02-25 against
the live Sierra PostgreSQL instance to collect baseline timing data. Run #8 completed in
**1m 36s** total. Two stages dominate and warrant investigation before the full production
pipeline is benchmarked.

### Sample build timing (Run #8)

| Stage | Rows loaded | Elapsed | Rows/sec (sample) |
|---|---:|---:|---:|
| `circ_agg` | 500 (of 519,534) | 59.9s | 8/s ⚠ |
| `item_message` | 500 | 19.3s | 26/s ⚠ |
| `item` | 500 | 5.4s | 92/s |
| `volume_record` | 500 | 3.4s | 146/s |
| `bib` | 500 | 2.3s | 214/s |
| `record_metadata` | 500 | 1.8s | 276/s |
| All lookup tables | varies | <0.1s each | fast |
| `views`, `indexes`, `finalize` | — | ~0s | (sample only) |

---

## Assessment

### `circ_agg` — confirmed server-side bottleneck (63% of sample wall time)

The pipeline log printed `circ_agg: 519,534 rows` **before** the islice cap was applied,
which means PostgreSQL executed the full aggregation query and streamed back the entire
result set. The 8 rows/sec figure reflects Python stopping at 500 rows, not actual
transfer throughput.

**Root cause to investigate:** The `circ_agg` query is almost certainly a `GROUP BY`
aggregation over the Sierra checkout history tables. Aggregations must complete server-side
before the first row is returned to the client; there is no way to paginate them the same
way as base-table scans. The 60s is the query execution cost, and it will be present in
every production run regardless of how many rows are ultimately loaded.

**Production impact estimate:**
- 60s server-side aggregation (fixed cost, run #8 baseline)
- ~519k rows to transfer at unknown actual throughput
- If transfer sustains 5k rows/sec → +104s; at 1k rows/sec → +520s
- Likely owns **2–5 minutes** of production wall time

### `item_message` — slow first-page fetch, cause unknown

With `itersize=15000`, the first paginated fetch pulls ~15k rows. The full 15k-row first
page took ~19s, implying an effective throughput closer to **~750–800 rows/sec** once the
per-page overhead is paid. The 26 rows/sec headline is the islice artifact (500 rows ÷
19s), not the real rate.

However, 19s for a single paginated page fetch is still high relative to comparable tables
(`bib` fetches its first page in ~2s). This suggests the underlying SQL involves a
heavier join or a missing index on the Sierra side.

**Production impact estimate:**
- If `item_message` has ~1M rows at 800 rows/sec → ~20 min
- If it has fewer rows or the query is optimised → much less
- Size of the `item_message` table in production is unknown

### Everything else

All other stages appear healthy. Paginated base tables (`bib`, `record_metadata`, `item`,
etc.) show first-page costs of 1–5s, consistent with well-indexed queries. Lookup tables
(reference data) are sub-100ms. Views and indexes will grow with real data but are unlikely
to be the limiting factor.

---

## Plan (deferred — implement when production credentials are available)

### Step 1: Get production row counts and true throughput

Run the pipeline once without `EXTRACT_LIMIT` in a maintenance window and record the
telemetry. This gives ground-truth numbers instead of sample extrapolations.

```bash
uv run collection-analysis   # .env has OUTPUT_DIR set to production path
uv run python scripts/report-runs.py $OUTPUT_DIR/pipeline_runs.db --last-run
```

### Step 2: Inspect the `circ_agg` query

File: `collection_analysis/extract.py`, function `extract_circ_agg`.
File: `sql/` (if a corresponding view file exists).

- Confirm it is an aggregation (not a base-table scan) — if so, pagination is not possible
  without a rewrite.
- Check whether an index on `sierra_view` that would support the `GROUP BY` column(s) exists.
- Consider whether the aggregation can be broken into paginated chunks (e.g. keyed by
  `bib_record_id` ranges) instead of a single full-table scan.

### Step 3: Inspect the `item_message` query

File: `collection_analysis/extract.py`, function `extract_item_message`.
File: `reference/collection-analysis.cincy.pl_gen_db.ipynb` for the original SQL.

- Run `EXPLAIN ANALYZE` on the query against Sierra to identify missing indexes or
  sequential scans.
- Check if the WHERE clause or JOIN condition allows index use; if not, explore rewriting
  or adding an `ORDER BY` on a well-indexed column.

### Step 4: Tune `PG_ITERSIZE` for slow tables if needed

If query structure can't be changed, increasing `PG_ITERSIZE` specifically for slow tables
reduces round-trips. Currently `extract_item_message` and others share the global
`itersize` from config. A per-table override mechanism could be added to `extract.py` if
profiling shows it would help.

### Step 5: Re-benchmark and compare

After any changes, run `scripts/build-sample-db.sh` again and compare `report-runs.py`
output. For `circ_agg` specifically, also compare the server-side query time (the elapsed
before the first row is logged) across runs.

---

## Verification

```bash
# After any change, compare sample build timing:
scripts/build-sample-db.sh
uv run python scripts/report-runs.py out/pipeline_runs.db --last-run

# For a before/after markdown summary suitable for a PR or issue comment:
uv run python scripts/report-runs.py out/pipeline_runs.db --markdown
```

Acceptance criteria:
- `circ_agg` elapsed reduced by ≥ 30% in a full production run, OR query restructured to
  be paginated (verified by absence of the "N rows" pre-load log line).
- `item_message` first-page fetch time < 5s (matching `bib`-class tables).
