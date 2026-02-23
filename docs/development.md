# Development

## Setup

```bash
git clone https://github.com/cincinnatilibrary/ils-reports
cd ils-reports

# Install uv if you don't have it:
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all deps (core + dev + docs + datasette) and pre-commit hooks
make install-dev
# equivalent to: uv sync --all-extras && uv run pre-commit install
```

`uv sync` creates `.venv/` automatically and generates/updates `uv.lock`. You
do not need to activate the venv — prefix commands with `uv run` or use the
`make` targets.

---

## Make targets

| Target | What it does |
|---|---|
| `make install-dev` | Install package in editable mode with all extras; install pre-commit hooks |
| `make lint` | Run `ruff check` on Python + `sqlfluff lint` on SQL |
| `make format` | Auto-format Python with `ruff format` + fix SQL with `sqlfluff fix` |
| `make test` | Run unit tests (no PostgreSQL required) |
| `make test-integration` | Run integration tests (requires PostgreSQL) |
| `make test-all` | Run all tests |
| `make test-cov` | Unit tests with HTML coverage report → `htmlcov/` |
| `make docs` | Build MkDocs site → `site/` |
| `make docs-serve` | Serve docs locally at `http://127.0.0.1:8000` |
| `make datasette` | Serve `current_collection.db` via Datasette on port 8001 |
| `make datasette-dev` | Same as above with `--reload` |
| `make deploy-datasette` | Deploy to Fly.io via `flyctl` |
| `make clean` | Remove build artifacts (`site/`, `htmlcov/`, `.coverage`, caches) |

---

## Running the pipeline

```bash
# Uses config.json in the project root
uv run python -m collection_analysis.run

# Or with a custom config path
uv run python -m collection_analysis.run --config /path/to/config.json

# Console script
uv run collection-analysis
```

---

## Tests

Unit tests have no external dependencies:

```bash
make test
# or
pytest tests/unit/ -v
```

Integration tests require a running PostgreSQL instance (managed automatically
by `pytest-postgresql`):

```bash
make test-integration
# or
pytest tests/ -m integration -v
```

Coverage report:

```bash
make test-cov
open htmlcov/index.html
```

---

## Linting

`ruff` handles Python formatting and linting; `sqlfluff` handles SQL files in
`sql/views/` and `sql/indexes/`.

```bash
make lint    # check only
make format  # auto-fix
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
4. `make lint` will check it with `sqlfluff`.

---

## Datasette (local)

After running the pipeline to produce `current_collection.db`:

```bash
make datasette        # production config, port 8001
make datasette-dev    # same + auto-reload on config change
```

See [datasette/metadata.yml](../datasette/metadata.yml) for canned queries and
column descriptions.
