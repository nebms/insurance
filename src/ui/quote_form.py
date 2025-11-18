"""
Quote entry form widget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QCheckBox, QRadioButton,
    QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import Quote, QuoteRepository
from models.customer import CustomerRepository
from calculations.premium_calc import PremiumCalculator
from database.db_manager import get_db


class QuoteForm(QWidget):
    """Quote entry form."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.customer_repo = CustomerRepository()
        self.quote_repo = QuoteRepository()
        self.calculator = PremiumCalculator()

        self._init_ui()
        self._load_states()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title = QLabel("Create New Insurance Quote")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Customer Information
        layout.addWidget(self._create_customer_group())

        # Equipment Details
        layout.addWidget(self._create_equipment_group())

        # Coverage Options
        layout.addWidget(self._create_coverage_group())

        # Buttons
        layout.addWidget(self._create_button_group())

        # Add stretch to push everything to top
        layout.addStretch()

        self.setLayout(layout)

    def _create_customer_group(self):
        """Create customer information group."""
        group = QGroupBox("Customer Information")
        layout = QGridLayout()

        # Customer Name
        layout.addWidget(QLabel("Customer Name *:"), 0, 0)
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Enter customer name")
        layout.addWidget(self.customer_name, 0, 1, 1, 2)

        # Agent Name
        layout.addWidget(QLabel("Agent Name:"), 1, 0)
        self.agent_name = QLineEdit()
        self.agent_name.setPlaceholderText("Your name")
        layout.addWidget(self.agent_name, 1, 1, 1, 2)

        group.setLayout(layout)
        return group

    def _create_equipment_group(self):
        """Create equipment details group."""
        group = QGroupBox("Equipment Details")
        layout = QGridLayout()

        # State
        layout.addWidget(QLabel("State *:"), 0, 0)
        self.state_combo = QComboBox()
        layout.addWidget(self.state_combo, 0, 1)

        # Equipment Age
        layout.addWidget(QLabel("Equipment Age (years) *:"), 1, 0)
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 99)
        self.age_spin.setValue(0)
        self.age_spin.setSuffix(" years")
        layout.addWidget(self.age_spin, 1, 1)

        # Pivot Amount
        layout.addWidget(QLabel("Pivot Amount Insured *:"), 2, 0)
        self.pivot_amount = QDoubleSpinBox()
        self.pivot_amount.setRange(0, 10000000)
        self.pivot_amount.setValue(100000)
        self.pivot_amount.setPrefix("$ ")
        self.pivot_amount.setGroupSeparatorShown(True)
        layout.addWidget(self.pivot_amount, 2, 1)

        # Ancillary Amount
        layout.addWidget(QLabel("Ancillary Amount:"), 3, 0)
        self.ancillary_amount = QDoubleSpinBox()
        self.ancillary_amount.setRange(0, 10000000)
        self.ancillary_amount.setValue(0)
        self.ancillary_amount.setPrefix("$ ")
        self.ancillary_amount.setGroupSeparatorShown(True)
        layout.addWidget(self.ancillary_amount, 3, 1)

        # Submersible Pump Amount
        layout.addWidget(QLabel("Submersible Pump Amount:"), 4, 0)
        self.submersible_amount = QDoubleSpinBox()
        self.submersible_amount.setRange(0, 10000000)
        self.submersible_amount.setValue(0)
        self.submersible_amount.setPrefix("$ ")
        self.submersible_amount.setGroupSeparatorShown(True)
        layout.addWidget(self.submersible_amount, 4, 1)

        # Equipment Type
        layout.addWidget(QLabel("Equipment Type *:"), 5, 0)
        self.type_group = QButtonGroup()
        self.type_standard = QRadioButton("Standard")
        self.type_towable = QRadioButton("Towable/Corner/Long")
        self.type_standard.setChecked(True)
        self.type_group.addButton(self.type_standard)
        self.type_group.addButton(self.type_towable)

        type_layout = QHBoxLayout()
        type_layout.addWidget(self.type_standard)
        type_layout.addWidget(self.type_towable)
        layout.addLayout(type_layout, 5, 1)

        # M&E Endorsement
        self.me_checkbox = QCheckBox("Mechanical & Electrical (M&E) Endorsement")
        self.me_checkbox.setChecked(True)
        layout.addWidget(self.me_checkbox, 6, 0, 1, 2)

        # Corner/Long (show only if age > 34)
        self.corner_checkbox = QCheckBox("Corner/Long/Underslung System (Age 35+)")
        self.corner_checkbox.setEnabled(False)
        layout.addWidget(self.corner_checkbox, 7, 0, 1, 2)

        # Connect age change to enable corner checkbox
        self.age_spin.valueChanged.connect(self._on_age_changed)

        group.setLayout(layout)
        return group

    def _create_coverage_group(self):
        """Create coverage options group."""
        group = QGroupBox("Coverage Options")
        layout = QGridLayout()

        # Pivot Deductible
        layout.addWidget(QLabel("Pivot Deductible *:"), 0, 0)
        self.pivot_deductible = QComboBox()
        self.pivot_deductible.addItems([
            "$500", "$1,000", "$2,500", "$5,000"
        ])
        self.pivot_deductible.setCurrentIndex(2)  # Default $2,500
        layout.addWidget(self.pivot_deductible, 0, 1)

        # Ancillary Deductible
        layout.addWidget(QLabel("Ancillary Deductible *:"), 1, 0)
        self.ancillary_deductible = QComboBox()
        self.ancillary_deductible.addItems([
            "$500", "$1,000", "$2,500", "$5,000"
        ])
        self.ancillary_deductible.setCurrentIndex(1)  # Default $1,000
        layout.addWidget(self.ancillary_deductible, 1, 1)

        # Term
        layout.addWidget(QLabel("Term (months) *:"), 2, 0)
        self.term_combo = QComboBox()
        self.term_combo.addItems([
            "12", "24", "36", "48", "60", "72", "84", "96"
        ])
        layout.addWidget(self.term_combo, 2, 1)

        group.setLayout(layout)
        return group

    def _create_button_group(self):
        """Create action buttons."""
        widget = QWidget()
        layout = QHBoxLayout()

        # Calculate button
        self.calc_button = QPushButton("Calculate Premium")
        self.calc_button.setMinimumHeight(40)
        self.calc_button.clicked.connect(self._calculate_quote)

        # Reset button
        self.reset_button = QPushButton("Reset Form")
        self.reset_button.clicked.connect(self.reset_form)

        layout.addStretch()
        layout.addWidget(self.reset_button)
        layout.addWidget(self.calc_button)

        widget.setLayout(layout)
        return widget

    def _load_states(self):
        """Load states into dropdown."""
        db = get_db()
        states = db.execute_query("SELECT code, name FROM states ORDER BY name")

        for state in states:
            self.state_combo.addItem(f"{state['name']} ({state['code']})", state['code'])

    def _on_age_changed(self, age):
        """Enable corner checkbox if age > 34."""
        self.corner_checkbox.setEnabled(age > 34)
        if age <= 34:
            self.corner_checkbox.setChecked(False)

    def _deductible_to_code(self, deductible_text):
        """Convert deductible dropdown text to code."""
        mapping = {
            "$500": 1,
            "$1,000": 2,
            "$2,500": 3,
            "$5,000": 4
        }
        return mapping.get(deductible_text, 3)

    def _validate_form(self):
        """Validate form inputs."""
        if not self.customer_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Customer name is required.")
            return False

        if self.state_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Validation Error", "Please select a state.")
            return False

        if self.pivot_amount.value() == 0:
            QMessageBox.warning(self, "Validation Error", "Pivot amount must be greater than 0.")
            return False

        return True

    def _calculate_quote(self):
        """Calculate quote and show results."""
        if not self._validate_form():
            return

        try:
            # Gather inputs
            params = {
                'pivot_amount': self.pivot_amount.value(),
                'ancillary_amount': self.ancillary_amount.value(),
                'submersible_pump_amount': self.submersible_amount.value(),
                'equipment_age_years': self.age_spin.value(),
                'is_towable': self.type_towable.isChecked(),
                'is_corner_or_long': self.corner_checkbox.isChecked(),
                'has_me_endorsement': self.me_checkbox.isChecked(),
                'pivot_deductible_code': self._deductible_to_code(self.pivot_deductible.currentText()),
                'ancillary_deductible_code': self._deductible_to_code(self.ancillary_deductible.currentText()),
                'term_months': int(self.term_combo.currentText()),
                'state_code': self.state_combo.currentData()
            }

            # Calculate
            result = self.calculator.calculate_complete_quote(**params)

            # Check if rates were found
            if result['pivot_rate'] is None:
                QMessageBox.warning(
                    self,
                    "Rate Not Found",
                    f"No rate found for {self.state_combo.currentText()} with current configuration.\n\n"
                    "Please verify rate tables are loaded."
                )
                return

            # Show results dialog
            self._show_results(params, result)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Calculation Error",
                f"Error calculating quote:\n{str(e)}"
            )

    def _show_results(self, params, result):
        """Show calculation results in dialog."""
        from .quote_results import QuoteResultsDialog

        dialog = QuoteResultsDialog(self, params, result)
        if dialog.exec():
            # User saved the quote
            self.parent.update_status("Quote saved successfully", 3000)
            self.reset_form()

    def reset_form(self):
        """Reset form to defaults."""
        self.customer_name.clear()
        self.agent_name.clear()
        self.state_combo.setCurrentIndex(-1)
        self.age_spin.setValue(0)
        self.pivot_amount.setValue(100000)
        self.ancillary_amount.setValue(0)
        self.submersible_amount.setValue(0)
        self.type_standard.setChecked(True)
        self.me_checkbox.setChecked(True)
        self.corner_checkbox.setChecked(False)
        self.pivot_deductible.setCurrentIndex(2)
        self.ancillary_deductible.setCurrentIndex(1)
        self.term_combo.setCurrentIndex(0)
