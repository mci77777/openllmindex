"""Unit tests for llmindex signature verification."""

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


def test_verify_valid_signature(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".well-known" / "llmindex.json"
    _write_minimal_manifest(manifest_path)

    private_path, public_path = keygen(tmp_path / "keys")
    sign_manifest(manifest_path, private_path)

    assert verify_signature(manifest_path, public_path) is True


def test_verify_tampered_manifest_fails(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".well-known" / "llmindex.json"
    _write_minimal_manifest(manifest_path)

    private_path, public_path = keygen(tmp_path / "keys")
    sign_manifest(manifest_path, private_path)

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["topics"] = ["tampered"]
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    assert verify_signature(manifest_path, public_path) is False


def test_verify_missing_sig_fails(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".well-known" / "llmindex.json"
    _write_minimal_manifest(manifest_path)

    _private_path, public_path = keygen(tmp_path / "keys")

    assert verify_signature(manifest_path, public_path) is False


def test_verify_wrong_key_fails(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".well-known" / "llmindex.json"
    _write_minimal_manifest(manifest_path)

    private_path_1, _public_path_1 = keygen(tmp_path / "keys1")
    _private_path_2, public_path_2 = keygen(tmp_path / "keys2")

    sign_manifest(manifest_path, private_path_1)
    assert verify_signature(manifest_path, public_path_2) is False

