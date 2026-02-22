"""Tests for the llmindex validator module."""

import json
from datetime import datetime, timedelta, timezone
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


def _make_manifest(tmp_path, **overrides):
    """Helper: create a minimal valid manifest, optionally with overrides."""
    base = {
        "version": "0.1",
        "updated_at": "2026-02-22T00:00:00Z",
        "entity": {"name": "Test Co", "canonical_url": "https://test.com"},
        "language": "en",
        "topics": ["test"],
        "endpoints": {
            "products": "https://test.com/llm/products",
            "policies": "https://test.com/llm/policies",
            "faq": "https://test.com/llm/faq",
            "about": "https://test.com/llm/about",
        },
    }
    base.update(overrides)
    path = tmp_path / "llmindex.json"
    path.write_text(json.dumps(base))
    return path


class TestAccessControlValidation:
    """Test business-logic validation for access_control field."""

    def test_valid_access_control_passes(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            access_control={
                "allow": ["GPTBot", "ClaudeBot"],
                "deny": ["BadBot/1.0"],
                "rate_limit": "1000/day",
                "requires_attribution": True,
                "commercial_use": "allowed",
            },
        )
        result = validate_manifest(path)
        assert result.valid, f"Errors: {result.errors}"
        assert result.warnings == []

    def test_deny_wildcard_produces_warning(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            access_control={"deny": ["*"]},
        )
        result = validate_manifest(path)
        assert result.valid  # Still valid — just a warning
        assert any("deny contains '*'" in w for w in result.warnings)

    def test_allow_deny_overlap_produces_warning(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            access_control={"allow": ["GPTBot", "ClaudeBot"], "deny": ["GPTBot"]},
        )
        result = validate_manifest(path)
        assert result.valid
        assert any("GPTBot" in w and "allow and deny" in w for w in result.warnings)

    def test_contact_required_with_allow_all_warns(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            access_control={"allow": ["*"], "commercial_use": "contact-required"},
        )
        result = validate_manifest(path)
        assert result.valid
        assert any("contact-required" in w for w in result.warnings)

    def test_invalid_commercial_use_value_fails_schema(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            access_control={"commercial_use": "unknown-value"},
        )
        result = validate_manifest(path)
        assert not result.valid
        assert any("access_control" in e or "commercial_use" in e for e in result.errors)

    def test_invalid_rate_limit_format_fails_schema(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            access_control={"rate_limit": "1000-per-day"},  # wrong format
        )
        result = validate_manifest(path)
        assert not result.valid

    def test_no_access_control_is_valid(self, tmp_path):
        path = _make_manifest(tmp_path)
        result = validate_manifest(path)
        assert result.valid
        assert result.warnings == []

    def test_non_commercial_usage_is_valid(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            access_control={"commercial_use": "non-commercial"},
        )
        result = validate_manifest(path)
        assert result.valid
        assert result.warnings == []


class TestLocalizedEndpoints:
    """Test business-logic validation for languages/localized_endpoints/feed_updated_at."""

    def test_valid_v02_manifest_passes(self, tmp_path):
        path = _make_manifest(tmp_path, version="0.2")
        result = validate_manifest(path)
        assert result.valid, f"Errors: {result.errors}"

    def test_v02_with_localized_endpoints_passes(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            version="0.2",
            languages=["en", "zh-CN"],
            localized_endpoints={
                "en": {
                    "products": "https://test.com/llm/products",
                    "policies": "https://test.com/llm/policies",
                    "faq": "https://test.com/llm/faq",
                    "about": "https://test.com/llm/about",
                },
                "zh-CN": {
                    "products": "https://test.com/llm/zh/products",
                    "about": "https://test.com/llm/zh/about",
                },
            },
        )
        result = validate_manifest(path)
        assert result.valid, f"Errors: {result.errors}"
        assert result.warnings == []

    def test_localized_endpoints_without_languages_warns(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            version="0.2",
            localized_endpoints={
                "en": {"products": "https://test.com/llm/products"},
            },
        )
        result = validate_manifest(path)
        assert result.valid
        assert any("languages and localized_endpoints" in w for w in result.warnings)

    def test_localized_endpoints_lang_not_in_languages_warns(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            version="0.2",
            languages=["en"],
            localized_endpoints={
                "en": {"products": "https://test.com/llm/products"},
                "zh-CN": {"products": "https://test.com/llm/zh/products"},
            },
        )
        result = validate_manifest(path)
        assert result.valid
        assert any("not present in languages" in w for w in result.warnings)

    def test_localized_endpoints_domain_mismatch_warns(self, tmp_path):
        path = _make_manifest(
            tmp_path,
            version="0.2",
            entity={"name": "Test Co", "canonical_url": "https://example.com"},
            languages=["en"],
            localized_endpoints={
                "en": {"products": "https://other-domain.com/llm/products"},
            },
        )
        result = validate_manifest(path)
        assert result.valid
        assert any("localized_endpoints" in w and "differs from canonical" in w for w in result.warnings)

    def test_unknown_version_uses_v01_with_warning(self, tmp_path):
        path = _make_manifest(tmp_path, version="0.9")
        result = validate_manifest(path)
        assert result.valid, f"Errors: {result.errors}"
        assert any("Unknown manifest version" in w for w in result.warnings)

    def test_feed_updated_at_stale_warns(self, tmp_path):
        stale = (datetime.now(timezone.utc) - timedelta(days=8)).replace(microsecond=0).isoformat()
        path = _make_manifest(tmp_path, version="0.2", feed_updated_at=stale)
        result = validate_manifest(path)
        assert result.valid, f"Errors: {result.errors}"
        assert any("feed_updated_at is older than 7 days" in w for w in result.warnings)

    def test_feed_updated_at_fresh_no_warning(self, tmp_path):
        fresh = (datetime.now(timezone.utc) - timedelta(days=1)).replace(microsecond=0).isoformat()
        path = _make_manifest(tmp_path, version="0.2", feed_updated_at=fresh)
        result = validate_manifest(path)
        assert result.valid, f"Errors: {result.errors}"
        assert not any("feed_updated_at is older than 7 days" in w for w in result.warnings)
