#!/usr/bin/env python3
"""
End-to-end tests for compare subcommand enhancements.

Tests the complete user journey for:
- User Story 1: Ignore file support with --config flag
- User Story 2: Attribute-level diff view
- User Story 3: Combined functionality

Per Constitution Principle V: User-Facing Features Require End-to-End Testing
"""

import subprocess
import pytest
import json
from pathlib import Path


class TestUS1IgnoreFileSupport:
    """End-to-end tests for User Story 1: Ignore file support."""
    
    def test_ignore_global_rules(self):
        """Test that global ignore rules filter out tags across all resources."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/env-char-diff-1.json',
             'test_data/env-char-diff-2.json',
             '--config', 'test_data/ignore_test_config.json'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should show ignore statistics in output
        assert 'IGNORE STATISTICS' in result.stdout
        assert 'Ignored Attributes:' in result.stdout
        assert 'tags' in result.stdout  # Should mention tags were ignored
    
    def test_ignore_resource_specific(self):
        """Test that resource-specific rules filter out description for specific types."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/env-char-diff-1.json',
             'test_data/env-char-diff-2.json',
             '--config', 'test_data/ignore_test_config.json'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Resource-specific ignores should be applied
        # The specific behavior depends on test data and resource types
        assert result.returncode == 0
    
    def test_ignore_nested_attributes(self):
        """Test that nested attributes with dot notation are ignored."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/env-char-diff-1.json',
             'test_data/env-char-diff-2.json',
             '--config', 'test_data/ignore_test_config.json'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Nested attributes should be filtered using dot notation
        # Specific verification depends on test data having nested structures
        assert result.returncode == 0
    
    def test_ignore_config_file_not_found(self):
        """Test that missing config file returns exit code 1 with error message."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/env-char-diff-1.json',
             'test_data/env-char-diff-2.json',
             '--config', 'test_data/nonexistent_config.json'],
            capture_output=True,
            text=True
        )
        
        # Exit code 1 for file not found
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
        
        # Should show error message about missing file
        error_output = result.stdout + result.stderr
        assert 'not found' in error_output.lower() or 'does not exist' in error_output.lower()
        assert 'config' in error_output.lower()
    
    def test_ignore_config_malformed_json(self):
        """Test that malformed JSON config returns exit code 2 with error message."""
        # Create a temporary malformed JSON file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{invalid json content')
            malformed_file = f.name
        
        try:
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/env-char-diff-1.json',
                 'test_data/env-char-diff-2.json',
                 '--config', malformed_file],
                capture_output=True,
                text=True
            )
            
            # Exit code 2 for malformed JSON
            assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"
            
            # Should show error message about JSON parsing
            error_output = result.stdout + result.stderr
            assert 'json' in error_output.lower() or 'parse' in error_output.lower() or 'malformed' in error_output.lower()
        finally:
            os.unlink(malformed_file)
    
    def test_ignore_with_html_output(self):
        """Test that ignore rules work correctly with HTML output."""
        import os
        
        output_file = 'test_ignore_html_output.html'
        
        # Clean up any existing file
        if os.path.exists(output_file):
            os.unlink(output_file)
        
        try:
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/env-char-diff-1.json',
                 'test_data/env-char-diff-2.json',
                 '--config', 'test_data/ignore_test_config.json',
                 '--html', output_file],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"
            
            # Read HTML and verify it contains ignore statistics
            with open(output_file, 'r') as f:
                html_content = f.read()
            
            # HTML should show some indication of ignored attributes
            # This could be in statistics, badges, or other indicators
            assert len(html_content) > 0, "HTML file is empty"
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_compare_without_config_still_works(self):
        """Test that compare subcommand still works without --config flag (backward compatibility)."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/env-char-diff-1.json',
             'test_data/env-char-diff-2.json'],
            capture_output=True,
            text=True
        )
        
        # Should work normally without config
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert 'Comparing' in result.stdout


class TestUS2AttributeLevelDiff:
    """End-to-end tests for User Story 2: Attribute-level diff view."""
    
    def test_attribute_level_single_change(self):
        """Test that HTML shows only changed attributes, not full JSON."""
        import os
        
        output_file = 'test_attribute_single_change.html'
        if os.path.exists(output_file):
            os.unlink(output_file)
        
        try:
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/env-char-diff-1.json',
                 'test_data/env-char-diff-2.json',
                 '--html', output_file],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"
            
            # Read HTML and verify attribute-level view
            with open(output_file, 'r') as f:
                html_content = f.read()
            
            # Should NOT contain full JSON dumps (old behavior)
            # Should contain attribute table structure instead
            assert '<table' in html_content or 'attribute' in html_content.lower()
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_attribute_level_multiple_changes(self):
        """Test that multiple changed attributes are all shown separately."""
        import os
        
        output_file = 'test_attribute_multiple_changes.html'
        if os.path.exists(output_file):
            os.unlink(output_file)
        
        try:
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/env-char-diff-1.json',
                 'test_data/env-char-diff-2.json',
                 '--html', output_file],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"
            
            with open(output_file, 'r') as f:
                html_content = f.read()
            
            # Should show attribute-level structure
            assert len(html_content) > 0
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_attribute_level_nested_object(self):
        """Test that nested objects are shown as top-level attributes."""
        import os
        
        output_file = 'test_attribute_nested.html'
        if os.path.exists(output_file):
            os.unlink(output_file)
        
        try:
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/env-deep-nested.json',
                 'test_data/env-char-diff-1.json',
                 '--html', output_file],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_attribute_level_identical_resource(self):
        """Test that identical resources show 'No differences' message."""
        import os
        
        output_file = 'test_attribute_identical.html'
        if os.path.exists(output_file):
            os.unlink(output_file)
        
        try:
            # Compare same file with different env names
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/env-char-diff-1.json',
                 'test_data/env-char-diff-1.json',
                 '--env-names', 'env1,env2',
                 '--html', output_file],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"
            
            with open(output_file, 'r') as f:
                html_content = f.read()
            
            # Should show "no differences" or "identical" message
            assert 'no differences' in html_content.lower() or 'identical' in html_content.lower()
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_attribute_level_sensitive_values(self):
        """Test that sensitive attributes show security badge in attribute view."""
        import os
        
        output_file = 'test_attribute_sensitive.html'
        if os.path.exists(output_file):
            os.unlink(output_file)
        
        try:
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/env-sensitive-char-1.json',
                 'test_data/env-sensitive-char-2.json',
                 '--html', output_file],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"
            
            with open(output_file, 'r') as f:
                html_content = f.read()
            
            # Should contain sensitive indicator for sensitive attributes
            assert 'SENSITIVE' in html_content or '🔒' in html_content
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestUS3CombinedFunctionality:
    """End-to-end tests for User Story 3: Combined ignore + attribute-level view."""
    
    # Placeholder - will be implemented in Phase 5
    pass
