CREATE VIEW IF NOT EXISTS branch_30_day_circ_view AS
WITH circ_data AS (
    SELECT
        c.branch_name,
        c.branch_code_num,
        d.target_date AS checkouts_since,
        CASE
        c.op_code
            WHEN 'o' THEN 'check-out'
            WHEN 'i' THEN 'check-in'
        END AS circ_type,
        SUM(c.count_op_code) AS sum_circ_type
    FROM
        circ_agg AS c,
        (
            SELECT DATE(JULIANDAY(MAX(transaction_day)) - 30.0) AS target_date
            FROM
                circ_agg
        ) AS d
    WHERE
        transaction_day > d.target_date
        AND op_code IN ('o', 'i')
    GROUP BY
        1,
        2,
        3
)

SELECT
    branch_name,
    latitude,
    longitude,
    -- checkouts_since, - it's last 30 days, so i don't think we need this
    -- chpl_branch_location_name,	code_num,	address
    JSON_GROUP_OBJECT(circ_type, sum_circ_type) AS circulations,
    SUM(sum_circ_type) AS total
FROM
    circ_data AS c
INNER JOIN branch_locations AS l ON c.branch_code_num = l.code_num
GROUP BY
    branch_name,
    latitude,
    longitude
ORDER BY
    SUM(sum_circ_type) DESC;
