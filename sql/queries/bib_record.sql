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
