"""
Integration tests for the collection_analysis pipeline.

All tests here are marked with @pytest.mark.integration and require a live
PostgreSQL instance. They are skipped automatically when running `make test`
(unit tests only). Run with:

    make test-integration
    # or
    pytest tests/ -m integration -v
"""

import pytest


@pytest.mark.integration
def test_pg_connection(sierra_db):
    """Smoke test: can we connect to the test PostgreSQL instance?"""
    cur = sierra_db.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1


@pytest.mark.integration
@pytest.mark.skip(reason="extract.py not yet implemented — add cases as functions are ported")
def test_extract_bib_returns_rows(sierra_db, sierra_config):
    """extract_bib() yields dicts with the expected columns."""
    from sqlalchemy import create_engine

    from collection_analysis import config as cfg_module
    from collection_analysis import extract

    engine = create_engine(cfg_module.pg_connection_string(sierra_config))
    with engine.connect() as pg:
        rows = list(extract.extract_bib(pg, sierra_config["pg_itersize"]))
    assert len(rows) > 0
    first = rows[0]
    assert "bib_record_num" in first
    assert "best_title" in first


@pytest.mark.integration
def test_full_pipeline_end_to_end(sierra_config, tmp_path):
    """
    run.main() completes without error and produces current_collection.db.

    Because extract.py is not yet implemented, this tests the skeleton pipeline
    (no tables extracted, but views/indexes attempted on empty DB, then swap).
    """
    import json

    from collection_analysis import load, run

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(sierra_config))

    # Patch sys.argv so argparse picks up our config path
    import sys
    sys_argv_orig = sys.argv
    sys.argv = ["collection-analysis", "--config", str(config_path)]
    try:
        run.main()
    finally:
        sys.argv = sys_argv_orig

    db_path = load.final_path(sierra_config["output_dir"])
    assert db_path.exists(), f"Expected {db_path} to exist after pipeline run"


@pytest.mark.integration
def test_swap_atomicity(sierra_config, tmp_path):
    """
    An exception raised after open_build_db() but before swap_db() must leave
    the live DB unchanged.
    """
    import sqlite_utils

    from collection_analysis import load

    output_dir = sierra_config["output_dir"]
    live_db_path = load.final_path(output_dir)

    # Create an existing live DB with a sentinel table
    live_db = sqlite_utils.Database(live_db_path)
    live_db["sentinel"].insert({"id": 1, "value": "original"})
    live_db.close()

    # Simulate a failed pipeline build
    try:
        _db = load.open_build_db(output_dir)
        raise RuntimeError("Simulated pipeline failure")
    except RuntimeError:
        pass  # build DB exists but swap never happened

    # The live DB must still contain the sentinel table
    check = sqlite_utils.Database(live_db_path)
    assert "sentinel" in check.table_names()
    check.close()
