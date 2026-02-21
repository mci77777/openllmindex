"""Tests for JSON and Shopify CSV importers."""

from pathlib import Path

import pytest

from llmindex.importers.json_importer import import_json
from llmindex.importers.shopify_importer import import_shopify_csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_JSON = PROJECT_ROOT / "llmindex" / "sample_data" / "sample.json"
SAMPLE_SHOPIFY = PROJECT_ROOT / "llmindex" / "sample_data" / "sample_shopify.csv"


class TestJSONImporter:
    """Test JSON array importer."""

    def test_import_sample_json(self):
        products = import_json(SAMPLE_JSON)
        assert len(products) == 3

    def test_product_fields(self):
        products = import_json(SAMPLE_JSON)
        mouse = products[0]
        assert mouse.id == "J001"
        assert mouse.title == "Wireless Mouse"
        assert mouse.price == 29.99
        assert mouse.currency == "USD"

    def test_all_have_required_fields(self):
        products = import_json(SAMPLE_JSON)
        for p in products:
            assert p.id
            assert p.title
            assert p.url
            assert p.availability in ("in_stock", "out_of_stock", "preorder")

    def test_empty_array(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("[]")
        products = import_json(path)
        assert products == []

    def test_invalid_format(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text('{"not": "an array"}')
        with pytest.raises(ValueError, match="Expected JSON array"):
            import_json(path)

    def test_missing_fields_skipped(self, tmp_path):
        path = tmp_path / "partial.json"
        path.write_text('[{"id": "1", "title": "Test", "url": "https://x.com/p"}, {"bad": true}]')
        products = import_json(path)
        # First item should import (availability defaults to in_stock)
        assert len(products) == 1
        assert products[0].id == "1"


class TestShopifyImporter:
    """Test Shopify CSV export importer."""

    def test_import_shopify_csv(self):
        products = import_shopify_csv(SAMPLE_SHOPIFY, base_url="https://myshop.com")
        # 4 unique handles: classic-leather-bag, wool-scarf, draft-item, silk-pillow
        assert len(products) == 4

    def test_deduplicates_variants(self):
        """Shopify exports one row per variant; we take only the first."""
        products = import_shopify_csv(SAMPLE_SHOPIFY, base_url="https://myshop.com")
        handles = [p.url.split("/products/")[-1] for p in products]
        assert len(handles) == len(set(handles)), "Duplicate handles found"

    def test_product_url_construction(self):
        products = import_shopify_csv(SAMPLE_SHOPIFY, base_url="https://myshop.com")
        bag = next(p for p in products if "leather" in p.title.lower())
        assert bag.url == "https://myshop.com/products/classic-leather-bag"

    def test_draft_product_availability(self):
        products = import_shopify_csv(SAMPLE_SHOPIFY, base_url="https://myshop.com")
        draft = next(p for p in products if "draft" in p.id.lower() or "draft" in p.title.lower())
        assert draft.availability == "out_of_stock"

    def test_vendor_mapped_to_brand(self):
        products = import_shopify_csv(SAMPLE_SHOPIFY, base_url="https://myshop.com")
        bag = next(p for p in products if "leather" in p.title.lower())
        assert bag.brand == "ArtisanCo"

    def test_custom_currency(self):
        products = import_shopify_csv(
            SAMPLE_SHOPIFY, base_url="https://myshop.com", currency="EUR"
        )
        for p in products:
            if p.price is not None:
                assert p.currency == "EUR"

    def test_image_url_preserved(self):
        products = import_shopify_csv(SAMPLE_SHOPIFY, base_url="https://myshop.com")
        bag = next(p for p in products if "leather" in p.title.lower())
        assert bag.image_url == "https://cdn.shopify.com/leather-bag.jpg"
