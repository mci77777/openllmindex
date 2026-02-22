/**
 * Test: product-line schema validation
 *
 * Validates product feed entries against product-line-0.1.schema.json.
 * Tests valid products, missing fields, bad formats, and price constraints.
 */
import Ajv from "ajv";
import addFormats from "ajv-formats";
import { readFileSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import assert from "assert";

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemasDir = join(__dirname, "..", "schemas");
const examplesDir = join(__dirname, "..", "..", "..", "spec", "examples");

const plSchema = JSON.parse(
  readFileSync(join(schemasDir, "product-line-0.1.schema.json"), "utf-8")
);

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const validate = ajv.compile(plSchema);

let passed = 0;
let failed = 0;

function check(label, result, expected) {
  if (result === expected) {
    console.log(`  PASS  ${label}`);
    passed++;
  } else {
    console.log(`  FAIL  ${label} (expected=${expected}, got=${result})`);
    failed++;
  }
}

// --- Minimal valid product (with price+currency) ---
const validProduct = {
  id: "prod-001",
  title: "Test Product",
  url: "https://example.com/products/001",
  price: 29.99,
  currency: "USD",
  availability: "in_stock",
  updated_at: "2026-01-01T00:00:00Z",
};
check("minimal product with price+currency", validate(validProduct), true);

// --- Valid product with price_range ---
const rangeProduct = {
  id: "prod-002",
  title: "Variable Product",
  url: "https://example.com/products/002",
  price_range: { min: 10, max: 50, currency: "EUR" },
  availability: "preorder",
  updated_at: "2026-02-01T00:00:00Z",
};
check("product with price_range", validate(rangeProduct), true);

// --- Full product (all optional fields) ---
const fullProduct = {
  ...validProduct,
  image_url: "https://example.com/img/001.jpg",
  brand: "TestBrand",
  category: "Electronics",
};
check("full product (all fields)", validate(fullProduct), true);

// --- Missing required fields ---
check("empty object rejected", validate({}), false);

const noId = { ...validProduct };
delete noId.id;
check("missing id rejected", validate(noId), false);

const noUrl = { ...validProduct };
delete noUrl.url;
check("missing url rejected", validate(noUrl), false);

const noAvail = { ...validProduct };
delete noAvail.availability;
check("missing availability rejected", validate(noAvail), false);

// --- Bad availability enum ---
const badAvail = { ...validProduct, availability: "discontinued" };
check("bad availability rejected", validate(badAvail), false);

// --- Bad URL format ---
const badUrl = { ...validProduct, url: "not-a-url" };
check("bad url format rejected", validate(badUrl), false);

// --- Bad date-time ---
const badDate = { ...validProduct, updated_at: "yesterday" };
check("bad updated_at format rejected", validate(badDate), false);

// --- Validate actual JSONL feed files ---
console.log();
console.log("  --- Feed File Validation ---");

const industries = readdirSync(examplesDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

for (const industry of industries) {
  const feedDir = join(examplesDir, industry, "feed");
  let files;
  try {
    files = readdirSync(feedDir).filter((f) => f.endsWith(".jsonl"));
  } catch {
    continue; // no feed dir
  }

  for (const file of files) {
    const lines = readFileSync(join(feedDir, file), "utf-8")
      .split("\n")
      .filter((l) => l.trim());
    let allValid = true;
    for (const line of lines) {
      const item = JSON.parse(line);
      if (!validate(item)) allValid = false;
    }
    check(`${industry}/feed/${file} (${lines.length} items)`, allValid, true);
  }
}

// --- Summary ---
console.log();
console.log(`Product-line: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
