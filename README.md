# llmindex

[![License: AGPL-3.0](https://img.shields.io/badge/CLI-AGPL--3.0-blue.svg)](LICENSE)
[![Spec: CC BY 4.0](https://img.shields.io/badge/Spec-CC_BY_4.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Spec Version](https://img.shields.io/badge/spec-v0.1-orange.svg)](spec/spec.md)

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
pip install -e .

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
pip install -e ".[dev]"
pytest
```

## CLI Reference

```
llmindex generate [OPTIONS]

Options:
  -s, --site        TEXT   Entity/brand name (required)
  -u, --url         TEXT   Canonical HTTPS URL (required)
  -i, --input-csv   PATH   Path to products CSV (required)
  -o, --output-dir  PATH   Output directory (default: dist)
  -l, --language    TEXT   Primary language, BCP-47 (default: en)
  -t, --topic       TEXT   Category topics (repeatable)
      --base-url    TEXT   Base URL for endpoints (defaults to --url)
```

## CSV Format

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

See [`cli/sample_data/sample.csv`](cli/sample_data/sample.csv) for a working example with 20 products.

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

## Project Structure

```
openllmindex/
├── spec/                        # The llmindex specification
│   ├── spec.md                  # v0.1 specification document
│   ├── schemas/                 # JSON Schema for validation
│   │   └── llmindex-0.1.schema.json
│   ├── examples/                # Industry examples
│   │   ├── ecommerce/           #   Full store with feed + verify
│   │   ├── local-business/      #   Minimal bakery
│   │   └── saas/                #   SaaS with license
│   └── test-vectors/            # Invalid manifests for testing
├── cli/                         # Generator CLI tool
│   ├── llmindex_cli/            # CLI application (Typer)
│   │   ├── main.py              # Entry point
│   │   ├── models.py            # Pydantic data models
│   │   └── generators/          # Output generators
│   │       ├── manifest.py      #   Manifest generator
│   │       ├── pages.py         #   Markdown page generator
│   │       └── feed.py          #   JSONL feed generator
│   ├── importers/               # Data importers
│   │   └── csv_importer.py      #   CSV product importer
│   ├── sample_data/             # Sample CSV for testing
│   └── tests/                   # Test suite (40+ tests)
├── examples/                    # Usage examples
│   ├── demo.py                  # End-to-end demo script
│   └── test_demo.py             # Demo test suite
├── pyproject.toml               # Python package config
├── LICENSE                      # AGPL-3.0
└── README.md
```

## License

- **Specification** (`spec/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to adopt, reference, and build upon
- **CLI Tools** (`cli/`): [AGPL-3.0-or-later](LICENSE)

## Contributing

Contributions welcome. Please open an issue first to discuss what you'd like to change.

### Areas for Contribution

- **New industry examples** — Healthcare, education, real estate, etc.
- **New importers** — Shopify, WooCommerce, JSON, XML
- **Validators** — Standalone validation tools for manifest + feeds
- **Integrations** — WordPress plugin, Next.js middleware, etc.
- **Translations** — Spec and examples in other languages
