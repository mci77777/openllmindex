"""Generate /.well-known/llmindex.json manifest."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from llmindex.llmindex_cli.models import SiteConfig


def generate_manifest(config: SiteConfig, has_feed: bool = True) -> dict:
    """Build the llmindex.json manifest dict from a SiteConfig."""
    base = config.get_base_url()

    manifest: dict = {
        "version": "0.1",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entity": {
            "name": config.name,
            "canonical_url": config.canonical_url,
        },
        "language": config.language,
        "topics": config.topics,
        "endpoints": {
            "products": f"{base}/llm/products",
            "policies": f"{base}/llm/policies",
            "faq": f"{base}/llm/faq",
            "about": f"{base}/llm/about",
        },
    }

    if has_feed:
        manifest["feeds"] = {
            "products_jsonl": f"{base}/llm/feed/products.jsonl",
        }

    return manifest


def write_manifest(manifest: dict, output_path: str) -> None:
    """Serialize manifest to JSON and write to file."""
    from pathlib import Path

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
