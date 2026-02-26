---
id: "004"
title: "Comprehensive Project Walkthrough"
date: "2026-02-26"
status: "proposed"
tags: [documentation, walkthrough, architecture]
---

# Comprehensive Project Walkthrough

## 1. Introduction

This document is the single, authoritative reference for understanding the
**ils-reports** project — a data pipeline that extracts the Cincinnati &
Hamilton County Public Library (CHPL) physical collection from the Sierra
Integrated Library System (ILS) into a SQLite database served publicly via
Datasette at <https://collection-analysis.cincy.pl/>.

**Audience:** developers, data analysts, library staff, and future
maintainers who need to understand how every piece fits together — from the
PostgreSQL queries that pull data out of Sierra to the Fly.io container that
serves it.

**One-paragraph summary:** A nightly Python pipeline connects to Sierra's
`sierra_view` PostgreSQL schema, extracts 21 tables (10 paginated, 11
non-paginated), bulk-loads them into a temporary SQLite database with
aggressive write-speed PRAGMAs, creates 26 analytical views and 40+ indexes,
runs `ANALYZE`, switches the database to WAL mode, atomically swaps the
temporary file over the live database, and records telemetry. The live
database is served by a Datasette instance on Fly.io with CHPL-branded
templates and canned queries.

---

## 2. Project Lineage

The project started as a single Jupyter notebook
(`reference/collection-analysis.cincy.pl_gen_db.ipynb`) written to generate
a SQLite database from CHPL's Sierra ILS for ad-hoc reporting. That notebook
remains in the repository as the authoritative source for all Sierra SQL
queries and the full list of tables, views, and indexes.

Over time, the notebook was decomposed into a proper Python package
(`collection_analysis/`) with dedicated modules for configuration,
extraction, loading, transformation, and telemetry. The packaging uses
**hatchling** as the build backend and **uv** as the project/venv manager.

**Sierra context:** Sierra is an ILS developed by Innovative Interfaces
(now part of Clarivate). It stores library records in a PostgreSQL database
and exposes a read-only `sierra_view` schema. CHPL's Sierra instance runs on
port 1032 (the conventional Sierra PostgreSQL port) and uses database name
`iii`. The pipeline authenticates via username/password over TLS
(`sslmode=require`).

---

## 3. Repository Layout

```
ils-reports/
├── collection_analysis/        # Python package — the pipeline
│   ├── __init__.py
│   ├── config.py               # Configuration loading (.env / env vars)
│   ├── extract.py              # 21 Sierra extraction functions
│   ├── load.py                 # SQLite build lifecycle (open → load → finalize → swap)
│   ├── transform.py            # SQL view and index execution
│   ├── telemetry.py            # Persistent pipeline_runs.db
│   └── run.py                  # Orchestrator — the entry point
│
├── sql/
│   ├── queries/                # 21 PostgreSQL extraction queries (.sql)
│   ├── views/                  # 26 SQLite CREATE VIEW files (01–26)
│   └── indexes/                # 01_indexes.sql (40+ CREATE INDEX statements)
│
├── datasette/                  # Datasette serving layer
│   ├── metadata.yml            # DB metadata, canned queries, CC-BY-4.0 license
│   ├── datasette.yml           # Datasette settings (page size, SQL time limit)
│   ├── Dockerfile              # python:3.11-slim + uv + datasette 1.0a24
│   ├── fly.toml                # Fly.io deployment config (ord region, 512MB)
│   ├── requirements-datasette.txt
│   ├── templates/
│   │   ├── base.html           # CHPL-branded base (logo, footer, theme toggle)
│   │   └── index.html          # Landing page (hero, card links)
│   └── static/
│       ├── chpl-variables.css  # CHPL design tokens (navy, cream, teal, etc.)
│       ├── chpl-base.css       # Datasette component styling
│       ├── theme.js            # Dark/light toggle (localStorage + system pref)
│       ├── CHPL_Brandmark_Primary.svg
│       └── CHPL_Brandmark_OneColorNavy.svg
│
├── tests/
│   ├── conftest.py             # Shared fixtures (tmp dirs, valid_config, integration PG)
│   ├── unit/                   # 7 test modules (no external services)
│   └── integration/            # 1 test module (requires PostgreSQL)
│
├── scripts/                    # 14 shell/Python scripts (see §15)
│
├── docs/                       # MkDocs documentation source
│
├── reference/                  # Authoritative notebook — do not modify
│
├── llore/                      # Planning documents (001–004)
│
├── pyproject.toml              # hatchling build, deps, tool configs
├── .pre-commit-config.yaml     # 11 hooks across 5 repos
├── .sqlfluff                   # SQLFluff dialect=sqlite config
├── .secrets.baseline           # detect-secrets baseline (27 detectors)
├── .env.sample                 # Template for local .env
├── .github/workflows/ci.yml   # GitHub Actions CI
├── mkdocs.yml                  # MkDocs configuration
└── README.md
```

---

## 4. Data Flow Diagram

```
┌──────────────────────┐
│  Sierra PostgreSQL    │
│  (sierra_view schema) │
│  Port 1032 / TLS     │
└──────────┬───────────┘
           │  21 extraction queries
           │  (cursor-based pagination
           │   or single-shot lookups)
           ▼
┌──────────────────────┐
│  extract.py          │
│  Yields RowMapping   │
│  dicts per table     │
└──────────┬───────────┘
           │  Streaming rows
           │  (capped by EXTRACT_LIMIT
           │   via itertools.islice)
           ▼
┌──────────────────────┐
│  load.py             │
│  ┌────────────────┐  │
│  │ open_build_db()│  │   current_collection.db.new
│  │ BUILD_PRAGMAS  │──┼──▶  (journal_mode=OFF,
│  └────────────────┘  │     synchronous=OFF,
│  ┌────────────────┐  │     2GB cache, EXCLUSIVE)
│  │ load_table()   │  │
│  │ batch inserts  │  │
│  │ 5000 rows/batch│  │
│  └────────────────┘  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  transform.py        │
│  ┌────────────────┐  │
│  │ create_views() │  │   26 SQL files from sql/views/
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │create_indexes()│  │   40+ indexes from sql/indexes/
│  └────────────────┘  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  load.finalize_db()  │
│  ANALYZE + WAL mode  │
│  + NORMAL locking    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  load.swap_db()      │
│  os.replace(         │
│   .db.new → .db)     │   Atomic — Datasette sees
└──────────┬───────────┘   old DB until this instant
           │
           ▼
┌──────────────────────┐
│  Datasette (Fly.io)  │
│  Serves .db in WAL   │
│  mode for concurrent  │
│  reads                │
└──────────────────────┘

  Telemetry (pipeline_runs.db) ◄── recorded in try/finally
```

---

## 5. The Entry Point: `run.py`

`collection_analysis/run.py` orchestrates the entire pipeline in a
12-step sequence. It is invoked via `python -m collection_analysis.run`
or the console script `collection-analysis`.

### 5.1 Module-level setup (lines 1–39)

The module configures `logging.basicConfig()` at import time with a
standard format (`%(asctime)s  %(levelname)-8s  %(message)s`). This
guarantees that log output is visible even if `_configure_logging()` is
never reached.

