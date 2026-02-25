---
id: "003"
title: "Comprehensive Repository Assessment"
date: "2026-02-25"
status: "completed"
tags: [assessment, review, quality]
---

# Comprehensive Repository Assessment

## Sprint Progress Tracker

| Sprint | Description | Status | Date |
|--------|-------------|--------|------|
| 0 | Housekeeping | Complete | 2026-02-25 |
| 1 | Inventory & Deep Code Review | Complete | 2026-02-25 |
| 2 | Run & Verify | Complete | 2026-02-25 |
| 3 | Rubric Assessment A–D | Complete | 2026-02-25 |
| 4 | Rubric Assessment E–I | Complete | 2026-02-25 |
| 5 | Synthesis & Final Report | Complete | 2026-02-25 |

---

## Repository Context

- **Repo:** `/home/ray/Documents/ils-reports` (GitHub: `rayvoelker/ils-reports`)
- **Primary purpose:** ETL pipeline — Sierra ILS (PostgreSQL) → SQLite database for reporting and public analysis via Datasette
- **Tooling:** uv (modern Python project: `pyproject.toml`, `uv.lock`), hatchling build backend
- **Entrypoint:** `uv run python -m collection_analysis.run` or `uv run collection-analysis`
- **Output artifact:** `$OUTPUT_DIR/current_collection.db` (served at https://collection-analysis.cincy.pl/)
- **Current phase:** Phase 14 — all core functionality implemented (6 modules, 21 extraction functions, 26 views, 40+ indexes, 146 unit tests, CI/CD, docs)

---

## Assessment Rubric

(Sourced from the original `repo_assessment_prompt_uv_etl_sqlite.md`)

You are a senior Python maintainer and ETL/data-engineering reviewer. Your task is to conduct a **complete, thorough assessment** of the repository below and produce a pragmatic report focused on **correctness, maintainability, operational simplicity**, and avoiding **foot-guns**.

### What you must do

#### 1) Inventory & understand the project
- Read and understand:
  - `README*`, `pyproject.toml`, `uv.lock`
  - `src/` layout, any `cli/` or `__main__.py`
  - `tests/` and fixture data
  - docs (e.g., `docs/`, `mkdocs.yml`, `sphinx/`)
  - CI workflows (e.g., `.github/workflows/*`)
  - scripts (`scripts/`, `bin/`, `Makefile`, `justfile`, etc.)
  - config examples (`.env.example`, `config*.yaml`, etc.)
- Identify user-facing entrypoints:
  - CLI commands, Python API, scheduled job, container entrypoint, etc.
- Map the pipeline shape:
  - **inputs → transforms → load** (SQLite schema/tables/indexes)
  - dependencies on external services or APIs
- Create a short "mental model" diagram in text form (bullet flow is fine).

#### 2) Run and verify (if possible)
If the repo is runnable in your environment:
- Use uv as intended:
  - install/sync deps using `uv`
  - run the canonical commands (lint/type-check/tests if present)
- Try a **small sample ETL run** if fixtures/sample inputs exist.
- Verify that the SQLite output is produced and sane:
  - tables exist, row counts look plausible, indexes/constraints are present
  - basic smoke queries succeed
If you cannot run the repo:
- Perform a static review anyway.
- Be explicit about what you could not validate.

#### 3) Evaluate against this maintainer-grade rubric
For each category below:
- Call out **Strengths**
- Call out **Risks / foot-guns**
- Provide **Specific, concrete improvements** (prefer small, high-leverage steps)

---

### Rubric Categories

**A) Architecture & complexity** — ETL boundary clarity, navigability, unnecessary abstractions

**B) ETL correctness & data guarantees** — idempotency, determinism, validation, error strategy

**C) SQLite design & performance** — schema, PRAGMAs, indexes, transactions, schema evolution

**D) Packaging & uv hygiene** — pyproject.toml quality, deps, reproducibility

**E) Testing strategy** — test pyramid, coverage, fixtures, behavioral vs structural

**F) Observability & operations** — logging, telemetry, failure modes, config posture

**G) Security & safety** — SQL injection, PII, supply chain, input validation

**H) Documentation & developer experience** — README, architecture docs, contributor docs

**I) CI/CD & quality gates** — CI coverage, pre-commit alignment, artifact checks

---

### Required Deliverables

1. **Executive summary** (5–10 bullets)
2. **Top risks / foot-guns** (ranked by severity)
3. **Complexity audit** (keep / minimal / bigger options)
4. **Testing & documentation gap analysis**
5. **Prioritized action plan** (quick wins / next sprint / longer-term)
6. **Concrete recommendations** (with file:line refs and code snippets)

---

## Sprint 1: Inventory & Deep Code Review

### 1.1 Pipeline Mental Model

```
                         Sierra ILS (PostgreSQL)
                         sierra_view schema
                                │
    ┌───────────────────────────┼───────────────────────────┐
    │                    run.py:main()                       │
    │                                                       │
    │  1. config.load()          ← .env / env vars          │
    │  2. _configure_logging()   ← LOG_LEVEL, LOG_FILE      │
    │  3. telemetry.open_telemetry_db()                     │
    │  4. load.open_build_db()   → current_collection.db.new│
    │  5. create_engine()        → SQLAlchemy PG connection  │
    │                                                       │
    │  ┌─────────── for each of 21 tables ───────────┐     │
    │  │  extract.extract_<table>(pg_conn, itersize)  │     │
    │  │       │                                      │     │
    │  │       ▼  (generator yields RowMapping dicts) │     │
    │  │  itertools.islice(gen, extract_limit)        │     │
    │  │       │                                      │     │
    │  │       ▼                                      │     │
    │  │  load.load_table(db, name, rows)             │     │
    │  │    - auto-creates table from first row keys  │     │
    │  │    - JSON-serializes dict/list values         │     │
    │  │    - ISO-formats datetime values              │     │
    │  │    - batch INSERT via executemany             │     │
    │  │    - db.commit() per batch                   │     │
    │  └──────────────────────────────────────────────┘     │
    │                                                       │
    │  6. transform.create_views(db)   ← sql/views/*.sql   │
    │  7. transform.create_indexes(db) ← sql/indexes/*.sql │
    │  8. load.finalize_db(db)         ← ANALYZE + WAL     │
    │  9. _write_run_stats(db)         → _pipeline_run tbl │
    │ 10. load.swap_db()  → atomic os.replace(.new → .db)  │
    │                                                       │
    │  finally:                                             │
    │    telemetry.finish_run()   → pipeline_runs.db        │
    └───────────────────────────────────────────────────────┘
                                │
                                ▼
                    $OUTPUT_DIR/current_collection.db
                    (served via Datasette at cincy.pl)
```

### 1.2 Production Module Inventory

| Module | Lines | Purpose |
| --- | --- | --- |
| `config.py` | 179 | Env var loading, type coercion, deprecated JSON fallback |
| `extract.py` | 316 | 21 extraction functions querying Sierra PostgreSQL |
| `load.py` | 145 | SQLite build lifecycle: open, load_table, finalize, swap |
| `transform.py` | 50 | Execute SQL view/index files in alphabetical order |
| `run.py` | 243 | Pipeline orchestration, telemetry, logging setup |
| `telemetry.py` | 130 | Persistent `pipeline_runs.db` with run/stage tables + views |

