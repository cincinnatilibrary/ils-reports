"""
transform.py — Create views and indexes in the SQLite database.

Reads SQL files from the sql/ directory and executes them in order:
  1. sql/views/     — CREATE VIEW statements
  2. sql/indexes/   — CREATE INDEX statements

Views and indexes are always created AFTER all base tables are loaded,
which is significantly faster than maintaining indexes during inserts.

SQL files are executed in alphabetical order within each directory,
so prefix filenames with a number if order matters (e.g. 01_item_view.sql).

TODO: Extract view and index SQL from reference/collection-analysis.cincy.pl_gen_db.ipynb
      into individual .sql files under sql/views/ and sql/indexes/
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).parent.parent / "sql"


def create_views(db: sqlite3.Connection, sql_dir=None) -> None:
    """Execute all .sql files in sql/views/ against the database."""
    _execute_sql_dir(db, (Path(sql_dir) if sql_dir else SQL_DIR) / "views")


def create_indexes(db: sqlite3.Connection, sql_dir=None) -> None:
    """Execute all .sql files in sql/indexes/ against the database."""
    _execute_sql_dir(db, (Path(sql_dir) if sql_dir else SQL_DIR) / "indexes")


def _execute_sql_dir(db: sqlite3.Connection, directory: Path) -> None:
    sql_files = sorted(directory.glob("*.sql"))
    if not sql_files:
        logger.warning(f"No .sql files found in {directory}")
        return
    for sql_file in sql_files:
        logger.info(f"Executing {sql_file.name} ...")
        sql = sql_file.read_text()
        # Split on semicolons to support files with multiple statements
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                db.execute(statement)
