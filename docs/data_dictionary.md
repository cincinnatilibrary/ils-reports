# Data Dictionary

> TODO: Document each table and view in `current_collection.db`.
>
> For each table/view, describe:
> - What it contains and why it exists
> - Key columns and their meaning
> - How it relates to other tables
> - Any caveats or Sierra-specific quirks
>
> See the reference notebook for the source queries:
> `reference/collection-analysis.cincy.pl_gen_db.ipynb`

---

## Base Tables (extracted from Sierra)

### `record_metadata`
### `bib`
### `item`
### `bib_record`
### `volume_record`
### `hold`
### `circ_agg`
### `circ_leased_items`
### `item_message`

---

## Lookup / Property Tables

### `location`
### `branch`
### `branch_name`
### `language_property`
### `country_property_myuser`
### `item_status_property`
### `itype_property`
### `bib_level_property`
### `material_property`
### `location_name`

---

## Link Tables

### `bib_record_item_record_link`
### `volume_record_item_record_link`

---

## Views

### `item_view`
### `isbn_view`
### `location_view`
### `branch_location_view`
### `branch_30_day_circ_view`
### `collection_value_branch_view`
### `item_in_transit_view`
### `hold_view`
### `hold_title_view`
### `leased_item_view`
### `ld_compare_view`
### `location_percent_checkout_view`
### `book_connections_view`
### `active_holds_view`
### `active_items_view`
### `duplicate_items_at_location_view`
### `circ_agg_branch_view`
### `collection_detail_view`
### `genre_view`
### `last_copy_view`
