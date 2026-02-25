-- Comprehensive seed data for Sierra integration tests.
-- Covers all 21 extraction queries in extract.py.

-- -------------------------------------------------------------------------
-- record_metadata — bibs (b), items (i), volumes (j), patrons (p)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.record_metadata
    (id, record_num, record_type_code, campus_code, creation_date_gmt, record_last_updated_gmt)
VALUES
    -- bibs
    (1000001, 1000001, 'b', '', '2020-01-01', '2024-01-01'),
    (1000002, 1000002, 'b', '', '2021-06-15', '2024-06-15'),
    (1000003, 1000003, 'b', '', '2019-03-20', '2023-03-20'),
    -- items (standard barcodes)
    (2000001, 2000001, 'i', '', '2020-02-01', '2024-02-01'),
    (2000002, 2000002, 'i', '', '2021-07-10', '2024-07-10'),
    (2000003, 2000003, 'i', '', '2019-04-05', '2023-04-05'),
    (2000004, 2000004, 'i', '', '2022-09-01', '2024-09-01'),
    -- item with L-barcode (for circ_leased_items)
    (2000005, 2000005, 'i', '', '2023-01-01', '2024-01-01'),
    -- patrons
    (3000001, 3000001, 'p', '', '2018-05-01', '2024-05-01'),
    (3000002, 3000002, 'p', '', '2019-11-11', '2024-11-11'),
    -- volume
    (4000001, 4000001, 'j', '', '2021-01-01', '2024-01-01');

-- -------------------------------------------------------------------------
-- bib_record (needed by extract_bib and extract_bib_record)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.bib_record
    (record_id, language_code, bcode1, bcode2, bcode3, country_code,
     index_change_count, is_on_course_reserve, is_right_result_exact,
     allocation_rule_code, skip_num, cataloging_date_gmt, marc_type_code, is_suppressed)
VALUES
    (1000001, 'eng', 'a', ' ', '-', 'ohu', 0, FALSE, TRUE, ' ', 0, '2020-02-01', 'a', FALSE),
    (1000002, 'eng', 'a', ' ', '-', 'ohu', 0, FALSE, TRUE, ' ', 0, '2021-07-01', 'a', FALSE),
    (1000003, 'eng', 'a', ' ', '-', 'ohu', 0, FALSE, TRUE, ' ', 0, '2019-05-01', 'a', FALSE);

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
-- volume_record (needed by extract_volume_record)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.volume_record (record_id) VALUES (4000001);

-- -------------------------------------------------------------------------
-- varfield (needed by bib.sql and item_message extractor)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.varfield (record_id, marc_tag, varfield_type_code, occ_num, field_content)
VALUES
    -- Item message varfield (type 'm') for item_message extractor
    (2000001, NULL, 'm', 0, 'Jan 01 2024 09:00AM');

-- -------------------------------------------------------------------------
-- item_record
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.item_record
    (record_id, agency_code_num, location_code, checkout_statistic_group_code_num,
     checkin_statistics_group_code_num, last_checkout_gmt, last_checkin_gmt,
     checkout_total, renewal_total, itype_code_num, item_status_code, price)
VALUES
    (2000001, 1, 'mapl',  10, 10, '2024-01-15', '2024-01-20', 42, 5,  1, '-', 14.99),
    (2000002, 1, 'wpl',   20, 20, '2024-06-01', '2024-06-15', 18, 2,  1, '-', 12.99),
    (2000003, 1, 'npl',   30, 30, '2023-11-01', '2023-11-15', 67, 12, 1, '-', 10.00),
    (2000004, 1, 'cpl',   10, 10, NULL,          NULL,          3,  0,  2, 'o', 24.95),
    (2000005, 1, '2anf',  10, 10, NULL,          NULL,          1,  0,  1, '-', 19.99);

-- -------------------------------------------------------------------------
-- item_record_property
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.item_record_property
    (item_record_id, barcode, call_number, call_number_norm)
