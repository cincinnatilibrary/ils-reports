# Development

## Setup

```bash
git clone https://github.com/cincinnatilibrary/ils-reports
cd ils-reports

# Install uv if you don't have it:
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all deps (core + dev + docs + datasette) and pre-commit hooks
scripts/setup.sh
```

`uv sync` creates `.venv/` automatically and generates/updates `uv.lock`. You
do not need to activate the venv — prefix commands with `uv run` or use the
scripts in `scripts/`.

---

## Scripts

| Script | Flags | What it does |
|---|---|---|
| `scripts/setup.sh` | | Install all deps + pre-commit hooks |
| `scripts/run.sh` | | Run the pipeline (checks for `config.json`) |
| `scripts/lint.sh` | | Run `ruff check`, `sqlfluff lint`, `djlint`, CSS lint |
| `scripts/format.sh` | | Auto-format Python with `ruff format` + fix SQL with `sqlfluff fix` |
| `scripts/test.sh` | | Unit tests (no PostgreSQL required) |
| `scripts/test.sh` | `--integration` | Integration tests (requires PostgreSQL) |
| `scripts/test.sh` | `--all` | All tests |
| `scripts/test.sh` | `--cov` | Unit tests with HTML coverage report → `htmlcov/` |
| `scripts/docs.sh` | | Build MkDocs site → `site/` |
| `scripts/docs.sh` | `--serve` | Serve docs locally at `http://127.0.0.1:8000` |
| `scripts/datasette.sh` | | Serve `current_collection.db` via Datasette on port 8001 |
| `scripts/datasette.sh` | `--dev` | Same with `--reload` |
| `scripts/datasette.sh` | `--db PATH` | Serve a custom DB path |
| `scripts/deploy.sh` | | Deploy Datasette to Fly.io via `flyctl` |
| `scripts/deploy.sh` | `--db` | Open SFTP shell to upload the database |
| `scripts/clean.sh` | | Remove build artifacts (`site/`, `htmlcov/`, `.coverage`, caches) |

---

## Running the pipeline

```bash
# Uses config.json in the project root
scripts/run.sh

# Or with a custom config path
uv run python -m collection_analysis.run --config /path/to/config.json
```

---

## Tests

Unit tests have no external dependencies:

```bash
scripts/test.sh
# or
pytest tests/unit/ -v
```

Integration tests require a running PostgreSQL instance (managed automatically
by `pytest-postgresql`):

```bash
scripts/test.sh --integration
# or
pytest tests/ -m integration -v
```

Coverage report:

```bash
scripts/test.sh --cov
open htmlcov/index.html
```

---

## Linting

`ruff` handles Python formatting and linting; `sqlfluff` handles SQL files in
`sql/views/` and `sql/indexes/`.

```bash
scripts/lint.sh    # check only
scripts/format.sh  # auto-fix
```

Pre-commit hooks run both automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

---

## Adding a new extraction function

1. Add the query to `collection_analysis/extract.py` following the naming
   convention `extract_<table_name>()`.
2. Reference `reference/collection-analysis.cincy.pl_gen_db.ipynb` for the
   authoritative Sierra query.
3. Wire up the call in `run.py`.
4. Add a corresponding integration test in `tests/integration/test_pipeline.py`.

## Adding a new view or index

1. Create a `.sql` file in `sql/views/` or `sql/indexes/`.
2. Use a numeric prefix if ordering matters: `01_item_view.sql`.
3. The file may contain multiple statements separated by semicolons.
4. `scripts/lint.sh` will check it with `sqlfluff`.

---

## Datasette (local)

After running the pipeline to produce `current_collection.db`:

```bash
scripts/datasette.sh        # production config, port 8001
scripts/datasette.sh --dev  # same + auto-reload on config change
```

See `datasette/metadata.yml` for canned queries and column descriptions.
