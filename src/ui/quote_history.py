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
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import QuoteRepository, Quote
from models.customer import CustomerRepository
from reports.pdf_generator import PDFQuoteGenerator
from ui.quote_comparison_dialog import QuoteComparisonDialog


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
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Compare", "Quote #", "Date", "State", "Type", "Items", "Total Premium", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Track selected quotes for comparison
        self.selected_quotes = []

        # Enable double-click to view details
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.compare_btn = QPushButton("Compare Selected")
        self.compare_btn.clicked.connect(self._compare_quotes)
        self.compare_btn.setEnabled(False)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_quotes)

        button_layout.addWidget(self.compare_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_quotes(self):
        """Load quotes into table."""
        # Clear selected quotes
        self.selected_quotes = []
        self.compare_btn.setEnabled(False)

        # Load quotes with line items for accurate display
        quotes = self.quote_repo.get_all(limit=100, load_line_items=True)
        self.table.setRowCount(len(quotes))

        for row, quote in enumerate(quotes):
            is_multi = quote.has_multiple_items()

            # Comparison checkbox
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, q=quote: self._on_checkbox_changed(state, q))
            checkbox_layout.addWidget(checkbox)
            self.table.setCellWidget(row, 0, checkbox_widget)

            self.table.setItem(row, 1, QTableWidgetItem(quote.quote_number))
            self.table.setItem(row, 2, QTableWidgetItem(quote.quote_date))
            self.table.setItem(row, 3, QTableWidgetItem(quote.state_code))

            # Type column
            if is_multi:
                type_item = QTableWidgetItem("Multi-Pivot")
                type_font = QFont()
                type_font.setBold(True)
                type_item.setFont(type_font)
                self.table.setItem(row, 4, type_item)
            else:
                self.table.setItem(row, 4, QTableWidgetItem("Single"))

            # Items column
            if is_multi:
                self.table.setItem(row, 5, QTableWidgetItem(f"{len(quote.line_items)} items"))
            else:
                self.table.setItem(row, 5, QTableWidgetItem(f"{quote.equipment_age_years} yrs"))

            self.table.setItem(row, 6, QTableWidgetItem(f"${quote.total_premium:,.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(quote.status))

            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, q=quote: self._view_quote(q))

            duplicate_btn = QPushButton("Duplicate")
            duplicate_btn.clicked.connect(lambda checked, q=quote: self._duplicate_quote(q))

            pdf_btn = QPushButton("Export PDF")
            pdf_btn.clicked.connect(lambda checked, q=quote: self._export_pdf(q))

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, q=quote: self._delete_quote(q))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(duplicate_btn)
            actions_layout.addWidget(pdf_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 8, actions_widget)

    def _on_row_double_clicked(self, row, column):
        """Handle double-click on row."""
        quote_number = self.table.item(row, 1).text()
        quote = self.quote_repo.get_by_quote_number(quote_number)
        if quote:
            self._view_quote(quote)

    def _on_checkbox_changed(self, state, quote):
        """Handle checkbox state change for comparison."""
        if state == Qt.CheckState.Checked.value:
            # Add to selected quotes
            if quote not in self.selected_quotes:
                self.selected_quotes.append(quote)
        else:
            # Remove from selected quotes
            if quote in self.selected_quotes:
                self.selected_quotes.remove(quote)

        # Enable/disable compare button
        self.compare_btn.setEnabled(len(self.selected_quotes) >= 2)

        # Update button text with count
        if len(self.selected_quotes) >= 2:
            self.compare_btn.setText(f"Compare Selected ({len(self.selected_quotes)})")
        else:
            self.compare_btn.setText("Compare Selected")

    def _compare_quotes(self):
        """Compare selected quotes."""
        if len(self.selected_quotes) < 2:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select at least 2 quotes to compare."
            )
            return

        if len(self.selected_quotes) > 4:
            QMessageBox.warning(
                self,
                "Too Many Quotes",
                "Please select no more than 4 quotes to compare.\n\n"
                "For best viewing, 2-3 quotes are recommended."
            )
            return

        # Show comparison dialog
        dialog = QuoteComparisonDialog(self.selected_quotes, self)
        dialog.exec()

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

    def _duplicate_quote(self, quote):
        """Duplicate a quote with all its line items."""
        try:
            # Generate new quote number
            new_quote_number = self.quote_repo.generate_quote_number()

            # Create new quote with copied data
            new_quote = Quote(
                quote_number=new_quote_number,
                state_code=quote.state_code,
                term_months=quote.term_months,
                customer_id=quote.customer_id,
                agent_name=quote.agent_name,
                quote_date=str(date.today()),
                status='draft',
                notes=f"Duplicated from {quote.quote_number}",
                # Legacy fields for backward compatibility
                pivot_amount=quote.pivot_amount,
                equipment_age_years=quote.equipment_age_years,
                pivot_deductible_code=quote.pivot_deductible_code,
                ancillary_deductible_code=quote.ancillary_deductible_code,
                ancillary_amount=quote.ancillary_amount,
                submersible_pump_amount=quote.submersible_pump_amount,
                is_towable=quote.is_towable,
                is_corner_or_long=quote.is_corner_or_long,
                has_me_endorsement=quote.has_me_endorsement,
                pivot_rate=quote.pivot_rate,
                ancillary_rate=quote.ancillary_rate,
                pivot_premium=quote.pivot_premium,
                ancillary_premium=quote.ancillary_premium,
                submersible_charge=quote.submersible_charge,
                total_premium=quote.total_premium
            )

            # Duplicate line items if this is a multi-pivot quote
            duplicated_line_items = None
            if quote.has_multiple_items():
                from models.quote_line_item import QuoteLineItem
                duplicated_line_items = []

                for item in quote.line_items:
                    new_item = QuoteLineItem(
                        line_number=item.line_number,
                        pivot_amount=item.pivot_amount,
                        equipment_age_years=item.equipment_age_years,
                        pivot_deductible_code=item.pivot_deductible_code,
                        ancillary_deductible_code=item.ancillary_deductible_code,
                        ancillary_amount=item.ancillary_amount,
                        submersible_pump_amount=item.submersible_pump_amount,
                        is_towable=item.is_towable,
                        is_corner_or_long=item.is_corner_or_long,
                        has_me_endorsement=item.has_me_endorsement,
                        pivot_rate=item.pivot_rate,
                        ancillary_rate=item.ancillary_rate,
                        pivot_premium=item.pivot_premium,
                        ancillary_premium=item.ancillary_premium,
                        submersible_charge=item.submersible_charge,
                        line_total_premium=item.line_total_premium,
                        alt1_deductible=item.alt1_deductible,
                        alt1_rate=item.alt1_rate,
                        alt1_premium=item.alt1_premium,
                        alt2_deductible=item.alt2_deductible,
                        alt2_rate=item.alt2_rate,
                        alt2_premium=item.alt2_premium
                    )
                    duplicated_line_items.append(new_item)

            # Save the duplicated quote
            new_quote_id = self.quote_repo.create(new_quote, duplicated_line_items)

            if new_quote_id:
                QMessageBox.information(
                    self,
                    "Quote Duplicated",
                    f"Quote duplicated successfully!\n\n"
                    f"Original: {quote.quote_number}\n"
                    f"New Quote: {new_quote_number}"
                )
                self._load_quotes()  # Refresh table
            else:
                QMessageBox.warning(
                    self,
                    "Duplication Failed",
                    f"Could not duplicate quote {quote.quote_number}."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Duplication Error",
                f"Error duplicating quote:\n{str(e)}"
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
        is_multi = self.quote.has_multiple_items()
        title_text = f"Quote {self.quote.quote_number}"
        if is_multi:
            title_text += f" (Multi-Pivot - {len(self.quote.line_items)} items)"

        title = QLabel(title_text)
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
        self._add_detail(grid, row, "State:", self.quote.state_code)
        row += 1
        self._add_detail(grid, row, "Term:", f"{self.quote.term_months} months")
        row += 1

        layout.addLayout(grid)

        if is_multi:
            # Multi-pivot: show line items table
            self._add_line_items_table(layout)
        else:
            # Single pivot: show traditional details
            self._add_single_pivot_details(layout)

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

    def _add_single_pivot_details(self, layout):
        """Add single pivot equipment details."""
        grid = QGridLayout()
        row = 0

        header_font = QFont()
        header_font.setBold(True)

        # Equipment
        header = QLabel("Equipment Details")
        header.setFont(header_font)
        grid.addWidget(header, row, 0, 1, 2)
        row += 1

        self._add_detail(grid, row, "Age:", f"{self.quote.equipment_age_years} years")
        row += 1
        self._add_detail(grid, row, "Type:", "Towable" if self.quote.is_towable else "Standard")
        row += 1
        self._add_detail(grid, row, "M&E Endorsement:", "Yes" if self.quote.has_me_endorsement else "No")
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

    def _add_line_items_table(self, layout):
        """Add line items table for multi-pivot quotes."""
        header_font = QFont()
        header_font.setBold(True)

        header = QLabel("Equipment Items")
        header.setFont(header_font)
        layout.addWidget(header)

        # Create table
        table = QTableWidget()
        table.setRowCount(len(self.quote.line_items))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "#", "Pivot Amount", "Age", "Type", "Deductible", "Premium"
        ])

        # Set column widths
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 120)
        table.setColumnWidth(2, 60)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 100)
        table.setColumnWidth(5, 120)

        deductible_map = {1: "$500", 2: "$1,000", 3: "$2,500", 4: "$5,000"}

        for row, item in enumerate(self.quote.line_items):
            # Line number
            line_num = QTableWidgetItem(str(item.line_number))
            line_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, line_num)

            # Pivot amount
            pivot_amt = QTableWidgetItem(f"${item.pivot_amount:,.2f}")
            pivot_amt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 1, pivot_amt)

            # Age
            age = QTableWidgetItem(f"{item.equipment_age_years} yrs")
            age.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, age)

            # Type
            type_parts = []
            if item.is_towable:
                type_parts.append("Towable")
            else:
                type_parts.append("Standard")
            if item.is_corner_or_long:
                type_parts.append("Corner/Long")
            type_str = ", ".join(type_parts)
            table.setItem(row, 3, QTableWidgetItem(type_str))

            # Deductible
            ded = deductible_map.get(item.pivot_deductible_code, "N/A")
            table.setItem(row, 4, QTableWidgetItem(ded))

            # Premium
            prem = QTableWidgetItem(f"${item.line_total_premium:,.2f}")
            prem.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            prem_font = QFont()
            prem_font.setBold(True)
            prem.setFont(prem_font)
            table.setItem(row, 5, prem)

        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMaximumHeight(min(300, (len(self.quote.line_items) + 1) * 35))

        layout.addWidget(table)

        # Total row
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel("TOTAL PREMIUM:")
        total_label_font = QFont()
        total_label_font.setBold(True)
        total_label.setFont(total_label_font)

        total_value = QLabel(f"${self.quote.total_premium:,.2f}")
        total_value_font = QFont()
        total_value_font.setPointSize(12)
        total_value_font.setBold(True)
        total_value.setFont(total_value_font)

        total_layout.addWidget(total_label)
        total_layout.addWidget(total_value)

        layout.addLayout(total_layout)

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