VALUES
    (2000001, '31234001', 'SF ADAMS',    'sf adams'),
    (2000002, '31234002', 'SF LE GUIN',  'sf le guin'),
    (2000003, '31234003', 'SF BUTLER',   'sf butler'),
    (2000004, '31234004', 'SF BUTLER K', 'sf butler k'),
    (2000005, 'L000000002005', 'SF TEST', 'sf test');

-- -------------------------------------------------------------------------
-- bib_record_item_record_link (with id, items_display_order, bibs_display_order)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.bib_record_item_record_link
    (bib_record_id, item_record_id, items_display_order, bibs_display_order)
VALUES
    (1000001, 2000001, 0, 0),
    (1000002, 2000002, 0, 0),
    (1000003, 2000003, 0, 0),
    (1000003, 2000004, 1, 0),
    (1000001, 2000005, 2, 0);

-- -------------------------------------------------------------------------
-- bib_record_volume_record_link
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.bib_record_volume_record_link (bib_record_id, volume_record_id)
VALUES (1000001, 4000001);

-- -------------------------------------------------------------------------
-- volume_record_item_record_link
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.volume_record_item_record_link
    (volume_record_id, item_record_id, items_display_order)
VALUES (4000001, 2000001, 0);

-- -------------------------------------------------------------------------
-- checkout (item 2000004 is currently checked out)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.checkout
    (item_record_id, patron_record_id, checkout_gmt, due_gmt,
     loanrule_code_num, renewal_count, overdue_count)
VALUES
    (2000004, 3000001, '2024-11-01', '2024-11-22', 1, 0, 0);

-- -------------------------------------------------------------------------
-- patron_record (with all required columns)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.patron_record
    (record_id, home_library_code, ptype_code, mblock_code, owed_amt, activity_gmt)
VALUES
    (3000001, 'mapl',  1, ' ', 0.00, CURRENT_TIMESTAMP - INTERVAL '30 days'),
    (3000002, 'wpl',   1, ' ', 0.00, CURRENT_TIMESTAMP - INTERVAL '60 days');

-- -------------------------------------------------------------------------
-- hold (with all required columns)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.hold
    (patron_record_id, record_id, placed_gmt, delay_days, is_frozen, expires_gmt,
     status, is_ir, is_ill, pickup_location_code, location_code,
     ir_pickup_location_code, ir_print_name, ir_delivery_stop_name,
     is_ir_converted_request)
VALUES
    (3000001, 1000001, '2024-10-15', 0, FALSE, '2025-01-15',
     '0', FALSE, FALSE, 'mapl', 'mapl', NULL, NULL, NULL, FALSE),
    (3000002, 1000002, '2024-11-01', 7, FALSE, '2025-02-01',
     '0', FALSE, FALSE, 'wpl',  'wpl',  NULL, NULL, NULL, FALSE);

-- -------------------------------------------------------------------------
-- Branch / location tables
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.branch (id, code_num, address, email_source, email_reply_to,
                                 address_latitude, address_longitude)
VALUES
    (1, 10, '800 Vine St, Cincinnati OH 45202', 'library@cincy.lib', 'noreply@cincy.lib',
     39.1031, -84.5120),
    (2, 20, '3450 Central Ave, Cincinnati OH 45225', 'anderson@cincy.lib', 'noreply@cincy.lib',
     39.1350, -84.5330);

INSERT INTO sierra_view.branch_name (branch_id, name)
VALUES (1, 'Main Library'), (2, 'Anderson Library');

INSERT INTO sierra_view.location (id, code, branch_code_num, parent_location_code,
                                   is_public, is_requestable)
VALUES
    (1, 'mapl',  10, NULL, TRUE, TRUE),
    (2, 'wpl',   20, NULL, TRUE, TRUE),
    (3, 'npl',   10, NULL, TRUE, TRUE),
    (4, 'cpl',   10, NULL, TRUE, TRUE),
    (5, '2anf',  20, NULL, TRUE, TRUE);

INSERT INTO sierra_view.location_name (location_id, name)
VALUES
    (1, 'Main Library - Adult Fiction'),
    (2, 'Westwood Library'),
    (3, 'Northside Library'),
    (4, 'College Hill Library'),
    (5, 'Anderson Library - Adult Non-Fiction');

