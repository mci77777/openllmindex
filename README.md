# llmindex

> A machine-readable index standard for LLM and AI search discovery.

**llmindex** defines a lightweight JSON manifest at `/.well-known/llmindex.json` that tells LLMs, AI search engines, and crawlers where to find structured information about your website — products, policies, FAQs, and more.

Think of it as **robots.txt for the AI era**: instead of telling crawlers what *not* to access, llmindex tells AI agents what *is* available and where to find it.

## How It Works

```
Your Website
├── /.well-known/llmindex.json   ← Entry point (manifest)
├── /llm/products                ← Product listing page
├── /llm/policies                ← Shipping, returns, warranty
├── /llm/faq                     ← Frequently asked questions
├── /llm/about                   ← Brand & contact info
└── /llm/feed/products.jsonl     ← Machine-readable product feed
```

An LLM agent visiting your site fetches `/.well-known/llmindex.json` first, discovers available endpoints, and then reads the structured content it needs.

## Example Manifest

```json
{
  "version": "0.1",
  "updated_at": "2026-02-17T10:00:00Z",
  "entity": { "name": "ACME", "canonical_url": "https://acme.com" },
  "language": "en",
  "topics": ["outdoor-gear"],
  "endpoints": {
    "products": "https://acme.com/llm/products",
    "policies": "https://acme.com/llm/policies",
    "faq": "https://acme.com/llm/faq",
    "about": "https://acme.com/llm/about"
  },
  "feeds": {
    "products_jsonl": "https://acme.com/llm/feed/products.jsonl"
  }
}
```

## Quick Start

### Install

```bash
pip install -e .
```

Requires Python 3.11+.

### Generate from CSV

Prepare a products CSV file with columns: `id`, `title`, `url`, `price`, `currency`, `availability`, etc. (see `cli/sample_data/sample.csv` for the full format).

```bash
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

### Validate Against Schema

```bash
python -c "
import json, jsonschema
schema = json.load(open('spec/schemas/llmindex-0.1.schema.json'))
data = json.load(open('dist/.well-known/llmindex.json'))
jsonschema.validate(data, schema)
print('Valid!')
"
```

### Run Tests

```bash
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

See [`cli/sample_data/sample.csv`](cli/sample_data/sample.csv) for a working example.

## Specification

The full llmindex v0.1 specification is at [`spec/spec.md`](spec/spec.md).

### Required Manifest Fields

| Field | Description |
|-------|-------------|
| `version` | `"0.1"` |
| `updated_at` | ISO 8601 datetime |
| `entity.name` | Brand/company name |
| `entity.canonical_url` | Homepage (HTTPS) |
| `language` | BCP-47 language code |
| `topics` | Category tags |
| `endpoints` | URLs: products, policies, faq, about |

### Optional Fields

`feeds`, `verify` (domain ownership), `sig` (cryptographic signature), `license`

### JSON Schema

Machine-readable schema for validation: [`spec/schemas/llmindex-0.1.schema.json`](spec/schemas/llmindex-0.1.schema.json)

## Examples

| Industry | Directory | Description |
|----------|-----------|-------------|
| E-commerce | [`spec/examples/ecommerce/`](spec/examples/ecommerce/) | Outdoor gear store with full feed |
| Local Business | [`spec/examples/local-business/`](spec/examples/local-business/) | Bakery with minimal fields |
| SaaS | [`spec/examples/saas/`](spec/examples/saas/) | Productivity tool, no product feed |

## Project Structure

```
├── spec/                        # The llmindex specification
│   ├── spec.md                  # v0.1 specification document
│   ├── schemas/                 # JSON Schema for validation
│   ├── examples/                # Industry examples (ecommerce, local, SaaS)
│   └── test-vectors/            # Invalid manifests for testing validators
├── cli/                         # Generator CLI tool
│   ├── llmindex_cli/            # CLI application (Typer)
│   │   ├── main.py              # Entry point
│   │   ├── models.py            # Pydantic data models
│   │   └── generators/          # Output generators
│   ├── importers/               # Data importers (CSV)
│   ├── sample_data/             # Sample CSV for testing
│   └── tests/                   # Test suite
└── pyproject.toml
```

## License

- **Specification** (`spec/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **CLI Tools** (`cli/`): [AGPL-3.0-or-later](LICENSE)

## Contributing

Contributions welcome. Please open an issue first to discuss what you'd like to change.
