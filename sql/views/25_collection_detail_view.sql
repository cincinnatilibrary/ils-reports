CREATE VIEW IF NOT EXISTS collection_detail_view AS
WITH collection_detail_data AS (
    SELECT
    -- br.record_id,
        rm.record_num AS bib_record_num,
        br.cataloging_date_gmt AS bib_cat_date,
        br.language_code,
        br.bcode1,
        br.bcode2,
        br.bcode3,
        br.is_suppressed AS is_bib_suppressed,
        item.volume_record_statement AS vol_stmnt,
        item.item_record_num,
        item.creation_date AS item_creation_date,
        item.record_last_updated AS item_last_update,
        item.agency_code_num AS item_agency_code_num,
        item.location_code AS item_location_code,
        item_status_code,
        item.item_format,
        price_cents AS item_price_cents,
        DATE(rm.creation_julianday) AS creation_date,
        DATE(rm.record_last_updated_julianday) AS record_last_update,
        (
            SELECT location_name.name
            FROM
                location
            INNER JOIN location_name ON location.id = location_name.location_id
            WHERE
                location.code = item.location_code
        ) AS item_location_name,
        (
            SELECT branch_name.name
            FROM
                location
            INNER JOIN branch ON location.branch_code_num = branch.code_num
            INNER JOIN branch_name ON branch.id = branch_name.branch_id
            WHERE
                location.code = item.location_code
        ) AS item_branch_name
    FROM
        bib_record AS br
    INNER JOIN record_metadata AS rm ON br.record_id = rm.record_id
    LEFT JOIN item ON rm.record_num = item.bib_record_num
)

SELECT
    bib_record_num,
    bib_cat_date,
    creation_date,
    record_last_update,
    language_code,
    bcode1,
    bcode2,
    bcode3,
    is_bib_suppressed,
    vol_stmnt,
    item_record_num,
    item_creation_date,
    item_last_update,
    item_agency_code_num,
    item_location_code,
    item_location_name,
    item_branch_name,
    item_status_code,
    item_format,
    item_price_cents
FROM
    collection_detail_data;
