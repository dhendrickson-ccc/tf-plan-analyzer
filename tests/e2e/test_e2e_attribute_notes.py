#!/usr/bin/env python3
"""
End-to-end tests for attribute notes feature.

Tests HTML structure generation for question/answer notes fields.
Per Constitution Principle V: User-Facing Features Require End-to-End Testing
"""

import subprocess
import pytest
from pathlib import Path
import re


class TestUS1AddQuestionField:
    """End-to-end tests for User Story 1: Add question field to attribute changes."""

    def test_question_field_renders_in_html(self, tmp_path):
        """
        Test that question textarea is present in generated HTML report.

        Generates a comparison report and verifies HTML contains:
        - Notes container div
        - Question label
        - Question textarea with correct ID and attributes
        """
        output_file = tmp_path / "comparison.html"

        # Generate HTML comparison report
        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/dev-plan.json",
                "tests/fixtures/staging-plan.json",
                "--html",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert output_file.exists(), "HTML file was not created"

        # Read generated HTML
        html_content = output_file.read_text()

        # Verify notes container exists
        assert '<div class="notes-container">' in html_content, \
            "Notes container div not found in HTML"

        # Verify question label exists
        assert '<label class="note-label"' in html_content, \
            "Question label not found in HTML"
        assert 'Question:' in html_content, \
            "Question label text not found"

        # Verify question textarea exists with required attributes
        assert '<textarea' in html_content, \
            "Textarea element not found"
        assert 'class="note-field"' in html_content, \
            "Textarea does not have note-field class"
        assert 'id="note-q-' in html_content, \
            "Question textarea does not have correct ID pattern"
        assert 'placeholder="Add a question..."' in html_content, \
            "Question textarea missing placeholder text"
        assert 'rows="4"' in html_content, \
            "Question textarea missing rows attribute"
        assert 'oninput="debouncedSaveNote(' in html_content, \
            "Question textarea missing oninput event handler"

    def test_notes_css_included_in_html(self, tmp_path):
        """Test that notes CSS styles are included in generated HTML."""
        output_file = tmp_path / "comparison.html"

        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/dev-plan.json",
                "tests/fixtures/staging-plan.json",
                "--html",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        html_content = output_file.read_text()

        # Verify notes CSS classes are defined
        assert ".notes-container" in html_content, \
            "Notes container CSS not found"
        assert ".note-field" in html_content, \
            "Note field CSS not found"
        assert ".note-label" in html_content, \
            "Note label CSS not found"

    def test_notes_javascript_included_in_html(self, tmp_path):
        """Test that notes JavaScript functions are included in generated HTML."""
        output_file = tmp_path / "comparison.html"

        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/dev-plan.json",
                "tests/fixtures/staging-plan.json",
                "--html",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        html_content = output_file.read_text()

        # Verify JavaScript functions are embedded
        assert "function getReportId()" in html_content, \
            "getReportId function not found"
        assert "function debounce(" in html_content, \
            "debounce function not found"
        assert "function saveNote(" in html_content, \
            "saveNote function not found"
        assert "function loadNotes()" in html_content, \
            "loadNotes function not found"
        assert "localStorage.setItem" in html_content, \
            "localStorage.setItem not found in JavaScript"
        assert "localStorage.getItem" in html_content, \
            "localStorage.getItem not found in JavaScript"

    def test_question_field_has_unique_ids_per_attribute(self, tmp_path):
        """Test that each attribute has a unique question field ID."""
        output_file = tmp_path / "comparison.html"

        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/dev-plan.json",
                "tests/fixtures/staging-plan.json",
                "--html",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        html_content = output_file.read_text()

        # Extract all question field IDs
        question_ids = re.findall(r'id="note-q-([^"]+)"', html_content)

        # Verify we have question fields
        assert len(question_ids) > 0, \
            "No question field IDs found"

        # Verify all IDs are unique
        assert len(question_ids) == len(set(question_ids)), \
            "Question field IDs are not unique"


class TestUS2AnswerField:
    """End-to-end tests for User Story 2: Add answer field below question."""

    def test_answer_field_renders_in_html(self, tmp_path):
        """
        Test that answer textarea is present in generated HTML report.

        Verifies HTML contains:
        - Answer label
        - Answer textarea with correct ID and attributes
        - Answer field appears after question field
        """
        output_file = tmp_path / "comparison.html"

        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/dev-plan.json",
                "tests/fixtures/staging-plan.json",
                "--html",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        html_content = output_file.read_text()

        # Verify answer label exists
        assert 'Answer:' in html_content, \
            "Answer label text not found"

        # Verify answer textarea exists with required attributes
        assert 'id="note-a-' in html_content, \
            "Answer textarea does not have correct ID pattern"
        assert 'placeholder="Add an answer..."' in html_content, \
            "Answer textarea missing placeholder text"

        # Verify answer wrapper div exists
        assert '<div class="note-answer">' in html_content, \
            "Answer wrapper div not found"

    def test_question_and_answer_fields_paired(self, tmp_path):
        """Test that question and answer fields are paired for each attribute."""
        output_file = tmp_path / "comparison.html"

        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/dev-plan.json",
                "tests/fixtures/staging-plan.json",
                "--html",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        html_content = output_file.read_text()

        # Extract question and answer IDs
        question_ids = re.findall(r'id="note-q-([^"]+)"', html_content)
        answer_ids = re.findall(r'id="note-a-([^"]+)"', html_content)

        # Verify we have matching counts
        assert len(question_ids) == len(answer_ids), \
            f"Question count ({len(question_ids)}) != Answer count ({len(answer_ids)})"

        # Verify each question has matching answer (same resource-attribute suffix)
        for q_id in question_ids:
            assert q_id in answer_ids, \
                f"Question field {q_id} has no matching answer field"


class TestUS3ReviewMultipleNotes:
    """End-to-end tests for User Story 3: Review multiple annotated changes."""

    def test_multiple_attributes_have_independent_notes(self, tmp_path):
        """Test that multiple attributes each have their own independent note fields."""
        output_file = tmp_path / "comparison.html"

        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/dev-plan.json",
                "tests/fixtures/staging-plan.json",
                "--html",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        html_content = output_file.read_text()

        # Count notes containers
        notes_containers = html_content.count('<div class="notes-container">')

        # We should have at least one notes container per changed attribute
        # Dev and staging have 2 resources with differences
        assert notes_containers >= 1, \
            f"Expected at least 1 notes container, found {notes_containers}"

        # Verify each container has both question and answer fields
        # For each notes container, verify structure
        assert html_content.count('id="note-q-') == html_content.count('id="note-a-'), \
            "Question and answer field counts don't match"
