# Test Vectors

Negative test cases for llmindex v0.1 schema validation.

## Files

| File | Expected Result | Description |
|------|----------------|-------------|
| `invalid-missing-required.json` | FAIL | Missing `version` field and `entity.canonical_url` |
| `invalid-bad-urls.json` | FAIL | `canonical_url` uses ftp://, endpoints contain non-URL strings |
| `invalid-bad-dates.json` | FAIL | `updated_at` is not a valid ISO 8601 datetime |
| `invalid-feed.jsonl` | FAIL (per line) | Line 1: broken JSON; Line 2: missing `url` and `price`/`price_range`; Line 3: empty `id`/`title`, invalid `availability`; Line 4: `price` is string, bad `updated_at` |

## Usage

These vectors should be used by the validator to verify that:
1. Schema validation correctly rejects invalid manifests
2. Feed validation correctly identifies malformed JSONL lines
3. Error messages include specific field names and expected formats