### 1.3 Extraction Function Catalog

#### Paginated functions (10) — cursor-based `id > :id_val` pagination

| Function | ID Column | Query File | Uses `:target_date` |
| --- | --- | --- | --- |
| `extract_record_metadata` (line 50) | `record_id` | `record_metadata.sql` | Yes |
| `extract_bib` (line 71) | `bib_record_id` | `bib.sql` | Yes |
| `extract_item` (line 92) | `item_record_id` | `item.sql` | Yes |
| `extract_bib_record` (line 113) | `id` | `bib_record.sql` | Yes |
| `extract_volume_record` (line 134) | `volume_record_id` | `volume_record.sql` | Yes |
| `extract_item_message` (line 155) | `varfield_id` | `item_message.sql` | No |
| `extract_bib_record_item_record_link` (line 178) | `id` | `bib_record_item_record_link.sql` | No |
| `extract_volume_record_item_record_link` (line 193) | `id` | `volume_record_item_record_link.sql` | No |
| `extract_hold` (line 280) | `hold_id` | `hold.sql` | No |
| `extract_circ_leased_items` (line 303) | `id` | `circ_leased_items.sql` | No |

All 10 share identical boilerplate: `id_val=0` → `while True` → `.mappings().all()` → `yield from` → advance cursor.

#### Non-paginated functions (11) — single query, `yield from rows`

| Function | Query File |
| --- | --- |
| `extract_language_property` (line 170) | `language_property.sql` |
| `extract_location` (line 208) | `location.sql` |
| `extract_location_name` (line 216) | `location_name.sql` |
| `extract_branch_name` (line 224) | `branch_name.sql` |
| `extract_branch` (line 232) | `branch.sql` |
| `extract_country_property_myuser` (line 240) | `country_property_myuser.sql` |
| `extract_item_status_property` (line 248) | `item_status_property.sql` |
| `extract_itype_property` (line 256) | `itype_property.sql` |
| `extract_bib_level_property` (line 264) | `bib_level_property.sql` |
| `extract_material_property` (line 272) | `material_property.sql` |
| `extract_circ_agg` (line 295) | `circ_agg.sql` |

### 1.4 SQL File Inventory

- **`sql/queries/`** — 22 files (21 extraction queries + `itype_property.sql`)
- **`sql/views/`** — 26 files (`01_isbn_view.sql` through `26_genre_view.sql`)
- **`sql/indexes/`** — 1 file (`01_indexes.sql`, 87 lines, 40 indexes)

### 1.5 Table-to-View-to-Index Dependency Map

Key inter-view dependencies (verified from SQL source):

- `04_item_view` depends on: `item`, `record_metadata`, `item_message`, `location`, `circ_agg` tables
- `06_branch_location_view` depends on: `location`, `location_name`, `branch`, `branch_name` tables
- `10_leased_item_view` depends on: `item_view` (view 04), `circ_leased_items`, `bib` tables
- `11_ld_compare_view` depends on: `leased_item_view` (view 10) — **only inter-view dependency in the chain**
- `14_two_months_leased_item_view` depends on: `circ_leased_items`, `item`, `bib` tables
- `17_last_copy_view` depends on: `item_view` (view 04), `branch_location_view` (view 06)
- `19_active_holds_view` depends on: `hold`, `item` tables
- `20_active_items_view` depends on: `item_view` (view 04)

Ordering is correct: view numbering respects all dependency chains. The critical path is `04 → 10 → 11`.

### 1.6 Initial Concern List

#### HIGH priority

**C1. Password not URL-encoded in connection string** — `config.py:174-177`

`pg_connection_string()` uses raw f-string interpolation:

```python
f"postgresql+psycopg://{cfg['pg_username']}:{cfg['pg_password']}"
f"@{cfg['pg_host']}:{cfg['pg_port']}/{cfg['pg_dbname']}"
```

Passwords containing `@`, `/`, `%`, or `#` will produce a malformed URL. SQLAlchemy's `URL.create()` handles this correctly.

**C2. SQLite build connection never closed on failure** — `run.py:112-225`

`db = load.open_build_db(...)` at line 113 is inside the `try` block, but the `finally` block (line 225) never calls `db.close()`. On pipeline failure, the SQLite connection leaks and `*.db.new` remains on disk. The telemetry DB *is* properly closed (`tel_db.close()` at line 235).

**C3. Naive semicolon splitting in transform.py** — `transform.py:46`

```python
for statement in sql.split(";"):
```

Will break on semicolons inside SQL string literals or comments. Current SQL files don't trigger this, but it's a latent foot-gun for future SQL additions.

#### MEDIUM priority

**C4. `.all()` materializes entire page in memory** — `extract.py:57,62` (and all paginated functions)

Each page calls `.mappings().all()`, loading up to `itersize` rows (default 15,000) into memory at once. With wide tables like `bib` (92-line query, many columns with JSON arrays), peak memory per page could be substantial. Not unbounded, but worth monitoring.

**C5. `logging.basicConfig()` at module import time** — `run.py:34-38`

Called when `run.py` is imported (including during tests). Can interfere with test logging configuration and add duplicate handlers. Should be moved inside `main()`.

**C6. No data validation on SQLite side** — `load.py:116-121`

`load_table()` auto-creates tables from the first row's keys with no type declarations, no constraints, no NOT NULL. Corrupted source data flows silently into the output DB. The pipeline has zero validation gates between PostgreSQL and SQLite.

**C7. f-string SQL for table/column names** — `load.py:100-104,119`

```python
f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_defs})'
```

Table and column names are injected via f-string. Values use `?` placeholders (safe). Risk is LOW because names come from Sierra's fixed schema, not user input — but it's still a pattern to be aware of.

**C8. Duplicate extraction boilerplate** — `extract.py` (10 functions)

The 10 paginated functions are identical except for: (a) SQL file name, (b) cursor column name, (c) whether `:target_date` is used. A `_paginate()` helper could eliminate ~150 lines of duplication.

**C9. 21 hardcoded (name, gen) tuples** — `run.py:128-171`

Adding a new extraction table requires manually editing a 43-line list. Could be data-driven from a registry or config structure.

#### LOW priority

**C10. Telemetry DB has no WAL mode** — `telemetry.py:82`

`open_telemetry_db()` uses default journal mode (DELETE). If Datasette later serves this DB, concurrent reads during writes could block.

**C11. `page_size: 8192` vs documentation** — `load.py:31`

BUILD_PRAGMAS sets `page_size: 8192` with comment "8KB pages are empirically fastest". MEMORY.md mentions 32768 was discussed. The current value is defensible but the discrepancy should be resolved.

**C12. `mmap_size: 30_000_000_000` (30GB)** — `load.py:36`

On systems with less virtual address space or constrained containers, this is silently ignored. Not harmful, but could confuse operators who expect it to take effect.

**C13. Hardcoded values in SQL views** — various

- Status codes duplicated across `13_book_connections_view.sql`, `19_active_holds_view.sql`, `20_active_items_view.sql` (16 ptype codes, 11 status codes)
- Location codes hardcoded in `23_duplicate_items_2ra_2rabi.sql` and `24_duplicate_items_3ra_2rabi.sql` (nearly identical files)
- Catalog URL patterns hardcoded in 6+ views

