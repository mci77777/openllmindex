# llmindex Specification v0.1

> **Status**: v0.1.0
> **Fixed Entry Point**: `/.well-known/llmindex.json`
> **Goal**: Provide a machine-readable index for LLMs, AI search engines, and crawlers to discover and understand a website's key information.

## 1. Overview

llmindex is a lightweight specification that defines a standardized JSON manifest at a well-known URL. It acts as a "table of contents" for LLM agents, telling them where to find products, policies, FAQs, and other structured information about a website.

**Design Principles**:
- Minimal: ≤10 top-level fields
- Discoverable: Fixed well-known path
- Verifiable: Optional domain ownership proof and cryptographic signatures
- Versionable: Semantic versioning with backward compatibility guarantees

## 2. Entry Point

```
GET /.well-known/llmindex.json
Content-Type: application/json; charset=utf-8
```

Servers SHOULD support conditional requests via:
- `ETag` header for content-based caching
- `Last-Modified` header for time-based caching
- `Cache-Control` header (recommended: `max-age=3600, must-revalidate`)

## 3. Field Definitions

### 3.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Specification version. MUST be `"0.1"` for this version. |
| `updated_at` | string | ISO 8601 datetime (UTC recommended). Indicates when the manifest was last updated. |
| `entity` | object | The entity this manifest describes. |
| `entity.name` | string | Display name of the entity (company, brand, person). |
| `entity.canonical_url` | string (URI) | The canonical homepage URL. MUST be a valid HTTPS URL. |
| `language` | string | Primary language, BCP-47 format (e.g., `"en"`, `"zh-CN"`, `"ja"`). |
| `topics` | array[string] | Category tags describing the entity's domain. At least one required. |
| `endpoints` | object | URLs pointing to human/machine-readable information pages. |
| `endpoints.products` | string (URI) | Product listing page URL. |
| `endpoints.policies` | string (URI) | Policies page URL (shipping, returns, warranty, payment). |
| `endpoints.faq` | string (URI) | FAQ page URL. |
| `endpoints.about` | string (URI) | About/company information page URL. |

### 3.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `feeds` | object | Machine-readable data feeds. |
| `feeds.products_jsonl` | string (URI) | URL to a JSONL file containing product data (recommended). |
| `feeds.offers_json` | string (URI) | URL to a JSON file containing current offers/promotions. |
| `verify` | object | Domain ownership verification. |
| `verify.method` | string | Verification method: `"dns_txt"` or `"http_file"`. |
| `verify.value` | string | Challenge value (DNS TXT record content) or proof file name. |
| `sig` | object | Cryptographic signature of the manifest. |
| `sig.alg` | string | Signature algorithm (recommended: `"EdDSA"`). |
| `sig.kid` | string | Key identifier for public key lookup. |
| `sig.jws` | string | JWS Compact Serialization of the signed manifest. |
| `license` | string | License identifier (SPDX format) or URL to license text. |

## 4. /llm Pages

The `endpoints` object points to pages optimized for LLM consumption. These pages SHOULD:
- Be accessible without authentication
- Use clean, structured markup (Markdown or well-structured HTML)
- Contain factual, up-to-date information
- Avoid heavy JavaScript rendering (content should be in initial HTML/Markdown)

### 4.1 Required Pages

| Page | Path (recommended) | Content |
|------|---------------------|---------|
| Products | `/llm/products` | Grouped product listing with names, prices, categories, and links. |
| Policies | `/llm/policies` | Shipping, returns, warranty, and payment policies. |
| FAQ | `/llm/faq` | Frequently asked questions organized by topic. |
| About | `/llm/about` | Brand story, company information, contact details. |

## 5. products.jsonl Feed Format

Each line is a JSON object with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique product identifier. |
| `title` | string | Yes | Product display name. |
| `url` | string (URI) | Yes | Product page URL. |
| `image_url` | string (URI) | No | Primary product image URL. |
| `price` | number | Yes* | Product price. Required if `price_range` is absent. |
| `currency` | string | Yes* | ISO 4217 currency code. Required with `price`. |
| `price_range` | object | No | Alternative to `price`: `{"min": number, "max": number, "currency": string}`. |
| `availability` | string | Yes | One of: `"in_stock"`, `"out_of_stock"`, `"preorder"`. |
| `brand` | string | No | Brand name. |
| `category` | string | No | Product category. |
| `updated_at` | string | Yes | ISO 8601 datetime of last product update. |

*Either `price` + `currency` or `price_range` MUST be present.

## 6. Verification

### 6.1 DNS TXT Verification

Add a TXT record to the domain's DNS:
```
_llmindex-challenge.example.com TXT "challenge-value-here"
```

Set `verify.method` to `"dns_txt"` and `verify.value` to the challenge string.

### 6.2 HTTP File Verification

Place a proof file at:
```
GET /.well-known/llmindex-proof.txt
```

The file content MUST match `verify.value`. Set `verify.method` to `"http_file"`.

### 6.3 Signature (Optional)

For tamper-proof manifests, sign the canonical JSON (sorted keys, no whitespace) using JWS:
- Recommended algorithm: `EdDSA` (Ed25519)
- The `sig.jws` field contains the JWS Compact Serialization
- Validators MUST verify the signature against a published public key (identified by `sig.kid`)

## 7. Versioning Strategy

- **0.x versions**: Breaking changes allowed between minor versions. Clients SHOULD check `version` field.
- **1.0+**: Backward-compatible changes only. New optional fields may be added; existing fields will not be removed or change semantics.
- **Version negotiation**: Clients read the `version` field and apply version-appropriate parsing.

## 8. Compatibility

Implementors MAY generate a `/llms.txt` file as a compatibility layer for tools that expect it. However, `/.well-known/llmindex.json` is the canonical entry point.

## 9. Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| `/.well-known/llmindex.json` returns 404 | Site does not support llmindex. |
| `/.well-known/llmindex.json` returns non-JSON | Treat as unsupported; log warning. |
| `version` field is unrecognized | Attempt best-effort parsing; warn on unknown fields. |
| `endpoints.*` URL returns 404/5xx | Mark endpoint as unavailable; continue with others. |
| `feeds.*` URL is unreachable | Skip feed; rely on endpoint pages. |

## 10. Security Considerations

- **HTTPS required**: Manifests MUST be served over HTTPS, and `entity.canonical_url` MUST be an HTTPS URL. Implementations SHOULD use HTTPS for all `endpoints.*` and `feeds.*` URLs.
- **No secrets in manifests**: Implementations MUST NOT include authentication tokens, API keys, session identifiers, or other secrets in the manifest (including in URL query strings).
- **robots.txt guidance**: If you want AI agents to discover and read your llmindex content, do not block `/.well-known/llmindex.json` or your referenced `/llm/*` endpoints in `robots.txt`. If you do not want automated access, use `robots.txt` and/or other access controls to limit crawling.

## 11. IANA Considerations

This specification uses the existing `application/json` media type. No new IANA registrations are required.

## 12. Changelog

- **v0.1.0 (2025-02-22)** — Initial Release.
- **v0.2.0 (Unreleased)** — Add `languages`, `localized_endpoints`, `access_control`, `feed_updated_at`, and EdDSA JWS signing (CLI: `llmindex sign keygen|manifest|verify`).
