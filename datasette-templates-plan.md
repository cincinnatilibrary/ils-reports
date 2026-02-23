# Plan: CHPL-Branded Datasette 1.0 Templates

## Context

The current `datasette/templates/index.html` uses a teal hero (`#00695c`) that is not a CHPL brand color and has no logo. This plan replaces it with three properly branded template variants derived from the official 2020 CHPL Brand Guidelines PDF, targets Datasette 1.0, and documents compatibility considerations.

---

## Datasette 1.0 Compatibility Notes

| Topic | Finding |
|---|---|
| Template API stability | **Not guaranteed stable** — may change on minor version bumps; document which Datasette version each template was written against |
| Safest override strategy | `extra_css_urls` CSS + minimal block overrides (`extra_head`, `nav`, `content`, `footer`); avoid full `base.html` rewrites |
| Template inheritance | `{% extends "default:index.html" %}` + `{{ super() }}` works in 1.0 |
| Plugin config | Moved from `metadata.yaml` → `datasette.yaml` in 1.0; canned queries and table/column descriptions stay in `metadata.yml` |
| `--config` flag | Verify flag syntax unchanged under 1.0; update Makefile/Dockerfile if needed |
| `settings:` block | Our current `datasette.yml` `settings:` format is forward-compatible |
| Hashed URL mode | Removed from core in 1.0 (moved to separate plugin); no impact on our setup |

**Version change required:** `pyproject.toml` `datasette>=0.64` → `datasette>=1.0`

---

## Official Brand Tokens (CHPL Brand Guidelines 2020, page 21–22)

### Primary Palette

| Name | Hex | Use |
|---|---|---|
| CHPL Navy | `#0C2340` | Core color; headlines, nav backgrounds |
| Cream | `#F6F1EB` | Alternate body background (brand-sanctioned) |
| Gray 30% | `#BCBEC0` | Borders, subtle dividers |
| Gray 60% | `#808285` | Secondary / caption text |
| White | `#FFFFFF` | Body backgrounds, text on dark |

### Secondary Palette (from the logo dots)

| Name | Hex | 50% Tint | Use |
|---|---|---|---|
| Blue | `#0092BD` | `#71C5E8` | Links, primary accent |
| Teal | `#34B78F` | `#91D6AC` | Accent borders, highlights |
| Purple | `#8659B5` | `#C7B2DE` | Accent only |
| Gold | `#FFB81C` | `#F9E27D` | Accent only |
| Coral | `#E56A54` | `#FFB3AB` | Accent only |

> Per guidelines: secondary palette is for subheads, accents, and background floods only —
> **never for body copy**. If used as a background, typography must be white or CHPL Navy.

### Typography

- **Brand typeface:** BrownStd (licensed from Lineto — **not available as a web font**)
- **Web fallback:** Arial — the brand-sanctioned digital alternate for day-to-day digital use
- **Font stack:** `Arial, "Helvetica Neue", sans-serif`
- **Headlines:** Bold weight, CHPL Navy `#0C2340`
- **Body copy:** Regular/Light weight, Navy or Gray 60%

### Logo Usage Rules

- Full-color Primary brandmark: approved on **white, cream, or navy backgrounds only**
- DO NOT place on colored backgrounds (e.g., teal, blue, green)
- DO NOT skew, distort, alter colors, or remove "Hamilton County"
- Minimum sizes: 96px wide (with location), 72px (full color), 48px (one-color)
- **On navy header:** no white SVG exists in the brand kit — use `CHPL_Brandmark_Primary.svg`
  with CSS `filter: brightness(0) invert(1)` to render a white logo (accepted web compromise;
  the colored dots become white but the wordmark reads clearly)

---

## Logo Assets to Use

Copy from `reference/CHPL_BrandGuidelines/` → `datasette/static/`:

| File | When to use |
|---|---|
| `CHPL_Brandmark_Primary.svg` | White or cream header background (full color — brand correct) |
| `CHPL_Brandmark_Primary.svg` + CSS invert | Navy header background |
| `CHPL_Brandmark_OneColorNavy.svg` | Alternative on cream if full-color feels too busy |

---

## Architecture: CSS-Driven Variants

All three variants share **identical template files**. Visual differences are expressed
entirely through CSS custom properties. Switching variants = changing one line in `datasette.yml`.