**C14. Missing ORDER BY in LIMIT 1 subqueries** — `hold.sql` (lines ~9, 40), `16_new_titles_view.sql`

Subqueries using `LIMIT 1` without explicit `ORDER BY` rely on implicit row ordering. PostgreSQL returns a consistent but undefined order; results may vary between versions.

**C15. `circ_agg.sql` is non-paginated** — `extract.py:295-300`

Unlike most large tables, `circ_agg` loads all rows via a single `.all()` call. If the result set is large, this materializes the entire table in memory at once.

### 1.7 Test Suite Summary

| Test File | Lines | Tests | Module Covered |
| --- | --- | --- | --- |
| `tests/conftest.py` | 114 | 6 fixtures | Shared fixtures |
| `tests/unit/test_config.py` | 238 | ~30 | `config.py` |
| `tests/unit/test_extract.py` | 632 | ~38 | `extract.py` |
| `tests/unit/test_load.py` | 245 | ~27 | `load.py` |
| `tests/unit/test_run.py` | 215 | ~18 | `run.py` helpers |
| `tests/unit/test_static_assets.py` | 21 | 1 | CSS validation |
| `tests/unit/test_telemetry.py` | 167 | ~16 | `telemetry.py` |
| `tests/unit/test_transform.py` | 124 | ~14 | `transform.py` |
| `tests/integration/test_pipeline.py` | 483 | ~25 | End-to-end |
| **Total** | **~2,239** | **~169** | |

Key observations:

- Unit tests use MagicMock for PostgreSQL — SQL query correctness is only validated in integration tests
- Integration tests exist but never run in CI (require real PostgreSQL)
- No view correctness tests (views are created but never queried to verify results)
- No `main()` smoke test in the unit test suite
- Extract tests are shallow for lookup tables (check 1-2 columns, not full schema)
- Fixture design is excellent (proper cleanup, scope management, environment isolation)

### 1.8 Project Configuration Summary

- **Build backend:** hatchling with `packages = ["collection_analysis"]` (correct)
- **Core deps (4):** SQLAlchemy >=2.0, psycopg[binary] >=3.1, python-dotenv >=1.0, sqlite-fts4==1.0.1
- **`sqlite-fts4` usage:** pinned but not imported anywhere in production code — appears to be a Datasette dependency that leaked into core
- **Dev deps (PEP 735):** 9 tools, all with minimum version bounds
- **Pre-commit hooks:** ruff v0.4.7, sqlfluff 2.3.5, detect-secrets v1.5.0, djlint (local)
- **CI:** unit-tests (Python 3.10-3.13) + security job — **no lint job in CI**
- **Coverage threshold:** 85% enforced in pyproject.toml + scripts/test.sh + CI
- **Scripts:** 10 well-organized scripts replacing Makefile

---

## Sprint 2: Run & Verify

### 2.1 Test Results

**Command:** `scripts/test.sh --cov` on Python 3.14.1

- **Result:** 146/146 passed in 0.57s
- **Coverage:** 88.36% (threshold: 85%)
- **Warnings:** None from tests themselves

Coverage per module:

| Module | Stmts | Miss | Cover | Uncovered Lines |
| --- | --- | --- | --- | --- |
| `config.py` | 62 | 2 | 97% | 136-137 (itersize ValueError branch) |
| `extract.py` | 183 | 0 | 100% | — |
| `load.py` | 64 | 0 | 100% | — |
| `run.py` | 87 | 49 | 44% | 91-238 (`main()` entirely uncovered) |
| `telemetry.py` | 21 | 0 | 100% | — |
| `transform.py` | 21 | 0 | 100% | — |

Key observation: `run.py:main()` (the actual pipeline entry point) has 0% unit test coverage. The 88% total is achieved because helper functions (`_timed_load`, `_configure_logging`, etc.) are tested individually, but the orchestration logic is only exercised in integration tests that never run in CI.

### 2.2 Lint Results

**Command:** `scripts/lint.sh`

- **Result:** FAILED — 3 ruff findings (all in test files)

| Rule | File | Issue |
| --- | --- | --- |
| SIM117 | `tests/unit/test_run.py:110` | Nested `with` statements should be combined |
| SIM105 | `tests/unit/test_transform.py:46` | `try/except/pass` should use `contextlib.suppress` |
| SIM105 | `tests/unit/test_transform.py:93` | `try/except/pass` should use `contextlib.suppress` |

These are style findings, not correctness bugs. Production code passes cleanly.

### 2.3 Existing Build Database Inspection

A `current_collection.db` exists at `out/current_collection.db` (1.4 MB) from a sample build with `EXTRACT_LIMIT=500`.

**Tables:** 21 base tables + `sqlite_stat1` (from ANALYZE)
**Views:** 26 views (all created successfully)
**Indexes:** 42 (40 application indexes + 2 SQLite internal)
**`PRAGMA integrity_check`:** `ok`

Row counts from the sample build (EXTRACT_LIMIT=500):

| Table | Rows | Notes |
| --- | --- | --- |
| `bib` | 500 | Capped |
| `item` | 500 | Capped |
| `record_metadata` | 500 | Capped |
| `circ_agg` | 500 | Capped |
| `hold` | 500 | Capped |
| `location` | 500 | Capped — should be ~200 (full lookup) |
| `location_name` | 500 | Capped — same issue |
| `language_property` | 485 | Under 500; full lookup data |
| `country_property_myuser` | 333 | Under 500; full lookup data |
| `itype_property` | 116 | Full lookup data |
| `branch` / `branch_name` | 52 each | Full lookup data |
| `item_status_property` | 30 | Full lookup data |
| `material_property` | 29 | Full lookup data |
| `bib_level_property` | 8 | Full lookup data |

Note: `EXTRACT_LIMIT` applies uniformly to all tables including small lookup tables. This means `location` (normally ~200 rows) and `location_name` are capped at 500 — which happened to be above their actual size, so they got full data. But if the limit were set to 50, lookup tables would be incomplete, breaking views that depend on them.

### 2.4 Telemetry Data (pipeline_runs.db)

8 runs recorded. History:

| Run | Duration | Result | Notes |
| --- | --- | --- | --- |
| 1 | 0.0 min | failed | Initial setup issues |
| 2 | — | failed | No completion timestamp |
| 3 | 84.0 min | failed | Long run, eventually failed |
| 4 | 0.0 min | failed | Quick failure |
| 5 | 93.1 min | failed | Long run, eventually failed |
| 6 | 0.3 min | failed | Quick failure |
| 7 | 2.3 min | success | First successful sample build |
| 8 | 1.6 min | success | Most recent sample build |

Stage timing from run 8 (most recent success, EXTRACT_LIMIT=500):

| Stage | Rows | Seconds | Rows/sec | Notes |
| --- | --- | --- | --- | --- |
| `circ_agg` | 500 | 59.9 | 8 | **Bottleneck** — 62% of total time |
| `item_message` | 500 | 19.3 | 26 | Second slowest |
| `item` | 500 | 5.4 | 92 | Complex JOIN chain |
| `volume_record` | 500 | 3.4 | 146 | |
| `bib` | 500 | 2.3 | 214 | |
| Other 16 stages | varies | <2.0 each | — | Fast |
| **Total** | | **97.0** | | |

