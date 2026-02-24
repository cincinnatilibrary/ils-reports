CREATE VIEW IF NOT EXISTS hold_view AS
SELECT
    hold_id,
    bib.best_title AS title,
    bib.cataloging_date AS cat_date,
    hold.bib_record_num,
    hold.item_record_num,
    hold.volume_record_num,
    volume_record.volume_statement,
    --  (
    --    select
    --      volume_statement
    --    from
    --      volume_record
    --    where
    --      volume_record.volume_record_num = hold.volume_record_num
    --    limit
    --      1
    --  ) as volume_statement,
    campus_code,
    record_type_on_hold,
    hold_status,
    is_frozen,
    is_ir,
    is_ill,
    location_code,
    pickup_location_code,
    branch_name."name" AS branch_pickup_name,
    ir_pickup_location_code,
    -- delay_days,
    ir_print_name,
    ir_delivery_stop_name,
    is_ir_converted_request,
    patron_is_active,
    patron_ptype_code,
    patron_home_library_code,
    patron_mblock_code,
    patron_has_over_10usd_owed,
    (
        SELECT location_name."name"
        FROM
            location
        INNER JOIN location_name ON location.id = location_name.location_id
        WHERE
            location.code = hold.campus_code
        LIMIT
            1
    ) AS campus_location_name,
    DATE(placed_julianday) AS hold_placed_date,
    DATE(expires_julianday) AS hold_expires_date,
    CASE
        WHEN is_frozen IS true THEN null
        ELSE DATE(placed_julianday + delay_days)
    END AS not_wanted_before_date
FROM
    hold
INNER JOIN bib ON hold.bib_record_num = bib.bib_record_num
LEFT OUTER JOIN volume_record ON hold.volume_record_num = volume_record.volume_record_num
LEFT OUTER JOIN location ON hold.pickup_location_code = location.code
LEFT OUTER JOIN location_name ON location.id = location_name.location_id
LEFT OUTER JOIN branch ON location.branch_code_num = branch.code_num
LEFT OUTER JOIN branch_name ON branch.id = branch_name.branch_id;
