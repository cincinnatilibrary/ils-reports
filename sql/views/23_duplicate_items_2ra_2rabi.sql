CREATE VIEW IF NOT EXISTS duplicate_items_2ra_2rabi AS
WITH duplicate_items_at_location AS (
    SELECT
        bib.bib_record_num,
        item.volume_record_statement,
        JSON_GROUP_ARRAY(item.location_code) AS locations,
        JSON_GROUP_ARRAY(item.barcode) AS item_barcodes,
        JSON_GROUP_ARRAY(item.item_callnumber) AS item_callnumbers,
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
    WHERE
        location_code IN ('2ra', '2rabi') -- and 3ra and 2rabi
    GROUP BY
        1,
        2
    HAVING
        COUNT(*) > 1
)

SELECT
    duplicate_items_at_location.bib_record_num,
    duplicate_items_at_location.volume_record_statement,
    bib.best_author,
    bib.best_title,
    bib.publisher,
    bib.publish_year,
    duplicate_items_at_location.locations,
    duplicate_items_at_location.item_callnumbers,
    duplicate_items_at_location.item_barcodes,
    duplicate_items_at_location.count_items,
    JSON_OBJECT(
    -- 'img_src', 'https://covers.openlibrary.org/b/isbn/0899080871-L.jpg',
        'img_src',
        'https://covers.openlibrary.org/b/isbn/'
        || JSON_EXTRACT(bib.isbn_values, '$[0]')
        || '-L.jpg',
        'href',
        'https://cincinnatilibrary.bibliocommons.com/v2/record/S170C' || bib.bib_record_num
    ) AS jacket
FROM
    duplicate_items_at_location
INNER JOIN bib ON duplicate_items_at_location.bib_record_num = bib.bib_record_num;