`circ_agg` at 8 rows/sec is a known bottleneck (documented in llore/002). The query is non-paginated and uses a cross join with date subquery over `circ_trans`.

### 2.5 Pipeline Log Analysis

`pipeline.log` exists at project root (11,758 lines, 1.3 MB). Contains output from all 8 runs including failures. The log shows:

- Run failures were due to connection/config issues during initial setup, not pipeline logic bugs
- Successful runs complete with clean stage-by-stage timing output
- No ERROR-level entries in the successful runs
- INFO-level pagination progress messages work correctly (`record_metadata: 500 rows (cursor at id ...)`)

### 2.6 Stale Artifacts

| Artifact | Location | Issue |
| --- | --- | --- |
| `test.db` | Project root | Contains 4 tables (bib, item, hold, bib_record_item_record_link). Appears to be from manual testing. Not in `.gitignore`. |
| `pipeline.log` | Project root | 1.3 MB log from 8 runs. Not in `.gitignore`. |
| `current_collection.db.new-shm` | `out/` | **Orphaned WAL sidecar** from finalize step (see below) |
| `current_collection.db.new-wal` | `out/` | **Orphaned WAL sidecar** from finalize step (see below) |
| `coverage-badge.svg` | Project root | Regenerated on each `--cov` run |

**Orphaned WAL sidecar bug:** `finalize_db()` switches the `.db.new` file to WAL mode, which creates `.db.new-shm` and `.db.new-wal` sidecar files. Then `swap_db()` does `os.replace(.db.new → .db)`, but only renames the main file — the `-shm` and `-wal` files remain with the `.db.new` prefix, orphaned on disk. This is a real (minor) bug: stale sidecar files accumulate, and the live `.db` starts in WAL mode without its checkpoint files.

### 2.7 What Could Not Be Validated

- **Full production build:** No access to Sierra PostgreSQL credentials from this environment. The sample build used `EXTRACT_LIMIT=500`.
- **Integration tests:** Require `pytest-postgresql` with a running PostgreSQL; not executed in this review.
- **Datasette serving:** Did not start a Datasette instance to verify view rendering.

---

## Sprint 3: Rubric Assessment A–D

### A) Architecture & Complexity

#### Strengths

- **Clear ETL boundaries.** Extract (extract.py) yields rows, Load (load.py) writes SQLite, Transform (transform.py) applies SQL files. Each module has a single responsibility. No module imports another except run.py, which orchestrates.
- **Flat, navigable structure.** 6 modules in one package, 49 SQL files in two directories. A new contributor can understand the full pipeline in under an hour.
- **No unnecessary abstractions.** No ORM for transforms, no plugin system, no abstract base classes. The code is straightforward procedural Python.
- **SQL files as the unit of transformation.** Views and indexes are plain `.sql` files with numeric prefixes for ordering. Easy to read, diff, and review.
- **Atomic swap pattern.** Build to `.db.new`, swap only on success. This is the correct pattern for full-rebuild ETL.

#### Risks / foot-guns

- **Pagination boilerplate duplication** (`extract.py`): 10 paginated functions share identical structure — `while True` → `.all()` → `yield from` → advance cursor. Only the SQL file name, cursor column, and parameter set differ. This is ~150 lines of repetition. Not a correctness issue today, but a maintenance burden when behavior needs to change (e.g., adding server-side cursors).
- **21 hardcoded (name, gen) tuples** (`run.py:128-171`): Adding or removing a table requires editing a 43-line list in `main()`. No validation that the list matches available SQL files or extraction functions.
- **Helper functions in run.py** (`_timed_load`, `_write_run_stats`, `_configure_logging`, `_log_summary`): These are well-placed in run.py because they're orchestration concerns, not reusable utilities. Keep as-is.

#### Simplification opportunities

**Pagination boilerplate** (extract.py):

- **Keep as-is:** 10 functions are explicit and greppable. Each is independently testable.
- **Minimal change:** Extract `_paginate(pg_conn, sql_name, cursor_col, params, itersize)` helper that encapsulates the while-loop. Reduce 10 functions to 10 one-liner calls. ~150 lines removed.
- **Bigger refactor:** Data-driven registry mapping table names to (sql_file, cursor_col, params). `run.py` iterates the registry. Not recommended — adds indirection without meaningful benefit.

**Table list in run.py:**

- **Keep as-is:** Explicit list is greppable and makes the extraction order obvious.
- **Minimal change:** Move to a module-level constant `EXTRACTION_STAGES` as a list of named tuples. Still explicit but separated from `main()`.
- **Bigger refactor:** Auto-discover from SQL files + extract function naming convention. Over-engineered for 21 tables.

### B) ETL Correctness & Data Guarantees

#### Data contract summary

The pipeline guarantees:

1. **Idempotency** — full rebuild + atomic swap means re-running produces the same result and never corrupts the live DB. Confirmed correct.
2. **Full rebuild** — `_TARGET_DATE = "1969-01-01"` ensures all records are fetched. No incremental logic exists or is needed.
3. **Atomic delivery** — `os.replace()` is atomic on POSIX. The live DB is either the old version or the new version, never a partial build.
4. **Deterministic row content** — each row comes from a specific PostgreSQL query with parameterized WHERE clauses. Same source data produces same rows.

#### Correctness risks

| Risk | Severity | Impact | Location | Fix |
| --- | --- | --- | --- | --- |
| **No ORDER BY in paginated queries** | MED | Row order within the output DB is undefined. Different PostgreSQL versions or plan changes could reorder rows. Doesn't affect correctness (views use their own ORDER BY) but makes diffing builds harder. | `sql/queries/*.sql` | Add `ORDER BY <cursor_col>` to all paginated queries. Already implicitly ordered by the `WHERE id > :id_val` pagination, but explicit is safer. |
| **Missing ORDER BY in LIMIT 1 subqueries** | MED | `hold.sql` and `16_new_titles_view.sql` use `LIMIT 1` without `ORDER BY`. PostgreSQL returns an arbitrary row; results are non-deterministic. | `sql/queries/hold.sql`, `sql/views/16_new_titles_view.sql` | Add explicit `ORDER BY` to every `LIMIT` subquery. |
| **No schema validation on SQLite side** | MED | `load_table()` creates untyped columns from the first row's keys. If a source query changes its column set (e.g., after a Sierra upgrade), the mismatch silently propagates. No column type, NOT NULL, or CHECK constraints. | `load.py:116-121` | For a full-rebuild pipeline, this is an acceptable tradeoff. Consider adding a post-build schema assertion step (compare actual columns against expected). |
| **`_serialize` ignores unexpected types** | LOW | `_serialize(v)` handles dict, list, datetime, date, and passes everything else through. If PostgreSQL returns a `Decimal`, `UUID`, or `memoryview`, it passes through to SQLite which may store it as a blob or string. | `load.py:108-113` | LOW risk — Sierra's schema is well-known. Could add a catch-all `else: str(v)` for safety. |
| **Deduplication** | NONE | Pagination-by-id prevents duplicates. Each page fetches `WHERE id > :id_val ORDER BY id LIMIT :limit_val`. No row can appear in two pages. Confirmed correct for all 10 paginated functions. | — | — |
| **Error strategy** | OK | Single try/finally wrapping the entire pipeline. On any failure: telemetry records the failure, `.db.new` is left on disk (cleaned up on next run by `open_build_db`), live DB is untouched. This is correct for a full-rebuild pipeline. | `run.py:112-237` | Consider `db.close()` in finally (see C2 in Sprint 1). |

