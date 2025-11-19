"""
Renewal Dashboard and Management Interface.
Displays upcoming renewals, sends reminders, and manages renewal lifecycle.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QDialog, QTextEdit, QLineEdit, QDateEdit, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date, timedelta

from models.renewal import Renewal, RenewalRepository
from models.quote import Quote, QuoteRepository
from models.customer import CustomerRepository
from services.renewal_service import RenewalService
from services.notification_service import get_notification_service
from ui.loading_widgets import LoadingSpinner


class RenewalDashboard(QWidget):
    """Renewal dashboard and management interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renewal_repo = RenewalRepository()
        self.quote_repo = QuoteRepository()
        self.customer_repo = CustomerRepository()
        self.renewal_service = RenewalService()
        self.notification_service = get_notification_service()

        self.renewals = []
        self.filtered_renewals = []

        self._init_ui()
        self._load_renewals()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title and stats
        title_layout = QHBoxLayout()

        title = QLabel("Renewal Management Dashboard")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_renewals)
        title_layout.addWidget(refresh_btn)

        # Process renewals button
        process_btn = QPushButton("Process Daily Renewals")
        process_btn.clicked.connect(self._process_daily_renewals)
        process_btn.setStyleSheet("background-color: #3b82f6; color: white;")
        title_layout.addWidget(process_btn)

        layout.addLayout(title_layout)

        # Statistics cards
        self.stats_group = self._create_statistics_group()
        layout.addWidget(self.stats_group)

        # Filters
        filter_group = self._create_filter_group()
        layout.addWidget(filter_group)

        # Renewals table
        table_layout = QVBoxLayout()

        # Results label
        self.results_label = QLabel("Showing: 0 renewals")
        table_layout.addWidget(self.results_label)

        # Loading spinner
        self.loading_spinner = LoadingSpinner(self, size=16)
        self.loading_spinner.hide()
        table_layout.addWidget(self.loading_spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Quote #", "Customer", "Agent", "Expires", "Days Left",
            "Status", "Renewal Quote", "Premium Change", "Last Reminder", "Actions"
        ])

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(9, 150)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        table_layout.addWidget(self.table)
        layout.addLayout(table_layout)

        self.setLayout(layout)

    def _create_statistics_group(self) -> QGroupBox:
        """Create statistics cards group."""
        group = QGroupBox("Renewal Statistics")
        grid = QGridLayout()

        # Stats labels
        self.stat_urgent = QLabel("0")
        self.stat_30days = QLabel("0")
        self.stat_60days = QLabel("0")
        self.stat_90days = QLabel("0")
        self.stat_pending_reminders = QLabel("0")
        self.stat_avg_change = QLabel("0%")

        # Style stats
        for stat in [self.stat_urgent, self.stat_30days, self.stat_60days,
                     self.stat_90days, self.stat_pending_reminders, self.stat_avg_change]:
            font = QFont()
            font.setPointSize(18)
            font.setBold(True)
            stat.setFont(font)
            stat.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create stat cards
        grid.addWidget(self._create_stat_card("Urgent (< 30 days)", self.stat_urgent, "#ef4444"), 0, 0)
        grid.addWidget(self._create_stat_card("Next 30 Days", self.stat_30days, "#f59e0b"), 0, 1)
        grid.addWidget(self._create_stat_card("Next 60 Days", self.stat_60days, "#3b82f6"), 0, 2)
        grid.addWidget(self._create_stat_card("Next 90 Days", self.stat_90days, "#10b981"), 0, 3)
        grid.addWidget(self._create_stat_card("Pending Reminders", self.stat_pending_reminders, "#8b5cf6"), 0, 4)
        grid.addWidget(self._create_stat_card("Avg Premium Change", self.stat_avg_change, "#6366f1"), 0, 5)

        group.setLayout(grid)
        return group

    def _create_stat_card(self, title: str, value_label: QLabel, color: str) -> QWidget:
        """Create a statistics card."""
        card = QWidget()
        card.setStyleSheet(f"background-color: {color}; border-radius: 8px; padding: 10px;")

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 11px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label.setStyleSheet("color: white;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def _create_filter_group(self) -> QGroupBox:
        """Create filter controls."""
        group = QGroupBox("Filters")
        layout = QHBoxLayout()

        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", None)
        self.status_filter.addItem("Pending", "pending")
        self.status_filter.addItem("Generated", "generated")
        self.status_filter.addItem("Sent", "sent")
        self.status_filter.addItem("Bound", "bound")
        self.status_filter.addItem("Declined", "declined")
        self.status_filter.addItem("Lapsed", "lapsed")
        self.status_filter.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.status_filter)

        # Days until expiration filter
        layout.addWidget(QLabel("Days Until Expiration:"))
        self.days_filter = QComboBox()
        self.days_filter.addItem("All", None)
        self.days_filter.addItem("< 30 days", 30)
        self.days_filter.addItem("< 60 days", 60)
        self.days_filter.addItem("< 90 days", 90)
        self.days_filter.addItem("< 180 days", 180)
        self.days_filter.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.days_filter)

        layout.addStretch()

        # Clear filters
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(clear_btn)

        group.setLayout(layout)
        return group

    def _load_renewals(self):
        """Load renewals from database."""
        self.loading_spinner.start()
        self.results_label.setText("Loading renewals...")

        try:
            # Get all renewals
            self.renewals = self.renewal_repo.get_all(limit=500)

            # Update statistics
            dashboard_data = self.renewal_service.get_renewal_dashboard_data()
            self.stat_urgent.setText(str(dashboard_data['urgent_renewals']))
            self.stat_30days.setText(str(dashboard_data['upcoming_renewals_30']))
            self.stat_60days.setText(str(dashboard_data['upcoming_renewals_60']))
            self.stat_90days.setText(str(dashboard_data['upcoming_renewals_90']))
            self.stat_pending_reminders.setText(str(dashboard_data['reminders_pending']))

            avg_change = dashboard_data['statistics'].get('avg_premium_change', 0)
            self.stat_avg_change.setText(f"{avg_change:+.1f}%")

            # Apply filters
            self._apply_filters()

        finally:
            self.loading_spinner.stop()

    def _apply_filters(self):
        """Apply filters to renewals list."""
        status = self.status_filter.currentData()
        days = self.days_filter.currentData()

        filtered = []
        for renewal in self.renewals:
            # Status filter
            if status and renewal.status != status:
                continue

            # Days filter
            if days:
                days_until = renewal.calculate_days_until_expiration()
                if days_until < 0 or days_until > days:
                    continue

            filtered.append(renewal)

        self.filtered_renewals = filtered
        self._populate_table(filtered)
        self.results_label.setText(f"Showing: {len(filtered)} of {len(self.renewals)} renewals")

    def _clear_filters(self):
        """Clear all filters."""
        self.status_filter.setCurrentIndex(0)
        self.days_filter.setCurrentIndex(0)

    def _populate_table(self, renewals: list):
        """Populate table with renewals."""
        self.table.setRowCount(0)

        for row, renewal in enumerate(renewals):
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
            if days_left < 0:
                days_item.setBackground(QColor("#ef4444"))
                days_item.setForeground(QColor("white"))
            elif days_left < 30:
                days_item.setBackground(QColor("#f59e0b"))
                days_item.setForeground(QColor("white"))
            elif days_left < 60:
                days_item.setBackground(QColor("#3b82f6"))
                days_item.setForeground(QColor("white"))
            self.table.setItem(row, 4, days_item)

            # Status
            status_item = QTableWidgetItem(renewal.status.capitalize())
            self.table.setItem(row, 5, status_item)

            # Renewal quote number
            renewal_quote_num = ""
            if renewal.renewal_quote_id:
                renewal_quote = self.quote_repo.get_by_id(renewal.renewal_quote_id)
                if renewal_quote:
                    renewal_quote_num = renewal_quote.quote_number
            self.table.setItem(row, 6, QTableWidgetItem(renewal_quote_num))

            # Premium change
            premium_change = ""
            if renewal.premium_change_percent is not None:
                premium_change = f"{renewal.premium_change_percent:+.1f}%"
            self.table.setItem(row, 7, QTableWidgetItem(premium_change))

            # Last reminder
            last_reminder = "None"
            if renewal.reminder_final_sent:
                last_reminder = f"Final ({renewal.reminder_final_date})"
            elif renewal.reminder_30_days_sent:
                last_reminder = f"30-day ({renewal.reminder_30_days_date})"
            elif renewal.reminder_60_days_sent:
                last_reminder = f"60-day ({renewal.reminder_60_days_date})"
            elif renewal.reminder_90_days_sent:
                last_reminder = f"90-day ({renewal.reminder_90_days_date})"
            self.table.setItem(row, 8, QTableWidgetItem(last_reminder))

            # Actions button
            actions_btn = QPushButton("Actions ▼")
            actions_btn.clicked.connect(lambda checked, r=renewal: self._show_actions(r))
            self.table.setCellWidget(row, 9, actions_btn)

    def _show_actions(self, renewal: Renewal):
        """Show actions menu for renewal."""
        from PyQt6.QtWidgets import QMenu

        menu = QMenu(self)

        # View details
        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self._view_renewal_details(renewal))

        menu.addSeparator()

        # Generate renewal quote
        if not renewal.renewal_quote_id:
            generate_action = menu.addAction("Generate Renewal Quote")
            generate_action.triggered.connect(lambda: self._generate_renewal_quote(renewal))

        # Send reminder
        next_reminder = renewal.get_next_reminder_due()
        if next_reminder:
            _, reminder_type = next_reminder
            send_reminder_action = menu.addAction(f"Send {reminder_type.replace('_', '-')} Reminder")
            send_reminder_action.triggered.connect(lambda: self._send_reminder(renewal, reminder_type))

        menu.addSeparator()

        # Mark as bound
        if renewal.status in ['generated', 'sent']:
            bind_action = menu.addAction("Mark as Bound")
            bind_action.triggered.connect(lambda: self._mark_as_bound(renewal))

        # Mark as declined
        if renewal.status not in ['declined', 'lapsed', 'bound']:
            decline_action = menu.addAction("Mark as Declined")
            decline_action.triggered.connect(lambda: self._mark_as_declined(renewal))

        # Show menu at cursor
        menu.exec(self.mapToGlobal(self.sender().pos()))

    def _view_renewal_details(self, renewal: Renewal):
        """View detailed renewal information."""
        dialog = RenewalDetailsDialog(renewal, self)
        dialog.exec()

    def _generate_renewal_quote(self, renewal: Renewal):
        """Generate renewal quote."""
        reply = QMessageBox.question(
            self,
            "Generate Renewal Quote",
            f"Generate renewal quote for this policy?\n\n"
            f"Original Quote ID: {renewal.original_quote_id}\n"
            f"Policy Expires: {renewal.policy_end_date}\n\n"
            f"Current rates will be applied.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                renewal_quote = self.renewal_service.generate_renewal_quote(renewal.id)
                if renewal_quote:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Renewal quote generated successfully!\n\n"
                        f"New Quote Number: {renewal_quote.quote_number}\n"
                        f"Premium: ${renewal_quote.total_premium:,.2f}"
                    )
                    self._load_renewals()
                else:
                    QMessageBox.warning(self, "Error", "Failed to generate renewal quote.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error generating renewal quote:\n{str(e)}")

    def _send_reminder(self, renewal: Renewal, reminder_type: str):
        """Send renewal reminder."""
        try:
            success = self.renewal_service.send_renewal_reminder(renewal.id, reminder_type)
            if success:
                QMessageBox.information(
                    self,
                    "Reminder Sent",
                    f"{reminder_type.replace('_', '-')} reminder has been sent successfully!"
                )
                self._load_renewals()
            else:
                QMessageBox.warning(self, "Error", "Failed to send reminder.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error sending reminder:\n{str(e)}")

    def _mark_as_bound(self, renewal: Renewal):
        """Mark renewal as bound."""
        # Show dialog to enter bind date
        dialog = BindRenewalDialog(renewal, self)
        if dialog.exec():
            QMessageBox.information(self, "Success", "Renewal marked as bound!")
            self._load_renewals()

    def _mark_as_declined(self, renewal: Renewal):
        """Mark renewal as declined."""
        # Show dialog to enter decline reason
        reason, ok = self._get_text_input(
            "Decline Renewal",
            "Please enter the reason for declining this renewal:",
            multiline=True
        )

        if ok and reason:
            self.renewal_repo.update_status(renewal.id, 'declined', reason)
            renewal.declined_reason = reason
            self.renewal_repo.update(renewal)

            QMessageBox.information(self, "Success", "Renewal marked as declined.")
            self._load_renewals()

    def _process_daily_renewals(self):
        """Process daily renewals job."""
        reply = QMessageBox.question(
            self,
            "Process Daily Renewals",
            "This will:\n"
            "• Send due reminders\n"
            "• Generate renewal quotes for pending renewals\n"
            "• Mark lapsed renewals\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                summary = self.renewal_service.process_daily_renewals()

                QMessageBox.information(
                    self,
                    "Processing Complete",
                    f"Daily renewal processing completed:\n\n"
                    f"Reminders sent: {summary['reminders_sent']}\n"
                    f"Quotes generated: {summary['quotes_generated']}\n"
                    f"Renewals lapsed: {summary['renewals_lapsed']}\n"
                    f"Errors: {len(summary['errors'])}"
                )
                self._load_renewals()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error processing renewals:\n{str(e)}")

    def _get_text_input(self, title: str, prompt: str, multiline: bool = False) -> tuple:
        """Get text input from user."""
        from PyQt6.QtWidgets import QInputDialog

        if multiline:
            dialog = QInputDialog(self)
            dialog.setWindowTitle(title)
            dialog.setLabelText(prompt)
            dialog.setInputMode(QInputDialog.InputMode.TextInput)
            dialog.setOption(QInputDialog.InputDialogOption.UsePlainTextEditForTextInput)
            ok = dialog.exec()
            return dialog.textValue(), ok
        else:
            return QInputDialog.getText(self, title, prompt)


class RenewalDetailsDialog(QDialog):
    """Dialog showing detailed renewal information."""

    def __init__(self, renewal: Renewal, parent=None):
        super().__init__(parent)
        self.renewal = renewal
        self.setWindowTitle("Renewal Details")
        self.setModal(True)
        self.resize(600, 500)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Details text
        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(self._build_details_text())
        layout.addWidget(details)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _build_details_text(self) -> str:
        """Build details text."""
        renewal = self.renewal

        text = f"""
RENEWAL DETAILS
{'='*60}

Renewal ID: {renewal.id}
Original Quote ID: {renewal.original_quote_id}
Renewal Quote ID: {renewal.renewal_quote_id or 'Not Generated'}
Status: {renewal.status.upper()}

TIMELINE
{'='*60}
Policy End Date: {renewal.policy_end_date}
Renewal Due Date: {renewal.renewal_due_date}
Days Until Expiration: {renewal.calculate_days_until_expiration()}

REMINDERS
{'='*60}
90-Day Reminder: {'Sent ' + renewal.reminder_90_days_date if renewal.reminder_90_days_sent else 'Not Sent'}
60-Day Reminder: {'Sent ' + renewal.reminder_60_days_date if renewal.reminder_60_days_sent else 'Not Sent'}
30-Day Reminder: {'Sent ' + renewal.reminder_30_days_date if renewal.reminder_30_days_sent else 'Not Sent'}
Final Reminder: {'Sent ' + renewal.reminder_final_date if renewal.reminder_final_sent else 'Not Sent'}

RENEWAL QUOTE
{'='*60}
"""
        if renewal.renewal_quote_id:
            text += f"Generated: {renewal.renewal_generated_date}\n"
            text += f"Sent: {renewal.renewal_sent_date or 'Not Sent'}\n"
            text += f"Premium: ${renewal.renewal_premium:,.2f}\n"
            if renewal.premium_change_percent:
                text += f"Premium Change: {renewal.premium_change_percent:+.2f}%\n"
        else:
            text += "Renewal quote not yet generated\n"

        if renewal.outcome_date:
            text += f"\nOUTCOME\n{'='*60}\n"
            text += f"Date: {renewal.outcome_date}\n"
            text += f"Notes: {renewal.outcome_notes}\n"

        if renewal.declined_reason:
            text += f"\nDeclined Reason: {renewal.declined_reason}\n"

        text += f"\nMETADATA\n{'='*60}\n"
        text += f"Created: {renewal.created_at}\n"
        text += f"Updated: {renewal.updated_at}\n"

        return text


class BindRenewalDialog(QDialog):
    """Dialog for binding a renewal."""

    def __init__(self, renewal: Renewal, parent=None):
        super().__init__(parent)
        self.renewal = renewal
        self.renewal_service = RenewalService()

        self.setWindowTitle("Bind Renewal")
        self.setModal(True)
        self.setFixedSize(400, 200)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Info
        info = QLabel(f"Mark renewal as bound for Quote #{self.renewal.original_quote_id}")
        layout.addWidget(info)

        # Form
        form = QGridLayout()

        # Policy start date
        form.addWidget(QLabel("Policy Start Date:"), 0, 0)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        form.addWidget(self.start_date, 0, 1)

        # Policy end date (calculated)
        form.addWidget(QLabel("Policy End Date:"), 1, 0)
        self.end_date = QLabel(self.renewal.policy_end_date)
        form.addWidget(self.end_date, 1, 1)

        layout.addLayout(form)

        # Notes
        layout.addWidget(QLabel("Notes (optional):"))
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addWidget(self.notes)

        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bind_btn = QPushButton("Bind Renewal")
        bind_btn.clicked.connect(self._bind_renewal)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(bind_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _bind_renewal(self):
        """Bind the renewal."""
        try:
            # Update renewal status
            self.renewal_service.renewal_repo.update_status(
                self.renewal.id,
                'bound',
                self.notes.toPlainText()
            )

            # If renewal quote exists, mark it as bound
            if self.renewal.renewal_quote_id:
                renewal_quote = self.renewal_service.quote_repo.get_by_id(self.renewal.renewal_quote_id)
                if renewal_quote:
                    # Set policy dates on renewal quote
                    start_date_str = self.start_date.date().toString("yyyy-MM-dd")
                    renewal_quote.is_bound = 1
                    renewal_quote.status = 'bound'
                    renewal_quote.policy_start_date = start_date_str
                    renewal_quote.policy_end_date = self.renewal.policy_end_date
                    self.renewal_service.quote_repo.update(renewal_quote)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error binding renewal:\n{str(e)}")
