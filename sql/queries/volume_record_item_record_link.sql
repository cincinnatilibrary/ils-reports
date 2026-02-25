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
