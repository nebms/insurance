"""
Database manager for SQLite connections and operations.
Designed for easy migration to PostgreSQL.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime

from .schema import ALL_TABLES, CREATE_INDEXES


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_path: str = "data/csi_quotes.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_type = "sqlite"

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._initialize_database()

    def _initialize_database(self):
        """Create tables and indexes if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            # Create all tables
            for table_sql in ALL_TABLES:
                cursor.execute(table_sql)

            # Create indexes
            for index_sql in CREATE_INDEXES:
                cursor.execute(index_sql)

            conn.commit()
            print(f"✓ Database initialized: {self.db_path}")

        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to initialize database: {e}")
        finally:
            cursor.close()
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.

        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor.
        Automatically commits on success, rolls back on error.

        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("INSERT ...")
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters (tuple)

        Returns:
            List of rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Execute INSERT query and return last row ID.

        Args:
            query: SQL INSERT statement
            params: Query parameters (tuple)

        Returns:
            int: Last inserted row ID
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute UPDATE/DELETE query and return affected rows.

        Args:
            query: SQL UPDATE/DELETE statement
            params: Query parameters (tuple)

        Returns:
            int: Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database."""
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """
        results = self.execute_query(query, (table_name,))
        return len(results) > 0

    def get_table_row_count(self, table_name: str) -> int:
        """Get number of rows in table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0

    def clear_table(self, table_name: str):
        """Delete all rows from table."""
        query = f"DELETE FROM {table_name}"
        self.execute_update(query)
        print(f"✓ Cleared table: {table_name}")


# Singleton instance
_db_instance = None

def get_db(db_path: str = "data/csi_quotes.db") -> DatabaseManager:
    """Get or create database manager singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance
