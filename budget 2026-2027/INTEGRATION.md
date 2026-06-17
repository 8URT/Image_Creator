# Budget Speech 2026-2027 — Integration Guide

Documentation for connecting an external app to this media database.

---

## Overview

This package contains **35 budget speech themes**, each with a standardized background image (1920×1080 JPEG, 16:9) and optional alternates. Data is available in three forms:

| Source | Path | Best for |
|--------|------|----------|
| **SQLite** | `database/budget_2026_2027.db` | Apps that query relational data |
| **API export** | `data/api-export.json` | Simple HTTP/static imports, frontends |
| **Full config** | `data/themes.json` | Rebuilding or editing the database |
| **Summary** | `data/summary.json` | Quick status check |

All image paths in the database are **relative to the project root**.

---

## Directory structure

```
budget 2026-2027/
├── database/
│   └── budget_2026_2027.db      ← SQLite database
├── data/
│   ├── api-export.json          ← Flat JSON for app consumption
│   ├── themes.json              ← Source of truth (config)
│   └── summary.json             ← Lightweight status list
├── images/
│   ├── standardized/            ← Primary images (use these)
│   │   ├── 01_gros-titre-budget.jpg
│   │   ├── 02_economie-investissement.jpg
│   │   └── ...
│   └── standardized/alternates/ ← Backup images per theme
└── images/originals/            ← Unprocessed source copies
```

---

## Image spec

| Property | Value |
|----------|-------|
| Width | 1920 px |
| Height | 1080 px |
| Format | JPEG |
| Aspect ratio | 16:9 (center-cropped) |
| Quality | 85% |

**Naming convention:** `NN_slug.jpg`

- `NN` = zero-padded theme ID (01–35)
- `slug` = URL-safe theme identifier

Example: `12_sante.jpg` → theme ID 12, slug `sante`

---

## Status values

| Status | Meaning |
|--------|---------|
| `ready` | Image assigned and validated |
| `needs_review` | Image assigned but may need replacement |
| `missing` | No image assigned |

Themes currently marked `needs_review`: **28** (Eau), **30** (Culture), **34** (Défense).

---

## SQLite schema

### Table: `themes`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key (1–35) |
| `slug` | TEXT | Unique identifier, e.g. `sante` |
| `title_fr` | TEXT | French display title |
| `title_en` | TEXT | English display title |
| `sort_order` | INTEGER | Display order (= `id`) |
| `status` | TEXT | `ready`, `needs_review`, or `missing` |
| `notes` | TEXT | Optional notes (nullable) |

### Table: `images`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-increment primary key |
| `theme_id` | INTEGER | FK → `themes.id` |
| `role` | TEXT | `primary` or `alternate` |
| `original_filename` | TEXT | Source file name |
| `original_path` | TEXT | Relative path to source |
| `standardized_filename` | TEXT | Output file name |
| `standardized_path` | TEXT | Relative path to standardized image |
| `source_width` | INTEGER | Original width in px |
| `source_height` | INTEGER | Original height in px |
| `output_width` | INTEGER | Always 1920 |
| `output_height` | INTEGER | Always 1080 |
| `file_size_bytes` | INTEGER | JPEG file size |
| `created_at` | TEXT | ISO 8601 UTC timestamp |

---

## SQL queries

### All themes with primary image (recommended for app load)

```sql
SELECT
    t.id,
    t.slug,
    t.title_fr,
    t.title_en,
    t.status,
    t.sort_order,
    i.standardized_path   AS image_path,
    i.standardized_filename AS image_filename,
    i.file_size_bytes
FROM themes t
LEFT JOIN images i ON i.theme_id = t.id AND i.role = 'primary'
ORDER BY t.sort_order;
```

### Single theme by slug

```sql
SELECT t.*, i.standardized_path, i.standardized_filename
FROM themes t
LEFT JOIN images i ON i.theme_id = t.id AND i.role = 'primary'
WHERE t.slug = 'sante';
```

### All images for a theme (primary + alternates)

```sql
SELECT role, standardized_path, standardized_filename, file_size_bytes
FROM images
WHERE theme_id = 12
ORDER BY role DESC, id;
```

### Only ready themes

```sql
SELECT t.id, t.slug, t.title_fr, i.standardized_path
FROM themes t
JOIN images i ON i.theme_id = t.id AND i.role = 'primary'
WHERE t.status = 'ready'
ORDER BY t.sort_order;
```

---

## JSON consumption

### `data/api-export.json` structure

```json
{
  "budget_year": "2026-2027",
  "image_spec": {
    "width": 1920,
    "height": 1080,
    "format": "jpeg",
    "aspect_ratio": "16:9"
  },
  "themes": [
    {
      "id": 12,
      "slug": "sante",
      "title_fr": "Santé",
      "title_en": "Health",
      "status": "ready",
      "sort_order": 12,
      "image_path": "images/standardized/12_sante.jpg",
      "image_filename": "12_sante.jpg",
      "file_size_bytes": 224678
    }
  ]
}
```

### JavaScript example

```javascript
const BASE = '/path/to/budget 2026-2027';

async function loadThemes() {
  const res = await fetch(`${BASE}/data/api-export.json`);
  const data = await res.json();
  return data.themes.map(theme => ({
    ...theme,
    imageUrl: `${BASE}/${theme.image_path}`,
  }));
}
```

