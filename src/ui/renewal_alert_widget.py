"""
Renewal alert widget for displaying urgent renewal notifications.
Shows at startup if there are renewals requiring attention.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from models.renewal import RenewalRepository
from models.quote import QuoteRepository
from models.customer import CustomerRepository


class RenewalAlertDialog(QDialog):
    """Dialog showing urgent renewal alerts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renewal_repo = RenewalRepository()
        self.quote_repo = QuoteRepository()
        self.customer_repo = CustomerRepository()

        self.setWindowTitle("Renewal Alerts")
        self.setModal(False)  # Allow user to interact with main window
        self.resize(800, 400)

        self.urgent_renewals = []
        self._init_ui()
        self._load_urgent_renewals()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("⚠️ Urgent Renewal Alerts")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #ef4444; padding: 10px;")
        layout.addWidget(header)

        # Message
        self.message_label = QLabel()
        layout.addWidget(self.message_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Quote #", "Customer", "Agent", "Expires", "Days Left", "Status"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        view_all_btn = QPushButton("View Renewal Dashboard")
        view_all_btn.clicked.connect(self._view_dashboard)
        view_all_btn.setStyleSheet("background-color: #3b82f6; color: white;")

        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(view_all_btn)
        button_layout.addWidget(dismiss_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_urgent_renewals(self):
        """Load urgent renewals (< 30 days)."""
        # Get renewals due in next 30 days
        self.urgent_renewals = self.renewal_repo.get_upcoming_renewals(days_ahead=30)

        # Filter to only show non-completed renewals
        self.urgent_renewals = [r for r in self.urgent_renewals
                               if r.status not in ['bound', 'declined', 'lapsed']]

        # Update message
        count = len(self.urgent_renewals)
        if count == 0:
            self.message_label.setText("No urgent renewals at this time.")
            self.message_label.setStyleSheet("color: #10b981; padding: 10px;")
        elif count == 1:
            self.message_label.setText(
                "You have 1 policy expiring in the next 30 days that requires attention."
            )
            self.message_label.setStyleSheet("color: #f59e0b; padding: 10px;")
        else:
            self.message_label.setText(
                f"You have {count} policies expiring in the next 30 days that require attention."
            )
            self.message_label.setStyleSheet("color: #ef4444; padding: 10px;")

        # Populate table
        self._populate_table()

    def _populate_table(self):
        """Populate table with urgent renewals."""
        self.table.setRowCount(0)

        # Sort by days until expiration
        sorted_renewals = sorted(self.urgent_renewals,
                                key=lambda r: r.calculate_days_until_expiration())

        for row, renewal in enumerate(sorted_renewals):
            self.table.insertRow(row)

            # Get quote info
            quote = self.quote_repo.get_by_id(renewal.original_quote_id)
            if not quote:
                continue

            customer_name = "N/A"
            if quote.customer_id:
                customer = self.customer_repo.get_by_id(quote.customer_id)
                if customer:
                    customer_name = customer.name

            days_left = renewal.calculate_days_until_expiration()

            # Quote number
            self.table.setItem(row, 0, QTableWidgetItem(quote.quote_number))

            # Customer
            self.table.setItem(row, 1, QTableWidgetItem(customer_name))

            # Agent
            self.table.setItem(row, 2, QTableWidgetItem(quote.agent_name or "N/A"))

            # Expiration date
            self.table.setItem(row, 3, QTableWidgetItem(renewal.policy_end_date))

            # Days left (with color coding)
            days_item = QTableWidgetItem(str(days_left))
            if days_left < 7:
                days_item.setBackground(QColor("#ef4444"))
                days_item.setForeground(QColor("white"))
            elif days_left < 15:
                days_item.setBackground(QColor("#f59e0b"))
                days_item.setForeground(QColor("white"))
            elif days_left < 30:
                days_item.setBackground(QColor("#3b82f6"))
                days_item.setForeground(QColor("white"))
            self.table.setItem(row, 4, days_item)

            # Status
            status_text = renewal.status.capitalize()
            if renewal.status == 'pending' and not renewal.renewal_quote_id:
                status_text += " (Needs Quote)"
            elif renewal.status == 'generated' and not renewal.renewal_sent_date:
                status_text += " (Not Sent)"
            self.table.setItem(row, 5, QTableWidgetItem(status_text))

    def _view_dashboard(self):
        """Navigate to renewal dashboard."""
        # Signal to parent window to switch to renewals tab
        self.accept()
        if self.parent():
            # Assuming parent is main window with tabs
            if hasattr(self.parent(), 'tabs') and hasattr(self.parent(), 'renewal_dashboard'):
                self.parent().tabs.setCurrentWidget(self.parent().renewal_dashboard)

    @staticmethod
    def show_if_urgent(parent=None) -> bool:
        """
        Show alert dialog if there are urgent renewals.

        Args:
            parent: Parent widget

        Returns:
            True if dialog was shown, False otherwise
        """
        # Check for urgent renewals
        renewal_repo = RenewalRepository()
        urgent = renewal_repo.get_upcoming_renewals(days_ahead=30)
        urgent = [r for r in urgent if r.status not in ['bound', 'declined', 'lapsed']]

        if urgent:
            dialog = RenewalAlertDialog(parent)
            dialog.exec()
            return True

        return False


def check_and_notify_renewals(parent=None) -> dict:
    """
    Check for urgent renewals and return notification data.

    Args:
        parent: Parent widget

    Returns:
        Dictionary with renewal notification info
    """
    renewal_repo = RenewalRepository()

    # Get urgent renewals (< 30 days)
    urgent = renewal_repo.get_upcoming_renewals(days_ahead=30)
    urgent = [r for r in urgent if r.status not in ['bound', 'declined', 'lapsed']]

    # Get pending reminders
    reminders_due = renewal_repo.get_reminders_due()

    # Get statistics
    stats = renewal_repo.get_renewal_statistics()

    return {
        'urgent_count': len(urgent),
        'urgent_renewals': urgent,
        'reminders_due': len(reminders_due),
        'pending_count': stats.get('by_status', {}).get('pending', 0),
        'generated_count': stats.get('by_status', {}).get('generated', 0),
        'should_alert': len(urgent) > 0 or len(reminders_due) > 0
    }
