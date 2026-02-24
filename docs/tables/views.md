# Views

Views are defined as `.sql` files in `sql/views/` and executed in alphabetical
order after all base tables are loaded. They are not stored separately —
they are recomputed at query time by SQLite.

There are 26 views in total.

---

## `isbn_view`

ISBNs extracted from `bib.isbn_values` (a JSON array), producing one row per
ISBN per item. Used to look up bibs by ISBN.

---

## `duplicate_items_in_location_view`

Available items where the same bib + volume combination appears more than once
at the same location. Used to identify duplication candidates for weeding or
redistribution.

---

## `location_view`

Location codes joined with their display names and branch information, plus a
generated Datasette deep-link URL for each location.

---

## `item_view`

The **primary analysis table**. A fully denormalized join of `item`, `bib`,
`location`, `branch`, `item_status_property`, and `itype_property`. One row
per item with human-readable labels for all coded fields and computed columns
(e.g. days overdue, days since last checkout).

Most collection analysis queries start here.

---

## `branch_30_day_circ_view`

Checkouts and checkins per branch in the last 30 days (based on
`item.checkout_date` and `item.last_checkin_date`). Includes the branch's
geographic coordinates for map-based visualizations.

---

## `branch_location_view`

All locations joined with their branch names, plus a generated Datasette URL
for browsing items at each location.

---

## `collection_value_branch_view`

Total item count and aggregate dollar value (from `item.price_cents`) grouped
by branch, location, and item format.

---

## `hold_view`

Holds from the `hold` table joined with bib title, patron information, pickup
branch name, and computed dates (days since placed, days until expiry).

---

## `hold_title_view`

Active holds grouped by bib/volume/item with:

- total hold count
- count of available items that could fill the hold
- title, author, and catalog link

Used to surface titles with high demand relative to available supply.

---

## `leased_item_view`

Leased items (barcodes starting with `L`) joined with their parent bib
metadata. Used for DDA (demand-driven acquisition) analysis.

---

## `ld_compare_view`

Per-bib comparison of leased vs. non-leased items: checkouts-per-item for
each group. Depends on `leased_item_view` (must be numbered after it).
Used to evaluate whether leasing outperforms owned copies.

---

## `location_percent_checkout_view`

Per location: total item count, count of currently checked-out items, and
checkout percentage. Used for collection utilization analysis.

---

## `book_connections_view`

Items (excluding lost and withdrawn statuses) joined with title, author, and
location, with total lifetime circulation count. Used for browsing reports.

---

## `two_months_leased_item_view`

Leased items where the two-month initial checkout window has closed (i.e. the
item has been active for more than 60 days). Used to evaluate whether to
purchase or return leased titles.

---

## `new_downloadable_book_view`

Downloadable books (e-books, digital audiobooks) added to the collection in
the last ~60 days, with cover jacket image URLs and catalog links.

---

## `new_titles_view`

Bibs cataloged in the last ~30 days (based on `bib.cataloging_date`), with
cover jacket image URLs and catalog links. Used for new-arrivals displays.

---

## `last_copy_view`

Items that are the only remaining available copy of a bib + volume combination
in the system. Used to flag items that should not be discarded or transferred
without care.

---

## `dup_at_location_view`

Bibs with more than one available copy at the same location, with catalog
links. A broader version of `duplicate_items_in_location_view` that operates
at the bib level.

---

## `active_holds_view`

Holds meeting the "active" criteria: not frozen, not expired, and placed on a
non-deleted record. Equivalent to `SELECT * FROM hold` with standard activity
filters applied.

---

## `active_items_view`

Items meeting the "active" criteria: a valid status code, not 60+ days
overdue, and not a lost or withdrawn status. Used as a base filter in other
views and analysis queries.

---

## `item_in_transit_view`

Items with `item_status_code = 't'` (in transit), enriched with in-transit
message details from `item_message` and linked hold pickup information.

---

## `circ_agg_branch_view`

Monthly checkout volume from `circ_agg`, grouped by branch and item type,
with browse checkouts (patron-initiated) and hold-fill checkouts split into
separate columns.

---

## `duplicate_items_2ra_2rabi`

Available duplicate items at locations `2ra` and `2rabi` specifically.
A location-specific variant of the general duplicate detection logic.

---

## `duplicate_items_3ra_2rabi`

Available duplicate items at locations `3ra` and `2rabi`. Another
location-specific variant for a different set of branches.

---

## `collection_detail_view`

Full detail view: MARC fixed fields from `bib_record` joined with `item`,
`location`, and all relevant lookup tables. One row per item. Intended for
data exports and detailed collection audits.

---

## `genre_view`

Bibs grouped by genre term (extracted from `bib.genres`, a JSON array of
MARC 655$a values), with a count of bibs per genre and a generated Datasette
link for browsing.
