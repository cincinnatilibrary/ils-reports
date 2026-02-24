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
"""

import argparse
import logging
import time
from datetime import datetime

from sqlalchemy import create_engine

from . import config as cfg_module
from . import extract, load, transform

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
    itersize = cfg["pg_itersize"]

    engine = create_engine(cfg_module.pg_connection_string(cfg))
    with engine.connect() as pg:
        logger.info("Extracting tables from Sierra ...")

        load.load_table(db, "record_metadata", extract.extract_record_metadata(pg, itersize))
        load.load_table(db, "bib", extract.extract_bib(pg, itersize))
        load.load_table(db, "item", extract.extract_item(pg, itersize))
        load.load_table(db, "bib_record", extract.extract_bib_record(pg, itersize))
        load.load_table(db, "volume_record", extract.extract_volume_record(pg, itersize))
        load.load_table(db, "item_message", extract.extract_item_message(pg, itersize))
        load.load_table(db, "language_property", extract.extract_language_property(pg, itersize))
        load.load_table(
            db,
            "bib_record_item_record_link",
            extract.extract_bib_record_item_record_link(pg, itersize),
        )
        load.load_table(
            db,
            "volume_record_item_record_link",
            extract.extract_volume_record_item_record_link(pg, itersize),
        )
        load.load_table(db, "location", extract.extract_location(pg, itersize))
        load.load_table(db, "location_name", extract.extract_location_name(pg, itersize))
        load.load_table(db, "branch_name", extract.extract_branch_name(pg, itersize))
        load.load_table(db, "branch", extract.extract_branch(pg, itersize))
        load.load_table(
            db,
            "country_property_myuser",
            extract.extract_country_property_myuser(pg, itersize),
        )
        load.load_table(
            db,
            "item_status_property",
            extract.extract_item_status_property(pg, itersize),
        )
        load.load_table(db, "itype_property", extract.extract_itype_property(pg, itersize))
        load.load_table(db, "bib_level_property", extract.extract_bib_level_property(pg, itersize))
        load.load_table(db, "material_property", extract.extract_material_property(pg, itersize))
        load.load_table(db, "hold", extract.extract_hold(pg, itersize))
        load.load_table(db, "circ_agg", extract.extract_circ_agg(pg, itersize))
        load.load_table(db, "circ_leased_items", extract.extract_circ_leased_items(pg, itersize))

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
