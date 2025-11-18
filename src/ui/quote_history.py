"""
Quote history widget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QLabel, QMessageBox,
    QDialog, QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os
import platform

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import QuoteRepository, Quote
from models.customer import CustomerRepository
from reports.pdf_generator import PDFQuoteGenerator


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
        title = QLabel("Quote History")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Quotes table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Quote #", "Date", "State", "Age", "Total Premium", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Enable double-click to view details
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)

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

            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, q=quote: self._view_quote(q))

            pdf_btn = QPushButton("Export PDF")
            pdf_btn.clicked.connect(lambda checked, q=quote: self._export_pdf(q))

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, q=quote: self._delete_quote(q))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(pdf_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 6, actions_widget)

    def _on_row_double_clicked(self, row, column):
        """Handle double-click on row."""
        quote_number = self.table.item(row, 0).text()
        quote = self.quote_repo.get_by_quote_number(quote_number)
        if quote:
            self._view_quote(quote)

    def _view_quote(self, quote):
        """View quote details."""
        dialog = QuoteDetailsDialog(self, quote)
        dialog.exec()

    def _export_pdf(self, quote):
        """Export quote as PDF."""
        try:
            # Get customer name
            customer_name = "Customer"
            if quote.customer_id:
                customer_repo = CustomerRepository()
                customer = customer_repo.get_by_id(quote.customer_id)
                if customer:
                    customer_name = customer.name

            # Generate PDF
            generator = PDFQuoteGenerator()
            pdf_path = generator.generate_quote_pdf(quote, customer_name)

            # Open PDF
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{pdf_path}"')
            else:  # Linux
                os.system(f'xdg-open "{pdf_path}"')

            QMessageBox.information(
                self,
                "PDF Exported",
                f"PDF exported to:\n{pdf_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting PDF:\n{str(e)}"
            )

    def _delete_quote(self, quote):
        """Delete quote after confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete quote {quote.quote_number}?\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.quote_repo.delete(quote.id)
                if success:
                    QMessageBox.information(
                        self,
                        "Quote Deleted",
                        f"Quote {quote.quote_number} has been deleted."
                    )
                    self._load_quotes()  # Refresh table
                else:
                    QMessageBox.warning(
                        self,
                        "Delete Failed",
                        f"Could not delete quote {quote.quote_number}."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Error",
                    f"Error deleting quote:\n{str(e)}"
                )


class QuoteDetailsDialog(QDialog):
    """Dialog for viewing quote details."""

    def __init__(self, parent, quote):
        super().__init__(parent)
        self.quote = quote
        self.setWindowTitle(f"Quote Details - {quote.quote_number}")
        self.setModal(True)
        self.resize(600, 500)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Quote {self.quote.quote_number}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Details grid
        grid = QGridLayout()
        row = 0

        # Quote Info
        self._add_detail(grid, row, "Quote Number:", self.quote.quote_number)
        row += 1
        self._add_detail(grid, row, "Date:", self.quote.quote_date)
        row += 1
        self._add_detail(grid, row, "Agent:", self.quote.agent_name or "N/A")
        row += 1
        self._add_detail(grid, row, "Status:", self.quote.status)
        row += 1

        # Equipment
        grid.addWidget(QLabel(""), row, 0)  # Spacer
        row += 1
        header = QLabel("Equipment Details")
        header_font = QFont()
        header_font.setBold(True)
        header.setFont(header_font)
        grid.addWidget(header, row, 0, 1, 2)
        row += 1

        self._add_detail(grid, row, "State:", self.quote.state_code)
        row += 1
        self._add_detail(grid, row, "Age:", f"{self.quote.equipment_age_years} years")
        row += 1
        self._add_detail(grid, row, "Type:", "Towable" if self.quote.is_towable else "Standard")
        row += 1
        self._add_detail(grid, row, "M&E Endorsement:", "Yes" if self.quote.has_me_endorsement else "No")
        row += 1
        self._add_detail(grid, row, "Term:", f"{self.quote.term_months} months")
        row += 1

        # Coverage
        grid.addWidget(QLabel(""), row, 0)  # Spacer
        row += 1
        header = QLabel("Coverage Amounts")
        header.setFont(header_font)
        grid.addWidget(header, row, 0, 1, 2)
        row += 1

        self._add_detail(grid, row, "Pivot:", f"${self.quote.pivot_amount:,.2f}")
        row += 1
        self._add_detail(grid, row, "Ancillary:", f"${self.quote.ancillary_amount:,.2f}")
        row += 1
        self._add_detail(grid, row, "Pump:", f"${self.quote.submersible_pump_amount:,.2f}")
        row += 1

        # Premiums
        grid.addWidget(QLabel(""), row, 0)  # Spacer
        row += 1
        header = QLabel("Premiums")
        header.setFont(header_font)
        grid.addWidget(header, row, 0, 1, 2)
        row += 1

        self._add_detail(grid, row, "Pivot Premium:", f"${self.quote.pivot_premium:,.2f}")
        row += 1
        self._add_detail(grid, row, "Ancillary Premium:", f"${self.quote.ancillary_premium:,.2f}")
        row += 1
        self._add_detail(grid, row, "Submersible Charge:", f"${self.quote.submersible_charge:,.2f}")
        row += 1
        self._add_detail(grid, row, "TOTAL:", f"${self.quote.total_premium:,.2f}", bold=True)
        row += 1

        layout.addLayout(grid)

        # Notes
        if self.quote.notes:
            layout.addWidget(QLabel("Notes:"))
            notes_text = QTextEdit()
            notes_text.setPlainText(self.quote.notes)
            notes_text.setReadOnly(True)
            notes_text.setMaximumHeight(100)
            layout.addWidget(notes_text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _add_detail(self, grid, row, label, value, bold=False):
        """Add a detail row to the grid."""
        label_widget = QLabel(label)
        value_widget = QLabel(str(value))

        if bold:
            font = QFont()
            font.setBold(True)
            label_widget.setFont(font)
            value_widget.setFont(font)

        grid.addWidget(label_widget, row, 0)
        grid.addWidget(value_widget, row, 1)