### 5.2 Helper functions

**`_configure_logging(cfg)`** (lines 42–55) — Sets the root logger's
level from `cfg["log_level"]` and optionally attaches a `FileHandler` if
`cfg["log_file"]` is set.

**`_timed_load(db, name, rows)`** (lines 59–66) — Wraps `load.load_table()`
with `time.perf_counter()` timing. Returns `(row_count, elapsed_seconds)`
and logs throughput as rows/sec.

**`_write_run_stats(db, run_started, stats)`** (lines 69–72) — Writes a
snapshot of stage timing data into the build database as the
`_pipeline_run` table. This table survives the atomic swap and is
queryable in the live Datasette instance.

**`_log_summary(stats, elapsed)`** (lines 75–87) — Prints a
human-readable timing table to the log, with aligned columns for stage
name, row count, seconds, and rows/sec.

### 5.3 The `main()` function (lines 90–242)

The 12 steps map directly to the docstring at the top of the module:

1. **Parse arguments** — `--config` is deprecated; default is `None`.
2. **Load config** — `cfg_module.load(args.config)` reads `.env` then
   env vars, with deprecated JSON fallback.
3. **Configure logging** — `_configure_logging(cfg)` sets level + file.
4. **Open telemetry DB** — `telemetry.open_telemetry_db()` creates or
   opens `pipeline_runs.db` in the output directory.
5. **Start telemetry run** — `telemetry.start_run()` inserts a
   `success=0` row and returns `run_id`.
6. **Open build DB** — `load.open_build_db()` creates
   `current_collection.db.new` with `BUILD_PRAGMAS`.
7. **Connect to Sierra** — `create_engine(pg_connection_string(cfg))`
   opens the PostgreSQL connection.
8. **Extract and load 21 tables** — The `for name, gen in [...]` loop
   iterates over all 21 `(table_name, generator)` pairs. Each generator
   is optionally capped via `itertools.islice(gen, extract_limit)` when
   `EXTRACT_LIMIT > 0`. After each table, an optional
   `PG_SLEEP_BETWEEN_TABLES` pause is honored.
9. **Create 26 views** — `transform.create_views(db)`.
10. **Create 40+ indexes** — `transform.create_indexes(db)`.
11. **Finalize** — `load.finalize_db(db)` runs `ANALYZE` and switches to
    WAL/NORMAL PRAGMAs.
12. **Write run stats and swap** — `_write_run_stats()` embeds the stats
    into the build DB, then `load.swap_db()` atomically replaces the
    live file.

### 5.4 The `try/finally` guarantee (lines 112–236)

All work from step 6 onward is inside a `try` block. The `finally`
block (lines 225–236) always executes, regardless of success or failure:

- Calls `telemetry.finish_run()` with `success=True` or `success=False`.
- Closes the telemetry database.
- Logs the stage summary via `_log_summary()`.

This guarantees that every run — even failed ones — is recorded in
`pipeline_runs.db`.

---

## 6. Configuration: `config.py`

`collection_analysis/config.py` provides a single public function,
`load()`, and a helper, `pg_connection_string()`.

### 6.1 The `load()` function

**Priority order** (highest wins):

1. Environment variables — including those auto-loaded from `.env` by
   `python-dotenv`.
2. `config.json` — deprecated fallback with a `DeprecationWarning`.

**Step-by-step walk-through:**

1. `load_dotenv()` — silently loads `.env` if present.
2. Iterates over `_ENV_VARS` (12 `(ENV_NAME, config_key)` tuples) and
   reads each from `os.environ`.
3. Checks `_REQUIRED_KEYS` — if any are missing, attempts JSON fallback.
4. If a JSON file is used, emits `DeprecationWarning`.
5. Final validation — raises `ValueError` listing missing env var names.
6. **Type coercions:**
   - `pg_port` → `int`
   - `pg_itersize` → `int` (default 15000)
   - `pg_sleep_between_tables` → `float` (default 0.0)
   - `extract_limit` → non-negative `int` (default 0)
7. Applies defaults via `setdefault()` for optional keys.

### 6.2 Configuration keys

| Key | Env var | Type | Required | Default | Purpose |
|-----|---------|------|----------|---------|---------|
| `pg_host` | `PG_HOST` | str | yes | — | Sierra PostgreSQL hostname |
| `pg_port` | `PG_PORT` | int | yes | — | PostgreSQL port (typically 1032) |
| `pg_dbname` | `PG_DBNAME` | str | yes | — | Database name (typically `iii`) |
| `pg_username` | `PG_USERNAME` | str | yes | — | PostgreSQL username |
| `pg_password` | `PG_PASSWORD` | str | yes | — | PostgreSQL password |
| `output_dir` | `OUTPUT_DIR` | str | yes | — | Directory for output databases |
| `pg_sslmode` | `PG_SSLMODE` | str | no | `"require"` | SSL mode |
| `pg_itersize` | `PG_ITERSIZE` | int | no | 15000 | Rows per PostgreSQL fetch |
| `pg_sleep_between_tables` | `PG_SLEEP_BETWEEN_TABLES` | float | no | 0.0 | Pause between tables (seconds) |
| `log_level` | `LOG_LEVEL` | str | no | `"INFO"` | Python log level |
| `log_file` | `LOG_FILE` | str | no | `None` | Path to log file |
| `extract_limit` | `EXTRACT_LIMIT` | int | no | 0 | Cap per table (0 = no limit) |

### 6.3 `pg_connection_string(cfg)`

Builds a SQLAlchemy-compatible URL:

```
postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}
```

Uses the `psycopg` (v3) driver.

---

## 7. Extraction: `extract.py`

`collection_analysis/extract.py` contains 21 public functions, each
targeting one Sierra table or derived dataset. All functions accept a
SQLAlchemy connection and `itersize` parameter, and yield `RowMapping`
objects (dict-like).

### 7.1 Two extraction patterns

**Pattern A — Paginated (10 functions):**

Uses cursor-based pagination with a `while True` loop:

```python
id_val = 0
while True:
    rows = pg_conn.execute(sql, {"id_val": id_val, "limit_val": itersize})
                  .mappings().all()
    if not rows:
        break
    yield from rows
    id_val = rows[-1]["<cursor_column>"]
```

The cursor column varies by table (e.g., `record_id`, `bib_record_id`,
`item_record_id`, `varfield_id`, `hold_id`). The query's `WHERE`
clause includes `AND <id> > :id_val ORDER BY <id> ASC LIMIT :limit_val`.

Paginated functions:
1. `extract_record_metadata` — cursor: `record_id`
2. `extract_bib` — cursor: `bib_record_id`
3. `extract_item` — cursor: `item_record_id`
4. `extract_bib_record` — cursor: `id`
5. `extract_volume_record` — cursor: `volume_record_id`
6. `extract_item_message` — cursor: `varfield_id`
7. `extract_bib_record_item_record_link` — cursor: `id`
8. `extract_volume_record_item_record_link` — cursor: `id`
9. `extract_hold` — cursor: `hold_id`
10. `extract_circ_leased_items` — cursor: `id`

**Pattern B — Non-paginated lookup (11 functions):**

Single query, no parameters (or no pagination parameters):

