"""
Cancel Policy Dialog.
Allows cancelling bound policies with reason, type, and effective date.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QDateEdit, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date

from models.quote import QuoteRepository
from models.customer import CustomerRepository
from services.cancellation_service import CancellationService


class CancelPolicyDialog(QDialog):
    """Dialog for cancelling a bound policy."""

    def __init__(self, quote_id: int, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.quote_repo = QuoteRepository()
        self.customer_repo = CustomerRepository()
        self.cancellation_service = CancellationService()

        # Load quote
        self.quote = self.quote_repo.get_by_id(quote_id)
        if not self.quote:
            QMessageBox.critical(self, "Error", "Quote not found")
            self.reject()
            return

        # Validate quote is bound
        if not self.quote.is_bound:
            QMessageBox.warning(self, "Cannot Cancel", "Only bound policies can be cancelled")
            self.reject()
            return

        # Validate quote is not already cancelled
        if self.quote.is_cancelled:
            QMessageBox.warning(self, "Already Cancelled", "This policy is already cancelled")
            self.reject()
            return

        self.setWindowTitle(f"Cancel Policy - {self.quote.quote_number}")
        self.setModal(True)
        self.resize(600, 500)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Cancel Policy")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Policy summary
        layout.addWidget(self._create_policy_summary())

        # Cancellation details
        layout.addWidget(self._create_cancellation_details())

        # Warning
        warning = QLabel(
            "⚠️ Warning: Cancelling a policy is a permanent action. "
            "This will mark the policy as cancelled and calculate return premium."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #dc2626; font-weight: bold; padding: 10px; background-color: #fee2e2; border-radius: 4px;")
        layout.addWidget(warning)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel Operation")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirm Cancellation")
        confirm_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold;")
        confirm_btn.clicked.connect(self._confirm_cancellation)
        button_layout.addWidget(confirm_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_policy_summary(self) -> QGroupBox:
        """Create policy summary section."""
        group = QGroupBox("Policy Information")
        layout = QGridLayout()

        row = 0

        # Quote/Policy number
        layout.addWidget(QLabel("<b>Quote Number:</b>"), row, 0)
        layout.addWidget(QLabel(self.quote.quote_number), row, 1)
        row += 1

        if self.quote.policy_number:
            layout.addWidget(QLabel("<b>Policy Number:</b>"), row, 0)
            layout.addWidget(QLabel(self.quote.policy_number), row, 1)
            row += 1

        # Customer
        if self.quote.customer_id:
            customer = self.customer_repo.get_by_id(self.quote.customer_id)
            if customer:
                layout.addWidget(QLabel("<b>Customer:</b>"), row, 0)
                layout.addWidget(QLabel(customer.name), row, 1)
                row += 1

        # Premium
        layout.addWidget(QLabel("<b>Total Premium:</b>"), row, 0)
        layout.addWidget(QLabel(f"${self.quote.total_premium:,.2f}"), row, 1)
        row += 1

        # Coverage period
        if self.quote.effective_date and self.quote.expiration_date:
            layout.addWidget(QLabel("<b>Coverage Period:</b>"), row, 0)
            layout.addWidget(
                QLabel(f"{self.quote.effective_date} to {self.quote.expiration_date}"),
                row, 1
            )
            row += 1

        # Carrier
        if self.quote.carrier_name:
            layout.addWidget(QLabel("<b>Carrier:</b>"), row, 0)
            layout.addWidget(QLabel(self.quote.carrier_name), row, 1)
            row += 1

        group.setLayout(layout)
        return group

    def _create_cancellation_details(self) -> QGroupBox:
        """Create cancellation details section."""
        group = QGroupBox("Cancellation Details")
        layout = QGridLayout()

        row = 0

        # Cancellation effective date
        layout.addWidget(QLabel("Effective Date: *"), row, 0)
        self.effective_date = QDateEdit()
        self.effective_date.setCalendarPopup(True)
        self.effective_date.setDate(QDate.currentDate())
        self.effective_date.setDisplayFormat("yyyy-MM-dd")
        self.effective_date.dateChanged.connect(self._update_premium_calculation)
        layout.addWidget(self.effective_date, row, 1)
        row += 1

        # Cancellation reason
        layout.addWidget(QLabel("Reason: *"), row, 0)
        self.reason = QComboBox()
        self.reason.addItems(self.cancellation_service.CANCELLATION_REASONS)
        layout.addWidget(self.reason, row, 1)
        row += 1

        # Cancellation type
        layout.addWidget(QLabel("Cancellation Type: *"), row, 0)
        self.cancel_type = QComboBox()
        self.cancel_type.addItem("Flat (Full Refund)", "Flat")
        self.cancel_type.addItem("Pro-rata (Proportional Refund)", "Pro-rata")
        self.cancel_type.addItem("Short-rate (90% of Pro-rata)", "Short-rate")
        self.cancel_type.currentIndexChanged.connect(self._update_premium_calculation)
        layout.addWidget(self.cancel_type, row, 1)
        row += 1

        # Return premium display
        layout.addWidget(QLabel("Return Premium:"), row, 0)
        self.return_premium_label = QLabel("$0.00")
        self.return_premium_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981;")
        layout.addWidget(self.return_premium_label, row, 1)
        row += 1

        # Notes
        layout.addWidget(QLabel("Notes:"), row, 0, Qt.AlignmentFlag.AlignTop)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Enter any additional notes about this cancellation...")
        self.notes.setMaximumHeight(80)
        layout.addWidget(self.notes, row, 1)
        row += 1

        group.setLayout(layout)

        # Initial calculation
        self._update_premium_calculation()

        return group

    def _update_premium_calculation(self):
        """Update return premium calculation based on current selections."""
        if not self.quote:
            return

        effective_date = self.effective_date.date().toString("yyyy-MM-dd")
        cancel_type = self.cancel_type.currentData()

        if not cancel_type:
            cancel_type = "Flat"

        return_premium = self.cancellation_service._calculate_return_premium(
            self.quote,
            effective_date,
            cancel_type
        )

        self.return_premium_label.setText(f"${return_premium:,.2f}")

    def _confirm_cancellation(self):
        """Confirm and process cancellation."""
        # Get values
        effective_date = self.effective_date.date().toString("yyyy-MM-dd")
        reason = self.reason.currentText()
        cancel_type = self.cancel_type.currentData()
        notes = self.notes.toPlainText().strip()

        # Validate
        if not reason:
            QMessageBox.warning(self, "Missing Information", "Please select a cancellation reason")
            return

        # Confirm with user
        return_premium = self.cancellation_service._calculate_return_premium(
            self.quote,
            effective_date,
            cancel_type
        )

        confirm_msg = (
            f"Are you sure you want to cancel this policy?\n\n"
            f"Policy: {self.quote.quote_number}\n"
            f"Effective Date: {effective_date}\n"
            f"Reason: {reason}\n"
            f"Type: {cancel_type}\n"
            f"Return Premium: ${return_premium:,.2f}\n\n"
            f"This action cannot be undone."
        )

        reply = QMessageBox.question(
            self,
            "Confirm Cancellation",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Process cancellation
        cancellation_info = {
            'effective_date': effective_date,
            'reason': reason,
            'cancellation_type': cancel_type,
            'notes': notes
        }

        success, message = self.cancellation_service.cancel_policy(
            self.quote_id,
            cancellation_info
        )

        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Cancellation failed:\n{message}")
