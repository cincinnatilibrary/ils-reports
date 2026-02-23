"""Unit tests for collection_analysis.load — SQLite only, no PostgreSQL."""

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