```python
rows = pg_conn.execute(sql).mappings().all()
yield from rows
```

Non-paginated functions:
1. `extract_language_property`
2. `extract_location`
3. `extract_location_name`
4. `extract_branch_name`
5. `extract_branch`
6. `extract_country_property_myuser`
7. `extract_item_status_property`
8. `extract_itype_property`
9. `extract_bib_level_property`
10. `extract_material_property`
11. `extract_circ_agg`

### 7.2 The `_TARGET_DATE` sentinel

```python
_TARGET_DATE = "1969-01-01 00:00:00"
```

Because the pipeline always rebuilds the full database from scratch (no
incremental updates), this date predates any possible Sierra record. The
paginated queries use it as
`WHERE r.record_last_updated_gmt >= :target_date :: timestamptz` — which
matches all records.

### 7.3 The `_load_sql()` helper

```python
_SQL_DIR = Path(__file__).parent.parent / "sql" / "queries"

def _load_sql(name: str) -> str:
    return (_SQL_DIR / f"{name}.sql").read_text()
```

Each extraction function loads its query from `sql/queries/{name}.sql`.
This keeps SQL out of Python and makes queries easier to lint with
SQLFluff.

### 7.4 Representative queries

**`record_metadata.sql`** — Uses a CTE to select the ID page, then
joins back to `record_metadata` for the full row. Converts timestamps
to Julian day integers via `to_char(date, 'J') :: INTEGER`. Filters for
record types `'b'` (bib), `'i'` (item), and `'j'` (volume) with empty
`campus_code`.

**`bib.sql`** — The most complex extraction query. Uses a CTE to page
through bibs, then enriches each row with:
- `control_numbers` — `json_agg()` from `phrase_entry` (index tag `'o'`)
- `isbn_values` — `regexp_matches()` on `varfield` MARC tag `020`
- `publisher` — scalar subquery on `subfield` (field type `'p'`, tag `'b'`)
- `indexed_subjects` — `json_agg()` from `phrase_entry` (index tag `'d'`)
- `genres` — `json_agg()` from `varfield`/`subfield` (type `'j'`, tag `'a'`)
- `item_types` — nested CTE counting items by `itype_code_num`, joined
  to `itype_property_name`

**`location.sql`** — A simple `SELECT ... FROM sierra_view.location
ORDER BY id` — no parameters, no pagination.

---

## 8. Loading: `load.py`

`collection_analysis/load.py` manages the SQLite build lifecycle through
four functions called in strict order.

### 8.1 `open_build_db(output_dir)` → `sqlite3.Connection`

1. Computes the build path: `{output_dir}/current_collection.db.new`.
2. Creates parent directories (`mkdir -p`).
3. **Deletes any stale `.db.new`** from a previous failed run
   (`path.unlink(missing_ok=True)`).
4. Opens a fresh `sqlite3.connect(path)`.
5. Applies `BUILD_PRAGMAS`:

| PRAGMA | Value | Purpose |
|--------|-------|---------|
| `page_size` | 8192 | 8KB pages — empirically fastest for row-based tabular data |
| `journal_mode` | OFF | No rollback journal during build (safe because we swap atomically) |
| `synchronous` | OFF | Skip `fsync` calls (safe because `.db.new` is disposable) |
| `cache_size` | -2000000 | 2GB page cache (negative = KiB) |
| `temp_store` | MEMORY | Temp tables in RAM |
| `mmap_size` | 30000000000 | ~30GB memory-mapped I/O |
| `locking_mode` | EXCLUSIVE | No reader contention during build |

### 8.2 `load_table(db, table_name, rows, batch_size=5000)` → int

Inserts an iterable of row dicts into a SQLite table:

1. **Auto-creates the table** from the first row's column names (no type
   declarations — SQLite uses dynamic typing).
2. **Serializes values:**
   - `dict`/`list` → `json.dumps()`
   - `datetime`/`date` → `.isoformat()`
   - Everything else → passed through.
3. **Batches inserts** — accumulates rows in a list, flushes with
   `executemany()` every `batch_size` rows (default 5000), then
   `db.commit()`.
4. Returns the total row count.

### 8.3 `finalize_db(db)`

1. Runs `ANALYZE` — collects query-planner statistics for all tables and
   indexes.
2. Applies `FINAL_PRAGMAS`:

| PRAGMA | Value | Purpose |
|--------|-------|---------|
| `journal_mode` | WAL | Write-Ahead Logging for concurrent Datasette reads |
| `synchronous` | NORMAL | Balanced durability for serving |
| `locking_mode` | NORMAL | Allow multiple readers |

### 8.4 `swap_db(output_dir)`

```python
os.replace(src, dst)  # .db.new → .db
```

`os.replace()` is atomic on POSIX systems — Datasette readers see the
old database until the exact instant of the rename, then see the new one.

---

## 9. Transformation: `transform.py` & SQL

`collection_analysis/transform.py` exposes two public functions:

- `create_views(db, sql_dir=None)` — executes `sql/views/*.sql`
- `create_indexes(db, sql_dir=None)` — executes `sql/indexes/*.sql`

Both delegate to `_execute_sql_dir(db, directory)`, which:

1. Globs `*.sql` in the directory.
2. Sorts alphabetically (hence the numeric prefixes).
3. Reads each file, splits on `;`, strips whitespace.
4. Executes each non-empty statement via `db.execute()`.

The `sql_dir` parameter allows tests to inject a temporary directory.

### 9.1 The 26 views

The views are organized by purpose into several categories:

**Enrichment views** — Join base tables to produce human-readable data:
- `01_isbn_view.sql` — Extracts individual ISBNs from JSON arrays via
  `JSON_EACH`
- `03_location_view.sql` — Maps location codes to branch names with
  hyperlinks
- `04_item_view.sql` — Comprehensive item catalog with bib, location,
  branch, and status data
- `06_branch_location_view.sql` — Maps locations to branches with URLs
- `25_collection_detail_view.sql` — Low-level detail view with all bib
  record codes

**Analytics views** — Aggregate data for reporting:
- `05_branch_30_day_circ_view.sql` — 30-day circulation by branch
- `07_collection_value_branch_view.sql` — Collection value by branch,
  location, and format
- `12_location_percent_checkout_view.sql` — Percentage of items checked
  out by location
- `13_book_connections_view.sql` — Items grouped by title/author/location
- `22_circ_agg_branch_view.sql` — Monthly circulation by branch and item
  type
- `26_genre_view.sql` — Genre counts from JSON array extraction

**Hold views:**
- `08_hold_view.sql` — Comprehensive hold data with calculated dates
- `09_hold_title_view.sql` — Holds grouped by title with item counts
- `19_active_holds_view.sql` — Filters to currently active holds

**Leased item views:**
- `10_leased_item_view.sql` — Items with barcodes starting with `'L'`
- `11_ld_compare_view.sql` — Lucky Day vs. non-leased checkout rates
- `14_two_months_leased_item_view.sql` — Leased item circulation
  within 2 months

**Collection development views:**
- `15_new_downloadable_book_view.sql` — Downloadable books added in
  last 60 days
- `16_new_titles_view.sql` — Titles cataloged in last 30 days
- `17_last_copy_view.sql` — Last available copy at a location
- `20_active_items_view.sql` — Items with active status codes

