"""
Shared test fixtures for Fast6 test suite.

Provides isolated temporary database fixtures so tests never
touch the production database.
"""

import os
import sys
import sqlite3
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure src is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


@pytest.fixture
def tmp_db_dir(tmp_path):
    """Create a temporary directory for database files."""
    db_dir = tmp_path / "data"
    db_dir.mkdir()
    return db_dir


@pytest.fixture
def tmp_db_path(tmp_db_dir):
    """Create a temporary database path (file doesn't exist yet)."""
    return tmp_db_dir / "fast6_test.db"


@pytest.fixture
def isolated_db(tmp_db_path):
    """
    Provide a fully isolated test database.
    
    Patches DB_PATH in both connection.py and migrations.py so all 
    database operations go to a temp file. Runs migrations to set up 
    the full schema. Cleans up automatically after the test.
    
    Usage:
        def test_something(isolated_db):
            from database import add_user
            user_id = add_user("Test", "test@test.com")
            assert user_id is not None
    """
    db_path = tmp_db_path
    
    with patch('database.connection.DB_PATH', db_path), \
         patch('src.database.connection.DB_PATH', db_path):
        # Initialize schema via migrations (v1 creates all tables)
        from database.migrations import run_migrations
        run_migrations()
        yield db_path


@pytest.fixture
def sample_data(isolated_db):
    """
    Provide a database pre-populated with sample data for testing.
    
    Creates:
    - 3 users (Alice, Bob, Charlie)
    - 1 week (2025, week 1)
    - 3 picks (one per user)
    - 2 results (Alice correct first TD, Bob anytime TD)
    
    Returns a dict with all created IDs.
    """
    from database import (
        add_user, add_week, add_pick, add_result
    )
    
    # Users
    alice_id = add_user("Alice", "alice@example.com")
    bob_id = add_user("Bob", "bob@example.com")
    charlie_id = add_user("Charlie", "charlie@example.com")
    
    # Week
    week_id = add_week(2025, 1)
    
    # Picks
    pick_alice = add_pick(alice_id, week_id, 'KC', 'Patrick Mahomes', 150, game_id='gid_001')
    pick_bob = add_pick(bob_id, week_id, 'SF', 'Jauan Jennings', 300, game_id='gid_002')
    pick_charlie = add_pick(charlie_id, week_id, 'BUF', 'Josh Allen', 200, game_id='gid_003')
    
    # Results (Alice = first TD correct, Bob = anytime TD only)
    add_result(pick_alice, 'Patrick Mahomes', True, 1.50, False)
    add_result(pick_bob, 'Jauan Jennings', False, 0.0, True)
    # Charlie has no result (ungraded)
    
    return {
        'users': {'alice': alice_id, 'bob': bob_id, 'charlie': charlie_id},
        'week_id': week_id,
        'picks': {'alice': pick_alice, 'bob': pick_bob, 'charlie': pick_charlie},
    }
