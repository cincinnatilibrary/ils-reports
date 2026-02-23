# ils-reports

**ils-reports** is the data pipeline that powers the Cincinnati & Hamilton County Public Library (CHPL) open collection dataset. It extracts records from the Sierra Integrated Library System (ILS) PostgreSQL database, transforms them, and writes a SQLite snapshot served publicly via Datasette.

## Live site

The finished database is available at **[collection-analysis.cincy.pl](https://collection-analysis.cincy.pl/)**.

## What it does

The `collection_analysis` pipeline:

1. Connects to Sierra's `sierra_view` PostgreSQL schema
2. Extracts bib, item, hold, and circulation records
3. Writes them to a local SQLite database with bulk-write optimisations
4. Creates summary views and indexes
5. Atomically replaces the live database file

A full rebuild from scratch runs on a nightly cron schedule.

## Quick start

```bash
git clone https://github.com/cincinnatilibrary/ils-reports
cd ils-reports
uv sync --all-extras
cp config.json.sample config.json
# fill in Sierra credentials
uv run python -m collection_analysis.run
```

See [Configuration](configuration.md) for all available settings and [Development](development.md) for the full developer workflow.
