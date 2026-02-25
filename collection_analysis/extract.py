"""
extract.py — Query Sierra PostgreSQL and yield rows for each table.

All queries target the `sierra_view` schema. Each function accepts a
SQLAlchemy connection and yields rows as RowMapping dicts.

Extraction functions:
    extract_record_metadata(pg_conn, itersize)
    extract_bib(pg_conn, itersize)
    extract_item(pg_conn, itersize)
    extract_bib_record(pg_conn, itersize)
    extract_volume_record(pg_conn, itersize)
    extract_item_message(pg_conn, itersize)
    extract_language_property(pg_conn, itersize)
    extract_bib_record_item_record_link(pg_conn, itersize)
    extract_volume_record_item_record_link(pg_conn, itersize)
    extract_location(pg_conn, itersize)
    extract_location_name(pg_conn, itersize)
    extract_branch_name(pg_conn, itersize)
    extract_branch(pg_conn, itersize)
    extract_country_property_myuser(pg_conn, itersize)
    extract_item_status_property(pg_conn, itersize)
    extract_itype_property(pg_conn, itersize)
    extract_bib_level_property(pg_conn, itersize)
    extract_material_property(pg_conn, itersize)
    extract_hold(pg_conn, itersize)
    extract_circ_agg(pg_conn, itersize)
    extract_circ_leased_items(pg_conn, itersize)

All functions yield RowMapping objects (dict-like).
"""

import logging
from pathlib import Path

from sqlalchemy import text

logger = logging.getLogger(__name__)

# Full-rebuild target date: fetch all records regardless of update time.
_TARGET_DATE = "1969-01-01 00:00:00"

_SQL_DIR = Path(__file__).parent.parent / "sql" / "queries"


def _load_sql(name: str) -> str:
    return (_SQL_DIR / f"{name}.sql").read_text()


def extract_record_metadata(pg_conn, itersize: int = 5000):
    """Yield record_metadata rows for bib ('b'), item ('i'), and volume ('j') records."""
    sql = text(_load_sql("record_metadata"))
    id_val = 0
    total = 0
    while True:
        rows = (
            pg_conn.execute(
                sql, {"target_date": _TARGET_DATE, "id_val": id_val, "limit_val": itersize}
            )
            .mappings()
            .all()
        )
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["record_id"]
        logger.info(f"  record_metadata: {total} rows (cursor at id {id_val})")


def extract_bib(pg_conn, itersize: int = 5000):
    """Yield bib rows with aggregated JSON fields."""
    sql = text(_load_sql("bib"))
    id_val = 0
    total = 0
    while True:
        rows = (
            pg_conn.execute(
                sql, {"target_date": _TARGET_DATE, "id_val": id_val, "limit_val": itersize}
            )
            .mappings()
            .all()
        )
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["bib_record_id"]
        logger.info(f"  bib: {total} rows (cursor at id {id_val})")


def extract_item(pg_conn, itersize: int = 5000):
    """Yield item rows with join to bib, checkout, volume, and format lookup."""
    sql = text(_load_sql("item"))
    id_val = 0
    total = 0
    while True:
        rows = (
            pg_conn.execute(
                sql, {"target_date": _TARGET_DATE, "id_val": id_val, "limit_val": itersize}
            )
            .mappings()
            .all()
        )
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["item_record_id"]
        logger.info(f"  item: {total} rows (cursor at id {id_val})")


def extract_bib_record(pg_conn, itersize: int = 5000):
    """Yield bib_record rows (MARC-level bib metadata)."""
    sql = text(_load_sql("bib_record"))
    id_val = 0
    total = 0
    while True:
        rows = (
            pg_conn.execute(
                sql, {"target_date": _TARGET_DATE, "id_val": id_val, "limit_val": itersize}
            )
            .mappings()
            .all()
        )
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["id"]
        logger.info(f"  bib_record: {total} rows (cursor at id {id_val})")


def extract_volume_record(pg_conn, itersize: int = 5000):
    """Yield volume_record rows with bib linkage."""
    sql = text(_load_sql("volume_record"))
    id_val = 0
    total = 0
    while True:
        rows = (
            pg_conn.execute(
                sql, {"target_date": _TARGET_DATE, "id_val": id_val, "limit_val": itersize}
            )
            .mappings()
            .all()
        )
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["volume_record_id"]
        logger.info(f"  volume_record: {total} rows (cursor at id {id_val})")


