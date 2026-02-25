"""
run.py — Main entry point for the collection analysis pipeline.

Usage:
    python -m collection_analysis.run
    python -m collection_analysis.run --config /path/to/config.json

What it does:
    1. Load config
    2. Configure logging (level + optional file handler)
    3. Open persistent telemetry DB
    4. Connect to Sierra PostgreSQL
    5. Open temp SQLite build database with fast-write PRAGMAs
    6. Extract each table from Sierra and load into SQLite (with per-table timing)
    7. Create views (sql/views/)
    8. Create indexes (sql/indexes/)
    9. Finalize (ANALYZE, re-apply safe PRAGMAs)
    10. Write run stats snapshot into build DB
    11. Atomically swap temp database -> live database
    12. Record telemetry and print stage summary
"""

import argparse
import itertools
import logging
import time
from datetime import datetime

from sqlalchemy import create_engine

from . import config as cfg_module
from . import extract, load, telemetry, transform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _configure_logging(cfg: dict) -> None:
    """Set log level and optionally attach a file handler from config."""
    level = getattr(logging, cfg.get("log_level", "INFO").upper(), logging.INFO)
    logging.getLogger().setLevel(level)
    log_file = cfg.get("log_file")
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logging.getLogger().addHandler(fh)
        logger.info(f"Logging to file: {log_file}")


def _timed_load(db, name: str, rows) -> tuple[int, float]:
    """Load rows into *name* and return (row_count, elapsed_seconds)."""
    t0 = time.perf_counter()
    n = load.load_table(db, name, rows)
    elapsed = time.perf_counter() - t0
    rate = n / elapsed if elapsed > 0 else 0.0
    logger.info(f"    -> {elapsed:.1f}s  ({rate:,.0f} rows/sec)")
    return n, elapsed


def _write_run_stats(db, run_started: str, stats: list[dict]) -> None:
    """Write a snapshot of run stats into the build DB as _pipeline_run."""
    rows = ({"run_started": run_started, **s} for s in stats)
    load.load_table(db, "_pipeline_run", rows)


def _log_summary(stats: list[dict], elapsed: float) -> None:
    """Log a human-readable stage timing table."""
    logger.info("--- Stage summary ---")
    logger.info(f"  {'stage':<40} {'rows':>10} {'secs':>8} {'rows/sec':>12}")
    for s in stats:
        rows_str = f"{s['rows']:>10,}" if s["rows"] is not None else f"{'':>10}"
        rate_str = (
            f"{s['rows_per_sec']:>12,.0f}" if s.get("rows_per_sec") else f"{'':>12}"
        )
        logger.info(
            f"  {s['stage']:<40} {rows_str} {s['elapsed_seconds']:>8.1f} {rate_str}"
        )
    logger.info(f"  {'TOTAL':<40} {'':>10} {elapsed:>8.1f}")


