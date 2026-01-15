"""
Diff highlighting utilities for JSON and character-level comparisons.

This module provides functions for highlighting differences between strings and JSON structures
with HTML formatting. Used across analyze_plan.py and multi_env_comparator.py.
"""

import html
import json
from difflib import SequenceMatcher
from typing import Any, Tuple


def highlight_char_diff(
    before_str: str, after_str: str, is_known_after_apply: bool = False, is_baseline_comparison: bool = False
) -> Tuple[str, str]:
    """
    Highlight character-level differences between two similar strings.

    Uses difflib.SequenceMatcher to identify character-level changes and wraps them
    in HTML span elements for visual highlighting. Supports special styling for
    "known after apply" values from Terraform.

    Args:
        before_str: Original string value
        after_str: New string value to compare against
        is_known_after_apply: If True, uses 'char-known-after-apply' CSS class for additions
                             instead of 'char-added'. Used for Terraform placeholder values.
        is_baseline_comparison: If True, uses blue 'baseline-char-removed' and 'baseline-char-added'
                               CSS classes for multi-environment baseline comparisons.

    Returns:
        Tuple of (before_html, after_html) where each is an HTML string with:
        - Removed characters wrapped in <span class="char-removed"> or <span class="baseline-char-removed">
        - Added characters wrapped in <span class="char-added"> or <span class="baseline-char-added">
        - Unchanged characters as plain HTML-escaped text

    Example:
        >>> before, after = highlight_char_diff("hello world", "hello terra")
        >>> # before: 'hello <span class="char-removed">world</span>'
        >>> # after: 'hello <span class="char-added">terra</span>'
    """
    matcher = SequenceMatcher(None, before_str, after_str)
    before_parts = []
    after_parts = []

    # Choose the CSS classes based on context
    if is_baseline_comparison:
        char_removed_class = "baseline-char-removed"
        char_added_class = "baseline-char-added"
    elif is_known_after_apply:
        char_removed_class = "char-removed"
        char_added_class = "char-known-after-apply"
    else:
        char_removed_class = "char-removed"
        char_added_class = "char-added"

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            # Characters are the same
            text = html.escape(before_str[i1:i2])
            before_parts.append(text)
            after_parts.append(text)
        elif tag == "delete":
            # Characters only in before
            before_parts.append(
                f'<span class="{char_removed_class}">{html.escape(before_str[i1:i2])}</span>'
            )
        elif tag == "insert":
            # Characters only in after
            after_parts.append(
                f'<span class="{char_added_class}">{html.escape(after_str[j1:j2])}</span>'
            )
        elif tag == "replace":
            # Characters differ
            before_parts.append(
                f'<span class="{char_removed_class}">{html.escape(before_str[i1:i2])}</span>'
            )
            after_parts.append(
                f'<span class="{char_added_class}">{html.escape(after_str[j1:j2])}</span>'
            )

    return "".join(before_parts), "".join(after_parts)


