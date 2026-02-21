# @llmindex/schema

JSON Schema and TypeScript types for the [llmindex](https://github.com/mci77777/openllmindex) v0.1 manifest standard.

## Install

```bash
npm install @llmindex/schema
```

## Usage

### Validate a manifest (with Ajv)

```typescript
import Ajv from "ajv";
import addFormats from "ajv-formats";
import llmindexSchema from "@llmindex/schema";

const ajv = new Ajv();
addFormats(ajv);
const validate = ajv.compile(llmindexSchema);

const manifest = {
  version: "0.1",
  updated_at: "2026-02-20T00:00:00Z",
  entity: { name: "ACME", canonical_url: "https://acme.com" },
  language: "en",
  topics: ["outdoor-gear"],
  endpoints: {
    products: "https://acme.com/llm/products",
    policies: "https://acme.com/llm/policies",
    faq: "https://acme.com/llm/faq",
    about: "https://acme.com/llm/about",
  },
};

if (validate(manifest)) {
  console.log("Valid!");
} else {
  console.log(validate.errors);
}
```

### TypeScript types

```typescript
import type { LlmindexManifest, LlmindexProductLine } from "@llmindex/schema";

const manifest: LlmindexManifest = {
  version: "0.1",
  updated_at: new Date().toISOString(),
  entity: { name: "My Store", canonical_url: "https://mystore.com" },
  language: "en",
  topics: ["ecommerce"],
  endpoints: {
    products: "https://mystore.com/llm/products",
    policies: "https://mystore.com/llm/policies",
    faq: "https://mystore.com/llm/faq",
    about: "https://mystore.com/llm/about",
  },
};
```

## What is llmindex?

llmindex is a machine-readable index standard for LLM and AI search discovery. A JSON manifest at `/.well-known/llmindex.json` tells AI agents where to find structured information about your website.

See the [full specification](https://github.com/mci77777/openllmindex/blob/main/spec/spec.md).

## License

CC-BY-4.0
