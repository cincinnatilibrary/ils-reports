# Configuration

The pipeline is configured via environment variables.
For local development, copy `.env.sample` to `.env` and fill in your values —
the `.env` file is loaded automatically when the pipeline starts.

```bash
cp .env.sample .env
# edit .env with your Sierra credentials and OUTPUT_DIR
```

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PG_HOST` | Yes | — | Sierra PostgreSQL hostname or IP |
| `PG_PORT` | Yes | — | Port (typically `1032` for Sierra) |
| `PG_DBNAME` | Yes | — | Database name (typically `"iii"`) |
| `PG_USERNAME` | Yes | — | PostgreSQL username |
| `PG_PASSWORD` | Yes | — | PostgreSQL password |
| `OUTPUT_DIR` | Yes | — | Directory where `current_collection.db` is written |
| `PG_SSLMODE` | No | `"require"` | SSL mode passed to psycopg2 (`require`, `disable`, etc.) |
| `PG_ITERSIZE` | No | `5000` | Server-side cursor fetch size. Increase to `10000`–`50000` to reduce round-trips on fast networks. |
| `LOG_LEVEL` | No | `"INFO"` | Logging verbosity: `DEBUG`, `INFO`, or `WARNING`. |
| `LOG_FILE` | No | _(unset)_ | Path to a log file. When set, all log output is also written there. |

---

## Example `.env`

```dotenv
PG_HOST=sierra-db.example.org
PG_PORT=1032
PG_DBNAME=iii
PG_USERNAME=readonly_user
PG_PASSWORD=s3cr3t
PG_SSLMODE=require
PG_ITERSIZE=10000
OUTPUT_DIR=/srv/datasette/data
LOG_LEVEL=INFO
# LOG_FILE=/var/log/collection-analysis/pipeline.log
```

---

## Notes

- `PG_SSLMODE=require` is recommended for production. Set to `disable` only
  in isolated test environments.
- `OUTPUT_DIR` must be writable by the process running the pipeline. The
  directory is created automatically if it does not exist.
- The pipeline writes to `<OUTPUT_DIR>/current_collection.db.new` during the
  build and renames it to `current_collection.db` only on success. Keep at
  least **3× the database size** of free disk space.

---

## Legacy: `config.json` (Deprecated)

`config.json` is still accepted for backward compatibility but will emit a
`DeprecationWarning` every time it is used.  Migrate to environment variables
at your earliest convenience.

If both env vars and `config.json` are present, **env vars take priority**.

```bash
# Old workflow (deprecated)
cp config.json.sample config.json
python -m collection_analysis.run --config config.json
```
