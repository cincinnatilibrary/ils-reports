# Link Tables

Link tables capture many-to-many relationships between record types in Sierra.
They are thin junction tables — usually just two foreign key columns — and are
used extensively in JOIN-heavy views.

---

## `bib_record_item_record_link`

Associates bib records with their physical items.

| Column | Type | Description |
|---|---|---|
| `bib_record_id` | INTEGER | FK → `record_metadata.id` (bib) |
| `item_record_id` | INTEGER | FK → `record_metadata.id` (item) |

A single bib can have many items (multiple copies). An item belongs to
exactly one bib in most cases, but Sierra technically allows an item to be
linked to multiple bibs.

**Index:** `(item_record_id)` — supports lookups from item → bib.

---

## `volume_record_item_record_link`

Associates volume records with physical items. Volume records are used for
multi-volume sets (e.g. encyclopedias with per-volume barcodes).

| Column | Type | Description |
|---|---|---|
| `volume_record_id` | INTEGER | FK → `record_metadata.id` (volume) |
| `item_record_id` | INTEGER | FK → `record_metadata.id` (item) |

Most items are **not** linked to a volume record. Volume-level holds use this
table to resolve to a specific item.
