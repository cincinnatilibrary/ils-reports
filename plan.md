# Collection Analysis Pipeline — Plan

> **Goal:** Take the existing notebook and make it more efficient, maintainable, and robust.
> Incremental improvements — not a redesign. Keep it simple.

---

## Decisions (from Q&A)

| Question | Decision |
|---|---|
| SQL transform tooling | Pure Python — SQL views in `.sql` files, no dbt |
| Where pipeline runs | Local for now, deployment out of scope for this stage |
| Daily/weekly incremental mode | Drop it for now — focus on making full rebuild faster |
| Scheduler | cron (local); revisit systemd timer if pipeline moves to server |
| New repo name | `ils-reports` (private to start, public later) |
| This repo | Leave as-is; add README note pointing to new repo when ready |
| Documentation | Add a data dictionary for the SQLite views/tables |

---

## What We're Building

A new private repo (`ils-reports`) that contains the collection analysis pipeline
as a proper Python project — extracted from the notebook, structured for
maintainability, and optimized for faster full rebuilds.

### Repo structure

```
ils-reports/
├── collection_analysis/
│   ├── __init__.py
│   ├── config.py          # Load and validate config.json
│   ├── extract.py         # All Sierra PostgreSQL queries
│   ├── load.py            # Bulk-write tables into SQLite
│   ├── transform.py       # Read + execute .sql files (views, indexes)
│   └── run.py             # Entry point: `python -m collection_analysis.run`
├── sql/
│   ├── views/             # One .sql file per view (e.g. item_view.sql)
│   └── indexes/           # Index definitions
├── docs/
│   └── data_dictionary.md # What each table/view contains and why
├── config.json.sample
├── requirements.txt
└── README.md
```

---

## Performance: Making Full Rebuilds Faster

The full rebuild currently takes ~6 hours even on a server local to Sierra.
The main levers to pull, roughly in order of expected impact:

### 1. SQLite write optimizations (biggest win, essentially free)

Apply these PRAGMAs before bulk-loading data:

```sql
PRAGMA journal_mode = OFF;     -- or WAL; OFF is fastest for a clean build
PRAGMA synchronous = OFF;      -- skip fsync during build (safe if we swap atomically)
PRAGMA cache_size = -2000000;  -- 2GB page cache
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 30000000000;
PRAGMA locking_mode = EXCLUSIVE;
```

Re-enable WAL and normal sync after the build is done and before the swap.
These settings alone can cut SQLite write time dramatically.

### 2. Build to a temp file, then atomic swap

Instead of writing to `current_collection.db` directly:

```
Build → current_collection.db.new
When done → mv current_collection.db.new current_collection.db  (atomic)
```

This means: if the build fails partway through, the existing DB is untouched.
No corrupt half-built database on the server.

### 3. Defer all index creation until after all data is loaded

The current notebook interleaves table creation and indexing. Creating indexes
on a populated table is far faster than maintaining them incrementally during
inserts. All `CREATE INDEX` statements should run as a final step after every
table is loaded.

### 4. Tune the PostgreSQL fetch (itersize)

The current `itersize=5000` controls how many rows are fetched per round-trip
from Sierra. Increasing this (e.g. 10000–50000) reduces round-trips for large
tables. Worth profiling to find the sweet spot — too large uses more memory.

### 5. Profile where the 6 hours actually goes

Before optimizing further, add timing around each table extraction so we know
which tables are the bottleneck. It's very likely that 80% of the time is spent
on 2-3 large tables. That tells us where to focus.

---

## Migration Plan (step by step)

1. **Create `ils-reports` repo** (private, under `cincinnatilibrary` org)
2. **Set up Python project structure** — `pyproject.toml`, `requirements.txt`, module skeleton
3. **Extract config logic** — `config.py` reads `config.json`, same format as current
4. **Extract SQL views** — move each view definition from the notebook into its own `.sql` file under `sql/views/`
5. **Extract extraction queries** — Sierra PostgreSQL queries into `extract.py` as functions
6. **Build `load.py`** — bulk-insert logic with SQLite optimizations from above
7. **Build `transform.py`** — reads and executes `.sql` files for views and indexes
8. **Build `run.py`** — ties it all together with timing/logging, builds to temp file, swaps when done
9. **Write `docs/data_dictionary.md`** — document each table and view
10. **Test against Sierra** — run it, compare output to existing notebook output
11. **Replace the cron job** — point the existing cron at `run.py` instead of the notebook

---

## Out of Scope (for now)

- Incremental / daily update mode (save for a future stage)
- Moving the pipeline to the remote server
- GitHub Actions
- dbt
- Cleaning up this (`collection-analysis`) repo
