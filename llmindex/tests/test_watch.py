"""Tests for llmindex watch command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from llmindex.llmindex_cli.commands.watch import (
    build_artifacts,
    collect_watch_paths,
)
from llmindex.llmindex_cli.config import ConfigError


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create a minimal llmindex.yaml config in tmp_path."""
    config = {
        "site_name": "TestSite",
        "base_url": "https://example.com",
        "language": "en",
        "topics": ["general"],
    }
    config_path = tmp_path / "llmindex.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return tmp_path


@pytest.fixture
def config_with_csv(config_dir: Path) -> Path:
    """Config dir with a products.csv file."""
    csv_path = config_dir / "products.csv"
    csv_path.write_text(
        "id,title,url,availability,updated_at\n"
        'P001,Widget,https://example.com/widget,in_stock,2026-01-01T00:00:00Z\n',
        encoding="utf-8",
    )
    return config_dir


@pytest.fixture
def config_with_json(config_dir: Path) -> Path:
    """Config dir with a products.json file."""
    json_path = config_dir / "products.json"
    json_path.write_text(
        json.dumps([
            {
                "id": "P001",
                "title": "Widget",
                "url": "https://example.com/widget",
                "availability": "in_stock",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]),
        encoding="utf-8",
    )
    return config_dir


class TestBuildArtifacts:
    """Test the shared build_artifacts function."""

    def test_build_no_products(self, config_dir: Path, tmp_path: Path):
        output_dir = tmp_path / "dist"
        config_path = config_dir / "llmindex.yaml"
        written = build_artifacts(config_path, output_dir)
        # Manifest + 4 pages (products, policies, faq, about) = 5 files
        assert len(written) == 5
        manifest_path = output_dir / ".well-known" / "llmindex.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["entity"]["name"] == "TestSite"
        assert data["entity"]["canonical_url"] == "https://example.com"

    def test_build_with_csv(self, config_with_csv: Path, tmp_path: Path):
        output_dir = tmp_path / "dist"
        config_path = config_with_csv / "llmindex.yaml"
        written = build_artifacts(config_path, output_dir)
        # Manifest + 4 pages + 1 feed = 6 files
        assert len(written) == 6
        feed_path = output_dir / "llm" / "feed" / "products.jsonl"
        assert feed_path.exists()
        lines = feed_path.read_text().strip().split("\n")
        assert len(lines) == 1
        product = json.loads(lines[0])
        assert product["id"] == "P001"

    def test_build_with_json(self, config_with_json: Path, tmp_path: Path):
        output_dir = tmp_path / "dist"
        config_path = config_with_json / "llmindex.yaml"
        written = build_artifacts(config_path, output_dir)
        assert len(written) == 6
        feed_path = output_dir / "llm" / "feed" / "products.jsonl"
        assert feed_path.exists()

    def test_build_with_explicit_csv(self, config_dir: Path, tmp_path: Path):
        output_dir = tmp_path / "dist"
        csv_path = tmp_path / "custom_products.csv"
        csv_path.write_text(
            "id,title,url,availability,updated_at\n"
            'P002,Gadget,https://example.com/gadget,in_stock,2026-01-01T00:00:00Z\n',
            encoding="utf-8",
        )
        config_path = config_dir / "llmindex.yaml"
        written = build_artifacts(config_path, output_dir, input_csv=csv_path)
        assert len(written) == 6

    def test_build_missing_site_name(self, tmp_path: Path):
        config_path = tmp_path / "llmindex.yaml"
        config_path.write_text(yaml.safe_dump({"base_url": "https://example.com"}))
        with pytest.raises(ConfigError, match="Missing site_name"):
            build_artifacts(config_path, tmp_path / "dist")

    def test_build_missing_base_url(self, tmp_path: Path):
        config_path = tmp_path / "llmindex.yaml"
        config_path.write_text(yaml.safe_dump({"site_name": "TestSite"}))
        with pytest.raises(ConfigError, match="Missing base_url"):
            build_artifacts(config_path, tmp_path / "dist")

    def test_build_invalid_config(self, tmp_path: Path):
        config_path = tmp_path / "llmindex.yaml"
        config_path.write_text("not: a\nvalid: []config", encoding="utf-8")
        with pytest.raises(ConfigError):
            build_artifacts(config_path, tmp_path / "dist")


class TestCollectWatchPaths:
    """Test watch path discovery."""

    def test_includes_config_file(self, config_dir: Path):
        config_path = config_dir / "llmindex.yaml"
        paths = collect_watch_paths(config_path)
        assert config_path.resolve() in paths

    def test_includes_csv_source(self, config_with_csv: Path):
        config_path = config_with_csv / "llmindex.yaml"
        csv_path = config_with_csv / "products.csv"
        paths = collect_watch_paths(config_path)
        assert csv_path.resolve() in paths

    def test_includes_json_source(self, config_with_json: Path):
        config_path = config_with_json / "llmindex.yaml"
        json_path = config_with_json / "products.json"
        paths = collect_watch_paths(config_path)
        assert json_path.resolve() in paths

    def test_includes_template_files(self, config_dir: Path):
        template = config_dir / "policies.md.j2"
        template.write_text("# {{ config.name }}", encoding="utf-8")
        config_path = config_dir / "llmindex.yaml"
        paths = collect_watch_paths(config_path)
        assert template.resolve() in paths

    def test_no_product_source_returns_only_config(self, config_dir: Path):
        config_path = config_dir / "llmindex.yaml"
        paths = collect_watch_paths(config_path)
        assert len(paths) == 1
        assert paths[0] == config_path.resolve()


class TestWatchfilesImport:
    """Test graceful handling when watchfiles is not installed."""

    def test_run_watch_raises_without_watchfiles(self, config_dir: Path, tmp_path: Path):
        from llmindex.llmindex_cli.commands.watch import run_watch

        config_path = config_dir / "llmindex.yaml"
        with patch.dict("sys.modules", {"watchfiles": None}):
            with pytest.raises(ModuleNotFoundError, match="watchfiles"):
                run_watch(config_path, tmp_path / "dist")
