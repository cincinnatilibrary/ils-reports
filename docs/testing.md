# Testing

## Overview

The test suite is split into two categories:

| Category | Location | Requires PostgreSQL | Count |
|----------|----------|---------------------|-------|
| Unit | `tests/unit/` | No | 136 |
| Integration | `tests/integration/` | Yes | 29 |

CI runs unit tests only. A **85% coverage gate** is enforced via `pytest-cov` and `[tool.coverage.report] fail_under = 85` in `pyproject.toml`.

## Running tests

| Command | What it runs |
|---------|-------------|
| `scripts/test.sh` | Unit tests only (default) |
| `scripts/test.sh --integration` | Integration tests only |
| `scripts/test.sh --all` | Unit + integration |
| `scripts/test.sh --cov` | Unit tests + HTML coverage report + regenerates `coverage-badge.svg` |

## Coverage report

Run `scripts/test.sh --cov` to:

1. Execute unit tests with coverage measurement
2. Write `htmlcov/index.html` (browsable HTML report)
3. Write `coverage.xml` (intermediate XML; gitignored)
4. Regenerate `coverage-badge.svg` (committed to repo; displayed in `README.md`)

To include the HTML coverage report in the built docs site:

```bash
scripts/docs.sh --with-coverage
# → site/coverage/index.html available in built site
```

The `docs/coverage/` directory is gitignored — the HTML is copied in at build time and removed afterwards.

## Test inventory — unit

### `tests/unit/test_config.py`

| Class | Covers |
|-------|--------|
| `TestLoadValidConfig` | Env-var loading, all key types (str, int, float) |
| `TestLoadErrors` | Missing required vars, bad numeric types |
| `TestDeprecationWarnings` | `config.json` deprecation path and warning text |
| `TestSleepBetweenTables` | `PG_SLEEP_BETWEEN_TABLES` parsing and default |
| `TestPgConnectionString` | SQLAlchemy URL construction from config dict |

### `tests/unit/test_extract.py`

| Class | Covers |
|-------|--------|
| `TestLoadSql` | `_load_sql()` file-not-found and bad-SQL paths |
| `TestExtractRecordMetadata` | Pagination cursor, b/i/j type filter |
| `TestExtractBib` | Bib pagination and column schema |
| `TestExtractItem` | Item pagination and column schema |
| `TestExtractBibRecord` | `bib_record` fields |
| `TestExtractVolumeRecord` | `volume_record` fields |
| `TestExtractHold` | Hold record fields |
| `TestExtractLookupTables` | 9 non-paginated lookup extractors |
| `TestExtractCircAgg` | `circ_agg` date filter |
| `TestExtractItemMessage` | `item_message` varfield extraction |
| `TestExtractBibRecordItemRecordLink` | Bib ↔ item link table |
| `TestExtractVolumeRecordItemRecordLink` | Volume ↔ item link table |
| `TestExtractCircLeasedItems` | L-barcode leased item extraction |

### `tests/unit/test_load.py`

| Class | Covers |
|-------|--------|
| `TestBuildPath` | `.db.new` suffix naming |
| `TestOpenBuildDb` | PRAGMA settings, stale `.db.new` file cleanup |
| `TestFinalizeDb` | WAL mode, `NORMAL` synchronous PRAGMA |
| `TestSwapDb` | Atomic swap, overwrite, missing-source error |
| `TestLoadTable` | Insert, JSON serialisation, date ISO formatting, `None` → `NULL`, unicode, microseconds |

### `tests/unit/test_run.py`

| Class | Covers |
|-------|--------|
| `TestConfigureLogging` | Log level, file handler, `PermissionError` propagation |
| `TestTimedLoad` | Timing measurement, row count, exception propagation |
| `TestWriteRunStats` | `_pipeline_run` table creation and content |
| `TestLogSummary` | Summary log output format |

### `tests/unit/test_telemetry.py`