def main():
    parser = argparse.ArgumentParser(description="collection-analysis pipeline")
    parser.add_argument(
        "--config",
        default=None,
        help="(Deprecated) path to config.json; use .env or env vars instead",
    )
    args = parser.parse_args()

    start = time.time()
    logger.info(f"Pipeline started at {datetime.now().isoformat()}")

    cfg = cfg_module.load(args.config)
    _configure_logging(cfg)
    logger.info(f"Output directory: {cfg['output_dir']}")

    run_started = datetime.now().isoformat(timespec="seconds")
    tel_db = telemetry.open_telemetry_db(cfg["output_dir"])
    run_id = telemetry.start_run(tel_db, run_started)
    stats: list[dict] = []
    success = False

    try:
        db = load.open_build_db(cfg["output_dir"])
        itersize = cfg["pg_itersize"]
        sleep_between = cfg.get("pg_sleep_between_tables", 0.0)
        extract_limit = cfg.get("extract_limit", 0)
        if extract_limit > 0:
            logger.warning(
                "EXTRACT_LIMIT=%d — each table capped at %d rows. "
                "This is a SAMPLE database, not suitable for production.",
                extract_limit, extract_limit,
            )

        engine = create_engine(cfg_module.pg_connection_string(cfg))
        with engine.connect() as pg:
            logger.info("Extracting tables from Sierra ...")

            for name, gen in [
                ("record_metadata", extract.extract_record_metadata(pg, itersize)),
                ("bib", extract.extract_bib(pg, itersize)),
                ("item", extract.extract_item(pg, itersize)),
                ("bib_record", extract.extract_bib_record(pg, itersize)),
                ("volume_record", extract.extract_volume_record(pg, itersize)),
                ("item_message", extract.extract_item_message(pg, itersize)),
                ("language_property", extract.extract_language_property(pg, itersize)),
                (
                    "bib_record_item_record_link",
                    extract.extract_bib_record_item_record_link(pg, itersize),
                ),
                (
                    "volume_record_item_record_link",
                    extract.extract_volume_record_item_record_link(pg, itersize),
                ),
                ("location", extract.extract_location(pg, itersize)),
                ("location_name", extract.extract_location_name(pg, itersize)),
                ("branch_name", extract.extract_branch_name(pg, itersize)),
                ("branch", extract.extract_branch(pg, itersize)),
                (
                    "country_property_myuser",
                    extract.extract_country_property_myuser(pg, itersize),
                ),
                (
                    "item_status_property",
                    extract.extract_item_status_property(pg, itersize),
                ),
                ("itype_property", extract.extract_itype_property(pg, itersize)),
                (
                    "bib_level_property",
                    extract.extract_bib_level_property(pg, itersize),
                ),
                (
                    "material_property",
                    extract.extract_material_property(pg, itersize),
                ),
                ("hold", extract.extract_hold(pg, itersize)),
                ("circ_agg", extract.extract_circ_agg(pg, itersize)),
                (
                    "circ_leased_items",
                    extract.extract_circ_leased_items(pg, itersize),
                ),
            ]:
                capped = itertools.islice(gen, extract_limit) if extract_limit > 0 else gen
                n, elapsed = _timed_load(db, name, capped)
                stats.append(
                    {
                        "stage": name,
                        "rows": n,
                        "elapsed_seconds": round(elapsed, 3),
                        "rows_per_sec": round(n / elapsed, 1) if elapsed > 0 else None,
                    }
                )
                if sleep_between > 0:
                    logger.debug("  sleeping %.1fs (PG_SLEEP_BETWEEN_TABLES) ...", sleep_between)
                    time.sleep(sleep_between)

        t0 = time.perf_counter()
        logger.info("Creating views ...")
        transform.create_views(db)
        stats.append(
            {
                "stage": "views",
                "rows": None,
                "elapsed_seconds": round(time.perf_counter() - t0, 3),
                "rows_per_sec": None,
            }
        )

        t0 = time.perf_counter()
        logger.info("Creating indexes ...")
        transform.create_indexes(db)
        stats.append(
            {
                "stage": "indexes",
                "rows": None,
                "elapsed_seconds": round(time.perf_counter() - t0, 3),
                "rows_per_sec": None,
            }
        )

        t0 = time.perf_counter()
        load.finalize_db(db)
        stats.append(
            {
                "stage": "finalize",
                "rows": None,
                "elapsed_seconds": round(time.perf_counter() - t0, 3),
                "rows_per_sec": None,
            }
        )

        _write_run_stats(db, run_started, stats)
        load.swap_db(cfg["output_dir"])
        success = True

    finally:
        elapsed = time.time() - start
        telemetry.finish_run(
            tel_db,
            run_id,
            datetime.now().isoformat(timespec="seconds"),
            elapsed,
            success,
            stats,
        )
        tel_db.close()
        _log_summary(stats, elapsed)

    logger.info(f"Pipeline complete in {elapsed / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