-- -------------------------------------------------------------------------
-- Statistic groups (for circ_agg and circ_leased_items)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.statistic_group (id, code_num, location_code)
VALUES (1, 10, 'mapl'), (2, 20, 'wpl');

INSERT INTO sierra_view.statistic_group_name (statistic_group_id, name)
VALUES (1, 'Main Library'), (2, 'Westwood Library');

-- -------------------------------------------------------------------------
-- circ_trans (recent rows for circ_agg and circ_leased_items)
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.circ_trans
    (transaction_gmt, stat_group_code_num, op_code, itype_code_num,
     loanrule_code_num, patron_record_id, item_record_id, bib_record_id,
     volume_record_id, item_location_code, ptype_code, patron_home_library_code,
     patron_agency_code_num, due_date_gmt, application_name)
VALUES
    -- standard circ transaction (within last 6 months for circ_agg)
    (CURRENT_TIMESTAMP - INTERVAL '7 days', 10, 'o', 1,
     1, 3000001, 2000001, 1000001,
     NULL, 'mapl', 1, 'mapl',
     1, CURRENT_TIMESTAMP + INTERVAL '14 days', 'self-checkout'),
    -- L-barcode item checkout (within last 180 days for circ_leased_items)
    (CURRENT_TIMESTAMP - INTERVAL '14 days', 10, 'o', 1,
     1, 3000001, 2000005, 1000001,
     NULL, '2anf', 1, 'mapl',
     1, CURRENT_TIMESTAMP + INTERVAL '14 days', 'self-checkout'),
    -- L-barcode item checkin
    (CURRENT_TIMESTAMP - INTERVAL '7 days', 10, 'i', 1,
     1, 3000001, 2000005, 1000001,
     NULL, '2anf', 1, 'mapl',
     1, NULL, 'staff-client');

-- -------------------------------------------------------------------------
-- Lookup / property tables
-- -------------------------------------------------------------------------
INSERT INTO sierra_view.language_property (id, code, display_order)
VALUES (1, 'eng', 1), (2, 'spa', 2), (3, 'fre', 3);

INSERT INTO sierra_view.language_property_name (language_property_id, name)
VALUES (1, 'English'), (2, 'Spanish'), (3, 'French');

INSERT INTO sierra_view.country_property_myuser (code, display_order, name)
VALUES ('ohu', 1, 'Ohio'), ('xxu', 2, 'United States'), ('enk', 3, 'England');

INSERT INTO sierra_view.item_status_property (id, code, display_order)
VALUES (1, '-', 1), (2, 'o', 2), (3, 'm', 3);

INSERT INTO sierra_view.item_status_property_name (item_status_property_id, name)
VALUES (1, 'Available'), (2, 'Checked Out'), (3, 'Missing');

INSERT INTO sierra_view.itype_property (id, code_num, display_order, physical_format_id)
VALUES (1, 1, 1, 1), (2, 2, 2, 2);

INSERT INTO sierra_view.physical_format_name (physical_format_id, name)
VALUES (1, 'Print'), (2, 'Video');

INSERT INTO sierra_view.itype_property_name (itype_property_id, name)
VALUES (1, 'Book'), (2, 'DVD');

INSERT INTO sierra_view.bib_level_property (id, code, display_order)
VALUES (1, 'a', 1), (2, 'b', 2), (3, 'm', 3);

INSERT INTO sierra_view.bib_level_property_name (bib_level_property_id, name)
VALUES (1, 'Monograph Part'), (2, 'Serial Part'), (3, 'Monograph');

INSERT INTO sierra_view.material_property (id, code, display_order, is_public)
VALUES (1, 'a', 1, TRUE), (2, 'g', 2, TRUE), (3, 'v', 3, TRUE);

INSERT INTO sierra_view.material_property_name (material_property_id, name)
VALUES (1, 'Book'), (2, 'Video Recording'), (3, 'DVD');
