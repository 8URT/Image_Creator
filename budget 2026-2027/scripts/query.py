#!/usr/bin/env python3
"""Quick queries for the budget speech image database."""

import argparse
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "database" / "budget_2026_2027.db"


def list_themes(conn: sqlite3.Connection, status: str | None = None) -> None:
    query = """
        SELECT t.id, t.title_fr, t.status, i.standardized_path
        FROM themes t
        LEFT JOIN images i ON i.theme_id = t.id AND i.role = 'primary'
        ORDER BY t.sort_order
    """
    rows = conn.execute(query).fetchall()
    for row in rows:
        if status and row[2] != status:
            continue
        img = row[3] or "—"
        print(f"{row[0]:2d}. [{row[2]:12s}] {row[1]}")
        print(f"     → {img}")


def show_theme(conn: sqlite3.Connection, slug: str) -> None:
    theme = conn.execute(
        "SELECT id, title_fr, title_en, status FROM themes WHERE slug = ?",
        (slug,),
    ).fetchone()
    if not theme:
        print(f"Theme not found: {slug}")
        return

    print(f"#{theme[0]} {theme[1]}")
    if theme[2]:
        print(f"   EN: {theme[2]}")
    print(f"   Status: {theme[3]}\n")

    images = conn.execute(
        """
        SELECT role, original_filename, standardized_path, file_size_bytes
        FROM images WHERE theme_id = ? ORDER BY role, id
        """,
        (theme[0],),
    ).fetchall()
    for img in images:
        size = f"{img[3] / 1024:.0f} KB" if img[3] else "?"
        print(f"   [{img[0]}] {img[1]}")
        print(f"         → {img[2]} ({size})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query budget speech database")
    parser.add_argument("--list", action="store_true", help="List all themes")
    parser.add_argument("--missing", action="store_true", help="List themes without images")
    parser.add_argument("--theme", help="Show details for a theme slug")
    args = parser.parse_args()

    if not DB.exists():
        print(f"Database not found. Run: python scripts/setup_database.py")
        return

    conn = sqlite3.connect(DB)
    try:
        if args.theme:
            show_theme(conn, args.theme)
        elif args.missing:
            list_themes(conn, status="missing")
        else:
            list_themes(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
