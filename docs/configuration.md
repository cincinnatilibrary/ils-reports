# Configuration

The pipeline is configured via `config.json` in the project root (gitignored).
Copy `config.json.sample` to get started:

```bash
cp config.json.sample config.json
```

---

## Fields

| Field | Required | Default | Description |
|---|---|---|---|
| `pg_host` | Yes | — | Sierra PostgreSQL hostname or IP |
| `pg_port` | Yes | — | Port (typically `1032` for Sierra) |
| `pg_dbname` | Yes | — | Database name (typically `"iii"`) |
| `pg_username` | Yes | — | PostgreSQL username |
| `pg_password` | Yes | — | PostgreSQL password |
| `output_dir` | Yes | — | Directory where `current_collection.db` is written |
| `pg_sslmode` | No | `"require"` | SSL mode passed to psycopg2 (`require`, `disable`, etc.) |
| `pg_itersize` | No | `5000` | Server-side cursor fetch size. Increase to `10000`–`50000` to reduce round-trips on fast networks. |

---

## Example

```json
{
  "pg_host": "sierra-db.example.org",
  "pg_port": 1032,
  "pg_dbname": "iii",
  "pg_username": "readonly_user",
  "pg_password": "s3cr3t",
  "pg_sslmode": "require",
  "pg_itersize": 10000,
  "output_dir": "/srv/datasette/data"
}
```

---

## Custom config path

Pass `--config` to use a different file:

```bash
python -m collection_analysis.run --config /etc/ils-reports/config.json
```

---

## Notes

- `pg_sslmode=require` is the recommended setting for production. Set to
  `disable` only in isolated test environments.
- `output_dir` must be writable by the process running the pipeline. The
  directory is created automatically if it does not exist.
- The pipeline writes to `<output_dir>/current_collection.db.new` during the
  build and renames it to `current_collection.db` only on success. Keep at
  least **3× the database size** of free disk space.
