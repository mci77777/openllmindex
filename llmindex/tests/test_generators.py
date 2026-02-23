"""Tests for the generator output pipeline."""

import json
from pathlib import Path

import jsonschema
import pytest

from llmindex.importers.csv_importer import import_csv
from llmindex.llmindex_cli.generators.feed import generate_feed, write_feed
from llmindex.llmindex_cli.generators.manifest import generate_manifest, write_manifest
from llmindex.llmindex_cli.generators.pages import write_pages
from llmindex.llmindex_cli.models import SiteConfig

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sample.csv"
SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent / "spec" / "schemas" / "llmindex-0.2.schema.json"
)


@pytest.fixture
def config():
    return SiteConfig(
        name="Test Store",
        canonical_url="https://test-store.com",
        language="en",
        topics=["test", "outdoor"],
    )


@pytest.fixture
def products():
    return import_csv(SAMPLE_CSV)


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


class TestManifestGenerator:
    def test_generates_valid_manifest(self, config, schema):
        manifest = generate_manifest(config)
        jsonschema.validate(manifest, schema)

    def test_manifest_fields(self, config):
        manifest = generate_manifest(config)
        assert manifest["version"] == "0.2"
        assert manifest["entity"]["name"] == "Test Store"
        assert manifest["entity"]["canonical_url"] == "https://test-store.com"
        assert manifest["language"] == "en"
        assert manifest["languages"] == ["en"]
        assert manifest["topics"] == ["test", "outdoor"]
        assert "products" in manifest["endpoints"]
        assert "feeds" in manifest
        assert "feed_updated_at" in manifest

    def test_manifest_without_feed(self, config):
        manifest = generate_manifest(config, has_feed=False)
        assert "feeds" not in manifest

    def test_endpoint_urls(self, config):
        manifest = generate_manifest(config)
        base = "https://test-store.com"
        assert manifest["endpoints"]["products"] == f"{base}/llm/products"
        assert manifest["endpoints"]["policies"] == f"{base}/llm/policies"
        assert manifest["endpoints"]["faq"] == f"{base}/llm/faq"
        assert manifest["endpoints"]["about"] == f"{base}/llm/about"

    def test_write_manifest(self, config, tmp_path):
        manifest = generate_manifest(config)
        out_path = str(tmp_path / ".well-known" / "llmindex.json")
        write_manifest(manifest, out_path)
        loaded = json.loads(Path(out_path).read_text())
        assert loaded["version"] == "0.2"


class TestFeedGenerator:
    def test_generates_jsonl(self, products):
        content = generate_feed(products)
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 20

    def test_each_line_valid_json(self, products):
        content = generate_feed(products)
        for line in content.strip().split("\n"):
            if line:
                obj = json.loads(line)
                assert "id" in obj
                assert "title" in obj
                assert "url" in obj
                assert "availability" in obj

    def test_write_feed(self, products, tmp_path):
        path = write_feed(products, str(tmp_path))
        assert Path(path).exists()
        lines = Path(path).read_text().strip().split("\n")
        assert len(lines) == 20

    def test_empty_products(self):
        content = generate_feed([])
        assert content == ""


class TestPagesGenerator:
    def test_writes_four_pages(self, products, config, tmp_path):
        paths = write_pages(products, config, str(tmp_path))
        assert len(paths) == 4
        for p in paths:
            assert Path(p).exists()

    def test_products_page_has_content(self, products, config, tmp_path):
        write_pages(products, config, str(tmp_path))
        content = (tmp_path / "llm" / "products.md").read_text()
        assert "Trail Runner Pro" in content
        assert "## Footwear" in content

    def test_policies_page(self, products, config, tmp_path):
        write_pages(products, config, str(tmp_path))
        content = (tmp_path / "llm" / "policies.md").read_text()
        assert "Shipping" in content
        assert "Return" in content

    def test_about_page_has_site_name(self, products, config, tmp_path):
        write_pages(products, config, str(tmp_path))
        content = (tmp_path / "llm" / "about.md").read_text()
        assert "Test Store" in content


class TestEndToEnd:
    """Integration test: CSV → generate all artifacts → validate manifest against schema."""

    def test_full_pipeline(self, config, products, schema, tmp_path):
        # Generate manifest
        manifest = generate_manifest(config)
        manifest_path = str(tmp_path / ".well-known" / "llmindex.json")
        write_manifest(manifest, manifest_path)

        # Generate pages
        page_paths = write_pages(products, config, str(tmp_path))

        # Generate feed
        feed_path = write_feed(products, str(tmp_path))

        # Verify manifest validates
        loaded = json.loads(Path(manifest_path).read_text())
        jsonschema.validate(loaded, schema)

        # Verify all files exist
        assert Path(manifest_path).exists()
        assert len(page_paths) == 4
        assert Path(feed_path).exists()

        # Verify feed line count
        feed_lines = Path(feed_path).read_text().strip().split("\n")
        assert len(feed_lines) == 20
