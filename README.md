# ils-reports

![Coverage](coverage-badge.svg)
[![CI](https://github.com/cincinnatilibrary/ils-reports/actions/workflows/ci.yml/badge.svg)](https://github.com/cincinnatilibrary/ils-reports/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%E2%80%93%203.13-blue)

Data pipelines from the Cincinnati & Hamilton County Public Library (CHPL)
Sierra ILS (PostgreSQL) to SQLite databases for reporting and public analysis.
Nightly, the pipeline queries Sierra's PostgreSQL `sierra_view` schema, loads
21 tables into a fresh SQLite database, creates 26 analytical views and 40+
indexes, and atomically swaps the result into place.

## Live site

**[https://collection-analysis.cincy.pl/](https://collection-analysis.cincy.pl/)**

## Architecture

The `collection_analysis` package builds `current_collection.db` — a SQLite
snapshot of the CHPL collection served publicly via Datasette.

| Module | Purpose |
|---|---|
| `config.py` | Loads env vars (`.env` via python-dotenv) or deprecated `config.json`; builds SQLAlchemy PostgreSQL URL |
| `extract.py` | Queries Sierra `sierra_view`; yields 21 row generators (bib, item, hold, circ_agg, location lookups, …) |
| `load.py` | Opens temp `*.db.new` with aggressive write PRAGMAs; bulk-inserts rows; finalizes; atomic `os.replace()` swap |
| `transform.py` | Executes `.sql` files from `sql/views/` and `sql/indexes/` in alphabetical order |
| `run.py` | Orchestrates the full pipeline; records per-stage timing; supports `EXTRACT_LIMIT` for sample builds |
| `telemetry.py` | Persists run + stage stats to `pipeline_runs.db` for post-build analysis |

## Setup

```bash
git clone https://github.com/cincinnatilibrary/ils-reports.git
cd ils-reports
scripts/setup.sh   # uv sync --all-extras + pre-commit install
cp .env.sample .env
# edit .env with Sierra credentials and OUTPUT_DIR
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `PG_HOST` | ✓ | — | Sierra PostgreSQL host |
| `PG_PORT` | ✓ | — | PostgreSQL port (typically 1032) |
| `PG_DBNAME` | ✓ | — | Database name |
| `PG_USERNAME` | ✓ | — | PostgreSQL username |
| `PG_PASSWORD` | ✓ | — | PostgreSQL password |
| `OUTPUT_DIR` | ✓ | — | Directory where `current_collection.db` is written |
| `PG_SSLMODE` | | `require` | PostgreSQL SSL mode |
| `PG_ITERSIZE` | | `15000` | Server-side cursor fetch size (5000–50000) |
| `PG_SLEEP_BETWEEN_TABLES` | | `0.0` | Seconds to sleep between extractions (throttle Sierra load) |
| `LOG_LEVEL` | | `INFO` | `DEBUG`, `INFO`, or `WARNING` |
| `LOG_FILE` | | — | Optional path for file logging |
| `EXTRACT_LIMIT` | | `0` | Cap each table at N rows; `0` = no limit (sample builds only) |

## Running the pipeline

### Full production build

```bash
scripts/run.sh
# or:
uv run collection-analysis
```

### Sample build

```bash
scripts/build-sample-db.sh --limit 500 --output ./out
```

## Tests & linting

```bash
scripts/test.sh            # 146 unit tests (no PostgreSQL required)
scripts/test.sh --all      # + integration tests (requires PostgreSQL)
scripts/test.sh --cov      # + HTML coverage report → htmlcov/
scripts/lint.sh            # ruff + sqlfluff + djlint + CSS
scripts/format.sh          # auto-fix
```

CI runs `test.sh --cov` against Python 3.10–3.13; 85% coverage enforced.

## Project structure

```
ils-reports/
├── collection_analysis/   Python pipeline package (config, extract, load, transform, run, telemetry)
├── sql/
│   ├── views/             26 SQL view files (01_isbn_view.sql … 26_genre_view.sql)
│   ├── indexes/           01_indexes.sql (40+ CREATE INDEX statements)
│   └── queries/           Reference extraction queries
├── docs/                  MkDocs documentation (mkdocs.yml at root)
├── datasette/             Datasette config, branded templates, Fly.io deployment
├── tests/
│   ├── unit/              7 test modules, 146 tests (no PostgreSQL required)
│   ├── integration/       End-to-end tests (requires PostgreSQL)
│   └── fixtures/          Sierra schema + seed SQL
├── scripts/               Shell scripts for setup, run, test, lint, deploy, sample build
├── llore/                 Planning and design decision records
├── reference/             Original reference notebook (read-only)
├── .env.sample            Environment variable template
├── pyproject.toml
└── uv.lock
```

## Documentation

Full documentation is built with MkDocs Material and lives in `docs/`. Run
`scripts/docs.sh --serve` to browse locally. Topics: pipeline architecture,
all configuration options, data dictionary, table/view reference, and
development guide.

## Deployment

```bash
scripts/deploy.sh          # deploys Datasette to Fly.io (app: chpl-collection-analysis)
scripts/deploy.sh --db     # uploads current_collection.db via SFTP
```

## License

[MIT](LICENSE) — Copyright (c) 2026 Cincinnati & Hamilton County Public Library

## Related repos

- [`cincinnatilibrary/collection-analysis`](https://github.com/cincinnatilibrary/collection-analysis)
  — Datasette server config, Sphinx docs, and historical exploration notebooks
