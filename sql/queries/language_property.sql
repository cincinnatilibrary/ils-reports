SELECT
    p.id,
    p.code,
    p.display_order,
    n.name
FROM sierra_view.language_property AS p
JOIN sierra_view.language_property_name AS n ON n.language_property_id = p.id
ORDER BY p.id
