"""Unit tests for llmindex signature commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("cryptography")

from llmindex.llmindex_cli.commands.sign import keygen, sign_manifest
from llmindex.llmindex_cli.commands.verify_sig import verify_signature


def _write_minimal_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
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
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_keygen_creates_key_files(tmp_path: Path) -> None:
    keys_dir = tmp_path / "keys"
    private_path, public_path = keygen(keys_dir)

    assert private_path.exists()
    assert public_path.exists()

    assert "BEGIN PRIVATE KEY" in private_path.read_text(encoding="utf-8")
    assert "BEGIN PUBLIC KEY" in public_path.read_text(encoding="utf-8")


def test_sign_manifest_adds_sig_field(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".well-known" / "llmindex.json"
    _write_minimal_manifest(manifest_path)

    private_path, _public_path = keygen(tmp_path / "keys")
    jws = sign_manifest(manifest_path, private_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "sig" in manifest
    assert manifest["sig"]["alg"] == "EdDSA"
    assert manifest["sig"]["kid"] == "local"
    assert manifest["sig"]["jws"] == jws


def test_sign_roundtrip_verify(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".well-known" / "llmindex.json"
    _write_minimal_manifest(manifest_path)

    private_path, public_path = keygen(tmp_path / "keys")
    sign_manifest(manifest_path, private_path)

    assert verify_signature(manifest_path, public_path) is True


def test_sign_missing_key_fails(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".well-known" / "llmindex.json"
    _write_minimal_manifest(manifest_path)

    missing_key = tmp_path / "missing-private.pem"
    with pytest.raises(FileNotFoundError):
        sign_manifest(manifest_path, missing_key)
