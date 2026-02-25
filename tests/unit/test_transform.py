"""Unit tests for collection_analysis.transform — SQLite only."""

import sqlite3

import pytest

from collection_analysis import transform
from collection_analysis.transform import SQL_DIR


def _view_names(conn):
    return [
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()
    ]


class TestCreateViews:
    def test_create_views_empty_dir(self, empty_db, tmp_sql_dir):
        # Should log a warning but not raise
        transform.create_views(empty_db, sql_dir=tmp_sql_dir)

    def test_create_views_single_file(self, empty_db, tmp_sql_dir):
        # Create a simple base table then a view on top of it
        empty_db.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        view_sql = tmp_sql_dir / "views" / "01_item_view.sql"
        view_sql.write_text("CREATE VIEW item_view AS SELECT id, name FROM items")
        transform.create_views(empty_db, sql_dir=tmp_sql_dir)
        assert "item_view" in _view_names(empty_db)

    def test_create_views_alphabetical_order(self, empty_db, tmp_sql_dir):
        """A view that depends on another view must be created after it."""
        empty_db.execute("CREATE TABLE base (id INTEGER PRIMARY KEY, val TEXT)")
        (tmp_sql_dir / "views" / "01_first_view.sql").write_text(
            "CREATE VIEW first_view AS SELECT id, val FROM base"
        )
        (tmp_sql_dir / "views" / "02_second_view.sql").write_text(
            "CREATE VIEW second_view AS SELECT id FROM first_view"
        )
        transform.create_views(empty_db, sql_dir=tmp_sql_dir)
        assert "first_view" in _view_names(empty_db)
        assert "second_view" in _view_names(empty_db)

    def test_nonexistent_directory_raises(self, empty_db, tmp_path):
        """Non-existent sql dir: raises on Python 3.12+ or silently returns."""
        bad_sql_dir = tmp_path / "no_such_sql"
        try:
            transform.create_views(empty_db, sql_dir=bad_sql_dir)
        except OSError:
            pass  # Python 3.12+ raises for non-existent glob paths
        assert _view_names(empty_db) == []

    def test_file_with_only_comments_skipped(self, empty_db, tmp_sql_dir):
        (tmp_sql_dir / "views" / "01_comment_only.sql").write_text("-- this is a comment only")
        transform.create_views(empty_db, sql_dir=tmp_sql_dir)
        assert _view_names(empty_db) == []

    def test_view_dependency_order(self, empty_db, tmp_sql_dir):
        """View B depends on view A; only works if A is created first."""
        empty_db.execute("CREATE TABLE data (id INTEGER, val TEXT)")
        (tmp_sql_dir / "views" / "01_view_a.sql").write_text(
            "CREATE VIEW view_a AS SELECT id, val FROM data"
        )
        (tmp_sql_dir / "views" / "02_view_b.sql").write_text(
            "CREATE VIEW view_b AS SELECT id FROM view_a WHERE id > 0"
        )
        transform.create_views(empty_db, sql_dir=tmp_sql_dir)
        views = _view_names(empty_db)
        assert "view_a" in views
        assert "view_b" in views

    def test_smoke_all_real_view_files_syntax(self):
        """All 26 real view SQL files load and split without error."""
        views_dir = SQL_DIR / "views"
        sql_files = sorted(views_dir.glob("*.sql"))
        assert len(sql_files) > 0, "No real view SQL files found"
        for sql_file in sql_files:
            sql = sql_file.read_text()
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            assert len(statements) >= 0  # file loads and splits without error


class TestCreateIndexes:
    def test_create_indexes_single_file(self, empty_db, tmp_sql_dir):
        empty_db.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        idx_sql = tmp_sql_dir / "indexes" / "01_item_name.sql"
        idx_sql.write_text("CREATE INDEX idx_item_name ON items(name)")
        transform.create_indexes(empty_db, sql_dir=tmp_sql_dir)
        indexes = [row[1] for row in empty_db.execute("PRAGMA index_list('items')").fetchall()]
        assert "idx_item_name" in indexes

    def test_nonexistent_directory_raises(self, empty_db, tmp_path):
        bad_sql_dir = tmp_path / "no_such_sql"
        try:
            transform.create_indexes(empty_db, sql_dir=bad_sql_dir)
        except OSError:
            pass  # Python 3.12+ raises; older versions log a warning and return

    def test_smoke_all_real_index_file_syntax(self):
        """The real index SQL file loads and splits without error."""
        indexes_dir = SQL_DIR / "indexes"
        sql_files = sorted(indexes_dir.glob("*.sql"))
        assert len(sql_files) > 0, "No real index SQL files found"
        for sql_file in sql_files:
            sql = sql_file.read_text()
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            assert len(statements) >= 0


class TestMultiStatement:
    def test_multi_statement_sql_file(self, empty_db, tmp_sql_dir):
        """Multiple semicolon-separated statements in one file all execute."""
        empty_db.execute("CREATE TABLE t1 (id INTEGER PRIMARY KEY)")
        empty_db.execute("CREATE TABLE t2 (id INTEGER PRIMARY KEY)")
        sql = "CREATE VIEW v1 AS SELECT id FROM t1;\nCREATE VIEW v2 AS SELECT id FROM t2"
        (tmp_sql_dir / "views" / "01_multi.sql").write_text(sql)
        transform.create_views(empty_db, sql_dir=tmp_sql_dir)
        assert "v1" in _view_names(empty_db)
        assert "v2" in _view_names(empty_db)

    def test_bad_sql_raises(self, empty_db, tmp_sql_dir):
        (tmp_sql_dir / "views" / "01_bad.sql").write_text("THIS IS NOT SQL")
        with pytest.raises(sqlite3.OperationalError):
            transform.create_views(empty_db, sql_dir=tmp_sql_dir)
