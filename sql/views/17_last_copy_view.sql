CREATE VIEW IF NOT EXISTS last_copy_view AS
WITH last_available_copy AS (
    SELECT
        bib_record_num,
        volume_record_statement,
        -- branch_name,
        COUNT(*)
    FROM
        item
    WHERE
    -- these are available status codes
    -- ... will also exclude electronic items
        item_status_code IN (
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
    GROUP BY
        1,
        2
    HAVING
        COUNT(*) = 1
)

SELECT
    bib.bib_record_num,
    blv.branch_name,
    item.location_code,
    item.barcode,
    item.item_format,
    item.item_callnumber,
    item.volume_record_statement AS vol_statement,
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
    -- bib.isbn_values,
    JSON_OBJECT(
        'last_checkout_date',
        item.last_checkout_date,
        'due_date',
        item.due_date,
        'checkout_total',
        item.checkout_total,
        'renewal_total',
        item.renewal_total
    ) AS circ_stats
FROM
    last_available_copy AS lac
INNER JOIN bib ON lac.bib_record_num = bib.bib_record_num
INNER JOIN item ON lac.bib_record_num = item.bib_record_num
INNER JOIN branch_location_view AS blv ON item.location_code = blv.code;
