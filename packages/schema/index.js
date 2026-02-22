"use strict";

const schemaV01 = require("./schemas/llmindex-0.1.schema.json");
const schemaV02 = require("./schemas/llmindex-0.2.schema.json");

module.exports = schemaV01;
module.exports.default = schemaV01;
module.exports.llmindexSchema = schemaV01;
module.exports.llmindexSchemaV01 = schemaV01;
module.exports.llmindexSchemaV02 = schemaV02;
