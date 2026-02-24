CREATE VIEW IF NOT EXISTS branch_location_view AS
SELECT
    location.code,
    location_name."name" AS location_name,
    branch.code_num AS branch_code_num,
    branch_name."name" AS branch_name,
    'https://collection-analysis.cincy.pl/current_collection/item_view?_facet=location_code&_facet=item_format&location_code__exact='
    || location.code AS location_item_view
FROM
    location
LEFT OUTER JOIN location_name ON location.id = location_name.location_id
LEFT OUTER JOIN branch ON location.branch_code_num = branch.code_num
LEFT OUTER JOIN branch_name ON branch.id = branch_name.branch_id
WHERE
    branch_code_num IS NOT null
ORDER BY
    branch_code_num,
    location_name;
