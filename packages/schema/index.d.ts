/**
 * llmindex Manifest Schema — TypeScript type definitions.
 *
 * @see https://github.com/mci77777/openllmindex/blob/main/spec/spec.md
 */

/** Verification method for domain ownership proof. */
export interface LlmindexVerify {
  method: "dns_txt" | "http_file";
  value: string;
}

/** Cryptographic signature (JWS with EdDSA). */
export interface LlmindexSig {
  alg: string;
  kid: string;
  jws: string;
}

/** Entity (brand/company) information. */
export interface LlmindexEntity {
  /** Display name of the entity. */
  name: string;
  /** Canonical homepage URL (HTTPS). */
  canonical_url: string;
}

/** Required endpoint URLs. */
export interface LlmindexEndpoints {
  products: string;
  policies: string;
  faq: string;
  about: string;
}

/** Localized endpoint URLs keyed by BCP-47 language tag. */
export interface LocalizedEndpoints {
  [lang: string]: Partial<LlmindexEndpoints>;
}

/** Optional machine-readable data feeds. */
export interface LlmindexFeeds {
  products_jsonl?: string;
  products_jsonl_delta?: string;
  offers_json?: string;
}

/**
 * Access control declarations for AI agents and LLM crawlers.
 * @since v0.2 pre-adoption (optional field in v0.1 schema)
 */
export interface AccessControl {
  /** List of allowed AI agent identifiers. Use ['*'] to allow all (default). */
  allow?: string[];
  /** List of denied AI agent identifiers. Takes precedence over allow. */
  deny?: string[];
  /** Suggested rate limit hint. Format: '<count>/<unit>' (e.g., '1000/day'). */
  rate_limit?: string;
  /** If true, AI-generated content derived from this data must attribute the source. */
  requires_attribution?: boolean;
  /** Commercial use permission level. */
  commercial_use?: "allowed" | "non-commercial" | "contact-required";
}

/** The llmindex manifest (v0.1/v0.2). */
export interface LlmindexManifest {
  /** Spec version. */
  version: "0.1" | "0.2";
  /** ISO 8601 datetime of last update. */
  updated_at: string;
  /** ISO 8601 datetime of last feed update. */
  feed_updated_at?: string;
  /** Entity information. */
  entity: LlmindexEntity;
  /** Primary language (BCP-47). */
  language: string;
  /** Optional list of supported languages (BCP-47). */
  languages?: string[];
  /** Category tags. */
  topics: string[];
  /** Required endpoint URLs. */
  endpoints: LlmindexEndpoints;
  /** Optional localized endpoint URL overrides. */
  localized_endpoints?: LocalizedEndpoints;
  /** Optional data feeds. */
  feeds?: LlmindexFeeds;
  /** Domain verification. */
  verify?: LlmindexVerify;
  /** Cryptographic signature. */
  sig?: LlmindexSig;
  /** SPDX license identifier or URL. */
  license?: string;
  /** Access control declarations for AI agents. */
  access_control?: AccessControl;
}

/** Price range for products with variable pricing. */
export interface ProductPriceRange {
  min: number;
  max: number;
  currency: string;
}

/** A single product line in products.jsonl feed. */
export interface LlmindexProductLine {
  id: string;
  title: string;
  url: string;
  image_url?: string;
  price?: number;
  currency?: string;
  price_range?: ProductPriceRange;
  availability: "in_stock" | "out_of_stock" | "preorder";
  brand?: string;
  category?: string;
  updated_at: string;
}

/** The full JSON Schema object for v0.1 (Draft-07). */
declare const llmindexSchema: object;
/** The full JSON Schema object for v0.1 (Draft-07). */
declare const llmindexSchemaV01: object;
/** The full JSON Schema object for v0.2 (Draft-07). */
declare const llmindexSchemaV02: object;

export default llmindexSchema;
export { llmindexSchema, llmindexSchemaV01, llmindexSchemaV02 };