### Shared `chpl-base.css` — brand token declarations

```css
:root {
  /* Primary palette */
  --chpl-navy:   #0C2340;
  --chpl-cream:  #F6F1EB;
  --chpl-gray30: #BCBEC0;
  --chpl-gray60: #808285;

  /* Secondary palette */
  --chpl-teal:       #34B78F;
  --chpl-teal-light: #91D6AC;
  --chpl-blue:       #0092BD;
  --chpl-blue-light: #71C5E8;

  /* Semantic tokens — overridden per variant */
  --chpl-header-bg:      var(--chpl-navy);
  --chpl-header-text:    #ffffff;
  --chpl-body-bg:        #ffffff;
  --chpl-accent:         var(--chpl-teal);
  --chpl-link:           var(--chpl-blue);
  --chpl-logo-filter:    none;

  /* Typography */
  --chpl-font: Arial, "Helvetica Neue", sans-serif;
}

/* Apply tokens to Datasette's structure */
body   { background: var(--chpl-body-bg); font-family: var(--chpl-font); }
.hd    { background: var(--chpl-header-bg); color: var(--chpl-header-text); }
a      { color: var(--chpl-link); }
.chpl-logo { filter: var(--chpl-logo-filter); }
/* ... table headers, row hover, nav link styling ... */
```

---

## Three Variants

### Variant A — "Navy Header" *(recommended default)*

```
┌──────────────────────────────────────────────────────────┐
│  [LOGO white]   CHPL Collection Analysis      [nav]      │  ← #0C2340 navy bg
├──────────────────────────────────────────────────────────┤
│                                                          │
│   Hero: description, data freshness note, source link    │  ← white body (#FFFFFF)
│   Teal (#34B78F) accent borders                          │
│   [Datasette default table/database listing]             │
└──────────────────────────────────────────────────────────┘
```

**File:** `datasette/static/chpl-navy.css`

```css
:root {
  --chpl-header-bg:   #0C2340;
  --chpl-header-text: #ffffff;
  --chpl-body-bg:     #ffffff;
  --chpl-accent:      #34B78F;
  --chpl-link:        #0092BD;
  --chpl-logo-filter: brightness(0) invert(1);  /* white logo on navy */
}
```

---

### Variant B — "Light" *(most brand-correct logo placement)*

```
┌──────────────────────────────────────────────────────────┐
│ ████████████████████████ 4px #0C2340 top stripe          │
│  [LOGO full color]   CHPL Collection Analysis   [nav]   │  ← white bg, navy text
├──────────────────────────────────────────────────────────┤
│  ▌ #34B78F teal accent bar                               │
│   Hero + Datasette table listing                         │  ← white body
└──────────────────────────────────────────────────────────┘
```

**File:** `datasette/static/chpl-light.css`

```css
:root {
  --chpl-header-bg:          #ffffff;
  --chpl-header-text:        #0C2340;
  --chpl-header-border-top:  4px solid #0C2340;
  --chpl-body-bg:            #ffffff;
  --chpl-accent:             #34B78F;
  --chpl-link:               #0C2340;
  --chpl-logo-filter:        none;  /* full color logo — brand correct on white */
}
```

---

### Variant C — "Cream" *(warmest, most inviting)*

```
┌──────────────────────────────────────────────────────────┐
│  [LOGO full color]   CHPL Collection Analysis   [nav]   │  ← #F6F1EB cream bg
│ ████████████████████████ 3px #0C2340 bottom rule         │
├──────────────────────────────────────────────────────────┤
│   Hero + Datasette table listing                         │  ← cream body (#F6F1EB)
│   Navy headings, blue (#0092BD) links                    │
└──────────────────────────────────────────────────────────┘
```

**File:** `datasette/static/chpl-cream.css`

```css
:root {
  --chpl-header-bg:             #F6F1EB;
  --chpl-header-text:           #0C2340;
  --chpl-header-border-bottom:  3px solid #0C2340;
  --chpl-body-bg:               #F6F1EB;
  --chpl-accent:                #0092BD;  /* blue for contrast on cream */
  --chpl-link:                  #0C2340;
  --chpl-logo-filter:           none;  /* full color logo — brand correct on cream */
}
```

---

