# Data Dictionary

`current_collection.db` contains a nightly snapshot of the CHPL collection
extracted from Sierra. This page provides a high-level overview; detailed
column documentation is in the sub-pages.

---

## Base Tables (extracted from Sierra)

| Table | Description |
|---|---|
| [`record_metadata`](tables/base_tables.md#record_metadata) | Registry of every Sierra record |
| [`bib`](tables/base_tables.md#bib) | Bibliographic records (one per title) |
| [`item`](tables/base_tables.md#item) | Physical items (one per barcode) |
| [`bib_record`](tables/base_tables.md#bib_record) | Sierra bib-level properties |
| [`volume_record`](tables/base_tables.md#volume_record) | Volume records for multi-volume sets |
| [`hold`](tables/base_tables.md#hold) | Active bib-level holds |
| [`circ_agg`](tables/base_tables.md#circ_agg) | Aggregated circulation statistics |
| [`circ_leased_items`](tables/base_tables.md#circ_leased_items) | DDA/leased item circulation |
| [`item_message`](tables/base_tables.md#item_message) | Item notes and messages |

See [Base Tables](tables/base_tables.md) for full column documentation.

---

## Lookup / Property Tables

| Table | Description |
|---|---|
| [`location`](tables/lookup_tables.md#location) | Location codes and attributes |
| [`branch`](tables/lookup_tables.md#branch) | Branch codes |
| [`branch_name`](tables/lookup_tables.md#branch_name) | Branch display names |
| [`language_property`](tables/lookup_tables.md#language_property) | MARC language codes |
| [`country_property_myuser`](tables/lookup_tables.md#country_property_myuser) | Country codes |
| [`item_status_property`](tables/lookup_tables.md#item_status_property) | Item status codes |
| [`itype_property`](tables/lookup_tables.md#itype_property) | Item format types |
| [`bib_level_property`](tables/lookup_tables.md#bib_level_property) | Bib level codes |
| [`material_property`](tables/lookup_tables.md#material_property) | Material type codes |
| [`location_name`](tables/lookup_tables.md#location_name) | Location display names |

See [Lookup Tables](tables/lookup_tables.md) for full column documentation.

---

## Link Tables

| Table | Description |
|---|---|
| [`bib_record_item_record_link`](tables/link_tables.md#bib_record_item_record_link) | Bib ↔ item many-to-many |
| [`volume_record_item_record_link`](tables/link_tables.md#volume_record_item_record_link) | Volume ↔ item many-to-many |

See [Link Tables](tables/link_tables.md) for full documentation.

---

## Views

26 SQLite views provide pre-joined, analysis-ready datasets. See [Views](tables/views.md) for the full list.

Notable views:

| View | Description |
|---|---|
| `item_view` | Denormalized item + bib + location (primary analysis table) |
| `hold_title_view` | Hold counts by title |
| `branch_30_day_circ_view` | Recent checkouts by branch |
| `last_copy_view` | Last remaining copy per bib |
| `active_holds_view` | Currently active, unfrozen holds |
