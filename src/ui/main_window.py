"""
Main application window for CSI Pivot Quote.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QStatusBar,
    QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont

from .quote_form import QuoteForm
from .customer_mgmt import CustomerManagement
from .quote_history import QuoteHistory


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSI Pivot Quote - Insurance Quote Calculator")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize UI
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()

        # Show welcome message
        self.statusBar().showMessage("Ready to create quotes", 3000)

    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_quote_action = QAction("&New Quote", self)
        new_quote_action.setShortcut("Ctrl+N")
        new_quote_action.triggered.connect(self._new_quote)
        file_menu.addAction(new_quote_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        load_rates_action = QAction("&Load Rate Tables", self)
        load_rates_action.triggered.connect(self._load_rate_tables)
        tools_menu.addAction(load_rates_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_central_widget(self):
        """Create main content area with tabs."""
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Create Quote tab
        self.quote_form = QuoteForm(self)
        self.tabs.addTab(self.quote_form, "New Quote")

        # Quote History tab
        self.quote_history = QuoteHistory(self)
        self.tabs.addTab(self.quote_history, "Quote History")

        # Customer Management tab
        self.customer_mgmt = CustomerManagement(self)
        self.tabs.addTab(self.customer_mgmt, "Customers")

        # Set as central widget
        self.setCentralWidget(self.tabs)

    def _create_status_bar(self):
        """Create status bar."""
        self.setStatusBar(QStatusBar())

    def _new_quote(self):
        """Switch to new quote tab and reset form."""
        self.tabs.setCurrentWidget(self.quote_form)
        self.quote_form.reset_form()
        self.statusBar().showMessage("Ready for new quote", 2000)

    def _load_rate_tables(self):
        """Load rate tables from CSV."""
        from .rate_import_dialog import RateImportDialog
        dialog = RateImportDialog(self)
        if dialog.exec():
            # Rates were successfully imported
            self.statusBar().showMessage("Rate tables updated successfully", 5000)

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About CSI Pivot Quote",
            "<h2>CSI Pivot Quote</h2>"
            "<p>Version 1.0</p>"
            "<p>Insurance quote calculator for center pivot irrigation equipment.</p>"
            "<p>© 2025 Western Valley Irrigation Sales and Service, Inc.</p>"
        )

    def update_status(self, message: str, timeout: int = 0):
        """Update status bar message."""
        self.statusBar().showMessage(message, timeout)