def extract_item_message(pg_conn, itersize: int = 5000):
    """Yield item_message rows (in-transit and status message fields)."""
    sql = text(_load_sql("item_message"))
    id_val = 0
    total = 0
    while True:
        rows = pg_conn.execute(sql, {"id_val": id_val, "limit_val": itersize}).mappings().all()
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["varfield_id"]
        logger.info(f"  item_message: {total} rows (cursor at id {id_val})")


def extract_language_property(pg_conn, itersize: int = 5000):
    """Yield language_property lookup rows."""
    sql = text(_load_sql("language_property"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  language_property: {len(rows)} rows")
    yield from rows


def extract_bib_record_item_record_link(pg_conn, itersize: int = 5000):
    """Yield bib_record_item_record_link rows."""
    sql = text(_load_sql("bib_record_item_record_link"))
    id_val = 0
    total = 0
    while True:
        rows = pg_conn.execute(sql, {"id_val": id_val, "limit_val": itersize}).mappings().all()
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["id"]
        logger.info(f"  bib_record_item_record_link: {total} rows (cursor at id {id_val})")


def extract_volume_record_item_record_link(pg_conn, itersize: int = 5000):
    """Yield volume_record_item_record_link rows."""
    sql = text(_load_sql("volume_record_item_record_link"))
    id_val = 0
    total = 0
    while True:
        rows = pg_conn.execute(sql, {"id_val": id_val, "limit_val": itersize}).mappings().all()
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["id"]
        logger.info(f"  volume_record_item_record_link: {total} rows (cursor at id {id_val})")


def extract_location(pg_conn, itersize: int = 5000):
    """Yield location rows."""
    sql = text(_load_sql("location"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  location: {len(rows)} rows")
    yield from rows


def extract_location_name(pg_conn, itersize: int = 5000):
    """Yield location_name rows."""
    sql = text(_load_sql("location_name"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  location_name: {len(rows)} rows")
    yield from rows


def extract_branch_name(pg_conn, itersize: int = 5000):
    """Yield branch_name rows."""
    sql = text(_load_sql("branch_name"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  branch_name: {len(rows)} rows")
    yield from rows


def extract_branch(pg_conn, itersize: int = 5000):
    """Yield branch rows."""
    sql = text(_load_sql("branch"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  branch: {len(rows)} rows")
    yield from rows


def extract_country_property_myuser(pg_conn, itersize: int = 5000):
    """Yield country_property_myuser lookup rows."""
    sql = text(_load_sql("country_property_myuser"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  country_property_myuser: {len(rows)} rows")
    yield from rows


def extract_item_status_property(pg_conn, itersize: int = 5000):
    """Yield item_status_property lookup rows."""
    sql = text(_load_sql("item_status_property"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  item_status_property: {len(rows)} rows")
    yield from rows


def extract_itype_property(pg_conn, itersize: int = 5000):
    """Yield itype_property lookup rows (item format names)."""
    sql = text(_load_sql("itype_property"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  itype_property: {len(rows)} rows")
    yield from rows


def extract_bib_level_property(pg_conn, itersize: int = 5000):
    """Yield bib_level_property lookup rows."""
    sql = text(_load_sql("bib_level_property"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  bib_level_property: {len(rows)} rows")
    yield from rows


def extract_material_property(pg_conn, itersize: int = 5000):
    """Yield material_property lookup rows."""
    sql = text(_load_sql("material_property"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  material_property: {len(rows)} rows")
    yield from rows


def extract_hold(pg_conn, itersize: int = 5000):
    """Yield hold rows with patron metadata."""
    sql = text(_load_sql("hold"))
    id_val = 0
    total = 0
    while True:
        rows = pg_conn.execute(sql, {"id_val": id_val, "limit_val": itersize}).mappings().all()
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["hold_id"]
        logger.info(f"  hold: {total} rows (cursor at id {id_val})")


def extract_circ_agg(pg_conn, itersize: int = 5000):
    """Yield circ_agg rows — aggregated circulation transactions for the last 6 months."""
    sql = text(_load_sql("circ_agg"))
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  circ_agg: {len(rows)} rows")
    yield from rows


def extract_circ_leased_items(pg_conn, itersize: int = 5000):
    """Yield circ_leased_items rows — checkout/checkin activity for leased items (last 180 days)."""
    sql = text(_load_sql("circ_leased_items"))
    id_val = 0
    total = 0
    while True:
        rows = pg_conn.execute(sql, {"id_val": id_val, "limit_val": itersize}).mappings().all()
        if not rows:
            break
        yield from rows
        total += len(rows)
        id_val = rows[-1]["id"]
        logger.info(f"  circ_leased_items: {total} rows (cursor at id {id_val})")
