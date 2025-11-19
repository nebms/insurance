"""
Edit Policy Information Dialog.
Allows updating policy details after binding (policy number, payment status, etc.).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QDateEdit, QComboBox,
    QTextEdit, QMessageBox, QRadioButton, QButtonGroup, QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date
from pathlib import Path
import subprocess
import sys
import os

from models.quote import Quote, QuoteRepository
from models.customer import CustomerRepository
from models.policy_document import PolicyDocumentRepository
from services.binding_service import BindingService
from services.document_service import DocumentService
from services.cancellation_service import CancellationService
from ui.document_upload_dialog import DocumentUploadDialog
from ui.cancel_policy_dialog import CancelPolicyDialog


class EditPolicyDialog(QDialog):
    """Dialog for editing policy information."""

    def __init__(self, quote_id: int, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.quote_repo = QuoteRepository()
        self.customer_repo = CustomerRepository()
        self.document_repo = PolicyDocumentRepository()
        self.binding_service = BindingService()
        self.document_service = DocumentService()
        self.cancellation_service = CancellationService()

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

        # Cancellation section (if cancelled or can be cancelled)
        if self.quote.is_cancelled or (self.quote.is_bound and not self.quote.is_cancelled):
            cancel_group = self._create_cancellation_section()
            layout.addWidget(cancel_group)

        # Buttons
        button_layout = QHBoxLayout()

        # Cancel Policy / Reinstate button (left side)
        if self.quote.is_bound and not self.quote.is_cancelled:
            cancel_policy_btn = QPushButton("Cancel Policy")
            cancel_policy_btn.setStyleSheet("background-color: #dc2626; color: white; padding: 8px 16px;")
            cancel_policy_btn.clicked.connect(self._cancel_policy)
            button_layout.addWidget(cancel_policy_btn)
        elif self.quote.is_cancelled:
            reinstate_btn = QPushButton("Reinstate Policy")
            reinstate_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px 16px;")
            reinstate_btn.clicked.connect(self._reinstate_policy)
            button_layout.addWidget(reinstate_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Close")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        if not self.quote.is_cancelled:
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
                item = QListWidgetItem(doc_info)
                item.setData(Qt.ItemDataRole.UserRole, doc.id)  # Store document ID
                self.doc_list.addItem(item)
            layout.addWidget(self.doc_list)

            # Document count
            count_label = QLabel(f"Total: {len(self.documents)} document(s)")
            count_label.setStyleSheet("color: #6b7280; font-size: 11px;")
            layout.addWidget(count_label)

            # Document action buttons
            doc_actions_layout = QHBoxLayout()

            view_btn = QPushButton("View Document")
            view_btn.clicked.connect(self._view_document)
            doc_actions_layout.addWidget(view_btn)

            delete_btn = QPushButton("Delete Document")
            delete_btn.setStyleSheet("color: #dc2626;")
            delete_btn.clicked.connect(self._delete_document)
            doc_actions_layout.addWidget(delete_btn)

            layout.addLayout(doc_actions_layout)
        else:
            no_docs = QLabel("<i>No documents attached yet</i>")
            no_docs.setStyleSheet("color: #6b7280;")
            layout.addWidget(no_docs)

        # Upload button
        upload_btn = QPushButton("+ Upload Document")
        upload_btn.clicked.connect(self._upload_document)
        layout.addWidget(upload_btn)

        group.setLayout(layout)
        return group

    def _upload_document(self):
        """Handle document upload."""
        dialog = DocumentUploadDialog(self.quote_id, self)
        if dialog.exec():
            # Refresh documents list
            self.documents = self.document_repo.get_by_quote(self.quote_id)
            # Recreate the documents section to show new document
            self._refresh_documents_section()

    def _view_document(self):
        """Open selected document in system viewer."""
        if not self.doc_list or not self.doc_list.currentItem():
            QMessageBox.warning(self, "No Selection", "Please select a document to view")
            return

        # Get selected document ID
        doc_id = self.doc_list.currentItem().data(Qt.ItemDataRole.UserRole)
        document = self.document_repo.get_by_id(doc_id)

        if not document:
            QMessageBox.warning(self, "Error", "Document not found")
            return

        # Get file path
        file_path = Path(document.file_path)
        if not file_path.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"Document file not found:\n{document.file_path}\n\n"
                "The file may have been moved or deleted."
            )
            return

        # Open file with default system application
        try:
            if sys.platform == 'win32':
                os.startfile(str(file_path))
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', str(file_path)])
            else:  # linux
                subprocess.run(['xdg-open', str(file_path)])
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error Opening File",
                f"Could not open document:\n{str(e)}\n\n"
                f"File location: {file_path}"
            )

    def _delete_document(self):
        """Delete selected document."""
        if not self.doc_list or not self.doc_list.currentItem():
            QMessageBox.warning(self, "No Selection", "Please select a document to delete")
            return

        # Get selected document ID
        doc_id = self.doc_list.currentItem().data(Qt.ItemDataRole.UserRole)
        document = self.document_repo.get_by_id(doc_id)

        if not document:
            QMessageBox.warning(self, "Error", "Document not found")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete this document?\n\n"
            f"Name: {document.document_name}\n"
            f"Type: {document.document_type}\n\n"
            f"This will remove the database record and optionally delete the file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Delete from database
        success = self.document_repo.delete(doc_id)

        if success:
            # Ask if they want to delete the physical file too
            file_path = Path(document.file_path)
            if file_path.exists():
                delete_file = QMessageBox.question(
                    self,
                    "Delete File?",
                    f"Document record deleted.\n\n"
                    f"Also delete the physical file?\n{file_path}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if delete_file == QMessageBox.StandardButton.Yes:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        QMessageBox.warning(
                            self,
                            "File Deletion Failed",
                            f"Could not delete file:\n{str(e)}"
                        )

            # Refresh documents list
            self.documents = self.document_repo.get_by_quote(self.quote_id)
            self._refresh_documents_section()

            QMessageBox.information(self, "Success", "Document deleted successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to delete document")

    def _refresh_documents_section(self):
        """Refresh the documents section after upload/delete."""
        # Find the documents group box in the layout
        layout = self.layout()

        # Find and remove old documents section (it's the 3rd widget after title and summary)
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox) and widget.title() == "Attached Documents":
                layout.removeWidget(widget)
                widget.deleteLater()
                break

        # Create and insert new documents section
        docs_group = self._create_documents_section()
        layout.insertWidget(2, docs_group)  # Insert after summary section

    def _create_cancellation_section(self) -> QGroupBox:
        """Create cancellation information section."""
        group = QGroupBox("Cancellation Information")

        if self.quote.is_cancelled:
            # Show cancellation details
            group.setStyleSheet("QGroupBox { border: 2px solid #dc2626; border-radius: 4px; padding: 10px; }")
            layout = QGridLayout()

            row = 0
            layout.addWidget(QLabel("<b style='color: #dc2626;'>⚠️ This policy is CANCELLED</b>"), row, 0, 1, 2)
            row += 1

            if self.quote.cancellation_date:
                layout.addWidget(QLabel("<b>Cancelled On:</b>"), row, 0)
                layout.addWidget(QLabel(self.quote.cancellation_date), row, 1)
                row += 1

            if self.quote.cancellation_effective_date:
                layout.addWidget(QLabel("<b>Effective Date:</b>"), row, 0)
                layout.addWidget(QLabel(self.quote.cancellation_effective_date), row, 1)
                row += 1

            if self.quote.cancellation_reason:
                layout.addWidget(QLabel("<b>Reason:</b>"), row, 0)
                layout.addWidget(QLabel(self.quote.cancellation_reason), row, 1)
                row += 1

            if self.quote.cancellation_type:
                layout.addWidget(QLabel("<b>Cancellation Type:</b>"), row, 0)
                layout.addWidget(QLabel(self.quote.cancellation_type), row, 1)
                row += 1

            layout.addWidget(QLabel("<b>Return Premium:</b>"), row, 0)
            return_amount = self.quote.return_premium or 0.0
            return_label = QLabel(f"${return_amount:,.2f}")
            return_label.setStyleSheet("font-weight: bold; color: #10b981;")
            layout.addWidget(return_label, row, 1)
            row += 1

            if self.quote.cancellation_notes:
                layout.addWidget(QLabel("<b>Notes:</b>"), row, 0, Qt.AlignmentFlag.AlignTop)
                notes_label = QLabel(self.quote.cancellation_notes)
                notes_label.setWordWrap(True)
                layout.addWidget(notes_label, row, 1)
                row += 1

            group.setLayout(layout)
        else:
            # Policy can be cancelled
            layout = QVBoxLayout()
            info_label = QLabel(
                "This policy can be cancelled. Click 'Cancel Policy' button below to initiate cancellation."
            )
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #6b7280; font-style: italic;")
            layout.addWidget(info_label)
            group.setLayout(layout)

        return group

    def _cancel_policy(self):
        """Open cancel policy dialog."""
        dialog = CancelPolicyDialog(self.quote_id, self)
        if dialog.exec():
            # Reload quote data and UI
            self._load_data()
            self.close()
            # Reopen to show updated state
            QMessageBox.information(
                self,
                "Policy Cancelled",
                "The policy has been cancelled successfully."
            )
            self.accept()

    def _reinstate_policy(self):
        """Reinstate a cancelled policy."""
        reply = QMessageBox.question(
            self,
            "Confirm Reinstatement",
            f"Are you sure you want to reinstate this policy?\n\n"
            f"Policy: {self.quote.quote_number}\n"
            f"This will restore the policy to active status.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        notes = f"Policy reinstated on {datetime.now().strftime('%Y-%m-%d')}"
        success, message = self.cancellation_service.reinstate_policy(
            self.quote_id,
            notes
        )

        if success:
            QMessageBox.information(self, "Success", message)
            self._load_data()
            self.close()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Reinstatement failed:\n{message}")

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
