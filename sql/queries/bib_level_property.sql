SELECT
    blp.code AS bib_level_property_code,
    blp.display_order,
    blpn."name" AS bib_level_property_name
FROM sierra_view.bib_level_property AS blp
LEFT OUTER JOIN sierra_view.bib_level_property_name AS blpn ON blpn.bib_level_property_id = blp.id
ORDER BY blp.display_order
