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

    def test_deletes_stale_new_file(self, tmp_output_dir):
        stale_path = load.build_path(tmp_output_dir)
        stale_path.write_bytes(b"THIS IS NOT A SQLITE FILE")
        db = load.open_build_db(tmp_output_dir)
        db.close()
        # File should now be a valid empty SQLite database
        fresh_db = sqlite3.connect(stale_path)
        count = fresh_db.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0]
        fresh_db.close()
        assert count == 0

    def test_build_pragma_synchronous_off(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        result = db.execute("PRAGMA synchronous").fetchone()[0]
        db.close()
        assert result == 0  # OFF

    def test_build_pragma_cache_size(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        result = db.execute("PRAGMA cache_size").fetchone()[0]
        db.close()
        assert result < 0  # negative value = size in kilobytes


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

    def test_finalize_sets_synchronous_normal(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        load.finalize_db(db)
        result = db.execute("PRAGMA synchronous").fetchone()[0]
        db.close()
        assert result == 1  # NORMAL


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

    def test_swap_overwrites_existing_live_db(self, tmp_output_dir):
        # Pre-create a live DB at the destination
        dst = load.final_path(tmp_output_dir)
        sqlite3.connect(dst).close()
        assert dst.exists()

        db = load.open_build_db(tmp_output_dir)
        load.finalize_db(db)
        db.close()
        load.swap_db(tmp_output_dir)

        assert dst.exists()
        assert not load.build_path(tmp_output_dir).exists()

    def test_swap_content_correct(self, tmp_output_dir):
        db = load.open_build_db(tmp_output_dir)
        db.execute("CREATE TABLE sentinel (id INTEGER)")
        db.execute("INSERT INTO sentinel VALUES (42)")
        db.commit()
        load.finalize_db(db)
        db.close()
        load.swap_db(tmp_output_dir)

        dst = load.final_path(tmp_output_dir)
        check_db = sqlite3.connect(dst)
        val = check_db.execute("SELECT id FROM sentinel").fetchone()[0]
        check_db.close()
        assert val == 42


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

    def test_none_values_stored_as_null(self):
        db = self._mem_db()
        rows = [{"id": 1, "name": None}]
        load.load_table(db, "items", iter(rows))
        val = db.execute("SELECT name FROM items").fetchone()[0]
        db.close()
        assert val is None

    def test_unicode_values(self):
        db = self._mem_db()
        rows = [{"id": 1, "label": "Hello 🌍 café"}]
        load.load_table(db, "items", iter(rows))
        val = db.execute("SELECT label FROM items").fetchone()[0]
        db.close()
        assert val == "Hello 🌍 café"

    def test_table_already_exists_is_idempotent(self):
        db = self._mem_db()
        load.load_table(db, "items", iter([{"id": 1}]))
        load.load_table(db, "items", iter([{"id": 2}]))  # should not raise
        count = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        db.close()
        assert count == 2