**Duplicate detection views:**
- `02_duplicate_items_in_location_view.sql` — Duplicates by location,
  bib, and volume
- `18_dup_at_location_view.sql` — Detailed duplicate items at same
  location
- `23_duplicate_items_2ra_2rabi.sql` — Duplicates at locations 2ra/2rabi
- `24_duplicate_items_3ra_2rabi.sql` — Duplicates at locations 3ra/2rabi

**Operational views:**
- `21_item_in_transit_view.sql` — Items in transit with hold and
  overdue details

### 9.2 Inter-view dependency

View 10 (`leased_item_view`) must exist before view 11
(`ld_compare_view`) can be created. The numeric prefix system enforces
this ordering naturally.

### 9.3 Common SQL techniques across views

- **`JSON_EACH`** — Explodes JSON arrays into rows (views 1, 26)
- **`JSON_OBJECT`** — Builds structured URLs and metadata objects
  (views 3, 4, 6, 8, 15, 16, 17, 18, 23, 24)
- **`JSON_GROUP_ARRAY`** — Aggregates values into JSON arrays
  (views 2, 18, 23, 24)
- **CTEs** — Nearly every complex view uses one or more CTEs
- **`JULIANDAY`/date math** — Date calculations and filtering
  (views 5, 14, 19, 20)
- **`CASE`** — Conditional logic (views 5, 8, 9, 11, 20, 22)
- **Scalar subqueries** — Inline lookups for location/branch names
  (views 8, 9, 14, 16, 18, 25)

### 9.4 Indexes

`sql/indexes/01_indexes.sql` defines 40+ indexes across 13 tables:

| Table | Index count | Key columns indexed |
|-------|-------------|-------------------|
| `item` | 9 | `location_code`, `item_status_code`, `bib_record_num`, `barcode`, `item_format`, `creation_date`, composite (`bib_record_num`, `item_status_code`) |
| `bib_record` | 8 | `bcode1`–`bcode3`, `country_code`, `language_code`, `record_id`, `cataloging_date_gmt`, `id` |
| `bib` | 2 | `bib_record_num`, `indexed_subjects` |
| `record_metadata` | 2 | `record_id`, composite (`record_num`, `record_type_code`) |
| `volume_record` | 3 | `volume_record_num`, `bib_record_num`, `creation_julianday` |
| `language_property` | 2 | `code`, `id` |
| `bib_record_item_record_link` | 2 | `item_record_num`, `bib_record_num` |
| `volume_record_item_record_link` | 2 | `volume_record_num`, `item_record_num` |
| `location` | 3 | `branch_code_num`, `code`, `id` |
| `branch_name` | 2 | `branch_id`, `name` |
| `branch` | 2 | `code_num`, `id` |
| `hold` | 4 | `hold_id`, `bib_record_num`, `volume_record_num`, `item_record_num` |
| `circ_leased_items` | 1 | composite (`bib_record_num`, `op_code`) |

All indexes are created **after** all tables are loaded — this is
dramatically faster than maintaining indexes during inserts.

---

## 10. Telemetry: `telemetry.py`

`collection_analysis/telemetry.py` manages `pipeline_runs.db`, a
persistent SQLite database in the output directory that accumulates run
history across every pipeline execution and is **never wiped or
replaced**.

### 10.1 Schema

**`run` table** — one row per pipeline execution:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-incrementing run ID |
| `started_at` | TEXT | ISO timestamp |
| `completed_at` | TEXT | ISO timestamp (NULL if still running) |
| `total_elapsed_seconds` | REAL | Wall-clock time |
| `success` | INTEGER | 0=failed, 1=success |

**`stage` table** — one row per stage per run:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-incrementing stage ID |
| `run_id` | INTEGER FK | References `run(id)` |
| `stage` | TEXT | Stage name (table name, `views`, `indexes`, `finalize`) |
| `rows` | INTEGER | Row count (NULL for non-table stages) |
| `elapsed_seconds` | REAL | Stage wall-clock time |
| `rows_per_sec` | REAL | Throughput (NULL for non-table stages) |

### 10.2 Analytical views

1. **`v_stage_summary`** — AVG/MIN/MAX elapsed per stage across
   successful runs. Useful for spotting regression.
2. **`v_recent_runs`** — Most recent 20 runs with outcome
   (success/failed) and total minutes.
3. **`v_stage_trends`** — Per-stage timing over time for trend analysis.

### 10.3 Public API

- `open_telemetry_db(output_dir)` — Opens/creates `pipeline_runs.db`,
  applies schema and views, returns `sqlite3.Connection`.
- `start_run(db, started_at)` — Inserts `run` row with `success=0`,
  returns `run_id`.
- `finish_run(db, run_id, completed_at, total_elapsed_seconds, success,
  stats)` — Updates the `run` row and bulk-inserts `stage` rows.

---

## 11. The Atomic Swap Pattern

This pattern is central to the project's reliability and deserves its
own section.

### 11.1 The problem

Datasette serves the live `current_collection.db` file. The pipeline
takes minutes to rebuild it. During that time, the database must remain
queryable. A naive approach (truncate + reload) would break readers
mid-query.

### 11.2 The solution

1. Build to a **separate file**: `current_collection.db.new`.
2. Use aggressive PRAGMAs (`journal_mode=OFF`, `synchronous=OFF`) since
   the build file is disposable.
3. Once the build is complete, run `ANALYZE`, switch to `WAL` mode
   (for concurrent reads), and apply `NORMAL` PRAGMAs.
4. **Atomically swap** via `os.replace(.db.new, .db)`. On POSIX, this
   is a single `rename()` syscall — existing Datasette file handles
   continue reading the old inode, and new opens get the new file.

### 11.3 Failure mode

If the pipeline crashes mid-build:

- `current_collection.db` is untouched — readers see stale but valid
  data.
- `current_collection.db.new` is left on disk as a partial/corrupt
  file.
- On the next run, `open_build_db()` calls
  `path.unlink(missing_ok=True)` to delete the stale `.db.new` before
  starting fresh.

### 11.4 Telemetry in `finally`

The `try/finally` block in `run.py` ensures that `telemetry.finish_run()`
is always called. Even if the pipeline crashes after loading 15 of 21
tables, the telemetry database records the partial stats with
`success=0`. This makes post-mortem analysis possible.

---

## 12. Datasette Serving Layer

