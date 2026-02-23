-- Seed data for Sierra integration tests.
-- 5-10 representative rows per table.

-- -------------------------------------------------------------------------
-- record_metadata — bibs (type 'b'), items (type 'i'), patrons (type 'p')
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.record_metadata
    (id, record_num, record_type_code, campus_code, creation_date_gmt, record_last_updated_gmt)
VALUES
    -- bibs
    (1000001, 1000001, 'b', '', '2020-01-01', '2024-01-01'),
    (1000002, 1000002, 'b', '', '2021-06-15', '2024-06-15'),
    (1000003, 1000003, 'b', '', '2019-03-20', '2023-03-20'),
    -- items
    (2000001, 2000001, 'i', '', '2020-02-01', '2024-02-01'),
    (2000002, 2000002, 'i', '', '2021-07-10', '2024-07-10'),
    (2000003, 2000003, 'i', '', '2019-04-05', '2023-04-05'),
    (2000004, 2000004, 'i', '', '2022-09-01', '2024-09-01'),
    -- patrons
    (3000001, 3000001, 'p', '', '2018-05-01', '2024-05-01'),
    (3000002, 3000002, 'p', '', '2019-11-11', '2024-11-11');

-- -------------------------------------------------------------------------
-- bib_record_property
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.bib_record_property
    (bib_record_id, best_author, best_author_norm, best_title, best_title_norm, publish_year)
VALUES
    (1000001, 'Adams, Douglas', 'adams douglas', 'The Hitchhiker''s Guide to the Galaxy', 'hitchhikers guide to the galaxy', 1979),
    (1000002, 'Le Guin, Ursula K.', 'le guin ursula k', 'The Left Hand of Darkness', 'left hand of darkness', 1969),
    (1000003, 'Butler, Octavia E.', 'butler octavia e', 'Kindred', 'kindred', 1979);

-- -------------------------------------------------------------------------
-- item_record
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.item_record
    (record_id, agency_code_num, location_code, checkout_total, renewal_total,
     itype_code_num, item_status_code, price)
VALUES
    (2000001, 1, 'mapl ', 42, 5,  1, '-', 14.99),
    (2000002, 1, 'wpl  ', 18, 2,  1, '-', 12.99),
    (2000003, 1, 'npl  ', 67, 12, 1, '-', 10.00),
    (2000004, 1, 'cpl  ',  3, 0,  2, 'o', 24.95);

-- -------------------------------------------------------------------------
-- item_record_property
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.item_record_property
    (item_record_id, barcode, call_number_norm)
VALUES
    (2000001, '31234001', 'SF ADAMS'),
    (2000002, '31234002', 'SF LE GUIN'),
    (2000003, '31234003', 'SF BUTLER'),
    (2000004, '31234004', 'SF BUTLER K');

-- -------------------------------------------------------------------------
-- bib_record_item_record_link
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.bib_record_item_record_link (bib_record_id, item_record_id)
VALUES
    (1000001, 2000001),
    (1000002, 2000002),
    (1000003, 2000003),
    (1000003, 2000004);

-- -------------------------------------------------------------------------
-- checkout (item 2000004 is currently checked out)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.checkout
    (item_record_id, patron_record_id, checkout_gmt, due_gmt)
VALUES
    (2000004, 3000001, '2024-11-01', '2024-11-22');

-- -------------------------------------------------------------------------
-- hold
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.hold
    (patron_record_id, record_id, placed_gmt, delay_days, is_frozen, status, pickup_location_code)
VALUES
    (3000001, 1000001, '2024-10-15', 0, FALSE, '0', 'mapl '),
    (3000002, 1000002, '2024-11-01', 7, FALSE, '0', 'wpl  ');

-- -------------------------------------------------------------------------
-- patron_record
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.patron_record (record_id, home_library_code)
VALUES
    (3000001, 'mapl '),
    (3000002, 'wpl  ');

-- -------------------------------------------------------------------------
-- itype_property + itype_property_name
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.itype_property (code_num) VALUES (1), (2);
INSERT INTO sierra_view.itype_property_name (itype_property_id, name)
VALUES
    (1, 'Book'),
    (2, 'DVD');
