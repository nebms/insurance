"""
Bind Quote Dialog - Convert quote to active policy.
Simple workflow matching real agency/broker process.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QDateEdit, QComboBox,
    QTextEdit, QMessageBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date, timedelta

from models.quote import Quote, QuoteRepository
from models.customer import CustomerRepository
from services.binding_service import BindingService


class BindQuoteDialog(QDialog):
    """Dialog for binding a quote to create an active policy."""

    def __init__(self, quote_id: int, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.quote_repo = QuoteRepository()
        self.customer_repo = CustomerRepository()
        self.binding_service = BindingService()

        self.quote = None
        self.customer = None

        self.setWindowTitle("Bind Quote to Policy")
        self.setModal(True)
        self.setMinimumWidth(550)

        self._load_quote_data()
        self._init_ui()

    def _load_quote_data(self):
        """Load quote and customer information."""
        self.quote = self.quote_repo.get_by_id(self.quote_id, load_line_items=True)
        if not self.quote:
            QMessageBox.critical(self, "Error", "Quote not found")
            self.reject()
            return

        if self.quote.customer_id:
            self.customer = self.customer_repo.get_by_id(self.quote.customer_id)

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Bind Quote to Policy")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Quote information summary
        info_group = self._create_quote_info_section()
        layout.addWidget(info_group)

        # Binding information form
        binding_group = self._create_binding_form()
        layout.addWidget(binding_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        bind_btn = QPushButton("Bind Policy")
        bind_btn.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px 16px;")
        bind_btn.clicked.connect(self._bind_quote)
        button_layout.addWidget(bind_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_quote_info_section(self) -> QGroupBox:
        """Create quote information summary section."""
        group = QGroupBox("Quote Information")
        layout = QGridLayout()

        row = 0

        # Quote number
        layout.addWidget(QLabel("Quote #:"), row, 0)
        layout.addWidget(QLabel(f"<b>{self.quote.quote_number}</b>"), row, 1)
        row += 1

        # Customer
        customer_name = self.customer.name if self.customer else "N/A"
        layout.addWidget(QLabel("Customer:"), row, 0)
        layout.addWidget(QLabel(customer_name), row, 1)
        row += 1

        # Premium
        layout.addWidget(QLabel("Premium:"), row, 0)
        layout.addWidget(QLabel(f"<b>${self.quote.total_premium:,.2f}</b>"), row, 1)
        row += 1

        # Term
        layout.addWidget(QLabel("Term:"), row, 0)
        layout.addWidget(QLabel(f"{self.quote.term_months} months"), row, 1)
        row += 1

        group.setLayout(layout)
        return group

    def _create_binding_form(self) -> QGroupBox:
        """Create binding information form."""
        group = QGroupBox("Binding Information")
        layout = QGridLayout()

        row = 0

        # Effective Date (REQUIRED)
        layout.addWidget(QLabel("Effective Date: *"), row, 0)
        self.effective_date = QDateEdit()
        self.effective_date.setDate(QDate.currentDate())
        self.effective_date.setCalendarPopup(True)
        self.effective_date.setDisplayFormat("yyyy-MM-dd")
        self.effective_date.dateChanged.connect(self._calculate_expiration)
        layout.addWidget(self.effective_date, row, 1)
        row += 1

        # Term (display only, from quote)
        layout.addWidget(QLabel("Term:"), row, 0)
        self.term_display = QLabel(f"{self.quote.term_months} months")
        layout.addWidget(self.term_display, row, 1)
        row += 1

        # Expiration Date (calculated)
        layout.addWidget(QLabel("Expiration Date:"), row, 0)
        self.expiration_display = QLabel()
        self.expiration_display.setStyleSheet("color: #6366f1; font-weight: bold;")
        self._calculate_expiration()  # Calculate initial value
        layout.addWidget(self.expiration_display, row, 1)
        row += 1

        # Spacer
        layout.addWidget(QLabel(""), row, 0)
        row += 1

        # Carrier Name (REQUIRED)
        layout.addWidget(QLabel("Carrier: *"), row, 0)
        self.carrier_name = QLineEdit()
        self.carrier_name.setPlaceholderText("e.g., ABC Insurance Company")
        layout.addWidget(self.carrier_name, row, 1)
        row += 1

        # Policy Number (OPTIONAL)
        layout.addWidget(QLabel("Policy Number:"), row, 0)
        self.policy_number = QLineEdit()
        self.policy_number.setPlaceholderText("(Optional - can add later)")
        layout.addWidget(self.policy_number, row, 1)
        row += 1

        # Spacer
        layout.addWidget(QLabel(""), row, 0)
        row += 1

        # Payment Status
        layout.addWidget(QLabel("Payment Status:"), row, 0)
        payment_layout = QHBoxLayout()

        self.payment_status_group = QButtonGroup()

        self.payment_pending = QRadioButton("Pending")
        self.payment_pending.setChecked(True)
        self.payment_status_group.addButton(self.payment_pending)
        payment_layout.addWidget(self.payment_pending)

        self.payment_paid = QRadioButton("Paid")
        self.payment_status_group.addButton(self.payment_paid)
        payment_layout.addWidget(self.payment_paid)

        self.payment_financed = QRadioButton("Financed")
        self.payment_status_group.addButton(self.payment_financed)
        payment_layout.addWidget(self.payment_financed)

        payment_layout.addStretch()

        layout.addLayout(payment_layout, row, 1)
        row += 1

        # Payment Method
        layout.addWidget(QLabel("Payment Method:"), row, 0)
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Select...",
            "Check",
            "Premium Financing",
            "Wire Transfer",
            "Credit Card",
            "Direct Bill",
            "Other"
        ])
        layout.addWidget(self.payment_method, row, 1)
        row += 1

        # Spacer
        layout.addWidget(QLabel(""), row, 0)
        row += 1

        # Notes (optional)
        layout.addWidget(QLabel("Notes:"), row, 0, Qt.AlignmentFlag.AlignTop)
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Optional binding notes...")
        layout.addWidget(self.notes, row, 1)
        row += 1

        # Required fields note
        layout.addWidget(QLabel("<i>* Required fields</i>"), row, 0, 1, 2)

        group.setLayout(layout)
        return group

    def _calculate_expiration(self):
        """Calculate and display expiration date."""
        effective_date = self.effective_date.date().toPyDate()
        expiration_date = effective_date + timedelta(days=self.quote.term_months * 30)
        self.expiration_display.setText(expiration_date.strftime("%Y-%m-%d"))

    def _bind_quote(self):
        """Bind the quote to create a policy."""
        # Validate required fields
        if not self.carrier_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Carrier name is required")
            self.carrier_name.setFocus()
            return

        # Get payment status
        if self.payment_paid.isChecked():
            payment_status = 'paid'
        elif self.payment_financed.isChecked():
            payment_status = 'financed'
        else:
            payment_status = 'pending'

        # Get payment method
        payment_method = self.payment_method.currentText()
        if payment_method == "Select...":
            payment_method = ""

        # Prepare binding information
        binding_info = {
            'effective_date': self.effective_date.date().toString("yyyy-MM-dd"),
            'carrier_name': self.carrier_name.text().strip(),
            'policy_number': self.policy_number.text().strip() or None,
            'payment_status': payment_status,
            'payment_method': payment_method,
            'notes': self.notes.toPlainText().strip(),
            'bound_by_user_id': None  # TODO: Get from session/auth
        }

        # Confirm binding
        confirm_msg = f"""
        Bind this quote to create an active policy?

        Quote #: {self.quote.quote_number}
        Customer: {self.customer.name if self.customer else 'N/A'}
        Premium: ${self.quote.total_premium:,.2f}

        Effective: {binding_info['effective_date']}
        Expiration: {self.expiration_display.text()}
        Carrier: {binding_info['carrier_name']}
        """

        if binding_info['policy_number']:
            confirm_msg += f"\nPolicy #: {binding_info['policy_number']}"

        reply = QMessageBox.question(
            self,
            "Confirm Binding",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Bind the quote
        try:
            success, message = self.binding_service.bind_quote(self.quote_id, binding_info)

            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"{message}\n\n"
                    f"Quote #{self.quote.quote_number} is now an active policy.\n"
                    f"Renewal tracking has been created automatically."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Binding Failed", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while binding the quote:\n\n{str(e)}"
            )
