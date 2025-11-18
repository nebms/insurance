"""
CSI Pivot Quote - Main Application Entry Point
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from database.db_manager import get_db
from database.data_loader import load_states, load_sample_rates


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

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("CSI Pivot Quote")
    app.setOrganizationName("Western Valley Irrigation")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
