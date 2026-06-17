#!/usr/bin/env python3
"""Standardize budget speech images and populate SQLite database."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "themes.json"
ORIGINALS_DIR = ROOT / "images" / "originals"
STANDARDIZED_DIR = ROOT / "images" / "standardized"
DB_PATH = ROOT / "database" / "budget_2026_2027.db"


def load_config() -> dict:
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def standardize_image(
    source: Path,
    dest: Path,
    width: int,
    height: int,
    quality: int,
) -> dict:
    """Crop to 16:9 (center) and resize to target dimensions."""
    with Image.open(source) as img:
        img = img.convert("RGB")
        src_w, src_h = img.size
        target_ratio = width / height
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            box = (left, 0, left + new_w, src_h)
        else:
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            box = (0, top, src_w, top + new_h)

        cropped = img.crop(box)
        resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        resized.save(dest, "JPEG", quality=quality, optimize=True)

        return {
            "source_width": src_w,
            "source_height": src_h,
            "output_width": width,
            "output_height": height,
            "file_size_bytes": dest.stat().st_size,
        }


def init_database(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY,
            slug TEXT NOT NULL UNIQUE,
            title_fr TEXT NOT NULL,
            title_en TEXT,
            sort_order INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'missing',
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('primary', 'alternate')),
            original_filename TEXT,
            original_path TEXT,
            standardized_filename TEXT,
            standardized_path TEXT,
            source_width INTEGER,
            source_height INTEGER,
            output_width INTEGER,
            output_height INTEGER,
            file_size_bytes INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (theme_id) REFERENCES themes(id)
        );

        CREATE INDEX IF NOT EXISTS idx_images_theme ON images(theme_id);
        CREATE INDEX IF NOT EXISTS idx_images_role ON images(role);
        """
    )


def archive_originals() -> None:
  """Copy loose root images into images/originals/ (once)."""
  ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
  extensions = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".JPG"}
  for path in ROOT.iterdir():
      if path.is_file() and path.suffix in extensions:
          dest = ORIGINALS_DIR / path.name
          if not dest.exists():
              shutil.copy2(path, dest)


def process_theme_images(config: dict, conn: sqlite3.Connection) -> dict:
    spec = config["standard_image"]
    width = spec["width"]
    height = spec["height"]
    quality = spec["quality"]
    now = datetime.now(timezone.utc).isoformat()

    stats = {"processed": 0, "skipped": 0, "missing": 0, "errors": []}

    for theme in config["themes"]:
        conn.execute(
            """
            INSERT INTO themes (id, slug, title_fr, title_en, sort_order, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                slug = excluded.slug,
                title_fr = excluded.title_fr,
                title_en = excluded.title_en,
                sort_order = excluded.sort_order,
                status = excluded.status,
                notes = excluded.notes
            """,
            (
                theme["id"],
                theme["slug"],
                theme["title_fr"],
                theme.get("title_en"),
                theme["id"],
                theme["status"],
                None,
            ),
        )

        primary = theme.get("primary_image")
        if not primary:
            stats["missing"] += 1
            continue

        source_candidates = [
            ROOT / primary,
            ORIGINALS_DIR / primary,
        ]
        source = next((p for p in source_candidates if p.exists()), None)
        if source is None:
            stats["errors"].append(f"{theme['slug']}: source not found ({primary})")
            stats["missing"] += 1
            continue

        dest_name = f"{theme['id']:02d}_{theme['slug']}.jpg"
        dest = STANDARDIZED_DIR / dest_name

        try:
            meta = standardize_image(source, dest, width, height, quality)
            conn.execute(
                """
                INSERT INTO images (
                    theme_id, role, original_filename, original_path,
                    standardized_filename, standardized_path,
                    source_width, source_height, output_width, output_height,
                    file_size_bytes, created_at
                ) VALUES (?, 'primary', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    theme["id"],
                    primary,
                    str(source.relative_to(ROOT)),
                    dest_name,
                    str(dest.relative_to(ROOT)),
                    meta["source_width"],
                    meta["source_height"],
                    meta["output_width"],
                    meta["output_height"],
                    meta["file_size_bytes"],
                    now,
                ),
            )
            stats["processed"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["errors"].append(f"{theme['slug']}: {exc}")
            stats["skipped"] += 1

        for alt in theme.get("alternates", []):
            alt_source = next(
                (p for p in [ROOT / alt, ORIGINALS_DIR / alt] if p.exists()),
                None,
            )
            if alt_source is None:
                continue
            alt_dest_name = f"{theme['id']:02d}_{theme['slug']}_alt_{Path(alt).stem}.jpg"
            alt_dest = STANDARDIZED_DIR / "alternates" / alt_dest_name
            try:
                meta = standardize_image(alt_source, alt_dest, width, height, quality)
                conn.execute(
                    """
                    INSERT INTO images (
                        theme_id, role, original_filename, original_path,
                        standardized_filename, standardized_path,
                        source_width, source_height, output_width, output_height,
                        file_size_bytes, created_at
                    ) VALUES (?, 'alternate', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        theme["id"],
                        alt,
                        str(alt_source.relative_to(ROOT)),
                        alt_dest_name,
                        str(alt_dest.relative_to(ROOT)),
                        meta["source_width"],
                        meta["source_height"],
                        meta["output_width"],
                        meta["output_height"],
                        meta["file_size_bytes"],
                        now,
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                stats["errors"].append(f"{theme['slug']} alt ({alt}): {exc}")

    conn.commit()
    return stats


def export_summary(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT t.id, t.slug, t.title_fr, t.status,
               i.standardized_path, i.file_size_bytes
        FROM themes t
        LEFT JOIN images i ON i.theme_id = t.id AND i.role = 'primary'
        ORDER BY t.sort_order
        """
    ).fetchall()

    summary = []
    for row in rows:
        summary.append(
            {
                "id": row[0],
                "slug": row[1],
                "title_fr": row[2],
                "status": row[3],
                "standardized_image": row[4],
                "file_size_kb": round(row[5] / 1024, 1) if row[5] else None,
            }
        )

    out = ROOT / "data" / "summary.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "budget_year": "2026-2027",
                "themes": summary,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def export_api(conn: sqlite3.Connection, config: dict) -> None:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.id, t.slug, t.title_fr, t.title_en, t.status, t.sort_order,
               i.standardized_path AS image_path,
               i.standardized_filename AS image_filename,
               i.file_size_bytes
        FROM themes t
        LEFT JOIN images i ON i.theme_id = t.id AND i.role = 'primary'
        ORDER BY t.sort_order
        """
    ).fetchall()

    out = ROOT / "data" / "api-export.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "budget_year": config.get("budget_year", "2026-2027"),
                "image_spec": config.get("standard_image", {}),
                "themes": [dict(row) for row in rows],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    config = load_config()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Archiving originals...")
    archive_originals()

    conn = sqlite3.connect(DB_PATH)
    try:
        init_database(conn)
        conn.execute("DELETE FROM images")
        conn.execute("DELETE FROM themes")

        print("Standardizing images...")
        stats = process_theme_images(config, conn)
        export_summary(conn)
        export_api(conn, config)

        print(f"\nDone — {stats['processed']} primary images processed")
        print(f"  Missing themes: {stats['missing']}")
        if stats["errors"]:
            print("  Errors:")
            for err in stats["errors"]:
                print(f"    - {err}")
        print(f"\nDatabase: {DB_PATH}")
        print(f"Standardized images: {STANDARDIZED_DIR}")
        print(f"Summary: {ROOT / 'data' / 'summary.json'}")
        print(f"API export: {ROOT / 'data' / 'api-export.json'}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
