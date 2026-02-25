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
