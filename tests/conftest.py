"""
Pytest configuration for tf-plan-analyzer tests.

Sets up the Python path to allow imports from src/ directory.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set PYTHONPATH for subprocess calls in e2e tests
os.environ['PYTHONPATH'] = str(project_root)
