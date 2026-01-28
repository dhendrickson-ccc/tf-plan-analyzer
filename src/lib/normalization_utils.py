#!/usr/bin/env python3
"""
Normalization Configuration Utilities

This module provides utilities for loading and applying normalization patterns
to filter environment-specific differences in Terraform plan comparisons.
"""

import json
import json5
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class NormalizationPattern:
    """
    Represents a single regex find/replace transformation.
    
    Attributes:
        pattern: Compiled regex pattern to match
        replacement: String to replace matches with (can include backreferences)
        description: Human-readable explanation of what the pattern does
        original_pattern: Original pattern string (for error messages and verbose logging)
    """
    pattern: re.Pattern
    replacement: str
    description: str
    original_pattern: str


@dataclass
class NormalizationConfig:
    """
    Stores pre-compiled regex patterns for efficient normalization during comparison.
    
    Attributes:
        name_patterns: Patterns for normalizing attribute names and values
        resource_id_patterns: Patterns for normalizing Azure resource IDs, subscription IDs, tenant IDs
        source_file: Path to the normalization config file (for error messages)
    """
    name_patterns: List[NormalizationPattern] = field(default_factory=list)
    resource_id_patterns: List[NormalizationPattern] = field(default_factory=list)
    source_file: Optional[Path] = None


def load_normalization_config(file_path: Path) -> NormalizationConfig:
    """
    Load and validate normalization configuration from JSON file.
    
    Args:
        file_path: Path to the normalization config file
        
    Returns:
        NormalizationConfig with pre-compiled regex patterns
        
    Raises:
        FileNotFoundError: Config file not found (with clear path in message)
        json.JSONDecodeError: Malformed JSON (with line/column info)
        ValueError: Invalid structure or regex patterns (with specific problem)
        
    Example:
        >>> config = load_normalization_config(Path('examples/normalizations.json'))
        >>> len(config.name_patterns) > 0
        True
    """
    # Check file exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Normalization config file not found: {file_path}\n"
            f"Hint: Check path in ignore_config.json 'normalization_config_path' field"
        )
    
    # Load and parse JSON
    try:
        with open(file_path, 'r') as f:
            config_dict = json5.load(f)
    except Exception as e:
        raise ValueError(
            f"Failed to parse normalization config file: {file_path}\n"
            f"Error: {str(e)}"
        ) from e
    
    # Validate structure
    if not isinstance(config_dict, dict):
        raise ValueError(
            f"Invalid normalization config: root must be an object, got {type(config_dict).__name__}"
        )
    
    # Must have at least one pattern array
    if 'name_patterns' not in config_dict and 'resource_id_patterns' not in config_dict:
        raise ValueError(
            "Invalid normalization config: must contain at least one of 'name_patterns' or 'resource_id_patterns'"
        )
    
    # Compile name patterns
    name_patterns = []
    if 'name_patterns' in config_dict:
        if not isinstance(config_dict['name_patterns'], list):
            raise ValueError(
                f"Invalid normalization config: 'name_patterns' must be an array, got {type(config_dict['name_patterns']).__name__}"
            )
        
        for idx, pattern_obj in enumerate(config_dict['name_patterns']):
            if not isinstance(pattern_obj, dict):
                raise ValueError(
                    f"Invalid normalization config: name_patterns[{idx}] must be an object, got {type(pattern_obj).__name__}"
                )
            
            # Validate required fields
            if 'pattern' not in pattern_obj:
                raise ValueError(
                    f"Invalid normalization config: missing required field 'pattern' at name_patterns[{idx}]\n"
                    f"Expected structure: {{'pattern': 'regex', 'replacement': 'text'}}"
                )
            
            if 'replacement' not in pattern_obj:
                raise ValueError(
                    f"Invalid normalization config: missing required field 'replacement' at name_patterns[{idx}]\n"
                    f"Expected structure: {{'pattern': 'regex', 'replacement': 'text'}}"
                )
            
            # Compile regex pattern
            pattern_str = pattern_obj['pattern']
            try:
                compiled_pattern = re.compile(pattern_str)
            except re.error as e:
                raise ValueError(
                    f"Invalid regex pattern at name_patterns[{idx}]: {pattern_str}\n"
                    f"Regex Error: {str(e)}\n"
                    f"Hint: Check pattern syntax. Test with: python -c \"import re; re.compile(r'{pattern_str}')\""
                )
            
            name_patterns.append(NormalizationPattern(
                pattern=compiled_pattern,
                replacement=pattern_obj['replacement'],
                description=pattern_obj.get('description', f"Pattern: {pattern_str} → {pattern_obj['replacement']}"),
                original_pattern=pattern_str
            ))
    
    # Compile resource_id patterns
    resource_id_patterns = []
    if 'resource_id_patterns' in config_dict:
        if not isinstance(config_dict['resource_id_patterns'], list):
            raise ValueError(
                f"Invalid normalization config: 'resource_id_patterns' must be an array, got {type(config_dict['resource_id_patterns']).__name__}"
            )
        
        for idx, pattern_obj in enumerate(config_dict['resource_id_patterns']):
            if not isinstance(pattern_obj, dict):
                raise ValueError(
                    f"Invalid normalization config: resource_id_patterns[{idx}] must be an object, got {type(pattern_obj).__name__}"
                )
            
            # Validate required fields
            if 'pattern' not in pattern_obj:
                raise ValueError(
                    f"Invalid normalization config: missing required field 'pattern' at resource_id_patterns[{idx}]\n"
                    f"Expected structure: {{'pattern': 'regex', 'replacement': 'text'}}"
                )
            
            if 'replacement' not in pattern_obj:
                raise ValueError(
                    f"Invalid normalization config: missing required field 'replacement' at resource_id_patterns[{idx}]\n"
                    f"Expected structure: {{'pattern': 'regex', 'replacement': 'text'}}"
                )
            
            # Compile regex pattern
            pattern_str = pattern_obj['pattern']
            try:
                compiled_pattern = re.compile(pattern_str)
            except re.error as e:
                raise ValueError(
                    f"Invalid regex pattern at resource_id_patterns[{idx}]: {pattern_str}\n"
                    f"Regex Error: {str(e)}\n"
                    f"Hint: Check pattern syntax. Test with: python -c \"import re; re.compile(r'{pattern_str}')\""
                )
            
            resource_id_patterns.append(NormalizationPattern(
                pattern=compiled_pattern,
                replacement=pattern_obj['replacement'],
                description=pattern_obj.get('description', f"Pattern: {pattern_str} → {pattern_obj['replacement']}"),
                original_pattern=pattern_str
            ))
    
    return NormalizationConfig(
        name_patterns=name_patterns,
        resource_id_patterns=resource_id_patterns,
        source_file=file_path
    )


