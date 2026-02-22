"""Validators for llmindex manifests and feeds."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import jsonschema

# Schema path relative to project root
_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "spec" / "schemas"


@dataclass
class ValidationResult:
    """Result of a validation run."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def _parse_rfc3339_datetime(value: str) -> datetime | None:
    """Parse an ISO 8601 / RFC 3339 datetime string into an aware UTC datetime."""
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _warn_if_url_hosts_differ(
    result: ValidationResult,
    *,
    canonical_url: str,
    urls: dict[str, object],
    prefix: str,
) -> None:
    expected_host = urlparse(canonical_url).hostname
    if not expected_host:
        return

    for name, url in urls.items():
        if not isinstance(url, str):
            continue
        parsed = urlparse(url)
        if parsed.hostname and parsed.hostname != expected_host:
            result.add_warning(
                f"{prefix}.{name} host ({parsed.hostname}) differs from canonical ({expected_host})"
            )


def validate_manifest(manifest_path: str | Path) -> ValidationResult:
    """Validate a manifest JSON file against the llmindex v0.1/v0.2 schema."""
    result = ValidationResult(valid=True)
    path = Path(manifest_path)

    if not path.exists():
        result.add_error(f"File not found: {path}")
        return result

    # Parse JSON
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON: {e}")
        return result

    # Load schema (based on manifest version)
    schema_filename = "llmindex-0.1.schema.json"
    version = data.get("version") if isinstance(data, dict) else None
    if version == "0.2":
        schema_filename = "llmindex-0.2.schema.json"
    elif version == "0.1":
        schema_filename = "llmindex-0.1.schema.json"
    else:
        schema_filename = "llmindex-0.1.schema.json"
        if isinstance(version, str) and version:
            result.add_warning(
                f"Unknown manifest version '{version}', validating against llmindex v0.1 schema"
            )
        else:
            result.add_warning(
                "Missing or unknown manifest version, validating against llmindex v0.1 schema"
            )

    schema_path = _SCHEMA_DIR / schema_filename
    if not schema_path.exists():
        result.add_error(f"Schema not found: {schema_path}")
        return result

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Validate against schema
    data_for_schema = data
    if isinstance(data, dict) and isinstance(version, str) and version not in {"0.1", "0.2"}:
        data_for_schema = {**data, "version": "0.1"}

    validator = jsonschema.Draft7Validator(schema)
    schema_errors = sorted(
        validator.iter_errors(data_for_schema), key=lambda e: list(e.absolute_path)
    )

    for error in schema_errors:
        field_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        result.add_error(f"Schema: {field_path} — {error.message}")

    # Additional checks beyond schema
    if isinstance(data, dict):
        # Check canonical_url is HTTPS
        canonical = data.get("entity", {}).get("canonical_url", "")
        if canonical and not canonical.startswith("https://"):
            result.add_error(f"entity.canonical_url must be HTTPS, got: {canonical}")

        # Check endpoint URLs match canonical domain
        endpoints = data.get("endpoints", {})
        if canonical and isinstance(endpoints, dict):
            _warn_if_url_hosts_differ(result, canonical_url=canonical, urls=endpoints, prefix="endpoints")

        # Validate access_control business logic
        ac = data.get("access_control")
        if ac and isinstance(ac, dict):
            allow = ac.get("allow", [])
            deny = ac.get("deny", [])
            commercial_use = ac.get("commercial_use")

            # deny=['*'] blocks all agents — flag as a warning
            if "*" in deny:
                result.add_warning(
                    "access_control.deny contains '*' which will block all AI agents"
                )

            # allow/deny overlap: same identifier appears in both lists
            if allow and deny:
                overlap = set(allow) & set(deny)
                # '*' in deny dominates, already warned above; check non-wildcard overlap
                specific_overlap = overlap - {"*"}
                for entry in sorted(specific_overlap):
                    result.add_warning(
                        f"access_control: '{entry}' appears in both allow and deny; "
                        "deny takes precedence"
                    )

            # commercial_use='contact-required' with allow='*' is unusual — add info warning
            if commercial_use == "contact-required" and allow == ["*"]:
                result.add_warning(
                    "access_control.commercial_use is 'contact-required' but allow=['*']; "
                    "consider restricting allow or adding contact information to about page"
                )

        # Validate localized_endpoints business logic
        languages = data.get("languages")
        localized_endpoints = data.get("localized_endpoints")
        has_languages = isinstance(languages, list)
        has_localized_endpoints = isinstance(localized_endpoints, dict)

        if has_languages ^ has_localized_endpoints:
            result.add_warning("languages and localized_endpoints should be provided together")

        if has_languages and has_localized_endpoints:
            language_set = {lang for lang in languages if isinstance(lang, str)}
            for lang, localized in localized_endpoints.items():
                if lang not in language_set:
                    result.add_warning(
                        f"localized_endpoints includes '{lang}' which is not present in languages"
                    )
                if canonical and isinstance(localized, dict):
                    _warn_if_url_hosts_differ(
                        result,
                        canonical_url=canonical,
                        urls=localized,
                        prefix=f"localized_endpoints.{lang}",
                    )

        # Validate feed_updated_at freshness (stale after 7 days)
        feed_updated_at = data.get("feed_updated_at")
        if isinstance(feed_updated_at, str) and feed_updated_at:
            parsed = _parse_rfc3339_datetime(feed_updated_at)
            if parsed:
                age = datetime.now(timezone.utc) - parsed
                if age > timedelta(days=7):
                    result.add_warning("feed_updated_at is older than 7 days")

    return result


