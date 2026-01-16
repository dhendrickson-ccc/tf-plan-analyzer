#!/usr/bin/env python3
"""
Unit tests for normalization_utils module.

Tests normalization configuration loading, validation, and pattern application
following the TDD approach for feature 007 (normalization-based difference filtering).
"""

import json
import pytest
import re
from pathlib import Path
from src.lib.normalization_utils import (
    load_normalization_config,
    NormalizationConfig,
    NormalizationPattern,
)


class TestLoadNormalizationConfig:
    """Tests for load_normalization_config function."""

    def test_load_valid_config(self, tmp_path):
        """Test loading valid normalization config with all fields."""
        config_file = tmp_path / "normalizations.json"
        config_data = {
            "name_patterns": [
                {
                    "pattern": "-(dev|test)-",
                    "replacement": "-ENV-",
                    "description": "Environment suffix"
                },
                {
                    "pattern": "-(prod|p)-",
                    "replacement": "-ENV-",
                    "description": "Production suffix"
                }
            ],
            "resource_id_patterns": [
                {
                    "pattern": "/subscriptions/[0-9a-f-]+/",
                    "replacement": "/subscriptions/SUB_ID/",
                    "description": "Azure subscription ID"
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))

        result = load_normalization_config(config_file)

        assert isinstance(result, NormalizationConfig)
        assert len(result.name_patterns) == 2
        assert len(result.resource_id_patterns) == 1
        assert result.source_file == config_file
        
        # Verify patterns are compiled
        assert isinstance(result.name_patterns[0].pattern, re.Pattern)
        assert result.name_patterns[0].replacement == "-ENV-"
        assert result.name_patterns[0].description == "Environment suffix"

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        config_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_normalization_config(config_file)

        assert "not found" in str(exc_info.value)
        assert "Hint:" in str(exc_info.value)

    def test_malformed_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        config_file = tmp_path / "malformed.json"
        config_file.write_text("{invalid json content")

        with pytest.raises(json.JSONDecodeError) as exc_info:
            load_normalization_config(config_file)

        assert "Failed to parse" in str(exc_info.value)

    def test_invalid_regex_pattern(self, tmp_path):
        """Test that ValueError is raised for invalid regex pattern."""
        config_file = tmp_path / "invalid_pattern.json"
        config_data = {
            "name_patterns": [
                {
                    "pattern": "[invalid(regex",  # unclosed bracket
                    "replacement": "REPLACED"
                }
            ],
            "resource_id_patterns": []
        }
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError) as exc_info:
            load_normalization_config(config_file)

        # Should include pattern index and the problematic pattern
        error_msg = str(exc_info.value)
        assert "pattern" in error_msg.lower()
        assert "index 0" in error_msg.lower() or "[invalid(regex" in error_msg

    def test_empty_pattern_arrays(self, tmp_path):
        """Test that ValueError is raised if both pattern arrays are missing."""
        config_file = tmp_path / "empty.json"
        config_data = {}  # Missing both arrays
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError) as exc_info:
            load_normalization_config(config_file)

        assert "at least one" in str(exc_info.value).lower()

    def test_only_name_patterns(self, tmp_path):
        """Test that config can have only name_patterns (resource_id_patterns optional)."""
        config_file = tmp_path / "only_name.json"
        config_data = {
            "name_patterns": [
                {"pattern": "-(dev)-", "replacement": "-ENV-"}
            ]
        }
        config_file.write_text(json.dumps(config_data))

        result = load_normalization_config(config_file)

        assert len(result.name_patterns) == 1
        assert len(result.resource_id_patterns) == 0

    def test_only_resource_id_patterns(self, tmp_path):
        """Test that config can have only resource_id_patterns (name_patterns optional)."""
        config_file = tmp_path / "only_resource_id.json"
        config_data = {
            "resource_id_patterns": [
                {"pattern": "/sub/[^/]+/", "replacement": "/sub/ID/"}
            ]
        }
        config_file.write_text(json.dumps(config_data))

        result = load_normalization_config(config_file)

        assert len(result.name_patterns) == 0
        assert len(result.resource_id_patterns) == 1

    def test_missing_pattern_field(self, tmp_path):
        """Test that ValueError is raised if pattern object missing 'pattern' field."""
        config_file = tmp_path / "missing_field.json"
        config_data = {
            "name_patterns": [
                {
                    "replacement": "REPLACED"
                    # missing 'pattern' field
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError) as exc_info:
            load_normalization_config(config_file)

        assert "pattern" in str(exc_info.value).lower()

    def test_missing_replacement_field(self, tmp_path):
        """Test that ValueError is raised if pattern object missing 'replacement' field."""
        config_file = tmp_path / "missing_replacement.json"
        config_data = {
            "name_patterns": [
                {
                    "pattern": "-(dev)-"
                    # missing 'replacement' field
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError) as exc_info:
            load_normalization_config(config_file)

        assert "replacement" in str(exc_info.value).lower()

    def test_description_field_optional(self, tmp_path):
        """Test that 'description' field is optional and gets auto-generated."""
        config_file = tmp_path / "no_description.json"
        config_data = {
            "name_patterns": [
                {
                    "pattern": "-(dev)-",
                    "replacement": "-ENV-"
                    # no description field
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))

        result = load_normalization_config(config_file)

        assert len(result.name_patterns) == 1
        # Should have auto-generated description
        assert "Pattern:" in result.name_patterns[0].description
        assert "-(dev)-" in result.name_patterns[0].description
        assert "-ENV-" in result.name_patterns[0].description


class TestApplyNormalizationPatterns:
    """Tests for apply_normalization_patterns function."""

    def test_apply_single_pattern(self):
        """Test applying a single normalization pattern."""
        from src.lib.normalization_utils import apply_normalization_patterns
        
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r"-(dev|test)-"),
                replacement="-ENV-",
                description="Environment suffix",
                original_pattern="-(dev|test)-"
            )
        ]
        
        # Should match and replace
        result = apply_normalization_patterns("storage-dev-eastus", patterns)
        assert result == "storage-ENV-eastus"
        
        result = apply_normalization_patterns("storage-test-westus", patterns)
        assert result == "storage-ENV-westus"

    def test_apply_multiple_patterns_in_order(self):
        """Test that patterns are applied in order (each pattern runs once via regex.sub)."""
        from src.lib.normalization_utils import apply_normalization_patterns
        
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r"-(dev|test|t)-"),
                replacement="-ENV-",
                description="Environment suffix",
                original_pattern="-(dev|test|t)-"
            ),
            NormalizationPattern(
                pattern=re.compile(r"(eastus|westus|centralus)"),
                replacement="REGION",
                description="Azure region",
                original_pattern="(eastus|westus|centralus)"
            )
        ]
        
        # Both patterns should apply
        result = apply_normalization_patterns("storage-dev-eastus", patterns)
        assert result == "storage-ENV-REGION"
        
        # First pattern applies, second applies to result
        result = apply_normalization_patterns("app-test-westus", patterns)
        assert result == "app-ENV-REGION"

    def test_no_match_returns_original(self):
        """Test that original value is returned when no patterns match."""
        from src.lib.normalization_utils import apply_normalization_patterns
        
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r"-(dev|test)-"),
                replacement="-ENV-",
                description="Environment suffix",
                original_pattern="-(dev|test)-"
            )
        ]
        
        # Should not match
        result = apply_normalization_patterns("storage-prod-eastus", patterns)
        assert result == "storage-prod-eastus"  # unchanged

    def test_empty_pattern_list_returns_original(self):
        """Test that empty pattern list returns original value."""
        from src.lib.normalization_utils import apply_normalization_patterns
        
        result = apply_normalization_patterns("any-value-here", [])
        assert result == "any-value-here"

    def test_pattern_with_groups(self):
        """Test pattern with capture groups works correctly."""
        from src.lib.normalization_utils import apply_normalization_patterns
        
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r"/subscriptions/[0-9a-f-]+/"),
                replacement="/subscriptions/SUB_ID/",
                description="Subscription ID",
                original_pattern="/subscriptions/[0-9a-f-]+/"
            )
        ]
        
        result = apply_normalization_patterns(
            "/subscriptions/abc-123-def/resourceGroups/rg-test",
            patterns
        )
        assert result == "/subscriptions/SUB_ID/resourceGroups/rg-test"


