"""
Main admin portal for rate management.
Provides tabbed interface for managing all rate tables.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.auth_manager import User
from ui.admin.rate_viewer import RateViewer


class AdminPortal(QWidget):
    """Main admin portal widget for rate management."""

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.parent = parent

        # Verify user is admin
        if self.user.role != 'admin':
            raise ValueError("Admin portal requires admin role")

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Admin Portal - Rate Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)

        # User info
        user_info = QLabel(f"🔒 {self.user.full_name} ({self.user.username})")
        user_info_font = QFont()
        user_info_font.setPointSize(10)
        user_info.setFont(user_info_font)

        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self._logout)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(user_info)
        header_layout.addWidget(logout_btn)

        layout.addLayout(header_layout)

        # Tab widget for different rate tables
        self.tabs = QTabWidget()

        # Create rate viewer tabs for each table type
        self.pivot_under_20_tab = RateViewer(
            'pivot_rates_under_20',
            'Pivot Rates Under 20 Years',
            self.user,
            self
        )
        self.pivot_20_to_34_tab = RateViewer(
            'pivot_rates_20_to_34',
            'Pivot Rates 20-34 Years',
            self.user,
            self
        )
        self.pivot_35_plus_tab = RateViewer(
            'pivot_rates_35_plus',
            'Pivot Rates 35+ Years',
            self.user,
            self
        )
        self.ancillary_tab = RateViewer(
            'ancillary_rates',
            'Ancillary Equipment Rates',
            self.user,
            self
        )

        self.tabs.addTab(self.pivot_under_20_tab, "Pivot <20")
        self.tabs.addTab(self.pivot_20_to_34_tab, "Pivot 20-34")
        self.tabs.addTab(self.pivot_35_plus_tab, "Pivot 35+")
        self.tabs.addTab(self.ancillary_tab, "Ancillary")

        layout.addWidget(self.tabs)

        # Global action buttons
        button_layout = QHBoxLayout()

        view_history_btn = QPushButton("View Change History")
        view_history_btn.clicked.connect(self._view_change_history)

        import_rates_btn = QPushButton("Import Rates from CSV")
        import_rates_btn.clicked.connect(self._import_rates)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        button_layout.addWidget(view_history_btn)
        button_layout.addWidget(import_rates_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _logout(self):
        """Handle logout."""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Close admin portal and return to login
            self.close()
            if self.parent:
                self.parent.show_login()

    def _view_change_history(self):
        """View rate change history (audit log)."""
        # Will be implemented in Phase 5
        QMessageBox.information(
            self,
            "Change History",
            "Audit log viewer will be implemented in Phase 5:\n"
            "Export and Audit Log Viewer"
        )

    def _import_rates(self):
        """Import rates from CSV file."""
        # Use existing rate import dialog
        from ui.rate_import_dialog import RateImportDialog

        dialog = RateImportDialog(self)
        if dialog.exec():
            QMessageBox.information(
                self,
                "Rates Imported",
                "Rate tables have been updated successfully.\n\n"
                "Changes are now available for quote calculations."
            )
            # Refresh current tab (will be implemented in Phase 3)

    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            "Close Admin Portal",
            "Are you sure you want to close the admin portal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from database.auth_manager import User

    app = QApplication(sys.argv)

    # Create test admin user
    test_user = User(
        id=1,
        username="admin",
        full_name="Administrator",
        email=None,
        role="admin",
        is_active=True,
        created_at="2025-01-01",
        last_login=None
    )

    portal = AdminPortal(test_user)
    portal.setWindowTitle("CSI Pivot Quote - Admin Portal")
    portal.resize(900, 600)
    portal.show()

    sys.exit(app.exec())
