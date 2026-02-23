# Views

Views are defined as `.sql` files in `sql/views/` and executed in alphabetical
order after all base tables are loaded. They are not stored separately —
they are recomputed at query time by SQLite.

> **Status:** All views are stubs. Fill in definitions and documentation as the
> corresponding `.sql` files are added to `sql/views/`.

---

## `item_view`

A denormalized join of `item`, `bib`, `location`, and lookup tables. The
primary table used for collection analysis queries.

> TODO: Document columns once `sql/views/01_item_view.sql` is implemented.

---

## `isbn_view`

ISBNs extracted from bib records, one row per ISBN.

> TODO

---

## `location_view`

Location codes joined with display names and branch information.

> TODO

---

## `branch_location_view`

Locations grouped by branch with aggregate counts.

> TODO

---

## `branch_30_day_circ_view`

Checkouts per branch in the last 30 days, derived from `checkout_date` in
the `item` table.

> TODO

---

## `collection_value_branch_view`

Sum of item prices by branch.

> TODO

---

## `item_in_transit_view`

Items with `item_status_code = 't'` (in transit), joined with location data.

> TODO

---

## `hold_view`

Active holds joined with bib and location information.

> TODO

---

## `hold_title_view`

Hold counts per bib title.

> TODO

---

## `leased_item_view`

Leased (DDA) items with circulation statistics.

> TODO

---

## `ld_compare_view`

Comparison view for LibraryData analytics integration.

> TODO

---

## `location_percent_checkout_view`

Percentage of items checked out at each location.

> TODO

---

## `book_connections_view`

Co-occurrence of bibs borrowed by the same patrons (requires patron data).

> TODO

---

## `active_holds_view`

Currently active (unfrozen, unexpired) holds.

> TODO

---

## `active_items_view`

Items with an active (`-`) or checked-out (`o`) status code.

> TODO

---

## `duplicate_items_at_location_view`

Locations where the same bib has more than one copy.

> TODO

---

## `circ_agg_branch_view`

Aggregated circulation counts by branch from the `circ_agg` table.

> TODO

---

## `collection_detail_view`

Full collection detail: item + bib + location + format + status.

> TODO

---

## `genre_view`

Bibs grouped by genre (derived from subject headings or MARC fixed fields).

> TODO

---

## `last_copy_view`

Items that are the last remaining copy of a bib in the system.

> TODO
