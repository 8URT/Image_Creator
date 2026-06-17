"""Load Budget Speech 2026-2027 theme catalog for the Budget Creator tool."""

from __future__ import annotations

import json
from pathlib import Path

BUDGET_ROOT = Path(__file__).resolve().parent.parent / "budget 2026-2027"
API_EXPORT = BUDGET_ROOT / "data" / "api-export.json"
STANDARDIZED_PREFIX = "images/standardized/"


def _alternate_label(filename: str) -> str:
    """Derive a short label from an alternate filename stem."""
    stem = Path(filename).stem
    if "_alt_" in stem:
        return stem.split("_alt_", 1)[1].replace("-", " ").replace("_", " ")
    return stem


def load_budget_catalog() -> list[dict]:
    """Return themes with primary image paths and discovered alternates."""
    if not API_EXPORT.exists():
        return []

    with API_EXPORT.open(encoding="utf-8") as f:
        data = json.load(f)

    themes = sorted(data.get("themes", []), key=lambda t: t.get("sort_order", t.get("id", 0)))
    catalog: list[dict] = []

    for theme in themes:
        theme_id = theme["id"]
        slug = theme["slug"]
        image_path = theme.get("image_path") or ""

        alternates_dir = BUDGET_ROOT / "images" / "standardized" / "alternates"
        alt_pattern = f"{theme_id:02d}_{slug}_alt_*.jpg"
        alt_paths = sorted(alternates_dir.glob(alt_pattern)) if alternates_dir.exists() else []

        catalog.append(
            {
                "id": theme_id,
                "slug": slug,
                "title_fr": theme.get("title_fr", ""),
                "title_en": theme.get("title_en", ""),
                "status": theme.get("status", "ready"),
                "primary": {
                    "path": image_path,
                    "label": "Image principale",
                },
                "alternates": [
                    {
                        "path": str(p.relative_to(BUDGET_ROOT)).replace("\\", "/"),
                        "label": _alternate_label(p.name),
                    }
                    for p in alt_paths
                ],
            }
        )

    return catalog


def is_allowed_budget_media_path(subpath: str) -> bool:
    """Only serve files under images/standardized/."""
    normalized = subpath.replace("\\", "/").lstrip("/")
    if not normalized.startswith(STANDARDIZED_PREFIX):
        return False
    full = (BUDGET_ROOT / normalized).resolve()
    try:
        full.relative_to(BUDGET_ROOT.resolve())
    except ValueError:
        return False
    return full.is_file()
