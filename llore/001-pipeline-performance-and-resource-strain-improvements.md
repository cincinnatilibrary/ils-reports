---
id: "001"
title: "Pipeline Performance and Resource-Strain Improvements"
date: "2026-02-25"
status: "proposed"
tags: [performance, postgresql, sqlite, pipeline, optimization]
---

# Pipeline Performance and Resource-Strain Improvements

## Context

The last pipeline run completed only 5 of 21 extraction stages in 84 minutes before failing.
Sierra PostgreSQL is a shared production system serving live ILS traffic — parallel connections
or aggressive query volume would harm other users. The SQLite write side is already well-optimized
(journal_mode=OFF, synchronous=OFF, 2 GB cache, exclusive lock). The remaining gains are:
fewer PostgreSQL round-trips, lower Python-level commit overhead, better SQLite page geometry,
and a configurable inter-table pause for courtesy on a shared server.

---

## Changes (in implementation order)

### 1. `collection_analysis/config.py` — new config key + updated default

**a)** Add to `_ENV_VARS` list (after `PG_ITERSIZE` entry):
```python
("PG_SLEEP_BETWEEN_TABLES", "pg_sleep_between_tables"),
```

**b)** Add float coercion in the type-coercion block (after `pg_itersize` block):
```python
try:
    cfg["pg_sleep_between_tables"] = float(cfg.get("pg_sleep_between_tables", 0.0))
except (ValueError, TypeError) as exc:
    raise ValueError(
        f"PG_SLEEP_BETWEEN_TABLES must be a number, got "
        f"{cfg.get('pg_sleep_between_tables')!r}"
    ) from exc
```

**c)** Add setdefault alongside the existing ones:
```python
cfg.setdefault("pg_sleep_between_tables", 0.0)
```

**d)** Change `pg_itersize` default from `5000` → `15000` in both places:
- `int(cfg.get("pg_itersize", 15000))` (coercion call, ~line 132)
- `cfg.setdefault("pg_itersize", 15000)` (setdefault, ~line 139)

**e)** Update module docstring: note new default (5000 → 15000) and add the new var.

**Impact:** 67% fewer PostgreSQL round-trips. `record_metadata` (15.6 M rows): 3,120 fetches → 1,040.

---

### 2. `collection_analysis/load.py` — page_size pragma + batch_size default

**a)** Add `page_size=32768` as the **first** entry in `BUILD_PRAGMAS`:
```python
BUILD_PRAGMAS = {
    "page_size": 32768,        # must precede any CREATE TABLE; 32 KB pages improve sequential writes
    "journal_mode": "OFF",
    "synchronous": "OFF",
    "cache_size": -2_000_000,
    "temp_store": "MEMORY",
    "mmap_size": 30_000_000_000,
    "locking_mode": "EXCLUSIVE",
}
```
`open_build_db()` applies all pragmas before any `load_table()` call, so ordering is safe.
SQLite default page size is 4 KB; 32 KB reduces I/O for large sequential inserts by ~10–30%.

**b)** Change `load_table` default `batch_size` from `1000` → `5000` (~line 81):
```python
def load_table(db, table_name, rows, batch_size: int = 5000) -> int:
```
Reduces Python-level commit cycles by 5×. Since `synchronous=OFF`, each commit has no fsync
cost — the gain is pure overhead reduction (15,633 → 3,127 commits for `record_metadata`).

---

### 3. `collection_analysis/run.py` — consume `pg_sleep_between_tables`

After `itersize = cfg["pg_itersize"]`, add:
```python
sleep_between = cfg.get("pg_sleep_between_tables", 0.0)
```

At the end of each iteration in the extraction loop (after `stats.append({...})`):
```python
if sleep_between > 0:
    logger.debug("  sleeping %.1fs (PG_SLEEP_BETWEEN_TABLES) ...", sleep_between)
    time.sleep(sleep_between)
```
(`time` is already imported.) Logs at `DEBUG` so it is silent under the default `INFO` level.

---

### 4. `.env.sample` — document tuning knobs

Replace the brief `PG_ITERSIZE` comment with an expanded tuning section:
```ini
# --- Performance tuning ---
#
# PG_ITERSIZE: rows fetched per PostgreSQL round-trip.
#   Fewer round-trips = less query-planner overhead on the shared Sierra server.
#   Default: 15000.  Safe range: 5000–50000.
PG_ITERSIZE=15000
#
# PG_SLEEP_BETWEEN_TABLES: seconds to pause between each table extraction.
#   Use to reduce load on Sierra during business hours.
#   Default: 0 (no pause).  With 21 tables, adds at most 21×value seconds total.
# PG_SLEEP_BETWEEN_TABLES=0
#
# SQLite write performance is tuned internally (page_size=32768, batch_size=5000,
# journal_mode=OFF, synchronous=OFF, 2 GB cache) — no env-var changes needed.
```

---

### 5. `tests/unit/test_config.py` — update + extend

**a)** Update `test_load_defaults_applied`: `assert result["pg_itersize"] == 5000` → `15000`.

**b)** Add `TestSleepBetweenTables` class with 4 tests:
- Default is `0.0`
- `PG_SLEEP_BETWEEN_TABLES=1.5` → `1.5`
- Integer string `"2"` coerced to `float(2.0)`
- Invalid value raises `ValueError` matching `"PG_SLEEP_BETWEEN_TABLES"`

---

### 6. `tests/unit/test_load.py` — two new tests

**a)** `test_build_pragma_page_size` in `TestOpenBuildDb` (must use a file-backed DB — `:memory:`
ignores `page_size`):
```python
def test_build_pragma_page_size(self, tmp_output_dir):
    db = load.open_build_db(tmp_output_dir)
    result = db.execute("PRAGMA page_size").fetchone()[0]
    assert result == 32768
    db.close()
```

**b)** `test_load_table_default_batch_size` in `TestLoadTable`:
```python
def test_load_table_default_batch_size(self):
    import inspect
    sig = inspect.signature(load.load_table)
    assert sig.parameters["batch_size"].default == 5000
```

---

## Expected impact

| Change | What improves | Estimated gain |
|---|---|---|
| `page_size=32768` | SQLite write throughput | 10–30% faster on large tables |
| `batch_size` 1000 → 5000 | Python commit-loop overhead | 5–10% reduction |
| `PG_ITERSIZE` 5000 → 15000 | PostgreSQL round-trips | 67% fewer fetches; lower PG load |
| `PG_SLEEP_BETWEEN_TABLES` | Shared PG courtesy | Configurable; no speed impact |

The `bib` stage (1.5 k rows/s) will remain the slowest — its bottleneck is 7 correlated SQL
subqueries, out of scope here. Combined changes are estimated to reduce total pipeline time by
15–25% on write-heavy tables.

---

## Verification

```bash
scripts/test.sh            # all unit tests must pass (no regressions)
scripts/lint.sh            # ruff must be clean
uv run collection-analysis # smoke-test against real Sierra; observe logs and timing
uv run python scripts/report-runs.py --last-run   # confirm new run in pipeline_runs.db
```
