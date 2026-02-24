CREATE VIEW IF NOT EXISTS isbn_view AS
SELECT
    json_each.value AS isbn,
    bib.bib_level_callnumber,
    bib.bib_record_num,
    item.item_record_num,
    location_code,
    item_status_code
FROM
    bib, JSON_EACH(bib.isbn_values)
LEFT OUTER JOIN item ON item.bib_record_num = bib.bib_record_num
-- GROUP BY 
-- 1;
