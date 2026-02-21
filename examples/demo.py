"""
llmindex Demo — End-to-end usage example

This script demonstrates the complete llmindex workflow:
1. Import products from CSV
2. Generate all artifacts (manifest, pages, feed)
3. Validate the generated manifest against the JSON Schema
4. Display a summary

Usage:
    python examples/demo.py
"""

import json
import shutil
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from llmindex.importers.csv_importer import import_csv  # noqa: E402
from llmindex.llmindex_cli.generators.feed import write_feed  # noqa: E402
from llmindex.llmindex_cli.generators.manifest import (  # noqa: E402
    generate_manifest,
    write_manifest,
)
from llmindex.llmindex_cli.generators.pages import write_pages  # noqa: E402
from llmindex.llmindex_cli.models import SiteConfig  # noqa: E402


def main():
    # --- Configuration ---
    config = SiteConfig(
        name="Demo Store",
        canonical_url="https://demo-store.example.com",
        language="en",
        topics=["electronics", "gadgets"],
    )
    csv_path = project_root / "llmindex" / "sample_data" / "sample.csv"
    output_dir = project_root / "examples" / "_demo_output"

    # Clean previous output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    print("=" * 60)
    print("llmindex Demo")
    print("=" * 60)

    # --- Step 1: Import products ---
    print(f"\n[1/4] Importing products from {csv_path.name}...")
    products = import_csv(csv_path)
    print(f"      Imported {len(products)} products")
    print(f"      Categories: {sorted(set(p.category for p in products if p.category))}")

    # --- Step 2: Generate artifacts ---
    print("\n[2/4] Generating artifacts...")

    # Manifest
    manifest = generate_manifest(config, has_feed=True)
    manifest_path = str(output_dir / ".well-known" / "llmindex.json")
    write_manifest(manifest, manifest_path)
    print(f"      -> {manifest_path}")

    # Pages
    page_paths = write_pages(products, config, str(output_dir))
    for p in page_paths:
        print(f"      -> {p}")

    # Feed
    feed_path = write_feed(products, str(output_dir))
    print(f"      -> {feed_path}")

    # --- Step 3: Validate ---
    print("\n[3/4] Validating against JSON Schema...")
    import jsonschema

    schema_path = project_root / "spec" / "schemas" / "llmindex-0.1.schema.json"
    schema = json.loads(schema_path.read_text())
    loaded_manifest = json.loads(Path(manifest_path).read_text())

    try:
        jsonschema.validate(loaded_manifest, schema)
        print("      PASSED - Manifest is valid!")
    except jsonschema.ValidationError as e:
        print(f"      FAILED - {e.message}")
        return 1

    # --- Step 4: Summary ---
    print("\n[4/4] Summary")
    print(f"      Site:      {config.name}")
    print(f"      URL:       {config.canonical_url}")
    print(f"      Language:  {config.language}")
    print(f"      Topics:    {', '.join(config.topics)}")
    print(f"      Products:  {len(products)}")
    print(f"      Files:     {2 + len(page_paths)} total")
    print()

    # Show the generated manifest
    print("-" * 60)
    print("Generated /.well-known/llmindex.json:")
    print("-" * 60)
    print(json.dumps(loaded_manifest, indent=2))
    print()

    # Show first 3 lines of feed
    print("-" * 60)
    print("First 3 lines of products.jsonl:")
    print("-" * 60)
    feed_content = Path(feed_path).read_text().strip().split("\n")
    for line in feed_content[:3]:
        obj = json.loads(line)
        currency = obj.get("currency", "")
        price = obj.get("price", "N/A")
        print(f"  {obj['id']}: {obj['title']} — {currency} {price}")
    print(f"  ... ({len(feed_content)} total)")

    print("\n" + "=" * 60)
    print("Demo complete! Output in: examples/_demo_output/")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
