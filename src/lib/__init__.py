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

__all__ = [
    'get_base_css',
    'get_diff_highlight_css',
    'get_summary_card_css',
    'get_resource_card_css',
    'generate_full_styles',
]
