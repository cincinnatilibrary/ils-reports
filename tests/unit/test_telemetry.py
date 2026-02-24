"""Unit tests for telemetry.py (no PostgreSQL required)."""

from collection_analysis.telemetry import finish_run, open_telemetry_db, start_run


def _open(tmp_path):
    return open_telemetry_db(str(tmp_path))


def _sample_stats():
    return [
        {"stage": "item", "rows": 500, "elapsed_seconds": 1.2, "rows_per_sec": 416.7},
        {"stage": "views", "rows": None, "elapsed_seconds": 0.5, "rows_per_sec": None},
    ]


def test_open_creates_tables(tmp_path):
    db = _open(tmp_path)
    tables = {
        r[0]
        for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "run" in tables
    assert "stage" in tables
    db.close()


def test_open_creates_views(tmp_path):
    db = _open(tmp_path)
    views = {
        r[0]
        for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        ).fetchall()
    }
    assert "v_stage_summary" in views
    assert "v_recent_runs" in views
    assert "v_stage_trends" in views
    db.close()


def test_open_idempotent(tmp_path):
    db1 = _open(tmp_path)
    db1.close()
    db2 = _open(tmp_path)  # should not raise
    db2.close()


def test_start_run_returns_id(tmp_path):
    db = _open(tmp_path)
    run_id = start_run(db, "2026-01-01T00:00:00")
    assert isinstance(run_id, int)
    assert run_id > 0
    db.close()


def test_finish_run_success(tmp_path):
    db = _open(tmp_path)
    run_id = start_run(db, "2026-01-01T00:00:00")
    finish_run(db, run_id, "2026-01-01T00:05:00", 300.0, True, _sample_stats())
    row = db.execute(
        "SELECT success, completed_at FROM run WHERE id = ?", (run_id,)
    ).fetchone()
    assert row[0] == 1
    assert row[1] == "2026-01-01T00:05:00"
    db.close()


def test_finish_run_failure(tmp_path):
    db = _open(tmp_path)
    run_id = start_run(db, "2026-01-01T00:00:00")
    finish_run(db, run_id, "2026-01-01T00:01:00", 60.0, False, [])
    row = db.execute(
        "SELECT success FROM run WHERE id = ?", (run_id,)
    ).fetchone()
    assert row[0] == 0
    db.close()


def test_stage_row_count(tmp_path):
    db = _open(tmp_path)
    run_id = start_run(db, "2026-01-01T00:00:00")
    stats = _sample_stats()
    finish_run(db, run_id, "2026-01-01T00:05:00", 300.0, True, stats)
    count = db.execute(
        "SELECT COUNT(*) FROM stage WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    assert count == len(stats)
    db.close()


def test_v_stage_summary_filters_failed(tmp_path):
    db = _open(tmp_path)
    # Failed run — should not appear in v_stage_summary
    run_id = start_run(db, "2026-01-01T00:00:00")
    finish_run(db, run_id, "2026-01-01T00:01:00", 60.0, False, _sample_stats())
    rows = db.execute("SELECT * FROM v_stage_summary").fetchall()
    assert rows == []
    # Successful run — should appear
    run_id2 = start_run(db, "2026-01-02T00:00:00")
    finish_run(db, run_id2, "2026-01-02T00:05:00", 300.0, True, _sample_stats())
    rows = db.execute("SELECT * FROM v_stage_summary").fetchall()
    assert len(rows) > 0
    db.close()


def test_v_recent_runs_ordering(tmp_path):
    db = _open(tmp_path)
    for i in range(3):
        run_id = start_run(db, f"2026-01-0{i+1}T00:00:00")
        finish_run(db, run_id, f"2026-01-0{i+1}T00:05:00", 300.0, True, [])
    rows = db.execute("SELECT id FROM v_recent_runs").fetchall()
    ids = [r[0] for r in rows]
    assert ids == sorted(ids, reverse=True)
    db.close()
