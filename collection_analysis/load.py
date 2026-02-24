"""
load.py — Write extracted data into a SQLite database with optimized settings.

Handles:
  - Opening a SQLite connection with build-time PRAGMAs for maximum write speed
  - Bulk-inserting rows (executemany with plain sqlite3)
  - Deferring index creation until all tables are loaded
  - Building to a temp file (*.db.new) and atomically swapping on completion

Typical usage:
    db = open_build_db(path)         # open temp file, apply fast-write PRAGMAs
    load_table(db, "item", rows)     # insert rows
    ...
    finalize_db(db)                  # re-apply safe PRAGMAs, ANALYZE
    swap_db(path)                    # mv *.db.new -> *.db

TODO: Port loading logic from reference/collection-analysis.cincy.pl_gen_db.ipynb
"""

import json
import logging
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# PRAGMAs applied before bulk loading — maximize write throughput
BUILD_PRAGMAS = {
    "journal_mode": "OFF",  # no rollback journal during build
    "synchronous": "OFF",  # skip fsync (safe because we swap atomically)
    "cache_size": -2_000_000,  # 2GB page cache
    "temp_store": "MEMORY",
    "mmap_size": 30_000_000_000,
    "locking_mode": "EXCLUSIVE",
}

# PRAGMAs applied after build is complete (before swap)
FINAL_PRAGMAS = {
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "locking_mode": "NORMAL",
}


def build_path(output_dir: str, db_name: str = "current_collection.db") -> Path:
    """Return the path for the in-progress (temp) database file."""
    return Path(output_dir) / (db_name + ".new")


def final_path(output_dir: str, db_name: str = "current_collection.db") -> Path:
    """Return the path for the live database file."""
    return Path(output_dir) / db_name


def open_build_db(output_dir: str, db_name: str = "current_collection.db") -> sqlite3.Connection:
    """Open (or create) the temp build database and apply fast-write PRAGMAs."""
    path = build_path(output_dir, db_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    for pragma, value in BUILD_PRAGMAS.items():
        db.execute(f"PRAGMA {pragma} = {value}")
    logger.info(f"Opened build database: {path}")
    return db


def finalize_db(db: sqlite3.Connection) -> None:
    """Run ANALYZE and re-apply safe PRAGMAs before swapping."""
    logger.info("Running ANALYZE ...")
    db.execute("ANALYZE")
    for pragma, value in FINAL_PRAGMAS.items():
        db.execute(f"PRAGMA {pragma} = {value}")
    logger.info("Database finalized.")


def load_table(
    db: sqlite3.Connection,
    table_name: str,
    rows,
    batch_size: int = 1000,
) -> int:
    """Insert an iterable of row dicts into *table_name*, creating it if needed.

    - The table is created from the column names of the first row (no type
      declarations — SQLite uses dynamic typing).
    - dict/list values are JSON-serialized to strings.
    - datetime/date values are converted to ISO-format strings.
    - Rows are inserted in batches of *batch_size* for efficiency.

    Returns the total number of rows inserted.
    """
    cols: list[str] | None = None
    batch: list[list] = []
    total = 0

    def _flush(cols, batch):
        col_names = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join("?" for _ in cols)
        db.executemany(
            f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})',
            batch,
        )

    def _serialize(v):
        if isinstance(v, (dict, list)):
            return json.dumps(v)
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        return v

    for row in rows:
        if cols is None:
            cols = list(row.keys())
            col_defs = ", ".join(f'"{c}"' for c in cols)
            db.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_defs})')

        batch.append([_serialize(row[c]) for c in cols])
        total += 1

        if len(batch) >= batch_size:
            _flush(cols, batch)
            batch.clear()

    if batch and cols:
        _flush(cols, batch)

    if total:
        logger.info(f"Loaded {total:,} rows into '{table_name}'")
    else:
        logger.warning(f"No rows loaded into '{table_name}'")

    return total


def swap_db(output_dir: str, db_name: str = "current_collection.db") -> None:
    """Atomically replace the live database with the newly built one."""
    src = build_path(output_dir, db_name)
    dst = final_path(output_dir, db_name)
    os.replace(src, dst)
    logger.info(f"Swapped: {src} -> {dst}")
