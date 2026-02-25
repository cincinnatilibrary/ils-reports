"""Unit tests for run.py helpers (no PostgreSQL required)."""

import logging
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from collection_analysis.run import (
    _configure_logging,
    _log_summary,
    _timed_load,
    _write_run_stats,
)


class TestConfigureLogging:
    def setup_method(self):
        # Remove any file handlers added by previous tests
        root = logging.getLogger()
        for h in list(root.handlers):
            if isinstance(h, logging.FileHandler):
                h.close()
                root.removeHandler(h)

    def test_file_handler_added(self, tmp_path):
        log_file = str(tmp_path / "pipeline.log")
        cfg = {"log_file": log_file, "log_level": "INFO"}
        _configure_logging(cfg)
        root = logging.getLogger()
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1
        # cleanup
        for h in file_handlers:
            h.close()
            root.removeHandler(h)

    def test_no_file_handler_by_default(self):
        cfg = {"log_level": "INFO"}  # no log_file key
        root = logging.getLogger()
        before = len([h for h in root.handlers if isinstance(h, logging.FileHandler)])
        _configure_logging(cfg)
        after = len([h for h in root.handlers if isinstance(h, logging.FileHandler)])
        assert after == before

    def test_log_level_applied(self):
        cfg = {"log_level": "WARNING"}
        _configure_logging(cfg)
        assert logging.getLogger().level == logging.WARNING
        # restore
        logging.getLogger().setLevel(logging.INFO)

    def test_invalid_log_level_falls_back_to_info(self):
        cfg = {"log_level": "GARBAGE"}
        _configure_logging(cfg)
        assert logging.getLogger().level == logging.INFO
        # restore
        logging.getLogger().setLevel(logging.WARNING)

    def test_log_file_path_creates_file(self, tmp_path):
        log_file = str(tmp_path / "run.log")
        cfg = {"log_file": log_file, "log_level": "INFO"}
        _configure_logging(cfg)
        assert Path(log_file).exists()
        # cleanup
        root = logging.getLogger()
        for h in list(root.handlers):
            if isinstance(h, logging.FileHandler):
                h.close()
                root.removeHandler(h)

    def test_unwritable_log_dir_raises_permission_error(self, tmp_path):
        """FileHandler raises PermissionError for an unwritable directory."""
        unwritable_dir = tmp_path / "noperms"
        unwritable_dir.mkdir()
        unwritable_dir.chmod(0o000)
        log_file = str(unwritable_dir / "run.log")
        cfg = {"log_file": log_file, "log_level": "INFO"}
        try:
            with pytest.raises(PermissionError):
                _configure_logging(cfg)
        finally:
            unwritable_dir.chmod(0o755)  # restore so tmp_path cleanup succeeds


class TestTimedLoad:
    def _make_db(self):
        db = sqlite3.connect(":memory:")
        return db

    def test_returns_row_count_and_elapsed(self):
        db = self._make_db()
        rows = [{"id": i, "val": f"v{i}"} for i in range(10)]
        n, elapsed = _timed_load(db, "test_table", iter(rows))
        assert n == 10
        assert isinstance(elapsed, float)
        db.close()

    def test_elapsed_positive(self):
        db = self._make_db()
        rows = [{"id": i} for i in range(100)]
        _, elapsed = _timed_load(db, "elapsed_table", iter(rows))
        assert elapsed >= 0.0
        db.close()

    def test_exception_from_load_table_propagates(self):
        db = self._make_db()
        with patch("collection_analysis.load.load_table", side_effect=RuntimeError("injected error")):
            with pytest.raises(RuntimeError, match="injected error"):
                _timed_load(db, "t", iter([{"id": 1}]))
        db.close()


class TestWriteRunStats:
    def _make_db(self):
        return sqlite3.connect(":memory:")

    def _sample_stats(self):
        return [
            {"stage": "item", "rows": 500, "elapsed_seconds": 1.2, "rows_per_sec": 416.7},
            {"stage": "views", "rows": None, "elapsed_seconds": 0.5, "rows_per_sec": None},
        ]

    def test_table_created(self):
        db = self._make_db()
        _write_run_stats(db, "2026-01-01T00:00:00", self._sample_stats())
        tables = {
            r[0]
            for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "_pipeline_run" in tables
        db.close()

    def test_row_count(self):
        db = self._make_db()
        stats = self._sample_stats()
        _write_run_stats(db, "2026-01-01T00:00:00", stats)
        count = db.execute("SELECT COUNT(*) FROM _pipeline_run").fetchone()[0]
        assert count == len(stats)
        db.close()

    def test_columns(self):
        db = self._make_db()
        _write_run_stats(db, "2026-01-01T00:00:00", self._sample_stats())
        cols = {
            r[1]
            for r in db.execute("PRAGMA table_info(_pipeline_run)").fetchall()
        }
        assert {"stage", "rows", "elapsed_seconds"}.issubset(cols)
        db.close()


class TestLogSummary:
    def test_smoke(self, caplog):
        stats = [
            {"stage": "item", "rows": 1000, "elapsed_seconds": 2.5, "rows_per_sec": 400.0},
            {"stage": "views", "rows": None, "elapsed_seconds": 0.3, "rows_per_sec": None},
        ]
        with caplog.at_level(logging.INFO):
            _log_summary(stats, 5.0)
        assert "Stage summary" in caplog.text
        assert "TOTAL" in caplog.text

    def test_output_contains_stage_names(self, caplog):
        stats = [
            {"stage": "record_metadata", "rows": 500, "elapsed_seconds": 1.0, "rows_per_sec": 500.0},
            {"stage": "bib", "rows": 200, "elapsed_seconds": 0.5, "rows_per_sec": 400.0},
        ]
        with caplog.at_level(logging.INFO):
            _log_summary(stats, 1.5)
        assert "record_metadata" in caplog.text
        assert "bib" in caplog.text
