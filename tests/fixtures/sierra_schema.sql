-- Minimal Sierra sierra_view schema for integration tests.
-- Column names sourced from reference/temp_table-bib_data.sql,
-- reference/temp_table-item_data.sql, reference/temp_table-hold_data.sql,
-- and reference/collection-analysis.cincy.pl_gen_db.ipynb.

CREATE SCHEMA IF NOT EXISTS sierra_view;

-- -------------------------------------------------------------------------
-- Core record registry
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.record_metadata (
    id                       BIGINT PRIMARY KEY,
    record_num               INT,
    record_type_code         CHAR(1),
    campus_code              VARCHAR(5)  DEFAULT '',
    deletion_date_gmt        TIMESTAMP,
    creation_date_gmt        TIMESTAMP,
    record_last_updated_gmt  TIMESTAMP
);

-- -------------------------------------------------------------------------
-- Bib records
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.bib_record_property (
    id              BIGSERIAL PRIMARY KEY,
    bib_record_id   BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    best_author     VARCHAR(255),
    best_author_norm VARCHAR(255),
    best_title      VARCHAR(500),
    best_title_norm  VARCHAR(500),
    publish_year    SMALLINT
);

CREATE TABLE sierra_view.phrase_entry (
    id                 BIGSERIAL PRIMARY KEY,
    record_id          BIGINT REFERENCES sierra_view.record_metadata(id),
    index_tag          CHAR(1),
    varfield_type_code CHAR(1),
    index_entry        TEXT,
    occurrence         INT DEFAULT 0
);

CREATE TABLE sierra_view.varfield (
    id                 BIGSERIAL PRIMARY KEY,
    record_id          BIGINT REFERENCES sierra_view.record_metadata(id),
    marc_tag           VARCHAR(3),
    varfield_type_code CHAR(1),
    occ_num            INT DEFAULT 0,
    field_content      TEXT
);

CREATE TABLE sierra_view.subfield (
    id             BIGSERIAL PRIMARY KEY,
    record_id      BIGINT REFERENCES sierra_view.record_metadata(id),
    field_type_code CHAR(1),
    tag            CHAR(1),
    display_order  INT DEFAULT 0,
    content        TEXT
);

-- -------------------------------------------------------------------------
-- Item records
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.item_record (
    id                                  BIGSERIAL PRIMARY KEY,
    record_id                           BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    agency_code_num                     SMALLINT,
    location_code                       VARCHAR(5),
    checkout_statistic_group_code_num   SMALLINT,
    checkin_statistics_group_code_num   SMALLINT,
    last_checkout_gmt                   TIMESTAMP,
    last_checkin_gmt                    TIMESTAMP,
    checkout_total                      INT DEFAULT 0,
    renewal_total                       INT DEFAULT 0,
    itype_code_num                      SMALLINT,
    item_status_code                    CHAR(1),
    price                               NUMERIC(30, 4)
);

CREATE TABLE sierra_view.item_record_property (
    id               BIGSERIAL PRIMARY KEY,
    item_record_id   BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    barcode          VARCHAR(20),
    call_number_norm VARCHAR(255)
);

-- -------------------------------------------------------------------------
-- Link tables
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.bib_record_item_record_link (
    bib_record_id   BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    item_record_id  BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    PRIMARY KEY (bib_record_id, item_record_id)
);

CREATE TABLE sierra_view.bib_record_volume_record_link (
    bib_record_id    BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    volume_record_id BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    PRIMARY KEY (bib_record_id, volume_record_id)
);

-- -------------------------------------------------------------------------
-- Circulation
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.checkout (
    id              BIGSERIAL PRIMARY KEY,
    item_record_id  BIGINT REFERENCES sierra_view.record_metadata(id),
    patron_record_id BIGINT REFERENCES sierra_view.record_metadata(id),
    checkout_gmt    TIMESTAMP,
    due_gmt         TIMESTAMP
);

CREATE TABLE sierra_view.hold (
    id                BIGSERIAL PRIMARY KEY,
    patron_record_id  BIGINT REFERENCES sierra_view.record_metadata(id),
    record_id         BIGINT REFERENCES sierra_view.record_metadata(id),
    placed_gmt        TIMESTAMP,
    delay_days        INT DEFAULT 0,
    is_frozen         BOOLEAN DEFAULT FALSE,
    expires_gmt       TIMESTAMP,
    status            CHAR(1),
    is_ir             BOOLEAN DEFAULT FALSE,
    pickup_location_code VARCHAR(5)
);

-- -------------------------------------------------------------------------
-- Patron records
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.patron_record (
    id                BIGSERIAL PRIMARY KEY,
    record_id         BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    home_library_code VARCHAR(5)
);

-- -------------------------------------------------------------------------
-- Item type lookup
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.itype_property (
    id        BIGSERIAL PRIMARY KEY,
    code_num  SMALLINT UNIQUE
);

CREATE TABLE sierra_view.itype_property_name (
    id                  BIGSERIAL PRIMARY KEY,
    itype_property_id   BIGINT REFERENCES sierra_view.itype_property(id),
    name                VARCHAR(100)
);
