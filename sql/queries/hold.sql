SELECT
    h.id AS hold_id,
    CASE
        WHEN r.record_type_code = 'i' THEN (
            SELECT br.record_num
            FROM sierra_view.bib_record_item_record_link AS l
            JOIN sierra_view.record_metadata AS br ON br.id = l.bib_record_id
            WHERE l.item_record_id = h.record_id
            LIMIT 1
        )
        WHEN r.record_type_code = 'j' THEN (
            SELECT br.record_num
            FROM sierra_view.bib_record_volume_record_link AS l
            JOIN sierra_view.record_metadata AS br ON br.id = l.bib_record_id
            WHERE l.volume_record_id = h.record_id
            LIMIT 1
        )
        WHEN r.record_type_code = 'b' THEN r.record_num
        ELSE NULL
    END AS bib_record_num,
    r.campus_code,
    r.record_type_code AS record_type_on_hold,
    CASE WHEN r.record_type_code = 'i' THEN r.record_num ELSE NULL END AS item_record_num,
    CASE WHEN r.record_type_code = 'j' THEN r.record_num ELSE NULL END AS volume_record_num,
    to_char(h.placed_gmt, 'J') :: INTEGER AS placed_julianday,
    h.is_frozen,
    h.delay_days,
    h.location_code,
    to_char(h.expires_gmt, 'J') :: INTEGER AS expires_julianday,
    CASE
        WHEN h.status = '0' THEN 'on hold'
        WHEN h.status = 'b' THEN 'bib hold ready for pickup'
        WHEN h.status = 'j' THEN 'volume hold ready for pickup'
        WHEN h.status = 'i' THEN 'item hold ready for pickup'
        WHEN h.status = 't' THEN 'in transit to pickup location'
        ELSE h.status
    END AS hold_status,
    h.is_ir,
    h.is_ill,
    h.pickup_location_code,
    h.ir_pickup_location_code,
    h.ir_print_name,
    h.ir_delivery_stop_name,
    h.is_ir_converted_request,
    CASE
        WHEN p.activity_gmt >= (NOW() - '3 years' :: INTERVAL) THEN TRUE
        ELSE FALSE
    END AS patron_is_active,
    p.ptype_code AS patron_ptype_code,
    p.home_library_code AS patron_home_library_code,
    p.mblock_code AS patron_mblock_code,
    CASE WHEN p.owed_amt > 10.00 THEN TRUE ELSE FALSE END AS patron_has_over_10usd_owed
FROM sierra_view.hold AS h
JOIN sierra_view.record_metadata AS r ON r.id = h.record_id
LEFT OUTER JOIN sierra_view.patron_record AS p ON p.record_id = h.patron_record_id
WHERE h.id > :id_val
ORDER BY hold_id ASC
LIMIT :limit_val
