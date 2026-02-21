"""Shopify CSV importer — reads a Shopify product export CSV and returns Product models.

Shopify exports products in a specific CSV format with columns like:
Handle, Title, Vendor, Type, Tags, Published, Variant SKU, Variant Price, etc.

This importer maps the Shopify format to the llmindex Product model.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from cli.llmindex_cli.models import Product


# Mapping from Shopify CSV columns to llmindex Product fields
_SHOPIFY_COLUMN_MAP = {
    "Handle": "handle",
    "Title": "title",
    "Vendor": "brand",
    "Type": "category",
    "Variant SKU": "sku",
    "Variant Price": "price",
    "Image Src": "image_url",
    "Published": "published",
    "Status": "status",
}


def import_shopify_csv(
    path: str | Path,
    base_url: str = "https://example.com",
    currency: str = "USD",
) -> list[Product]:
    """Import products from a Shopify product export CSV.

    Args:
        path: Path to the Shopify CSV export.
        base_url: Base URL for constructing product URLs (e.g., https://mystore.com).
        currency: Default currency code (Shopify CSVs may not include currency).

    Returns:
        List of Product models.
    """
    path = Path(path)
    products: list[Product] = []
    errors: list[str] = []
    seen_handles: set[str] = set()

    base_url = base_url.rstrip("/")

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                handle = row.get("Handle", "").strip()
                if not handle:
                    continue

                # Shopify exports multiple rows per product (variants).
                # Take only the first row for each handle.
                if handle in seen_handles:
                    continue
                seen_handles.add(handle)

                title = row.get("Title", "").strip()
                if not title:
                    continue

                # Build product URL from handle
                url = f"{base_url}/products/{handle}"

                # Price
                price_raw = row.get("Variant Price", "").strip()
                price = float(price_raw) if price_raw else None

                # Image
                image_url = row.get("Image Src", "").strip() or None

                # Brand / Category
                brand = row.get("Vendor", "").strip() or None
                category = row.get("Type", "").strip() or None

                # Availability from Status/Published
                status = row.get("Status", "active").strip().lower()
                published = row.get("Published", "true").strip().lower()
                if status == "draft" or published == "false":
                    availability = "out_of_stock"
                else:
                    availability = "in_stock"

                # SKU as product ID, fallback to handle
                product_id = row.get("Variant SKU", "").strip() or handle

                product = Product(
                    id=product_id,
                    title=title,
                    url=url,
                    image_url=image_url,
                    price=price,
                    currency=currency if price is not None else None,
                    availability=availability,
                    brand=brand,
                    category=category,
                    updated_at=datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                )
                products.append(product)
            except Exception as exc:
                errors.append(f"Row {row_num}: {exc}")

    if errors:
        import sys

        for err in errors:
            print(f"[warn] {err}", file=sys.stderr)

    return products