def highlight_json_diff(
    before: Any,
    after: Any,
    is_known_after_apply: bool = False,
    values_changed: bool = None,
    is_baseline_comparison: bool = False,
) -> Tuple[str, str]:
    """
    Highlight differences between two JSON structures with line and character-level comparison.

    Converts Python objects to formatted JSON strings and performs a line-by-line diff,
    with character-level highlighting for lines that are similar but not identical.

    Args:
        before: Original value (can be dict, list, str, int, float, bool, or None)
        after: New value to compare against (same types as before)
        is_known_after_apply: If True, uses special styling for Terraform placeholder values
        values_changed: Optional metadata flag indicating if values actually changed.
                       Useful when both before and after display identically (e.g., "<REDACTED>")
                       but underlying values differ.
        is_baseline_comparison: If True, uses blue baseline CSS classes for multi-environment comparisons

    Returns:
        Tuple of (before_html, after_html) where each is an HTML <pre> block containing:
        - Lines with differences highlighted via CSS classes (.removed, .added, .unchanged)
        - Character-level diffs within similar lines
        - Empty placeholder lines for alignment when line counts differ

    Example:
        >>> before = {"name": "server-1", "size": "small"}
        >>> after = {"name": "server-2", "size": "large"}
        >>> before_html, after_html = highlight_json_diff(before, after)
        >>> # Returns formatted JSON with character-level highlighting on the changed values

    CSS Classes Used:
        - .removed or .baseline-removed: Red or blue background for removed content
        - .added or .baseline-added: Green or blue background for added content
        - .unchanged: Normal styling for unchanged content
        - .char-removed or .baseline-char-removed: Character-level removal highlighting
        - .char-added or .baseline-char-added: Character-level addition highlighting
    """
    # Convert to formatted JSON strings
    before_str = (
        json.dumps(before, indent=2, sort_keys=True) if before is not None else "null"
    )
    after_str = (
        json.dumps(after, indent=2, sort_keys=True) if after is not None else "null"
    )

    # Choose CSS classes based on context
    if is_baseline_comparison:
        removed_class = "baseline-removed"
        added_class = "baseline-added"
    elif is_known_after_apply:
        removed_class = "removed"
        added_class = "known-after-apply"
    else:
        removed_class = "removed"
        added_class = "added"

    # Check if both values contain "(changed)" indicator - this means sensitive values changed
    both_have_changed_indicator = "(changed)" in before_str and "(changed)" in after_str

    # If strings are identical after normalization AND no metadata indicates change, return without highlighting
    # Use metadata (values_changed) as the source of truth for whether highlighting is needed
    strings_identical = before_str == after_str
    should_highlight = (
        values_changed
        if values_changed is not None
        else (not strings_identical or both_have_changed_indicator)
    )

    if strings_identical and not should_highlight:
        before_html = f'<pre class="json-content">{html.escape(before_str)}</pre>'
        after_html = f'<pre class="json-content">{html.escape(after_str)}</pre>'
        return before_html, after_html

    # Split into lines for comparison
    before_lines = before_str.split("\n")
    after_lines = after_str.split("\n")

    # Use SequenceMatcher to find differences
    matcher = SequenceMatcher(None, before_lines, after_lines)

    before_html_lines = []
    after_html_lines = []

    # When strings are identical but metadata says values changed, force highlighting
    if strings_identical and should_highlight:
        # Both strings are the same but values actually changed (e.g., both show <REDACTED (changed)>)
        # Only highlight lines that contain the "(changed)" indicator
        for before_line, after_line in zip(before_lines, after_lines):
            if "(changed)" in before_line or "(changed)" in after_line:
                # This line has a changed sensitive value - highlight it
                before_html_lines.append(
                    f'<span class="{removed_class}">{html.escape(before_line)}</span>'
                )
                after_html_lines.append(
                    f'<span class="{added_class}">{html.escape(after_line)}</span>'
                )
            else:
                # This line didn't change - show as unchanged
                before_html_lines.append(
                    f'<span class="unchanged">{html.escape(before_line)}</span>'
                )
                after_html_lines.append(
                    f'<span class="unchanged">{html.escape(after_line)}</span>'
                )

        # Handle any remaining lines if lengths differ
        if len(before_lines) > len(after_lines):
            for line in before_lines[len(after_lines) :]:
                if "(changed)" in line:
                    before_html_lines.append(
                        f'<span class="{removed_class}">{html.escape(line)}</span>'
                    )
                else:
                    before_html_lines.append(
                        f'<span class="unchanged">{html.escape(line)}</span>'
                    )
        elif len(after_lines) > len(before_lines):
            for line in after_lines[len(before_lines) :]:
                if "(changed)" in line:
                    after_html_lines.append(
                        f'<span class="{added_class}">{html.escape(line)}</span>'
                    )
                else:
                    after_html_lines.append(
                        f'<span class="unchanged">{html.escape(line)}</span>'
                    )
    else:
        # Normal diff highlighting based on line comparison
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                # Lines are the same
                for line in before_lines[i1:i2]:
                    before_html_lines.append(
                        f'<span class="unchanged">{html.escape(line)}</span>'
                    )
                for line in after_lines[j1:j2]:
                    after_html_lines.append(
                        f'<span class="unchanged">{html.escape(line)}</span>'
                    )
            elif tag == "delete":
                # Lines only in before
                for line in before_lines[i1:i2]:
                    before_html_lines.append(
                        f'<span class="{removed_class}">{html.escape(line)}</span>'
                    )
                # Add empty lines to after to maintain alignment
                empty_line = (
                    '<span class="unchanged opacity-50">' + ("&nbsp;" * 20) + "</span>"
                )
                for _ in range(i2 - i1):
                    after_html_lines.append(empty_line)
            elif tag == "insert":
                # Lines only in after
                # Add empty lines to before to maintain alignment
                empty_line = (
                    '<span class="unchanged opacity-50">' + ("&nbsp;" * 20) + "</span>"
                )
                for _ in range(j2 - j1):
                    before_html_lines.append(empty_line)
                for line in after_lines[j1:j2]:
                    after_html_lines.append(
                        f'<span class="{added_class}">{html.escape(line)}</span>'
                    )
            elif tag == "replace":
                # Lines differ - do character-level comparison for similar lines
                before_chunk = before_lines[i1:i2]
                after_chunk = after_lines[j1:j2]

                # For each pair of lines, check if they're similar (e.g., only value differs)
                max_len = max(len(before_chunk), len(after_chunk))
                empty_line = (
                    '<span class="unchanged opacity-50">' + ("&nbsp;" * 20) + "</span>"
                )
                for idx in range(max_len):
                    if idx < len(before_chunk) and idx < len(after_chunk):
                        before_line = before_chunk[idx]
                        after_line = after_chunk[idx]

                        # Check if lines are similar enough for character-level diff
                        similarity = SequenceMatcher(
                            None, before_line, after_line
                        ).ratio()
                        if (
                            similarity > 0.5
                        ):  # If more than 50% similar, show character diff
                            before_highlighted, after_highlighted = highlight_char_diff(
                                before_line, after_line, is_known_after_apply, is_baseline_comparison
                            )
                            before_html_lines.append(
                                f'<span class="{removed_class}">{before_highlighted}</span>'
                            )
                            after_html_lines.append(
                                f'<span class="{added_class}">{after_highlighted}</span>'
                            )
                        else:
                            # Lines are too different, show as full line changes
                            if before_line in after_chunk:
                                before_html_lines.append(
                                    f'<span class="unchanged">{html.escape(before_line)}</span>'
                                )
                            else:
                                before_html_lines.append(
                                    f'<span class="{removed_class}">{html.escape(before_line)}</span>'
                                )

                            if after_line in before_chunk:
                                after_html_lines.append(
                                    f'<span class="unchanged">{html.escape(after_line)}</span>'
                                )
                            else:
                                after_html_lines.append(
                                    f'<span class="{added_class}">{html.escape(after_line)}</span>'
                                )
                    elif idx < len(before_chunk):
                        before_line = before_chunk[idx]
                        if before_line in after_chunk:
                            before_html_lines.append(
                                f'<span class="unchanged">{html.escape(before_line)}</span>'
                            )
                        else:
                            before_html_lines.append(
                                f'<span class="{removed_class}">{html.escape(before_line)}</span>'
                            )
                        after_html_lines.append(empty_line)
                    else:
                        before_html_lines.append(empty_line)
                        after_line = after_chunk[idx]
                        if after_line in before_chunk:
                            after_html_lines.append(
                                f'<span class="unchanged">{html.escape(after_line)}</span>'
                            )
                        else:
                            after_html_lines.append(
                                f'<span class="{added_class}">{html.escape(after_line)}</span>'
                            )

    before_html = f'<pre class="json-content">{"<br>".join(before_html_lines)}</pre>'
    after_html = f'<pre class="json-content">{"<br>".join(after_html_lines)}</pre>'

    return before_html, after_html