### C) SQLite Design & Performance

#### SQLite posture summary

| Setting | Build Phase | Final Phase | Assessment |
| --- | --- | --- | --- |
| `journal_mode` | OFF | WAL | Correct — no journal during build, WAL for Datasette reads |
| `synchronous` | OFF | NORMAL | Correct — speed during build, safety for serving |
| `cache_size` | -2,000,000 (2GB) | (unchanged) | Aggressive but appropriate for a build machine |
| `page_size` | 8192 | (unchanged) | Reasonable for mixed row sizes. 32768 would be better for large JSON blobs but 8KB is fine. |
| `mmap_size` | 30,000,000,000 | (unchanged) | 30GB is aggressive; silently ignored if not available. Fine for build. |
| `temp_store` | MEMORY | (unchanged) | Correct for build performance |
| `locking_mode` | EXCLUSIVE | NORMAL | Correct — exclusive during build, shared for serving |

Overall: **Build PRAGMAs are well-chosen.** The pipeline follows the recommended SQLite bulk-loading pattern.

#### Schema assessment

- **No column types:** `CREATE TABLE "item" ("item_record_id", "barcode", ...)` — all columns are typeless. SQLite's dynamic typing makes this work, but Datasette users get no type hints, and tools like `sqlite-utils` can't infer types. Acceptable for this use case since the data comes from a known schema.
- **No constraints:** No PRIMARY KEY, NOT NULL, UNIQUE, CHECK, or FOREIGN KEY constraints. This is an intentional tradeoff: the pipeline does a full rebuild, so constraints add build time without catching errors (the source is trusted). The live DB is read-only via Datasette.
- **No `PRAGMA user_version`:** No schema versioning. The `_pipeline_run` table records run metadata, which partially fills this role. Consider setting `PRAGMA user_version = <unix_timestamp>` for quick version checks.

#### Index coverage analysis

42 indexes cover 10 of 21 tables. Key coverage gaps:

| Table | Missing indexes | Impact |
| --- | --- | --- |
| `circ_agg` | No indexes at all | Views `05_branch_30_day_circ_view` and `22_circ_agg_branch_view` query this table |
| `item_message` | No indexes | `04_item_view` joins on `item_message` |
| `hold` | Missing `ptype`, `is_frozen` | `19_active_holds_view` filters on these |
| `item` | Missing `item_record_id` | Several views join on this; only `item_record_num` is indexed |

No covering indexes or partial indexes exist. For a read-heavy Datasette workload, covering indexes on the most-queried views could significantly improve response time.

#### Transaction strategy

- `load_table()` commits per batch (`db.commit()` at `load.py:106`). With `journal_mode=OFF`, each commit is a no-op (no journal to flush). This is correct for the build phase.
- `finalize_db()` runs `ANALYZE` then sets WAL mode. ANALYZE generates `sqlite_stat1` rows used by the query planner.
- **Orphaned WAL sidecar bug** (documented in Sprint 2.6): `finalize_db()` creates WAL files for `.db.new`, then `swap_db()` renames only the main file. The `.db.new-wal` and `.db.new-shm` files are orphaned. Fix: either checkpoint WAL before swap, or don't switch to WAL until after swap.

### D) Packaging & uv Hygiene

#### uv health check

1. **`pyproject.toml` quality: GOOD.** Metadata complete, build backend correct, scripts entrypoint defined, dependency groups properly separated (core / datasette / docs / dev).
2. **`sqlite-fts4==1.0.1` is an unused dependency.** Not imported in any production module or SQL file. Likely intended for Datasette's full-text search plugin but should be moved to the `[project.optional-dependencies] datasette` group, or removed entirely if not used.
3. **`uv.lock` is checked in: YES.** Reproducible builds across machines and CI. Correct.
4. **Dev dependencies use PEP 735 `[dependency-groups]`: GOOD.** Modern pattern, properly supported by uv.
5. **`detect-secrets` is not in pyproject.toml.** Only available via `--with detect-secrets` in CI. Inconsistent with other dev tools — should be added to dev dependencies for local use.
6. **No type checking (mypy/pyright).** Not in dev deps, not in CI, not in pre-commit. For a 1063-line codebase with 6 modules, the value is moderate but the gap will grow with the codebase.
7. **Ruff version alignment: OK.** `pyproject.toml` says `>=0.4.0`, pre-commit pins `v0.4.7`. Compatible, but the pre-commit pin will drift from what developers run locally. Consider pinning in both places or using `rev: v0.4.0` in pre-commit.
8. **`requires-python = ">=3.10"`: GOOD.** Matches CI matrix (3.10, 3.11, 3.12, 3.13).
9. **Hatchling build config: CORRECT.** `packages = ["collection_analysis"]` is required because the project name (`ils-reports`) differs from the package directory (`collection_analysis`).
10. **No release automation.** No version bumping, no changelog, no PyPI publishing. Appropriate — this is an internal pipeline, not a library.

---

## Sprint 4: Rubric Assessment E–I

### E) Testing Strategy

#### Test pyramid assessment

| Level | Count | CI | Quality |
| --- | --- | --- | --- |
| Unit tests | ~144 | Yes (4 Python versions) | Good — covers all modules |
| Integration tests | ~25 | **No** (require PostgreSQL) | Comprehensive but never gate PRs |
| E2E tests | 0 | No | `main()` has 0% unit coverage; integration tests cover it but not in CI |
| View correctness tests | 0 | No | Views are created but never queried to verify output |
| Property-based tests | 0 | No | Not needed at this scale |

#### Coverage analysis

Overall 88.36% exceeds the 85% threshold. But this masks a critical gap:

- `run.py:main()` (lines 91-238, the entire pipeline orchestration) has **0% unit test coverage**
- The 88% comes from testing helper functions (`_timed_load`, `_configure_logging`, etc.) and other modules at 97-100%
- `main()` is only tested in integration tests that never run in CI

This means CI can pass with a completely broken `main()` function.

#### Test quality patterns

- **Behavioral tests:** `test_load.py` and `test_telemetry.py` are genuinely behavioral — they verify outcomes (rows inserted, PRAGMA values, file created).
- **Structural tests:** Many `test_extract.py` tests are structural — they verify that a mock was called with expected parameters rather than testing actual query results. This is inherent to unit-testing database code.
- **Fixture design:** Excellent. `conftest.py` uses `yield` with cleanup, `monkeypatch.setenv` for isolation, optional PostgreSQL fixtures with graceful skip.

#### Missing test categories

1. **`main()` smoke test** — even a minimal test that patches `create_engine` and verifies the pipeline runs to completion would catch orchestration regressions
2. **View correctness tests** — load known data, create views, query views, assert expected results. This is the highest-leverage missing test category.
3. **Schema assertion test** — verify that `current_collection.db` has the expected tables, columns, and indexes after a build

### F) Observability & Operations

#### Logging assessment

