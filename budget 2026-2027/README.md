# Budget Speech 2026-2027 — Base médias

Base de données et images standardisées pour le discours budgétaire.

## Structure

```
budget 2026-2027/
├── data/
│   ├── themes.json      # Configuration des 35 thèmes
│   └── summary.json     # État actuel (généré)
├── database/
│   └── budget_2026_2027.db
├── images/
│   ├── originals/       # Copies des fichiers sources
│   └── standardized/    # Images 1920×1080 JPEG (16:9)
│       └── alternates/  # Images de remplacement
└── scripts/
    ├── setup_database.py
    └── query.py
```

## Standard image

- **Format :** JPEG, qualité 85
- **Dimensions :** 1920 × 1080 px (16:9)
- **Nommage :** `NN_slug.jpg` (ex. `02_economie-investissement.jpg`)

## Commandes

```bash
source .venv/bin/activate

# (Re)générer images + base de données
python scripts/setup_database.py

# Lister tous les thèmes
python scripts/query.py --list

# Thèmes sans image
python scripts/query.py --missing

# Détail d'un thème
python scripts/query.py --theme sante
```

## Thèmes à valider

| # | Thème | Image actuelle | Note |
|---|-------|----------------|------|
| 28 | Eau et assainissement | Canette + éclaboussure d'eau | À remplacer |
| 30 | Culture, arts et patrimoine | `1.webp` | À remplacer |
| 34 | Défense et sécurité nationale | `port plane agalega.jpg` | À remplacer |

## Bilan actuel

- **35** thèmes — **32** prêts, **3** à valider, **0** manquants

## Thèmes ajoutés (24–35)

| # | Thème |
|---|-------|
| 24 | Énergie et électricité |
| 25 | Cybersécurité et protection des données |
| 26 | Jeunesse et employabilité |
| 27 | PME et entrepreneuriat |
| 28 | Eau et assainissement |
| 29 | Transports et mobilité urbaine |
| 30 | Culture, arts et patrimoine |
| 31 | Finances publiques et gestion de la dette |
| 32 | Handicap et inclusion sociale |
| 33 | Climat et transition écologique |
| 34 | Défense et sécurité nationale |
| 35 | Retraites et pensions |

Pour ajouter une image : placez le fichier à la racine, mettez à jour `primary_image` dans `data/themes.json`, puis relancez `setup_database.py`.
