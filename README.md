# ils-reports

![Coverage](coverage-badge.svg)

Data pipelines from the Cincinnati & Hamilton County Public Library (CHPL)
Sierra ILS (PostgreSQL) to SQLite databases for reporting and public analysis.

## Current pipelines

### `collection_analysis`

Builds `current_collection.db` — a SQLite snapshot of the CHPL collection,
served publicly via Datasette at https://collection-analysis.cincy.pl/

**Docs:** [`docs/data_dictionary.md`](docs/data_dictionary.md)

## Setup

```bash
git clone <this repo>
cd ils-reports
scripts/setup.sh   # uv sync --all-extras + pre-commit install

cp .env.sample .env
# edit .env with your Sierra credentials and OUTPUT_DIR
```

## Running the pipeline

```bash
scripts/run.sh
```

## Project structure

```
ils-reports/
├── collection_analysis/   Python package — extract, load, transform, run
├── sql/
│   ├── views/             One .sql file per SQLite view
│   └── indexes/           One .sql file per index group
├── docs/                  MkDocs documentation
├── datasette/             Datasette config + Fly.io deployment
├── tests/                 pytest unit and integration tests
├── reference/             Original notebook and scripts (read-only reference)
├── config.json.sample     Config template (copy to config.json)
├── pyproject.toml
└── uv.lock
```

## Related repos

- [`cincinnatilibrary/collection-analysis`](https://github.com/cincinnatilibrary/collection-analysis)
  — Datasette server config, Sphinx docs, and historical exploration notebooks
