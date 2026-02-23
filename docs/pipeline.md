# Pipeline Architecture

## Overview

The pipeline lives in `collection_analysis/` and has four modules:

| Module | Responsibility |
|---|---|
| `config.py` | Load and validate `config.json` |
| `extract.py` | Query Sierra PostgreSQL, yield rows |
| `load.py` | Write rows to SQLite with optimised PRAGMAs |
| `transform.py` | Execute SQL view/index files after loading |
| `run.py` | Orchestrate all four stages |

---

## Execution flow

```
run.main()
  ├── config.load()              → cfg dict
  ├── load.open_build_db()       → sqlite_utils.Database (*.db.new)
  ├── extract.*()                → row iterators
  ├── load_table() × N           → INSERT rows into SQLite
  ├── transform.create_views()   → execute sql/views/*.sql
  ├── transform.create_indexes() → execute sql/indexes/*.sql
  ├── load.finalize_db()         → ANALYZE + safe PRAGMAs
  └── load.swap_db()             → os.replace(*.db.new → *.db)
```

---

## Key design decisions

### No incremental updates

The pipeline always rebuilds the full database from scratch. Sierra does not
expose a reliable change feed, and a nightly full rebuild keeps the logic
simple and the output deterministic.

### Atomic swap pattern

The pipeline writes to `current_collection.db.new` throughout the build.
Only on success does it call `os.replace()` to move the new file over the
live one. If the pipeline fails at any point, the live database is left
untouched.

### Aggressive write PRAGMAs during build

`load.open_build_db()` applies:

| PRAGMA | Value | Reason |
|---|---|---|
| `journal_mode` | `OFF` | No rollback journal needed during a clean build |
| `synchronous` | `OFF` | Skip fsync — safe because we swap atomically |
| `cache_size` | `-2000000` (2 GB) | Large in-memory page cache |
| `temp_store` | `MEMORY` | Keep temp tables in RAM |
| `mmap_size` | `30000000000` | Memory-map the DB file |
| `locking_mode` | `EXCLUSIVE` | Single writer, no contention |

After the build, `load.finalize_db()` re-applies `journal_mode=WAL` and
`synchronous=NORMAL` so Datasette can read the file safely with multiple
readers.

### Deferred index creation

All `CREATE INDEX` statements in `sql/indexes/` run **after** all tables have
been populated. Maintaining indexes during bulk inserts is an order of
magnitude slower; deferring them means each index is built in a single fast
pass.

### SQL files control ordering

View and index SQL files are executed in alphabetical order within their
directory. Use numeric prefixes when order matters:

```
sql/views/01_item_view.sql
sql/views/02_isbn_view.sql
sql/indexes/01_item_location.sql
```

---

## Module API

::: collection_analysis.config
::: collection_analysis.load
::: collection_analysis.transform
::: collection_analysis.extract
