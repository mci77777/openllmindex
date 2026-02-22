# llmindex

[![License: AGPL-3.0](https://img.shields.io/badge/CLI-AGPL--3.0-blue.svg)](LICENSE)
[![Spec: CC BY 4.0](https://img.shields.io/badge/Spec-CC_BY_4.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Spec Version](https://img.shields.io/badge/spec-v0.2-orange.svg)](spec/spec.md)
[![PyPI](https://img.shields.io/pypi/v/openllmindex.svg)](https://pypi.org/project/openllmindex/)
[![npm](https://img.shields.io/npm/v/@llmindex/schema.svg)](https://www.npmjs.com/package/@llmindex/schema)

<p align="center">
  <img src="assets/openllmindex.png" alt="llmindex — AI-readable index for your website" width="700">
</p>

> A machine-readable index standard for LLM and AI search discovery.

**llmindex** defines a lightweight JSON manifest at `/.well-known/llmindex.json` that tells LLMs, AI search engines, and crawlers where to find structured information about your website — products, policies, FAQs, and more.

Think of it as **robots.txt for the AI era**: instead of telling crawlers what *not* to access, llmindex tells AI agents what *is* available and where to find it.

## Why llmindex?

AI search engines (ChatGPT, Perplexity, Gemini, etc.) are increasingly answering user questions by reading website content directly. But today, there's no standard way for websites to tell AI agents:

- **What information is available** (products, policies, FAQs)
- **Where to find it** (structured URLs, not scattered HTML)
- **In what format** (Markdown for reading, JSONL for data)

**llmindex solves this.** One JSON file at a well-known path gives AI agents everything they need to understand and represent your business accurately.

| Without llmindex | With llmindex |
|---|---|
| AI agents guess what pages matter | AI agents know exactly where to look |
| Product info scattered across HTML | Clean Markdown pages + structured JSONL feed |
| No way to verify domain ownership | Built-in DNS/HTTP verification |
| No version control for AI-facing data | Timestamped, versioned manifest |

## How It Works

```
1. LLM agent visits your site
2. Fetches /.well-known/llmindex.json    ← discovers the manifest
3. Reads endpoints → /llm/products       ← gets product listing
4. Reads feed → /llm/feed/products.jsonl ← gets structured data
5. Answers user's question accurately    ← better AI responses
```

Your website structure:

```
/.well-known/llmindex.json   ← Entry point (manifest)
/llm/products                ← Product listing (Markdown)
/llm/policies                ← Shipping, returns, warranty
/llm/faq                     ← Frequently asked questions
/llm/about                   ← Brand & contact info
/llm/feed/products.jsonl     ← Machine-readable product feed
```

## Example Manifest

```json
{
  "version": "0.1",
  "updated_at": "2026-02-17T10:00:00Z",
  "entity": {
    "name": "ACME Outdoor Gear",
    "canonical_url": "https://acme-outdoor.com"
  },
  "language": "en",
  "topics": ["outdoor-gear", "camping", "hiking"],
  "endpoints": {
    "products": "https://acme-outdoor.com/llm/products",
    "policies": "https://acme-outdoor.com/llm/policies",
    "faq": "https://acme-outdoor.com/llm/faq",
    "about": "https://acme-outdoor.com/llm/about"
  },
  "feeds": {
    "products_jsonl": "https://acme-outdoor.com/llm/feed/products.jsonl"
  }
}
```

## Quick Start

### For Website Owners (Adopt the Standard)

You don't need the CLI tool. Just create a JSON file at `/.well-known/llmindex.json` on your server:

```json
{
  "version": "0.1",
  "updated_at": "2026-02-20T00:00:00Z",
  "entity": {
    "name": "Your Brand Name",
    "canonical_url": "https://your-site.com"
  },
  "language": "en",
  "topics": ["your-industry"],
  "endpoints": {
    "products": "https://your-site.com/llm/products",
    "policies": "https://your-site.com/llm/policies",
    "faq": "https://your-site.com/llm/faq",
    "about": "https://your-site.com/llm/about"
  }
}
```

Then create the `/llm/*` pages as simple Markdown or HTML files. That's it.

Validate your manifest against the [JSON Schema](spec/schemas/llmindex-0.1.schema.json):

```bash
python -c "
import json, jsonschema
schema = json.load(open('spec/schemas/llmindex-0.1.schema.json'))
data = json.load(open('your-manifest.json'))
jsonschema.validate(data, schema)
print('Valid!')
"
```

### For Developers (Use the CLI Generator)

The CLI tool auto-generates all llmindex files from a product CSV:

```bash
# Install
pip install openllmindex

# Generate from CSV
llmindex generate \
  --site "ACME Outdoor" \
  --url https://acme-outdoor.com \
  --input-csv products.csv \
  --topic outdoor-gear \
  --topic camping \
  --output-dir dist
```

This generates:

```
dist/
├── .well-known/llmindex.json      # The manifest
├── llm/
│   ├── products.md                # Product listing grouped by category
│   ├── policies.md                # Policies page (template)
│   ├── faq.md                     # FAQ page (template)
│   ├── about.md                   # About page (template)
│   └── feed/
│       └── products.jsonl         # Machine-readable feed (1 JSON per line)
```

### Run the Demo

```bash
# Run the interactive demo
python examples/demo.py

# Run the test suite
pip install "openllmindex[dev]"
pytest
```

## CLI Reference

### `llmindex generate`

```
llmindex generate [OPTIONS]

Input (one required):
  -i, --input-csv         PATH   Products CSV file
      --input-json        PATH   Products JSON file (array of objects)
      --input-shopify-csv PATH   Shopify product export CSV

Options:
  -s, --site        TEXT   Entity/brand name (required)
  -u, --url         TEXT   Canonical HTTPS URL (required)
  -o, --output-dir  PATH   Output directory (default: dist)
  -l, --language    TEXT   Primary language, BCP-47 (default: en)
  -t, --topic       TEXT   Category topics (repeatable)
      --base-url    TEXT   Base URL for endpoints (defaults to --url)
      --currency    TEXT   Default currency for Shopify imports (default: USD)
```

### `llmindex validate`

```
llmindex validate MANIFEST_PATH [OPTIONS]

Arguments:
  MANIFEST_PATH     PATH   Path to llmindex.json file (required)

Options:
  -f, --feed        PATH   Path to products.jsonl (auto-detected if omitted)
```

Example:

```bash
llmindex validate dist/.well-known/llmindex.json
llmindex validate dist/.well-known/llmindex.json --feed dist/llm/feed/products.jsonl
```

## Input Formats

### CSV (default)

Standard CSV with columns matching the product schema.

| Column | Required | Description |
|--------|----------|-------------|
| `id` | Yes | Unique product ID |
| `title` | Yes | Product name |
| `url` | Yes | Product page URL |
| `image_url` | No | Product image URL |
| `price` | Yes | Numeric price |
| `currency` | Yes | ISO 4217 code (USD, EUR, etc.) |
| `availability` | Yes | `in_stock`, `out_of_stock`, or `preorder` |
| `brand` | No | Brand name |
| `category` | No | Product category |
| `updated_at` | No | ISO 8601 datetime |

See [`llmindex/sample_data/sample.csv`](llmindex/sample_data/sample.csv) for a working example with 20 products.

### JSON

A JSON array of product objects with the same fields:

```bash
llmindex generate --site "TechCo" --url https://techco.com --input-json products.json
```

See [`llmindex/sample_data/sample.json`](llmindex/sample_data/sample.json) for an example.

### Shopify CSV Export

Import directly from Shopify's product CSV export format. Handles are deduplicated (one product per handle), and product URLs are auto-constructed from your store URL:

```bash
llmindex generate \
  --site "My Store" \
  --url https://mystore.com \
  --input-shopify-csv shopify_products.csv \
  --currency USD
```

See [`llmindex/sample_data/sample_shopify.csv`](llmindex/sample_data/sample_shopify.csv) for an example.

## Industry Examples

Each example includes a complete `llmindex.json` manifest and `/llm` content pages.

### E-commerce — Outdoor Gear Store

Full example with product feed and domain verification.

```
spec/examples/ecommerce/
├── llmindex.json              # Manifest with feeds + verify
├── llm/
│   ├── products.md            # 10 products, grouped by category
│   ├── policies.md            # Shipping, returns, warranty
│   ├── faq.md                 # Customer FAQ
│   └── about.md               # Brand story
└── feed/
    └── products.jsonl         # 10-line JSONL product feed
```

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.1",
  "updated_at": "2026-02-17T10:00:00Z",
  "entity": {
    "name": "ACME Outdoor Gear",
    "canonical_url": "https://acme-outdoor.com"
  },
  "language": "en",
  "topics": ["outdoor-gear", "camping", "hiking"],
  "endpoints": {
    "products": "https://acme-outdoor.com/llm/products",
    "policies": "https://acme-outdoor.com/llm/policies",
    "faq": "https://acme-outdoor.com/llm/faq",
    "about": "https://acme-outdoor.com/llm/about"
  },
  "feeds": {
    "products_jsonl": "https://acme-outdoor.com/llm/feed/products.jsonl"
  },
  "verify": {
    "method": "dns_txt",
    "value": "llmindex-verify-a1b2c3d4e5"
  }
}
```
</details>

### Local Business — Bakery

Minimal manifest with required fields only. No product feed needed.

```
spec/examples/local-business/
├── llmindex.json              # Minimal required fields
└── llm/
    ├── products.md            # Menu items
    ├── policies.md            # Store policies
    ├── faq.md                 # Common questions
    └── about.md               # About the bakery
```

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.1",
  "updated_at": "2026-02-15T09:00:00Z",
  "entity": {
    "name": "Sunrise Bakery",
    "canonical_url": "https://sunrise-bakery.com"
  },
  "language": "en",
  "topics": ["bakery", "pastry", "local-business"],
  "endpoints": {
    "products": "https://sunrise-bakery.com/llm/products",
    "policies": "https://sunrise-bakery.com/llm/policies",
    "faq": "https://sunrise-bakery.com/llm/faq",
    "about": "https://sunrise-bakery.com/llm/about"
  }
}
```
</details>

### SaaS — Productivity Tool

Software product with license field, no product feed.

```
spec/examples/saas/
├── llmindex.json              # Manifest with license field
└── llm/
    ├── products.md            # Pricing plans
    ├── policies.md            # Terms, privacy, SLA
    ├── faq.md                 # Product FAQ
    └── about.md               # Company info
```

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.1",
  "updated_at": "2026-02-10T14:30:00Z",
  "entity": {
    "name": "TaskFlow",
    "canonical_url": "https://taskflow.io"
  },
  "language": "en",
  "topics": ["saas", "productivity", "project-management"],
  "endpoints": {
    "products": "https://taskflow.io/llm/products",
    "policies": "https://taskflow.io/llm/policies",
    "faq": "https://taskflow.io/llm/faq",
    "about": "https://taskflow.io/llm/about"
  },
  "license": "CC-BY-4.0"
}
```
</details>

### Healthcare — Telemedicine (v0.2)

Multi-language healthcare platform with access control and attribution requirements.

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.2",
  "updated_at": "2026-02-22T12:00:00Z",
  "entity": {
    "name": "MediCare Health Systems",
    "canonical_url": "https://medicare-health.com"
  },
  "language": "en",
  "languages": ["en", "es"],
  "topics": ["healthcare", "telemedicine", "medical"],
  "endpoints": { "..." },
  "localized_endpoints": { "es": { "..." } },
  "access_control": {
    "allow": ["*"],
    "deny": ["BadBot"],
    "rate_limit": "500/day",
    "requires_attribution": true,
    "commercial_use": "contact-required"
  },
  "license": "CC-BY-NC-4.0"
}
```
</details>

### Education — Online Courses (v0.2)

Course platform with 3-language support and non-commercial license.

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.2",
  "entity": { "name": "LearnHub Academy", "canonical_url": "https://learnhub.edu" },
  "languages": ["en", "zh-CN", "ja"],
  "topics": ["education", "online-courses", "certification"],
  "access_control": { "commercial_use": "non-commercial" },
  "license": "CC-BY-NC-SA-4.0"
}
```
</details>

### Real Estate — Property Listings

Property listing site with product feed and HTTP file verification.

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.1",
  "entity": { "name": "PrimeProperty Realty", "canonical_url": "https://primeproperty.com" },
  "topics": ["real-estate", "property", "housing", "rental"],
  "feeds": { "products_jsonl": "https://primeproperty.com/llm/feed/products.jsonl" },
  "verify": { "method": "http_file", "value": "llmindex-verify.txt" }
}
```
</details>

### Fintech — Digital Payments (v0.2)

Financial services with selective bot access, multi-language, and dual feeds.

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.2",
  "entity": { "name": "PayWave Financial", "canonical_url": "https://paywave.finance" },
  "languages": ["en", "de", "fr"],
  "topics": ["fintech", "payments", "banking", "digital-wallet"],
  "access_control": {
    "allow": ["GPTBot", "ClaudeBot", "PerplexityBot"],
    "rate_limit": "100/hour",
    "commercial_use": "contact-required"
  },
  "feeds": { "products_jsonl": "...", "offers_json": "..." }
}
```
</details>

### Nonprofit — Environmental Foundation

Public-domain nonprofit with DNS verification.

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.1",
  "entity": { "name": "GreenEarth Foundation", "canonical_url": "https://greenearth.org" },
  "topics": ["nonprofit", "environment", "sustainability", "charity"],
  "license": "CC0-1.0",
  "verify": { "method": "dns_txt", "value": "llmindex-verify-greenearth-2026" }
}
```
</details>

### Travel — Global Tourism (v0.2)

Travel platform with 6-language support, delta feeds, and open access.

<details>
<summary>View manifest</summary>

```json
{
  "version": "0.2",
  "entity": { "name": "WanderPath Travel", "canonical_url": "https://wanderpath.com" },
  "languages": ["en", "es", "fr", "de", "ja", "zh-CN"],
  "topics": ["travel", "tourism", "hotels", "flights", "vacation"],
  "feeds": { "products_jsonl": "...", "products_jsonl_delta": "...?since=..." },
  "access_control": { "rate_limit": "2000/day", "commercial_use": "allowed" },
  "license": "CC-BY-4.0"
}
```
</details>

## Specification

The full llmindex v0.1 specification: [`spec/spec.md`](spec/spec.md)

### Required Manifest Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | `"0.1"` |
| `updated_at` | string | ISO 8601 datetime |
| `entity.name` | string | Brand/company name |
| `entity.canonical_url` | string | Homepage (HTTPS) |
| `language` | string | BCP-47 language code |
| `topics` | array | Category tags (1+ required) |
| `endpoints` | object | URLs: products, policies, faq, about |

### Optional Fields

| Field | Description |
|-------|-------------|
| `feeds` | Machine-readable data feeds (`products_jsonl`, `offers_json`) |
| `verify` | Domain ownership proof (`dns_txt` or `http_file`) |
| `sig` | Cryptographic signature (JWS with EdDSA) |
| `license` | SPDX license identifier or URL |

### JSON Schema

Machine-readable schema for validation: [`spec/schemas/llmindex-0.1.schema.json`](spec/schemas/llmindex-0.1.schema.json)

### Comparison with llms.txt

| | llmindex | llms.txt |
|---|---|---|
| Format | JSON (structured, machine-parseable) | Plain text |
| Location | `/.well-known/llmindex.json` | `/llms.txt` |
| Schema validation | JSON Schema provided | No formal schema |
| Structured data feeds | JSONL product feeds | Not specified |
| Domain verification | DNS TXT / HTTP file | Not specified |
| Versioning | Semantic versioning built-in | Not specified |
| Focus | Structured discovery + data | Guidance for LLMs |

llmindex and llms.txt serve complementary purposes. llmindex focuses on structured, machine-parseable discovery; llms.txt focuses on human-readable guidance. You can use both.

## Packages

| Package | Registry | Install |
|---------|----------|---------|
| [`openllmindex`](https://pypi.org/project/openllmindex/) | PyPI | `pip install openllmindex` |
| [`@llmindex/schema`](https://www.npmjs.com/package/@llmindex/schema) | npm | `npm install @llmindex/schema` |

## Integrations

- **[Next.js](integrations/nextjs/)** — Static files, API routes, or middleware rewrite
- **[WordPress](integrations/wordpress/)** — Static file, rewrite rules, or WooCommerce product feed

## Project Structure

```
openllmindex/
├── spec/                        # The llmindex specification
│   ├── spec.md                  # v0.1 specification document
│   ├── schemas/                 # JSON Schema for validation
│   │   └── llmindex-0.1.schema.json
│   ├── examples/                # Industry examples (12 industries)
│   │   ├── blog/                #   Blog/newsletter
│   │   ├── ecommerce/           #   Full store with feed + verify (v0.2)
│   │   ├── education/           #   Online courses, 3 languages (v0.2)
│   │   ├── fintech/             #   Digital payments, selective access (v0.2)
│   │   ├── healthcare/          #   Telemedicine, access control (v0.2)
│   │   ├── local-business/      #   Minimal bakery
│   │   ├── marketplace/         #   Handmade marketplace
│   │   ├── nonprofit/           #   Environmental foundation
│   │   ├── real-estate/         #   Property listings with feed
│   │   ├── restaurant/          #   Restaurant with verify
│   │   ├── saas/                #   SaaS with license + verify
│   │   └── travel/              #   Global tourism, 6 languages (v0.2)
│   └── test-vectors/            # Invalid manifests for testing
├── llmindex/                    # Generator CLI tool (Python package)
│   ├── llmindex_cli/            # CLI application (Typer)
│   │   ├── main.py              # Entry point
│   │   ├── models.py            # Pydantic data models
│   │   ├── validators.py        # Schema + feed validation
│   │   └── generators/          # Output generators
│   ├── importers/               # Data importers (CSV, JSON, Shopify)
│   ├── sample_data/             # Sample data for testing
│   └── tests/                   # Test suite (100+ tests)
├── packages/                    # Published packages
│   └── schema/                  # @llmindex/schema (npm)
├── integrations/                # Platform integrations
│   ├── nextjs/                  #   Next.js middleware + examples
│   └── wordpress/               #   WordPress + WooCommerce
├── docs/                        # GitHub Pages documentation site
├── examples/                    # Usage examples
├── pyproject.toml               # Python package config
├── LICENSE                      # AGPL-3.0
└── README.md
```

## License

- **Specification** (`spec/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to adopt, reference, and build upon
- **CLI Tools** (`llmindex/`): [AGPL-3.0-or-later](LICENSE)

## Contributing

Contributions welcome. Please open an issue first to discuss what you'd like to change.

### Areas for Contribution

- **New industry examples** — Healthcare, education, real estate, etc.
- **New importers** — Shopify, WooCommerce, JSON, XML
- **Validators** — Standalone validation tools for manifest + feeds
- **Integrations** — WordPress plugin, Next.js middleware, etc.
- **Translations** — Spec and examples in other languages
