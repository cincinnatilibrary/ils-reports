-- Comprehensive Sierra sierra_view schema for integration tests.
-- Covers all 21 extraction queries in extract.py.

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
CREATE TABLE sierra_view.bib_record (
    id                    BIGSERIAL PRIMARY KEY,
    record_id             BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    language_code         CHAR(3),
    bcode1                CHAR(1) DEFAULT ' ',
    bcode2                CHAR(1) DEFAULT ' ',
    bcode3                CHAR(1) DEFAULT '-',
    country_code          CHAR(3),
    index_change_count    INT DEFAULT 0,
    is_on_course_reserve  BOOLEAN DEFAULT FALSE,
    is_right_result_exact BOOLEAN DEFAULT FALSE,
    allocation_rule_code  CHAR(1) DEFAULT ' ',
    skip_num              INT DEFAULT 0,
    cataloging_date_gmt   TIMESTAMP,
    marc_type_code        CHAR(1) DEFAULT 'a',
    is_suppressed         BOOLEAN DEFAULT FALSE
);

CREATE TABLE sierra_view.bib_record_property (
    id               BIGSERIAL PRIMARY KEY,
    bib_record_id    BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    best_author      VARCHAR(255),
    best_author_norm VARCHAR(255),
    best_title       VARCHAR(500),
    best_title_norm  VARCHAR(500),
    publish_year     SMALLINT
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
    id              BIGSERIAL PRIMARY KEY,
    record_id       BIGINT REFERENCES sierra_view.record_metadata(id),
    varfield_id     BIGINT REFERENCES sierra_view.varfield(id),
    field_type_code CHAR(1),
    tag             CHAR(1),
    display_order   INT DEFAULT 0,
    occ_num         INT DEFAULT 0,
    content         TEXT
);

-- -------------------------------------------------------------------------
-- Volume records
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.volume_record (
    id        BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id)
);

-- -------------------------------------------------------------------------
-- Item records
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.item_record (
    id                                BIGSERIAL PRIMARY KEY,
    record_id                         BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    agency_code_num                   SMALLINT DEFAULT 0,
    location_code                     VARCHAR(5),
    checkout_statistic_group_code_num SMALLINT DEFAULT 0,
    checkin_statistics_group_code_num SMALLINT DEFAULT 0,
    last_checkout_gmt                 TIMESTAMP,
    last_checkin_gmt                  TIMESTAMP,
    checkout_total                    INT DEFAULT 0,
    renewal_total                     INT DEFAULT 0,
    itype_code_num                    SMALLINT,
    item_status_code                  CHAR(1) DEFAULT '-',
    price                             NUMERIC(30, 4)
);

CREATE TABLE sierra_view.item_record_property (
    id               BIGSERIAL PRIMARY KEY,
    item_record_id   BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    barcode          VARCHAR(20),
    call_number      VARCHAR(255),
    call_number_norm VARCHAR(255)
);

-- -------------------------------------------------------------------------
-- Link tables
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.bib_record_item_record_link (
    id                  BIGSERIAL PRIMARY KEY,
    bib_record_id       BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    item_record_id      BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    items_display_order INT DEFAULT 0,
    bibs_display_order  INT DEFAULT 0
);

CREATE TABLE sierra_view.bib_record_volume_record_link (
    bib_record_id    BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    volume_record_id BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    PRIMARY KEY (bib_record_id, volume_record_id)
);

CREATE TABLE sierra_view.volume_record_item_record_link (
    id                  BIGSERIAL PRIMARY KEY,
    volume_record_id    BIGINT REFERENCES sierra_view.record_metadata(id),
    item_record_id      BIGINT REFERENCES sierra_view.record_metadata(id),
    items_display_order INT DEFAULT 0
);

-- -------------------------------------------------------------------------
-- Circulation
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.checkout (
    id               BIGSERIAL PRIMARY KEY,
    item_record_id   BIGINT REFERENCES sierra_view.record_metadata(id),
    patron_record_id BIGINT REFERENCES sierra_view.record_metadata(id),
    checkout_gmt     TIMESTAMP,
    due_gmt          TIMESTAMP,
    loanrule_code_num SMALLINT DEFAULT 1,
    renewal_count    INT DEFAULT 0,
    overdue_count    INT DEFAULT 0,
    overdue_gmt      TIMESTAMP
);

CREATE TABLE sierra_view.circ_trans (
    id                        BIGSERIAL PRIMARY KEY,
    transaction_gmt           TIMESTAMP,
    stat_group_code_num       SMALLINT,
    op_code                   CHAR(1),
    itype_code_num            SMALLINT,
    loanrule_code_num         SMALLINT DEFAULT 1,
    patron_record_id          BIGINT REFERENCES sierra_view.record_metadata(id),
    item_record_id            BIGINT REFERENCES sierra_view.record_metadata(id),
    bib_record_id             BIGINT REFERENCES sierra_view.record_metadata(id),
    volume_record_id          BIGINT REFERENCES sierra_view.record_metadata(id),
    item_location_code        VARCHAR(5),
    ptype_code                SMALLINT,
    patron_home_library_code  VARCHAR(5),
    patron_agency_code_num    SMALLINT DEFAULT 0,
    due_date_gmt              TIMESTAMP,
    application_name          VARCHAR(100) DEFAULT 'self-checkout'
);

