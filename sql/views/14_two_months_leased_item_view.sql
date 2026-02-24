CREATE VIEW IF NOT EXISTS two_months_leased_item_view AS
WITH counted_data AS (
    WITH leased_item_data AS (
        SELECT
            item.item_record_num,
            item.bib_record_num,
            item.item_format,
            item.item_status_code,
            item.item_callnumber,
            item.checkout_total,
            item.renewal_total,
            item.creation_date
        FROM
            item
        WHERE
            -- item.barcode like "l%"
            item.item_format IN ('Leased Book', 'Leased DVD') --
    -- and item.bib_record_num = 3681498
    )

    SELECT
        lid.bib_record_num,
        lid.item_format,
        COUNT(lid.item_record_num) AS count_items,
        SUM(lid.checkout_total) AS sum_total_items_checkouts,
        MIN(lid.creation_date) AS item_creation_date,
        (
            SELECT MIN(c.transaction_day)
            FROM
                circ_leased_items AS c
            WHERE
                c.bib_record_num = lid.bib_record_num -- and c.op_code = 'o'
        ) AS earliest_circ_date,
        (
            SELECT
                DATE(
                    MIN(c.transaction_day),
                    'weekday 1',
                    '-7 days',
                    '+2 months'
                )
            FROM
                circ_leased_items AS c
            WHERE
                c.bib_record_num = lid.bib_record_num -- and c.op_code = 'o'
        ) AS _2_months_from_earliest_circ_date,
        (
            SELECT COUNT(*)
            FROM
                circ_leased_items AS c
            WHERE
                c.bib_record_num = lid.bib_record_num
                AND c.op_code = 'o'
                AND c.transaction_day <= (
                    SELECT
                        DATETIME(
                            MIN(c.transaction_day),
                            'weekday 1',
                            '-7 days',
                            '+2 months'
                        )
                    FROM
                        circ_leased_items AS c
                    WHERE
                        c.bib_record_num = lid.bib_record_num
                        AND c.op_code = 'o'
                )
        ) AS count_checkouts_2_months_from_earliest_circ_date
    FROM
        leased_item_data AS lid
    GROUP BY
        1,
        2
)

SELECT
    cd.item_format,
    cd.bib_record_num,
    bib.best_title,
    bib.best_author,
    cd.count_items,
    cd.sum_total_items_checkouts,
    cd.item_creation_date,
    cd.earliest_circ_date,
    cd._2_months_from_earliest_circ_date,
    -- julianday(earliest_circ_date) - julianday(item_creation_date),
    cd.count_checkouts_2_months_from_earliest_circ_date
FROM
    counted_data AS cd
INNER JOIN bib ON cd.bib_record_num = bib.bib_record_num
WHERE
    earliest_circ_date IS NOT null --
    -- earliest circulation date is within 14 days of item creation date
    AND JULIANDAY(earliest_circ_date) - JULIANDAY(item_creation_date) <= 14.0
    -- +2 months is not a date in the future
    AND _2_months_from_earliest_circ_date <= DATE('now', 'weekday 1', '-7 days')
    AND earliest_circ_date > (
        SELECT MIN(earliest_circ_date)
        FROM
            counted_data --group by
    --  bib_record_num
    ) -- has to be larger than the minimum seen
ORDER BY
    _2_months_from_earliest_circ_date DESC;
