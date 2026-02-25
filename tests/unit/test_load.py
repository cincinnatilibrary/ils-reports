"""Unit tests for collection_analysis.load — SQLite only, no PostgreSQL."""

import json
import logging
import sqlite3
from datetime import date, datetime

import pytest

from collection_analysis import load


class TestBuildPath:
    def test_build_path_default_name(self, tmp_output_dir):
        p = load.build_path(tmp_output_dir)
        assert p.name == "current_collection.db.new"

    def test_build_path_custom_name(self, tmp_output_dir):
        p = load.build_path(tmp_output_dir, db_name="my_report.db")
        assert p.name == "my_report.db.new"

    def test_final_path(self, tmp_output_dir):
        p = load.final_path(tmp_output_dir)
        assert p.name == "current_collection.db"
        assert ".new" not in p.name


class TestOpenBuildDb:
    def test_open_build_db_creates_file(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        assert load.build_path(tmp_output_dir).exists()
        db.close()

    def test_open_build_db_creates_parent_dirs(self, tmp_path):
        nested = str(tmp_path / "deep" / "nested" / "output")
        db = load.open_build_db(nested)
        assert load.build_path(nested).exists()
        db.close()

    def test_build_pragmas_applied(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        result = db.execute("PRAGMA journal_mode").fetchone()[0]
        assert result.lower() == "off"
        db.close()

    def test_build_pragma_page_size(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        result = db.execute("PRAGMA page_size").fetchone()[0]
        assert result == 8192
        db.close()


class TestFinalizeDb:
    def test_finalize_db_sets_wal(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        load.finalize_db(db)
        result = db.execute("PRAGMA journal_mode").fetchone()[0]
        assert result.lower() == "wal"
        db.close()

    def test_finalize_db_runs_analyze(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        # Should not raise
        load.finalize_db(db)
        db.close()


class TestSwapDb:
    def test_swap_db_replaces_file(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        load.finalize_db(db)
        db.close()

        src = load.build_path(tmp_output_dir)
        dst = load.final_path(tmp_output_dir)
        assert src.exists()
        assert not dst.exists()

        load.swap_db(tmp_output_dir)

        assert not src.exists()
        assert dst.exists()

    def test_swap_db_source_missing(self, tmp_output_dir):
        # No build DB was created — swap should raise
        with pytest.raises(FileNotFoundError):
            load.swap_db(tmp_output_dir)


class TestLoadTable:
    def _mem_db(self):
        return sqlite3.connect(":memory:")

    def test_load_table_creates_table(self):
        db = self._mem_db()
        rows = [{"id": 1, "name": "alpha"}, {"id": 2, "name": "beta"}]
        count = load.load_table(db, "items", iter(rows))
        assert count == 2
        result = db.execute("SELECT id, name FROM items ORDER BY id").fetchall()
        assert result == [(1, "alpha"), (2, "beta")]
        db.close()

    def test_load_table_json_serializes_dicts(self):
        db = self._mem_db()
        payload = {"key": "value", "num": 42}
        rows = [{"id": 1, "data": payload}]
        load.load_table(db, "items", iter(rows))
        raw = db.execute("SELECT data FROM items").fetchone()[0]
        assert json.loads(raw) == payload
        db.close()

    def test_load_table_json_serializes_lists(self):
        db = self._mem_db()
        payload = [1, 2, 3]
        rows = [{"id": 1, "tags": payload}]
        load.load_table(db, "items", iter(rows))
        raw = db.execute("SELECT tags FROM items").fetchone()[0]
        assert json.loads(raw) == payload
        db.close()

    def test_load_table_serializes_dates(self):
        db = self._mem_db()
        d = date(2024, 6, 15)
        dt = datetime(2024, 6, 15, 12, 30, 0)
        rows = [{"d": d, "dt": dt}]
        load.load_table(db, "items", iter(rows))
        row = db.execute("SELECT d, dt FROM items").fetchone()
        assert row[0] == "2024-06-15"
        assert row[1] == "2024-06-15T12:30:00"
        db.close()

    def test_load_table_empty_rows_returns_zero(self, caplog):
        db = self._mem_db()
        with caplog.at_level(logging.WARNING, logger="collection_analysis.load"):
            count = load.load_table(db, "items", iter([]))
        assert count == 0
        assert "No rows loaded" in caplog.text
        db.close()

    def test_load_table_batching(self):
        db = self._mem_db()
        rows = [{"n": i} for i in range(250)]
        count = load.load_table(db, "nums", iter(rows), batch_size=100)
        assert count == 250
        result = db.execute("SELECT COUNT(*) FROM nums").fetchone()[0]
        assert result == 250
        db.close()

    def test_load_table_default_batch_size(self):
        import inspect
        sig = inspect.signature(load.load_table)
        assert sig.parameters["batch_size"].default == 5000
