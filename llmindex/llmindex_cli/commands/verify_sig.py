"""EdDSA (Ed25519) JWS verification helpers for llmindex manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import typer

from llmindex.llmindex_cli.commands.sign import base64url_decode, canonical_json_bytes


def _load_manifest(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Manifest not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest: {e}") from e

    if not isinstance(obj, dict):
        raise ValueError("Manifest JSON must be an object at the top level.")
    return obj


def _fail(message: str) -> bool:
    typer.echo(f"FAIL: {message}")
    return False


def verify_signature(manifest_path: Path, key_path: Path) -> bool:
    """Verify a signed manifest using an Ed25519 public key PEM."""
    try:
        from cryptography.hazmat.primitives import serialization  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # type: ignore[import-not-found]
            Ed25519PublicKey,
        )
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "cryptography is required for `llmindex sign verify`. "
            "Install with: pip install 'llmindex[sign]'"
        ) from e

    manifest = _load_manifest(manifest_path)
    sig = manifest.get("sig")
    if not isinstance(sig, dict):
        return _fail("manifest is missing `sig` field")

    jws = sig.get("jws")
    if not isinstance(jws, str) or not jws.strip():
        return _fail("`sig.jws` is missing or empty")

    parts = jws.split(".")
    if len(parts) != 3:
        return _fail("`sig.jws` is not a valid JWS compact string (expected 3 parts)")

    header_b64, payload_b64, signature_b64 = parts

    try:
        header_json = base64url_decode(header_b64).decode("utf-8")
        header = json.loads(header_json)
    except Exception:
        return _fail("JWS header is not valid base64url JSON")

    if not isinstance(header, dict) or header.get("alg") != "EdDSA":
        return _fail("JWS header alg is not EdDSA")

    unsigned = dict(manifest)
    unsigned.pop("sig", None)
    canonical = canonical_json_bytes(unsigned)
    expected_hash = hashlib.sha256(canonical).digest()

    try:
        payload_hash = base64url_decode(payload_b64)
    except Exception:
        return _fail("JWS payload is not valid base64url")

    if payload_hash != expected_hash:
        return _fail("payload hash mismatch (manifest content changed since signing)")

    try:
        signature = base64url_decode(signature_b64)
    except Exception:
        return _fail("JWS signature is not valid base64url")

    try:
        public_key_obj = serialization.load_pem_public_key(key_path.read_bytes())
    except FileNotFoundError:
        return _fail(f"public key not found: {key_path}")
    except ValueError:
        return _fail(f"invalid public key PEM: {key_path}")

    if not isinstance(public_key_obj, Ed25519PublicKey):
        return _fail("public key must be an Ed25519 public key (PEM)")

    try:
        public_key_obj.verify(signature, canonical)
    except Exception:
        return _fail("signature verification failed (wrong key or tampered JWS)")

    kid = sig.get("kid")
    kid_msg = f" kid={kid}" if isinstance(kid, str) and kid.strip() else ""
    typer.echo(f"PASS: signature valid.{kid_msg}")
    return True
