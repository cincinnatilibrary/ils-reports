"""
load.py — Write extracted data into a SQLite database with optimized settings.

Handles:
  - Opening a SQLite connection with build-time PRAGMAs for maximum write speed
  - Bulk-inserting rows using sqlite-utils
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

import logging
import os
from pathlib import Path

import sqlite_utils

logger = logging.getLogger(__name__)

# PRAGMAs applied before bulk loading — maximize write throughput
BUILD_PRAGMAS = {
    "journal_mode": "OFF",       # no rollback journal during build
    "synchronous": "OFF",        # skip fsync (safe because we swap atomically)
    "cache_size": -2_000_000,    # 2GB page cache
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


def open_build_db(output_dir: str, db_name: str = "current_collection.db") -> sqlite_utils.Database:
    """Open (or create) the temp build database and apply fast-write PRAGMAs."""
    path = build_path(output_dir, db_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite_utils.Database(path)
    for pragma, value in BUILD_PRAGMAS.items():
        db.execute(f"PRAGMA {pragma} = {value}")
    logger.info(f"Opened build database: {path}")
    return db


def finalize_db(db: sqlite_utils.Database) -> None:
    """Run ANALYZE and re-apply safe PRAGMAs before swapping."""
    logger.info("Running ANALYZE ...")
    db.execute("ANALYZE")
    for pragma, value in FINAL_PRAGMAS.items():
        db.execute(f"PRAGMA {pragma} = {value}")
    logger.info("Database finalized.")


def swap_db(output_dir: str, db_name: str = "current_collection.db") -> None:
    """Atomically replace the live database with the newly built one."""
    src = build_path(output_dir, db_name)
    dst = final_path(output_dir, db_name)
    os.replace(src, dst)
    logger.info(f"Swapped: {src} -> {dst}")