-- -------------------------------------------------------------------------
-- Hold
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.hold (
    id                        BIGSERIAL PRIMARY KEY,
    patron_record_id          BIGINT REFERENCES sierra_view.record_metadata(id),
    record_id                 BIGINT REFERENCES sierra_view.record_metadata(id),
    placed_gmt                TIMESTAMP,
    delay_days                INT DEFAULT 0,
    is_frozen                 BOOLEAN DEFAULT FALSE,
    expires_gmt               TIMESTAMP,
    status                    CHAR(1) DEFAULT '0',
    is_ir                     BOOLEAN DEFAULT FALSE,
    is_ill                    BOOLEAN DEFAULT FALSE,
    pickup_location_code      VARCHAR(5),
    location_code             VARCHAR(5),
    ir_pickup_location_code   VARCHAR(5),
    ir_print_name             VARCHAR(255),
    ir_delivery_stop_name     VARCHAR(255),
    is_ir_converted_request   BOOLEAN DEFAULT FALSE
);

-- -------------------------------------------------------------------------
-- Patron records
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.patron_record (
    id                BIGSERIAL PRIMARY KEY,
    record_id         BIGINT NOT NULL REFERENCES sierra_view.record_metadata(id),
    home_library_code VARCHAR(5),
    ptype_code        SMALLINT DEFAULT 0,
    mblock_code       CHAR(1) DEFAULT ' ',
    owed_amt          NUMERIC(30, 4) DEFAULT 0.00,
    activity_gmt      TIMESTAMP
);

-- -------------------------------------------------------------------------
-- Statistic groups (for circ queries)
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.statistic_group (
    id            BIGSERIAL PRIMARY KEY,
    code_num      SMALLINT UNIQUE,
    location_code VARCHAR(5)
);

CREATE TABLE sierra_view.statistic_group_name (
    id                 BIGSERIAL PRIMARY KEY,
    statistic_group_id BIGINT REFERENCES sierra_view.statistic_group(id),
    name               VARCHAR(255)
);

-- -------------------------------------------------------------------------
-- Location tables
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.location (
    id                   BIGSERIAL PRIMARY KEY,
    code                 VARCHAR(5) UNIQUE,
    branch_code_num      SMALLINT,
    parent_location_code VARCHAR(5),
    is_public            BOOLEAN DEFAULT TRUE,
    is_requestable       BOOLEAN DEFAULT TRUE
);

CREATE TABLE sierra_view.location_name (
    id          BIGSERIAL PRIMARY KEY,
    location_id BIGINT REFERENCES sierra_view.location(id),
    name        VARCHAR(255)
);

-- -------------------------------------------------------------------------
-- Branch tables
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.branch (
    id                BIGSERIAL PRIMARY KEY,
    code_num          SMALLINT UNIQUE,
    address           VARCHAR(255),
    email_source      VARCHAR(255),
    email_reply_to    VARCHAR(255),
    address_latitude  NUMERIC(10, 6),
    address_longitude NUMERIC(10, 6)
);

CREATE TABLE sierra_view.branch_name (
    id        BIGSERIAL PRIMARY KEY,
    branch_id BIGINT REFERENCES sierra_view.branch(id),
    name      VARCHAR(255)
);

-- -------------------------------------------------------------------------
-- Lookup / property tables
-- -------------------------------------------------------------------------
CREATE TABLE sierra_view.language_property (
    id            BIGSERIAL PRIMARY KEY,
    code          CHAR(3) UNIQUE,
    display_order INT DEFAULT 0
);

CREATE TABLE sierra_view.language_property_name (
    id                   BIGSERIAL PRIMARY KEY,
    language_property_id BIGINT REFERENCES sierra_view.language_property(id),
    name                 VARCHAR(100)
);

CREATE TABLE sierra_view.country_property_myuser (
    id            BIGSERIAL PRIMARY KEY,
    code          CHAR(3) UNIQUE,
    display_order INT DEFAULT 0,
    name          VARCHAR(100)
);

CREATE TABLE sierra_view.item_status_property (
    id            BIGSERIAL PRIMARY KEY,
    code          CHAR(1) UNIQUE,
    display_order INT DEFAULT 0
);

CREATE TABLE sierra_view.item_status_property_name (
    id                      BIGSERIAL PRIMARY KEY,
    item_status_property_id BIGINT REFERENCES sierra_view.item_status_property(id),
    name                    VARCHAR(100)
);

CREATE TABLE sierra_view.itype_property (
    id                BIGSERIAL PRIMARY KEY,
    code_num          SMALLINT UNIQUE,
    display_order     INT DEFAULT 0,
    physical_format_id BIGINT
);

CREATE TABLE sierra_view.physical_format_name (
    id                 BIGSERIAL PRIMARY KEY,
    physical_format_id BIGINT,
    name               VARCHAR(100)
);

CREATE TABLE sierra_view.itype_property_name (
    id                BIGSERIAL PRIMARY KEY,
    itype_property_id BIGINT REFERENCES sierra_view.itype_property(id),
    name              VARCHAR(100)
);

CREATE TABLE sierra_view.bib_level_property (
    id            BIGSERIAL PRIMARY KEY,
    code          CHAR(1) UNIQUE,
    display_order INT DEFAULT 0
);

CREATE TABLE sierra_view.bib_level_property_name (
    id                    BIGSERIAL PRIMARY KEY,
    bib_level_property_id BIGINT REFERENCES sierra_view.bib_level_property(id),
    name                  VARCHAR(100)
);

CREATE TABLE sierra_view.material_property (
    id            BIGSERIAL PRIMARY KEY,
    code          CHAR(1) UNIQUE,
    display_order INT DEFAULT 0,
    is_public     BOOLEAN DEFAULT TRUE
);

CREATE TABLE sierra_view.material_property_name (
    id                   BIGSERIAL PRIMARY KEY,
    material_property_id BIGINT REFERENCES sierra_view.material_property(id),
    name                 VARCHAR(100)
);