The live database is served by [Datasette](https://datasette.io/) — a
tool for exploring and publishing SQLite databases as JSON APIs and
interactive web interfaces.

### 12.1 `metadata.yml`

Defines the public-facing metadata:

- **Title:** "CHPL Collection Analysis"
- **License:** CC-BY-4.0
- **Source:** Cincinnati & Hamilton County Public Library Sierra ILS
- **Database description:** "Bibliographic records, items, holds, and
  circulation statistics"
- **Column-level documentation** for `item`, `bib`, `hold`, and
  `bib_record_item_record_link` tables
- **5 canned queries:**
  1. `items_by_branch` — Item count by location code
  2. `top_holds` — Titles with the most active holds
  3. `most_checked_out` — Top items by lifetime checkout total
  4. `available_items_by_format` — Available item count by format
  5. `recently_added` — Items added in the last 30 days

### 12.2 `datasette.yml`

Datasette runtime settings:

| Setting | Value | Purpose |
|---------|-------|---------|
| `default_page_size` | 100 | Rows per page |
| `max_returned_rows` | 10000 | Hard cap on query results |
| `sql_time_limit_ms` | 10000 | 10-second SQL timeout |
| `allow_download` | true | Enable full-DB download |
| `allow_signed_tokens` | false | Disable token auth |
| `default_allow_sql` | true | Allow arbitrary SQL queries |
| `force_https_urls` | true | HTTPS in generated links |
| `num_sql_threads` | 3 | Concurrent SQL executor threads |

Extra CSS/JS files are loaded from the static directory:
- `/static/chpl-variables.css`
- `/static/chpl-base.css`
- `/static/theme.js`

### 12.3 CHPL Branding

**`chpl-variables.css`** — Design token system using CSS custom
properties. Three brand colors (navy `#0C2340`, cream `#F6F1EB`, white
`#FFFFFF`) with a secondary palette (teal, blue, purple, gold, coral).
Defines semantic tokens for light and dark modes.

**`chpl-base.css`** — Applies the semantic tokens to Datasette's HTML
structure. Styles the fixed navy header, body theme switching, tables
(`table.rows-and-columns`), pagination, export links, filter rows,
SQL textarea, message boxes, and cards.

**`theme.js`** — Dark/light theme toggle. Checks `localStorage` for a
saved preference, falls back to `prefers-color-scheme` system setting.
Exposes `window.CHPLTheme` API for programmatic control.

### 12.4 Templates

**`base.html`** — Extends Datasette's `default:base.html`:
- Overrides `{% block crumbs %}` to prepend the CHPL logo and
  "ILS-Reports" site title.
- Includes an anti-FODT (Flash of Default Theme) inline script that
  reads `localStorage` before CSS renders.
- Adds a dark/light toggle button with sun/moon SVG icons.
- Custom footer with CHPL branding, links to chpl.org, GitHub repo,
  and Datasette attribution.

**`index.html`** — Extends `default:index.html`:
- Full-bleed hero section with CHPL logo, "ILS-Reports" heading, and
  tagline.
- Three `.chpl-page-card` links:
  1. Current Collection — Browse bib records, items, holds, circulation
  2. Documentation — Data dictionary, pipeline, schemas
  3. Reports — Curated queries

---

## 13. Deployment

### 13.1 Dockerfile

```dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```

- Installs Datasette and plugins from `requirements-datasette.txt`
  plus `datasette-horizontal-scroll`.
- Copies metadata, config, templates, and static assets.
- The database is **not** baked into the image — it lives on a mounted
  volume at `/data` and is updated nightly by the pipeline.
- Exposes port 8001.

### 13.2 `fly.toml`

| Setting | Value |
|---------|-------|
| App name | `chpl-collection-analysis` |
| Region | `ord` (Chicago) |
| VM memory | 512MB |
| CPU | shared, 1 vCPU |
| Volume | `collection_data` mounted at `/data`, 10GB initial |
| Auto-stop | enabled (scales to zero when idle) |
| HTTPS | forced |

### 13.3 Local development

`scripts/dev-datasette.sh` builds and runs the Datasette container
locally using Podman. Supports `--db PATH`, `--no-rebuild`, and
`--port PORT` flags.

`scripts/datasette.sh` serves `current_collection.db` directly via
`uv run datasette` without containerization. Supports `--dev` mode.

---

## 14. Test Suite

### 14.1 Architecture

- **Unit tests** (`tests/unit/`) — 7 test modules, no external services
  required. Run via `scripts/test.sh`.
- **Integration tests** (`tests/integration/`) — 1 module
  (`test_pipeline.py`), requires a PostgreSQL instance via
  `pytest-postgresql`. Run via `scripts/test.sh --integration`.
- **Coverage gate:** 85% minimum enforced via `[tool.coverage.report]
  fail_under = 85`.

### 14.2 Shared fixtures (`tests/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `tmp_output_dir` | function | Temporary output directory |
| `tmp_sql_dir` | function | Temp dir with `views/` and `indexes/` subdirs |
| `empty_db` | function | Open `sqlite3.Connection` backed by temp file |
| `valid_config` | function | Sets 6 required env vars via `monkeypatch.setenv`, returns config dict |
| `sierra_db` | session | PostgreSQL instance with Sierra schema + seed data (integration only) |
| `sierra_config` | session | Config dict pointing at test PostgreSQL (integration only) |

### 14.3 Unit test modules

**`test_config.py`** (237 lines) — Tests config loading from env vars,
`DeprecationWarning` emission for `config.json`, `.env` auto-loading,
type coercions (port→int, itersize→int, etc.), missing-key validation,
and the `no_dotenv` autouse fixture that patches `load_dotenv` to
prevent real `.env` files from bleeding into tests.

**`test_extract.py`** (631 lines) — Tests all 21 extraction functions.
Uses a mock SQLAlchemy connection that returns predetermined
`RowMapping` objects. Verifies pagination loop advancement (cursor column
updates), non-paginated single-shot returns, and parameter binding
(`_TARGET_DATE`, `id_val`, `limit_val`).

**`test_load.py`** (244 lines) — Tests `open_build_db()` (PRAGMA
application, stale file cleanup), `load_table()` (auto-schema creation,
JSON serialization, date formatting, batch flushing, empty-row
handling), `finalize_db()` (ANALYZE, FINAL_PRAGMAS), and `swap_db()`
(atomic rename).

**`test_run.py`** (214 lines) — Tests pipeline orchestration via
mocking. Verifies the 12-step sequence, `EXTRACT_LIMIT` capping via
`islice`, `PG_SLEEP_BETWEEN_TABLES` sleeping, and error handling in the
`try/finally` block.

**`test_transform.py`** (123 lines) — Tests `create_views()` and
`create_indexes()` with the injected `sql_dir` parameter. Verifies
alphabetical ordering, multi-statement splitting on `;`, and warning
on empty directories.

**`test_telemetry.py`** (166 lines) — Tests the full telemetry lifecycle
(`open_telemetry_db` → `start_run` → `finish_run`), schema creation,
view creation, stage row insertion, and success/failure recording.

**`test_static_assets.py`** (20 lines) — Verifies static asset existence
and basic validity (CSS syntax via `tinycss2`, SVG well-formedness).

### 14.4 Integration tests

**`test_pipeline.py`** (482 lines) — Full end-to-end pipeline tests
against a real PostgreSQL instance loaded with Sierra schema and seed
data from `tests/fixtures/`. Tests extraction, loading, view creation,
and indexing.

### 14.5 `scripts/test.sh` modes

| Invocation | Behavior |
|------------|----------|
| `scripts/test.sh` | Unit tests only |
| `scripts/test.sh --integration` | Integration tests only |
| `scripts/test.sh --all` | All tests |
| `scripts/test.sh --cov` | Unit tests + HTML coverage → `htmlcov/` |

---

## 15. Scripts

The 14 scripts in `scripts/` are grouped by function:

### Pipeline

| Script | Purpose |
|--------|---------|
| `run.sh` | Execute the pipeline via `uv run collection-analysis` |
| `build-sample-db.sh` | Build a small sample database; supports `--limit N` and `--output DIR` |

### Setup

| Script | Purpose |
|--------|---------|
| `setup.sh` | `uv sync --all-extras` + `uv run pre-commit install` |

### QA

| Script | Purpose |
|--------|---------|
| `test.sh` | Run tests (unit/integration/all/coverage) |
| `lint.sh` | Run all linters: ruff, sqlfluff, djlint, tinycss2 |
| `format.sh` | Auto-fix: ruff format + ruff fix + sqlfluff fix |

### Datasette development

| Script | Purpose |
|--------|---------|
| `create-test-db.py` | Create minimal SQLite test DB with sample data |
| `dev-datasette.sh` | Build and run Datasette container locally with Podman |
| `datasette.sh` | Serve DB directly via `uv run datasette` |

### Documentation

| Script | Purpose |
|--------|---------|
| `docs.sh` | Build or serve MkDocs; supports `--serve` and `--with-coverage` |

### Deployment

| Script | Purpose |
|--------|---------|
| `deploy.sh` | Deploy to Fly.io; `--db` flag opens SFTP for DB upload |

### Observability

| Script | Purpose |
|--------|---------|
| `report-runs.py` | Summarize `pipeline_runs.db`; supports `--last-run` and `--markdown` |

### Maintenance

| Script | Purpose |
|--------|---------|
| `clean.sh` | Remove `site/`, `htmlcov/`, `.coverage`, `__pycache__` |

### Planning

| Script | Purpose |
|--------|---------|
| `new-plan.py` | Create numbered planning docs in `llore/` with YAML front-matter |

---

## 16. Build System & Packaging

### 16.1 `pyproject.toml` overview

**Build backend:** `hatchling` — chosen because the project name
(`ils-reports`) differs from the package directory
(`collection_analysis`). The explicit `packages` directive resolves
this:

```toml
[tool.hatch.build.targets.wheel]
packages = ["collection_analysis"]
```

**Console script:**

```toml
[project.scripts]
collection-analysis = "collection_analysis.run:main"
```

### 16.2 Dependencies

**Core:**
- `SQLAlchemy>=2.0` — PostgreSQL connection management
- `psycopg[binary]>=3.1` — PostgreSQL driver (psycopg v3)
- `python-dotenv>=1.0` — `.env` file loading
- `sqlite-fts4==1.0.1` — Full-text search support for SQLite

**Optional extras:**
- `datasette` — `datasette>=1.0a1`, `datasette-leaflet>=0.2`
- `docs` — `mkdocs>=1.5`, `mkdocs-material>=9.5`,
  `mkdocstrings[python]>=0.24`

**Dev dependencies** (PEP 735 `[dependency-groups]`):
- `pytest>=7.4`, `pytest-postgresql>=5.0`, `pytest-cov>=4.1`
- `ruff>=0.4.0`, `sqlfluff>=2.3`
- `pre-commit>=3.6`
- `djlint>=1.34`, `tinycss2>=1.3`
- `genbadge[coverage]>=1.1`

### 16.3 Tool configurations

**ruff** — `target-version = "py310"`, `line-length = 100`. Selects
rules: E/W/F (pyflakes/pycodestyle), I (isort), UP (pyupgrade),
B (bugbear), C4 (comprehensions), SIM (simplify). Ignores E501
(line length — handled by formatter).

**pytest** — `testpaths = ["tests"]`, `addopts = "-v --tb=short"`,
custom `integration` marker.

**sqlfluff** — `dialect = sqlite`, `max_line_length = 150`,
`templater = raw`. Extensive `exclude_rules` for patterns that are
valid in the project's analytical SQL.

**djlint** — `profile = "jinja"`, ignores H006 (img alt), E102 (indent),
J018 (url tag), J004 (inner url).

**coverage** — `source = ["collection_analysis"]`, `fail_under = 85`,
excludes `pragma: no cover`, `if __name__`, `raise NotImplementedError`.

---

## 17. Code Quality & Pre-commit

`.pre-commit-config.yaml` defines 11 hooks across 5 repositories:

### pre-commit/pre-commit-hooks (v4.6.0)

1. **trailing-whitespace** — Strips trailing whitespace.
2. **end-of-file-fixer** — Ensures files end with a newline.
3. **check-yaml** — Validates YAML syntax.
4. **check-json** — Validates JSON syntax.
5. **mixed-line-ending** — Enforces LF line endings (`--fix=lf`).

### astral-sh/ruff-pre-commit (v0.4.7)

6. **ruff** — Lints Python with auto-fix (`--fix`).
7. **ruff-format** — Formats Python code.

### sqlfluff/sqlfluff (v2.3.5)

8. **sqlfluff-lint** — Lints SQL files in `sql/`.
9. **sqlfluff-fix** — Auto-fixes SQL files in `sql/` (`--force`).

### Yelp/detect-secrets (v1.5.0)

10. **detect-secrets** — Scans for secrets against
    `.secrets.baseline`.

### Local hooks

11. **djlint** — Lints Jinja templates in `datasette/templates/`.

### `.secrets.baseline`

The `detect-secrets` baseline file configures 27 detectors and
allowlists 4 placeholder values (from `.env.sample` and
`config.json.sample`). It is verified in CI via the `security` job.

---

## 18. CI/CD

### GitHub Actions: `.github/workflows/ci.yml`

Triggers on push to `main` and on all pull requests.

**Job 1: `unit-tests`**

- Runs on `ubuntu-latest`.
- Python version matrix: 3.10, 3.11, 3.12, 3.13.
- Steps: checkout → setup uv (with cache) → `uv sync --all-extras`
  → `scripts/test.sh --cov`.
- Uploads `htmlcov/` as an artifact per Python version.

**Job 2: `security`**

- Runs on `ubuntu-latest`.
- Steps: checkout → setup uv → runs `detect-secrets scan --baseline
  .secrets.baseline`.
- Ensures no new secrets are introduced.

### Branch protection on `main`

| Rule | Setting |
|------|---------|
| Required checks | `unit-tests` (3.10, 3.11, 3.12, 3.13) + `security` |
| Strict | Branch must be up-to-date before merge |
| Linear history | Enforced (squash merge only) |
| Force pushes | Blocked |
| `enforce_admins` | Off (emergency bypass available) |

---

## 19. Git Workflow

### Branch → PR → squash-merge

All non-trivial work goes through a branch and pull request. PRs are
squash-merged into `main` to keep the history linear and each entry
meaningful.

### Branch naming

| Prefix | Purpose |
|--------|---------|
| `feat/` | New feature or capability |
| `fix/` | Bug fix |
| `chore/` | Maintenance, deps, tooling |
| `docs/` | Documentation only |
| `ci/` | CI/CD changes |
| `security/` | Security hardening |

### Commit discipline

- One logical change per commit.
- Subject line: `<type>: <what changed>` (50 chars or less).
- Body (if needed): explain *why*, not *what*. Wrap at 72 chars.
- Do not bundle unrelated changes.

### Squash commit message

Summarises the entire branch in the same `<type>: ...` format.
The branch is deleted after merge.

---

## 20. Performance Engineering

### 20.1 SQLite BUILD_PRAGMAS rationale

| PRAGMA | Why |
|--------|-----|
| `page_size=8192` | 8KB is empirically fastest for row-based tabular data. Must be set before any `CREATE TABLE`. |
| `journal_mode=OFF` | Eliminates rollback journal overhead. Safe because the build file is disposable. |
| `synchronous=OFF` | Eliminates `fsync()` calls. Safe because we only swap on success. |
| `cache_size=-2000000` | 2GB page cache reduces I/O during bulk inserts. |
| `temp_store=MEMORY` | Temporary tables and indexes in RAM. |
| `mmap_size=30000000000` | ~30GB memory-mapped I/O for read-ahead during index creation. |
| `locking_mode=EXCLUSIVE` | No reader contention during the build phase. |

### 20.2 Cursor vs. OFFSET pagination

The paginated extraction functions use **cursor-based pagination**
(`WHERE id > :id_val ORDER BY id ASC LIMIT :limit_val`) rather than
`OFFSET`-based pagination. Cursor pagination is O(1) per page because
the database uses the primary key index to seek directly to the start
of the next page. `OFFSET` is O(n) because the database must scan and
discard all preceding rows.

### 20.3 Tuning knobs

| Knob | Env var | Default | Effect |
|------|---------|---------|--------|
| Fetch size | `PG_ITERSIZE` | 15000 | Rows per PostgreSQL round-trip. Fewer round-trips = less query-planner overhead on Sierra. Safe range: 5000–50000. |
| Inter-table sleep | `PG_SLEEP_BETWEEN_TABLES` | 0.0 | Seconds to pause between tables. Reduces load on Sierra during business hours. |
| Extract cap | `EXTRACT_LIMIT` | 0 | Caps each table at N rows for fast sample builds. 0 = no limit. |
| Batch size | `batch_size` param | 5000 | Rows per `executemany()` call + `commit()` in `load_table()`. |

### 20.4 `report-runs.py`

The `scripts/report-runs.py` script reads `pipeline_runs.db` and
displays stage-by-stage timing data. Use `--last-run` for the most
recent run or `--markdown` for formatted output. This is the primary
tool for bottleneck analysis.

### 20.5 Related planning documents

- `llore/001-pipeline-performance.md` — Analysis of PostgreSQL
  round-trip and SQLite write overhead; implementation of tuning knobs.
- `llore/002-extraction-bottlenecks.md` — Analysis of `circ_agg` and
  `item_message` extraction bottlenecks; deferred investigation plan.

---

## 21. Security

### 21.1 Credential management

- `.env` is gitignored — never committed.
- `.env.sample` uses placeholder values (`your-sierra-host.example.com`,
  `USERNAME`, `PASSWORD`).
- Internal hostnames were redacted from all sample files.

### 21.2 Secret scanning

- **Pre-commit hook:** `detect-secrets v1.5.0` scans against
  `.secrets.baseline` (27 detectors, 4 allowlisted placeholders).
- **CI job:** The `security` job in GitHub Actions runs the same scan.
- Both must pass before merging to `main`.

### 21.3 Licensing

- **Source code:** MIT License (`LICENSE` at root).
- **Data:** CC-BY-4.0 (declared in `metadata.yml`). This reflects
  CHPL's policy for publicly sharing library data.

---

## 22. Design Decisions Summary

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **Full rebuild every run** | Simpler than incremental CDC; Sierra `sierra_view` is read-only; pipeline runtime is acceptable. | Longer pipeline runs; more PG load per execution. |
| **Atomic swap (`os.replace`)** | Readers never see a partial database; failure leaves live DB untouched. | Requires 2× disk space during build; WAL sidecar files from `finalize_db()` may be orphaned (see llore/003). |
| **Deferred index creation** | Creating indexes after all rows are loaded is dramatically faster than maintaining them during inserts. | Views that reference indexed columns don't benefit during the build phase. |
| **Plain SQL files (no dbt, no ORM)** | Minimal tooling; SQL is version-controlled and lintable; easy for SQL-literate staff to review. | No dependency tracking between views (handled by numeric prefixes). |
| **Env-first config (deprecated JSON)** | Environment variables are the 12-factor standard; `.env` files integrate with all tooling. | Legacy users must migrate from `config.json`. |
| **Cursor-based pagination** | O(1) per page via index seek; no row-skipping overhead; no OFFSET. | Requires a unique, indexed ID column in every paginated query. |
| **`_TARGET_DATE = "1969-01-01"`** | Sentinel date guaranteed to predate all Sierra records; avoids the need for a separate "full extract" code path. | Slightly unusual convention; may confuse new developers unfamiliar with it. |
| **Persistent telemetry DB** | Accumulates run history for trend analysis; never wiped; survives failed runs. | Extra DB file to manage; not yet served via Datasette. |
| **Fly.io deployment** | Simple container hosting; auto-stop scales to zero; built-in volumes for DB storage. | Vendor lock-in for deployment; cold-start latency when auto-stopped. |
| **CHPL CSS design tokens** | Brand-compliant theming without forking Datasette; tokens enable dark/light mode; consistent across pages. | Coupled to Datasette 1.0a24 HTML structure; may break with Datasette updates. |
| **hatchling build backend** | Handles the mismatch between project name (`ils-reports`) and package directory (`collection_analysis`) via explicit `packages` directive. | Less common than setuptools; smaller ecosystem. |
| **PEP 735 dependency groups** | `[dependency-groups] dev = [...]` is the modern standard for dev dependencies; replaces deprecated `[tool.uv.dev-dependencies]`. | Requires uv ≥0.5 or compatible tooling. |
| **Python ≥3.10 minimum** | Required by `pre-commit>=3.6`; enables `match` statements and `X | Y` union types. | Excludes Python 3.9 and earlier. |
| **uv as project manager** | Fast dependency resolution, lockfile generation, virtualenv creation, and script running. | Relatively new tool; team must learn uv-specific commands. |

---

## Appendix A: SQL View Catalog

| # | Filename | View Name | Purpose | Base Tables | Notable Techniques |
|---|----------|-----------|---------|-------------|--------------------|
| 1 | `01_isbn_view.sql` | `isbn_view` | Extract individual ISBNs from JSON array, link to items | bib, item | JSON_EACH, LEFT OUTER JOIN |
| 2 | `02_duplicate_items_in_location_view.sql` | `duplicate_items_in_location_view` | Identify duplicate available items by location, bib, and volume | item, bib_record_item_record_link | CTE, COUNT > 1, JSON_GROUP_ARRAY |
| 3 | `03_location_view.sql` | `location_view` | Map location codes to branch names with hyperlinks | location, location_name, branch, branch_name | JSON_OBJECT, multiple INNER JOINs |
| 4 | `04_item_view.sql` | `item_view` | Comprehensive item catalog with bib, location, branch, status | item, bib, location, location_name, branch, branch_name, item_status_property | COALESCE, multiple LEFT OUTER JOINs |
| 5 | `05_branch_30_day_circ_view.sql` | `branch_30_day_circ_view` | 30-day circulation checkouts/check-ins by branch | circ_agg, branch_locations | CTE, CASE, JSON_GROUP_OBJECT, JULIANDAY |
| 6 | `06_branch_location_view.sql` | `branch_location_view` | Map locations to branches with item-view URLs | location, location_name, branch, branch_name | String concatenation, LEFT OUTER JOINs |
| 7 | `07_collection_value_branch_view.sql` | `collection_value_branch_view` | Collection value (count + price sum) by branch/location/format | item, location, location_name, branch, branch_name | GROUP BY, SUM |
| 8 | `08_hold_view.sql` | `hold_view` | Comprehensive hold data with title, location, patron, dates | hold, bib, volume_record, location, location_name, branch, branch_name | Scalar subquery, CASE, multiple LEFT OUTER JOINs |
| 9 | `09_hold_title_view.sql` | `hold_title_view` | Group active holds by title with item counts | hold, bib, volume_record, item, volume_record_item_record_link | Multiple CTEs, nested CASE, scalar subqueries |
| 10 | `10_leased_item_view.sql` | `leased_item_view` | Filter items with barcode prefix `'L'` (leased items) | item, item_status_property, bib | CTE, barcode range comparison, LEFT JOIN |
| 11 | `11_ld_compare_view.sql` | `ld_compare_view` | Compare Lucky Day vs. non-leased checkout rates | item, bib | Nested CTEs, LIKE pattern matching, ROUND |
| 12 | `12_location_percent_checkout_view.sql` | `location_percent_checkout_view` | Percentage of items checked out by location | item, location, location_name, branch, branch_name | CTE, COUNT, ROUND percentage |
| 13 | `13_book_connections_view.sql` | `book_connections_view` | Group items by title/author/location/format, total circulation | item, bib | CTE, JSON_EXTRACT, IN clause, SUM |
| 14 | `14_two_months_leased_item_view.sql` | `two_months_leased_item_view` | Leased item circulation within 2 months of earliest circ date | item, circ_leased_items, bib | Nested CTEs, date math with modifiers |
| 15 | `15_new_downloadable_book_view.sql` | `new_downloadable_book_view` | Downloadable books added in last 60 days with cover images | item_view, bib | JSON_OBJECT, JSON_EXTRACT, date range |
| 16 | `16_new_titles_view.sql` | `new_titles_view` | Titles cataloged in last 30 days with cover images | bib, item | JSON_OBJECT, JSON_EXTRACT, scalar subquery |
| 17 | `17_last_copy_view.sql` | `last_copy_view` | Last available copy of titles at a location | item, bib, branch_location_view | CTE, HAVING COUNT = 1, JSON_OBJECT |
| 18 | `18_dup_at_location_view.sql` | `dup_at_location_view` | Detailed duplicate items at same location | bib, item | CTE, HAVING COUNT > 1, JSON_GROUP_ARRAY |
| 19 | `19_active_holds_view.sql` | `active_holds_view` | Filter to currently active holds (not frozen, valid ptype) | hold, record_metadata | CTE, IN clause, JULIANDAY |
| 20 | `20_active_items_view.sql` | `active_items_view` | Filter items with active status codes | item, volume_record_item_record_link, record_metadata | CTE, IN clause, COALESCE, date math |
| 21 | `21_item_in_transit_view.sql` | `item_in_transit_view` | Items in transit with hold and overdue details | item, hold, item_message | Multiple INNER JOINs, DATE conversion |
| 22 | `22_circ_agg_branch_view.sql` | `circ_agg_branch_view` | Monthly circulation by branch and item type | circ_agg, itype_property | CTE, STRFTIME, CASE, self-join pattern |
| 23 | `23_duplicate_items_2ra_2rabi.sql` | `duplicate_items_2ra_2rabi` | Duplicate items at locations 2ra and 2rabi | bib, item | CTE, JSON_GROUP_ARRAY, location filtering |
| 24 | `24_duplicate_items_3ra_2rabi.sql` | `duplicate_items_3ra_2rabi` | Duplicate items at locations 3ra and 2rabi | bib, item | CTE, JSON_GROUP_ARRAY, location filtering |
| 25 | `25_collection_detail_view.sql` | `collection_detail_view` | Low-level detail with all bib record codes and computed names | bib_record, record_metadata, item, location, location_name, branch, branch_name | CTE, scalar subqueries, multiple LEFT JOINs |
| 26 | `26_genre_view.sql` | `genre_view` | Genre counts from JSON array with search links | bib | JSON_EACH, JSON_OBJECT, COUNT |

---

## Appendix B: Extraction Function Catalog

| Function | Target table | Pagination | Cursor column | Query features |
|----------|-------------|------------|---------------|----------------|
| `extract_record_metadata` | `record_metadata` | paginated | `record_id` | CTE for ID page; Julian day conversion; filters record types `b`, `i`, `j` |
| `extract_bib` | `bib` | paginated | `bib_record_id` | Most complex query; `json_agg` for control numbers, ISBNs, subjects, genres, item types; `regexp_matches` for ISBN extraction; scalar subqueries for publisher and call number |
| `extract_item` | `item` | paginated | `item_record_id` | Joins to bib, checkout, volume, and format lookup tables |
| `extract_bib_record` | `bib_record` | paginated | `id` | MARC-level bib metadata (bcode1–bcode3, language, country, cataloging date) |
| `extract_volume_record` | `volume_record` | paginated | `volume_record_id` | Volume records with bib linkage and Julian day creation date |
| `extract_item_message` | `item_message` | paginated | `varfield_id` | In-transit and status message fields from varfield; no `_TARGET_DATE` |
| `extract_bib_record_item_record_link` | `bib_record_item_record_link` | paginated | `id` | Many-to-many bib↔item link; no `_TARGET_DATE` |
| `extract_volume_record_item_record_link` | `volume_record_item_record_link` | paginated | `id` | Many-to-many volume↔item link; no `_TARGET_DATE` |
| `extract_hold` | `hold` | paginated | `hold_id` | Active holds with patron metadata |
| `extract_circ_leased_items` | `circ_leased_items` | paginated | `id` | Checkout/checkin activity for leased items (last 180 days) |
| `extract_language_property` | `language_property` | non-paginated | — | Lookup table: language code → name |
| `extract_location` | `location` | non-paginated | — | Lookup table: location codes, branch linkage, requestable flag |
| `extract_location_name` | `location_name` | non-paginated | — | Lookup table: location ID → display name |
| `extract_branch_name` | `branch_name` | non-paginated | — | Lookup table: branch ID → display name |
| `extract_branch` | `branch` | non-paginated | — | Lookup table: branch code and metadata |
| `extract_country_property_myuser` | `country_property_myuser` | non-paginated | — | Lookup table: country codes |
| `extract_item_status_property` | `item_status_property` | non-paginated | — | Lookup table: item status code → description |
| `extract_itype_property` | `itype_property` | non-paginated | — | Lookup table: item type code → format name |
| `extract_bib_level_property` | `bib_level_property` | non-paginated | — | Lookup table: bib level codes |
| `extract_material_property` | `material_property` | non-paginated | — | Lookup table: material type codes |
| `extract_circ_agg` | `circ_agg` | non-paginated | — | Aggregated circulation transactions (last 6 months); server-side aggregation; known bottleneck (see llore/002) |
