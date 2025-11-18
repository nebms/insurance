"""
Customer creation/edit dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

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
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        form_layout.addWidget(self.email_input, 1, 1)

        # Phone
        form_layout.addWidget(QLabel("Phone:"), 2, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(555) 123-4567")
        form_layout.addWidget(self.phone_input, 2, 1)

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

    def _save(self):
        """Validate and save customer."""
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Customer name is required."
            )
            self.name_input.setFocus()
            return

        # Create customer object
        if self.customer:
            # Editing existing
            self.customer.name = name
            self.customer.email = self.email_input.text().strip()
            self.customer.phone = self.phone_input.text().strip()
            self.customer.address = self.address_input.toPlainText().strip()
            self.customer.notes = self.notes_input.toPlainText().strip()
        else:
            # Creating new
            self.customer = Customer(
                name=name,
                email=self.email_input.text().strip(),
                phone=self.phone_input.text().strip(),
                address=self.address_input.toPlainText().strip(),
                notes=self.notes_input.toPlainText().strip()
            )

        self.accept()

    def get_customer(self):
        """Get the customer object."""
        return self.customer
