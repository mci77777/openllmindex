/**
 * llmindex v0.1 Manifest Schema — TypeScript type definitions.
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

/** Optional machine-readable data feeds. */
export interface LlmindexFeeds {
  products_jsonl?: string;
  offers_json?: string;
}

/** The llmindex v0.1 manifest. */
export interface LlmindexManifest {
  /** Spec version. Always "0.1". */
  version: "0.1";
  /** ISO 8601 datetime of last update. */
  updated_at: string;
  /** Entity information. */
  entity: LlmindexEntity;
  /** Primary language (BCP-47). */
  language: string;
  /** Category tags. */
  topics: string[];
  /** Required endpoint URLs. */
  endpoints: LlmindexEndpoints;
  /** Optional data feeds. */
  feeds?: LlmindexFeeds;
  /** Domain verification. */
  verify?: LlmindexVerify;
  /** Cryptographic signature. */
  sig?: LlmindexSig;
  /** SPDX license identifier or URL. */
  license?: string;
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

/** The full JSON Schema object (Draft-07). */
declare const llmindexSchema: object;

export default llmindexSchema;
export { llmindexSchema };
