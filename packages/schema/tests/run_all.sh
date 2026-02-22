#!/usr/bin/env bash
# Run all @llmindex/schema npm package tests
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PKG="$(dirname "$DIR")"

echo "=============================="
echo "@llmindex/schema Test Suite"
echo "=============================="
echo

cd "$PKG"

# Ensure dependencies
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install ajv ajv-formats 2>/dev/null || true
fi

PASS=0
FAIL=0

run_test() {
  local label="$1"
  local cmd="$2"
  echo "--- $label ---"
  if eval "$cmd"; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "  ^^^ FAILED ^^^"
  fi
  echo
}

run_test "CJS require()" "node tests/test_cjs_require.cjs"
run_test "Schema fields" "node tests/test_schema_fields.mjs"
run_test "Ajv edge cases" "node tests/test_ajv_edge_cases.mjs"
run_test "Product-line" "node tests/test_product_line.mjs"
run_test "Examples (validate.mjs)" "node ../../examples/validate.mjs"

echo "=============================="
echo "Results: $PASS suites passed, $FAIL suites failed"
echo "=============================="

exit $FAIL
