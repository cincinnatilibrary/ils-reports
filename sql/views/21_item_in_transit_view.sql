CREATE VIEW IF NOT EXISTS item_in_transit_view AS
SELECT
    item.item_record_num,
    item.record_last_updated AS item_record_last_update,
    item.barcode,
    item_message.in_transit_days,
    item_message.transit_from,
    item_message.transit_to,
    item.agency_code_num,
    item.location_code,
    item.checkout_date,
    item.due_date,
    item.item_format,
    item.item_status_code,
    item.price_cents,
    item.item_callnumber,
    item.bib_record_num,
    item.volume_record_num,
    item.volume_record_statement,
    item_message.has_in_transit_too_long,
    DATE(item_message.in_transit_julianday) AS in_transit_date,
    DATE(hold.placed_julianday) AS date_hold_placed,
    DATE(hold.expires_julianday) AS date_hold_expires
FROM
    item
INNER JOIN hold ON item.item_record_num = hold.item_record_num
INNER JOIN item_message ON item.item_record_id = item_message.item_record_id
WHERE
    item.item_status_code = 't';