class TestNormalizeAttributeValue:
    """Tests for normalize_attribute_value function."""

    def test_normalize_string_value(self):
        """Test normalizing a string attribute value."""
        from src.lib.normalization_utils import normalize_attribute_value, NormalizationConfig
        
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r"-(dev|test)-"),
                replacement="-ENV-",
                description="Environment suffix",
                original_pattern="-(dev|test)-"
            )
        ]
        
        config = NormalizationConfig(
            name_patterns=patterns,
            resource_id_patterns=[],
            source_file=Path("/fake/path.json")
        )
        
        # String value should be normalized
        result = normalize_attribute_value("name", "storage-dev-eastus", config)
        assert result == "storage-ENV-eastus"

    def test_non_string_value_unchanged(self):
        """Test that non-string values are returned unchanged."""
        from src.lib.normalization_utils import normalize_attribute_value, NormalizationConfig
        
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r"-(dev)-"),
                replacement="-ENV-",
                description="Environment suffix",
                original_pattern="-(dev)-"
            )
        ]
        
        config = NormalizationConfig(
            name_patterns=patterns,
            resource_id_patterns=[],
            source_file=Path("/fake/path.json")
        )
        
        # Integer value should be unchanged
        result = normalize_attribute_value("count", 42, config)
        assert result == 42
        
        # Boolean value should be unchanged
        result = normalize_attribute_value("enabled", True, config)
        assert result is True
        
        # None value should be unchanged
        result = normalize_attribute_value("optional", None, config)
        assert result is None
        
        # Dict value should be unchanged
        result = normalize_attribute_value("tags", {"env": "dev"}, config)
        assert result == {"env": "dev"}

    def test_empty_string_value(self):
        """Test that empty string is returned unchanged."""
        from src.lib.normalization_utils import normalize_attribute_value, NormalizationConfig
        
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r"-(dev)-"),
                replacement="-ENV-",
                description="Environment suffix",
                original_pattern="-(dev)-"
            )
        ]
        
        config = NormalizationConfig(
            name_patterns=patterns,
            resource_id_patterns=[],
            source_file=Path("/fake/path.json")
        )
        
        result = normalize_attribute_value("name", "", config)
        assert result == ""

    def test_no_patterns_returns_original(self):
        """Test that value is returned unchanged when config has no patterns."""
        from src.lib.normalization_utils import normalize_attribute_value, NormalizationConfig
        
        config = NormalizationConfig(
            name_patterns=[],
            resource_id_patterns=[],
            source_file=Path("/fake/path.json")
        )
        
        result = normalize_attribute_value("name", "storage-dev-eastus", config)
        assert result == "storage-dev-eastus"


