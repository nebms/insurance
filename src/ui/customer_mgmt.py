"""
Customer management widget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.customer import Customer, CustomerRepository


class CustomerManagement(QWidget):
    """Customer management interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.customer_repo = CustomerRepository()

        self._init_ui()
        self._load_customers()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, email, or phone...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Customer table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Email", "Phone", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add Customer")
        add_btn.clicked.connect(self._add_customer)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_customers)

        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(add_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_customers(self):
        """Load all customers into table."""
        customers = self.customer_repo.get_all()
        self.table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            self.table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
            self.table.setItem(row, 1, QTableWidgetItem(customer.name))
            self.table.setItem(row, 2, QTableWidgetItem(customer.email))
            self.table.setItem(row, 3, QTableWidgetItem(customer.phone))

            # Actions button
            actions_btn = QPushButton("View Quotes")
            actions_btn.clicked.connect(lambda checked, c=customer: self._view_customer_quotes(c))
            self.table.setCellWidget(row, 4, actions_btn)

    def _on_search(self, text):
        """Filter customers by search text."""
        if not text:
            self._load_customers()
            return

        customers = self.customer_repo.search(text)
        self.table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            self.table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
            self.table.setItem(row, 1, QTableWidgetItem(customer.name))
            self.table.setItem(row, 2, QTableWidgetItem(customer.email))
            self.table.setItem(row, 3, QTableWidgetItem(customer.phone))

    def _add_customer(self):
        """Add new customer (simplified)."""
        QMessageBox.information(
            self,
            "Add Customer",
            "Customer creation dialog will be implemented.\n\n"
            "For now, customers are created automatically from quotes."
        )

    def _view_customer_quotes(self, customer):
        """View quotes for customer."""
        from models.quote import QuoteRepository
        quote_repo = QuoteRepository()
        quotes = quote_repo.get_by_customer(customer.id)

        if not quotes:
            QMessageBox.information(
                self,
                "No Quotes",
                f"No quotes found for {customer.name}"
            )
            return

        # Show quotes list
        msg = f"Quotes for {customer.name}:\n\n"
        for quote in quotes:
            msg += f"• {quote.quote_number} - ${quote.total_premium:,.2f} ({quote.quote_date})\n"

        QMessageBox.information(self, "Customer Quotes", msg)
