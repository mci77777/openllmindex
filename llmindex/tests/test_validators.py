"""Tests for the llmindex validator module."""

import json
from pathlib import Path

import pytest

from llmindex.llmindex_cli.validators import validate_all, validate_feed, validate_manifest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "spec" / "examples"
TEST_VECTORS_DIR = PROJECT_ROOT / "spec" / "test-vectors"


class TestManifestValidation:
    """Test manifest validation against schema."""

    @pytest.mark.parametrize(
        "industry", ["ecommerce", "local-business", "saas", "blog", "restaurant", "marketplace"]
    )
    def test_valid_examples_pass(self, industry):
        path = EXAMPLES_DIR / industry / "llmindex.json"
        result = validate_manifest(path)
        assert result.valid, f"Errors: {result.errors}"

    def test_missing_file(self):
        result = validate_manifest("/nonexistent/path.json")
        assert not result.valid
        assert any("not found" in e for e in result.errors)

    def test_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        result = validate_manifest(bad)
        assert not result.valid
        assert any("Invalid JSON" in e for e in result.errors)

    def test_missing_required_fields(self):
        path = TEST_VECTORS_DIR / "invalid-missing-required.json"
        result = validate_manifest(path)
        assert not result.valid
        assert len(result.errors) > 0

    def test_bad_urls_rejected(self):
        path = TEST_VECTORS_DIR / "invalid-bad-urls.json"
        result = validate_manifest(path)
        assert not result.valid

    def test_bad_dates_rejected(self):
        path = TEST_VECTORS_DIR / "invalid-bad-dates.json"
        result = validate_manifest(path)
        assert not result.valid

    def test_extra_fields_rejected(self):
        path = TEST_VECTORS_DIR / "invalid-extra-fields.json"
        result = validate_manifest(path)
        assert not result.valid

    def test_http_canonical_url_rejected(self):
        path = TEST_VECTORS_DIR / "invalid-http-url.json"
        result = validate_manifest(path)
        assert not result.valid

    def test_domain_mismatch_warning(self, tmp_path):
        manifest = {
            "version": "0.1",
            "updated_at": "2026-02-20T00:00:00Z",
            "entity": {"name": "Test", "canonical_url": "https://example.com"},
            "language": "en",
            "topics": ["test"],
            "endpoints": {
                "products": "https://other-domain.com/llm/products",
                "policies": "https://example.com/llm/policies",
                "faq": "https://example.com/llm/faq",
                "about": "https://example.com/llm/about",
            },
        }
        path = tmp_path / "llmindex.json"
        path.write_text(json.dumps(manifest))
        result = validate_manifest(path)
        assert result.valid  # Warnings don't fail validation
        assert any("differs from canonical" in w for w in result.warnings)


class TestFeedValidation:
    """Test products.jsonl feed validation."""

    def test_valid_feed(self):
        path = EXAMPLES_DIR / "ecommerce" / "feed" / "products.jsonl"
        result = validate_feed(path)
        assert result.valid, f"Errors: {result.errors}"

    def test_invalid_feed(self):
        path = TEST_VECTORS_DIR / "invalid-feed.jsonl"
        result = validate_feed(path)
        assert not result.valid

    def test_missing_feed_file(self):
        result = validate_feed("/nonexistent/feed.jsonl")
        assert not result.valid

    def test_empty_feed(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        result = validate_feed(path)
        assert not result.valid
        assert any("empty" in e.lower() for e in result.errors)

    def test_feed_missing_required_fields(self, tmp_path):
        path = tmp_path / "bad.jsonl"
        path.write_text('{"id": "1"}\n')  # Missing title, url, availability, updated_at
        result = validate_feed(path)
        assert not result.valid


class TestValidateAll:
    """Test combined manifest + feed validation."""

    def test_ecommerce_full_validation(self):
        manifest = EXAMPLES_DIR / "ecommerce" / "llmindex.json"
        feed = EXAMPLES_DIR / "ecommerce" / "feed" / "products.jsonl"
        result = validate_all(manifest, feed)
        assert result.valid, f"Errors: {result.errors}"

    def test_manifest_only(self):
        manifest = EXAMPLES_DIR / "local-business" / "llmindex.json"
        result = validate_all(manifest)
        assert result.valid, f"Errors: {result.errors}"

    def test_path_does_not_exist_returns_invalid(self):
        result = validate_all("/nonexistent/manifest.json")
        assert not result.valid
        assert result.errors
        assert any("File not found" in e for e in result.errors)

    def test_multiple_errors_aggregated(self, tmp_path):
        manifest = {
            "version": "0.1",
            "updated_at": "2026-02-20T00:00:00Z",
            "entity": {"name": "Test", "canonical_url": "https://example.com"},
            "language": "en",
            "topics": [],
            "endpoints": {"products": "https://example.com/llm/products"},
        }
        manifest_path = tmp_path / "bad.json"
        manifest_path.write_text(json.dumps(manifest))

        missing_feed = tmp_path / "missing.jsonl"
        result = validate_all(manifest_path, missing_feed)

        assert not result.valid
        assert any("File not found" in e for e in result.errors)
        assert sum(e.startswith("Schema:") for e in result.errors) >= 2
