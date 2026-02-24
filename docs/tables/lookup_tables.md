# Lookup / Property Tables

These tables map Sierra code values to human-readable names. They are small
(tens to hundreds of rows) and are loaded once at the start of each build.

---

## `location`

Branch/location codes and their attributes.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Sierra internal location ID (primary key) |
| `code` | TEXT | Location code (e.g. `mapl `) — note trailing spaces are preserved |
| `branch_code_num` | INTEGER | FK → `branch.code_num` |
| `parent_location_code` | TEXT | Parent location code (for sub-locations) |
| `is_public` | BOOLEAN | Whether this location appears in the public catalog |
| `is_requestable` | BOOLEAN | Whether patrons can request items to this location |

---

## `location_name`

Full display names for location codes.

| Column | Type | Description |
|---|---|---|
| `location_id` | INTEGER | FK → `location.id` |
| `name` | TEXT | Full display name (e.g. `Main Library`) |

---

## `branch`

CHPL branch/system-level codes with address and contact information.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Sierra internal branch ID (primary key) |
| `address` | TEXT | Street address |
| `email_source` | TEXT | From-address for branch email |
| `email_reply_to` | TEXT | Reply-to address for branch email |
| `address_latitude` | REAL | Latitude for map display |
| `address_longitude` | REAL | Longitude for map display |
| `code_num` | INTEGER | Branch code number (used as FK in other tables) |

---

## `branch_name`

Normalized display names for branches.

| Column | Type | Description |
|---|---|---|
| `branch_id` | INTEGER | FK → `branch.id` |
| `name` | TEXT | Display name |

---

## `language_property`

MARC language codes mapped to language names.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Sierra internal language ID (primary key) |
| `code` | TEXT | Three-letter MARC language code |
| `display_order` | INTEGER | Sort order for display |
| `name` | TEXT | Language name in English |

---

## `country_property_myuser`

Country codes used in Sierra's location data.

| Column | Type | Description |
|---|---|---|
| `code` | TEXT | Country code |
| `display_order` | INTEGER | Sort order for display |
| `name` | TEXT | Country name |

---

## `item_status_property`

Sierra item status codes and their display labels.

| Column | Type | Description |
|---|---|---|
| `item_status_code` | TEXT | Single-character status code |
| `display_order` | INTEGER | Sort order for display |
| `item_status_name` | TEXT | Human-readable status (e.g. `Available`, `Checked Out`) |

Common codes:

| Code | Meaning |
|---|---|
| `-` | Available |
| `o` | Checked out |
| `t` | In transit |
| `!` | On holdshelf |
| `p` | In process |
| `m` | Missing |

---

## `itype_property`

Item type codes (format types).

| Column | Type | Description |
|---|---|---|
| `itype_code` | INTEGER | Item type code |
| `display_order` | INTEGER | Sort order for display |
| `itype_name` | TEXT | Format name (e.g. `Book`, `DVD`, `Audiobook`) |
| `physical_format_name` | TEXT | Physical format grouping name |

---

## `bib_level_property`

Sierra bibliographic level codes.

| Column | Type | Description |
|---|---|---|
| `bib_level_property_code` | TEXT | Single-character bib level code |
| `display_order` | INTEGER | Sort order for display |
| `bib_level_property_name` | TEXT | Description |

---

## `material_property`

Material type codes from Sierra.

| Column | Type | Description |
|---|---|---|
| `material_property_code` | TEXT | Material type code |
| `display_order` | INTEGER | Sort order for display |
| `is_public` | BOOLEAN | Whether this material type is shown publicly |
| `material_property_name` | TEXT | Material type name |
