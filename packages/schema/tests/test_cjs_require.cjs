/**
 * Test: CommonJS require() compatibility
 *
 * Verifies the npm package exports work correctly via require().
 */
"use strict";

const assert = require("assert");
const schema = require("../index");

// Default export is v0.1 schema
assert.ok(typeof schema === "object", "schema is an object");
assert.ok(schema.properties, "schema has properties (is a JSON Schema)");

// Named exports
assert.ok(schema.llmindexSchema, "llmindexSchema export exists");
assert.ok(schema.llmindexSchemaV01, "llmindexSchemaV01 export exists");
assert.ok(schema.llmindexSchemaV02, "llmindexSchemaV02 export exists");

// Default alias
assert.strictEqual(schema.default, schema.llmindexSchemaV01, "default === llmindexSchemaV01");

// V01 schema version
assert.strictEqual(
  schema.llmindexSchemaV01.properties.version.const,
  "0.1",
  "V01 schema version const is 0.1"
);

// V02 schema version
assert.strictEqual(
  schema.llmindexSchemaV02.properties.version.const,
  "0.2",
  "V02 schema version const is 0.2"
);

// V01 and V02 are different objects
assert.notStrictEqual(schema.llmindexSchemaV01, schema.llmindexSchemaV02, "V01 !== V02");

console.log("CJS require: all assertions passed");
