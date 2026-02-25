#!/usr/bin/env python3
"""
report-runs.py — Summarise pipeline_runs.db for human review or AI context.

Usage:
    uv run python scripts/report-runs.py
    uv run python scripts/report-runs.py out/pipeline_runs.db
    uv run python scripts/report-runs.py --last-run          # last run only
    uv run python scripts/report-runs.py --markdown          # Markdown output
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── helpers ──────────────────────────────────────────────────────────────────

def _fmt_secs(secs: float | None) -> str:
    if secs is None:
        return "—"
    if secs < 60:
        return f"{secs:.1f}s"
    m, s = divmod(secs, 60)
    if m < 60:
        return f"{int(m)}m {int(s)}s"
    h, m = divmod(m, 60)
    return f"{int(h)}h {int(m)}m {int(s)}s"


def _fmt_rows(n: int | None) -> str:
    if n is None:
        return "—"
    return f"{n:,}"


def _fmt_rps(rps: float | None) -> str:
    if rps is None:
        return "—"
    if rps >= 1_000:
        return f"{rps/1_000:.1f}k/s"
    return f"{rps:.0f}/s"


def _result_icon(success: int) -> str:
    return "✓" if success else "✗"


def _col(value: str, width: int) -> str:
    return str(value).ljust(width)


# ── queries ───────────────────────────────────────────────────────────────────

def _fetch_runs(db: sqlite3.Connection) -> list[dict]:
    cur = db.execute(
        """SELECT id, started_at, completed_at, total_elapsed_seconds, success
           FROM run ORDER BY id DESC"""
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_stages_for_run(db: sqlite3.Connection, run_id: int) -> list[dict]:
    cur = db.execute(
        """SELECT stage, rows, elapsed_seconds, rows_per_sec
           FROM stage WHERE run_id = ? ORDER BY id""",
        (run_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_stage_summary(db: sqlite3.Connection) -> list[dict]:
    cur = db.execute(
        """SELECT stage, run_count, avg_secs, min_secs, max_secs,
                  avg_rows, avg_rows_per_sec
           FROM v_stage_summary"""
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _count_runs(db: sqlite3.Connection) -> tuple[int, int]:
    row = db.execute(
        "SELECT COUNT(*), SUM(success) FROM run"
    ).fetchone()
    total = row[0] or 0
    successes = int(row[1] or 0)
    return total, successes


# ── report sections ───────────────────────────────────────────────────────────

def _header(db_path: Path, md: bool) -> list[str]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    if md:
        lines += [f"# Pipeline Run Report", f"", f"**DB:** `{db_path}`  "]
        lines += [f"**Generated:** {now}", ""]
    else:
        lines += ["=" * 64]
        lines += [f"  PIPELINE RUN REPORT"]
        lines += [f"  DB:        {db_path}"]
        lines += [f"  Generated: {now}"]
        lines += ["=" * 64, ""]
    return lines


def _section(title: str, md: bool) -> list[str]:
    if md:
        return [f"## {title}", ""]
    return [f"── {title} " + "─" * max(0, 56 - len(title)), ""]


def _runs_table(runs: list[dict], total: int, successes: int, md: bool) -> list[str]:
    lines = []
    lines += [f"Total runs: {total}  |  Successes: {successes}  |  Failures: {total - successes}", ""]

    header = f"{'ID':>4}  {'Started':>19}  {'Completed':>19}  {'Duration':>10}  {'Result':>7}"
    divider = "-" * len(header)

    if md:
        lines += ["| ID | Started | Completed | Duration | Result |"]
        lines += ["|---:|---|---|---:|:---:|"]
        for r in runs:
            icon = _result_icon(r["success"])
            lines.append(
                f"| {r['id']} | {r['started_at'] or '—'} | {r['completed_at'] or '—'} "
                f"| {_fmt_secs(r['total_elapsed_seconds'])} | {icon} |"
            )
    else:
        lines += [header, divider]
        for r in runs:
            icon = _result_icon(r["success"])
            lines.append(
                f"{r['id']:>4}  {(r['started_at'] or '—'):>19}  "
                f"{(r['completed_at'] or '—'):>19}  "
                f"{_fmt_secs(r['total_elapsed_seconds']):>10}  {icon:>7}"
            )
    lines.append("")
    return lines


def _run_detail(run: dict, stages: list[dict], db_path: Path, md: bool) -> list[str]:
    icon = _result_icon(run["success"])
    outcome = "SUCCESS" if run["success"] else "FAILED"
    lines = []
    lines += [f"Run #{run['id']}  |  {outcome} {icon}"]
    lines += [f"  Started:   {run['started_at'] or '—'}"]
    lines += [f"  Completed: {run['completed_at'] or '(not recorded)'}"]
    lines += [f"  Duration:  {_fmt_secs(run['total_elapsed_seconds'])}"]

    if not run["success"]:
        new_db = db_path.parent / "current_collection.db.new"
        if new_db.exists():
            size_mb = new_db.stat().st_size / 1_048_576
            lines += [f"  *.db.new:   present ({size_mb:.0f} MB) — atomic swap never completed"]
        else:
            lines += [f"  *.db.new:   not present"]
    lines.append("")

    if not stages:
        lines += ["  No stages recorded for this run.", ""]
        return lines

    total_stage_secs = sum(s["elapsed_seconds"] for s in stages)
    lines += [f"  Stages completed: {len(stages)}  |  Stage time: {_fmt_secs(total_stage_secs)}", ""]

    if md:
        lines += ["| Stage | Rows | Duration | Rows/sec |"]
        lines += ["|---|---:|---:|---:|"]
        for s in stages:
            lines.append(
                f"| `{s['stage']}` | {_fmt_rows(s['rows'])} "
                f"| {_fmt_secs(s['elapsed_seconds'])} | {_fmt_rps(s['rows_per_sec'])} |"
            )
    else:
        col_w = max(len(s["stage"]) for s in stages) + 2
        hdr = f"  {'Stage':<{col_w}} {'Rows':>12}  {'Duration':>10}  {'Rows/sec':>10}"
        lines += [hdr, "  " + "-" * (len(hdr) - 2)]
        for s in stages:
            lines.append(
                f"  {s['stage']:<{col_w}} {_fmt_rows(s['rows']):>12}  "
                f"{_fmt_secs(s['elapsed_seconds']):>10}  {_fmt_rps(s['rows_per_sec']):>10}"
            )
    lines.append("")
    return lines


def _stage_summary_section(summary: list[dict], md: bool) -> list[str]:
    if not summary:
        return ["  No successful runs — no stage benchmarks available.", ""]

    lines = []
    if md:
        lines += ["| Stage | Runs | Avg | Min | Max | Avg rows | Avg rows/sec |"]
        lines += ["|---|---:|---:|---:|---:|---:|---:|"]
        for s in summary:
            lines.append(
                f"| `{s['stage']}` | {s['run_count']} "
                f"| {_fmt_secs(s['avg_secs'])} | {_fmt_secs(s['min_secs'])} | {_fmt_secs(s['max_secs'])} "
                f"| {_fmt_rows(s['avg_rows'])} | {_fmt_rps(s['avg_rows_per_sec'])} |"
            )
    else:
        col_w = max(len(s["stage"]) for s in summary) + 2
        hdr = f"  {'Stage':<{col_w}} {'Runs':>5}  {'Avg':>10}  {'Min':>10}  {'Max':>10}  {'Avg rows':>12}  {'Rows/sec':>10}"
        lines += [hdr, "  " + "-" * (len(hdr) - 2)]
        for s in summary:
            lines.append(
                f"  {s['stage']:<{col_w}} {s['run_count']:>5}  "
                f"{_fmt_secs(s['avg_secs']):>10}  {_fmt_secs(s['min_secs']):>10}  {_fmt_secs(s['max_secs']):>10}  "
                f"{_fmt_rows(s['avg_rows']):>12}  {_fmt_rps(s['avg_rows_per_sec']):>10}"
            )
    lines.append("")
    return lines


def _failure_analysis(runs: list[dict], db: sqlite3.Connection, md: bool) -> list[str]:
    failed = [r for r in runs if not r["success"]]
    if not failed:
        return ["  No failed runs.", ""]

    lines = []
    for r in failed:
        stages = _fetch_stages_for_run(db, r["id"])
        last = stages[-1]["stage"] if stages else "(no stages)"
        n = len(stages)
        duration = _fmt_secs(r["total_elapsed_seconds"])
        completed = r["completed_at"] or "(not recorded)"
        if md:
            lines += [
                f"**Run #{r['id']}** — started {r['started_at']}, duration {duration}",
                f"- Stages completed: {n}  |  Last stage: `{last}`",
                f"- completed_at: {completed}",
                "",
            ]
        else:
            lines += [
                f"  Run #{r['id']}  started={r['started_at']}  duration={duration}",
                f"    Stages completed: {n}  |  Last stage reached: {last}",
                f"    completed_at: {completed}",
                "",
            ]
    return lines


# ── main ──────────────────────────────────────────────────────────────────────

def build_report(db_path: Path, last_run_only: bool = False, md: bool = False) -> str:
    if not db_path.exists():
        return f"ERROR: {db_path} does not exist.\n"

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row

    runs = _fetch_runs(db)
    if not runs:
        return f"pipeline_runs.db at {db_path} contains no run records.\n"

    total, successes = _count_runs(db)
    out: list[str] = []

    out += _header(db_path, md)

    if last_run_only:
        run = runs[0]
        out += _section(f"Last Run Detail (#{run['id']})", md)
        stages = _fetch_stages_for_run(db, run["id"])
        out += _run_detail(run, stages, db_path, md)
    else:
        # All runs summary
        out += _section("All Runs", md)
        out += _runs_table(runs, total, successes, md)

        # Detail for every run
        for run in runs:
            out += _section(f"Run #{run['id']} Detail", md)
            stages = _fetch_stages_for_run(db, run["id"])
            out += _run_detail(run, stages, db_path, md)

        # Failure analysis
        out += _section("Failure Analysis", md)
        out += _failure_analysis(runs, db, md)

        # Stage benchmarks (successful runs only)
        out += _section("Stage Benchmarks (successful runs only)", md)
        summary = _fetch_stage_summary(db)
        out += _stage_summary_section(summary, md)

    db.close()
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report on pipeline_runs.db"
    )
    parser.add_argument(
        "db",
        nargs="?",
        default=None,
        help="Path to pipeline_runs.db (default: out/pipeline_runs.db)",
    )
    parser.add_argument(
        "--last-run",
        action="store_true",
        help="Show detail for the most recent run only",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output as Markdown",
    )
    args = parser.parse_args()

    if args.db:
        db_path = Path(args.db)
    else:
        # default: relative to this script's parent (project root)
        project_root = Path(__file__).parent.parent
        db_path = project_root / "out" / "pipeline_runs.db"

    print(build_report(db_path, last_run_only=args.last_run, md=args.markdown))


if __name__ == "__main__":
    main()
