"""Tests for llmindex Spec: JSON Schema validation of examples and test vectors."""

import json
from pathlib import Path

import jsonschema
import pytest

SPEC_DIR = Path(__file__).resolve().parent.parent.parent / "spec"
SCHEMA_PATH = SPEC_DIR / "schemas" / "llmindex-0.1.schema.json"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


class TestExamplesValidation:
    """All examples in spec/examples/ must validate against the schema."""

    @pytest.mark.parametrize(
        "example_name",
        ["ecommerce", "local-business", "saas", "blog", "restaurant", "marketplace"],
    )
    def test_example_validates(self, schema, example_name):
        path = SPEC_DIR / "examples" / example_name / "llmindex.json"
        data = json.loads(path.read_text())
        jsonschema.validate(data, schema)  # raises on failure


class TestTestVectors:
    """Test vectors in spec/test-vectors/ must match expected validity."""

    @pytest.mark.parametrize(
        "vector_name",
        ["valid-minimal", "valid-with-verify"],
    )
    def test_valid_manifest_accepted(self, schema, vector_name):
        path = SPEC_DIR / "test-vectors" / f"{vector_name}.json"
        data = json.loads(path.read_text())
        jsonschema.validate(data, schema)  # raises on failure

    @pytest.mark.parametrize(
        "vector_name",
        [
            "invalid-missing-required",
            "invalid-bad-urls",
            "invalid-bad-dates",
            "invalid-extra-fields",
            "invalid-http-url",
        ],
    )
    def test_invalid_manifest_rejected(self, schema, vector_name):
        path = SPEC_DIR / "test-vectors" / f"{vector_name}.json"
        data = json.loads(path.read_text())
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema)


class TestSchemaStructure:
    """Verify schema has expected required fields and structure."""

    def test_required_fields(self, schema):
        assert set(schema["required"]) == {
            "version",
            "updated_at",
            "entity",
            "language",
            "topics",
            "endpoints",
        }

    def test_endpoints_required(self, schema):
        ep = schema["properties"]["endpoints"]
        assert set(ep["required"]) == {"products", "policies", "faq", "about"}

    def test_entity_required(self, schema):
        ent = schema["properties"]["entity"]
        assert set(ent["required"]) == {"name", "canonical_url"}

    def test_version_const(self, schema):
        assert schema["properties"]["version"]["const"] == "0.1"

    def test_no_additional_properties(self, schema):
        assert schema["additionalProperties"] is False

    def test_product_line_schema_exists(self, schema):
        assert "product_line" in schema["definitions"]
        pl = schema["definitions"]["product_line"]
        assert "id" in pl["properties"]
        assert "title" in pl["properties"]
        assert "url" in pl["properties"]
        assert "availability" in pl["properties"]
