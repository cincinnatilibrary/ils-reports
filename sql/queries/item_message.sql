WITH item_messages AS (
    SELECT
        r.record_num AS item_record_num,
        r.id AS item_record_id,
        r.campus_code,
        v.id AS varfield_id,
        v.occ_num,
        v.field_content,
        v.field_content ~* '.*IN\sTRANSIT.*' AS has_in_transit,
        v.field_content ~* '.*IN\sTRANSIT\sTOO\sLONG.*' AS has_in_transit_too_long,
        regexp_matches(
            v.field_content,
            '.*IN\sTRANSIT\sfrom\s([0-9a-z]{1,})\sto\s([0-9a-z]{1,})',
            'gi'
        ) AS transit_from_to,
        (
            regexp_matches(
                v.field_content,
                '^[a-z]{3}\s[a-z]{1,3}\s[0-9]{2}\s[0-9]{4}\s[0-9]{2}\:[0-9]{2}[AP]M',
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
