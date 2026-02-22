"""EdDSA (Ed25519) JWS signing helpers for llmindex manifests."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path


def base64url_encode(raw: bytes) -> str:
    """Base64url encode without padding, per JWS compact rules."""
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def base64url_decode(encoded: str) -> bytes:
    """Base64url decode, accepting missing padding."""
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def canonical_json_bytes(data: dict) -> bytes:
    """Canonical JSON bytes for signing: sorted keys, no extra whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def _jws_header_b64() -> str:
    header = {"alg": "EdDSA"}
    header_json = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64url_encode(header_json)


def keygen(output: Path) -> tuple[Path, Path]:
    """Generate an Ed25519 keypair and write PEM files into `output/`."""
    try:
        from cryptography.hazmat.primitives import serialization  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # type: ignore[import-not-found]
            Ed25519PrivateKey,
        )
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "cryptography is required for `llmindex sign`. Install with: pip install 'llmindex[sign]'"
        ) from e

    output.mkdir(parents=True, exist_ok=True)
    private_path = output / "private.pem"
    public_path = output / "public.pem"

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    return private_path, public_path


def sign_manifest(manifest_path: Path, key_path: Path) -> str:
    """Sign a manifest and write `sig` back to disk.

    The JWS compact string is constructed as:
      base64url(header) + "." + base64url(payload_hash) + "." + base64url(signature)

    Where payload_hash is the SHA-256 digest of the canonical JSON (with `sig` removed),
    and the signature is Ed25519 over the JWS signing input: "<header>.<payload>".
    """
    try:
        from cryptography.hazmat.primitives import serialization  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # type: ignore[import-not-found]
            Ed25519PrivateKey,
        )
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "cryptography is required for `llmindex sign`. Install with: pip install 'llmindex[sign]'"
        ) from e

    manifest = _load_manifest(manifest_path)

    unsigned = dict(manifest)
    unsigned.pop("sig", None)

    canonical = canonical_json_bytes(unsigned)
    payload_hash = hashlib.sha256(canonical).digest()

    header_b64 = _jws_header_b64()
    payload_b64 = base64url_encode(payload_hash)

    try:
        private_key_obj = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Signing key not found: {key_path}") from e
    except ValueError as e:
        raise ValueError(f"Invalid private key PEM: {key_path}") from e

    if not isinstance(private_key_obj, Ed25519PrivateKey):
        raise ValueError("Signing key must be an Ed25519 private key (PEM).")

    signature = private_key_obj.sign(canonical)
    signature_b64 = base64url_encode(signature)
    jws = f"{header_b64}.{payload_b64}.{signature_b64}"

    manifest["sig"] = {"alg": "EdDSA", "kid": "local", "jws": jws}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return jws
