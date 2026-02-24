CREATE VIEW IF NOT EXISTS circ_agg_branch_view AS
WITH month_trans AS (
    SELECT
        op_code,
        itype_property.itype_name,
        branch_name,
        STRFTIME('%Y-%m', transaction_day) AS transaction_month,
        SUM(count_op_code) AS sum_transactions
    FROM
        circ_agg
    INNER JOIN itype_property ON itype_property.itype_code = itype_code_num
    WHERE
        op_code IN ('f', 'o')
    GROUP BY
        1,
        2,
        3,
        4
    ORDER BY
        branch_name,
        transaction_month,
        op_code
)

SELECT
    transaction_month,
    branch_name,
    itype_name,
    CASE
    op_code
        WHEN 'o' THEN 'from_browse'
        WHEN 'f' THEN "from_hold"
        ELSE ''
    END AS checkout_type,
    CASE
    -- we want the checkouts not from holds ...
        WHEN op_code = 'o'
            THEN sum_transactions - COALESCE(
                (
                    SELECT sum_transactions
                    FROM
                        month_trans AS mt
                    WHERE
                        mt.transaction_month = month_trans.transaction_month
                        AND mt.op_code = 'f'
                        AND mt.itype_name = month_trans.itype_name
                        AND mt.branch_name = month_trans.branch_name
                ),
                0
            )
        ELSE sum_transactions
    END AS sum_transactions
FROM
    month_trans;
