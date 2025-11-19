"""
Database migration script for policy binding and document tracking.
Adds policy management fields and document attachment support.

Run this script to upgrade existing databases to support policy binding.
"""

import sqlite3
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = "data/csi_quotes.db"


def migrate_database():
    """Migrate database to support policy binding and documents."""
    # Create backup first
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if Path(DB_PATH).exists():
        print(f"Creating backup: {backup_path}")
        shutil.copy2(DB_PATH, backup_path)

    # Connect directly to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        print("Starting policy binding migration...")

        # Check what fields already exist
        cursor.execute("PRAGMA table_info(quotes)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        # Add new policy binding fields to quotes table
        new_fields = {
            'policy_number': "ALTER TABLE quotes ADD COLUMN policy_number TEXT",
            'bound_date': "ALTER TABLE quotes ADD COLUMN bound_date TEXT",
            'bound_by_user_id': "ALTER TABLE quotes ADD COLUMN bound_by_user_id INTEGER",
            'effective_date': "ALTER TABLE quotes ADD COLUMN effective_date TEXT",
            'expiration_date': "ALTER TABLE quotes ADD COLUMN expiration_date TEXT",
            'carrier_name': "ALTER TABLE quotes ADD COLUMN carrier_name TEXT",
            'payment_status': "ALTER TABLE quotes ADD COLUMN payment_status TEXT DEFAULT 'pending'",
            'payment_method': "ALTER TABLE quotes ADD COLUMN payment_method TEXT",
            'policy_received_date': "ALTER TABLE quotes ADD COLUMN policy_received_date TEXT"
        }

        for field_name, sql in new_fields.items():
            if field_name not in existing_columns:
                print(f"Adding {field_name} column to quotes table...")
                cursor.execute(sql)

        # Check if policy_documents table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='policy_documents'
        """)

        if not cursor.fetchone():
            print("Creating policy_documents table...")
            cursor.execute("""
                CREATE TABLE policy_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_id INTEGER NOT NULL,
                    document_type TEXT NOT NULL,
                    document_name TEXT,
                    file_path TEXT,
                    uploaded_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    uploaded_by_user_id INTEGER,
                    received_from TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE
                )
            """)

        # Create indexes
        print("Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_quotes_policy_number ON quotes(policy_number)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_bound_date ON quotes(bound_date)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_effective_date ON quotes(effective_date)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_payment_status ON quotes(payment_status)",
            "CREATE INDEX IF NOT EXISTS idx_policy_docs_quote ON policy_documents(quote_id)",
            "CREATE INDEX IF NOT EXISTS idx_policy_docs_type ON policy_documents(document_type)"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        # Create documents directory
        docs_dir = Path("data/policy_documents")
        docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created documents directory: {docs_dir}")

        conn.commit()
        print("✓ Policy binding migration completed successfully!")

        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quote_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotes WHERE is_bound = 1")
        bound_count = cursor.fetchone()[0]

        print(f"\nDatabase Statistics:")
        print(f"  Total quotes: {quote_count}")
        print(f"  Bound policies: {bound_count}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("CSI Pivot Quote - Policy Binding Migration")
    print("=" * 60)
    print()

    success = migrate_database()

    print()
    if success:
        print("Migration completed successfully!")
        print("Your database is now ready for policy binding and document tracking.")
    else:
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)
