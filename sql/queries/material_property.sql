SELECT
    mp.code AS material_property_code,
    mp.display_order,
    mp.is_public,
    mpn."name" AS material_property_name
FROM sierra_view.material_property AS mp
LEFT OUTER JOIN sierra_view.material_property_name AS mpn ON mpn.material_property_id = mp.id
ORDER BY mp.display_order
