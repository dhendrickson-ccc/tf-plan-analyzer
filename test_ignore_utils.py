#!/usr/bin/env python3
"""
Unit tests for ignore_utils module.

Tests all functions in ignore_utils.py with various scenarios including:
- Valid and invalid JSON configurations
- Global and resource-specific ignore rules
- Nested attribute handling with dot notation
- Edge cases and error conditions
"""

import json
import pytest
from pathlib import Path
from ignore_utils import (
    load_ignore_config,
    apply_ignore_config,
    get_ignored_attributes,
    supports_dot_notation
)


class TestLoadIgnoreConfig:
    """Tests for load_ignore_config function."""
    
    def test_valid_json_with_all_fields(self, tmp_path):
        """Test loading valid JSON with both global and resource-specific ignores."""
        config_file = tmp_path / "test_config.json"
        config_data = {
            "global_ignores": {
                "tags": "Tags managed separately"
            },
            "resource_ignores": {
                "azurerm_monitor_metric_alert": {
                    "description": "Conditionally set by environment"
                }
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        result = load_ignore_config(config_file)
        
        assert result == config_data
        assert "global_ignores" in result
        assert "resource_ignores" in result
    
    def test_valid_json_list_format(self, tmp_path):
        """Test loading config with list format for ignores."""
        config_file = tmp_path / "test_config.json"
        config_data = {
            "global_ignores": ["tags", "metadata"],
            "resource_ignores": {
                "azurerm_resource": ["field1", "field2"]
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        result = load_ignore_config(config_file)
        
        assert result == config_data
        assert isinstance(result["global_ignores"], list)
    
    def test_empty_config(self, tmp_path):
        """Test loading empty but valid JSON config."""
        config_file = tmp_path / "empty_config.json"
        config_file.write_text("{}")
        
        result = load_ignore_config(config_file)
        
        assert result == {}
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_ignore_config(Path("/nonexistent/config.json"))
        
        assert "not found" in str(exc_info.value)
    
    def test_malformed_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        config_file = tmp_path / "malformed.json"
        config_file.write_text("{invalid json content")
        
        with pytest.raises(json.JSONDecodeError) as exc_info:
            load_ignore_config(config_file)
        
        assert "Malformed JSON" in str(exc_info.value)
    
    def test_invalid_root_type(self, tmp_path):
        """Test that ValueError is raised if root is not a dict."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text('["not", "a", "dict"]')
        
        with pytest.raises(ValueError) as exc_info:
            load_ignore_config(config_file)
        
        assert "must be a JSON object" in str(exc_info.value)
    
    def test_invalid_global_ignores_type(self, tmp_path):
        """Test that ValueError is raised if global_ignores is wrong type."""
        config_file = tmp_path / "invalid.json"
        config_data = {"global_ignores": "string_not_allowed"}
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ValueError) as exc_info:
            load_ignore_config(config_file)
        
        assert "global_ignores" in str(exc_info.value)
    
    def test_invalid_resource_ignores_type(self, tmp_path):
        """Test that ValueError is raised if resource_ignores is wrong type."""
        config_file = tmp_path / "invalid.json"
        config_data = {"resource_ignores": ["list_not_allowed"]}
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ValueError) as exc_info:
            load_ignore_config(config_file)
        
        assert "resource_ignores" in str(exc_info.value)
    
    def test_invalid_resource_fields_type(self, tmp_path):
        """Test that ValueError is raised if resource fields are wrong type."""
        config_file = tmp_path / "invalid.json"
        config_data = {
            "resource_ignores": {
                "azurerm_resource": "string_not_allowed"
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ValueError) as exc_info:
            load_ignore_config(config_file)
        
        assert "must be a dict or list" in str(exc_info.value)


class TestApplyIgnoreConfig:
    """Tests for apply_ignore_config function."""
    
    def test_global_ignore_removes_attribute(self):
        """Test that global ignore rules remove attributes."""
        config = {"name": "test", "tags": {"env": "dev"}, "location": "eastus"}
        rules = {"global_ignores": ["tags"]}
        
        result = apply_ignore_config(config, rules, "azurerm_resource")
        
        assert "tags" not in result
        assert result["name"] == "test"
        assert result["location"] == "eastus"
    
    def test_global_ignore_dict_format(self):
        """Test global ignore with dict format (with reasons)."""
        config = {"name": "test", "tags": {"env": "dev"}, "metadata": "info"}
        rules = {
            "global_ignores": {
                "tags": "Managed separately",
                "metadata": "Auto-generated"
            }
        }
        
        result = apply_ignore_config(config, rules, "azurerm_resource")
        
        assert "tags" not in result
        assert "metadata" not in result
        assert result["name"] == "test"
    
    def test_resource_specific_ignore(self):
        """Test resource-specific ignore rules."""
        config = {"name": "alert", "description": "Test alert", "enabled": True}
        rules = {
            "resource_ignores": {
                "azurerm_monitor_metric_alert": ["description"]
            }
        }
        
        result = apply_ignore_config(config, rules, "azurerm_monitor_metric_alert")
        
        assert "description" not in result
        assert result["name"] == "alert"
        assert result["enabled"] is True
    
    def test_resource_specific_ignore_wrong_type(self):
        """Test that resource-specific rules don't apply to wrong resource type."""
        config = {"name": "test", "description": "Should remain"}
        rules = {
            "resource_ignores": {
                "azurerm_monitor_metric_alert": ["description"]
            }
        }
        
        result = apply_ignore_config(config, rules, "azurerm_other_resource")
        
        assert "description" in result  # Not removed for different resource type
        assert result["description"] == "Should remain"
    
    def test_combined_global_and_resource_specific(self):
        """Test combining global and resource-specific ignore rules."""
        config = {
            "name": "test",
            "tags": {"env": "dev"},
            "description": "Test",
            "location": "eastus"
        }
        rules = {
            "global_ignores": ["tags"],
            "resource_ignores": {
                "azurerm_resource": ["description"]
            }
        }
        
        result = apply_ignore_config(config, rules, "azurerm_resource")
        
        assert "tags" not in result
        assert "description" not in result
        assert result["name"] == "test"
        assert result["location"] == "eastus"
    
    def test_nested_attribute_ignore(self):
        """Test ignoring nested attributes with dot notation."""
        config = {
            "name": "test",
            "identity": {
                "type": "SystemAssigned",
                "principal_id": "12345"
            }
        }
        rules = {"global_ignores": ["identity.type"]}
        
        result = apply_ignore_config(config, rules, "azurerm_resource")
        
        assert "identity" in result
        assert "type" not in result["identity"]
        assert result["identity"]["principal_id"] == "12345"
    
    def test_ignore_nonexistent_attribute(self):
        """Test that ignoring nonexistent attribute doesn't cause error."""
        config = {"name": "test", "location": "eastus"}
        rules = {"global_ignores": ["nonexistent_field"]}
        
        result = apply_ignore_config(config, rules, "azurerm_resource")
        
        assert result == config  # Nothing removed
    
    def test_empty_ignore_rules(self):
        """Test that empty ignore rules return unchanged config."""
        config = {"name": "test", "tags": {"env": "dev"}}
        rules = {}
        
        result = apply_ignore_config(config, rules, "azurerm_resource")
        
        assert result == config
    
    def test_does_not_modify_original(self):
        """Test that original config is not modified."""
        original = {"name": "test", "tags": {"env": "dev"}}
        config = original.copy()
        rules = {"global_ignores": ["tags"]}
        
        result = apply_ignore_config(config, rules, "azurerm_resource")
        
        assert "tags" in original  # Original unchanged
        assert "tags" not in result


class TestGetIgnoredAttributes:
    """Tests for get_ignored_attributes function."""
    
    def test_returns_only_present_attributes(self):
        """Test that only attributes present in config are returned."""
        config = {"name": "test", "tags": {"env": "dev"}}
        rules = {"global_ignores": ["tags", "missing_field", "another_missing"]}
        
        result = get_ignored_attributes(config, rules, "azurerm_resource")
        
        assert result == {"tags"}
        assert "missing_field" not in result
    
    def test_global_and_resource_specific(self):
        """Test combining global and resource-specific ignored attributes."""
        config = {"name": "test", "tags": {"env": "dev"}, "description": "Test"}
        rules = {
            "global_ignores": ["tags"],
            "resource_ignores": {
                "azurerm_resource": ["description"]
            }
        }
        
        result = get_ignored_attributes(config, rules, "azurerm_resource")
        
        assert result == {"tags", "description"}
    
    def test_nested_attributes(self):
        """Test with nested attribute dot notation."""
        config = {
            "name": "test",
            "identity": {
                "type": "SystemAssigned",
                "principal_id": "12345"
            }
        }
        rules = {"global_ignores": ["identity.type", "identity.missing"]}
        
        result = get_ignored_attributes(config, rules, "azurerm_resource")
        
        assert result == {"identity.type"}
        assert "identity.missing" not in result
    
    def test_empty_config(self):
        """Test with empty resource config."""
        config = {}
        rules = {"global_ignores": ["tags", "description"]}
        
        result = get_ignored_attributes(config, rules, "azurerm_resource")
        
        assert result == set()
    
    def test_empty_rules(self):
        """Test with empty ignore rules."""
        config = {"name": "test", "tags": {"env": "dev"}}
        rules = {}
        
        result = get_ignored_attributes(config, rules, "azurerm_resource")
        
        assert result == set()
    
    def test_dict_format_ignores(self):
        """Test with dict format (with reasons) for ignore rules."""
        config = {"name": "test", "tags": {"env": "dev"}, "metadata": "info"}
        rules = {
            "global_ignores": {
                "tags": "Managed separately",
                "metadata": "Auto-generated",
                "missing": "Not present"
            }
        }
        
        result = get_ignored_attributes(config, rules, "azurerm_resource")
        
        assert result == {"tags", "metadata"}
        assert "missing" not in result


class TestSupportsDotNotation:
    """Tests for supports_dot_notation function."""
    
    def test_top_level_attribute_exists(self):
        """Test checking for top-level attribute that exists."""
        config = {"name": "test", "tags": {"env": "dev"}}
        
        assert supports_dot_notation("name", config) is True
        assert supports_dot_notation("tags", config) is True
    
    def test_top_level_attribute_missing(self):
        """Test checking for top-level attribute that doesn't exist."""
        config = {"name": "test"}
        
        assert supports_dot_notation("missing", config) is False
    
    def test_nested_attribute_exists(self):
        """Test checking for nested attribute that exists."""
        config = {
            "identity": {
                "type": "SystemAssigned",
                "principal_id": "12345"
            }
        }
        
        assert supports_dot_notation("identity.type", config) is True
        assert supports_dot_notation("identity.principal_id", config) is True
    
    def test_nested_attribute_missing(self):
        """Test checking for nested attribute that doesn't exist."""
        config = {
            "identity": {
                "type": "SystemAssigned"
            }
        }
        
        assert supports_dot_notation("identity.missing", config) is False
    
    def test_deeply_nested_attribute(self):
        """Test checking for deeply nested attribute."""
        config = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        assert supports_dot_notation("level1.level2.level3", config) is True
        assert supports_dot_notation("level1.level2.missing", config) is False
    
    def test_parent_not_dict(self):
        """Test when parent in path is not a dict."""
        config = {
            "name": "test_string"
        }
        
        assert supports_dot_notation("name.type", config) is False
    
    def test_empty_path(self):
        """Test with empty attribute path."""
        config = {"name": "test"}
        
        assert supports_dot_notation("", config) is False
    
    def test_empty_config(self):
        """Test with empty config."""
        assert supports_dot_notation("name", {}) is False
    
    def test_none_config(self):
        """Test with None config."""
        assert supports_dot_notation("name", None) is False
