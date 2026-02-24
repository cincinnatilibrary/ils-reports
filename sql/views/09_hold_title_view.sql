CREATE VIEW IF NOT EXISTS hold_title_view AS
-- Note that the hold data provides record numbers for item, volume and bib records associated with a hold
-- (where it's possible that holds do not have volume or item record numbers e.g. bib-level holds)
WITH hold_data AS (
    SELECT
        hold.hold_id,
        hold.bib_record_num,
        hold.volume_record_num,
        hold.item_record_num
    FROM
        hold
    WHERE
        hold.hold_status = 'on hold'
        AND hold.is_frozen IS false
        -- (hold placed date + delay days > today)
        AND hold.placed_julianday + hold.delay_days < (CAST(JULIANDAY('now') AS integer))
        AND hold.patron_ptype_code IN (
            0,
            1,
            2,
            5,
            6,
            10,
            11,
            12,
            15,
            22,
            30,
            31,
            32,
            40,
            41,
            196
        )
)

SELECT
    hold_data.bib_record_num,
    volume_record.volume_statement AS vol,
    hold_data.volume_record_num,
    hold_data.item_record_num,
    bib.cataloging_date,
    CASE
        WHEN LENGTH(bib.best_title) > 37 THEN SUBSTR(bib.best_title, 1, 37) || '...'
        ELSE bib.best_title
    END AS title,
    CASE
        WHEN LENGTH(bib.best_author) > 37 THEN SUBSTR(bib.best_author, 1, 37) || '...'
        ELSE bib.best_author
    END AS author,
    -- hold_data.record_type_on_hold,
    (
        WITH distinct_item_format AS (
            SELECT DISTINCT item.item_format
            FROM
                item
            WHERE
                item.bib_record_num = hold_data.bib_record_num
            ORDER BY
                item.item_format
        )

        SELECT JSON_GROUP_ARRAY(item_format)
        FROM
            distinct_item_format
    ) AS item_types,
    COUNT(hold_data.hold_id) AS count_active_holds,
    --
    -- Item counts
    --   count "active item" as:
    --     * item has a status code in the subset of defined codes
    --     * item due date less than 60 days overdue
    --
    -- Holds for titles are grouped by the set: [bib record, volume record, item record] ...
    --   item-level holds: if a hold is on an item, then the count is 1
    --   volume-level holds: if a hold has a volume record num then count items associated with that volume
    --   bib-level holds: if a
    CASE
    --
    -- count item-level items (should be 1-to-1)
        WHEN hold_data.item_record_num IS NOT null THEN 1 --
        -- count volume-level items
        WHEN
            hold_data.volume_record_num IS NOT null
            AND hold_data.item_record_num IS null
            THEN (
                WITH vol_items AS (
                    SELECT l.item_record_num
                    FROM
                        volume_record_item_record_link AS l
                    WHERE
                        l.volume_record_num = hold_data.volume_record_num
                )

                SELECT COUNT(*)
                FROM
                    vol_items AS v,
                    (
                        SELECT CAST(JULIANDAY('now') AS integer) AS julianday_now
                    ) AS mydate
                INNER JOIN item ON item.item_record_num = v.item_record_num
                WHERE
                    item_status_code IN ('-', '!', 'b', 'p', '(', '@', ')', '_', '=', '+')
                    AND (
                        mydate.julianday_now
                        - COALESCE(JULIANDAY(item.due_date), mydate.julianday_now)
                    ) < 60 -- item due date (if it has one) has age less than 60 days.
            ) --
        -- count bib-level items
        WHEN
            hold_data.volume_record_num IS null
            AND hold_data.item_record_num IS null
            THEN (
                SELECT COUNT(*)
                FROM
                    item,
                    (
                        SELECT CAST(JULIANDAY('now') AS integer) AS julianday_now
                    ) AS mydate
                WHERE
                    item.bib_record_num = hold_data.bib_record_num
                    AND item_status_code IN ('-', '!', 'b', 'p', '(', '@', ')', '_', '=', '+')
                    AND (
                        mydate.julianday_now
                        - COALESCE(JULIANDAY(item.due_date), mydate.julianday_now)
                    ) < 60 -- item due date (if it has one) has age less than 60 days.
            )
    END AS count_items
FROM
    hold_data
INNER JOIN bib ON hold_data.bib_record_num = bib.bib_record_num
LEFT OUTER JOIN volume_record ON hold_data.volume_record_num = volume_record.volume_record_num
GROUP BY
    1,
    2,
    3,
    4,
    5,
    6,
    7
ORDER BY
    count_active_holds DESC;
