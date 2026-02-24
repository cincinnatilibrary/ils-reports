CREATE VIEW IF NOT EXISTS new_downloadable_book_view AS
SELECT
    creation_date AS "date added",
    JSON_OBJECT(
        -- 'img_src', 'https://covers.openlibrary.org/b/isbn/0899080871-L.jpg',
        'img_src',
        'https://covers.openlibrary.org/b/isbn/'
        || JSON_EXTRACT(bib.isbn_values, '$[0]')
        || '-L.jpg',
        'href', 'https://cincinnatilibrary.bibliocommons.com/v2/record/S170C' || bib.bib_record_num
    ) AS jacket,
    JSON_OBJECT(
    --'img_src', 'https://placekitten.com/200/300',
        'href',
        'https://cincinnatilibrary.bibliocommons.com/v2/record/S170C' || bib.bib_record_num,
        'label',
        item_view.best_title || COALESCE(vol_statement, ''),
        'title',
        item_view.best_title || COALESCE('
' || item_view.best_author, ''),
        'description',
        item_view.best_author || '
' || item_view.publish_year || COALESCE('
' || item_view.item_callnumber, '')
    ) AS catalog_link -- item_format
FROM
    item_view
INNER JOIN bib ON item_view.bib_record_num = bib.bib_record_num
WHERE
    item_view.creation_date >= DATE('now', 'weekday 1', '-7 days', '-60 days')
    -- item_view.creation_date >= :create_date_start
    AND item_view.item_format = 'Downloadable Book'
ORDER BY
    "date added" DESC,
    COALESCE(item_view.best_author, 'Zzzz') ASC,
    item_view.best_title ASC;
