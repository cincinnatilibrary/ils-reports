CREATE VIEW IF NOT EXISTS new_titles_view AS
SELECT
    bib.cataloging_date,
    bib.indexed_subjects,
    JSON_OBJECT(
    -- 'img_src', 'https://covers.openlibrary.org/b/isbn/0899080871-L.jpg',
        'img_src',
        'https://covers.openlibrary.org/b/isbn/'
        || JSON_EXTRACT(bib.isbn_values, '$[0]')
        || '-L.jpg',
        'href',
        'https://cincinnatilibrary.bibliocommons.com/v2/record/S170C' || bib.bib_record_num
    ) AS jacket,
    -- isbn_values,
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
    ) AS item_format
FROM
    bib
WHERE
    bib.cataloging_date >= DATE('now', 'weekday 1', '-7 days', '-30 days')
ORDER BY
    bib.cataloging_date DESC;
