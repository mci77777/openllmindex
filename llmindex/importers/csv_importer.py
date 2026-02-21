"""CSV importer — reads a products CSV and returns a list of Product models."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from llmindex.llmindex_cli.models import Product


def import_csv(path: str | Path) -> list[Product]:
    """Import products from a CSV file.

    Expected columns: id, title, url, image_url, price, currency, availability,
                      brand, category, updated_at

    Rows with missing required fields (id, title, url, availability) are skipped
    with a warning printed to stderr.
    """
    path = Path(path)
    products: list[Product] = []
    errors: list[str] = []

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # header is row 1
            try:
                price_raw = row.get("price", "").strip()
                price = float(price_raw) if price_raw else None
                currency = row.get("currency", "").strip() or None

                updated = row.get("updated_at", "").strip()
                if not updated:
                    updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                product = Product(
                    id=row.get("id", "").strip(),
                    title=row.get("title", "").strip(),
                    url=row.get("url", "").strip(),
                    image_url=row.get("image_url", "").strip() or None,
                    price=price,
                    currency=currency,
                    availability=row.get("availability", "in_stock").strip(),
                    brand=row.get("brand", "").strip() or None,
                    category=row.get("category", "").strip() or None,
                    updated_at=updated,
                )
                products.append(product)
            except Exception as exc:
                errors.append(f"Row {row_num}: {exc}")

    if errors:
        import sys

        for err in errors:
            print(f"[warn] {err}", file=sys.stderr)

    return products
