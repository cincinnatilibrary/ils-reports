# Base Tables

These tables are extracted directly from Sierra's `sierra_view` PostgreSQL
schema and loaded as-is into `current_collection.db`. Column names match the
Sierra field names where possible; derived columns are documented explicitly.

---

## `record_metadata`

The registry of every Sierra record. All other tables join back to this one
via `id`.

| Column | Type | Description |
|---|---|---|
| `record_id` | INTEGER | Sierra internal record ID (primary key) |
| `record_num` | INTEGER | Human-readable record number (e.g. `b1234567`) |
| `record_type_code` | TEXT | `b` = bib, `i` = item, `j` = volume |
| `creation_julianday` | INTEGER | Julian day the record was created |
| `record_last_updated_julianday` | INTEGER | Julian day the record was last modified |
| `deletion_julianday` | INTEGER | Julian day the record was deleted (NULL if active) |

Only records with `campus_code = ''` and `deletion_date_gmt IS NULL` are
included in the extract (except deleted records which appear with a
`deletion_julianday` value).

---

## `bib`

Bibliographic records — one row per title in the collection. Derived from
Sierra's `bib_record_property`, `phrase_entry`, `varfield`, and `subfield`
views.

| Column | Type | Description |
|---|---|---|
| `bib_record_id` | INTEGER | FK → `record_metadata.record_id` |
| `bib_record_num` | INTEGER | Human-readable bib number |
| `best_author` | TEXT | Sierra's normalized best-author string |
| `best_title` | TEXT | Sierra's display title |
| `publisher` | TEXT | Publisher name from MARC 260$b |
| `publish_year` | INTEGER | Publication year |
| `bib_level_callnumber` | TEXT | Normalized call number on the bib |
| `control_numbers` | TEXT | JSON array of OCLC/control numbers |
| `isbn_values` | TEXT | JSON array of ISBNs (10 or 13 digit) |
| `indexed_subjects` | TEXT | JSON array of subject headings |
| `genres` | TEXT | JSON array of genre terms from MARC 655$a |
| `item_types` | TEXT | JSON array of item type names attached to this bib, ordered by count descending |
| `cataloging_date` | TEXT | Date the bib was cataloged |

---

## `item`

Physical items in the collection — one row per barcode. Derived from Sierra's
`item_record`, `item_record_property`, `checkout`, and related views.

| Column | Type | Description |
|---|---|---|
| `item_record_id` | INTEGER | FK → `record_metadata.record_id` |
| `item_record_num` | INTEGER | Human-readable item number |
| `bib_record_num` | INTEGER | Human-readable bib number (parent bib) |
| `creation_date` | TEXT | Date the item was created |
| `record_last_updated` | TEXT | Date the item was last modified |
| `barcode` | TEXT | Item barcode |
| `agency_code_num` | INTEGER | Sierra agency code |
| `location_code` | TEXT | Branch/location code (e.g. `mapl `) |
| `checkout_statistic_group_code_num` | INTEGER | Checkout stat group |
| `checkin_statistics_group_code_num` | INTEGER | Checkin stat group |
| `checkout_date` | TEXT | Date of current checkout (NULL if not checked out) |
| `due_date` | TEXT | Due date of current checkout |
| `patron_branch_code` | TEXT | Home branch of current borrower |
| `last_checkout_date` | TEXT | Date of most recent checkout |
| `last_checkin_date` | TEXT | Date of most recent checkin |
| `checkout_total` | INTEGER | Lifetime checkout count |
| `renewal_total` | INTEGER | Lifetime renewal count |
| `item_format` | TEXT | Item type name (e.g. `Book`, `DVD`) |
| `item_status_code` | TEXT | Sierra status code (`-` = available, `o` = checked out, etc.) |
| `price_cents` | INTEGER | Item price in cents (original value × 100) |
| `item_callnumber` | TEXT | Normalized call number on the item |
| `volume_record_num` | INTEGER | Human-readable volume record number (NULL if no volume) |
| `volume_record_statement` | TEXT | Volume statement string (e.g. `v.1`) |

---

## `bib_record`

