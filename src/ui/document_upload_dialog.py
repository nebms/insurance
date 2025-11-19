"""
Document Upload Dialog.
Upload policy documents (binders, policies, certificates, etc.).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path

from services.document_service import DocumentService


class DocumentUploadDialog(QDialog):
    """Dialog for uploading policy documents."""

    def __init__(self, quote_id: int, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.document_service = DocumentService()

        self.selected_file_path = None

        self.setWindowTitle("Upload Policy Document")
        self.setModal(True)
        self.setMinimumWidth(500)

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Upload Policy Document")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # File selection section
        file_group = self._create_file_selection()
        layout.addWidget(file_group)

        # Document details section
        details_group = self._create_details_section()
        layout.addWidget(details_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        upload_btn = QPushButton("Upload")
        upload_btn.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px 16px;")
        upload_btn.clicked.connect(self._upload_document)
        button_layout.addWidget(upload_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_file_selection(self) -> QGroupBox:
        """Create file selection section."""
        group = QGroupBox("Select File")
        layout = QVBoxLayout()

        # File selection button and display
        file_layout = QHBoxLayout()

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        self.file_display = QLineEdit()
        self.file_display.setReadOnly(True)
        self.file_display.setPlaceholderText("No file selected")
        file_layout.addWidget(self.file_display)

        layout.addLayout(file_layout)

        # File info display
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #6b7280; font-size: 11px; padding: 5px;")
        layout.addWidget(self.file_info_label)

        # Allowed types info
        allowed_types = QLabel(
            "<i>Allowed types: PDF, DOC/DOCX, JPG/JPEG, PNG, TIF/TIFF (Max: 20MB)</i>"
        )
        allowed_types.setStyleSheet("color: #6b7280; font-size: 10px;")
        layout.addWidget(allowed_types)

        group.setLayout(layout)
        return group

    def _create_details_section(self) -> QGroupBox:
        """Create document details section."""
        group = QGroupBox("Document Details")
        layout = QGridLayout()

        row = 0

        # Document Type (REQUIRED)
        layout.addWidget(QLabel("Document Type: *"), row, 0)
        self.document_type = QComboBox()
        self.document_type.addItems([
            "Binder",
            "Policy Declarations",
            "Certificate of Insurance",
            "Endorsement",
            "Renewal Notice",
            "Cancellation Notice",
            "Other"
        ])
        layout.addWidget(self.document_type, row, 1)
        row += 1

        # Received From (REQUIRED)
        layout.addWidget(QLabel("Received From: *"), row, 0)
        self.received_from = QComboBox()
        self.received_from.addItems([
            "Insurance Carrier",
            "Customer",
            "Agent",
            "Broker",
            "Other"
        ])
        layout.addWidget(self.received_from, row, 1)
        row += 1

        # Notes (optional)
        layout.addWidget(QLabel("Notes:"), row, 0, Qt.AlignmentFlag.AlignTop)
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Optional notes about this document...")
        layout.addWidget(self.notes, row, 1)
        row += 1

        # Required fields note
        layout.addWidget(QLabel("<i>* Required fields</i>"), row, 0, 1, 2)

        group.setLayout(layout)
        return group

    def _browse_file(self):
        """Open file browser to select document."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "All Supported Files (*.pdf *.doc *.docx *.jpg *.jpeg *.png *.tif *.tiff);;"
            "PDF Files (*.pdf);;"
            "Word Documents (*.doc *.docx);;"
            "Images (*.jpg *.jpeg *.png *.tif *.tiff);;"
            "All Files (*.*)"
        )

        if file_path:
            self.selected_file_path = file_path
            self.file_display.setText(file_path)

            # Validate and show file info
            valid, error_msg = self.document_service.validate_file(file_path)

            if valid:
                file_info = self.document_service.get_file_info(file_path)
                info_text = f"✓ {file_info['name']} - {file_info['size_display']}"
                self.file_info_label.setText(info_text)
                self.file_info_label.setStyleSheet("color: #10b981; font-size: 11px; padding: 5px;")
            else:
                self.file_info_label.setText(f"⚠ {error_msg}")
                self.file_info_label.setStyleSheet("color: #ef4444; font-size: 11px; padding: 5px;")

    def _upload_document(self):
        """Upload the selected document."""
        # Validate file selection
        if not self.selected_file_path:
            QMessageBox.warning(self, "No File Selected", "Please select a file to upload")
            return

        # Validate file
        valid, error_msg = self.document_service.validate_file(self.selected_file_path)
        if not valid:
            QMessageBox.warning(self, "Invalid File", error_msg)
            return

        # Get document type
        document_type = self.document_type.currentText().lower().replace(" ", "_")

        # Get received from
        received_from = self.received_from.currentText()

        # Get notes
        notes = self.notes.toPlainText().strip()

        # Get file info for confirmation
        file_info = self.document_service.get_file_info(self.selected_file_path)

        # Confirm upload
        confirm_msg = f"""
        Upload this document?

        File: {file_info['name']}
        Size: {file_info['size_display']}
        Type: {self.document_type.currentText()}
        From: {received_from}
        """

        reply = QMessageBox.question(
            self,
            "Confirm Upload",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Upload document
        try:
            success, message, document = self.document_service.upload_document(
                source_path=self.selected_file_path,
                quote_id=self.quote_id,
                document_type=document_type,
                received_from=received_from,
                notes=notes,
                uploaded_by_user_id=None  # TODO: Get from session
            )

            if success:
                QMessageBox.information(
                    self,
                    "Upload Successful",
                    f"{message}\n\nDocument has been attached to this policy."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Upload Failed", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Upload Error",
                f"An error occurred while uploading the document:\n\n{str(e)}"
            )
