"""
Database migration script for renewal tracking feature.
Adds renewal fields to quotes table and creates renewals table.

Run this script to upgrade existing databases to support renewal tracking.
"""

import sqlite3
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = "data/csi_quotes.db"


def migrate_database():
    """Migrate database to support renewal tracking."""
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
        print("Starting renewal tracking migration...")

        # Check if migration is needed
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add new columns to quotes table if they don't exist
        if 'policy_start_date' not in columns:
            print("Adding policy_start_date column to quotes table...")
            cursor.execute("ALTER TABLE quotes ADD COLUMN policy_start_date TEXT")

        if 'policy_end_date' not in columns:
            print("Adding policy_end_date column to quotes table...")
            cursor.execute("ALTER TABLE quotes ADD COLUMN policy_end_date TEXT")

        if 'is_bound' not in columns:
            print("Adding is_bound column to quotes table...")
            cursor.execute("ALTER TABLE quotes ADD COLUMN is_bound INTEGER DEFAULT 0")

        if 'original_quote_id' not in columns:
            print("Adding original_quote_id column to quotes table...")
            cursor.execute("ALTER TABLE quotes ADD COLUMN original_quote_id INTEGER REFERENCES quotes(id)")

        # Check if renewals table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='renewals'
        """)
        if not cursor.fetchone():
            print("Creating renewals table...")
            cursor.execute("""
                CREATE TABLE renewals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_quote_id INTEGER NOT NULL,
                    renewal_quote_id INTEGER,

                    -- Renewal timeline
                    policy_end_date TEXT NOT NULL,
                    renewal_due_date TEXT NOT NULL,

                    -- Renewal status
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'generated', 'sent', 'bound', 'declined', 'lapsed')),

                    -- Reminder tracking
                    reminder_90_days_sent INTEGER DEFAULT 0,
                    reminder_90_days_date TEXT,
                    reminder_60_days_sent INTEGER DEFAULT 0,
                    reminder_60_days_date TEXT,
                    reminder_30_days_sent INTEGER DEFAULT 0,
                    reminder_30_days_date TEXT,
                    reminder_final_sent INTEGER DEFAULT 0,
                    reminder_final_date TEXT,

                    -- Renewal quote details (when generated)
                    renewal_generated_date TEXT,
                    renewal_sent_date TEXT,
                    renewal_premium REAL,
                    premium_change_percent REAL,

                    -- Outcome tracking
                    outcome_date TEXT,
                    outcome_notes TEXT,
                    declined_reason TEXT,

                    -- Metadata
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (original_quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
                    FOREIGN KEY (renewal_quote_id) REFERENCES quotes(id)
                )
            """)

        # Create indexes
        print("Creating renewal indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_quotes_policy_end ON quotes(policy_end_date)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_is_bound ON quotes(is_bound)",
            "CREATE INDEX IF NOT EXISTS idx_renewals_original_quote ON renewals(original_quote_id)",
            "CREATE INDEX IF NOT EXISTS idx_renewals_renewal_quote ON renewals(renewal_quote_id)",
            "CREATE INDEX IF NOT EXISTS idx_renewals_status ON renewals(status)",
            "CREATE INDEX IF NOT EXISTS idx_renewals_policy_end ON renewals(policy_end_date)",
            "CREATE INDEX IF NOT EXISTS idx_renewals_due_date ON renewals(renewal_due_date)"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        print("✓ Renewal tracking migration completed successfully!")

        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quote_count = cursor.fetchone()[0]
        print(f"\nDatabase Statistics:")
        print(f"  Total quotes: {quote_count}")

        cursor.execute("SELECT COUNT(*) FROM renewals")
        renewal_count = cursor.fetchone()[0]
        print(f"  Total renewals: {renewal_count}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("CSI Pivot Quote - Renewal Tracking Migration")
    print("=" * 60)
    print()

    success = migrate_database()

    print()
    if success:
        print("Migration completed successfully!")
        print("Your database is now ready to track renewals.")
    else:
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)
