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
from models.quote_line_item import QuoteLineItem
from reports.pdf_generator import PDFQuoteGenerator


class QuoteResultsDialog(QDialog):
    """Dialog showing quote calculation results."""

    def __init__(self, parent, params, result, customer_name="", agent_name="", line_items=None):
        super().__init__(parent)
        self.params = params
        self.result = result
        self.customer_name = customer_name
        self.agent_name = agent_name
        self.line_items = line_items  # For multi-pivot quotes
        self.is_multi_pivot = params.get('is_multi_pivot', False)
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

        # Premium Display - different for single vs multi-pivot
        if self.is_multi_pivot:
            layout.addWidget(self._create_line_items_table())
        else:
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
        group = QGroupBox("Quote Summary")
        layout = QGridLayout()

        row = 0

        # State
        layout.addWidget(QLabel("State:"), row, 0)
        layout.addWidget(QLabel(self.params['state_code']), row, 1)
        row += 1

        # Term
        layout.addWidget(QLabel("Term:"), row, 0)
        layout.addWidget(QLabel(f"{self.params['term_months']} months"), row, 1)
        row += 1

        if self.is_multi_pivot:
            # Multi-pivot: show count and total
            layout.addWidget(QLabel("Equipment Items:"), row, 0)
            layout.addWidget(QLabel(f"{len(self.line_items)} items"), row, 1)
            row += 1

            layout.addWidget(QLabel("Total Premium:"), row, 0)
            total_label = QLabel(f"${self.result['total_premium']:,.2f}")
            total_font = QFont()
            total_font.setPointSize(14)
            total_font.setBold(True)
            total_label.setFont(total_font)
            layout.addWidget(total_label, row, 1)

        else:
            # Single pivot: show details
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

        group.setLayout(layout)
        return group

    def _create_line_items_table(self):
        """Create line items table for multi-pivot quotes."""
        group = QGroupBox("Equipment Items")
        layout = QVBoxLayout()

        table = QTableWidget()
        table.setRowCount(len(self.line_items))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "#", "Pivot Amount", "Age", "Type", "Deductible", "Premium"
        ])

        # Set column widths
        table.setColumnWidth(0, 40)   # Line number
        table.setColumnWidth(1, 120)  # Pivot amount
        table.setColumnWidth(2, 60)   # Age
        table.setColumnWidth(3, 120)  # Type
        table.setColumnWidth(4, 100)  # Deductible
        table.setColumnWidth(5, 120)  # Premium

        deductible_map = {1: "$500", 2: "$1,000", 3: "$2,500", 4: "$5,000"}

        for row, item in enumerate(self.line_items):
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

        layout.addWidget(table)

        # Total row
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel("TOTAL PREMIUM:")
        total_label_font = QFont()
        total_label_font.setBold(True)
        total_label.setFont(total_label_font)

        total_value = QLabel(f"${self.result['total_premium']:,.2f}")
        total_value_font = QFont()
        total_value_font.setPointSize(14)
        total_value_font.setBold(True)
        total_value.setFont(total_value_font)

        total_layout.addWidget(total_label)
        total_layout.addWidget(total_value)

        layout.addLayout(total_layout)

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
            # Generate a preview quote number for tracking
            # Format: PREVIEW-YYYYMMDD-HHMMSS for uniqueness
            from datetime import datetime
            preview_number = f"PREVIEW-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # Create temporary quote object for PDF
            quote = Quote(
                quote_number=preview_number,
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

            # Create quote object (header)
            quote = Quote(
                quote_number=quote_number,
                customer_id=customer_id,
                agent_name=self.agent_name,
                quote_date=str(date.today()),
                term_months=self.params['term_months'],
                state_code=self.params['state_code'],
                total_premium=self.result['total_premium'],
                status='saved',
                notes=self.notes_input.text()
            )

            # Save to database with line items
            if self.is_multi_pivot:
                # Multi-pivot: save with line items
                quote_id = self.quote_repo.create(quote, self.line_items)
                quote.line_items = self.line_items
            else:
                # Single pivot: populate legacy fields
                quote.pivot_amount = self.params['pivot_amount']
                quote.ancillary_amount = self.params['ancillary_amount']
                quote.submersible_pump_amount = self.params['submersible_pump_amount']
                quote.equipment_age_years = self.params['equipment_age_years']
                quote.is_towable = int(self.params['is_towable'])
                quote.is_corner_or_long = int(self.params['is_corner_or_long'])
                quote.has_me_endorsement = int(self.params['has_me_endorsement'])
                quote.pivot_deductible_code = self.params['pivot_deductible_code']
                quote.ancillary_deductible_code = self.params['ancillary_deductible_code']
                quote.pivot_rate = self.result['pivot_rate']
                quote.ancillary_rate = self.result['ancillary_rate']
                quote.pivot_premium = self.result['pivot_premium']
                quote.ancillary_premium = self.result['ancillary_premium']
                quote.submersible_charge = self.result['submersible_charge']
                quote.alt1_deductible = self.result['alt1_deductible']
                quote.alt1_rate = self.result['alt1_rate']
                quote.alt1_premium = self.result['alt1_premium']
                quote.alt2_deductible = self.result['alt2_deductible']
                quote.alt2_rate = self.result['alt2_rate']
                quote.alt2_premium = self.result['alt2_premium']

                # Save (will auto-create single line item from quote fields)
                quote_id = self.quote_repo.create(quote)

            # Ask if user wants to export PDF
            reply = QMessageBox.question(
                self,
                "Quote Saved",
                f"Quote {quote_number} saved successfully!\n\n"
                f"Total Premium: ${self.result['total_premium']:,.2f}\n\n"
                f"Would you like to export this quote as a PDF?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            # Export PDF if requested
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    generator = PDFQuoteGenerator()
                    pdf_path = generator.generate_quote_pdf(quote, self.customer_name or "Customer")

                    # Open PDF
                    if platform.system() == 'Windows':
                        os.startfile(pdf_path)
                    elif platform.system() == 'Darwin':  # macOS
                        os.system(f'open "{pdf_path}"')
                    else:  # Linux
                        os.system(f'xdg-open "{pdf_path}"')

                    QMessageBox.information(
                        self,
                        "PDF Generated",
                        f"PDF exported to:\n{pdf_path}"
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "PDF Export Error",
                        f"Quote was saved but PDF export failed:\n{str(e)}"
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
