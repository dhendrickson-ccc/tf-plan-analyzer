#!/usr/bin/env python3
"""
Normalization Configuration Utilities

This module provides utilities for loading and applying normalization patterns
to filter environment-specific differences in Terraform plan comparisons.
"""

import json
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
            config_dict = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse normalization config file: {file_path}\n"
            f"JSON Error: {e.msg}",
            e.doc,
            e.pos
        )
    
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
