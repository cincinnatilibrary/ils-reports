# Lookup / Property Tables

These tables map Sierra code values to human-readable names. They are small
(tens to hundreds of rows) and are loaded once at the start of each build.

---

## `location`

Branch/location codes and their attributes.

| Column | Type | Description |
|---|---|---|
| `code` | TEXT | Location code (e.g. `mapl `) — note trailing spaces are preserved |
| `branch_code_num` | INTEGER | FK → `branch` |
| `is_public` | BOOLEAN | Whether this location appears in the public catalog |

---

## `branch`

CHPL branch/system-level codes.

| Column | Type | Description |
|---|---|---|
| `code_num` | INTEGER | Branch code (primary key) |
| `name` | TEXT | Branch name |

---

## `branch_name`

Normalized display names for branches, including abbreviated and full forms.

| Column | Type | Description |
|---|---|---|
| `branch_code_num` | INTEGER | FK → `branch` |
| `name` | TEXT | Display name |

---

## `language_property`

MARC language codes mapped to language names.

| Column | Type | Description |
|---|---|---|
| `code` | TEXT | Three-letter MARC language code |
| `name` | TEXT | Language name in English |

---

## `country_property_myuser`

Country codes used in Sierra's location data.

| Column | Type | Description |
|---|---|---|
| `code` | TEXT | Two-letter country code |
| `name` | TEXT | Country name |

---

## `item_status_property`

Sierra item status codes and their display labels.

| Column | Type | Description |
|---|---|---|
| `code` | TEXT | Single-character status code |
| `name` | TEXT | Human-readable status (e.g. `Available`, `Checked Out`) |

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
| `code_num` | INTEGER | Item type code |
| `name` | TEXT | Format name (e.g. `Book`, `DVD`, `Audiobook`) |

---

## `bib_level_property`

Sierra bibliographic level codes.

| Column | Type | Description |
|---|---|---|
| `code` | TEXT | Single-character bib level code |
| `name` | TEXT | Description |

---

## `material_property`

Material type codes from Sierra.

| Column | Type | Description |
|---|---|---|
| `code` | TEXT | Material type code |
| `name` | TEXT | Material type name |

---

## `location_name`

Full display names for location codes.

| Column | Type | Description |
|---|---|---|
| `location_code` | TEXT | FK → `location.code` |
| `name` | TEXT | Full display name (e.g. `Main Library`) |
