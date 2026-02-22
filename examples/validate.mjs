/**
 * llmindex Schema Validation Example
 *
 * Demonstrates using @llmindex/schema to validate manifest files
 * against both v0.1 and v0.2 JSON Schemas.
 *
 * Usage:
 *   cd packages/schema && npm install ajv ajv-formats
 *   node ../../examples/validate.mjs
 *
 * Or from project root:
 *   node examples/validate.mjs
 */

import Ajv from "ajv";
import addFormats from "ajv-formats";
import { readFileSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

// Load schemas directly from spec/schemas (same as npm package)
const schemaV01 = JSON.parse(
  readFileSync(join(root, "spec/schemas/llmindex-0.1.schema.json"), "utf-8")
);
const schemaV02 = JSON.parse(
  readFileSync(join(root, "spec/schemas/llmindex-0.2.schema.json"), "utf-8")
);

// Set up Ajv
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const validateV01 = ajv.compile(schemaV01);
const validateV02 = ajv.compile(schemaV02);

// Discover all examples
const examplesDir = join(root, "spec/examples");
const industries = readdirSync(examplesDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

console.log("=".repeat(60));
console.log("llmindex Schema Validation (Node.js / Ajv)");
console.log("=".repeat(60));
console.log();

let passed = 0;
let failed = 0;

for (const industry of industries) {
  const manifestPath = join(examplesDir, industry, "llmindex.json");
  let data;
  try {
    data = JSON.parse(readFileSync(manifestPath, "utf-8"));
  } catch {
    continue; // skip if no manifest
  }

  const version = data.version || "unknown";
  const validate = version === "0.2" ? validateV02 : validateV01;
  const valid = validate(data);

  if (valid) {
    console.log(`  PASS  ${industry.padEnd(20)} (v${version})`);
    passed++;
  } else {
    console.log(`  FAIL  ${industry.padEnd(20)} (v${version})`);
    for (const err of validate.errors) {
      console.log(`        ${err.instancePath} ${err.message}`);
    }
    failed++;
  }
}

// Also validate test vectors
console.log();
console.log("-".repeat(60));
console.log("Test Vectors");
console.log("-".repeat(60));

const vectorsDir = join(root, "spec/test-vectors");
const vectors = readdirSync(vectorsDir).filter((f) => f.endsWith(".json"));

for (const file of vectors) {
  const data = JSON.parse(readFileSync(join(vectorsDir, file), "utf-8"));
  const expectValid = file.startsWith("valid-");
  const version = data.version || "0.1";
  const validate = version === "0.2" ? validateV02 : validateV01;
  const valid = validate(data);

  const match = valid === expectValid;
  const status = match ? "PASS" : "FAIL";
  const expectStr = expectValid ? "valid" : "invalid";

  console.log(`  ${status}  ${file.padEnd(35)} expected=${expectStr} got=${valid ? "valid" : "invalid"}`);
  if (match) passed++;
  else failed++;
}

console.log();
console.log("=".repeat(60));
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log("=".repeat(60));

process.exit(failed > 0 ? 1 : 0);
