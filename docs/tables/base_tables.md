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
| `id` | INTEGER | Sierra internal record ID (primary key) |
| `record_num` | INTEGER | Human-readable record number (e.g. `b1234567`) |
| `record_type_code` | TEXT | `b` = bib, `i` = item, `p` = patron, etc. |
| `campus_code` | TEXT | Empty string for CHPL records; non-empty for virtual/ILL records |
| `deletion_date_gmt` | TEXT | Date the record was deleted (NULL if active) |
| `creation_date_gmt` | TEXT | Date the record was created |
| `record_last_updated_gmt` | TEXT | Date the record was last modified |

Only records with `campus_code = ''` and `deletion_date_gmt IS NULL` are
included in the extract.

---

## `bib`

Bibliographic records — one row per title in the collection. Derived from
Sierra's `bib_record_property`, `phrase_entry`, `varfield`, and `subfield`
views.

| Column | Type | Description |
|---|---|---|
| `bib_record_id` | INTEGER | FK → `record_metadata.id` |
| `bib_record_num` | INTEGER | Human-readable bib number |
| `creation_date` | TEXT | Date the bib was created |
| `record_last_updated` | TEXT | Date the bib was last modified |
| `control_numbers` | TEXT | Comma-separated OCLC/control numbers |
| `isbn` | TEXT | First ISBN (10 or 13 digit) |
| `best_author` | TEXT | Sierra's normalized best-author string |
| `best_author_norm` | TEXT | Lowercased, punctuation-stripped author |
| `best_title` | TEXT | Sierra's display title |
| `best_title_norm` | TEXT | Normalized title (for sorting/matching) |
| `publisher` | TEXT | Publisher name from MARC 260$b |
| `publish_year` | INTEGER | Publication year |
| `bib_level_callnumber` | TEXT | Normalized call number on the bib |
| `indexed_subjects` | TEXT | Comma-separated subject headings |

---

## `item`

Physical items in the collection — one row per barcode. Derived from Sierra's
`item_record`, `item_record_property`, `checkout`, and related views.

| Column | Type | Description |
|---|---|---|
| `item_record_id` | INTEGER | FK → `record_metadata.id` |
| `item_record_num` | INTEGER | Human-readable item number |
| `bib_record_id` | INTEGER | FK → `record_metadata.id` (parent bib) |
| `bib_record_num` | INTEGER | Human-readable bib number |
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
| `isbn` | TEXT | ISBN from parent bib (first match) |
| `item_format` | TEXT | Item type name (e.g. `Book`, `DVD`) |
| `item_status_code` | TEXT | Sierra status code (`-` = available, `o` = checked out, etc.) |
| `price` | TEXT | Item price as money string |
| `item_callnumber` | TEXT | Normalized call number on the item |

---

## `bib_record`

Sierra bib-level record properties not included in the `bib` table. Populated
from `sierra_view.bib_record`.

> TODO: Document columns as extraction is implemented.

---

## `volume_record`

Volume-level records linking bibs and items (used for multi-volume sets).

> TODO: Document columns as extraction is implemented.

---

## `hold`

Active holds on bib records. One row per hold.

| Column | Type | Description |
|---|---|---|
| `bib_record_id` | INTEGER | FK → bib being held |
| `bib_record_num` | INTEGER | Human-readable bib number |
| `holds` | TEXT | Pipe/semicolon-delimited string of hold details (Sierra API format) |

---

## `circ_agg`

Aggregated circulation statistics by bib record and branch.

> TODO: Document columns as extraction is implemented.

---

## `circ_leased_items`

Leased (demand-driven acquisition) items and their circulation counts.

> TODO: Document columns as extraction is implemented.

---

## `item_message`

Item-level messages and notes.

> TODO: Document columns as extraction is implemented.
