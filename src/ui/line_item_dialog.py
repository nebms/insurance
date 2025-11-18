"""
Line Item Dialog for adding/editing individual equipment items.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator, QIntValidator
from typing import Optional

from models.quote_line_item import QuoteLineItem
from calculations.premium_calc import PremiumCalculator


class LineItemDialog(QDialog):
    """Dialog for adding/editing a line item."""

    def __init__(self, state_code: str, term_months: int,
                 line_item: Optional[QuoteLineItem] = None, parent=None):
        """
        Initialize line item dialog.

        Args:
            state_code: State code for rate lookup
            term_months: Term in months
            line_item: Existing line item to edit (None for new)
            parent: Parent widget
        """
        super().__init__(parent)
        self.state_code = state_code
        self.term_months = term_months
        self.line_item = line_item
        self.is_edit_mode = line_item is not None

        self.calculator = PremiumCalculator()

        title = "Edit Equipment Item" if self.is_edit_mode else "Add Equipment Item"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 600)

        self._init_ui()

        if self.is_edit_mode:
            self._populate_from_line_item()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Equipment Item Details" if not self.is_edit_mode else "Edit Equipment Details")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Equipment Details Group
        equipment_group = QGroupBox("Equipment Specifications")
        equipment_layout = QGridLayout()
        row = 0

        # Pivot Amount
        equipment_layout.addWidget(QLabel("Pivot Amount:"), row, 0)
        self.pivot_amount = QLineEdit()
        self.pivot_amount.setPlaceholderText("e.g., 150000")
        self.pivot_amount.setValidator(QDoubleValidator(0.0, 10000000.0, 2))
        equipment_layout.addWidget(self.pivot_amount, row, 1)
        row += 1

        # Equipment Age
        equipment_layout.addWidget(QLabel("Equipment Age (years):"), row, 0)
        self.equipment_age = QLineEdit()
        self.equipment_age.setPlaceholderText("e.g., 5")
        self.equipment_age.setValidator(QIntValidator(0, 100))
        equipment_layout.addWidget(self.equipment_age, row, 1)
        row += 1

        # Equipment Type
        equipment_layout.addWidget(QLabel("Equipment Type:"), row, 0)
        self.is_towable = QCheckBox("Towable")
        equipment_layout.addWidget(self.is_towable, row, 1)
        row += 1

        equipment_layout.addWidget(QLabel(""), row, 0)
        self.is_corner_or_long = QCheckBox("Corner or Long System")
        equipment_layout.addWidget(self.is_corner_or_long, row, 1)
        row += 1

        # M&E Endorsement
        equipment_layout.addWidget(QLabel("M&E Endorsement:"), row, 0)
        self.has_me_endorsement = QCheckBox("Include M&E Coverage")
        self.has_me_endorsement.setChecked(True)
        equipment_layout.addWidget(self.has_me_endorsement, row, 1)
        row += 1

        equipment_group.setLayout(equipment_layout)
        layout.addWidget(equipment_group)

        # Coverage Group
        coverage_group = QGroupBox("Coverage Options")
        coverage_layout = QGridLayout()
        row = 0

        # Pivot Deductible
        coverage_layout.addWidget(QLabel("Pivot Deductible:"), row, 0)
        self.pivot_deductible = QComboBox()
        self.pivot_deductible.addItem("$500", 1)
        self.pivot_deductible.addItem("$1,000", 2)
        self.pivot_deductible.addItem("$2,500", 3)
        self.pivot_deductible.addItem("$5,000", 4)
        self.pivot_deductible.setCurrentIndex(2)  # Default to $2,500
        coverage_layout.addWidget(self.pivot_deductible, row, 1)
        row += 1

        # Ancillary Amount
        coverage_layout.addWidget(QLabel("Ancillary Amount:"), row, 0)
        self.ancillary_amount = QLineEdit()
        self.ancillary_amount.setPlaceholderText("0 (optional)")
        self.ancillary_amount.setValidator(QDoubleValidator(0.0, 10000000.0, 2))
        self.ancillary_amount.setText("0")
        coverage_layout.addWidget(self.ancillary_amount, row, 1)
        row += 1

        # Ancillary Deductible
        coverage_layout.addWidget(QLabel("Ancillary Deductible:"), row, 0)
        self.ancillary_deductible = QComboBox()
        self.ancillary_deductible.addItem("$500", 1)
        self.ancillary_deductible.addItem("$1,000", 2)
        self.ancillary_deductible.addItem("$2,500", 3)
        self.ancillary_deductible.addItem("$5,000", 4)
        self.ancillary_deductible.setCurrentIndex(1)  # Default to $1,000
        coverage_layout.addWidget(self.ancillary_deductible, row, 1)
        row += 1

        # Submersible Pump Amount
        coverage_layout.addWidget(QLabel("Submersible Pump:"), row, 0)
        self.submersible_pump_amount = QLineEdit()
        self.submersible_pump_amount.setPlaceholderText("0 (optional)")
        self.submersible_pump_amount.setValidator(QDoubleValidator(0.0, 10000000.0, 2))
        self.submersible_pump_amount.setText("0")
        coverage_layout.addWidget(self.submersible_pump_amount, row, 1)
        row += 1

        coverage_group.setLayout(coverage_layout)
        layout.addWidget(coverage_group)

        # Calculate button
        calc_layout = QHBoxLayout()
        self.calculate_btn = QPushButton("Calculate Premium")
        self.calculate_btn.clicked.connect(self._calculate_premium)
        calc_layout.addStretch()
        calc_layout.addWidget(self.calculate_btn)
        layout.addLayout(calc_layout)

        # Premium display
        premium_layout = QHBoxLayout()
        premium_label = QLabel("Estimated Premium:")
        premium_label_font = QFont()
        premium_label_font.setBold(True)
        premium_label.setFont(premium_label_font)

        self.premium_display = QLabel("Not calculated")
        premium_display_font = QFont()
        premium_display_font.setPointSize(14)
        premium_display_font.setBold(True)
        self.premium_display.setFont(premium_display_font)

        premium_layout.addStretch()
        premium_layout.addWidget(premium_label)
        premium_layout.addWidget(self.premium_display)

        layout.addLayout(premium_layout)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save" if self.is_edit_mode else "Add")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _populate_from_line_item(self):
        """Populate form from existing line item."""
        if not self.line_item:
            return

        self.pivot_amount.setText(str(self.line_item.pivot_amount))
        self.equipment_age.setText(str(self.line_item.equipment_age_years))
        self.is_towable.setChecked(bool(self.line_item.is_towable))
        self.is_corner_or_long.setChecked(bool(self.line_item.is_corner_or_long))
        self.has_me_endorsement.setChecked(bool(self.line_item.has_me_endorsement))

        # Set deductibles
        pivot_ded_index = self.pivot_deductible.findData(self.line_item.pivot_deductible_code)
        if pivot_ded_index >= 0:
            self.pivot_deductible.setCurrentIndex(pivot_ded_index)

        anc_ded_index = self.ancillary_deductible.findData(self.line_item.ancillary_deductible_code)
        if anc_ded_index >= 0:
            self.ancillary_deductible.setCurrentIndex(anc_ded_index)

        self.ancillary_amount.setText(str(self.line_item.ancillary_amount or 0))
        self.submersible_pump_amount.setText(str(self.line_item.submersible_pump_amount or 0))

        # Display existing premium if available
        if self.line_item.line_total_premium:
            self.premium_display.setText(f"${self.line_item.line_total_premium:,.2f}")

    def _validate_inputs(self) -> bool:
        """Validate form inputs."""
        # Pivot amount
        if not self.pivot_amount.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter pivot amount")
            self.pivot_amount.setFocus()
            return False

        try:
            pivot_amt = float(self.pivot_amount.text())
            if pivot_amt <= 0:
                QMessageBox.warning(self, "Validation Error", "Pivot amount must be greater than 0")
                self.pivot_amount.setFocus()
                return False
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Invalid pivot amount")
            self.pivot_amount.setFocus()
            return False

        # Equipment age
        if not self.equipment_age.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter equipment age")
            self.equipment_age.setFocus()
            return False

        try:
            age = int(self.equipment_age.text())
            if age < 0:
                QMessageBox.warning(self, "Validation Error", "Equipment age cannot be negative")
                self.equipment_age.setFocus()
                return False
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Invalid equipment age")
            self.equipment_age.setFocus()
            return False

        return True

    def _calculate_premium(self):
        """Calculate premium for this line item."""
        if not self._validate_inputs():
            return

        try:
            # Get values
            pivot_amt = float(self.pivot_amount.text())
            age = int(self.equipment_age.text())
            pivot_ded = self.pivot_deductible.currentData()
            anc_ded = self.ancillary_deductible.currentData()

            anc_amt_text = self.ancillary_amount.text().strip()
            anc_amt = float(anc_amt_text) if anc_amt_text else 0

            pump_amt_text = self.submersible_pump_amount.text().strip()
            pump_amt = float(pump_amt_text) if pump_amt_text else 0

            # Calculate
            result = self.calculator.calculate_quote(
                pivot_amount=pivot_amt,
                equipment_age_years=age,
                pivot_deductible_code=pivot_ded,
                ancillary_deductible_code=anc_ded,
                state_code=self.state_code,
                term_months=self.term_months,
                ancillary_amount=anc_amt,
                submersible_pump_amount=pump_amt,
                is_towable=self.is_towable.isChecked(),
                is_corner_or_long=self.is_corner_or_long.isChecked(),
                has_me_endorsement=self.has_me_endorsement.isChecked()
            )

            # Display premium
            total = result.get('total_premium', 0)
            self.premium_display.setText(f"${total:,.2f}")

            # Store result for save
            self.calculated_result = result

        except Exception as e:
            QMessageBox.critical(
                self,
                "Calculation Error",
                f"Error calculating premium:\n{str(e)}"
            )

    def _save(self):
        """Save line item."""
        if not self._validate_inputs():
            return

        # Calculate if not already done
        if not hasattr(self, 'calculated_result'):
            self._calculate_premium()
            if not hasattr(self, 'calculated_result'):
                return

        # Create line item from form
        line_item = QuoteLineItem(
            id=self.line_item.id if self.line_item else None,
            line_number=self.line_item.line_number if self.line_item else 1,
            pivot_amount=float(self.pivot_amount.text()),
            equipment_age_years=int(self.equipment_age.text()),
            pivot_deductible_code=self.pivot_deductible.currentData(),
            ancillary_deductible_code=self.ancillary_deductible.currentData(),
            ancillary_amount=float(self.ancillary_amount.text() or 0),
            submersible_pump_amount=float(self.submersible_pump_amount.text() or 0),
            is_towable=1 if self.is_towable.isChecked() else 0,
            is_corner_or_long=1 if self.is_corner_or_long.isChecked() else 0,
            has_me_endorsement=1 if self.has_me_endorsement.isChecked() else 0,
            # Calculated fields
            pivot_rate=self.calculated_result.get('pivot_rate'),
            ancillary_rate=self.calculated_result.get('ancillary_rate'),
            pivot_premium=self.calculated_result.get('pivot_premium'),
            ancillary_premium=self.calculated_result.get('ancillary_premium'),
            submersible_charge=self.calculated_result.get('submersible_charge'),
            line_total_premium=self.calculated_result.get('total_premium'),
            alt1_deductible=self.calculated_result.get('alt1_deductible'),
            alt1_rate=self.calculated_result.get('alt1_rate'),
            alt1_premium=self.calculated_result.get('alt1_premium'),
            alt2_deductible=self.calculated_result.get('alt2_deductible'),
            alt2_rate=self.calculated_result.get('alt2_rate'),
            alt2_premium=self.calculated_result.get('alt2_premium')
        )

        self.result_line_item = line_item
        self.accept()

    def get_line_item(self) -> Optional[QuoteLineItem]:
        """Get the created/edited line item."""
        return getattr(self, 'result_line_item', None)
