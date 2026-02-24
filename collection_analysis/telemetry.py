"""
telemetry.py — Persistent pipeline performance tracking.

Manages pipeline_runs.db in output_dir — a SQLite database that accumulates
run history across every pipeline execution and is never wiped or replaced.

Tables:
    run    — one row per pipeline execution (success or failure)
    stage  — one row per stage/table per run

Views:
    v_stage_summary  — avg/min/max per stage across successful runs
    v_recent_runs    — most recent 20 runs with outcome
    v_stage_trends   — per-stage timing over time for trend analysis
"""

import sqlite3
from pathlib import Path

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS run (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at            TEXT NOT NULL,
    completed_at          TEXT,
    total_elapsed_seconds REAL,
    success               INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES run(id),
    stage           TEXT    NOT NULL,
    rows            INTEGER,
    elapsed_seconds REAL    NOT NULL,
    rows_per_sec    REAL
);
"""

_VIEWS = [
    """CREATE VIEW IF NOT EXISTS v_stage_summary AS
SELECT
    stage,
    COUNT(*)                          AS run_count,
    ROUND(AVG(elapsed_seconds), 1)    AS avg_secs,
    ROUND(MIN(elapsed_seconds), 1)    AS min_secs,
    ROUND(MAX(elapsed_seconds), 1)    AS max_secs,
    ROUND(AVG(COALESCE(rows, 0)))     AS avg_rows,
    ROUND(AVG(rows_per_sec))          AS avg_rows_per_sec
FROM stage
JOIN run ON run.id = stage.run_id
WHERE run.success = 1
GROUP BY stage
ORDER BY avg_secs DESC""",
    """CREATE VIEW IF NOT EXISTS v_recent_runs AS
SELECT
    r.id,
    r.started_at,
    r.completed_at,
    ROUND(r.total_elapsed_seconds / 60.0, 1) AS total_minutes,
    CASE r.success WHEN 1 THEN 'success' ELSE 'failed' END AS result
FROM run r
ORDER BY r.id DESC
LIMIT 20""",
    """CREATE VIEW IF NOT EXISTS v_stage_trends AS
SELECT
    s.stage,
    r.id          AS run_id,
    r.started_at  AS run_started,
    s.rows,
    ROUND(s.elapsed_seconds, 1) AS elapsed_secs,
    ROUND(s.rows_per_sec)       AS rows_per_sec
FROM stage s
JOIN run r ON r.id = s.run_id
ORDER BY s.stage, r.id DESC""",
]


def open_telemetry_db(output_dir: str) -> sqlite3.Connection:
    """Open (or create) pipeline_runs.db; apply schema and views."""
    path = Path(output_dir) / "pipeline_runs.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(_SCHEMA_SQL)
    for view_sql in _VIEWS:
        db.execute(view_sql)
    db.commit()
    return db


def start_run(db: sqlite3.Connection, started_at: str) -> int:
    """Insert a new run row (success=0) and return its id."""
    cur = db.execute(
        "INSERT INTO run (started_at, success) VALUES (?, 0)",
        (started_at,),
    )
    db.commit()
    return cur.lastrowid


def finish_run(
    db: sqlite3.Connection,
    run_id: int,
    completed_at: str,
    total_elapsed_seconds: float,
    success: bool,
    stats: list[dict],
) -> None:
    """Update the run row and bulk-insert stage rows, then commit."""
    db.execute(
        """UPDATE run
           SET completed_at = ?, total_elapsed_seconds = ?, success = ?
           WHERE id = ?""",
        (completed_at, total_elapsed_seconds, int(success), run_id),
    )
    db.executemany(
        """INSERT INTO stage (run_id, stage, rows, elapsed_seconds, rows_per_sec)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (
                run_id,
                s["stage"],
                s.get("rows"),
                s["elapsed_seconds"],
                s.get("rows_per_sec"),
            )
            for s in stats
        ],
    )
    db.commit()
