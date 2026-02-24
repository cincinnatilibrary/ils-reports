CREATE VIEW IF NOT EXISTS duplicate_items_in_location_view AS
-- get duplicate "available" items by given item location code
-- grouping by the location, bib, and volume statement
WITH bib_item_data AS (
    SELECT
        item.bib_record_num,
        -- 'volume_record_statement',
        -- coalesce(i.volume_record_statement, '')
        item.volume_record_statement,
        item.location_code,
        item.volume_record_statement,
        COUNT(item.item_record_num) AS count_item_records
    FROM
        item
    WHERE
    -- parameters are not allowed in views
    -- item.location_code = :location_code
    -- and 
        item.item_status_code IN ('-', '!', 'b', 'p', '(', '@', ')', '_', '=', '+')
    GROUP BY
        1,
        2,
        3,
        4
    HAVING
        COUNT(item.item_record_num) > 1
    ORDER BY
        3 DESC
)

SELECT
    bib_item_data.bib_record_num,
    bib_item_data.volume_record_statement,
    bib_item_data.location_code,
    bib_item_data.count_item_records,
    JSON_GROUP_ARRAY(
        DISTINCT JSON_OBJECT(
            'barcode',
            i.barcode,
            'location_code',
            i.location_code,
            'call_number',
            i.item_callnumber
        )
    ) AS item_data
FROM
    bib_item_data
INNER JOIN bib_record_item_record_link AS l ON bib_item_data.bib_record_num = l.bib_record_num
INNER JOIN item AS i
    ON (
        l.bib_record_num = i.bib_record_num
        AND bib_item_data.location_code = i.location_code
        AND i.item_status_code IN ('-', '!', 'b', 'p', '(', '@', ')', '_', '=', '+')
        AND COALESCE(i.volume_record_statement, '')
        = COALESCE(bib_item_data.volume_record_statement, '')
    )
GROUP BY
    1,
    2,
    3,
    4
ORDER BY
    4 DESC -- 2 desc;
