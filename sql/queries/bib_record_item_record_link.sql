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
