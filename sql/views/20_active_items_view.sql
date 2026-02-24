CREATE VIEW IF NOT EXISTS active_items_view AS
WITH active_items AS (
    -- "active items"
    -- --------------
    -- This will produce a list of items meeting the following criteria:
    -- * item status is one of the following codes:
    --   ('-', '!', 'b', 'p', '(', '@', ')', '_', '=', '+', 't')
    -- * if the item has a due date, then it must be less than 60 days overdue:
    --   coalesce( (julianday(date('now')) - julianday(item.due_date) > 60.0 ), FALSE)
    SELECT
        item.bib_record_num,
        item.item_record_num,
        v.volume_record_num,
        v.volume_statement,
        v.items_display_order
    FROM
        item
    -- we need to consider volume information for volume-level holds
    LEFT OUTER JOIN volume_record_item_record_link AS v ON item.item_record_num = v.item_record_num
    INNER JOIN record_metadata AS r
        ON (
            r.record_type_code = 'b'
            AND item.bib_record_num = r.record_num
        ) -- considers only items belonging to us (no virtual items)
    WHERE
    -- * item status is one of the following codes:
    --   ('-', '!', 'b', 'p', '(', '@', ')', '_', '=', '+', 't')
        item.item_status_code IN (
            '-',
            '!',
            'b',
            'p',
            '(',
            '@',
            ')',
            '_',
            '=',
            '+',
            't'
        ) -- * if the item has a due date, then it must be less than 60 days overdue:
        --   coalesce( (julianday(date('now')) - julianday(item.due_date) > 60.0 ), FALSE)
        AND COALESCE(
            (
                JULIANDAY(DATE('now')) - JULIANDAY(item.due_date) > 60.0
            ),
            FALSE
        ) IS FALSE
)

SELECT *
FROM
    active_items;
