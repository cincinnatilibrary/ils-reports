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
