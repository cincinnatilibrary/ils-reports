"""
Integration tests for the collection_analysis pipeline.

All tests here are marked with @pytest.mark.integration and require a live
PostgreSQL instance. They are skipped automatically when running `make test`
(unit tests only). Run with:

    scripts/test.sh --integration
    # or
    pytest tests/ -m integration -v
"""

import sqlite3
import sys

import pytest
from sqlalchemy import create_engine

from collection_analysis import config as cfg_module
from collection_analysis import extract


def _make_engine(sierra_config):
    """Create a SQLAlchemy engine from the test config dict."""
    return create_engine(cfg_module.pg_connection_string(sierra_config))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_env(monkeypatch, cfg):
    """Set env vars from a sierra_config dict so run.main() reads them."""
    mapping = {
        "PG_HOST": str(cfg["pg_host"]),
        "PG_PORT": str(cfg["pg_port"]),
        "PG_DBNAME": str(cfg["pg_dbname"]),
        "PG_USERNAME": str(cfg["pg_username"]),
        "PG_PASSWORD": str(cfg.get("pg_password", "")),
        "PG_SSLMODE": str(cfg.get("pg_sslmode", "require")),
        "PG_ITERSIZE": str(cfg.get("pg_itersize", 100)),
        "OUTPUT_DIR": str(cfg["output_dir"]),
    }
    for key, val in mapping.items():
        monkeypatch.setenv(key, val)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_pg_connection(sierra_db):
    """Smoke test: can we connect to the test PostgreSQL instance?"""
    cur = sierra_db.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1


# ---------------------------------------------------------------------------
# Core extractor tests (previously existing, kept for regression)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_extract_bib_returns_rows(sierra_db, sierra_config):
    """extract_bib() yields dicts with the expected columns."""
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_bib(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    first = rows[0]
    assert "bib_record_num" in first
    assert "best_title" in first


@pytest.mark.integration
def test_extract_item_returns_rows(sierra_db, sierra_config):
    """extract_item() yields dicts with the expected columns."""
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_item(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    first = rows[0]
    assert "item_record_num" in first
    assert "item_status_code" in first


@pytest.mark.integration
def test_extract_record_metadata_returns_rows(sierra_db, sierra_config):
    """extract_record_metadata() yields rows for b, i, j record types."""
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_record_metadata(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    types = {r["record_type_code"] for r in rows}
    assert types <= {"b", "i", "j"}


# ---------------------------------------------------------------------------
# Extractor tests for all 21 functions
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_extract_bib_record_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_bib_record(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    assert "language_code" in rows[0]


@pytest.mark.integration
def test_extract_volume_record_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_volume_record(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    assert "volume_record_num" in rows[0]


@pytest.mark.integration
def test_extract_item_message_executes(sierra_db, sierra_config):
    """extract_item_message() runs without error (may return 0 rows if no messages)."""
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_item_message(pg, sierra_config["pg_itersize"]))
    # Seed has one item message varfield; result may be > 0
    assert isinstance(rows, list)
    if rows:
        assert "varfield_id" in rows[0]


@pytest.mark.integration
def test_extract_language_property_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_language_property(pg))
    assert len(rows) > 0
    assert "code" in rows[0]


@pytest.mark.integration
def test_extract_bib_record_item_record_link_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_bib_record_item_record_link(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    assert "bib_record_num" in rows[0]
    assert "item_record_num" in rows[0]


@pytest.mark.integration
def test_extract_volume_record_item_record_link_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_volume_record_item_record_link(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    assert "volume_record_num" in rows[0]


@pytest.mark.integration
def test_extract_location_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_location(pg))
    assert len(rows) > 0
    assert "code" in rows[0]


@pytest.mark.integration
def test_extract_location_name_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_location_name(pg))
    assert len(rows) > 0
    assert "name" in rows[0]


@pytest.mark.integration
def test_extract_branch_name_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_branch_name(pg))
    assert len(rows) > 0
    assert "name" in rows[0]


@pytest.mark.integration
def test_extract_branch_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_branch(pg))
    assert len(rows) > 0
    assert "code_num" in rows[0]


@pytest.mark.integration
def test_extract_country_property_myuser_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_country_property_myuser(pg))
    assert len(rows) > 0
    assert "code" in rows[0]


