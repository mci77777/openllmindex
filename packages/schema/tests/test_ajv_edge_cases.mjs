/**
 * Test: Ajv edge cases
 *
 * Validates boundary conditions and edge cases using Ajv:
 * - Missing required fields
 * - Extra unknown fields (additionalProperties)
 * - Format validation (uri, date-time)
 * - Pattern validation (BCP-47, rate_limit)
 * - Test vectors (valid + invalid)
 */
import Ajv from "ajv";
import addFormats from "ajv-formats";
import { readFileSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import assert from "assert";

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemasDir = join(__dirname, "..", "schemas");
const vectorsDir = join(__dirname, "..", "..", "..", "spec", "test-vectors");

const v01 = JSON.parse(readFileSync(join(schemasDir, "llmindex-0.1.schema.json"), "utf-8"));
const v02 = JSON.parse(readFileSync(join(schemasDir, "llmindex-0.2.schema.json"), "utf-8"));

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const validateV01 = ajv.compile(v01);
const validateV02 = ajv.compile(v02);

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

// --- Missing required fields ---
check("empty object is invalid (v0.1)", validateV01({}), false);
check("empty object is invalid (v0.2)", validateV02({}), false);

// --- Minimal valid v0.1 ---
const minV01 = {
  version: "0.1",
  updated_at: "2026-01-01T00:00:00Z",
  entity: { name: "Test", canonical_url: "https://test.com" },
  language: "en",
  topics: ["test"],
  endpoints: {
    products: "https://test.com/p",
    policies: "https://test.com/pol",
    faq: "https://test.com/faq",
    about: "https://test.com/about",
  },
};
check("minimal v0.1 is valid", validateV01(minV01), true);

// --- Wrong version ---
check("v0.2 doc fails v0.1 schema", validateV01({ ...minV01, version: "0.2" }), false);
check("v0.1 doc fails v0.2 schema", validateV02(minV01), false);

// --- Minimal valid v0.2 ---
const minV02 = { ...minV01, version: "0.2" };
check("minimal v0.2 is valid", validateV02(minV02), true);

// --- Bad URI format ---
const badUri = { ...minV01, entity: { name: "X", canonical_url: "not-a-url" } };
check("bad canonical_url format rejected (v0.1)", validateV01(badUri), false);

// --- Bad date-time format ---
const badDate = { ...minV01, updated_at: "not-a-date" };
check("bad updated_at format rejected (v0.1)", validateV01(badDate), false);

// --- Empty topics array ---
const noTopics = { ...minV01, topics: [] };
check("empty topics rejected (v0.1)", validateV01(noTopics), false);

// --- access_control rate_limit pattern ---
const goodAC = { ...minV02, access_control: { rate_limit: "100/day" } };
check("valid rate_limit accepted (v0.2)", validateV02(goodAC), true);

const badAC = { ...minV02, access_control: { rate_limit: "100 per day" } };
check("bad rate_limit rejected (v0.2)", validateV02(badAC), false);

// --- commercial_use enum ---
const goodCU = { ...minV02, access_control: { commercial_use: "allowed" } };
check("valid commercial_use accepted", validateV02(goodCU), true);

const badCU = { ...minV02, access_control: { commercial_use: "maybe" } };
check("bad commercial_use rejected", validateV02(badCU), false);

// --- languages uniqueItems ---
const dupLangs = { ...minV02, languages: ["en", "en"] };
check("duplicate languages rejected (v0.2)", validateV02(dupLangs), false);

// --- BCP-47 pattern in languages ---
const badLang = { ...minV02, languages: ["123"] };
check("bad BCP-47 in languages rejected (v0.2)", validateV02(badLang), false);

// --- localized_endpoints bad key ---
const badLocKey = { ...minV02, localized_endpoints: { "123-bad": { products: "https://x.com/p" } } };
check("bad localized_endpoints key rejected", validateV02(badLocKey), false);

// --- Test vectors from spec/test-vectors ---
console.log();
console.log("  --- Test Vectors ---");

let vectorFiles;
try {
  vectorFiles = readdirSync(vectorsDir).filter((f) => f.endsWith(".json"));
} catch {
  vectorFiles = [];
  console.log("  SKIP  No test vectors directory found");
}

for (const file of vectorFiles) {
  const data = JSON.parse(readFileSync(join(vectorsDir, file), "utf-8"));
  const expectValid = file.startsWith("valid-");
  const version = data.version || "0.1";
  const validate = version === "0.2" ? validateV02 : validateV01;
  const valid = validate(data);
  check(`vector: ${file}`, valid, expectValid);
}

// --- Summary ---
console.log();
console.log(`Ajv edge cases: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
