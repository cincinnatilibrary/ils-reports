CREATE VIEW IF NOT EXISTS dup_at_location_view AS
WITH duplicate_items_at_location AS (
    SELECT
        bib.bib_record_num,
        item.volume_record_statement,
        item.location_code,
        COUNT(*) AS count_items
    FROM
        bib
    INNER JOIN item
        ON (
            bib.bib_record_num = item.bib_record_num
            AND item_status_code IN (
                '-',
                '!',
                'b',
                'p',
                '(',
                '@',
                ')',
                '_',
                '=',
                '+',
                't'
            )
        )
    GROUP BY
        1,
        2,
        3
    HAVING
        COUNT(*) > 1
)

SELECT
    dil.bib_record_num,
    dil.volume_record_statement AS vol,
    dil.location_code,
    dil.count_items,
    bib.cataloging_date,
    bib.bib_level_callnumber,
    indexed_subjects,
    -- isbn_values,
    JSON_OBJECT(
    -- 'img_src', 'https://covers.openlibrary.org/b/isbn/0899080871-L.jpg',
        'img_src',
        'https://covers.openlibrary.org/b/isbn/'
        || JSON_EXTRACT(bib.isbn_values, '$[0]')
        || '-L.jpg',
        'href',
        'https://cincinnatilibrary.bibliocommons.com/v2/record/S170C' || bib.bib_record_num
    ) AS jacket,
    JSON_OBJECT(
    --'img_src', 'https://placekitten.com/200/300',
        'href',
        'https://cincinnatilibrary.bibliocommons.com/v2/record/S170C' || bib.bib_record_num,
        'label',
        bib.best_title,
        -- || coalesce(vol_statement, ''),
        'title',
        bib.best_title || COALESCE('
' || bib.best_author, ''),
        'description',
        bib.best_author || '
' || bib.publish_year || COALESCE('
' || bib.bib_level_callnumber, '')
    ) AS catalog_link,
    (
        SELECT JSON_GROUP_ARRAY(item.barcode)
        FROM
            item
        WHERE
            item.bib_record_num = bib.bib_record_num
            AND item.location_code = dil.location_code
    ) AS barcodes,
    (
        SELECT item_format
        FROM
            item
        WHERE
            item.bib_record_num = bib.bib_record_num
        GROUP BY
            1
        ORDER BY
            COUNT(*) DESC
        LIMIT
            1
    ) AS item_format -- item.barcode,
-- item.item_callnumber,
-- item.location_code,
-- item.barcode,
FROM
    duplicate_items_at_location AS dil
INNER JOIN bib ON dil.bib_record_num = bib.bib_record_num
ORDER BY
    bib_level_callnumber;
