# Test Vectors

Positive and negative test cases for llmindex v0.1 schema validation.

## Files

| File | Expected Result | Description |
|------|----------------|-------------|
| `valid-minimal.json` | PASS | Minimal valid manifest with only required fields |
| `valid-with-verify.json` | PASS | Valid manifest including `verify` field (`dns_txt`) |
| `invalid-missing-required.json` | FAIL | Missing `version` field and `entity.canonical_url` |
| `invalid-bad-urls.json` | FAIL | `canonical_url` uses ftp://, endpoints contain non-URL strings |
| `invalid-bad-dates.json` | FAIL | `updated_at` is not a valid ISO 8601 datetime |
| `invalid-extra-fields.json` | FAIL | Unknown top-level field present (tests `additionalProperties: false`) |
| `invalid-http-url.json` | FAIL | `entity.canonical_url` uses http:// instead of https:// |
| `invalid-feed.jsonl` | FAIL (per line) | Line 1: broken JSON; Line 2: missing `url` and `price`/`price_range`; Line 3: empty `id`/`title`, invalid `availability`; Line 4: `price` is string, bad `updated_at` |

## Usage

These vectors should be used by the validator to verify that:
1. Schema validation correctly accepts valid manifests
2. Schema validation correctly rejects invalid manifests
3. Feed validation correctly identifies malformed JSONL lines
4. Error messages include specific field names and expected formats
