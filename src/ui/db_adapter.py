"""
Database adapter layer for migrated views

Bridges old database module imports to new API layer to minimize view changes during migration.
This is a temporary compatibility layer - views should be refactored to use API layer directly.
"""

# Re-export database functions from original location to avoid breaking imports
# This allows views to use: from database import X (via sys.path manipulation)
# during the migration phase

# For now, import from old database module
# This will be removed once views are fully migrated to use API layer directly
import sys
import os

# Add src to path to access old database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from database import *
except Exception as e:
    print(f"Warning: Could not import from database module: {e}")
