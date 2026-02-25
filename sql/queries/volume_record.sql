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
