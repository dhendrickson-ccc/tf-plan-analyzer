"""
Shared library utilities for tf-plan-analyzer.

This module contains reusable functions for HTML generation, diff highlighting,
JSON utilities, and file I/O operations.
"""

from .html_generation import (
    get_base_css,
    get_diff_highlight_css,
    get_summary_card_css,
    get_resource_card_css,
    generate_full_styles,
)
from .diff_utils import highlight_char_diff, highlight_json_diff
from .json_utils import load_json_file, format_json_for_display
from .file_utils import safe_read_file, safe_write_file

__all__ = [
    'get_base_css',
    'get_diff_highlight_css',
    'get_summary_card_css',
    'get_resource_card_css',
    'generate_full_styles',
    'highlight_char_diff',
    'highlight_json_diff',
    'load_json_file',
    'format_json_for_display',
    'safe_read_file',
    'safe_write_file',
]