- **Format:** `%(asctime)s  %(levelname)-8s  %(message)s` — clear, includes timestamp
- **Levels used:** INFO for progress, WARNING for empty tables and sample mode, DEBUG for sleep-between-tables
- **Per-stage progress:** Each extraction function logs row count at each page (`record_metadata: 500 rows (cursor at id 12345)`)
- **Stage summary table:** `_log_summary()` prints a formatted table with rows, seconds, and rows/sec per stage

**Issue:** `logging.basicConfig()` at `run.py:34` executes at import time. This affects any code that imports `run`, including tests. Should be inside `main()`.

#### Telemetry assessment

- **`pipeline_runs.db`** with `run` and `stage` tables — records every run with per-stage timing. Persists across runs.
- **3 views** (`v_stage_summary`, `v_recent_runs`, `v_stage_trends`) — useful for monitoring trends
- **Success/failure tracking** — `try/finally` ensures telemetry records even on failure

This is above-average for an ETL pipeline of this size.

#### "2am operator" checklist

What an operator gets today:

- Pipeline.log with timestamped progress (GOOD)
- Stage summary table in log output (GOOD)
- `pipeline_runs.db` with historical timing (GOOD)
- `.db.new` left on disk on failure (useful for debugging)

What's missing:

- **No alerting integration** — operator must check logs manually
- **No `PRAGMA integrity_check` after build** — corrupt output could be swapped in
- **SQLite connection not closed on failure** (`run.py` — see C2)
- **Exit code:** `main()` doesn't set `sys.exit(1)` on failure — it relies on exception propagation, which works but could be clearer
- **No row count validation** — if a table returns 0 rows (source outage), it's logged as a warning but the build continues and swaps

#### Config posture

- **Primary:** Environment variables (clean, 12-factor compliant)
- **Fallback:** config.json with DeprecationWarning (good migration path)
- **Validation:** Required keys checked, types coerced with clear error messages
- **Defaults:** Sensible (sslmode=require, itersize=15000, log_level=INFO)

### G) Security & Safety

#### Ranked safety concerns

| # | Severity | Issue | Location | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | **HIGH** | Password not URL-encoded in connection string | `config.py:174-177` | Use `sqlalchemy.engine.URL.create()` instead of f-string. One-line fix. |
| 2 | **MED** | `hold.sql` extracts patron metadata (ptype, home library, block code) served publicly via Datasette | `sql/queries/hold.sql` | Review with library data governance. Ptype codes are not directly PII but could narrow identification in small populations. |
| 3 | **LOW** | f-string SQL for table/column names in load.py | `load.py:100-104,119` | Names come from hardcoded Sierra schema, not user input. Risk is theoretical. Could use parameterized DDL but SQLite doesn't support `?` for identifiers. |
| 4 | **LOW** | Naive `sql.split(";")` in transform.py | `transform.py:46` | Current SQL files don't contain semicolons in strings. Would break if future SQL includes string literals with semicolons. |

#### Supply chain posture

- **4 core dependencies** — minimal surface area
- **`uv.lock` checked in** — reproducible builds
- **`detect-secrets` pre-commit hook** — prevents credential leaks
- **`.secrets.baseline`** — tracked, allows audit

Rating: **GOOD** for a pipeline of this size.

### H) Documentation & Developer Experience

#### Documentation inventory

| Document | Quality | Notes |
| --- | --- | --- |
| `README.md` (131 lines) | Good | Recently rewritten. Clear setup, architecture table, config reference. Minor: says "4 core modules" but lists 6. |
| `CLAUDE.md` (140 lines) | Excellent | Comprehensive for AI-assisted development. Includes arch decisions, workflow, config reference. |
| `plan.md` | Good | Design decisions documented before implementation. |
| `docs/` MkDocs site (7 pages) | Good | Pipeline architecture, configuration, data dictionary with table docs, development guide. |
| `llore/` (2 existing docs) | Good | Informal ADR system for performance assessments. |

#### Missing documentation

1. **Operational runbook** — what to do when the pipeline fails at 2am. Which logs to check, how to recover, how to verify the output DB.
2. **CONTRIBUTING.md** — how to add a new extraction table, how to add a new view, how to run integration tests.
3. **ADR system** — `llore/` is an informal alternative but doesn't follow a standard format (e.g., MADR).
4. **Data lineage** — no documentation mapping Sierra source tables to SQLite output tables to Datasette views. The reference notebook is the authoritative source but not structured for quick lookup.

### I) CI/CD & Quality Gates

#### CI coverage

| Check | In CI | In pre-commit | Gap |
| --- | --- | --- | --- |
| Unit tests | Yes (3.10-3.13) | No | — |
| Coverage threshold (85%) | Yes | No | — |
| Ruff linting | **No** | Yes | **CI doesn't run linters** — only enforced locally via pre-commit |
| SQLfluff linting | **No** | Yes | Same gap |
| djlint (templates) | **No** | Yes (local hook) | Same gap |
| detect-secrets | Yes | Yes | — |
| Type checking | **No** | **No** | Not enforced anywhere |
| Integration tests | **No** | No | Require PostgreSQL; not in CI |
| Package install check | **No** | No | Never verified that `uv pip install .` works |
| Artifact validation | **No** | No | No smoke test of built DB |

#### Pre-commit / CI alignment

**Critical gap:** CI only runs `scripts/test.sh --cov` and `detect-secrets`. All linting (ruff, sqlfluff, djlint) is only enforced via pre-commit hooks. If a developer pushes without running pre-commit (or uses `--no-verify`), lint violations go undetected.

**Fix:** Add a `lint` job to `ci.yml`:

```yaml
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv sync --all-extras
    - run: scripts/lint.sh
```

#### Recommended CI additions (minimal complexity)

1. **Add lint job** — `scripts/lint.sh` already exists; just call it in CI (5 lines of YAML)
2. **Add package install check** — `uv pip install . && collection-analysis --help` (verifies entrypoint works)
3. **Type checking** — future consideration; not urgent at 1063 lines

---

## Sprint 5: Synthesis & Final Report

### Deliverable 1: Executive Summary

1. **The project is mostly on the right track.** Architecture is clean, ETL boundaries are clear, the atomic swap pattern is correct, and the codebase is navigable. A new contributor can understand the full pipeline in under an hour.
2. **146 unit tests pass at 88% coverage,** but `run.py:main()` — the actual pipeline entry point — has 0% unit test coverage. The 88% masks this because helper functions are tested individually.
3. **CI has a critical enforcement gap:** linting (ruff, sqlfluff, djlint) is only enforced via pre-commit hooks, not in CI. A developer who pushes with `--no-verify` bypasses all lint checks.
4. **One real bug:** `pg_connection_string()` doesn't URL-encode the password. Passwords with `@`, `/`, or `%` will produce a malformed connection URL. One-line fix.
5. **One real bug (minor):** `finalize_db()` creates WAL sidecar files for `.db.new`, then `swap_db()` renames only the main file, orphaning `.db.new-wal` and `.db.new-shm` on disk.
6. **The extraction layer works but has significant boilerplate.** 10 paginated functions share identical structure; a `_paginate()` helper would remove ~150 lines.
7. **No data validation gates exist.** Corrupted source data flows silently from PostgreSQL through to the live SQLite DB. For a trusted internal source this is acceptable, but a post-build schema assertion would catch schema drift.
8. **Telemetry is above-average** for a pipeline of this size. `pipeline_runs.db` with per-stage timing, 3 analytical views, and persistent history across runs.
9. **`sqlite-fts4==1.0.1` is a core dependency that is never imported.** Should be moved to the `datasette` optional group or removed.
10. **View correctness tests are entirely absent.** 26 SQL views are created but never queried to verify output. This is the highest-leverage missing test category.

