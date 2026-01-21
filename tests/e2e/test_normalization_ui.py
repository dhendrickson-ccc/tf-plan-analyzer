"""
End-to-end tests for normalization UI tracking (Feature 007 US3).

Tests verify that:
1. Badges show separate counts for config vs normalization ignores
2. Tooltips display attribute breakdowns correctly
3. Summary statistics show normalization counts
"""

import json
import subprocess
import tempfile
from pathlib import Path


def test_badge_shows_combined_counts():
    """
    T051: Verify badge displays combined config + normalization counts.
    
    Given: Resource with both config-ignored and normalization-ignored attributes
    When: HTML report is generated
    Then: Badge shows "X attributes ignored (Y config, Z normalized)"
    """
    # Setup test data with both types of ignores
    env1_data = {
        "resource_changes": [
            {
                "type": "azurerm_storage_account",
                "name": "test_storage",
                "change": {
                    "before": {
                        "name": "storagetest123",
                        "location": "eastus",
                        "tags": {"env": "dev"},
                        "id": "/subscriptions/sub-111/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storagetest123"
                    },
                    "after": {
                        "name": "storage-test-123",  # Will be normalized
                        "location": "westus",        # Will show as difference
                        "tags": {"env": "dev"},
                        "id": "/subscriptions/sub-111/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storage-test-123"
                    }
                }
            }
        ]
    }
    
    env2_data = {
        "resource_changes": [
            {
                "type": "azurerm_storage_account",
                "name": "test_storage",
                "change": {
                    "before": {
                        "name": "storagetest123",
                        "location": "eastus",
                        "tags": {"env": "prod"},
                        "id": "/subscriptions/sub-222/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storagetest123"
                    },
                    "after": {
                        "name": "storage-test-123",
                        "location": "westus",
                        "tags": {"env": "prod"},
                        "id": "/subscriptions/sub-222/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storage-test-123"
                    }
                }
            }
        ]
    }
    
    # Create ignore config that ignores tags and references normalization config
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write test data
        env1_path = tmpdir_path / "env1.json"
        env2_path = tmpdir_path / "env2.json"
        norm_path = tmpdir_path / "norm.json"
        html_path = tmpdir_path / "output.html"
        
        # Create normalization config using pattern-based approach
        normalization_config = {
            "name_patterns": [
                {
                    "pattern": "-",
                    "replacement": "",
                    "description": "Remove hyphens from names"
                }
            ],
            "resource_id_patterns": [
                {
                    "pattern": "/subscriptions/[^/]+",
                    "replacement": "/subscriptions/NORMALIZED",
                    "description": "Normalize subscription IDs"
                }
            ]
        }
        
        # Create ignore config with normalization path
        ignore_config = {
            "resource_patterns": [
                {
                    "type_pattern": "azurerm_storage_account",
                    "ignored_attributes": ["tags"]
                }
            ],
            "normalization_config_path": str(norm_path)
        }
        
        ignore_path = tmpdir_path / "ignore.json"
        
        env1_path.write_text(json.dumps(env1_data))
        env2_path.write_text(json.dumps(env2_data))
        norm_path.write_text(json.dumps(normalization_config))
        ignore_path.write_text(json.dumps(ignore_config))
        
        # Run CLI command
        result = subprocess.run(
            [
                "python3", "src/cli/analyze_plan.py", "compare",
                str(env1_path), str(env2_path),
                "--env-names", "dev,prod",
                "--config", str(ignore_path),
                "--html", str(html_path)
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Read generated HTML
        html_output = html_path.read_text()
        
        # Verify badge shows combined counts
        # Expected: tags (config-ignored), name and id (normalization-ignored)
        # Badge should show "3 attributes ignored (1 config, 2 normalized)"
        assert "3 attributes ignored" in html_output, "Badge should show total count of 3"
        assert "1 config" in html_output, "Badge should show 1 config-ignored attribute"
        assert "2 normalized" in html_output, "Badge should show 2 normalization-ignored attributes"


def test_tooltip_shows_attribute_breakdown():
    """
    T052: Verify tooltip displays separate lists for config vs normalized attributes.
    
    Given: Resource with both types of ignores
    When: HTML report is generated
    Then: Tooltip contains "Config: attr1 | Normalized: attr2, attr3"
    """
    # Same setup as test_badge_shows_combined_counts
    env1_data = {
        "resource_changes": [
            {
                "type": "azurerm_storage_account",
                "name": "test_storage",
                "change": {
                    "before": {
                        "name": "storagetest123",
                        "location": "eastus",
                        "tags": {"env": "dev"},
                        "id": "/subscriptions/sub-111/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storagetest123"
                    },
                    "after": {
                        "name": "storage-test-123",
                        "location": "westus",
                        "tags": {"env": "dev"},
                        "id": "/subscriptions/sub-111/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storage-test-123"
                    }
                }
            }
        ]
    }
    
    env2_data = {
        "resource_changes": [
            {
                "type": "azurerm_storage_account",
                "name": "test_storage",
                "change": {
                    "before": {
                        "name": "storagetest123",
                        "location": "eastus",
                        "tags": {"env": "prod"},
                        "id": "/subscriptions/sub-222/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storagetest123"
                    },
                    "after": {
                        "name": "storage-test-123",
                        "location": "westus",
                        "tags": {"env": "prod"},
                        "id": "/subscriptions/sub-222/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storage-test-123"
                    }
                }
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        env1_path = tmpdir_path / "env1.json"
        env2_path = tmpdir_path / "env2.json"
        norm_path = tmpdir_path / "norm.json"
        html_path = tmpdir_path / "output.html"
        
        # Create normalization config using pattern-based approach
        normalization_config = {
            "name_patterns": [
                {
                    "pattern": "-",
                    "replacement": "",
                    "description": "Remove hyphens from names"
                }
            ],
            "resource_id_patterns": [
                {
                    "pattern": "/subscriptions/[^/]+",
                    "replacement": "/subscriptions/NORMALIZED",
                    "description": "Normalize subscription IDs"
                }
            ]
        }
        
        # Create ignore config with tags ignored and normalization path
        ignore_config = {
            "resource_patterns": [
                {
                    "type_pattern": "azurerm_storage_account",
                    "ignored_attributes": ["tags"]
                }
            ],
            "normalization_config_path": str(norm_path)
        }
        
        ignore_path = tmpdir_path / "ignore.json"
        
        env1_path.write_text(json.dumps(env1_data))
        env2_path.write_text(json.dumps(env2_data))
        norm_path.write_text(json.dumps(normalization_config))
        ignore_path.write_text(json.dumps(ignore_config))
        
        result = subprocess.run(
            [
                "python3", "src/cli/analyze_plan.py", "compare",
                str(env1_path), str(env2_path),
                "--env-names", "dev,prod",
                "--config", str(ignore_path),
                "--html", str(html_path)
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        html_output = html_path.read_text()
        
        # Verify tooltip has separate sections
        # The tooltip should be in the format: "Config: tags | Normalized: id, name"
        assert "Config: tags" in html_output, "Tooltip should list config-ignored attributes"
        assert "Normalized:" in html_output, "Tooltip should have Normalized section"
        assert "id" in html_output and "name" in html_output, "Tooltip should list normalized attributes"


def test_summary_shows_normalization_statistics():
    """
    T053: Verify summary statistics show separate normalization count.
    
    Given: Comparison with normalization-ignored attributes
    When: Console text report is generated
    Then: Output shows "Normalized Attributes: X"
    """
    env1_data = {
        "resource_changes": [
            {
                "type": "azurerm_storage_account",
                "name": "test_storage",
                "change": {
                    "before": {
                        "name": "storagetest123",
                        "id": "/subscriptions/sub-111/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storagetest123"
                    },
                    "after": {
                        "name": "storage-test-123",
                        "id": "/subscriptions/sub-111/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storage-test-123"
                    }
                }
            }
        ]
    }
    
    env2_data = {
        "resource_changes": [
            {
                "type": "azurerm_storage_account",
                "name": "test_storage",
                "change": {
                    "before": {
                        "name": "storagetest123",
                        "id": "/subscriptions/sub-222/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storagetest123"
                    },
                    "after": {
                        "name": "storage-test-123",
                        "id": "/subscriptions/sub-222/resourceGroups/rg-shared/providers/Microsoft.Storage/storageAccounts/storage-test-123"
                    }
                }
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        env1_path = tmpdir_path / "env1.json"
        env2_path = tmpdir_path / "env2.json"
        norm_path = tmpdir_path / "norm.json"
        html_path = tmpdir_path / "output.html"
        
        # Create normalization config using pattern-based approach
        normalization_config = {
            "name_patterns": [
                {
                    "pattern": "-",
                    "replacement": "",
                    "description": "Remove hyphens from names"
                }
            ],
            "resource_id_patterns": [
                {
                    "pattern": "/subscriptions/[^/]+",
                    "replacement": "/subscriptions/NORMALIZED",
                    "description": "Normalize subscription IDs"
                }
            ]
        }
        
        # Create ignore config that references normalization
        ignore_config = {
            "normalization_config_path": str(norm_path)
        }
        
        ignore_path = tmpdir_path / "ignore.json"
        
        env1_path.write_text(json.dumps(env1_data))
        env2_path.write_text(json.dumps(env2_data))
        norm_path.write_text(json.dumps(normalization_config))
        ignore_path.write_text(json.dumps(ignore_config))
        
        result = subprocess.run(
            [
                "python3", "src/cli/analyze_plan.py", "compare",
                str(env1_path), str(env2_path),
                "--env-names", "dev,prod",
                "--config", str(ignore_path),
                "--html", str(html_path)
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Verify console shows normalization statistics
        text_output = result.stdout
        assert "IGNORE STATISTICS" in text_output, "Console should have IGNORE STATISTICS section"
        assert "Normalized Attributes: 2" in text_output, "Console should show 2 normalized attributes (name, id)"
        
        # Verify HTML summary shows normalization count
        html_output = html_path.read_text()
        assert "Normalized" in html_output, "HTML summary should show Normalized card"
