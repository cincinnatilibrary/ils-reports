CREATE VIEW IF NOT EXISTS collection_value_branch_view AS
SELECT
    n."name" AS branch_name,
    ln."name" AS location_name,
    i.item_format,
    COUNT(i.item_record_num) AS count_items,
    SUM(i.price_cents) / 100.0 AS sum_price
FROM
    item AS i
INNER JOIN "location" AS loc ON i.location_code = loc."code"
INNER JOIN location_name AS ln ON loc.id = ln.location_id
INNER JOIN branch AS b ON loc.branch_code_num = b.code_num
INNER JOIN branch_name AS n ON b.id = n.branch_id
GROUP BY
    1,
    2,
    3;
