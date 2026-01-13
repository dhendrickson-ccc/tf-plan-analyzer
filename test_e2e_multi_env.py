#!/usr/bin/env python3
"""
End-to-end tests for multi-environment comparison CLI.

Tests the complete user journey from CLI invocation to report generation.
Per Constitution Principle V: User-Facing Features Require End-to-End Testing
"""

import subprocess
import pytest
from pathlib import Path


class TestCLIRouting:
    """End-to-end tests for CLI subcommand routing."""
    
    def test_no_subcommand_shows_help(self):
        """Test that running without subcommand shows help and exits with error."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'report' in result.stdout
        assert 'compare' in result.stdout
    
    def test_report_subcommand_help(self):
        """Test that report subcommand help is accessible."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'report', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'plan_file' in result.stdout
        assert '--config' in result.stdout
        assert '--html' in result.stdout
    
    def test_compare_subcommand_help(self):
        """Test that compare subcommand help is accessible."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'plan_files' in result.stdout
        assert '--html' in result.stdout
    
    def test_compare_with_one_file_errors(self):
        """Test that compare subcommand requires at least 2 files."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare', 'dummy.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'at least 2 plan files' in result.stdout
        assert 'report' in result.stdout  # Should suggest report subcommand


class TestMultiEnvComparison:
    """End-to-end tests for multi-environment comparison."""
    pass

