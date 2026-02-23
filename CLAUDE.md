# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data pipeline from the Cincinnati & Hamilton County Public Library (CHPL) Sierra ILS (PostgreSQL) to SQLite databases for reporting and public analysis. The `collection_analysis` pipeline builds `current_collection.db`, a SQLite snapshot of the CHPL collection served via Datasette at https://collection-analysis.cincy.pl/

## Setup

```bash
# Install uv if needed: https://docs.astral.sh/uv/getting-started/installation/
uv sync --all-extras       # creates .venv, installs all deps, generates uv.lock
uv run pre-commit install  # install git hooks
cp config.json.sample config.json
# edit config.json with Sierra credentials and output_dir
```

## Running the Pipeline

```bash
uv run python -m collection_analysis.run
uv run python -m collection_analysis.run --config /path/to/config.json
# or via console script:
uv run collection-analysis
```

## Tests & Linting

```bash
make test       # unit tests (no PostgreSQL required)
make lint       # ruff + sqlfluff
make format     # auto-fix
```

## Architecture

The pipeline has four core modules in `collection_analysis/`:

- **`config.py`** — Loads/validates `config.json`; builds the SQLAlchemy PostgreSQL connection URL from Sierra credentials.
- **`extract.py`** — Queries Sierra's `sierra_view` PostgreSQL schema and yields rows. Currently a skeleton; extraction functions need to be ported from `reference/collection-analysis.cincy.pl_gen_db.ipynb`.
- **`load.py`** — Manages the SQLite build lifecycle: opens a temp `*.db.new` file with aggressive write-speed PRAGMAs (`journal_mode=OFF`, `synchronous=OFF`, 2GB cache), finalizes with WAL/NORMAL PRAGMAs, then atomically swaps `*.db.new` → `*.db` via `os.replace()`. This keeps the live DB untouched if the build fails.
- **`transform.py`** — Creates SQLite views and indexes by executing `.sql` files from `sql/views/` and `sql/indexes/` in alphabetical order. Indexes are deferred until after all tables are loaded.
- **`run.py`** — Orchestrates the full pipeline: load config → open build DB → extract → create views → create indexes → finalize → atomic swap.

## Key Design Decisions (see `plan.md` for details)

- **No incremental updates** — pipeline always rebuilds the full DB from scratch.
- **Atomic swap pattern** — build to `current_collection.db.new`, swap only on success.
- **Index creation deferred** — all indexes created after tables are populated (far faster than maintaining during inserts).
- **SQL files control view/index order** — use numeric prefixes (e.g., `01_item_view.sql`) when ordering matters.
- **No dbt, no ORM for transforms** — plain SQL files in `sql/views/` and `sql/indexes/`.

## Reference Material

`reference/collection-analysis.cincy.pl_gen_db.ipynb` is the authoritative source for all Sierra extraction queries and the full list of tables/views to implement. Use it when porting logic into `extract.py` and the `sql/` directories.

## Configuration

`config.json` (gitignored) follows the shape of `config.json.sample`. Key fields:

| Field | Purpose |
|---|---|
| `pg_host`, `pg_port`, `pg_dbname` | Sierra PostgreSQL connection |
| `pg_username`, `pg_password` | Sierra credentials |
| `pg_sslmode` | Default `"require"` |
| `pg_itersize` | Server-side cursor fetch size (default 5000; increase to 10000–50000 to reduce round-trips) |
| `output_dir` | Directory where `current_collection.db` is written |