def apply_normalization_patterns(
    value: str,
    patterns: List[NormalizationPattern],
    verbose: bool = False
) -> str:
    """
    Apply normalization patterns to a string value in order.
    
    Each pattern is applied once using regex.sub() (FR-011 first-match-wins strategy).
    Patterns are applied sequentially - each pattern operates on the result of the previous pattern.
    
    Args:
        value: String value to normalize
        patterns: List of NormalizationPattern objects to apply in order
        verbose: If True, log before/after values for debugging (FR-015)
        
    Returns:
        Normalized string with all patterns applied in sequence
        
    Example:
        >>> patterns = [
        ...     NormalizationPattern(re.compile(r"-(dev)-"), "-ENV-", "", "-(dev)-"),
        ...     NormalizationPattern(re.compile(r"eastus"), "REGION", "", "eastus")
        ... ]
        >>> apply_normalization_patterns("storage-dev-eastus", patterns)
        'storage-ENV-REGION'
    """
    if not patterns:
        return value
    
    result = value
    for pattern in patterns:
        before = result
        # Each pattern runs regex.sub() once (first-match-wins per pattern)
        result = pattern.pattern.sub(pattern.replacement, result)
        
        # Log transformation if verbose enabled and value changed (FR-015)
        if verbose and result != before:
            print(f"  [NORM] Pattern '{pattern.original_pattern}' → '{pattern.replacement}'")
            print(f"         Before: {before}")
            print(f"         After:  {result}")
    
    return result