Sierra bib-level record properties. Populated from `sierra_view.bib_record`.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Sierra internal bib_record row ID |
| `record_id` | INTEGER | FK → `record_metadata.record_id` |
| `language_code` | TEXT | Three-letter MARC language code |
| `bcode1` | TEXT | Bib-level fixed-field code 1 |
| `bcode2` | TEXT | Bib-level fixed-field code 2 |
| `bcode3` | TEXT | Bib-level fixed-field code 3 |
| `country_code` | TEXT | MARC country of publication code |
| `index_change_count` | INTEGER | Number of times the index has been changed |
| `is_on_course_reserve` | BOOLEAN | Whether bib is on course reserve |
| `is_right_result_exact` | BOOLEAN | Sierra right-result flag |
| `allocation_rule_code` | TEXT | Allocation rule code |
| `skip_num` | INTEGER | Internal skip counter |
| `cataloging_date_gmt` | TEXT | Date the bib was cataloged (ISO date string) |
| `marc_type_code` | TEXT | MARC record type code |
| `is_suppressed` | BOOLEAN | Whether the bib is suppressed from the public catalog |

---

## `volume_record`

Volume-level records linking bibs and items (used for multi-volume sets).

| Column | Type | Description |
|---|---|---|
| `volume_record_id` | INTEGER | FK → `record_metadata.record_id` |
| `volume_record_num` | INTEGER | Human-readable volume record number |
| `bib_record_id` | INTEGER | FK → parent bib's `record_metadata.record_id` |
| `bib_record_num` | INTEGER | Human-readable bib number |
| `creation_julianday` | INTEGER | Julian day the volume record was created |
| `volume_statement` | TEXT | Volume statement string (e.g. `v.1, 2024`) |

---

## `hold`

Active holds. One row per hold.

| Column | Type | Description |
|---|---|---|
| `hold_id` | INTEGER | Sierra internal hold ID |
| `bib_record_num` | INTEGER | Human-readable bib number being held |
| `campus_code` | TEXT | Campus code of the record being held |
| `record_type_on_hold` | TEXT | Record type: `b` = bib, `i` = item, `j` = volume |
| `item_record_num` | INTEGER | Item record number (NULL unless item-level hold) |
| `volume_record_num` | INTEGER | Volume record number (NULL unless volume-level hold) |
| `placed_julianday` | INTEGER | Julian day the hold was placed |
| `is_frozen` | BOOLEAN | Whether the hold is frozen (paused) |
| `delay_days` | INTEGER | Number of days to delay activating the hold |
| `location_code` | TEXT | Location code at time of hold placement |
| `expires_julianday` | INTEGER | Julian day the hold expires |
| `hold_status` | TEXT | Human-readable status: `on hold`, `in transit to pickup location`, etc. |
| `is_ir` | BOOLEAN | Whether this is an inter-library hold |
| `is_ill` | BOOLEAN | Whether this is an ILL request |
| `pickup_location_code` | TEXT | Patron's chosen pickup location |
| `ir_pickup_location_code` | TEXT | IR pickup location code |
| `ir_print_name` | TEXT | IR pickup location print name |
| `ir_delivery_stop_name` | TEXT | IR delivery stop name |
| `is_ir_converted_request` | BOOLEAN | Whether this IR request has been converted |
| `patron_is_active` | BOOLEAN | TRUE if patron has activity in the last 3 years |
| `patron_ptype_code` | INTEGER | Patron type code |
| `patron_home_library_code` | TEXT | Patron's home library code |
| `patron_mblock_code` | TEXT | Patron's manual block code |
| `patron_has_over_10usd_owed` | BOOLEAN | TRUE if patron owes more than $10.00 |

---

## `circ_agg`

Aggregated circulation statistics by stat group, operation, and item type.
Covers the last 6 months of transactions.

