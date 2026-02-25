SELECT
    c.id,
    TO_CHAR(c.transaction_gmt, 'YYYY-mm-dd') AS transaction_day,
    c.stat_group_code_num,
    sgn."name" AS stat_group_name,
    sg.location_code AS stat_group_location_code,
    bn."name" AS stat_group_branch_name,
    c.op_code,
    c.application_name,
    TO_CHAR(c.due_date_gmt, 'YYYY-mm-dd') AS due_date,
    c.item_record_id,
    (
        SELECT r.record_num
        FROM sierra_view.record_metadata AS r
        WHERE r.id = c.item_record_id
    ) AS item_record_num,
    (
        SELECT irp2.barcode
        FROM sierra_view.item_record_property AS irp2
        WHERE irp2.item_record_id = c.item_record_id
    ) AS barcode,
    c.bib_record_id,
    (
        SELECT r.record_num
        FROM sierra_view.record_metadata AS r
        WHERE r.id = c.bib_record_id
    ) AS bib_record_num,
    c.volume_record_id,
    (
        SELECT r.record_num
        FROM sierra_view.record_metadata AS r
        WHERE r.id = c.volume_record_id
    ) AS volume_record_num,
    c.itype_code_num,
    c.item_location_code,
    c.ptype_code,
    c.patron_home_library_code,
    c.patron_agency_code_num,
    c.loanrule_code_num
FROM sierra_view.circ_trans AS c
LEFT OUTER JOIN sierra_view.statistic_group AS sg ON sg.code_num = c.stat_group_code_num
LEFT OUTER JOIN sierra_view.statistic_group_name AS sgn ON sgn.statistic_group_id = sg.id
LEFT OUTER JOIN sierra_view."location" AS loc ON loc.code = sg.location_code
LEFT OUTER JOIN sierra_view.branch AS b ON b.code_num = loc.branch_code_num
LEFT OUTER JOIN sierra_view.branch_name AS bn ON bn.branch_id = b.id
WHERE c.item_record_id IN (
    SELECT irp.item_record_id
    FROM sierra_view.item_record_property AS irp
    JOIN sierra_view.record_metadata AS rm ON rm.id = irp.item_record_id
    WHERE
        rm.campus_code = ''
        AND irp.barcode >= 'L000000000000'
        AND irp.barcode < 'M'
)
AND c.transaction_gmt > date('NOW') - '180 days' :: INTERVAL
AND c.op_code IN ('o', 'i')
AND c.id > :id_val
ORDER BY c.id ASC
LIMIT :limit_val
