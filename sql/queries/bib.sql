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
