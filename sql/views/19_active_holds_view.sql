CREATE VIEW IF NOT EXISTS active_holds_view AS
WITH active_holds AS (
    -- "active holds"
    -- --------------
    -- This will produce a list of holds meeting the following criteria:
    -- * hold that is not Frozen (except for holds placed by patrons with ptype 196)
    -- * hold with zero delay days OR the hold delay has passed (hold placed date + delay days is not a date in the future)
    -- * hold placed by patron with one of the following ptype codes:
    --   ( 0, 1, 2, 5, 6, 10, 11, 12, 15, 22, 30, 31, 32, 40, 41, 196 )
    -- * hold status is "on hold"
    SELECT h.*
    FROM
        hold AS h
    INNER JOIN record_metadata AS r
        ON (
            -- TODO figure out if maybe we could just use the `is_ill` boolean value to do this (this is still fast since it's an indexed search)
            r.record_type_code = 'b'
            AND h.bib_record_num = r.record_num
        ) -- join the record metadata so that we're only concerning ourselves with titles that belong to us (to filter out ILL holds)
    WHERE
    -- * hold that is not Frozen (except for holds placed by patrons with ptype 196)
        (
            h.is_frozen IS FALSE
            OR h.patron_ptype_code = 196
        )
        AND -- * hold with zero delay days OR the hold delay has passed (hold placed date + delay days is not in the future)
        (
            JULIANDAY(DATETIME('now')) - (
                h.placed_julianday + (h.delay_days * 1.0)
            )
        ) > 0
        AND -- * hold placed by patron with one of the following ptype codes:
        --   ( 0, 1, 2, 5, 6, 10, 11, 12, 15, 22, 30, 31, 32, 40, 41, 196 )
        h.patron_ptype_code IN (
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
        AND -- * hold status is "on hold"
        h.hold_status = 'on hold'
)

SELECT *
FROM
    active_holds;
