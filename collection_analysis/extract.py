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

from sqlalchemy import text

logger = logging.getLogger(__name__)

# Full-rebuild target date: fetch all records regardless of update time.
_TARGET_DATE = "1969-01-01 00:00:00"


def extract_record_metadata(pg_conn, itersize: int = 5000):
    """Yield record_metadata rows for bib ('b'), item ('i'), and volume ('j') records."""
    sql = text("""\
WITH record_data AS (
    SELECT r.id
    FROM sierra_view.record_metadata AS r
    WHERE r.record_type_code IN ('b', 'i', 'j')
    AND r.campus_code = ''
    AND (
        r.deletion_date_gmt >= :target_date :: timestamptz
        OR r.record_last_updated_gmt >= :target_date :: timestamptz
    )
    AND r.id > :id_val
    ORDER BY r.id ASC
    LIMIT :limit_val
)
SELECT
    d.id AS record_id,
    r.record_num AS record_num,
    r.record_type_code,
    to_char(r.creation_date_gmt, 'J') :: INTEGER AS creation_julianday,
    to_char(r.record_last_updated_gmt, 'J') :: INTEGER AS record_last_updated_julianday,
    to_char(r.deletion_date_gmt, 'J') :: INTEGER AS deletion_julianday
FROM record_data AS d
JOIN sierra_view.record_metadata AS r ON r.id = d.id
""")
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
    sql = text("""\
WITH r AS (
    SELECT
        rm.id,
        rm.record_num AS bib_record_num,
        rm.record_last_updated_gmt :: date AS record_last_updated
    FROM sierra_view.record_metadata AS rm
    WHERE
        rm.record_type_code = 'b'
        AND rm.campus_code = ''
        AND rm.deletion_date_gmt IS NULL
        AND rm.record_last_updated_gmt >= :target_date :: timestamptz
        AND rm.id > :id_val
    ORDER BY rm.id ASC
    LIMIT :limit_val
)
SELECT
    r.bib_record_num,
    r.id AS bib_record_id,
    (
        SELECT json_agg(po.index_entry ORDER BY po.occurrence, po.id)
        FROM sierra_view.phrase_entry AS po
        WHERE po.record_id = r.id
            AND po.index_tag = 'o'
            AND po.varfield_type_code = 'o'
    ) AS control_numbers,
    (
        WITH isbns AS (
            SELECT regexp_matches(
                v.field_content,
                '[0-9]{9,10}[x]{0,1}|[0-9]{12,13}[x]{0,1}',
                'i'
            ) AS matches
            FROM sierra_view.varfield AS v
            WHERE v.record_id = r.id
                AND v.marc_tag || v.varfield_type_code = '020i'
            ORDER BY v.occ_num
        )
        SELECT json_agg(isbns.matches[1]) FROM isbns
    ) AS isbn_values,
    p.best_author,
    p.best_title,
    (
        SELECT s.content
        FROM sierra_view.subfield AS s
        WHERE s.record_id = r.id
            AND s.field_type_code = 'p'
            AND s.tag = 'b'
        ORDER BY s.display_order
        LIMIT 1
    ) AS publisher,
    p.publish_year,
    (
        SELECT pc.index_entry
        FROM sierra_view.phrase_entry AS pc
        WHERE pc.record_id = r.id
            AND pc.index_tag = 'c'
            AND pc.varfield_type_code = 'c'
        ORDER BY pc.id
        LIMIT 1
    ) AS bib_level_callnumber,
    (
        SELECT json_agg(p.index_entry ORDER BY p.occurrence, p.id)
        FROM sierra_view.phrase_entry AS p
        WHERE p.record_id = r.id
            AND p.index_tag = 'd'
    ) AS indexed_subjects,
    (
        SELECT json_agg(s."content" ORDER BY s.occ_num)
        FROM sierra_view.record_metadata rm
        JOIN sierra_view.varfield AS v ON (v.varfield_type_code = 'j' AND v.record_id = rm.id)
        JOIN sierra_view.subfield AS s ON s.varfield_id = v.id
        WHERE (rm.record_type_code = 'b' AND rm.record_num = r.bib_record_num AND rm.campus_code = '')
            AND s.tag = 'a'
    ) AS genres,
    (
        WITH attached_items AS (
            SELECT ir.itype_code_num, count(*) AS count_items
            FROM sierra_view.bib_record_item_record_link AS brirl
            JOIN sierra_view.item_record AS ir ON ir.record_id = brirl.item_record_id
            WHERE brirl.bib_record_id = r.id
            GROUP BY 1
        )
        SELECT json_agg(ipn."name" ORDER BY count_items DESC)
        FROM attached_items
        JOIN sierra_view.itype_property AS ip ON ip.code_num = attached_items.itype_code_num
        JOIN sierra_view.itype_property_name AS ipn ON ipn.itype_property_id = ip.id
    ) AS item_types,
    br.cataloging_date_gmt :: date AS cataloging_date
FROM r
JOIN sierra_view.bib_record AS br ON br.record_id = r.id
LEFT OUTER JOIN sierra_view.bib_record_property AS p ON p.bib_record_id = r.id
""")
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
    sql = text("""\
WITH r AS (
    SELECT
        rm.id,
        rm.record_num,
        rm.creation_date_gmt,
        rm.record_last_updated_gmt
    FROM sierra_view.record_metadata AS rm
    WHERE
        rm.record_type_code = 'i'
        AND rm.campus_code = ''
        AND rm.deletion_date_gmt IS NULL
        AND rm.record_last_updated_gmt >= :target_date :: timestamptz
        AND rm.id > :id_val
    ORDER BY rm.id ASC
    LIMIT :limit_val
),
temp_map_item_type AS (
    SELECT p.code_num AS code, n.name AS name
    FROM sierra_view.itype_property AS p
    JOIN sierra_view.itype_property_name AS n ON n.itype_property_id = p.id
)
SELECT
    r.record_num AS item_record_num,
    r.id AS item_record_id,
    br.record_num AS bib_record_num,
    r.creation_date_gmt :: date AS creation_date,
    r.record_last_updated_gmt :: date AS record_last_updated,
    p.barcode,
    i.agency_code_num,
    i.location_code,
    i.checkout_statistic_group_code_num,
    i.checkin_statistics_group_code_num,
    c.checkout_gmt :: date AS checkout_date,
    c.due_gmt :: date AS due_date,
    (
        SELECT p.home_library_code
        FROM sierra_view.patron_record AS p
        WHERE p.record_id = c.patron_record_id
        LIMIT 1
    ) AS patron_branch_code,
    i.last_checkout_gmt :: date AS last_checkout_date,
    i.last_checkin_gmt :: date AS last_checkin_date,
    i.checkout_total,
    i.renewal_total,
    (
        SELECT t.name
        FROM temp_map_item_type AS t
        WHERE t.code = i.itype_code_num
        LIMIT 1
    ) AS item_format,
    i.item_status_code,
    (i.price * 100.0) :: INTEGER AS price_cents,
    p.call_number_norm AS item_callnumber,
    rm2.record_num AS volume_record_num,
    (
        SELECT string_agg(v.field_content, ', ' ORDER BY v.occ_num)
        FROM sierra_view.varfield AS v
        WHERE v.record_id = rm2.id
            AND v.varfield_type_code = 'v'
    ) AS volume_record_statement
FROM r
JOIN sierra_view.item_record_property AS p ON p.item_record_id = r.id
JOIN sierra_view.item_record AS i ON i.record_id = r.id
LEFT OUTER JOIN sierra_view.checkout AS c ON c.item_record_id = r.id
JOIN sierra_view.bib_record_item_record_link AS l ON l.item_record_id = r.id
JOIN sierra_view.record_metadata AS br ON br.id = l.bib_record_id
LEFT OUTER JOIN sierra_view.volume_record_item_record_link AS vrirl ON vrirl.item_record_id = r.id
LEFT OUTER JOIN sierra_view.record_metadata AS rm2 ON rm2.id = vrirl.volume_record_id
""")
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
    sql = text("""\
SELECT
    b.id,
    b.record_id,
    b.language_code,
    b.bcode1,
    b.bcode2,
    b.bcode3,
    b.country_code,
    b.index_change_count,
    b.is_on_course_reserve,
    b.is_right_result_exact,
    b.allocation_rule_code,
    b.skip_num,
    date(b.cataloging_date_gmt) AS cataloging_date_gmt,
    b.marc_type_code,
    b.is_suppressed
FROM sierra_view.bib_record AS b
JOIN sierra_view.record_metadata AS r ON r.id = b.record_id
WHERE
    r.campus_code = ''
    AND r.record_last_updated_gmt >= :target_date :: timestamptz
    AND b.id > :id_val
ORDER BY b.id ASC
LIMIT :limit_val
""")
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
    sql = text("""\
SELECT
    rm.id AS volume_record_id,
    rm.record_num AS volume_record_num,
    rm2.id AS bib_record_id,
    rm2.record_num AS bib_record_num,
    to_char(rm.creation_date_gmt, 'J') :: INTEGER AS creation_julianday,
    (
        SELECT string_agg(v.field_content, ', ' ORDER BY v.occ_num)
        FROM sierra_view.varfield AS v
        WHERE v.record_id = vr.record_id
    ) AS volume_statement
FROM sierra_view.volume_record AS vr
JOIN sierra_view.record_metadata AS rm ON rm.id = vr.record_id
JOIN sierra_view.bib_record_volume_record_link AS brvrl ON brvrl.volume_record_id = vr.record_id
JOIN sierra_view.record_metadata rm2 ON rm2.id = brvrl.bib_record_id
WHERE
    rm.record_last_updated_gmt >= :target_date :: timestamptz
    AND rm.id > :id_val
ORDER BY rm.id ASC
LIMIT :limit_val
""")
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
    sql = text("""\
WITH item_messages AS (
    SELECT
        r.record_num AS item_record_num,
        r.id AS item_record_id,
        r.campus_code,
        v.id AS varfield_id,
        v.occ_num,
        v.field_content,
        v.field_content ~* '.*IN\\sTRANSIT.*' AS has_in_transit,
        v.field_content ~* '.*IN\\sTRANSIT\\sTOO\\sLONG.*' AS has_in_transit_too_long,
        regexp_matches(
            v.field_content,
            '.*IN\\sTRANSIT\\sfrom\\s([0-9a-z]{1,})\\sto\\s([0-9a-z]{1,})',
            'gi'
        ) AS transit_from_to,
        (
            regexp_matches(
                v.field_content,
                '^[a-z]{3}\\s[a-z]{1,3}\\s[0-9]{2}\\s[0-9]{4}\\s[0-9]{2}\\:[0-9]{2}(?:AM|PM)',
                'gi'
            )
        )[1] AS transit_time_string
    FROM sierra_view.record_metadata AS r
    JOIN sierra_view.varfield AS v ON v.record_id = r.id
    WHERE
        r.record_type_code = 'i'
        AND v.varfield_type_code = 'm'
        AND v.id > :id_val
    ORDER BY v.id ASC, v.occ_num ASC
    LIMIT :limit_val
)
SELECT
    irp.barcode AS item_barcode,
    item_messages.campus_code,
    irp.call_number,
    item_messages.item_record_id,
    item_messages.varfield_id,
    item_messages.has_in_transit,
    TO_CHAR(item_messages.transit_time_string :: TIMESTAMP, 'J') :: INTEGER AS in_transit_julianday,
    TO_CHAR('NOW' :: TIMESTAMP, 'J') :: INTEGER
        - TO_CHAR(item_messages.transit_time_string :: TIMESTAMP, 'J') :: INTEGER AS in_transit_days,
    transit_from_to[1] AS transit_from,
    transit_from_to[2] AS transit_to,
    item_messages.has_in_transit_too_long,
    item_messages.occ_num,
    item_messages.field_content,
    brp.publish_year,
    brp.best_title,
    brp.best_author,
    ir.item_status_code,
    ispn."name" AS item_status_name,
    ir.agency_code_num,
    ir.location_code,
    ir.itype_code_num,
    ipn."name" AS item_format,
    TO_CHAR(c.due_gmt, 'J') :: INTEGER AS due_julianday,
    c.loanrule_code_num,
    TO_CHAR(c.checkout_gmt, 'J') :: INTEGER AS checkout_julianday,
    c.renewal_count,
    c.overdue_count,
    TO_CHAR(c.overdue_gmt, 'J') :: INTEGER AS overdue_julianday
FROM item_messages
LEFT OUTER JOIN sierra_view.item_record_property AS irp ON irp.item_record_id = item_messages.item_record_id
LEFT OUTER JOIN sierra_view.item_record AS ir ON ir.record_id = item_messages.item_record_id
LEFT OUTER JOIN sierra_view.checkout AS c ON c.item_record_id = ir.record_id
LEFT OUTER JOIN sierra_view.item_status_property AS isp ON isp.code = ir.item_status_code
LEFT OUTER JOIN sierra_view.item_status_property_name AS ispn ON ispn.item_status_property_id = isp.id
LEFT OUTER JOIN sierra_view.bib_record_item_record_link AS brirl ON brirl.item_record_id = item_messages.item_record_id
LEFT OUTER JOIN sierra_view.bib_record_property AS brp ON brp.bib_record_id = brirl.bib_record_id
LEFT OUTER JOIN sierra_view.itype_property AS ip ON ip.code_num = ir.itype_code_num
LEFT OUTER JOIN sierra_view.itype_property_name AS ipn ON ipn.itype_property_id = ip.id
""")
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
    sql = text("""\
SELECT
    p.id,
    p.code,
    p.display_order,
    n.name
FROM sierra_view.language_property AS p
JOIN sierra_view.language_property_name AS n ON n.language_property_id = p.id
ORDER BY p.id
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  language_property: {len(rows)} rows")
    yield from rows


def extract_bib_record_item_record_link(pg_conn, itersize: int = 5000):
    """Yield bib_record_item_record_link rows."""
    sql = text("""\
SELECT
    l.id,
    l.bib_record_id,
    r.record_num AS bib_record_num,
    l.item_record_id,
    ir.record_num AS item_record_num,
    l.items_display_order,
    l.bibs_display_order
FROM sierra_view.bib_record_item_record_link AS l
JOIN sierra_view.record_metadata AS r ON r.id = l.bib_record_id
JOIN sierra_view.record_metadata AS ir ON ir.id = l.item_record_id
WHERE l.id > :id_val
ORDER BY l.id ASC
LIMIT :limit_val
""")
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
    sql = text("""\
SELECT
    l.id AS id,
    r.id AS volume_record_id,
    r.record_num AS volume_record_num,
    ri.id AS item_record_id,
    ri.record_num AS item_record_num,
    l.items_display_order,
    (
        SELECT string_agg(v.field_content, ', ' ORDER BY occ_num)
        FROM sierra_view.varfield AS v
        WHERE v.record_id = r.id
            AND v.varfield_type_code = 'v'
    ) AS volume_statement
FROM sierra_view.record_metadata AS r
LEFT OUTER JOIN sierra_view.volume_record_item_record_link AS l ON l.volume_record_id = r.id
LEFT OUTER JOIN sierra_view.record_metadata ri ON ri.id = l.item_record_id
WHERE
    l.id > :id_val
    AND r.record_type_code = 'j'
    AND r.campus_code = ''
ORDER BY l.id ASC
LIMIT :limit_val
""")
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
    sql = text("""\
SELECT
    id,
    code,
    branch_code_num,
    parent_location_code,
    is_public,
    is_requestable
FROM sierra_view.location
ORDER BY id
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  location: {len(rows)} rows")
    yield from rows


def extract_location_name(pg_conn, itersize: int = 5000):
    """Yield location_name rows."""
    sql = text("""\
SELECT location_id, "name"
FROM sierra_view.location_name
ORDER BY location_id
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  location_name: {len(rows)} rows")
    yield from rows


def extract_branch_name(pg_conn, itersize: int = 5000):
    """Yield branch_name rows."""
    sql = text("""\
SELECT branch_id, "name"
FROM sierra_view.branch_name
ORDER BY branch_id
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  branch_name: {len(rows)} rows")
    yield from rows


def extract_branch(pg_conn, itersize: int = 5000):
    """Yield branch rows."""
    sql = text("""\
SELECT id, address, email_source, email_reply_to, address_latitude, address_longitude, code_num
FROM sierra_view.branch
ORDER BY id
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  branch: {len(rows)} rows")
    yield from rows


def extract_country_property_myuser(pg_conn, itersize: int = 5000):
    """Yield country_property_myuser lookup rows."""
    sql = text("""\
SELECT code, display_order, "name"
FROM sierra_view.country_property_myuser
ORDER BY display_order
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  country_property_myuser: {len(rows)} rows")
    yield from rows


def extract_item_status_property(pg_conn, itersize: int = 5000):
    """Yield item_status_property lookup rows."""
    sql = text("""\
SELECT
    isp.code AS item_status_code,
    isp.display_order,
    ispn."name" AS item_status_name
FROM sierra_view.item_status_property AS isp
JOIN sierra_view.item_status_property_name AS ispn ON ispn.item_status_property_id = isp.id
ORDER BY isp.display_order
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  item_status_property: {len(rows)} rows")
    yield from rows


def extract_itype_property(pg_conn, itersize: int = 5000):
    """Yield itype_property lookup rows (item format names)."""
    sql = text("""\
SELECT
    ip.code_num AS itype_code,
    ip.display_order,
    ipn."name" AS itype_name,
    pfn."name" AS physical_format_name
FROM sierra_view.itype_property AS ip
JOIN sierra_view.itype_property_name AS ipn ON ipn.itype_property_id = ip.id
LEFT OUTER JOIN sierra_view.physical_format_name AS pfn ON pfn.physical_format_id = ip.physical_format_id
ORDER BY ip.display_order
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  itype_property: {len(rows)} rows")
    yield from rows


def extract_bib_level_property(pg_conn, itersize: int = 5000):
    """Yield bib_level_property lookup rows."""
    sql = text("""\
SELECT
    blp.code AS bib_level_property_code,
    blp.display_order,
    blpn."name" AS bib_level_property_name
FROM sierra_view.bib_level_property AS blp
LEFT OUTER JOIN sierra_view.bib_level_property_name AS blpn ON blpn.bib_level_property_id = blp.id
ORDER BY blp.display_order
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  bib_level_property: {len(rows)} rows")
    yield from rows


def extract_material_property(pg_conn, itersize: int = 5000):
    """Yield material_property lookup rows."""
    sql = text("""\
SELECT
    mp.code AS material_property_code,
    mp.display_order,
    mp.is_public,
    mpn."name" AS material_property_name
FROM sierra_view.material_property AS mp
LEFT OUTER JOIN sierra_view.material_property_name AS mpn ON mpn.material_property_id = mp.id
ORDER BY mp.display_order
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  material_property: {len(rows)} rows")
    yield from rows


def extract_hold(pg_conn, itersize: int = 5000):
    """Yield hold rows with patron metadata."""
    sql = text("""\
SELECT
    h.id AS hold_id,
    CASE
        WHEN r.record_type_code = 'i' THEN (
            SELECT br.record_num
            FROM sierra_view.bib_record_item_record_link AS l
            JOIN sierra_view.record_metadata AS br ON br.id = l.bib_record_id
            WHERE l.item_record_id = h.record_id
            LIMIT 1
        )
        WHEN r.record_type_code = 'j' THEN (
            SELECT br.record_num
            FROM sierra_view.bib_record_volume_record_link AS l
            JOIN sierra_view.record_metadata AS br ON br.id = l.bib_record_id
            WHERE l.volume_record_id = h.record_id
            LIMIT 1
        )
        WHEN r.record_type_code = 'b' THEN r.record_num
        ELSE NULL
    END AS bib_record_num,
    r.campus_code,
    r.record_type_code AS record_type_on_hold,
    CASE WHEN r.record_type_code = 'i' THEN r.record_num ELSE NULL END AS item_record_num,
    CASE WHEN r.record_type_code = 'j' THEN r.record_num ELSE NULL END AS volume_record_num,
    to_char(h.placed_gmt, 'J') :: INTEGER AS placed_julianday,
    h.is_frozen,
    h.delay_days,
    h.location_code,
    to_char(h.expires_gmt, 'J') :: INTEGER AS expires_julianday,
    CASE
        WHEN h.status = '0' THEN 'on hold'
        WHEN h.status = 'b' THEN 'bib hold ready for pickup'
        WHEN h.status = 'j' THEN 'volume hold ready for pickup'
        WHEN h.status = 'i' THEN 'item hold ready for pickup'
        WHEN h.status = 't' THEN 'in transit to pickup location'
        ELSE h.status
    END AS hold_status,
    h.is_ir,
    h.is_ill,
    h.pickup_location_code,
    h.ir_pickup_location_code,
    h.ir_print_name,
    h.ir_delivery_stop_name,
    h.is_ir_converted_request,
    CASE
        WHEN p.activity_gmt >= (NOW() - '3 years' :: INTERVAL) THEN TRUE
        ELSE FALSE
    END AS patron_is_active,
    p.ptype_code AS patron_ptype_code,
    p.home_library_code AS patron_home_library_code,
    p.mblock_code AS patron_mblock_code,
    CASE WHEN p.owed_amt > 10.00 THEN TRUE ELSE FALSE END AS patron_has_over_10usd_owed
FROM sierra_view.hold AS h
JOIN sierra_view.record_metadata AS r ON r.id = h.record_id
LEFT OUTER JOIN sierra_view.patron_record AS p ON p.record_id = h.patron_record_id
WHERE h.id > :id_val
ORDER BY hold_id ASC
LIMIT :limit_val
""")
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
    sql = text("""\
WITH circ_activity AS (
    SELECT
        TO_CHAR(c.transaction_gmt, 'YYYY-mm-dd') AS transaction_day,
        c.stat_group_code_num,
        c.op_code,
        c.itype_code_num,
        c.loanrule_code_num,
        count(*) AS count_op_code,
        count(DISTINCT c.patron_record_id) AS count_distinct_patrons
    FROM sierra_view.circ_trans AS c,
    (
        SELECT
            (to_char(date('now'), 'YYYY-mm') || '-01') :: timestamptz
            - '6 months' :: INTERVAL AS start_date
    ) AS d
    WHERE
        c.transaction_gmt > d.start_date
        AND c.op_code IN ('o', 'i', 'f')
    GROUP BY 1, 2, 3, 4, 5
)
SELECT
    a.transaction_day,
    a.stat_group_code_num,
    a.op_code,
    a.itype_code_num,
    a.loanrule_code_num,
    a.count_op_code,
    a.count_distinct_patrons,
    sgn."name" AS stat_group_name,
    loc.branch_code_num AS branch_code_num,
    bn."name" AS branch_name
FROM circ_activity AS a
JOIN sierra_view.statistic_group AS sg ON sg.code_num = a.stat_group_code_num
JOIN sierra_view.statistic_group_name AS sgn ON sgn.statistic_group_id = sg.id
JOIN sierra_view."location" AS loc ON loc.code = sg.location_code
JOIN sierra_view.branch AS b ON b.code_num = loc.branch_code_num
JOIN sierra_view.branch_name AS bn ON bn.branch_id = b.id
""")
    rows = pg_conn.execute(sql).mappings().all()
    logger.info(f"  circ_agg: {len(rows)} rows")
    yield from rows


def extract_circ_leased_items(pg_conn, itersize: int = 5000):
    """Yield circ_leased_items rows — checkout/checkin activity for leased items (last 180 days)."""
    sql = text("""\
SELECT
    c.id,
    TO_CHAR(c.transaction_gmt, 'YYYY-mm-dd') AS transaction_day,
    c.stat_group_code_num,
    sgn."name" AS stat_group_name,
    sg.location_code AS stat_group_location_code,
    bn."name" AS stat_group_branch_name,
    c.op_code,
    c.application_name,
    TO_CHAR(c.due_date_gmt, 'YYYY-mm-dd') AS due_date,
    c.item_record_id,
    (
        SELECT r.record_num
        FROM sierra_view.record_metadata AS r
        WHERE r.id = c.item_record_id
    ) AS item_record_num,
    (
        SELECT irp2.barcode
        FROM sierra_view.item_record_property AS irp2
        WHERE irp2.item_record_id = c.item_record_id
    ) AS barcode,
    c.bib_record_id,
    (
        SELECT r.record_num
        FROM sierra_view.record_metadata AS r
        WHERE r.id = c.bib_record_id
    ) AS bib_record_num,
    c.volume_record_id,
    (
        SELECT r.record_num
        FROM sierra_view.record_metadata AS r
        WHERE r.id = c.volume_record_id
    ) AS volume_record_num,
    c.itype_code_num,
    c.item_location_code,
    c.ptype_code,
    c.patron_home_library_code,
    c.patron_agency_code_num,
    c.loanrule_code_num
FROM sierra_view.circ_trans AS c
LEFT OUTER JOIN sierra_view.statistic_group AS sg ON sg.code_num = c.stat_group_code_num
LEFT OUTER JOIN sierra_view.statistic_group_name AS sgn ON sgn.statistic_group_id = sg.id
LEFT OUTER JOIN sierra_view."location" AS loc ON loc.code = sg.location_code
LEFT OUTER JOIN sierra_view.branch AS b ON b.code_num = loc.branch_code_num
LEFT OUTER JOIN sierra_view.branch_name AS bn ON bn.branch_id = b.id
WHERE c.item_record_id IN (
    SELECT irp.item_record_id
    FROM sierra_view.item_record_property AS irp
    JOIN sierra_view.record_metadata AS rm ON rm.id = irp.item_record_id
    WHERE
        rm.campus_code = ''
        AND irp.barcode >= 'L000000000000'
        AND irp.barcode < 'M'
)
AND c.transaction_gmt > date('NOW') - '180 days' :: INTERVAL
AND c.op_code IN ('o', 'i')
AND c.id > :id_val
ORDER BY c.id ASC
LIMIT :limit_val
""")
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
