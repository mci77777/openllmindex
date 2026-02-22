/**
 * Test: Schema property coverage
 *
 * Verifies that v0.1 and v0.2 schemas contain all expected properties
 * and definitions.
 */
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import assert from "assert";

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemasDir = join(__dirname, "..", "schemas");

const v01 = JSON.parse(readFileSync(join(schemasDir, "llmindex-0.1.schema.json"), "utf-8"));
const v02 = JSON.parse(readFileSync(join(schemasDir, "llmindex-0.2.schema.json"), "utf-8"));

// --- v0.1 required properties ---
const v01Required = ["version", "updated_at", "entity", "language", "topics", "endpoints"];
for (const field of v01Required) {
  assert.ok(v01.properties[field], `v0.1 has property: ${field}`);
  assert.ok(v01.required.includes(field), `v0.1 requires: ${field}`);
}

// --- v0.1 optional properties ---
const v01Optional = ["feeds", "verify", "sig", "license"];
for (const field of v01Optional) {
  assert.ok(v01.properties[field], `v0.1 has optional property: ${field}`);
  assert.ok(!v01.required.includes(field), `v0.1 does not require: ${field}`);
}

// --- v0.2 required properties (same as v0.1) ---
for (const field of v01Required) {
  assert.ok(v02.properties[field], `v0.2 has property: ${field}`);
  assert.ok(v02.required.includes(field), `v0.2 requires: ${field}`);
}

// --- v0.2 new optional properties ---
const v02New = ["feed_updated_at", "languages", "localized_endpoints"];
for (const field of v02New) {
  assert.ok(v02.properties[field], `v0.2 has new property: ${field}`);
  assert.ok(!v02.required.includes(field), `v0.2 does not require: ${field}`);
}

// --- Entity sub-schema ---
for (const s of [v01, v02]) {
  const entity = s.properties.entity;
  assert.ok(entity.properties.name, "entity has name");
  assert.ok(entity.properties.canonical_url, "entity has canonical_url");
  assert.deepStrictEqual(entity.required, ["name", "canonical_url"]);
}

// --- Endpoints sub-schema ---
for (const s of [v01, v02]) {
  const ep = s.properties.endpoints;
  for (const key of ["products", "policies", "faq", "about"]) {
    assert.ok(ep.properties[key], `endpoints has ${key}`);
  }
  assert.deepStrictEqual(ep.required.sort(), ["about", "faq", "policies", "products"]);
}

// --- Version const ---
assert.strictEqual(v01.properties.version.const, "0.1");
assert.strictEqual(v02.properties.version.const, "0.2");

// --- product-line schema ---
const pl = JSON.parse(readFileSync(join(schemasDir, "product-line-0.1.schema.json"), "utf-8"));
const plRequired = ["id", "title", "url", "availability", "updated_at"];
for (const field of plRequired) {
  assert.ok(pl.properties[field], `product-line has: ${field}`);
  assert.ok(pl.required.includes(field), `product-line requires: ${field}`);
}

console.log("Schema fields: all assertions passed");
