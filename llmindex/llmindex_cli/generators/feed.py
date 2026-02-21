"""Generate products.jsonl feed."""

from __future__ import annotations

import json
from pathlib import Path

from llmindex.llmindex_cli.models import Product


def generate_feed(products: list[Product]) -> str:
    """Generate JSONL content from a list of Product models.

    Each line is a JSON object with fields matching the spec.
    """
    lines = []
    for p in products:
        obj: dict = {
            "id": p.id,
            "title": p.title,
            "url": p.url,
            "availability": p.availability,
            "updated_at": p.updated_at,
        }
        if p.image_url:
            obj["image_url"] = p.image_url
        if p.price is not None and p.currency:
            obj["price"] = p.price
            obj["currency"] = p.currency
        if p.price_range:
            obj["price_range"] = p.price_range.model_dump()
        if p.brand:
            obj["brand"] = p.brand
        if p.category:
            obj["category"] = p.category

        lines.append(json.dumps(obj, ensure_ascii=False))

    return "\n".join(lines) + "\n" if lines else ""


def write_feed(products: list[Product], output_dir: str) -> str:
    """Generate and write products.jsonl to output_dir/llm/feed/."""
    feed_dir = Path(output_dir) / "llm" / "feed"
    feed_dir.mkdir(parents=True, exist_ok=True)

    path = feed_dir / "products.jsonl"
    content = generate_feed(products)
    path.write_text(content, encoding="utf-8")

    return str(path)
