SELECT
    isp.code AS item_status_code,
    isp.display_order,
    ispn."name" AS item_status_name
FROM sierra_view.item_status_property AS isp
JOIN sierra_view.item_status_property_name AS ispn ON ispn.item_status_property_id = isp.id
ORDER BY isp.display_order
