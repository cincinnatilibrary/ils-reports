CREATE VIEW IF NOT EXISTS item_view AS
SELECT
    item.item_record_num,
    item.volume_record_num,
    item.bib_record_num,
    item.creation_date,
    item.barcode,
    item.item_format,
    item.location_code,
    location_name."name" AS location_name,
    branch_name."name" AS branch_name,
    item.item_callnumber,
    item.volume_record_statement AS vol_statement,
    bib.best_author,
    bib.best_title,
    item.agency_code_num,
    item.item_status_code,
    item_status_property.item_status_name,
    item.checkout_date,
    item.due_date,
    item.checkout_total,
    item.renewal_total,
    bib.publish_year,
    COALESCE(
        item.checkout_date,
        item.last_checkin_date,
        item.last_checkout_date
    ) AS last_circ_act_date,
    item.price_cents / 100.0 AS item_price
FROM
    item
LEFT OUTER JOIN bib ON item.bib_record_num = bib.bib_record_num
LEFT OUTER JOIN location ON item.location_code = location.code
LEFT OUTER JOIN location_name ON location.id = location_name.location_id
LEFT OUTER JOIN branch ON location.branch_code_num = branch.code_num
LEFT OUTER JOIN branch_name ON branch.id = branch_name.branch_id
LEFT OUTER JOIN
    item_status_property
    ON item.item_status_code = item_status_property.item_status_code;