class TestConfigPrecedence:
    """Tests for config ignore precedence over normalization (FR-013)."""

    def test_config_ignored_takes_precedence(self):
        """Test that config-ignored attributes not counted as normalization-ignored."""
        # This test should FAIL until precedence logic is implemented
        pytest.skip("Not yet implemented - T025a")


# ==============================================================================
# User Story 2 Tests: Resource ID Transformation Normalization
# ==============================================================================


class TestClassifyAttribute:
    """Tests for classify_attribute function (T029)."""

    def test_detect_id_attribute(self):
        """Test detection of ID-like attribute names."""
        from src.lib.normalization_utils import classify_attribute
        
        # Should detect common ID patterns
        assert classify_attribute("id") == "resource_id"
        assert classify_attribute("resource_id") == "resource_id"
        assert classify_attribute("parent_id") == "resource_id"
        assert classify_attribute("subscription_id") == "resource_id"
        assert classify_attribute("tenant_id") == "resource_id"
        assert classify_attribute("app_service_plan_id") == "resource_id"
        assert classify_attribute("virtual_network_id") == "resource_id"

    def test_detect_name_attribute(self):
        """Test that non-ID attributes are classified as name."""
        from src.lib.normalization_utils import classify_attribute
        
        # Should classify normal attributes as name
        assert classify_attribute("name") == "name"
        assert classify_attribute("location") == "name"
        assert classify_attribute("resource_group_name") == "name"
        assert classify_attribute("tags") == "name"
        assert classify_attribute("identifier") == "name"  # Not ending in _id


