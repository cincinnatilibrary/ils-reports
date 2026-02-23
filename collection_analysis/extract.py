"""
extract.py — Query Sierra PostgreSQL and yield rows for each table.

All queries target the `sierra_view` schema. Each function accepts a
SQLAlchemy connection and yields rows as dicts (or returns a DataFrame).

Extraction functions are named after the SQLite table they populate:
    extract_bib()
    extract_item()
    extract_record_metadata()
    extract_bib_record()
    extract_volume_record()
    extract_bib_record_item_record_link()
    extract_volume_record_item_record_link()
    extract_hold()
    extract_circ_agg()
    ... etc.

TODO: Port queries from reference/collection-analysis.cincy.pl_gen_db.ipynb
"""

import logging

logger = logging.getLogger(__name__)
