CREATE VIEW IF NOT EXISTS location_view AS
SELECT
    "location".id AS location_id,
    "location"."code" AS location_code,
    "location".is_public,
    "location".is_requestable,
    branch.code_num AS branch_code_num,
    location_name."name" AS location_name,
    branch_name."name" AS branch_name,
    JSON_OBJECT(
        "href",
        "/current_collection/item?location_code__exact=" || COALESCE("location".code, ""),
        "label",
        "view items"
    ) AS items
FROM
    "location"
INNER JOIN location_name ON "location".id = location_name.location_id
INNER JOIN branch ON location.branch_code_num = branch.code_num
INNER JOIN branch_name ON branch.id = branch_name.branch_id;