### Deliverable 2: Top Risks / Foot-guns (Ranked)

#### 1. Password not URL-encoded (HIGH)

- **Severity:** HIGH
- **Impact:** Pipeline fails to connect to Sierra if password contains special characters
- **Likelihood:** Medium — depends on password policy
- **Location:** `config.py:174-177`
- **Fix:** Replace f-string with `sqlalchemy.engine.URL.create()`

```python
# Before (config.py:172-178)
def pg_connection_string(cfg: dict) -> str:
    return (
        f"postgresql+psycopg://{cfg['pg_username']}:{cfg['pg_password']}"
        f"@{cfg['pg_host']}:{cfg['pg_port']}/{cfg['pg_dbname']}"
        f"?sslmode={cfg['pg_sslmode']}"
    )

# After
from sqlalchemy.engine import URL

def pg_connection_string(cfg: dict) -> str:
    return URL.create(
        drivername="postgresql+psycopg",
        username=cfg["pg_username"],
        password=cfg["pg_password"],
        host=cfg["pg_host"],
        port=int(cfg["pg_port"]),
        database=cfg["pg_dbname"],
        query={"sslmode": cfg["pg_sslmode"]},
    ).render_as_string(hide_password=False)
```

#### 2. CI doesn't run linters (MED)

- **Severity:** MED
- **Impact:** Lint violations can merge to main if pre-commit is bypassed
- **Likelihood:** Medium — any `--no-verify` push
- **Location:** `.github/workflows/ci.yml`
- **Fix:** Add a `lint` job (5 lines of YAML, `scripts/lint.sh` already exists)

#### 3. Naive semicolon splitting in transform.py (MED)

- **Severity:** MED
- **Impact:** Future SQL files with semicolons in string literals will silently produce broken statements
- **Likelihood:** Low today (current SQL files are clean), but increases as views grow in complexity
- **Location:** `transform.py:46`
- **Fix:** Use `sqlite3` executescript() or a proper SQL parser. Minimal change: `db.executescript(sql)` handles multi-statement files natively.

```python
# Before (transform.py:42-49)
for sql_file in sql_files:
    sql = sql_file.read_text()
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            db.execute(statement)

# After
for sql_file in sql_files:
    sql = sql_file.read_text()
    db.executescript(sql)
```

Note: `executescript()` issues an implicit `COMMIT` before executing. With `journal_mode=OFF` this is a no-op, but verify no side effects with WAL mode during finalize.

#### 4. SQLite connection not closed on failure (MED)

- **Severity:** MED
- **Impact:** File descriptor leak and stale `.db.new` file left with open write lock
- **Likelihood:** Occurs on every pipeline failure
- **Location:** `run.py:112-225`
- **Fix:** Add `db.close()` in the finally block:

```python
# run.py, in the finally block (after line 225):
finally:
    if "db" in locals():
        db.close()
    # ... existing telemetry code
```

#### 5. No data validation gates (MED)

- **Severity:** MED
- **Impact:** Schema drift or source corruption silently propagates to the live DB
- **Likelihood:** Low (Sierra schema is stable), but non-zero
- **Location:** `load.py:load_table()` (no validation) and `run.py` (no post-build checks)
- **Fix:** Add a post-build assertion that verifies expected tables exist and have >0 rows. Quick win: after `finalize_db()`, run `PRAGMA integrity_check` and verify table list matches expectations.

#### 6. `.all()` memory pattern (LOW)

- **Severity:** LOW
- **Impact:** Each pagination page materializes up to 15,000 rows in memory. For wide tables (bib: ~20 columns with JSON arrays), peak memory per page could be 100-200MB.
- **Likelihood:** Low — current itersize (15,000) is reasonable
- **Location:** `extract.py` (all paginated functions, e.g., line 57)
- **Fix:** No change needed at current scale. If memory becomes an issue, switch to server-side cursors with `stream_results=True` on the SQLAlchemy connection. This requires `yield_per()` instead of `.all()`.

#### 7. Orphaned WAL sidecar files (LOW)

- **Severity:** LOW
- **Impact:** Stale `.db.new-wal` and `.db.new-shm` files accumulate in output directory
- **Likelihood:** Occurs on every successful build
- **Location:** `load.py:finalize_db()` + `swap_db()`
- **Fix:** Checkpoint WAL before swap, or don't switch to WAL until after swap:

```python
# Option A: checkpoint before swap (in finalize_db, before FINAL_PRAGMAS)
db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

# Option B: set WAL after swap (in a new function or at end of run.py)
# Reopen the final DB, set WAL, close
```

### Deliverable 3: Complexity Audit

#### 3.1 Extract.py — 10 identical pagination loops

| Option | Effort | Lines Saved | Risk |
| --- | --- | --- | --- |
| **Keep as-is** | 0 | 0 | Each function is explicit and independently testable |
| **Minimal: `_paginate()` helper** | S | ~150 | Small refactor; tests become slightly more abstract |
| **Bigger: data-driven registry** | M | ~200 | Adds indirection; harder to grep for specific tables |

**Recommendation:** Minimal change. The `_paginate()` helper is a clear win:

```python
def _paginate(pg_conn, sql_name, cursor_col, params, itersize, label):
    sql = text(_load_sql(sql_name))
    id_val = 0
    total = 0
    while True:
        bind = {**params, "id_val": id_val, "limit_val": itersize}
        rows = pg_conn.execute(sql, bind).mappings().all()
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1][cursor_col]
        logger.info(f"  {label}: {total} rows (cursor at id {id_val})")
```

Then each function becomes:

```python
def extract_record_metadata(pg_conn, itersize=5000):
    yield from _paginate(
        pg_conn, "record_metadata", "record_id",
        {"target_date": _TARGET_DATE}, itersize, "record_metadata",
    )
```

#### 3.2 Run.py — 21 hardcoded (name, gen) tuples

| Option | Effort | Lines Saved | Risk |
| --- | --- | --- | --- |
| **Keep as-is** | 0 | 0 | Explicit ordering, easy to read |
| **Minimal: module-level constant** | S | 0 (reorganize) | Separates data from logic |
| **Bigger: auto-discover from SQL** | M | ~30 | Magic; harder to understand ordering |

**Recommendation:** Keep as-is. The explicit list makes the extraction order obvious. 43 lines is not excessive for 21 tables.

#### 3.3 Load.py — f-string SQL construction

| Option | Effort | Lines Saved | Risk |
| --- | --- | --- | --- |
| **Keep as-is** | 0 | 0 | Works correctly; names from trusted source |
| **Minimal: validate table/column names** | S | -5 (adds code) | Catches unexpected characters |
| **Bigger: use sqlite-utils** | M | ~20 | Adds dependency; changes API |

**Recommendation:** Keep as-is, but add a one-line validation:

```python
# At top of load_table(), before CREATE TABLE
if not all(c.isalnum() or c == "_" for c in table_name):
    raise ValueError(f"Invalid table name: {table_name!r}")
```

