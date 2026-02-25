SELECT
    ip.code_num AS itype_code,
    ip.display_order,
    ipn."name" AS itype_name,
    pfn."name" AS physical_format_name
FROM sierra_view.itype_property AS ip
JOIN sierra_view.itype_property_name AS ipn ON ipn.itype_property_id = ip.id
LEFT OUTER JOIN sierra_view.physical_format_name AS pfn ON pfn.physical_format_id = ip.physical_format_id
ORDER BY ip.display_order