def normalize_attribute_value(
    attribute_name: str,
    value: Any,
    config: NormalizationConfig,
    verbose: bool = False
) -> Any:
    """
    Normalize an attribute value using appropriate patterns based on attribute type.
    
    Recursively normalizes nested structures (lists and dicts). Only string values  
    within the structure are normalized - other primitive types (int, bool, None)  
    are returned unchanged. 
    
    - For resource ID attributes (ending in '_id' or named 'id'), applies resource_id_patterns
    - For other attributes, applies name_patterns
    - For lists: recursively normalizes each element
    - For dicts: recursively normalizes each value
    
    Args:
        attribute_name: Name of the attribute (used to determine normalization type)
        value: Attribute value to normalize
        config: NormalizationConfig with patterns to apply
        verbose: If True, log normalization transformations (FR-015)
        
    Returns:
        Normalized value (or original if non-string primitive or no patterns)
        
    Example:
        >>> config = NormalizationConfig(
        ...     name_patterns=[NormalizationPattern(re.compile(r"-(dev)-"), "-ENV-", "", "-(dev)-")],
        ...     resource_id_patterns=[NormalizationPattern(re.compile(r"/subscriptions/[a-f0-9-]+"), "/subscriptions/SUB_ID", "", "/subscriptions/[a-f0-9-]+")],
        ...     source_file=Path("/fake.json")
        ... )
        >>> normalize_attribute_value("name", "storage-dev-eastus", config)
        'storage-ENV-eastus'
        >>> normalize_attribute_value("subscription_id", "/subscriptions/abc-123/rg/test", config)
        '/subscriptions/SUB_ID/rg/test'
        >>> normalize_attribute_value("count", 42, config)
        42
        >>> normalize_attribute_value("fqdns", ["app-dev.example.com"], config)
        ['app-ENV.example.com']
    """
    # Handle None
    if value is None:
        return value
    
    # Recursively normalize lists
    if isinstance(value, list):
        return [normalize_attribute_value(attribute_name, item, config, verbose) for item in value]
    
    # Recursively normalize dicts
    if isinstance(value, dict):
        return {k: normalize_attribute_value(k, v, config, verbose) for k, v in value.items()}
    
    # Only normalize string values (primitives like int, bool, None pass through)
    if not isinstance(value, str):
        return value
    
    # Classify the attribute to determine which patterns to apply
    attr_type = classify_attribute(attribute_name)
    
    if verbose:
        print(f"  [NORM] Normalizing attribute '{attribute_name}' (type: {attr_type})")
    
    if attr_type == "resource_id":
        # Apply resource ID patterns for ID-like attributes
        if not config.resource_id_patterns:
            return value
        return normalize_resource_id(value, config.resource_id_patterns, verbose)
    else:
        # Apply name patterns for regular attributes
        if not config.name_patterns:
            return value
        return apply_normalization_patterns(value, config.name_patterns, verbose)


# ==============================================================================
# User Story 2: Resource ID Transformation Normalization
# ==============================================================================


def classify_attribute(attribute_name: str) -> str:
    """
    Classify an attribute as either 'resource_id' or 'name' based on its name.
    
    Attributes ending in '_id' or named 'id' are classified as resource_id.
    This determines which normalization patterns to apply.
    
    Args:
        attribute_name: Name of the attribute to classify
        
    Returns:
        'resource_id' if the attribute contains resource identifiers,
        'name' otherwise
        
    Example:
        >>> classify_attribute("id")
        'resource_id'
        >>> classify_attribute("subscription_id")
        'resource_id'
        >>> classify_attribute("name")
        'name'
        >>> classify_attribute("location")
        'name'
    """
    # Check if attribute name ends with _id or is exactly "id"
    if attribute_name == "id" or attribute_name.endswith("_id"):
        return "resource_id"
    return "name"


def normalize_resource_id(
    value: str,
    patterns: List[NormalizationPattern],
    verbose: bool = False
) -> str:
    """
    Normalize a resource ID value by applying resource ID patterns.
    
    This function applies resource_id_patterns in order (first-match-wins
    per pattern) to normalize subscription IDs, tenant IDs, and other
    Azure-specific identifiers.
    
    Args:
        value: Resource ID string to normalize
        patterns: List of NormalizationPattern objects to apply
        verbose: If True, log normalization transformations (FR-015)
        
    Returns:
        Normalized resource ID string
        
    Example:
        >>> pattern = NormalizationPattern(
        ...     pattern=re.compile(r'/subscriptions/[0-9a-f-]+'),
        ...     replacement='/subscriptions/SUB_ID',
        ...     description='Subscription ID',
        ...     original_pattern='/subscriptions/[0-9a-f-]+'
        ... )
        >>> normalize_resource_id('/subscriptions/abc-123/rg/test', [pattern])
        '/subscriptions/SUB_ID/rg/test'
    """
    # Use the same pattern application logic as name normalization
    return apply_normalization_patterns(value, patterns, verbose)

