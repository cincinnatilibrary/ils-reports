CREATE VIEW IF NOT EXISTS ld_compare_view AS
WITH data AS (
    WITH ld_items AS (
        SELECT
            bib_record_num,
            item_format AS ld_item_format,
            COUNT(item_record_num) AS ld_count_items,
            SUM(checkout_total) AS ld_sum_checkout_total
        FROM
            item
        WHERE
            barcode LIKE 'L%'
        GROUP BY
            1,
            2
    )

    SELECT
        ld_items.*,
        best_author,
        best_title,
        -- non_ld_items.*,
        publisher,
        publish_year,
        cataloging_date,
        COUNT(i.item_record_num) AS non_ld_count_items,
        SUM(i.checkout_total) AS non_ld_sum_checkout_total
    FROM
        ld_items
    INNER JOIN bib ON ld_items.bib_record_num = bib.bib_record_num
    INNER JOIN item AS i
        ON (
            ld_items.bib_record_num = i.bib_record_num
            AND i.barcode NOT LIKE 'L%'
        )
    GROUP BY
        i.bib_record_num
)

SELECT
    bib_record_num,
    best_author,
    best_title,
    ld_item_format,
    ld_count_items,
    ld_sum_checkout_total,
    non_ld_count_items,
    non_ld_sum_checkout_total,
    publisher,
    publish_year,
    cataloging_date,
    ROUND(
        (ld_sum_checkout_total * 1.0) / (ld_count_items * 1.0),
        2
    ) AS ld_checkouts_per_item,
    ROUND(
        (non_ld_sum_checkout_total * 1.0) / (non_ld_count_items * 1.0),
        2
    ) AS non_ld_checkouts_per_item
FROM
    data;
