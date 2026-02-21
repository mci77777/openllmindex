"""CLI integration tests for llmindex (Typer app)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from llmindex.llmindex_cli.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_CSV = PROJECT_ROOT / "llmindex" / "sample_data" / "sample.csv"
SAMPLE_JSON = PROJECT_ROOT / "llmindex" / "sample_data" / "sample.json"
ECOMMERCE_MANIFEST = PROJECT_ROOT / "spec" / "examples" / "ecommerce" / "llmindex.json"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCLIVersion:
    def test_version_contains_llmindex(self, runner: CliRunner):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0, result.output
        assert "llmindex" in result.output.lower()


class TestCLIGenerate:
    def test_generate_happy_path_input_csv(self, runner: CliRunner, tmp_path: Path):
        output_dir = tmp_path / "dist"
        result = runner.invoke(
            app,
            [
                "generate",
                "--site",
                "CLI Test Store",
                "--url",
                "https://example.com",
                "--input-csv",
                str(SAMPLE_CSV),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Imported: 20 products" in result.output

        assert (output_dir / ".well-known" / "llmindex.json").exists()
        assert (output_dir / "llm" / "products.md").exists()
        assert (output_dir / "llm" / "policies.md").exists()
        assert (output_dir / "llm" / "faq.md").exists()
        assert (output_dir / "llm" / "about.md").exists()
        assert (output_dir / "llm" / "feed" / "products.jsonl").exists()

    def test_generate_missing_required_args(self, runner: CliRunner):
        result = runner.invoke(app, ["generate", "--input-csv", str(SAMPLE_CSV)])
        assert result.exit_code == 1
        assert "Missing site name" in result.output

    def test_generate_rejects_non_https_url(self, runner: CliRunner, tmp_path: Path):
        result = runner.invoke(
            app,
            [
                "generate",
                "--site",
                "CLI Test Store",
                "--url",
                "http://example.com",
                "--input-csv",
                str(SAMPLE_CSV),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )
        assert result.exit_code == 1
        assert "--url must be an HTTPS URL" in result.output

    def test_generate_rejects_nonexistent_input_file(self, runner: CliRunner, tmp_path: Path):
        missing = tmp_path / "missing.csv"
        result = runner.invoke(
            app,
            [
                "generate",
                "--site",
                "CLI Test Store",
                "--url",
                "https://example.com",
                "--input-csv",
                str(missing),
            ],
        )
        assert result.exit_code == 1
        assert "Input file not found" in result.output

    def test_generate_rejects_multiple_inputs(self, runner: CliRunner, tmp_path: Path):
        result = runner.invoke(
            app,
            [
                "generate",
                "--site",
                "CLI Test Store",
                "--url",
                "https://example.com",
                "--input-csv",
                str(SAMPLE_CSV),
                "--input-json",
                str(SAMPLE_JSON),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )
        assert result.exit_code == 1
        assert "Provide only one input source" in result.output

    def test_generate_uses_yaml_config_no_product_mode(self, runner: CliRunner):
        with runner.isolated_filesystem():
            Path("llmindex.yaml").write_text(
                yaml.safe_dump(
                    {
                        "site_name": "My Site",
                        "base_url": "https://example.com",
                        "language": "zh-CN",
                        "topics": ["foo"],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            result = runner.invoke(
                app, ["generate", "--config", "llmindex.yaml", "--output-dir", "out"]
            )
            assert result.exit_code == 0, result.output

            manifest_path = Path("out") / ".well-known" / "llmindex.json"
            assert manifest_path.exists()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert manifest["entity"]["name"] == "My Site"
            assert "feeds" not in manifest

            assert (Path("out") / "llm" / "products.md").exists()
            assert (Path("out") / "llm" / "policies.md").exists()
            assert (Path("out") / "llm" / "faq.md").exists()
            assert (Path("out") / "llm" / "about.md").exists()
            assert not (Path("out") / "llm" / "feed" / "products.jsonl").exists()

    @pytest.mark.skipif(
        importlib.util.find_spec("jinja2") is not None,
        reason="jinja2 installed; this test expects it to be missing in dev env",
    )
    def test_generate_templates_dir_requires_jinja2(self, runner: CliRunner, tmp_path: Path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        result = runner.invoke(
            app,
            [
                "generate",
                "--site",
                "CLI Test Store",
                "--url",
                "https://example.com",
                "--input-csv",
                str(SAMPLE_CSV),
                "--templates-dir",
                str(templates_dir),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )
        assert result.exit_code == 1
        assert "Jinja2 is required for --templates-dir" in result.output


class TestCLIValidate:
    def test_validate_happy_path_ecommerce_example(self, runner: CliRunner):
        result = runner.invoke(app, ["validate", str(ECOMMERCE_MANIFEST)])
        assert result.exit_code == 0, result.output
        assert "Valid!" in result.output

    def test_validate_nonexistent_manifest(self, runner: CliRunner, tmp_path: Path):
        result = runner.invoke(app, ["validate", str(tmp_path / "missing.json")])
        assert result.exit_code == 1
        assert "File not found" in result.output

    @pytest.mark.skipif(
        importlib.util.find_spec("httpx") is not None,
        reason="httpx installed; this test expects it to be missing in dev env",
    )
    def test_validate_check_urls_missing_httpx(self, runner: CliRunner):
        result = runner.invoke(
            app,
            [
                "validate",
                str(ECOMMERCE_MANIFEST),
                "--check-urls",
            ],
        )
        assert result.exit_code == 1
        assert "httpx is required for --check-urls" in result.output


class TestCLIInitAndStatus:
    def test_init_creates_llmindex_yaml(self, runner: CliRunner):
        with runner.isolated_filesystem():
            result = runner.invoke(
                app,
                ["init"],
                input="My Site\nhttps://example.com\n\nfoo,bar\n",
            )
            assert result.exit_code == 0, result.output
            cfg = Path("llmindex.yaml")
            assert cfg.exists()

            data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
            assert data["site_name"] == "My Site"
            assert data["base_url"] == "https://example.com"
            assert data["language"] == "zh-CN"
            assert data["topics"] == ["foo", "bar"]

    def test_init_does_not_overwrite_existing_config_by_default(self, runner: CliRunner):
        with runner.isolated_filesystem():
            Path("llmindex.yaml").write_text("site_name: Existing\n", encoding="utf-8")
            result = runner.invoke(app, ["init"], input="\n")
            assert result.exit_code == 0, result.output
            assert "Aborted" in result.output

    def test_status_missing_manifest_is_friendly(self, runner: CliRunner):
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 1
            assert "Run 'llmindex generate' first" in result.output

    def test_status_reads_default_dist_manifest(self, runner: CliRunner):
        with runner.isolated_filesystem():
            manifest_path = Path("dist") / ".well-known" / "llmindex.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": "0.1",
                        "updated_at": "2026-02-20T00:00:00Z",
                        "entity": {"name": "Test Site", "canonical_url": "https://example.com"},
                        "language": "en",
                        "topics": ["test"],
                        "endpoints": {
                            "products": "https://example.com/llm/products",
                            "policies": "https://example.com/llm/policies",
                            "faq": "https://example.com/llm/faq",
                            "about": "https://example.com/llm/about",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0, result.output
            assert "Test Site" in result.output

    def test_status_rejects_invalid_json_manifest(self, runner: CliRunner):
        with runner.isolated_filesystem():
            manifest_path = Path("dist") / ".well-known" / "llmindex.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text("{not valid json", encoding="utf-8")

            result = runner.invoke(app, ["status"])
            assert result.exit_code == 1
            assert "Invalid JSON" in result.output


class TestCLIVerify:
    def test_verify_dns_outputs_record_name_and_value(self, runner: CliRunner):
        result = runner.invoke(app, ["verify", "dns", "--url", "https://example.com"])
        assert result.exit_code == 0, result.output
        assert "_llmindex-challenge.example.com" in result.output
        assert "llmindex-verify=" in result.output

    def test_verify_http_outputs_proof_path_and_content(self, runner: CliRunner):
        result = runner.invoke(app, ["verify", "http", "--url", "https://example.com"])
        assert result.exit_code == 0, result.output
        assert "/.well-known/llmindex-proof.txt" in result.output
        assert "llmindex-verify=" in result.output

    def test_verify_dns_uses_llmindex_yaml_when_url_omitted(self, runner: CliRunner):
        with runner.isolated_filesystem():
            Path("llmindex.yaml").write_text(
                yaml.safe_dump({"base_url": "https://example.com"}, sort_keys=False),
                encoding="utf-8",
            )
            result = runner.invoke(app, ["verify", "dns"])
            assert result.exit_code == 0, result.output
            assert "_llmindex-challenge.example.com" in result.output

    def test_verify_check_rejects_invalid_method(self, runner: CliRunner):
        result = runner.invoke(
            app, ["verify", "check", "--method", "nope", "--url", "https://x.com"]
        )
        assert result.exit_code == 1
        assert "--method must be one of: dns, http" in result.output

    @pytest.mark.skipif(
        importlib.util.find_spec("dns") is not None,
        reason="dnspython installed; this test expects it to be missing in dev env",
    )
    def test_verify_check_dns_requires_dnspython(self, runner: CliRunner):
        result = runner.invoke(
            app,
            ["verify", "check", "--method", "dns", "--url", "https://example.com"],
        )
        assert result.exit_code == 1
        assert "dnspython is required for DNS checks" in result.output

    @pytest.mark.skipif(
        importlib.util.find_spec("httpx") is not None,
        reason="httpx installed; this test expects it to be missing in dev env",
    )
    def test_verify_check_http_requires_httpx(self, runner: CliRunner):
        result = runner.invoke(
            app,
            ["verify", "check", "--method", "http", "--url", "https://example.com"],
        )
        assert result.exit_code == 1
        assert "httpx is required for HTTP checks" in result.output
