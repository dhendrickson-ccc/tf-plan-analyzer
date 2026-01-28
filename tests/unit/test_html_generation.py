#!/usr/bin/env python3
"""
Unit tests for HTML generation module.

Tests CSS and JavaScript generation functions for attribute notes feature.
"""

import pytest
from src.lib.html_generation import (
    get_notes_css,
    get_notes_javascript,
    generate_full_styles,
)


class TestGetNotesCSS:
    """Tests for get_notes_css function."""

    def test_returns_string(self):
        """Test that get_notes_css returns a string."""
        result = get_notes_css()
        assert isinstance(result, str)

    def test_contains_notes_container_class(self):
        """Test that CSS includes .notes-container class."""
        css = get_notes_css()
        assert ".notes-container" in css

    def test_contains_note_field_class(self):
        """Test that CSS includes .note-field class."""
        css = get_notes_css()
        assert ".note-field" in css

    def test_contains_note_label_class(self):
        """Test that CSS includes .note-label class."""
        css = get_notes_css()
        assert ".note-label" in css

    def test_contains_note_answer_class(self):
        """Test that CSS includes .note-answer class for answer field wrapper."""
        css = get_notes_css()
        assert ".note-answer" in css

    def test_contains_focus_state(self):
        """Test that CSS includes focus state styling."""
        css = get_notes_css()
        assert ".note-field:focus" in css

    def test_contains_placeholder_styling(self):
        """Test that CSS includes placeholder text styling."""
        css = get_notes_css()
        assert ".note-field::placeholder" in css


class TestGetNotesJavaScript:
    """Tests for get_notes_javascript function."""

    def test_returns_string(self):
        """Test that get_notes_javascript returns a string."""
        result = get_notes_javascript()
        assert isinstance(result, str)

    def test_contains_getReportId_function(self):
        """Test that JavaScript includes getReportId function."""
        js = get_notes_javascript()
        assert "function getReportId()" in js

    def test_contains_debounce_function(self):
        """Test that JavaScript includes debounce utility function."""
        js = get_notes_javascript()
        assert "function debounce(" in js

    def test_contains_saveNote_function(self):
        """Test that JavaScript includes saveNote function."""
        js = get_notes_javascript()
        assert "function saveNote(" in js

    def test_contains_debouncedSaveNote_constant(self):
        """Test that JavaScript includes debouncedSaveNote debounced wrapper."""
        js = get_notes_javascript()
        assert "debouncedSaveNote" in js

    def test_contains_loadNotes_function(self):
        """Test that JavaScript includes loadNotes function."""
        js = get_notes_javascript()
        assert "function loadNotes()" in js

    def test_contains_localStorage_setItem(self):
        """Test that JavaScript uses localStorage.setItem for persistence."""
        js = get_notes_javascript()
        assert "localStorage.setItem" in js

    def test_contains_localStorage_getItem(self):
        """Test that JavaScript uses localStorage.getItem for retrieval."""
        js = get_notes_javascript()
        assert "localStorage.getItem" in js

    def test_contains_JSON_parse(self):
        """Test that JavaScript parses JSON from localStorage."""
        js = get_notes_javascript()
        assert "JSON.parse" in js

    def test_contains_JSON_stringify(self):
        """Test that JavaScript serializes to JSON for localStorage."""
        js = get_notes_javascript()
        assert "JSON.stringify" in js

    def test_contains_key_pattern_with_reportId(self):
        """Test that JavaScript uses correct localStorage key pattern."""
        js = get_notes_javascript()
        assert "tf-notes-" in js

    def test_contains_DOMContentLoaded_event(self):
        """Test that JavaScript loads notes on DOMContentLoaded."""
        js = get_notes_javascript()
        assert "DOMContentLoaded" in js

    def test_contains_QuotaExceededError_handling(self):
        """Test that JavaScript handles localStorage quota errors."""
        js = get_notes_javascript()
        assert "QuotaExceededError" in js


class TestGenerateFullStylesIncludesNotesCSS:
    """Tests for generate_full_styles integration with notes CSS."""

    def test_includes_notes_css(self):
        """Test that generate_full_styles includes notes CSS."""
        full_styles = generate_full_styles()
        assert ".notes-container" in full_styles

    def test_returns_complete_style_tag(self):
        """Test that generate_full_styles returns complete <style> tag."""
        full_styles = generate_full_styles()
        assert full_styles.startswith("<style>")
        assert full_styles.endswith("</style>")

    def test_includes_notes_field_styling(self):
        """Test that full styles include .note-field class."""
        full_styles = generate_full_styles()
        assert ".note-field" in full_styles
