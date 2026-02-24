"""Unit tests for collection_analysis.transform — SQLite only."""

import sqlite3

import pytest

from collection_analysis import transform


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


class TestCreateIndexes:
    def test_create_indexes_single_file(self, empty_db, tmp_sql_dir):
        empty_db.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        idx_sql = tmp_sql_dir / "indexes" / "01_item_name.sql"
        idx_sql.write_text("CREATE INDEX idx_item_name ON items(name)")
        transform.create_indexes(empty_db, sql_dir=tmp_sql_dir)
        indexes = [row[1] for row in empty_db.execute("PRAGMA index_list('items')").fetchall()]
        assert "idx_item_name" in indexes


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
