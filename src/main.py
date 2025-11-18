"""
CSI Pivot Quote - Main Application Entry Point with Authentication
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import get_db
from database.data_loader import load_states, load_sample_rates
from ui.app_launcher import main as app_launcher_main


def initialize_database():
    """Initialize database on first run."""
    db = get_db()

    # Check if states are loaded
    state_count = db.get_table_row_count('states')
    if state_count == 0:
        print("First run detected. Loading initial data...")
        load_states()
        load_sample_rates()
        print("✓ Database initialized")
    else:
        print(f"✓ Database ready ({state_count} states loaded)")


def main():
    """Main application entry point."""
    # Initialize database
    initialize_database()

    # Run application with authentication
    # This will show login dialog and route users based on role
    sys.exit(app_launcher_main())


if __name__ == "__main__":
    main()
