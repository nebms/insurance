"""
Customer creation/edit dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.customer import Customer


class CustomerDialog(QDialog):
    """Dialog for creating or editing customers."""

    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("New Customer" if customer is None else "Edit Customer")
        self.setModal(True)
        self.resize(500, 400)

        self._init_ui()

        # If editing, populate fields
        if self.customer:
            self._populate_fields()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Customer Information")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Form fields
        form_layout = QGridLayout()

        # Name
        form_layout.addWidget(QLabel("Name *:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name")
        form_layout.addWidget(self.name_input, 0, 1)

        # Email
        form_layout.addWidget(QLabel("Email:"), 1, 0)
        email_layout = QHBoxLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        self.email_input.textChanged.connect(self._validate_email)
        email_layout.addWidget(self.email_input)
        self.email_status = QLabel()
        self.email_status.setStyleSheet("color: #666; font-size: 10px;")
        email_layout.addWidget(self.email_status)
        form_layout.addLayout(email_layout, 1, 1)

        # Phone
        form_layout.addWidget(QLabel("Phone:"), 2, 0)
        phone_layout = QHBoxLayout()
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(555) 123-4567")
        self.phone_input.textChanged.connect(self._validate_phone)
        phone_layout.addWidget(self.phone_input)
        self.phone_status = QLabel()
        self.phone_status.setStyleSheet("color: #666; font-size: 10px;")
        phone_layout.addWidget(self.phone_status)
        form_layout.addLayout(phone_layout, 2, 1)

        # Address
        form_layout.addWidget(QLabel("Address:"), 3, 0)
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Street address, city, state, zip")
        self.address_input.setMaximumHeight(80)
        form_layout.addWidget(self.address_input, 3, 1)

        # Notes
        form_layout.addWidget(QLabel("Notes:"), 4, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes about this customer")
        self.notes_input.setMaximumHeight(80)
        form_layout.addWidget(self.notes_input, 4, 1)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Customer")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _populate_fields(self):
        """Populate form with customer data."""
        if self.customer:
            self.name_input.setText(self.customer.name)
            self.email_input.setText(self.customer.email)
            self.phone_input.setText(self.customer.phone)
            self.address_input.setPlainText(self.customer.address)
            self.notes_input.setPlainText(self.customer.notes)

    def _validate_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            bool: True if valid or empty, False otherwise
        """
        if not email:
            return True  # Email is optional

        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    def _validate_phone(self, phone: str) -> bool:
        """
        Validate phone format.

        Args:
            phone: Phone number to validate

        Returns:
            bool: True if valid or empty, False otherwise
        """
        if not phone:
            return True  # Phone is optional

        # Remove common separators for validation
        cleaned_phone = re.sub(r'[\s\-\(\)\.]', '', phone)

        # Must be 10-15 digits (supports international)
        # Must start with digit (not special characters)
        if not cleaned_phone.isdigit():
            return False

        if len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
            return False

        return True

    def _save(self):
        """Validate and save customer."""
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()
        notes = self.notes_input.toPlainText().strip()

        # Validate name (required)
        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Customer name is required."
            )
            self.name_input.setFocus()
            return

        # Validate name length
        if len(name) > 200:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Customer name must be 200 characters or less.\n\n"
                f"Current length: {len(name)} characters"
            )
            self.name_input.setFocus()
            return

        # Validate email format
        if email and not self._validate_email(email):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Invalid email format.\n\n"
                "Please enter a valid email address (e.g., john@example.com)\n"
                "or leave blank if not available."
            )
            self.email_input.setFocus()
            return

        # Validate email length
        if len(email) > 100:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Email must be 100 characters or less.\n\n"
                f"Current length: {len(email)} characters"
            )
            self.email_input.setFocus()
            return

        # Validate phone format
        if phone and not self._validate_phone(phone):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Invalid phone number format.\n\n"
                "Please enter a valid phone number:\n"
                "• 10-15 digits\n"
                "• Can include: spaces, hyphens, parentheses, periods\n"
                "• Examples: (555) 123-4567, 555-123-4567, 5551234567\n\n"
                "Or leave blank if not available."
            )
            self.phone_input.setFocus()
            return

        # Validate phone length
        if len(phone) > 30:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Phone number must be 30 characters or less.\n\n"
                f"Current length: {len(phone)} characters"
            )
            self.phone_input.setFocus()
            return

        # Validate address length
        if len(address) > 500:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Address must be 500 characters or less.\n\n"
                f"Current length: {len(address)} characters"
            )
            self.address_input.setFocus()
            return

        # Validate notes length
        if len(notes) > 1000:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Notes must be 1000 characters or less.\n\n"
                f"Current length: {len(notes)} characters"
            )
            self.notes_input.setFocus()
            return

        # Create customer object
        if self.customer:
            # Editing existing
            self.customer.name = name
            self.customer.email = email
            self.customer.phone = phone
            self.customer.address = address
            self.customer.notes = notes
        else:
            # Creating new
            self.customer = Customer(
                name=name,
                email=email,
                phone=phone,
                address=address,
                notes=notes
            )

        self.accept()

    def get_customer(self):
        """Get the customer object."""
        return self.customer

    def _validate_email(self, text):
        """Validate email format in real-time."""
        text = text.strip()

        if not text:
            self.email_input.setStyleSheet("")
            self.email_status.setText("")
            return

        # Email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if re.match(email_pattern, text):
            self.email_input.setStyleSheet("border: 1px solid #10b981;")
            self.email_status.setText("✓ Valid email")
            self.email_status.setStyleSheet("color: #10b981; font-size: 10px;")
        else:
            self.email_input.setStyleSheet("border: 1px solid #ef4444;")
            self.email_status.setText("❌ Invalid format")
            self.email_status.setStyleSheet("color: #ef4444; font-size: 10px;")

    def _validate_phone(self, text):
        """Validate phone number in real-time."""
        text = text.strip()

        if not text:
            self.phone_input.setStyleSheet("")
            self.phone_status.setText("")
            return

        # Remove common formatting characters
        digits_only = re.sub(r'[^\d]', '', text)

        if len(digits_only) < 10:
            self.phone_input.setStyleSheet("border: 1px solid #f59e0b;")
            self.phone_status.setText("⚠ Too short")
            self.phone_status.setStyleSheet("color: #f59e0b; font-size: 10px;")
        elif len(digits_only) > 15:
            self.phone_input.setStyleSheet("border: 1px solid #ef4444;")
            self.phone_status.setText("❌ Too long")
            self.phone_status.setStyleSheet("color: #ef4444; font-size: 10px;")
        else:
            self.phone_input.setStyleSheet("border: 1px solid #10b981;")
            self.phone_status.setText(f"✓ Valid ({len(digits_only)} digits)")
            self.phone_status.setStyleSheet("color: #10b981; font-size: 10px;")
