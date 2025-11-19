"""
Main application window for CSI Pivot Quote.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QStatusBar,
    QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont, QKeySequence

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
        new_quote_action.setStatusTip("Create a new quote (Ctrl+N)")
        new_quote_action.triggered.connect(self._new_quote)
        file_menu.addAction(new_quote_action)

        save_quote_action = QAction("&Save Quote", self)
        save_quote_action.setShortcut("Ctrl+S")
        save_quote_action.setStatusTip("Save current quote (Ctrl+S)")
        save_quote_action.triggered.connect(self._save_quote)
        file_menu.addAction(save_quote_action)

        file_menu.addSeparator()

        export_pdf_action = QAction("Export to &PDF", self)
        export_pdf_action.setShortcut("Ctrl+E")
        export_pdf_action.setStatusTip("Export quote to PDF (Ctrl+E)")
        export_pdf_action.triggered.connect(self._export_pdf)
        file_menu.addAction(export_pdf_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application (Ctrl+Q)")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        quote_history_action = QAction("Quote &History", self)
        quote_history_action.setShortcut("Ctrl+H")
        quote_history_action.setStatusTip("Go to quote history (Ctrl+H)")
        quote_history_action.triggered.connect(self._go_to_history)
        view_menu.addAction(quote_history_action)

        customers_action = QAction("&Customers", self)
        customers_action.setShortcut("Ctrl+U")
        customers_action.setStatusTip("Go to customer management (Ctrl+U)")
        customers_action.triggered.connect(self._go_to_customers)
        view_menu.addAction(customers_action)

        view_menu.addSeparator()

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh current view (F5)")
        refresh_action.triggered.connect(self._refresh_current_view)
        view_menu.addAction(refresh_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        load_template_action = QAction("Load &Template", self)
        load_template_action.setShortcut("Ctrl+T")
        load_template_action.setStatusTip("Load quote template (Ctrl+T)")
        load_template_action.triggered.connect(self._load_template)
        tools_menu.addAction(load_template_action)

        search_action = QAction("&Search/Filter", self)
        search_action.setShortcut("Ctrl+F")
        search_action.setStatusTip("Focus search box (Ctrl+F)")
        search_action.triggered.connect(self._focus_search)
        tools_menu.addAction(search_action)

        tools_menu.addSeparator()

        load_rates_action = QAction("Load &Rate Tables", self)
        load_rates_action.triggered.connect(self._load_rate_tables)
        tools_menu.addAction(load_rates_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.setStatusTip("Show keyboard shortcuts (F1)")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

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

    def _save_quote(self):
        """Save current quote (Ctrl+S)."""
        if self.tabs.currentWidget() == self.quote_form:
            # Trigger calculation which leads to save dialog
            self.quote_form._calculate_quote()
            self.statusBar().showMessage("Calculate quote to save", 2000)
        else:
            self.statusBar().showMessage("Switch to New Quote tab to create a quote", 2000)

    def _export_pdf(self):
        """Export quote to PDF (Ctrl+E)."""
        if self.tabs.currentWidget() == self.quote_history:
            self.statusBar().showMessage("Select a quote and click Export PDF", 2000)
        else:
            self.statusBar().showMessage("Go to Quote History to export PDFs", 2000)

    def _go_to_history(self):
        """Go to quote history (Ctrl+H)."""
        self.tabs.setCurrentWidget(self.quote_history)
        self.statusBar().showMessage("Quote History", 1000)

    def _go_to_customers(self):
        """Go to customer management (Ctrl+U)."""
        self.tabs.setCurrentWidget(self.customer_mgmt)
        self.statusBar().showMessage("Customer Management", 1000)

    def _refresh_current_view(self):
        """Refresh current view (F5)."""
        current_widget = self.tabs.currentWidget()

        if current_widget == self.quote_history:
            self.quote_history._load_quotes()
            self.statusBar().showMessage("Quote history refreshed", 2000)
        elif current_widget == self.customer_mgmt:
            self.customer_mgmt._load_customers()
            self.statusBar().showMessage("Customer list refreshed", 2000)
        else:
            self.statusBar().showMessage("Nothing to refresh on this tab", 2000)

    def _load_template(self):
        """Load quote template (Ctrl+T)."""
        if self.tabs.currentWidget() == self.quote_form:
            self.quote_form._load_template()
        else:
            self.tabs.setCurrentWidget(self.quote_form)
            self.statusBar().showMessage("Switched to New Quote - press Ctrl+T again to load template", 2000)

    def _focus_search(self):
        """Focus search box (Ctrl+F)."""
        if self.tabs.currentWidget() == self.quote_history:
            if hasattr(self.quote_history, 'search_input'):
                self.quote_history.search_input.setFocus()
                self.quote_history.search_input.selectAll()
                self.statusBar().showMessage("Search box focused", 1000)
        else:
            self.tabs.setCurrentWidget(self.quote_history)
            self.statusBar().showMessage("Switched to Quote History - press Ctrl+F again to focus search", 2000)

    def _show_shortcuts(self):
        """Show keyboard shortcuts help (F1)."""
        shortcuts_text = """
        <h2>Keyboard Shortcuts</h2>

        <h3>File Operations</h3>
        <table cellpadding='5'>
        <tr><td><b>Ctrl+N</b></td><td>New Quote</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save Quote (triggers calculation)</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Export to PDF</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>
        </table>

        <h3>Navigation</h3>
        <table cellpadding='5'>
        <tr><td><b>Ctrl+H</b></td><td>Go to Quote History</td></tr>
        <tr><td><b>Ctrl+U</b></td><td>Go to Customers</td></tr>
        <tr><td><b>F5</b></td><td>Refresh Current View</td></tr>
        </table>

        <h3>Tools</h3>
        <table cellpadding='5'>
        <tr><td><b>Ctrl+T</b></td><td>Load Template</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Focus Search/Filter</td></tr>
        </table>

        <h3>Help</h3>
        <table cellpadding='5'>
        <tr><td><b>F1</b></td><td>Show This Help</td></tr>
        </table>

        <p style='margin-top: 20px;'><i>Tip: Hover over menu items to see shortcuts in the status bar.</i></p>
        """

        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            shortcuts_text
        )