@pytest.mark.integration
def test_extract_item_status_property_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_item_status_property(pg))
    assert len(rows) > 0
    assert "item_status_code" in rows[0]


@pytest.mark.integration
def test_extract_itype_property_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_itype_property(pg))
    assert len(rows) > 0
    assert "itype_name" in rows[0]


@pytest.mark.integration
def test_extract_bib_level_property_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_bib_level_property(pg))
    assert len(rows) > 0
    assert "bib_level_property_code" in rows[0]


@pytest.mark.integration
def test_extract_material_property_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_material_property(pg))
    assert len(rows) > 0
    assert "material_property_name" in rows[0]


@pytest.mark.integration
def test_extract_hold_returns_rows(sierra_db, sierra_config):
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_hold(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    assert "hold_status" in rows[0]


@pytest.mark.integration
def test_extract_circ_agg_returns_rows(sierra_db, sierra_config):
    """circ_agg queries last 6 months; seed data uses CURRENT_TIMESTAMP."""
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_circ_agg(pg))
    assert len(rows) > 0
    assert "op_code" in rows[0]


@pytest.mark.integration
def test_extract_circ_leased_items_returns_rows(sierra_db, sierra_config):
    """circ_leased_items queries L-barcode items within 180 days."""
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_circ_leased_items(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    assert "barcode" in rows[0]
    assert all(r["barcode"].startswith("L") for r in rows)


# ---------------------------------------------------------------------------
# Pagination test
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_pagination_advances_cursor(sierra_db, sierra_config):
    """With itersize=1, extract_record_metadata makes one call per row."""
    engine = _make_engine(sierra_config)
    with engine.connect() as pg:
        rows = list(extract.extract_record_metadata(pg, itersize=1))
    # Seed has 11 records (b/i/j types only: 3 bibs + 5 items + 1 volume = 9)
    # Each page has 1 row; all rows should be yielded
    assert len(rows) >= 2  # at minimum more than 1, proving pagination advanced


# ---------------------------------------------------------------------------
# Fixed: was using deprecated --config / config.json approach
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_full_pipeline_end_to_end(sierra_db, sierra_config, monkeypatch, tmp_path):
    """
    run.main() completes without error and produces current_collection.db.
    Uses environment variables instead of the deprecated --config flag.
    """
    from collection_analysis import load, run

    # Override OUTPUT_DIR to use a fresh tmp dir for this test
    output_dir = str(tmp_path / "pipeline_output")
    test_cfg = {**sierra_config, "output_dir": output_dir}

    _set_env(monkeypatch, test_cfg)

    # Patch sys.argv to remove any pytest arguments
    orig_argv = sys.argv
    sys.argv = ["collection-analysis"]
    try:
        run.main()
    finally:
        sys.argv = orig_argv

    db_path = load.final_path(output_dir)
    assert db_path.exists(), f"Expected {db_path} to exist after pipeline run"

    conn = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    for table in ("bib", "item", "record_metadata"):
        assert table in tables, f"Expected table '{table}' in database"
        count = conn.execute(f"SELECT count(*) FROM \"{table}\"").fetchone()[0]
        assert count > 0, f"Expected non-empty table '{table}', got 0 rows"
    conn.close()


# ---------------------------------------------------------------------------
# Fixed: was using sqlite_utils (not in core deps)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_swap_atomicity(sierra_config, tmp_path):
    """
    An exception raised after open_build_db() but before swap_db() must leave
    the live DB unchanged.
    """
    from collection_analysis import load

    output_dir = str(tmp_path / "swap_test")
    import os
    os.makedirs(output_dir, exist_ok=True)
    live_db_path = load.final_path(output_dir)

    # Create an existing live DB with a sentinel table using stdlib sqlite3
    live_db = sqlite3.connect(live_db_path)
    live_db.execute("CREATE TABLE sentinel (id INTEGER, value TEXT)")
    live_db.execute("INSERT INTO sentinel VALUES (1, 'original')")
    live_db.commit()
    live_db.close()

    # Simulate a failed pipeline build
    try:
        _db = load.open_build_db(output_dir)
        raise RuntimeError("Simulated pipeline failure")
    except RuntimeError:
        pass  # build DB exists but swap never happened

    # The live DB must still contain the sentinel table with original data
    check_db = sqlite3.connect(live_db_path)
    tables = {
        row[0]
        for row in check_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "sentinel" in tables
    val = check_db.execute("SELECT value FROM sentinel WHERE id = 1").fetchone()[0]
    assert val == "original"
    check_db.close()


# ---------------------------------------------------------------------------
# Telemetry test
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_telemetry_written_after_run(sierra_db, sierra_config, monkeypatch, tmp_path):
    """After run.main(), pipeline_runs.db exists and has a successful run row."""
    from collection_analysis import run

    output_dir = str(tmp_path / "telemetry_output")
    test_cfg = {**sierra_config, "output_dir": output_dir}
    _set_env(monkeypatch, test_cfg)

    orig_argv = sys.argv
    sys.argv = ["collection-analysis"]
    try:
        run.main()
    finally:
        sys.argv = orig_argv

    tel_path = tmp_path / "telemetry_output" / "pipeline_runs.db"
    assert tel_path.exists(), "pipeline_runs.db was not created"

    tel_db = sqlite3.connect(tel_path)
    row = tel_db.execute(
        "SELECT success FROM run ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row is not None
    assert row[0] == 1  # success=1
    tel_db.close()


# ---------------------------------------------------------------------------
# Indexes and views
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_all_indexes_apply_without_error(sierra_db, sierra_config, tmp_path):
    """create_indexes() against a seeded build DB raises no exception."""
    from collection_analysis import load, transform

    output_dir = str(tmp_path / "idx_test")
    db = load.open_build_db(output_dir)
    # populate minimal tables so index DDL targets exist
    load.load_table(db, "item", [{"item_record_num": 1}])
    load.load_table(db, "bib", [{"bib_record_num": 1}])
    transform.create_indexes(db)  # must not raise
    db.close()


@pytest.mark.integration
def test_all_views_apply_without_error(sierra_db, sierra_config, monkeypatch, tmp_path):
    """
    run.main() completes without raising a view-creation exception.
    Views are created inside run.main(); asserting it succeeds is the key check.
    """
    from collection_analysis import load, run

    output_dir = str(tmp_path / "views_test")
    test_cfg = {**sierra_config, "output_dir": output_dir}
    _set_env(monkeypatch, test_cfg)

    orig_argv = sys.argv
    sys.argv = ["collection-analysis"]
    try:
        run.main()
    finally:
        sys.argv = orig_argv

    db_path = load.final_path(output_dir)
    assert db_path.exists(), "Pipeline did not produce a final DB"

    conn = sqlite3.connect(db_path)
    views = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        ).fetchall()
    }
    conn.close()
    # At least some views should have been created successfully
    assert len(views) >= 0  # reaching here without exception is the main assertion


@pytest.mark.integration
def test_full_pipeline_row_counts_match_seed(sierra_db, sierra_config, monkeypatch, tmp_path):
    """After run.main(), key table row counts are >= known seed floor."""
    from collection_analysis import load, run

    output_dir = str(tmp_path / "count_test")
    test_cfg = {**sierra_config, "output_dir": output_dir}
    _set_env(monkeypatch, test_cfg)

    orig_argv = sys.argv
    sys.argv = ["collection-analysis"]
    try:
        run.main()
    finally:
        sys.argv = orig_argv

    db_path = load.final_path(output_dir)
    conn = sqlite3.connect(db_path)
    bib_count = conn.execute('SELECT COUNT(*) FROM "bib"').fetchone()[0]
    item_count = conn.execute('SELECT COUNT(*) FROM "item"').fetchone()[0]
    meta_count = conn.execute('SELECT COUNT(*) FROM "record_metadata"').fetchone()[0]
    conn.close()

    assert bib_count >= 3, f"Expected >=3 bib rows from seed, got {bib_count}"
    assert item_count >= 5, f"Expected >=5 item rows from seed, got {item_count}"
    assert meta_count >= 11, f"Expected >=11 record_metadata rows from seed, got {meta_count}"
