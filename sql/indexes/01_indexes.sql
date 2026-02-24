-- Indexes for current_collection.db
-- Created after all tables are loaded for maximum performance.

-- bib
CREATE INDEX IF NOT EXISTS idx_bib_bib_record_num ON bib (bib_record_num);
CREATE INDEX IF NOT EXISTS idx_bib_indexed_subjects ON bib (indexed_subjects);

-- item
CREATE INDEX IF NOT EXISTS idx_item_item_format_location_code ON item (item_format, location_code);
CREATE INDEX IF NOT EXISTS idx_item_item_status_code ON item (item_status_code);
CREATE INDEX IF NOT EXISTS idx_item_location_code ON item (location_code);
CREATE INDEX IF NOT EXISTS idx_item_bib_record_num ON item (bib_record_num);
CREATE INDEX IF NOT EXISTS idx_item_item_record_num ON item (item_record_num);
CREATE INDEX IF NOT EXISTS idx_item_barcode ON item (barcode);
CREATE INDEX IF NOT EXISTS idx_item_item_format ON item (item_format);
CREATE INDEX IF NOT EXISTS idx_item_creation_date ON item (creation_date);
CREATE INDEX IF NOT EXISTS idx_item_bib_record_num_item_status_code ON item (
    bib_record_num, item_status_code
);

-- record_metadata
CREATE INDEX IF NOT EXISTS idx_record_metadata_record_id ON record_metadata (record_id);
CREATE INDEX IF NOT EXISTS idx_record_metadata_record_num_record_type_code ON record_metadata (
    record_num, record_type_code
);

-- bib_record
CREATE INDEX IF NOT EXISTS idx_bib_record_bcode3 ON bib_record (bcode3);
CREATE INDEX IF NOT EXISTS idx_bib_record_bcode1 ON bib_record (bcode1);
CREATE INDEX IF NOT EXISTS idx_bib_record_country_code ON bib_record (country_code);
CREATE INDEX IF NOT EXISTS idx_bib_record_language_code ON bib_record (language_code);
CREATE INDEX IF NOT EXISTS idx_bib_record_bcode2 ON bib_record (bcode2);
CREATE INDEX IF NOT EXISTS idx_bib_record_record_id ON bib_record (record_id);
CREATE INDEX IF NOT EXISTS idx_bib_record_cataloging_date_gmt ON bib_record (cataloging_date_gmt);
CREATE INDEX IF NOT EXISTS idx_bib_record_id ON bib_record (id);

-- volume_record
CREATE INDEX IF NOT EXISTS idx_volume_record_volume_record_num ON volume_record (volume_record_num);
CREATE INDEX IF NOT EXISTS idx_volume_record_bib_record_num ON volume_record (bib_record_num);
CREATE INDEX IF NOT EXISTS idx_volume_record_creation_julianday ON volume_record (
    creation_julianday
);

-- language_property
CREATE INDEX IF NOT EXISTS idx_language_property_code ON language_property (code);
CREATE INDEX IF NOT EXISTS idx_language_property_id ON language_property (id);

-- bib_record_item_record_link
CREATE INDEX IF NOT EXISTS idx_bib_record_item_record_link_item_record_num ON bib_record_item_record_link (
    item_record_num
);
CREATE INDEX IF NOT EXISTS idx_bib_record_item_record_link_bib_record_num ON bib_record_item_record_link (
    bib_record_num
);

-- volume_record_item_record_link
CREATE INDEX IF NOT EXISTS idx_volume_record_item_record_link_volume_record_num ON volume_record_item_record_link (
    volume_record_num
);
CREATE INDEX IF NOT EXISTS idx_volume_record_item_record_link_item_record_num ON volume_record_item_record_link (
    item_record_num
);

-- location
CREATE INDEX IF NOT EXISTS idx_location_branch_code_num ON location (branch_code_num);
CREATE INDEX IF NOT EXISTS idx_location_code ON location (code);
CREATE INDEX IF NOT EXISTS idx_location_id ON location (id);

-- branch_name
CREATE INDEX IF NOT EXISTS idx_branch_name_branch_id ON branch_name (branch_id);
CREATE INDEX IF NOT EXISTS idx_branch_name_name ON branch_name (name);

-- branch
CREATE INDEX IF NOT EXISTS idx_branch_code_num ON branch (code_num);
CREATE INDEX IF NOT EXISTS idx_branch_id ON branch (id);

-- hold
CREATE INDEX IF NOT EXISTS idx_hold_hold_id ON hold (hold_id);
CREATE INDEX IF NOT EXISTS idx_hold_bib_record_num ON hold (bib_record_num);
CREATE INDEX IF NOT EXISTS idx_hold_volume_record_num ON hold (volume_record_num);
CREATE INDEX IF NOT EXISTS idx_hold_item_record_num ON hold (item_record_num);

-- circ_leased_items
CREATE INDEX IF NOT EXISTS idx_circ_leased_items_bib_record_num_op_code ON circ_leased_items (
    bib_record_num, op_code
);
