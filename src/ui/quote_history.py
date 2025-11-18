"""
Quote history widget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import QuoteRepository


class QuoteHistory(QWidget):
    """Quote history interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.quote_repo = QuoteRepository()

        self._init_ui()
        self._load_quotes()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        layout.addWidget(QLabel("Quote History"))

        # Quotes table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Quote #", "Date", "State", "Age", "Total Premium", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_quotes)

        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_quotes(self):
        """Load quotes into table."""
        quotes = self.quote_repo.get_all(limit=100)
        self.table.setRowCount(len(quotes))

        for row, quote in enumerate(quotes):
            self.table.setItem(row, 0, QTableWidgetItem(quote.quote_number))
            self.table.setItem(row, 1, QTableWidgetItem(quote.quote_date))
            self.table.setItem(row, 2, QTableWidgetItem(quote.state_code))
            self.table.setItem(row, 3, QTableWidgetItem(f"{quote.equipment_age_years} yrs"))
            self.table.setItem(row, 4, QTableWidgetItem(f"${quote.total_premium:,.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(quote.status))
