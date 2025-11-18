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

        # Customer selection/creation
        layout.addWidget(QLabel("Customer:"), 0, 0)

        # Customer combo box
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setPlaceholderText("Select existing or type new customer name")
        self.customer_combo.currentTextChanged.connect(self._on_customer_changed)
        layout.addWidget(self.customer_combo, 0, 1)

        # New customer button
        new_customer_btn = QPushButton("+ New")
        new_customer_btn.clicked.connect(self._create_new_customer)
        layout.addWidget(new_customer_btn, 0, 2)

        # Customer Name (for new customers or display)
        layout.addWidget(QLabel("Customer Name *:"), 1, 0)
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Enter customer name")
        layout.addWidget(self.customer_name, 1, 1, 1, 2)

        # Agent Name
        layout.addWidget(QLabel("Agent Name:"), 2, 0)
        self.agent_name = QLineEdit()
        self.agent_name.setPlaceholderText("Your name")
        layout.addWidget(self.agent_name, 2, 1, 1, 2)

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

        # Also load customers
        self._load_customers()

    def _load_customers(self):
        """Load customers into dropdown."""
        customers = self.customer_repo.get_all()
        self.customer_combo.clear()
        self.customer_combo.addItem("-- New Customer --", None)

        for customer in customers:
            self.customer_combo.addItem(customer.name, customer.id)

    def _on_customer_changed(self, text):
        """Handle customer selection change."""
        if text and text != "-- New Customer --":
            self.customer_name.setText(text)

    def _create_new_customer(self):
        """Open dialog to create new customer."""
        from .customer_dialog import CustomerDialog

        dialog = CustomerDialog(self)
        if dialog.exec():
            customer = dialog.get_customer()
            if customer:
                # Save customer
                customer_id = self.customer_repo.create(customer)
                # Reload customer list
                self._load_customers()
                # Select the new customer
                self.customer_combo.setCurrentText(customer.name)
                self.customer_name.setText(customer.name)

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
        # Customer name validation
        if not self.customer_name.text().strip():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Customer name is required.\n\nPlease enter a customer name or select an existing customer."
            )
            self.customer_name.setFocus()
            return False

        # State validation
        if not self.state_combo.currentData():
            QMessageBox.warning(
                self,
                "Validation Error",
                "State is required.\n\nPlease select a state from the dropdown."
            )
            self.state_combo.setFocus()
            return False

        # Pivot amount validation
        if self.pivot_amount.value() <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Pivot amount must be greater than $0.\n\nPlease enter the insured value of the pivot equipment."
            )
            self.pivot_amount.setFocus()
            return False

        # Equipment age validation
        if self.age_spin.value() < 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Equipment age cannot be negative.\n\nPlease enter a valid age (0 for new equipment)."
            )
            self.age_spin.setFocus()
            return False

        # Ancillary amount validation (if entered, must be positive)
        if self.ancillary_amount.value() < 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Ancillary amount cannot be negative.\n\nLeave at $0 if no ancillary equipment."
            )
            self.ancillary_amount.setFocus()
            return False

        # Submersible pump validation (if entered, must be positive)
        if self.submersible_amount.value() < 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Submersible pump amount cannot be negative.\n\nLeave at $0 if no submersible pump."
            )
            self.submersible_amount.setFocus()
            return False

        # Warning for very high amounts
        total_coverage = (self.pivot_amount.value() +
                         self.ancillary_amount.value() +
                         self.submersible_amount.value())

        if total_coverage > 1000000:  # $1M+
            reply = QMessageBox.question(
                self,
                "Confirm High Value",
                f"The total coverage amount is ${total_coverage:,.2f}.\n\n"
                "This is unusually high. Is this correct?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
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
                state_name = self.state_combo.currentText()
                age = self.age_spin.value()
                equipment_type = "Towable" if self.type_towable.isChecked() else "Standard"

                QMessageBox.warning(
                    self,
                    "Rate Not Found",
                    f"<b>No insurance rate found for this configuration:</b><br><br>"
                    f"<b>State:</b> {state_name}<br>"
                    f"<b>Equipment Type:</b> {equipment_type}<br>"
                    f"<b>Equipment Age:</b> {age} years<br><br>"
                    f"<b>Possible reasons:</b><br>"
                    f"• Rate tables have not been loaded for this state<br>"
                    f"• This state/configuration is not supported<br>"
                    f"• Sample rates are incomplete (test data only)<br><br>"
                    f"<b>Action needed:</b><br>"
                    f"Use <i>Tools → Load Rate Tables</i> to import actual rates,<br>"
                    f"or contact your administrator for rate table support."
                )
                return

            # Show results dialog
            self._show_results(params, result)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()

            QMessageBox.critical(
                self,
                "Calculation Error",
                f"<b>An error occurred while calculating the quote:</b><br><br>"
                f"{str(e)}<br><br>"
                f"<b>Please check:</b><br>"
                f"• All form fields are filled correctly<br>"
                f"• Database is accessible<br>"
                f"• Rate tables are loaded<br><br>"
                f"<i>If this problem persists, contact technical support.</i>"
            )
            # Log the full error
            print("CALCULATION ERROR:")
            print(error_detail)

    def _show_results(self, params, result):
        """Show calculation results in dialog."""
        from .quote_results import QuoteResultsDialog

        # Pass customer and agent info
        customer_name = self.customer_name.text().strip()
        agent_name = self.agent_name.text().strip()

        dialog = QuoteResultsDialog(self, params, result, customer_name, agent_name)
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
