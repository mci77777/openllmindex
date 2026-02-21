"""JSON importer — reads a products JSON array and returns a list of Product models."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from llmindex.llmindex_cli.models import Product


def import_json(path: str | Path) -> list[Product]:
    """Import products from a JSON file.

    Expected format: a JSON array of objects with fields matching the Product model:
    [
      {"id": "P001", "title": "Widget", "url": "https://...", "price": 9.99, ...},
      ...
    ]
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")

    products: list[Product] = []
    errors: list[str] = []

    for i, item in enumerate(data):
        try:
            if not isinstance(item, dict):
                errors.append(f"Item {i}: expected object, got {type(item).__name__}")
                continue

            # Fill in defaults
            if "updated_at" not in item or not item["updated_at"]:
                item["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            if "availability" not in item or not item["availability"]:
                item["availability"] = "in_stock"

            product = Product(**item)
            products.append(product)
        except Exception as exc:
            errors.append(f"Item {i}: {exc}")

    if errors:
        import sys

        for err in errors:
            print(f"[warn] {err}", file=sys.stderr)

    return products
