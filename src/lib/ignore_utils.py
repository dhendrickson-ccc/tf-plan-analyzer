#!/usr/bin/env python3
"""
Ignore Configuration Utilities

Shared utilities for loading and applying ignore configuration rules
to filter out known acceptable differences in Terraform plan comparisons.

Supports both global ignore rules (applied to all resources) and
resource-specific ignore rules (applied to specific resource types).
"""

import json
from pathlib import Path
from typing import Dict, Set, Any, List


def load_ignore_config(file_path: Path) -> Dict:
    """
    Load and validate ignore configuration from a JSON file.

    Args:
        file_path: Path to the ignore configuration JSON file

    Returns:
        Dictionary containing ignore configuration with keys:
        - 'global_ignores': Dict[str, str] or List[str] - Attributes to ignore globally
        - 'resource_ignores': Dict[str, Dict[str, str] | List[str]] - Resource-specific ignores

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        json.JSONDecodeError: If the JSON is malformed

    Example:
        >>> config = load_ignore_config(Path('ignore_config.json'))
        >>> config['global_ignores']
        {'tags': 'Tags are managed separately'}
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Ignore configuration file not found: {file_path}")

    with open(file_path, "r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed JSON in ignore configuration file: {file_path}",
                e.doc,
                e.pos,
            ) from e

    # Validate basic structure (allow empty config)
    if not isinstance(config, dict):
        raise ValueError(
            f"Ignore configuration must be a JSON object, got {type(config).__name__}"
        )

    # Validate global_ignores if present
    if "global_ignores" in config:
        if not isinstance(config["global_ignores"], (dict, list)):
            raise ValueError(
                f"'global_ignores' must be a dict or list, got {type(config['global_ignores']).__name__}"
            )

    # Validate resource_ignores if present
    if "resource_ignores" in config:
        if not isinstance(config["resource_ignores"], dict):
            raise ValueError(
                f"'resource_ignores' must be a dict, got {type(config['resource_ignores']).__name__}"
            )
        for resource_type, fields in config["resource_ignores"].items():
            if not isinstance(fields, (dict, list)):
                raise ValueError(
                    f"Fields for resource '{resource_type}' must be a dict or list, "
                    f"got {type(fields).__name__}"
                )

    return config


def apply_ignore_config(
    resource_config: Dict, ignore_rules: Dict, resource_type: str
) -> Dict:
    """
    Apply ignore rules to a resource configuration, removing ignored attributes.

    Args:
        resource_config: The resource configuration dictionary to filter
        ignore_rules: The ignore configuration (from load_ignore_config)
        resource_type: The type of the resource (e.g., 'azurerm_monitor_metric_alert')

    Returns:
        A new dictionary with ignored attributes removed

    Example:
        >>> config = {'name': 'test', 'tags': {'env': 'dev'}, 'location': 'eastus'}
        >>> rules = {'global_ignores': ['tags']}
        >>> apply_ignore_config(config, rules, 'azurerm_resource')
        {'name': 'test', 'location': 'eastus'}
    """
    # Deep copy to avoid modifying original
    filtered_config = json.loads(json.dumps(resource_config))

    # Collect all attributes to ignore
    ignore_attributes: Set[str] = set()

    # Add global ignores
    if "global_ignores" in ignore_rules:
        global_ignores = ignore_rules["global_ignores"]
        if isinstance(global_ignores, list):
            ignore_attributes.update(global_ignores)
        elif isinstance(global_ignores, dict):
            ignore_attributes.update(global_ignores.keys())

    # Add resource-specific ignores
    if "resource_ignores" in ignore_rules:
        resource_ignores = ignore_rules["resource_ignores"].get(resource_type, {})
        if isinstance(resource_ignores, list):
            ignore_attributes.update(resource_ignores)
        elif isinstance(resource_ignores, dict):
            ignore_attributes.update(resource_ignores.keys())

    # Remove ignored attributes (handle both top-level and nested dot notation)
    for attr in ignore_attributes:
        if "." in attr:
            # Handle nested attributes (e.g., 'identity.type')
            _remove_nested_attribute(filtered_config, attr)
        else:
            # Top-level attribute
            filtered_config.pop(attr, None)

    return filtered_config


def get_ignored_attributes(
    resource_config: Dict, ignore_rules: Dict, resource_type: str
) -> Set[str]:
    """
    Get the set of attribute names that were actually ignored for a resource.

    Only returns attributes that were present in the resource configuration
    and matched by the ignore rules.

    Args:
        resource_config: The resource configuration dictionary
        ignore_rules: The ignore configuration (from load_ignore_config)
        resource_type: The type of the resource

    Returns:
        Set of attribute names that were actually ignored

    Example:
        >>> config = {'name': 'test', 'tags': {'env': 'dev'}}
        >>> rules = {'global_ignores': ['tags', 'missing_field']}
        >>> get_ignored_attributes(config, rules, 'azurerm_resource')
        {'tags'}
    """
    ignored_attributes: Set[str] = set()

    # Collect all potential ignore rules
    ignore_candidates: Set[str] = set()

    # Add global ignores
    if "global_ignores" in ignore_rules:
        global_ignores = ignore_rules["global_ignores"]
        if isinstance(global_ignores, list):
            ignore_candidates.update(global_ignores)
        elif isinstance(global_ignores, dict):
            ignore_candidates.update(global_ignores.keys())

    # Add resource-specific ignores
    if "resource_ignores" in ignore_rules:
        resource_ignores = ignore_rules["resource_ignores"].get(resource_type, {})
        if isinstance(resource_ignores, list):
            ignore_candidates.update(resource_ignores)
        elif isinstance(resource_ignores, dict):
            ignore_candidates.update(resource_ignores.keys())

    # Check which attributes are actually present in the config
    for attr in ignore_candidates:
        if supports_dot_notation(attr, resource_config):
            ignored_attributes.add(attr)

    return ignored_attributes


def supports_dot_notation(attribute_path: str, config: Dict) -> bool:
    """
    Check if an attribute path exists in a configuration dictionary.

    Supports dot notation for nested attributes (e.g., 'identity.type').

    Args:
        attribute_path: The attribute path to check (e.g., 'tags' or 'identity.type')
        config: The configuration dictionary to search

    Returns:
        True if the attribute exists at the specified path, False otherwise

    Example:
        >>> config = {'identity': {'type': 'SystemAssigned'}, 'name': 'test'}
        >>> supports_dot_notation('identity.type', config)
        True
        >>> supports_dot_notation('identity.missing', config)
        False
        >>> supports_dot_notation('name', config)
        True
    """
    if not attribute_path or not config:
        return False

    # Split on dots for nested attributes
    parts = attribute_path.split(".")
    current = config

    for part in parts:
        if not isinstance(current, dict):
            return False
        if part not in current:
            return False
        current = current[part]

    return True


def _remove_nested_attribute(config: Dict, attribute_path: str) -> None:
    """
    Remove a nested attribute from a configuration dictionary.

    Internal helper function that modifies the dictionary in place.

    Args:
        config: The configuration dictionary to modify
        attribute_path: The dot-notation path to remove (e.g., 'identity.type')
    """
    parts = attribute_path.split(".")
    if len(parts) == 1:
        # Top-level attribute
        config.pop(parts[0], None)
        return

    # Navigate to parent of target attribute
    current = config
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return  # Path doesn't exist, nothing to remove
        current = current[part]

    # Remove the final attribute
    if isinstance(current, dict):
        current.pop(parts[-1], None)
