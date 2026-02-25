SELECT
    id,
    code,
    branch_code_num,
    parent_location_code,
    is_public,
    is_requestable
FROM sierra_view.location
ORDER BY id