def validate_feed(feed_path: str | Path) -> ValidationResult:
    """Validate a products.jsonl feed file line by line."""
    result = ValidationResult(valid=True)
    path = Path(feed_path)

    if not path.exists():
        result.add_error(f"File not found: {path}")
        return result

    # Load product_line schema from definitions
    schema_path = _SCHEMA_DIR / "llmindex-0.1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    product_schema = schema.get("definitions", {}).get("product_line")

    if not product_schema:
        result.add_error("product_line schema not found in definitions")
        return result

    validator = jsonschema.Draft7Validator(product_schema)

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    if not lines or (len(lines) == 1 and not lines[0].strip()):
        result.add_error("Feed file is empty")
        return result

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        # Parse JSON
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            result.add_error(f"Line {i}: Invalid JSON — {e}")
            continue

        # Validate against product_line schema
        for error in validator.iter_errors(obj):
            field_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            result.add_error(f"Line {i}: {field_path} — {error.message}")

    if result.valid:
        result.warnings.append(f"Validated {len(lines)} product lines")

    return result


def validate_all(
    manifest_path: str | Path,
    feed_path: Optional[str | Path] = None,
) -> ValidationResult:
    """Validate manifest and optionally the feed."""
    combined = ValidationResult(valid=True)

    # Validate manifest
    manifest_result = validate_manifest(manifest_path)
    combined.errors.extend(manifest_result.errors)
    combined.warnings.extend(manifest_result.warnings)
    if not manifest_result.valid:
        combined.valid = False

    # Validate feed if provided or auto-detected
    if feed_path:
        feed_result = validate_feed(feed_path)
        combined.errors.extend(feed_result.errors)
        combined.warnings.extend(feed_result.warnings)
        if not feed_result.valid:
            combined.valid = False
    else:
        # Try to auto-detect feed relative to manifest
        manifest_dir = Path(manifest_path).resolve().parent
        # Look for feed in sibling structure: ../llm/feed/products.jsonl
        possible_feed = manifest_dir.parent / "llm" / "feed" / "products.jsonl"
        if possible_feed.exists():
            combined.warnings.append(f"Auto-detected feed: {possible_feed}")
            feed_result = validate_feed(possible_feed)
            combined.errors.extend(feed_result.errors)
            combined.warnings.extend(feed_result.warnings)
            if not feed_result.valid:
                combined.valid = False

    return combined