| Class / Module | Covers |
|----------------|--------|
| (module-level) | `pipeline_runs.db` schema, views, run recording |

### `tests/unit/test_transform.py`

| Class | Covers |
|-------|--------|
| `TestCreateViews` | View SQL execution, alphabetical ordering, real-file smoke test |
| `TestCreateIndexes` | Index SQL execution, real-file smoke test |
| `TestMultiStatement` | Semicolon-separated SQL files parsed and executed correctly |

### `tests/unit/test_static_assets.py`

| Class / Module | Covers |
|----------------|--------|
| (module-level) | CSS files parse without `tinycss2` errors |

## Test inventory — integration

All integration tests live in `tests/integration/test_pipeline.py` and require a live Sierra PostgreSQL instance. Mark with `@pytest.mark.integration`.

| Test | Covers |
|------|--------|
| `test_pg_connection` | PostgreSQL connectivity smoke test |
| `test_extract_bib_returns_rows` | `extract_bib()` columns and non-empty result |
| `test_extract_item_returns_rows` | `extract_item()` columns and non-empty result |
| `test_extract_record_metadata_returns_rows` | b/i/j type filter |
| `test_extract_bib_record_returns_rows` | `bib_record` columns |
| `test_extract_volume_record_returns_rows` | `volume_record` columns |
| `test_extract_item_message_executes` | Runs without error; rows optional |
| `test_extract_language_property_returns_rows` | Language lookup |
| `test_extract_bib_record_item_record_link_returns_rows` | Bib ↔ item link |
| `test_extract_volume_record_item_record_link_returns_rows` | Volume ↔ item link |
| `test_extract_location_returns_rows` | Location lookup |
| `test_extract_location_name_returns_rows` | `location_name` lookup |
| `test_extract_branch_name_returns_rows` | `branch_name` lookup |
| `test_extract_branch_returns_rows` | Branch lookup |
| `test_extract_country_property_myuser_returns_rows` | Country lookup |
| `test_extract_item_status_property_returns_rows` | Item status lookup |
| `test_extract_itype_property_returns_rows` | Itype lookup |
| `test_extract_bib_level_property_returns_rows` | Bib level lookup |
| `test_extract_material_property_returns_rows` | Material lookup |
| `test_extract_hold_returns_rows` | Hold records |
| `test_extract_circ_agg_returns_rows` | Circ aggregates (last 6 months) |
| `test_extract_circ_leased_items_returns_rows` | L-barcode leased items |
| `test_pagination_advances_cursor` | `itersize=1` cursor advance |
| `test_full_pipeline_end_to_end` | `run.main()` → valid DB with tables |
| `test_swap_atomicity` | Failed build leaves live DB unchanged |
| `test_telemetry_written_after_run` | `pipeline_runs.db` success row written |
| `test_all_indexes_apply_without_error` | `create_indexes()` on minimal build DB |
| `test_all_views_apply_without_error` | `run.main()` completes view creation |
| `test_full_pipeline_row_counts_match_seed` | Row counts ≥ seed floor |

## Adding tests

### Unit tests

Unit tests must not require a live PostgreSQL connection. Mock the engine with an in-memory iterable:

```python
from unittest.mock import MagicMock

def make_conn(rows):
    conn = MagicMock()
    conn.execute.return_value = iter(rows)
    return conn
```

Use `tmp_path` (pytest built-in) for any file-system operations:

```python
def test_something(tmp_path):
    db_path = tmp_path / "test.db"
    ...
```

### Integration tests

Mark with `@pytest.mark.integration` so they are excluded from the default `scripts/test.sh` run:

```python
import pytest

@pytest.mark.integration
def test_extract_something(pg_engine):
    rows = list(extract_something(pg_engine))
    assert len(rows) > 0
```

The `pg_engine` fixture is defined in `tests/conftest.py` and reads credentials from environment variables (or `.env`).
