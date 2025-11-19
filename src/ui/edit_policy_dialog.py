"""
Edit Policy Information Dialog.
Allows updating policy details after binding (policy number, payment status, etc.).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QDateEdit, QComboBox,
    QTextEdit, QMessageBox, QRadioButton, QButtonGroup, QListWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date
from pathlib import Path

from models.quote import Quote, QuoteRepository
from models.customer import CustomerRepository
from models.policy_document import PolicyDocumentRepository
from services.binding_service import BindingService


class EditPolicyDialog(QDialog):
    """Dialog for editing policy information."""

    def __init__(self, quote_id: int, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.quote_repo = QuoteRepository()
        self.customer_repo = CustomerRepository()
        self.document_repo = PolicyDocumentRepository()
        self.binding_service = BindingService()

        self.quote = None
        self.customer = None
        self.documents = []

        self.setWindowTitle("Edit Policy Information")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._load_data()
        self._init_ui()

    def _load_data(self):
        """Load quote, customer, and document information."""
        self.quote = self.quote_repo.get_by_id(self.quote_id, load_line_items=False)
        if not self.quote:
            QMessageBox.critical(self, "Error", "Quote not found")
            self.reject()
            return

        if not self.quote.is_bound:
            QMessageBox.warning(
                self,
                "Not Bound",
                "This quote is not bound. Please bind it first before editing policy information."
            )
            self.reject()
            return

        if self.quote.customer_id:
            self.customer = self.customer_repo.get_by_id(self.quote.customer_id)

        self.documents = self.document_repo.get_by_quote(self.quote_id)

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Edit Policy Information")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Policy summary
        summary_group = self._create_summary_section()
        layout.addWidget(summary_group)

        # Policy details form
        details_group = self._create_details_form()
        layout.addWidget(details_group)

        # Documents section
        docs_group = self._create_documents_section()
        layout.addWidget(docs_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_summary_section(self) -> QGroupBox:
        """Create policy summary section."""
        group = QGroupBox("Policy Summary")
        layout = QGridLayout()

        row = 0

        # Quote number
        layout.addWidget(QLabel("Quote #:"), row, 0)
        layout.addWidget(QLabel(f"<b>{self.quote.quote_number}</b>"), row, 1)
        row += 1

        # Status
        layout.addWidget(QLabel("Status:"), row, 0)
        status_label = QLabel("<b>BOUND</b>")
        status_label.setStyleSheet("color: #10b981;")
        layout.addWidget(status_label, row, 1)
        row += 1

        # Bound date
        if self.quote.bound_date:
            layout.addWidget(QLabel("Bound Date:"), row, 0)
            layout.addWidget(QLabel(self.quote.bound_date), row, 1)
            row += 1

        # Customer
        customer_name = self.customer.name if self.customer else "N/A"
        layout.addWidget(QLabel("Customer:"), row, 0)
        layout.addWidget(QLabel(customer_name), row, 1)
        row += 1

        # Premium
        layout.addWidget(QLabel("Premium:"), row, 0)
        layout.addWidget(QLabel(f"${self.quote.total_premium:,.2f}"), row, 1)
        row += 1

        # Coverage period
        if self.quote.effective_date and self.quote.expiration_date:
            layout.addWidget(QLabel("Coverage Period:"), row, 0)
            layout.addWidget(
                QLabel(f"{self.quote.effective_date} to {self.quote.expiration_date}"),
                row, 1
            )
            row += 1

        group.setLayout(layout)
        return group

    def _create_details_form(self) -> QGroupBox:
        """Create policy details form."""
        group = QGroupBox("Policy Details")
        layout = QGridLayout()

        row = 0

        # Policy Number
        layout.addWidget(QLabel("Policy Number:"), row, 0)
        self.policy_number = QLineEdit()
        self.policy_number.setText(self.quote.policy_number or "")
        self.policy_number.setPlaceholderText("Enter policy number when received from carrier")
        layout.addWidget(self.policy_number, row, 1)
        row += 1

        # Policy Received Date (auto-set when policy number is added)
        layout.addWidget(QLabel("Policy Received:"), row, 0)
        if self.quote.policy_received_date:
            layout.addWidget(QLabel(self.quote.policy_received_date), row, 1)
        else:
            layout.addWidget(QLabel("<i>Not yet received</i>"), row, 1)
        row += 1

        # Carrier
        layout.addWidget(QLabel("Carrier:"), row, 0)
        self.carrier_name = QLineEdit()
        self.carrier_name.setText(self.quote.carrier_name or "")
        layout.addWidget(self.carrier_name, row, 1)
        row += 1

        # Spacer
        layout.addWidget(QLabel(""), row, 0)
        row += 1

        # Payment Status
        layout.addWidget(QLabel("Payment Status:"), row, 0)
        payment_layout = QHBoxLayout()

        self.payment_status_group = QButtonGroup()

        self.payment_pending = QRadioButton("Pending")
        self.payment_status_group.addButton(self.payment_pending)
        payment_layout.addWidget(self.payment_pending)

        self.payment_paid = QRadioButton("Paid")
        self.payment_status_group.addButton(self.payment_paid)
        payment_layout.addWidget(self.payment_paid)

        self.payment_financed = QRadioButton("Financed")
        self.payment_status_group.addButton(self.payment_financed)
        payment_layout.addWidget(self.payment_financed)

        # Set current payment status
        if self.quote.payment_status == 'paid':
            self.payment_paid.setChecked(True)
        elif self.quote.payment_status == 'financed':
            self.payment_financed.setChecked(True)
        else:
            self.payment_pending.setChecked(True)

        payment_layout.addStretch()
        layout.addLayout(payment_layout, row, 1)
        row += 1

        # Payment Method
        layout.addWidget(QLabel("Payment Method:"), row, 0)
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "",
            "Check",
            "Premium Financing",
            "Wire Transfer",
            "Credit Card",
            "Direct Bill",
            "Other"
        ])
        # Set current value
        if self.quote.payment_method:
            index = self.payment_method.findText(self.quote.payment_method)
            if index >= 0:
                self.payment_method.setCurrentIndex(index)
        layout.addWidget(self.payment_method, row, 1)
        row += 1

        # Spacer
        layout.addWidget(QLabel(""), row, 0)
        row += 1

        # Update notes
        layout.addWidget(QLabel("Update Notes:"), row, 0, Qt.AlignmentFlag.AlignTop)
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Notes about this update (optional)...")
        layout.addWidget(self.notes, row, 1)
        row += 1

        group.setLayout(layout)
        return group

    def _create_documents_section(self) -> QGroupBox:
        """Create documents section."""
        group = QGroupBox("Attached Documents")
        layout = QVBoxLayout()

        if self.documents:
            # Document list
            self.doc_list = QListWidget()
            for doc in self.documents:
                doc_info = f"📄 {doc.document_name} ({doc.document_type})"
                if doc.uploaded_date:
                    doc_info += f" - {doc.uploaded_date[:10]}"
                self.doc_list.addItem(doc_info)
            layout.addWidget(self.doc_list)

            # Document count
            count_label = QLabel(f"Total: {len(self.documents)} document(s)")
            count_label.setStyleSheet("color: #6b7280; font-size: 11px;")
            layout.addWidget(count_label)
        else:
            no_docs = QLabel("<i>No documents attached yet</i>")
            no_docs.setStyleSheet("color: #6b7280;")
            layout.addWidget(no_docs)

        # Upload button (placeholder)
        upload_btn = QPushButton("+ Upload Document")
        upload_btn.clicked.connect(self._upload_document)
        layout.addWidget(upload_btn)

        group.setLayout(layout)
        return group

    def _upload_document(self):
        """Handle document upload (placeholder)."""
        QMessageBox.information(
            self,
            "Upload Document",
            "Document upload functionality coming soon!\n\n"
            "For now, you can manually add documents to the data/policy_documents folder."
        )

    def _save_changes(self):
        """Save policy information changes."""
        # Prepare update info
        policy_info = {
            'policy_number': self.policy_number.text().strip() or None,
            'carrier_name': self.carrier_name.text().strip(),
            'payment_method': self.payment_method.currentText(),
            'notes': self.notes.toPlainText().strip()
        }

        # Get payment status
        if self.payment_paid.isChecked():
            policy_info['payment_status'] = 'paid'
        elif self.payment_financed.isChecked():
            policy_info['payment_status'] = 'financed'
        else:
            policy_info['payment_status'] = 'pending'

        # Update policy
        try:
            success, message = self.binding_service.update_policy_info(self.quote_id, policy_info)

            if success:
                QMessageBox.information(self, "Success", message)
                self.accept()
            else:
                QMessageBox.warning(self, "Update Failed", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while updating policy information:\n\n{str(e)}"
            )
