CREATE VIEW IF NOT EXISTS location_percent_checkout_view AS
WITH item_data AS (
    SELECT
        item.location_code,
        COUNT(item.item_record_num) AS count_total,
        COUNT(item.due_date) AS count_checkout
    FROM
        item
    WHERE
    -- IF we want to include a param to limit to a specific branch ...
    --   item.location_code in (
    --   select
    --   location.code
    -- from
    --  location
    --  join branch on branch.code_num = location.branch_code_num
    --  join branch_name on branch_name.branch_id = branch.id
    -- where
    --   branch_name."name" = :branch_name
    --)
    -- consider these status codes as availbale
    --and
        item.item_status_code IN (
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
        item.location_code
)

SELECT
    item_data.count_checkout,
    item_data.count_total,
    item_data.location_code,
    location_name.name AS location_name,
    branch_name.name AS branch_name,
    -- branch.*,
    ROUND(
        (
            (
                item_data.count_checkout * 1.0 / item_data.count_total * 1.0
            ) * 100.0
        ),
        2
    ) AS percent_checkout
FROM
    item_data
INNER JOIN location ON item_data.location_code = location.code
INNER JOIN location_name ON location.id = location_name.location_id
INNER JOIN branch ON location.branch_code_num = branch.code_num
INNER JOIN branch_name ON branch.id = branch_name.branch_id
ORDER BY
    location.id;
