"""Tests for CSV importer."""

from pathlib import Path

import pytest

from cli.importers.csv_importer import import_csv

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sample.csv"


class TestCSVImporter:
    def test_import_sample_csv(self):
        products = import_csv(SAMPLE_CSV)
        assert len(products) == 20

    def test_product_fields(self):
        products = import_csv(SAMPLE_CSV)
        p = products[0]
        assert p.id == "P001"
        assert p.title == "Trail Runner Pro"
        assert p.url.startswith("https://")
        assert p.price == 129.99
        assert p.currency == "USD"
        assert p.availability == "in_stock"
        assert p.brand == "ACME"
        assert p.category == "Footwear"

    def test_out_of_stock(self):
        products = import_csv(SAMPLE_CSV)
        tent = next(p for p in products if p.id == "P006")
        assert tent.availability == "out_of_stock"

    def test_preorder(self):
        products = import_csv(SAMPLE_CSV)
        solar = next(p for p in products if p.id == "P010")
        assert solar.availability == "preorder"

    def test_all_have_required_fields(self):
        products = import_csv(SAMPLE_CSV)
        for p in products:
            assert p.id
            assert p.title
            assert p.url
            assert p.availability in ("in_stock", "out_of_stock", "preorder")
            assert p.updated_at

    def test_empty_csv(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("id,title,url,price,currency,availability,updated_at\n")
        products = import_csv(csv_file)
        assert products == []

    def test_malformed_row_skipped(self, tmp_path):
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(
            "id,title,url,price,currency,availability,updated_at\n"
            "P001,Good Product,https://example.com/p1,10.00,USD,in_stock,2026-01-01T00:00:00Z\n"
            ",,,,,,\n"  # empty row
        )
        products = import_csv(csv_file)
        assert len(products) >= 1  # at least the good row