| Column | Type | Description |
|---|---|---|
| `transaction_day` | TEXT | Date of transactions (YYYY-MM-DD) |
| `stat_group_code_num` | INTEGER | Statistics group code |
| `op_code` | TEXT | Operation code: `o` = checkout, `i` = checkin, `f` = checkout-from-hold |
| `itype_code_num` | INTEGER | Item type code |
| `loanrule_code_num` | INTEGER | Loan rule code |
| `count_op_code` | INTEGER | Number of transactions of this type |
| `count_distinct_patrons` | INTEGER | Number of distinct patrons involved |
| `stat_group_name` | TEXT | Human-readable statistics group name |
| `branch_code_num` | INTEGER | Branch code number (FK → `branch.code_num`) |
| `branch_name` | TEXT | Branch display name |

---

## `circ_leased_items`

Checkout/checkin transactions for leased (DDA) items in the last 180 days.
Leased items are identified by barcodes starting with `L`.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Sierra circulation transaction ID |
| `transaction_day` | TEXT | Date of transaction (YYYY-MM-DD) |
| `stat_group_code_num` | INTEGER | Statistics group code |
| `stat_group_name` | TEXT | Statistics group name |
| `stat_group_location_code` | TEXT | Location code for the stat group |
| `stat_group_branch_name` | TEXT | Branch name for the stat group |
| `op_code` | TEXT | Operation: `o` = checkout, `i` = checkin |
| `application_name` | TEXT | Application used for the transaction |
| `due_date` | TEXT | Due date (YYYY-MM-DD) |
| `item_record_id` | INTEGER | FK → `record_metadata.record_id` |
| `item_record_num` | INTEGER | Human-readable item number |
| `barcode` | TEXT | Item barcode (starts with `L`) |
| `bib_record_id` | INTEGER | FK → `record_metadata.record_id` (parent bib) |
| `bib_record_num` | INTEGER | Human-readable bib number |
| `volume_record_id` | INTEGER | FK → `record_metadata.record_id` (parent volume) |
| `volume_record_num` | INTEGER | Human-readable volume number |
| `itype_code_num` | INTEGER | Item type code |
| `item_location_code` | TEXT | Item's location code |
| `ptype_code` | INTEGER | Patron type code |
| `patron_home_library_code` | TEXT | Patron's home library code |
| `patron_agency_code_num` | INTEGER | Patron's agency code |
| `loanrule_code_num` | INTEGER | Loan rule code |

---

## `item_message`

Item-level varfield messages (type `m`), enriched with item, bib, and
circulation data. Primarily used to track in-transit items.

| Column | Type | Description |
|---|---|---|
| `item_barcode` | TEXT | Item barcode |
| `campus_code` | TEXT | Campus code of the item |
| `call_number` | TEXT | Item call number |
| `item_record_id` | INTEGER | FK → `record_metadata.record_id` |
| `varfield_id` | INTEGER | Sierra varfield ID (primary key for this table) |
| `has_in_transit` | BOOLEAN | TRUE if message contains "IN TRANSIT" |
| `in_transit_julianday` | INTEGER | Julian day the item entered transit |
| `in_transit_days` | INTEGER | Days elapsed since transit began |
| `transit_from` | TEXT | Origin location code |
| `transit_to` | TEXT | Destination location code |
| `has_in_transit_too_long` | BOOLEAN | TRUE if message contains "IN TRANSIT TOO LONG" |
| `occ_num` | INTEGER | Occurrence number of the varfield |
| `field_content` | TEXT | Raw message field content |
| `publish_year` | INTEGER | Publication year of the parent bib |
| `best_title` | TEXT | Title of the parent bib |
| `best_author` | TEXT | Author of the parent bib |
| `item_status_code` | TEXT | Sierra item status code |
| `item_status_name` | TEXT | Human-readable item status |
| `agency_code_num` | INTEGER | Item's agency code |
| `location_code` | TEXT | Item's current location code |
| `itype_code_num` | INTEGER | Item type code |
| `item_format` | TEXT | Item format name |
| `due_julianday` | INTEGER | Julian day the item is due (if checked out) |
| `loanrule_code_num` | INTEGER | Loan rule code |
| `checkout_julianday` | INTEGER | Julian day the item was checked out |
| `renewal_count` | INTEGER | Number of times the checkout has been renewed |
| `overdue_count` | INTEGER | Number of times the item has been overdue |
| `overdue_julianday` | INTEGER | Julian day the item became overdue |
