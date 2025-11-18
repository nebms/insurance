"""
Tests for database functionality.
"""

import os
import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import DatabaseManager


@pytest.fixture
def test_db():
    """Create a test database."""
    db_path = "data/test_csi_quotes.db"

    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create new test database
    db = DatabaseManager(db_path)

    yield db

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


def test_database_initialization(test_db):
    """Test that database initializes correctly."""
    assert os.path.exists(test_db.db_path)
    print("✓ Database file created")


def test_tables_created(test_db):
    """Test that all tables are created."""
    expected_tables = [
        'states',
        'customers',
        'quotes',
        'pivot_rates_under_20',
        'pivot_rates_20_to_34',
        'pivot_rates_35_plus',
        'ancillary_rates'
    ]

    for table in expected_tables:
        assert test_db.table_exists(table), f"Table {table} not found"
        print(f"✓ Table exists: {table}")


def test_foreign_keys_enabled(test_db):
    """Test that foreign keys are enabled."""
    result = test_db.execute_query("PRAGMA foreign_keys")
    assert result[0][0] == 1, "Foreign keys not enabled"
    print("✓ Foreign keys enabled")


def test_insert_and_query(test_db):
    """Test basic insert and query operations."""
    # Insert a state
    query = "INSERT INTO states (code, name, is_special_state) VALUES (?, ?, ?)"
    test_db.execute_insert(query, ('OK', 'Oklahoma', 1))

    # Query the state
    result = test_db.execute_query("SELECT * FROM states WHERE code = ?", ('OK',))
    assert len(result) == 1
    assert result[0]['name'] == 'Oklahoma'
    assert result[0]['is_special_state'] == 1
    print("✓ Insert and query successful")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
