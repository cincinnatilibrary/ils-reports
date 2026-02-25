WITH circ_activity AS (
    SELECT
        TO_CHAR(c.transaction_gmt, 'YYYY-mm-dd') AS transaction_day,
        c.stat_group_code_num,
        c.op_code,
        c.itype_code_num,
        c.loanrule_code_num,
        count(*) AS count_op_code,
        count(DISTINCT c.patron_record_id) AS count_distinct_patrons
    FROM sierra_view.circ_trans AS c,
    (
        SELECT
            (to_char(date('now'), 'YYYY-mm') || '-01') :: timestamptz
            - '6 months' :: INTERVAL AS start_date
    ) AS d
    WHERE
        c.transaction_gmt > d.start_date
        AND c.op_code IN ('o', 'i', 'f')
    GROUP BY 1, 2, 3, 4, 5
)
SELECT
    a.transaction_day,
    a.stat_group_code_num,
    a.op_code,
    a.itype_code_num,
    a.loanrule_code_num,
    a.count_op_code,
    a.count_distinct_patrons,
    sgn."name" AS stat_group_name,
    loc.branch_code_num AS branch_code_num,
    bn."name" AS branch_name
FROM circ_activity AS a
JOIN sierra_view.statistic_group AS sg ON sg.code_num = a.stat_group_code_num
JOIN sierra_view.statistic_group_name AS sgn ON sgn.statistic_group_id = sg.id
JOIN sierra_view."location" AS loc ON loc.code = sg.location_code
JOIN sierra_view.branch AS b ON b.code_num = loc.branch_code_num
JOIN sierra_view.branch_name AS bn ON bn.branch_id = b.id
