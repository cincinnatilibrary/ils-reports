CREATE VIEW IF NOT EXISTS leased_item_view AS
WITH ld_item_info AS (
    SELECT
        item.item_format,
        item.bib_record_num,
        item.barcode,
        item.price_cents,
        item.checkout_date,
        item.due_date,
        item.last_checkout_date,
        item.last_checkin_date,
        item.checkout_total,
        -- lucky day items are not renewable
        -- item.renewal_total,
        item.item_status_code,
        item.creation_date AS item_creation_date,
        item.record_last_updated
    FROM
        item
    WHERE
        (
            -- in order to effectively use the index for barcode,
            -- we can't use "LIKE"...
            -- item.barcode like 'L%'
            item.barcode >= 'L000000000000'
            AND item.barcode < 'M'
        )
)

SELECT
    ld_item_info.item_format,
    ld_item_info.bib_record_num,
    ld_item_info.barcode,
    ld_item_info.price_cents,
    ld_item_info.checkout_date,
    ld_item_info.due_date,
    ld_item_info.last_checkout_date,
    ld_item_info.last_checkin_date,
    ld_item_info.checkout_total,
    -- ld_item_info.item_status_code,
    p.item_status_name,
    ld_item_info.item_creation_date,
    ld_item_info.record_last_updated AS item_record_last_updated,
    bib.best_author,
    bib.best_title,
    bib.publisher,
    bib.publish_year,
    bib.bib_level_callnumber,
    bib.cataloging_date AS bib_cataloging_date
FROM
    ld_item_info
LEFT JOIN item_status_property AS p ON ld_item_info.item_status_code = p.item_status_code
LEFT JOIN bib ON ld_item_info.bib_record_num = bib.bib_record_num;