## Shared Templates

### `datasette/templates/base.html`

Extends `default:base.html`. Overrides two blocks only:

- `{% block nav %}` — prepends SVG logo + site title before Datasette's default nav links
- `{% block footer %}` — replaces default footer with CHPL footer (name, chpl.org link, data freshness note)

```jinja2
{% extends "default:base.html" %}

{% block nav %}
<div class="chpl-header-inner">
  <a href="/" class="chpl-logo-link">
    <img src="{{ urls.static('CHPL_Brandmark_Primary.svg') }}"
         alt="Cincinnati & Hamilton County Public Library"
         class="chpl-logo"
         width="100">
  </a>
  <span class="chpl-site-title">Collection Analysis</span>
</div>
{{ super() }}
{% endblock %}

{% block footer %}
<footer class="chpl-footer">
  <p>
    <a href="https://www.chpl.org/">Cincinnati &amp; Hamilton County Public Library</a>
    &middot; Data updated nightly from Sierra ILS
    &middot; <a href="https://github.com/cincinnatilibrary/ils-reports">Source</a>
  </p>
</footer>
{% endblock %}
```

> **Maintenance note:** `base.html` overrides may need minor updates on Datasette minor
> version bumps (template API is not guaranteed stable). Record Datasette version in a
> comment at the top of this file.

### `datasette/templates/index.html`

Replaces the current placeholder. Extends `default:index.html`:

```jinja2
{% extends "default:index.html" %}

{% block extra_head %}
{# All styling comes from chpl-base.css + variant CSS via extra_css_urls #}
{% endblock %}

{% block content %}
<div class="chpl-hero">
  <h1>CHPL Collection Analysis</h1>
  <p>
    A nightly snapshot of the
    <a href="https://www.chpl.org/">Cincinnati &amp; Hamilton County Public Library</a>
    physical collection, extracted from the Sierra ILS.
    Data is current as of the previous evening.
  </p>
  <p><a href="https://github.com/cincinnatilibrary/ils-reports">Source code</a></p>
</div>
{{ super() }}
{% endblock %}
```

---

## Files to Create / Modify

| File | Action |
|---|---|
| `datasette/static/CHPL_Brandmark_Primary.svg` | Copy from `reference/CHPL_BrandGuidelines/` |
| `datasette/static/CHPL_Brandmark_OneColorNavy.svg` | Copy from `reference/CHPL_BrandGuidelines/` |
| `datasette/static/chpl-base.css` | Brand tokens + shared layout rules |
| `datasette/static/chpl-navy.css` | Variant A overrides |
| `datasette/static/chpl-light.css` | Variant B overrides |
| `datasette/static/chpl-cream.css` | Variant C overrides |
| `datasette/templates/base.html` | Logo in nav + branded footer |
| `datasette/templates/index.html` | Replaces current placeholder |
| `pyproject.toml` | `datasette>=0.64` → `datasette>=1.0` in optional-dependencies |
| `datasette/datasette.yml` | Add `extra_css_urls: [chpl-base.css, chpl-navy.css]` |

---

## `datasette.yml` Addition

```yaml
extra_css_urls:
  - /static/chpl-base.css
  - /static/chpl-navy.css   # swap to chpl-light.css or chpl-cream.css for other variants
```

---

## Questions / Decisions Before Implementing

1. **Which variant should be the starting default?** (Navy A is recommended, but open to preference)
2. **Title:** Current metadata has emoji (`"CHPL Collection 📚 & Branch Explorer 🗺️"` from the old server). Keep, drop, or revise?
3. **Datasette 1.0 now:** Do you want to upgrade to 1.0 as part of this work, or hold at 0.x and build templates that will be 1.0-ready?
4. **Google Fonts fallback:** BrownStd isn't available. Arial is the official alternate. Acceptable, or worth exploring a Google Font substitute like Inter or DM Sans that has a similar geometric feel?

---

## Verification

- `make datasette` (requires a built `current_collection.db`) → opens on port 8001
- Visually check each variant by swapping `extra_css_urls` in `datasette.yml` and restarting
- Check all key pages: `/`, `/current_collection`, `/current_collection/item`, a canned query
- Confirm logo renders correctly on each header background
- Confirm `uv run datasette --version` reports 1.0.x after dependency update
