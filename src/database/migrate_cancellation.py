#!/usr/bin/env python3
"""
Database migration to add policy cancellation fields.
Adds fields to track when and why policies are cancelled, and calculate return premiums.
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


def create_backup(db_path: str) -> str:
    """Create a backup of the database before migration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"Creating backup: {backup_path}")
    return backup_path


def migrate_cancellation_fields(db_path: str = "data/csi_quotes.db"):
    """Add cancellation fields to quotes table."""

    print("=" * 60)
    print("CSI Pivot Quote - Policy Cancellation Migration")
    print("=" * 60)
    print()

    # Create backup
    backup_path = create_backup(db_path)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting cancellation migration...")

        # Check if cancellation fields already exist
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add new cancellation fields to quotes table
        new_fields = {
            'is_cancelled': "ALTER TABLE quotes ADD COLUMN is_cancelled INTEGER DEFAULT 0",
            'cancellation_date': "ALTER TABLE quotes ADD COLUMN cancellation_date TEXT",
            'cancellation_effective_date': "ALTER TABLE quotes ADD COLUMN cancellation_effective_date TEXT",
            'cancellation_reason': "ALTER TABLE quotes ADD COLUMN cancellation_reason TEXT",
            'cancellation_type': "ALTER TABLE quotes ADD COLUMN cancellation_type TEXT",
            'return_premium': "ALTER TABLE quotes ADD COLUMN return_premium REAL DEFAULT 0",
            'cancelled_by_user_id': "ALTER TABLE quotes ADD COLUMN cancelled_by_user_id INTEGER",
            'cancellation_notes': "ALTER TABLE quotes ADD COLUMN cancellation_notes TEXT"
        }

        for field_name, alter_query in new_fields.items():
            if field_name not in columns:
                print(f"  Adding field: {field_name}")
                cursor.execute(alter_query)
            else:
                print(f"  Field already exists: {field_name}")

        # Create indexes for performance
        print("Creating indexes...")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_quotes_is_cancelled ON quotes(is_cancelled)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_cancellation_date ON quotes(cancellation_date)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_cancellation_effective ON quotes(cancellation_effective_date)"
        ]

        for index_query in indexes:
            cursor.execute(index_query)

        conn.commit()
        print("✓ Policy cancellation migration completed successfully!")

        # Show statistics
        print()
        print("Database Statistics:")
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE is_bound = 1")
        bound_count = cursor.fetchone()[0]
        print(f"  Total bound policies: {bound_count}")

        cursor.execute("SELECT COUNT(*) FROM quotes WHERE is_cancelled = 1")
        cancelled_count = cursor.fetchone()[0]
        print(f"  Cancelled policies: {cancelled_count}")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        print(f"Rolling back changes. Database backup available at: {backup_path}")
        raise
    finally:
        conn.close()

    print()
    print("Migration completed successfully!")
    print("Your database is now ready for policy cancellation tracking.")


if __name__ == "__main__":
    migrate_cancellation_fields()
