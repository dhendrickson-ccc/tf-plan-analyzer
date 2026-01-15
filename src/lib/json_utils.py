"""
JSON file I/O and formatting utilities.

This module provides standardized functions for loading and formatting JSON data,
eliminating duplicate file handling patterns across the codebase.
"""

import json
from typing import Any, Dict


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load and parse a JSON file from disk.
    
    Provides a standardized way to load JSON files with consistent error handling
    and encoding. Used throughout the codebase to replace inline file reading patterns.
    
    Args:
        file_path: Path to the JSON file to load
    
    Returns:
        Parsed JSON data as a Python dictionary
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        IOError: For other file reading errors
    
    Example:
        >>> plan_data = load_json_file('test_data/dev-plan.json')
        >>> resource_changes = plan_data.get('resource_changes', [])
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_json_for_display(data: Any, indent: int = 2, sort_keys: bool = True) -> str:
    """
    Format Python data structures as pretty-printed JSON strings.
    
    Provides consistent JSON formatting across all output (reports, logs, etc).
    Handles None values by converting to "null" string.
    
    Args:
        data: Any JSON-serializable Python object (dict, list, str, int, float, bool, None)
        indent: Number of spaces for indentation (default: 2)
        sort_keys: Whether to sort dictionary keys alphabetically (default: True)
    
    Returns:
        Formatted JSON string with specified indentation and key ordering
    
    Example:
        >>> data = {"name": "server", "size": "large", "count": 3}
        >>> print(format_json_for_display(data))
        {
          "count": 3,
          "name": "server",
          "size": "large"
        }
    """
    if data is None:
        return "null"
    return json.dumps(data, indent=indent, sort_keys=sort_keys)
