"""
Demo test — verifies the example workflow runs end-to-end.

Run with: pytest examples/test_demo.py -v
"""

import json
from pathlib import Path

import jsonschema
import pytest

from llmindex.importers.csv_importer import import_csv
from llmindex.llmindex_cli.generators.feed import write_feed
from llmindex.llmindex_cli.generators.manifest import generate_manifest, write_manifest
from llmindex.llmindex_cli.generators.pages import write_pages
from llmindex.llmindex_cli.models import SiteConfig

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = PROJECT_ROOT / "llmindex" / "sample_data" / "sample.csv"
SCHEMA_PATH = PROJECT_ROOT / "spec" / "schemas" / "llmindex-0.1.schema.json"


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "demo_output"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


class TestDemoWorkflow:
    """Full end-to-end demo: CSV -> generate -> validate."""

    def test_csv_import(self):
        """Step 1: Import 20 products from sample CSV."""
        products = import_csv(SAMPLE_CSV)
        assert len(products) == 20
        assert all(p.id for p in products)
        assert all(p.title for p in products)

    def test_generate_manifest(self, output_dir, schema):
        """Step 2a: Generate manifest that passes schema validation."""
        config = SiteConfig(
            name="Demo Store",
            canonical_url="https://demo.example.com",
            topics=["demo"],
        )
        manifest = generate_manifest(config)
        path = str(output_dir / ".well-known" / "llmindex.json")
        write_manifest(manifest, path)

        loaded = json.loads(Path(path).read_text())
        jsonschema.validate(loaded, schema)  # must not raise

        assert loaded["version"] == "0.1"
        assert loaded["entity"]["name"] == "Demo Store"

    def test_generate_pages(self, output_dir):
        """Step 2b: Generate 4 markdown pages with product content."""
        config = SiteConfig(name="Demo", canonical_url="https://demo.example.com")
        products = import_csv(SAMPLE_CSV)
        paths = write_pages(products, config, str(output_dir))

        assert len(paths) == 4
        for p in paths:
            assert Path(p).exists()
            assert Path(p).stat().st_size > 0

        # Products page should contain actual product data
        products_md = (output_dir / "llm" / "products.md").read_text()
        assert "Trail Runner Pro" in products_md

    def test_generate_feed(self, output_dir):
        """Step 2c: Generate JSONL feed with 20 valid lines."""
        products = import_csv(SAMPLE_CSV)
        path = write_feed(products, str(output_dir))

        lines = Path(path).read_text().strip().split("\n")
        assert len(lines) == 20

        for line in lines:
            obj = json.loads(line)
            assert "id" in obj
            assert "title" in obj
            assert "url" in obj

    def test_full_pipeline(self, output_dir, schema):
        """Step 3: Complete pipeline — import, generate all, validate."""
        config = SiteConfig(
            name="Full Pipeline Store",
            canonical_url="https://pipeline.example.com",
            language="en",
            topics=["test", "demo"],
        )
        products = import_csv(SAMPLE_CSV)

        # Generate all
        manifest = generate_manifest(config)
        manifest_path = str(output_dir / ".well-known" / "llmindex.json")
        write_manifest(manifest, manifest_path)
        page_paths = write_pages(products, config, str(output_dir))
        feed_path = write_feed(products, str(output_dir))

        # Validate manifest
        loaded = json.loads(Path(manifest_path).read_text())
        jsonschema.validate(loaded, schema)

        # Count all output files
        all_files = [manifest_path] + page_paths + [feed_path]
        assert len(all_files) == 6  # 1 manifest + 4 pages + 1 feed

        for f in all_files:
            assert Path(f).exists(), f"Missing: {f}"


class TestSchemaExamplesValidation:
    """Validate all spec examples work as documented in README."""

    @pytest.mark.parametrize("industry", ["ecommerce", "local-business", "saas"])
    def test_readme_examples_valid(self, schema, industry):
        """Each README-listed example must validate against the schema."""
        path = PROJECT_ROOT / "spec" / "examples" / industry / "llmindex.json"
        data = json.loads(path.read_text())
        jsonschema.validate(data, schema)