class TestNormalizeResourceId:
    """Tests for normalize_resource_id function (T030-T032)."""

    def test_normalize_subscription_id(self):
        """Test normalization of Azure subscription GUID (T030)."""
        from src.lib.normalization_utils import normalize_resource_id, NormalizationPattern
        import re
        
        # Pattern to match Azure subscription GUIDs
        pattern = NormalizationPattern(
            pattern=re.compile(r'/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'),
            replacement='/subscriptions/SUBSCRIPTION_ID',
            description='Normalize subscription ID',
            original_pattern='/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        )
        
        resource_id = '/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/rg-test'
        result = normalize_resource_id(resource_id, [pattern])
        
        assert result == '/subscriptions/SUBSCRIPTION_ID/resourceGroups/rg-test'

    def test_normalize_tenant_id(self):
        """Test normalization of Azure tenant GUID (T031)."""
        from src.lib.normalization_utils import normalize_resource_id, NormalizationPattern
        import re
        
        # Pattern to match Azure tenant GUIDs
        pattern = NormalizationPattern(
            pattern=re.compile(r'/tenants/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'),
            replacement='/tenants/TENANT_ID',
            description='Normalize tenant ID',
            original_pattern='/tenants/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        )
        
        resource_id = '/tenants/87654321-4321-4321-4321-cba987654321/users/john'
        result = normalize_resource_id(resource_id, [pattern])
        
        assert result == '/tenants/TENANT_ID/users/john'

    def test_normalize_multiple_patterns_in_order(self):
        """Test that multiple patterns are applied in order (T032)."""
        from src.lib.normalization_utils import normalize_resource_id, NormalizationPattern
        import re
        
        # Multiple patterns - should apply in order
        patterns = [
            NormalizationPattern(
                pattern=re.compile(r'/subscriptions/[0-9a-f-]+'),
                replacement='/subscriptions/SUB_ID',
                description='Subscription ID',
                original_pattern='/subscriptions/[0-9a-f-]+'
            ),
            NormalizationPattern(
                pattern=re.compile(r'/resourceGroups/rg-(test|prod|dev)'),
                replacement='/resourceGroups/rg-ENV',
                description='Environment resource group',
                original_pattern='/resourceGroups/rg-(test|prod|dev)'
            )
        ]
        
        resource_id = '/subscriptions/abc-123/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/storage1'
        result = normalize_resource_id(resource_id, patterns)
        
        # Both patterns should be applied
        assert '/subscriptions/SUB_ID' in result
        assert '/resourceGroups/rg-ENV' in result
        assert result == '/subscriptions/SUB_ID/resourceGroups/rg-ENV/providers/Microsoft.Storage/storageAccounts/storage1'

    def test_no_match_returns_original(self):
        """Test that unmatched IDs are returned unchanged."""
        from src.lib.normalization_utils import normalize_resource_id, NormalizationPattern
        import re
        
        pattern = NormalizationPattern(
            pattern=re.compile(r'/subscriptions/[0-9a-f-]+'),
            replacement='/subscriptions/SUB_ID',
            description='Subscription ID',
            original_pattern='/subscriptions/[0-9a-f-]+'
        )
        
        # This ID doesn't match the pattern
        resource_id = '/custom/path/without/subscription'
        result = normalize_resource_id(resource_id, [pattern])
        
        assert result == resource_id
