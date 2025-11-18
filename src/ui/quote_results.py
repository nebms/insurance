"""
Quote results display dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import date
from typing import Optional
import os
import platform

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import Quote, QuoteRepository
from reports.pdf_generator import PDFQuoteGenerator


class QuoteResultsDialog(QDialog):
    """Dialog showing quote calculation results."""

    def __init__(self, parent, params, result, customer_name="", agent_name=""):
        super().__init__(parent)
        self.params = params
        self.result = result
        self.customer_name = customer_name
        self.agent_name = agent_name
        self.quote_repo = QuoteRepository()
        self.customer_id = None  # Will be set if customer exists or is created

        self.setWindowTitle("Quote Results")
        self.setModal(True)
        self.resize(800, 600)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Insurance Quote Calculated")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Equipment Summary
        layout.addWidget(self._create_summary_group())

        # Premium Comparison Table
        layout.addWidget(self._create_comparison_table())

        # Notes
        layout.addWidget(QLabel("Notes (optional):"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Add any notes about this quote...")
        layout.addWidget(self.notes_input)

        # Buttons
        layout.addWidget(self._create_buttons())

        self.setLayout(layout)

    def _create_summary_group(self):
        """Create equipment summary."""
        group = QGroupBox("Equipment Summary")
        layout = QGridLayout()

        row = 0

        # State
        layout.addWidget(QLabel("State:"), row, 0)
        layout.addWidget(QLabel(self.params['state_code']), row, 1)
        row += 1

        # Age
        layout.addWidget(QLabel("Equipment Age:"), row, 0)
        age_text = f"{self.params['equipment_age_years']} years"
        if self.params['equipment_age_years'] == 0:
            age_text += " (New)"
        layout.addWidget(QLabel(age_text), row, 1)
        row += 1

        # Type
        layout.addWidget(QLabel("Equipment Type:"), row, 0)
        eq_type = "Towable" if self.params['is_towable'] else "Standard"
        layout.addWidget(QLabel(eq_type), row, 1)
        row += 1

        # M&E
        layout.addWidget(QLabel("M&E Endorsement:"), row, 0)
        me_text = "Yes" if self.params['has_me_endorsement'] else "No"
        layout.addWidget(QLabel(me_text), row, 1)
        row += 1

        # Coverage Amount
        layout.addWidget(QLabel("Total Coverage:"), row, 0)
        total_coverage = self.params['pivot_amount'] + self.params['ancillary_amount']
        layout.addWidget(QLabel(f"${total_coverage:,.2f}"), row, 1)
        row += 1

        # Term
        layout.addWidget(QLabel("Term:"), row, 0)
        layout.addWidget(QLabel(f"{self.params['term_months']} months"), row, 1)

        group.setLayout(layout)
        return group

    def _create_comparison_table(self):
        """Create premium comparison table."""
        table = QTableWidget()
        table.setRowCount(6)

        # Determine number of columns (scenarios)
        num_scenarios = 1
        if self.result['alt1_premium'] is not None:
            num_scenarios += 1
        if self.result['alt2_premium'] is not None:
            num_scenarios += 1

        table.setColumnCount(num_scenarios)

        # Set headers
        headers = ["Selected"]
        if self.result['alt1_premium'] is not None:
            alt1_ded = self._code_to_deductible(self.result['alt1_deductible'])
            headers.append(f"Option 2\n(${alt1_ded:,})")
        if self.result['alt2_premium'] is not None:
            alt2_ded = self._code_to_deductible(self.result['alt2_deductible'])
            headers.append(f"Option 3\n(${alt2_ded:,})")

        table.setHorizontalHeaderLabels(headers)

        # Row labels
        row_labels = [
            "Deductible",
            "Pivot Rate",
            "Pivot Premium",
            "Ancillary Premium",
            "Submersible Charge",
            "TOTAL PREMIUM"
        ]
        table.setVerticalHeaderLabels(row_labels)

        # Fill data - Column 0 (Selected)
        col = 0
        pivot_ded = self._code_to_deductible(self.params['pivot_deductible_code'])
        table.setItem(0, col, QTableWidgetItem(f"${pivot_ded:,}"))
        table.setItem(1, col, QTableWidgetItem(f"{self.result['pivot_rate']:.2f}%"))
        table.setItem(2, col, QTableWidgetItem(f"${self.result['pivot_premium']:,.2f}"))
        table.setItem(3, col, QTableWidgetItem(f"${self.result['ancillary_premium']:,.2f}"))
        table.setItem(4, col, QTableWidgetItem(f"${self.result['submersible_charge']:,.2f}"))

        total_item = QTableWidgetItem(f"${self.result['total_premium']:,.2f}")
        total_font = QFont()
        total_font.setBold(True)
        total_item.setFont(total_font)
        table.setItem(5, col, total_item)

        # Fill Alternative 1
        if self.result['alt1_premium'] is not None:
            col += 1
            alt1_ded = self._code_to_deductible(self.result['alt1_deductible'])
            table.setItem(0, col, QTableWidgetItem(f"${alt1_ded:,}"))
            table.setItem(1, col, QTableWidgetItem(f"{self.result['alt1_rate']:.2f}%"))
            table.setItem(2, col, QTableWidgetItem(f"${self.result['alt1_premium']:,.2f}"))
            table.setItem(3, col, QTableWidgetItem("-"))
            table.setItem(4, col, QTableWidgetItem("-"))

            total_item = QTableWidgetItem(f"${self.result['alt1_premium']:,.2f}")
            total_item.setFont(total_font)
            table.setItem(5, col, total_item)

        # Fill Alternative 2
        if self.result['alt2_premium'] is not None:
            col += 1
            alt2_ded = self._code_to_deductible(self.result['alt2_deductible'])
            table.setItem(0, col, QTableWidgetItem(f"${alt2_ded:,}"))
            table.setItem(1, col, QTableWidgetItem(f"{self.result['alt2_rate']:.2f}%"))
            table.setItem(2, col, QTableWidgetItem(f"${self.result['alt2_premium']:,.2f}"))
            table.setItem(3, col, QTableWidgetItem("-"))
            table.setItem(4, col, QTableWidgetItem("-"))

            total_item = QTableWidgetItem(f"${self.result['alt2_premium']:,.2f}")
            total_item.setFont(total_font)
            table.setItem(5, col, total_item)

        # Formatting
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        return table

    def _code_to_deductible(self, code):
        """Convert deductible code to amount."""
        mapping = {1: 500, 2: 1000, 3: 2500, 4: 5000}
        return mapping.get(code, 2500)

    def _create_buttons(self):
        """Create action buttons."""
        widget = QWidget()
        layout = QHBoxLayout()

        # Export PDF button
        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(self._export_pdf)

        # Save Quote button
        save_btn = QPushButton("Save Quote")
        save_btn.clicked.connect(self._save_quote)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        layout.addStretch()
        layout.addWidget(pdf_btn)
        layout.addWidget(close_btn)
        layout.addWidget(save_btn)

        widget.setLayout(layout)
        return widget

    def _export_pdf(self):
        """Export quote as PDF."""
        try:
            # Create temporary quote object for PDF
            quote = Quote(
                quote_number="PREVIEW",
                quote_date=str(date.today()),
                agent_name=self.agent_name,
                **self.params,
                **self.result
            )

            # Generate PDF
            generator = PDFQuoteGenerator()
            pdf_path = generator.generate_quote_pdf(quote, self.customer_name or "Preview Customer")

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
                f"PDF quote exported to:\n{pdf_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting PDF:\n{str(e)}"
            )

    def _save_quote(self):
        """Save quote to database."""
        try:
            # Find or create customer
            customer_id = self._get_or_create_customer()

            # Generate quote number
            quote_number = self.quote_repo.generate_quote_number()

            # Create quote object
            quote = Quote(
                quote_number=quote_number,
                customer_id=customer_id,
                agent_name=self.agent_name,
                quote_date=str(date.today()),
                pivot_amount=self.params['pivot_amount'],
                ancillary_amount=self.params['ancillary_amount'],
                submersible_pump_amount=self.params['submersible_pump_amount'],
                equipment_age_years=self.params['equipment_age_years'],
                is_towable=int(self.params['is_towable']),
                is_corner_or_long=int(self.params['is_corner_or_long']),
                has_me_endorsement=int(self.params['has_me_endorsement']),
                pivot_deductible_code=self.params['pivot_deductible_code'],
                ancillary_deductible_code=self.params['ancillary_deductible_code'],
                term_months=self.params['term_months'],
                state_code=self.params['state_code'],
                pivot_rate=self.result['pivot_rate'],
                ancillary_rate=self.result['ancillary_rate'],
                pivot_premium=self.result['pivot_premium'],
                ancillary_premium=self.result['ancillary_premium'],
                submersible_charge=self.result['submersible_charge'],
                total_premium=self.result['total_premium'],
                alt1_deductible=self.result['alt1_deductible'],
                alt1_rate=self.result['alt1_rate'],
                alt1_premium=self.result['alt1_premium'],
                alt2_deductible=self.result['alt2_deductible'],
                alt2_rate=self.result['alt2_rate'],
                alt2_premium=self.result['alt2_premium'],
                status='saved',
                notes=self.notes_input.text()
            )

            # Save to database
            quote_id = self.quote_repo.create(quote)

            QMessageBox.information(
                self,
                "Quote Saved",
                f"Quote {quote_number} saved successfully!\n\n"
                f"Total Premium: ${self.result['total_premium']:,.2f}"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Error saving quote:\n{str(e)}"
            )

    def _get_or_create_customer(self) -> Optional[int]:
        """Find existing customer or create new one."""
        from models.customer import Customer, CustomerRepository

        if not self.customer_name:
            return None  # Quote without customer

        customer_repo = CustomerRepository()

        # Search for existing customer by name
        existing = customer_repo.search(self.customer_name)

        if existing:
            # Found existing customer(s), use first match
            return existing[0].id
        else:
            # Create new customer
            customer = Customer(
                name=self.customer_name,
                email="",
                phone="",
                address="",
                notes=f"Auto-created from quote on {date.today()}"
            )
            customer_id = customer_repo.create(customer)
            return customer_id
