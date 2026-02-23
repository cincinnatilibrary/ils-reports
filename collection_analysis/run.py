"""
run.py — Main entry point for the collection analysis pipeline.

Usage:
    python -m collection_analysis.run
    python -m collection_analysis.run --config /path/to/config.json

What it does:
    1. Load config
    2. Connect to Sierra PostgreSQL
    3. Open temp SQLite build database with fast-write PRAGMAs
    4. Extract each table from Sierra and load into SQLite
    5. Create views (sql/views/)
    6. Create indexes (sql/indexes/)
    7. Finalize (ANALYZE, re-apply safe PRAGMAs)
    8. Atomically swap temp database -> live database

TODO: Wire up extract.py calls once queries are ported from the reference notebook.
"""

import argparse
import logging
import time
from datetime import datetime

from . import config as cfg_module
from . import load, transform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="collection-analysis pipeline")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json (default: ./config.json)",
    )
    args = parser.parse_args()

    start = time.time()
    logger.info(f"Pipeline started at {datetime.now().isoformat()}")

    cfg = cfg_module.load(args.config)
    logger.info(f"Output directory: {cfg['output_dir']}")

    db = load.open_build_db(cfg["output_dir"])

    # TODO: connect to Sierra and load each table
    # from sqlalchemy import create_engine, text
    # engine = create_engine(cfg_module.pg_connection_string(cfg))
    # with engine.connect() as pg:
    #     load_table(db, "bib", extract.extract_bib(pg, cfg["pg_itersize"]))
    #     ...

    logger.info("Creating views ...")
    transform.create_views(db)

    logger.info("Creating indexes ...")
    transform.create_indexes(db)

    load.finalize_db(db)
    load.swap_db(cfg["output_dir"])

    elapsed = time.time() - start
    logger.info(f"Pipeline complete in {elapsed / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
