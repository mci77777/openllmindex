"""CLI smoke tests for llmindex (Typer app)."""

from __future__ import annotations

import hashlib
import json
import sys
import types
from pathlib import Path

import yaml
from typer.testing import CliRunner

from llmindex.llmindex_cli.main import app


def _challenge_value(url: str) -> str:
    digest = hashlib.sha256(url.rstrip("/").encode("utf-8")).hexdigest()[:32]
    return f"llmindex-verify={digest}"


def test_init_creates_llmindex_yaml():
    runner = CliRunner()
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


def test_generate_uses_yaml_config_no_product_mode():
    runner = CliRunner()
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


def test_generate_requires_site_and_url_without_config():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["generate"])
        assert result.exit_code == 1
        assert "Missing site name" in result.output


def test_status_missing_manifest_is_friendly():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 1
        assert "Run 'llmindex generate' first" in result.output


def test_status_reads_default_dist_manifest():
    runner = CliRunner()
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


def test_verify_dns_outputs_record_name_and_value():
    runner = CliRunner()
    result = runner.invoke(app, ["verify", "dns", "--url", "https://example.com"])
    assert result.exit_code == 0, result.output
    assert "_llmindex-challenge.example.com" in result.output
    assert "llmindex-verify=" in result.output


def test_verify_http_outputs_proof_path_and_content():
    runner = CliRunner()
    result = runner.invoke(app, ["verify", "http", "--url", "https://example.com"])
    assert result.exit_code == 0, result.output
    assert "/.well-known/llmindex-proof.txt" in result.output
    assert "llmindex-verify=" in result.output


def test_verify_check_dns_success_with_stub_dnspython(monkeypatch):
    expected = _challenge_value("https://example.com")

    class _Rdata:
        def __init__(self, strings: list[bytes]):
            self.strings = strings

    def _resolve(name: str, record_type: str):
        assert record_type == "TXT"
        assert name == "_llmindex-challenge.example.com"
        return [_Rdata([expected.encode("utf-8")])]

    dns_module = types.ModuleType("dns")
    resolver_module = types.ModuleType("dns.resolver")
    resolver_module.resolve = _resolve  # type: ignore[attr-defined]
    dns_module.resolver = resolver_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "dns", dns_module)
    monkeypatch.setitem(sys.modules, "dns.resolver", resolver_module)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "verify",
            "check",
            "--method",
            "dns",
            "--url",
            "https://example.com",
            "--value",
            expected,
        ],
    )
    assert result.exit_code == 0, result.output
    assert "DNS TXT record contains expected value" in result.output


def test_verify_check_http_success_with_stub_httpx(monkeypatch):
    expected = _challenge_value("https://example.com")

    class _Response:
        def __init__(self, status_code: int, text: str = ""):
            self.status_code = status_code
            self.text = text

    class HTTPError(Exception):
        pass

    def head(url: str, follow_redirects: bool = True, timeout: float = 5.0):
        assert url == "https://example.com/.well-known/llmindex-proof.txt"
        return _Response(200)

    def get(url: str, follow_redirects: bool = True, timeout: float = 5.0):
        assert url == "https://example.com/.well-known/llmindex-proof.txt"
        return _Response(200, text=expected)

    httpx_module = types.ModuleType("httpx")
    httpx_module.HTTPError = HTTPError  # type: ignore[attr-defined]
    httpx_module.head = head  # type: ignore[attr-defined]
    httpx_module.get = get  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "httpx", httpx_module)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "verify",
            "check",
            "--method",
            "http",
            "--url",
            "https://example.com",
            "--value",
            expected,
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Proof file content matches expected value" in result.output


def test_validate_check_urls_with_stub_httpx(monkeypatch):
    class _Response:
        def __init__(self, status_code: int):
            self.status_code = status_code

    class HTTPError(Exception):
        pass

    class Client:
        def __init__(self, follow_redirects: bool = True, timeout: float = 5.0):
            self.follow_redirects = follow_redirects
            self.timeout = timeout

        def head(self, url: str):
            assert url.startswith("https://example.com/llm/")
            return _Response(200)

        def close(self):
            return None

    httpx_module = types.ModuleType("httpx")
    httpx_module.HTTPError = HTTPError  # type: ignore[attr-defined]
    httpx_module.Client = Client  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "httpx", httpx_module)

    runner = CliRunner()
    with runner.isolated_filesystem():
        manifest_path = Path("llmindex.json")
        manifest_path.write_text(
            json.dumps(
                {
                    "version": "0.1",
                    "updated_at": "2026-02-20T00:00:00Z",
                    "entity": {"name": "Test", "canonical_url": "https://example.com"},
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

        result = runner.invoke(app, ["validate", str(manifest_path), "--check-urls"])
        assert result.exit_code == 0, result.output
        assert "Endpoint URL Reachability" in result.output