### Deliverable 4: Testing & Documentation Gap Analysis

#### Testing gaps (ranked by leverage)

| Gap | Leverage | Effort | Description |
| --- | --- | --- | --- |
| View correctness tests | **HIGH** | M | Load known data into base tables, create views, query views, assert expected output. Would catch SQL logic bugs in 26 views. |
| `main()` smoke test | **HIGH** | S | Patch `create_engine` to return mock, verify pipeline completes. Would catch orchestration regressions in CI. |
| Schema assertion test | MED | S | After build, verify expected tables/columns/indexes exist. Would catch schema drift. |
| Lint job in CI | MED | S | `scripts/lint.sh` already exists; 5 lines of YAML. |
| Post-build `PRAGMA integrity_check` | MED | S | One-line addition to `run.py` after `finalize_db()`. |
| Integration tests in CI | LOW | L | Requires PostgreSQL service in GitHub Actions. Valuable but complex. |

#### Documentation gaps (ranked by leverage)

| Gap | Leverage | Effort | Description |
| --- | --- | --- | --- |
| Operational runbook | HIGH | M | What to do at 2am: logs to check, recovery steps, verification commands |
| CONTRIBUTING.md | MED | S | How to add a table, add a view, run integration tests |
| Data lineage map | MED | M | Sierra source table → SQLite table → Datasette view |
| README module count fix | LOW | S | Says "4 core modules" but there are 6 |

### Deliverable 5: Prioritized Action Plan

#### Quick wins (this week)

| # | Action | Effort | Payoff | Location |
| --- | --- | --- | --- | --- |
| 1 | URL-encode password in `pg_connection_string` | S | Fixes a real bug | `config.py:172-178` |
| 2 | Add lint job to CI | S | Closes enforcement gap | `.github/workflows/ci.yml` |
| 3 | Close SQLite `db` in `finally` block | S | Fixes resource leak on failure | `run.py:225` |
| 4 | Move `sqlite-fts4` to datasette optional group | S | Removes unused core dep | `pyproject.toml:14` |
| 5 | Clean up stale artifacts (`test.db`, add to `.gitignore`) | S | Reduces confusion | Project root |
| 6 | Fix 3 ruff lint findings in test files | S | Makes `scripts/lint.sh` pass | `test_run.py:110`, `test_transform.py:46,93` |

#### Next sprint

| # | Action | Effort | Payoff | Location |
| --- | --- | --- | --- | --- |
| 7 | Extract `_paginate()` helper in extract.py | M | Removes ~150 lines of duplication | `extract.py` |
| 8 | Add view correctness tests (top 5 views) | M | Catches SQL logic bugs in CI | `tests/unit/test_views.py` (new) |
| 9 | Add `main()` smoke test | S | Covers 49 uncovered lines in run.py | `tests/unit/test_run.py` |
| 10 | Set `PRAGMA user_version` after build | S | Enables quick schema version checks | `load.py:finalize_db()` |
| 11 | Fix orphaned WAL sidecar files | S | Clean output directory | `load.py:finalize_db()` |
| 12 | Replace `sql.split(";")` with `executescript()` | S | Prevents semicolon foot-gun | `transform.py:46` |

#### Longer-term improvements

| # | Action | Effort | Payoff | Location |
| --- | --- | --- | --- | --- |
| 13 | Add post-build validation gate (schema + integrity + row counts) | M | Catches source corruption | `run.py` (new function) |
| 14 | Add mypy/pyright type checking | M | Catches type errors; IDE support | `pyproject.toml`, CI |
| 15 | Write operational runbook | M | 2am operator self-service | `docs/operations.md` (new) |
| 16 | Add index coverage for `circ_agg` and `item_message` tables | S | Improves Datasette query performance | `sql/indexes/01_indexes.sql` |
| 17 | Move `logging.basicConfig()` into `main()` | S | Prevents test interference | `run.py:34-38` |
| 18 | Add integration tests to CI (PostgreSQL service) | L | Gates SQL correctness | `.github/workflows/ci.yml` |

### Deliverable 6: Concrete Recommendations

#### Recommendation 1: Fix `pg_connection_string` (config.py:172-178)

Replace f-string URL construction with SQLAlchemy's `URL.create()`:

```python
from sqlalchemy.engine import URL

def pg_connection_string(cfg: dict) -> str:
    """Build a SQLAlchemy-compatible PostgreSQL connection URL from config."""
    return URL.create(
        drivername="postgresql+psycopg",
        username=cfg["pg_username"],
        password=cfg["pg_password"],
        host=cfg["pg_host"],
        port=int(cfg["pg_port"]),
        database=cfg["pg_dbname"],
        query={"sslmode": cfg["pg_sslmode"]},
    ).render_as_string(hide_password=False)
```

#### Recommendation 2: Add lint job to CI (.github/workflows/ci.yml)

```yaml
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --all-extras
      - run: scripts/lint.sh
```

#### Recommendation 3: Close SQLite db on failure (run.py:225)

```python
    finally:
        if "db" in locals():
            db.close()
        elapsed = time.time() - start
        telemetry.finish_run(
            tel_db,
            run_id,
            # ... rest unchanged
```

#### Recommendation 4: Replace sql.split(";") (transform.py:42-49)

```python
    for sql_file in sql_files:
        logger.info(f"Executing {sql_file.name} ...")
        sql = sql_file.read_text()
        db.executescript(sql)
```

#### Recommendation 5: Move sqlite-fts4 to datasette group (pyproject.toml:10-15)

```toml
# Before
dependencies = [
    "SQLAlchemy>=2.0",
    "psycopg[binary]>=3.1",
    "python-dotenv>=1.0",
    "sqlite-fts4==1.0.1",
]

# After
dependencies = [
    "SQLAlchemy>=2.0",
    "psycopg[binary]>=3.1",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
datasette = ["datasette>=1.0a1", "datasette-leaflet>=0.2", "sqlite-fts4>=1.0.1"]
```

#### Recommendation 6: Add `_paginate()` helper (extract.py)

```python
def _paginate(pg_conn, sql_name, cursor_col, params, itersize, label):
    """Generic cursor-based pagination over a Sierra query."""
    sql = text(_load_sql(sql_name))
    id_val = 0
    total = 0
    while True:
        bind = {**params, "id_val": id_val, "limit_val": itersize}
        rows = pg_conn.execute(sql, bind).mappings().all()
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1][cursor_col]
        logger.info(f"  {label}: {total} rows (cursor at id {id_val})")


def extract_record_metadata(pg_conn, itersize=5000):
    """Yield record_metadata rows."""
    yield from _paginate(
        pg_conn, "record_metadata", "record_id",
        {"target_date": _TARGET_DATE}, itersize, "record_metadata",
    )

# ... same pattern for the other 9 paginated functions
```

---

## Assessment Complete

This assessment reviewed 1,063 lines of production Python, 49 SQL files, ~2,239 lines of tests, CI/CD configuration, documentation, and a live sample database. The project is well-architected with clear ETL boundaries, correct atomic swap semantics, and above-average telemetry. The priority fixes are: (1) URL-encode password, (2) add lint CI job, (3) close db on failure, (4) add view correctness tests.
