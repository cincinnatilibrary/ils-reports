CREATE VIEW IF NOT EXISTS book_connections_view AS
WITH item_data AS (
    SELECT
        bib.best_title AS "Title",
        bib.best_author AS "Author",
        item.location_code,
        item.item_format,
        JSON_EXTRACT(bib.isbn_values, '$[0]') AS isbn,
        COUNT(*) AS count_location_items,
        SUM(
            (item.checkout_total + item.renewal_total)
        ) AS total_item_circulation -- count(item.item_record_num) as count_items,
    -- sum(item.checkout_total + item.renewal_total) as total_circulation,
    -- json_group_array(item.barcode) as item_barcodes --,
    -- json_group_array(item.item_status_code)
    FROM
        item
    INNER JOIN bib ON item.bib_record_num = bib.bib_record_num
    WHERE
    -- exclude items with these status codes ...
        item_status_code NOT IN (
            '$',
            --  2 	LOST AND PAID
            'e',
            --	14 	EXCUSED LOSS
            'f',
            --	15 	DISCARD TO FRIENDS
            'g',
            --	16 	LONG INTRANSIT
            'i',
            --	17 	MISSING IN INVENTORY
            'l',
            --	18 	LOST IN SYMPHONY
            'm',
            --	19 	MISSING
            'n',
            --	20 	BILLED
            's',
            --	24 	ON SEARCH
            'v',
            --	27 	ONLINE
            'w',
            --	28 	WITHDRAWN
            'y',
            --	29 	UNAVAILABLE
            'z' --	30 	CLMS RETD
        )
    GROUP BY
        1,
        2,
        3,
        4,
        5
)

SELECT
    title,
    author,
    isbn,
    location_code,
    item_format,
    count_location_items,
    total_item_circulation
FROM
    item_data;