### Python example

```python
import json
import sqlite3
from pathlib import Path

ROOT = Path("/path/to/budget 2026-2027")

# Option A: JSON
with open(ROOT / "data/api-export.json") as f:
    data = json.load(f)
for theme in data["themes"]:
    image = ROOT / theme["image_path"]
    print(theme["title_fr"], image.exists())

# Option B: SQLite
conn = sqlite3.connect(ROOT / "database/budget_2026_2027.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("""
    SELECT t.slug, t.title_fr, i.standardized_path
    FROM themes t
    JOIN images i ON i.theme_id = t.id AND i.role = 'primary'
    WHERE t.status = 'ready'
    ORDER BY t.sort_order
""").fetchall()
conn.close()
```

---

## Full theme index

| ID | Slug | Title (FR) | Status |
|----|------|------------|--------|
| 01 | `gros-titre-budget` | Gros titre budget | ready |
| 02 | `economie-investissement` | Économie et investissement | ready |
| 03 | `femmes-emploi` | Femmes et emploi | ready |
| 04 | `technologie-ia` | Technologie et IA | ready |
| 05 | `agriculture-securite-alimentaire` | Agriculture et sécurité alimentaire | ready |
| 06 | `peche-economie-bleue` | Pêcheurs — économie bleue | ready |
| 07 | `secteur-animal` | Secteur animal | ready |
| 08 | `tourisme` | Tourisme | ready |
| 09 | `infrastructures-publiques` | Infrastructures publiques | ready |
| 10 | `pouvoir-achat` | Pouvoir d'achat — TVA, gaz, alimentation | ready |
| 11 | `education` | Éducation | ready |
| 12 | `sante` | Santé | ready |
| 13 | `securite-sociale` | Sécurité sociale | ready |
| 14 | `logement` | Logement | ready |
| 15 | `environnement` | Environnement | ready |
| 16 | `drogue-police-justice-nadc` | Drogue, police et justice — NADC | ready |
| 17 | `securite-routiere` | Sécurité routière | ready |
| 18 | `sports` | Sports | ready |
| 19 | `rodrigues-agalega` | Rodrigues et Agaléga | ready |
| 20 | `fiscalite-particuliers` | Fiscalité des particuliers | ready |
| 21 | `vehicules-hybrides-electriques` | Véhicules — hybrides et électriques | ready |
| 22 | `entreprises-hauts-revenus` | Entreprises et hauts revenus | ready |
| 23 | `aides-sociales-supplementaires` | Aides sociales supplémentaires | ready |
| 24 | `energie-electricite` | Énergie et électricité | ready |
| 25 | `cybersecurite` | Cybersécurité et protection des données | ready |
| 26 | `jeunesse-emploi` | Jeunesse et employabilité | ready |
| 27 | `pme-entrepreneuriat` | PME et entrepreneuriat | ready |
| 28 | `eau-assainissement` | Eau et assainissement | needs_review |
| 29 | `transports-mobilite` | Transports et mobilité urbaine | ready |
| 30 | `culture-patrimoine` | Culture, arts et patrimoine | needs_review |
| 31 | `finances-publiques-dette` | Finances publiques et gestion de la dette | ready |
| 32 | `handicap-inclusion` | Handicap et inclusion sociale | ready |
| 33 | `climat-transition-ecologique` | Climat et transition écologique | ready |
| 34 | `defense-securite-nationale` | Défense et sécurité nationale | needs_review |
| 35 | `retraites-pensions` | Retraites et pensions | ready |

---

## Integration checklist

1. **Copy these folders** into your app or mount as a static asset:
   - `database/budget_2026_2027.db`
   - `images/standardized/` (and `alternates/` if needed)
   - `data/api-export.json` (if using JSON)

2. **Resolve image URLs** by prepending your base path:
   ```
   {BASE_URL}/images/standardized/12_sante.jpg
   ```

3. **Load themes** via SQLite or `api-export.json` (see examples above).

4. **Filter by status** if you only want production-ready themes:
   ```sql
   WHERE t.status = 'ready'
   ```

5. **Refresh data** after any update to this folder:
   ```bash
   source .venv/bin/activate
   python scripts/setup_database.py
   ```
   This regenerates the DB, `summary.json`, and `api-export.json`.

---

## Regenerating exports

After editing `data/themes.json` or adding new source images:

```bash
source .venv/bin/activate
python scripts/setup_database.py
```

Then re-copy `database/`, `images/standardized/`, and `data/api-export.json` to your app.

---

## Recommended app model

```typescript
interface BudgetTheme {
  id: number;
  slug: string;
  title_fr: string;
  title_en: string;
  status: 'ready' | 'needs_review' | 'missing';
  sort_order: number;
  image_path: string;       // relative path
  image_url: string;        // resolved URL in your app
  alternates?: string[];    // optional, from images table
}
```

Typical flow for a presentation/broadcast app:

1. Load all `ready` themes ordered by `sort_order`
2. Display `title_fr` as section heading
3. Show `image_url` as fullscreen background during that segment
4. Fall back to alternates if primary fails to load
