"""
Quote entry form widget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QCheckBox, QRadioButton,
    QButtonGroup, QMessageBox, QCompleter
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QFont, QStandardItemModel, QStandardItem

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import Quote, QuoteRepository
from models.quote_line_item import QuoteLineItem
from models.customer import CustomerRepository
from calculations.premium_calc import PremiumCalculator
from database.db_manager import get_db
from ui.line_item_widget import LineItemWidget
from ui.line_item_dialog import LineItemDialog
from ui.template_dialogs import SaveTemplateDialog, TemplateManagerDialog


class QuoteForm(QWidget):
    """Quote entry form."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.customer_repo = CustomerRepository()
        self.quote_repo = QuoteRepository()
        self.calculator = PremiumCalculator()

        # Quote mode: 'single' or 'multiple'
        self.quote_mode = 'single'

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

        # Mode Toggle
        layout.addWidget(self._create_mode_toggle())

        # Customer Information
        layout.addWidget(self._create_customer_group())

        # Equipment Mode Selection: Single or Multiple
        # Single Equipment (traditional form)
        self.single_equipment_group = self._create_equipment_group()
        layout.addWidget(self.single_equipment_group)

        # Multiple Equipment (line items)
        self.line_item_widget = LineItemWidget(self)
        self.line_item_widget.setVisible(False)
        layout.addWidget(self.line_item_widget)

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
        self.customer_combo.setToolTip(
            "Select an existing customer or search by name, email, or phone.\n\n"
            "Fuzzy search enabled:\n"
            "• Type any part of the name\n"
            "• Type email address\n"
            "• Type phone number\n\n"
            "Click '+ New' to create a new customer."
        )
        self.customer_combo.currentTextChanged.connect(self._on_customer_changed)
        layout.addWidget(self.customer_combo, 0, 1)

        # New customer button
        new_customer_btn = QPushButton("+ New")
        new_customer_btn.setToolTip("Create a new customer record with full contact details")
        new_customer_btn.clicked.connect(self._create_new_customer)
        layout.addWidget(new_customer_btn, 0, 2)

        # Customer Name (for new customers or display)
        layout.addWidget(QLabel("Customer Name *:"), 1, 0)
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Enter customer name")
        self.customer_name.setToolTip("Enter the customer's full name (2-200 characters)")
        self.customer_name.textChanged.connect(self._validate_customer_name)
        layout.addWidget(self.customer_name, 1, 1)

        # Validation indicator for customer name
        self.customer_name_status = QLabel()
        self.customer_name_status.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.customer_name_status, 1, 2)

        # Agent Name
        layout.addWidget(QLabel("Agent Name:"), 2, 0)
        self.agent_name = QLineEdit()
        self.agent_name.setPlaceholderText("Your name")
        self.agent_name.textChanged.connect(self._validate_agent_name)
        layout.addWidget(self.agent_name, 2, 1)

        # Validation indicator for agent name
        self.agent_name_status = QLabel()
        self.agent_name_status.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.agent_name_status, 2, 2)

        group.setLayout(layout)
        return group

    def _create_equipment_group(self):
        """Create equipment details group."""
        group = QGroupBox("Equipment Details")
        layout = QGridLayout()

        # State
        layout.addWidget(QLabel("State *:"), 0, 0)
        self.state_combo = QComboBox()
        self.state_combo.setToolTip("Select the state where the equipment is located.\nRates vary by state.")
        layout.addWidget(self.state_combo, 0, 1)

        # Equipment Age
        layout.addWidget(QLabel("Equipment Age (years) *:"), 1, 0)
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 99)
        self.age_spin.setValue(0)
        self.age_spin.setSuffix(" years")
        self.age_spin.setToolTip(
            "Enter the age of the pivot equipment in years.\n\n"
            "Age determines the rate category:\n"
            "• Under 20 years: Standard rates\n"
            "• 20-34 years: Higher rates\n"
            "• 35+ years: Special rates (Corner/Long option available)"
        )
        layout.addWidget(self.age_spin, 1, 1)

        # Pivot Amount
        layout.addWidget(QLabel("Pivot Amount Insured *:"), 2, 0)
        self.pivot_amount = QDoubleSpinBox()
        self.pivot_amount.setRange(0, 10000000)
        self.pivot_amount.setValue(100000)
        self.pivot_amount.setPrefix("$ ")
        self.pivot_amount.setGroupSeparatorShown(True)
        self.pivot_amount.setToolTip(
            "Enter the insured value of the center pivot equipment.\n\n"
            "This should be the replacement cost value (RCV):\n"
            "• Purchase price for new equipment\n"
            "• Depreciated value for used equipment\n"
            "• Typical range: $50,000 - $500,000"
        )
        layout.addWidget(self.pivot_amount, 2, 1)

        # Ancillary Amount
        layout.addWidget(QLabel("Ancillary Amount:"), 3, 0)
        self.ancillary_amount = QDoubleSpinBox()
        self.ancillary_amount.setRange(0, 10000000)
        self.ancillary_amount.setValue(0)
        self.ancillary_amount.setPrefix("$ ")
        self.ancillary_amount.setGroupSeparatorShown(True)
        self.ancillary_amount.setToolTip(
            "Enter the value of ancillary equipment (optional).\n\n"
            "Ancillary equipment includes:\n"
            "• Booster pumps\n"
            "• Chemigation equipment\n"
            "• Control panels\n"
            "• Variable frequency drives\n"
            "• GPS guidance systems"
        )
        layout.addWidget(self.ancillary_amount, 3, 1)

        # Submersible Pump Amount
        layout.addWidget(QLabel("Submersible Pump Amount:"), 4, 0)
        self.submersible_amount = QDoubleSpinBox()
        self.submersible_amount.setRange(0, 10000000)
        self.submersible_amount.setValue(0)
        self.submersible_amount.setPrefix("$ ")
        self.submersible_amount.setGroupSeparatorShown(True)
        self.submersible_amount.setToolTip(
            "Enter the value of submersible pumps (optional).\n\n"
            "A flat charge of $75 is added per $10,000 of coverage.\n"
            "Example: $50,000 pump = $375 additional premium"
        )
        layout.addWidget(self.submersible_amount, 4, 1)

        # Equipment Type
        layout.addWidget(QLabel("Equipment Type *:"), 5, 0)
        self.type_group = QButtonGroup()
        self.type_standard = QRadioButton("Standard")
        self.type_standard.setToolTip(
            "Standard center pivot systems.\n"
            "Most common equipment type with standard rates."
        )
        self.type_towable = QRadioButton("Towable/Corner/Long")
        self.type_towable.setToolTip(
            "Towable pivot systems or corner/long configurations.\n"
            "Different rate structure than standard pivots."
        )
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
        self.me_checkbox.setToolTip(
            "Mechanical & Electrical Endorsement (recommended).\n\n"
            "Provides coverage for mechanical and electrical breakdown:\n"
            "• Motor failures\n"
            "• Electrical component failures\n"
            "• Transmission problems\n\n"
            "Adds approximately 10-20% to premium.\n"
            "Highly recommended for equipment protection."
        )
        layout.addWidget(self.me_checkbox, 6, 0, 1, 2)

        # Corner/Long (show only if age > 34)
        self.corner_checkbox = QCheckBox("Corner/Long/Underslung System (Age 35+)")
        self.corner_checkbox.setEnabled(False)
        self.corner_checkbox.setToolTip(
            "Corner, Long, or Underslung pivot systems.\n\n"
            "Only available for equipment 35+ years old.\n"
            "Different rate structure for specialized systems."
        )
        layout.addWidget(self.corner_checkbox, 7, 0, 1, 2)

        # Connect age change to enable corner checkbox
        self.age_spin.valueChanged.connect(self._on_age_changed)

        group.setLayout(layout)
        return group

    def _create_mode_toggle(self):
        """Create quote mode toggle widget."""
        group = QGroupBox("Quote Mode")
        layout = QHBoxLayout()

        self.mode_group = QButtonGroup()
        self.mode_single = QRadioButton("Single Equipment")
        self.mode_multiple = QRadioButton("Multiple Equipment")
        self.mode_single.setChecked(True)

        self.mode_group.addButton(self.mode_single)
        self.mode_group.addButton(self.mode_multiple)

        # Connect to mode change handler
        self.mode_single.toggled.connect(self._on_mode_changed)

        layout.addWidget(self.mode_single)
        layout.addWidget(self.mode_multiple)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def _on_mode_changed(self, checked):
        """Handle quote mode change."""
        if checked:  # mode_single was checked
            self.quote_mode = 'single'
            self.single_equipment_group.setVisible(True)
            self.line_item_widget.setVisible(False)
        else:
            self.quote_mode = 'multiple'
            self.single_equipment_group.setVisible(False)
            self.line_item_widget.setVisible(True)

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
        self.pivot_deductible.setToolTip(
            "Select the deductible for pivot equipment coverage.\n\n"
            "Higher deductible = lower premium\n"
            "Lower deductible = higher premium\n\n"
            "Common choices:\n"
            "• $2,500 (recommended for most customers)\n"
            "• $5,000 (for lower premiums)\n"
            "• $1,000 (for maximum protection)"
        )
        layout.addWidget(self.pivot_deductible, 0, 1)

        # Ancillary Deductible
        layout.addWidget(QLabel("Ancillary Deductible *:"), 1, 0)
        self.ancillary_deductible = QComboBox()
        self.ancillary_deductible.addItems([
            "$500", "$1,000", "$2,500", "$5,000"
        ])
        self.ancillary_deductible.setCurrentIndex(1)  # Default $1,000
        self.ancillary_deductible.setToolTip(
            "Select the deductible for ancillary equipment.\n\n"
            "Typically lower than pivot deductible.\n"
            "Default: $1,000"
        )
        layout.addWidget(self.ancillary_deductible, 1, 1)

        # Term
        layout.addWidget(QLabel("Term (months) *:"), 2, 0)
        self.term_combo = QComboBox()
        self.term_combo.addItems([
            "12", "24", "36", "48", "60", "72", "84", "96"
        ])
        self.term_combo.setToolTip(
            "Select the policy term length in months.\n\n"
            "Standard term: 12 months (annual policy)\n"
            "Longer terms available for multi-year coverage.\n\n"
            "Note: Rates are based on 12-month term.\n"
            "Multi-year terms will be prorated accordingly."
        )
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

        # Template buttons
        self.load_template_button = QPushButton("Load Template")
        self.load_template_button.clicked.connect(self._load_template)

        self.save_template_button = QPushButton("Save as Template")
        self.save_template_button.clicked.connect(self._save_as_template)

        # Reset button
        self.reset_button = QPushButton("Reset Form")
        self.reset_button.clicked.connect(self.reset_form)

        layout.addWidget(self.load_template_button)
        layout.addWidget(self.save_template_button)
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
        """Load customers into dropdown with enhanced search."""
        customers = self.customer_repo.get_all()

        self.customer_combo.clear()
        self.customer_combo.addItem("-- New Customer --", None)

        # Store customer objects for lookup
        self.customer_map = {}

        # Add customers with enhanced display (name + email/phone)
        for customer in customers:
            # Create display text with additional info
            display_text = customer.name

            # Add email or phone if available
            extra_info = []
            if customer.email:
                extra_info.append(customer.email)
            elif customer.phone:
                extra_info.append(customer.phone)

            if extra_info:
                display_text += f" ({extra_info[0]})"

            self.customer_combo.addItem(display_text, customer.id)
            self.customer_map[customer.id] = customer

        # Set up fuzzy autocomplete
        completer = QCompleter(self.customer_combo)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)  # Fuzzy matching
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.customer_combo.setCompleter(completer)

    def _on_customer_changed(self, text):
        """Handle customer selection change."""
        if text and text != "-- New Customer --":
            # Extract customer name (before parentheses if they exist)
            customer_name = text.split(" (")[0] if " (" in text else text
            self.customer_name.setText(customer_name)

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

    def _open_line_item_dialog(self, line_item=None, index=None):
        """Open dialog to add or edit a line item."""
        # Validate state and term are selected
        if not self.state_combo.currentData():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select a state before adding equipment."
            )
            self.state_combo.setFocus()
            return

        state_code = self.state_combo.currentData()
        term_months = int(self.term_combo.currentText())

        # Open dialog
        dialog = LineItemDialog(state_code, term_months, line_item, self)
        if dialog.exec():
            result_item = dialog.get_line_item()
            if result_item:
                if index is not None:
                    # Edit mode
                    self.line_item_widget.update_item(index, result_item)
                else:
                    # Add mode
                    self.line_item_widget.add_line_item(result_item)

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

        # Mode-specific validation
        if self.quote_mode == 'multiple':
            # Multiple equipment mode - check line items exist
            if not self.line_item_widget.has_items():
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "No equipment items added.\n\nPlease add at least one equipment item using the '+ Add Equipment' button."
                )
                return False
            return True

        # Single equipment mode validation
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
            if self.quote_mode == 'multiple':
                # Multiple equipment mode - use line items
                line_items = self.line_item_widget.get_line_items()
                total_premium = self.line_item_widget.get_total_premium()

                # Create aggregated result for display
                result = {
                    'total_premium': total_premium,
                    'line_items': line_items,
                    'is_multi_pivot': True
                }

                # Use first line item for common params
                first_item = line_items[0]
                params = {
                    'state_code': self.state_combo.currentData(),
                    'term_months': int(self.term_combo.currentText()),
                    'pivot_amount': first_item.pivot_amount,  # For display only
                    'equipment_age_years': first_item.equipment_age_years,
                    'is_multi_pivot': True
                }

                # Show results dialog
                self._show_results(params, result, line_items)

            else:
                # Single equipment mode - traditional calculation
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

    def _show_results(self, params, result, line_items=None):
        """Show calculation results in dialog."""
        from .quote_results import QuoteResultsDialog

        # Pass customer and agent info
        customer_name = self.customer_name.text().strip()
        agent_name = self.agent_name.text().strip()

        dialog = QuoteResultsDialog(self, params, result, customer_name, agent_name, line_items)
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

        # Clear line items if in multiple mode
        if hasattr(self, 'line_item_widget'):
            self.line_item_widget.set_line_items([])

        # Reset to single mode
        if hasattr(self, 'mode_single'):
            self.mode_single.setChecked(True)

    def _save_as_template(self):
        """Save current quote configuration as a template."""
        # Only works in single mode
        if self.quote_mode == 'multiple':
            QMessageBox.information(
                self,
                "Single Mode Only",
                "Templates can only be saved in Single Equipment mode.\n\n"
                "Templates provide a quick way to populate common single equipment configurations."
            )
            return

        # Validate required fields
        if self.state_combo.currentIndex() < 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select a state before saving as template."
            )
            self.state_combo.setFocus()
            return

        if self.pivot_amount.value() <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a valid pivot amount before saving as template."
            )
            self.pivot_amount.setFocus()
            return

        # Collect current form data
        quote_data = {
            'state_code': self.state_combo.currentData(),
            'term_months': int(self.term_combo.currentText().split()[0]),
            'pivot_amount': self.pivot_amount.value(),
            'equipment_age_years': self.age_spin.value(),
            'pivot_deductible_code': self.pivot_deductible.currentData(),
            'ancillary_deductible_code': self.ancillary_deductible.currentData(),
            'ancillary_amount': self.ancillary_amount.value(),
            'submersible_pump_amount': self.submersible_amount.value(),
            'is_towable': 1 if self.type_towable.isChecked() else 0,
            'is_corner_or_long': 1 if self.corner_checkbox.isChecked() else 0,
            'has_me_endorsement': 1 if self.me_checkbox.isChecked() else 0
        }

        # Show save template dialog
        dialog = SaveTemplateDialog(quote_data, self)
        if dialog.exec():
            # Template was saved successfully
            pass

    def _load_template(self):
        """Load a template to populate the form."""
        # Only works in single mode
        if self.quote_mode == 'multiple':
            QMessageBox.information(
                self,
                "Single Mode Only",
                "Templates can only be loaded in Single Equipment mode.\n\n"
                "Switch to Single Equipment mode to use templates."
            )
            return

        # Get current state for filtering (if selected)
        state_code = self.state_combo.currentData() if self.state_combo.currentIndex() >= 0 else None

        # Show template manager dialog
        dialog = TemplateManagerDialog(state_code, self)
        if dialog.exec():
            template = dialog.get_selected_template()
            if template:
                self._populate_from_template(template)

    def _populate_from_template(self, template):
        """Populate form from template data."""
        # Set state
        for i in range(self.state_combo.count()):
            if self.state_combo.itemData(i) == template.state_code:
                self.state_combo.setCurrentIndex(i)
                break

        # Set term
        term_text = f"{template.term_months} months"
        for i in range(self.term_combo.count()):
            if self.term_combo.itemText(i) == term_text:
                self.term_combo.setCurrentIndex(i)
                break

        # Set equipment details
        self.pivot_amount.setValue(template.pivot_amount)
        self.age_spin.setValue(template.equipment_age_years)
        self.ancillary_amount.setValue(template.ancillary_amount)
        self.submersible_amount.setValue(template.submersible_pump_amount)

        # Set equipment type
        if template.is_towable:
            self.type_towable.setChecked(True)
        else:
            self.type_standard.setChecked(True)

        # Set checkboxes
        self.me_checkbox.setChecked(bool(template.has_me_endorsement))
        self.corner_checkbox.setChecked(bool(template.is_corner_or_long))

        # Set deductibles
        pivot_ded_index = self.pivot_deductible.findData(template.pivot_deductible_code)
        if pivot_ded_index >= 0:
            self.pivot_deductible.setCurrentIndex(pivot_ded_index)

        anc_ded_index = self.ancillary_deductible.findData(template.ancillary_deductible_code)
        if anc_ded_index >= 0:
            self.ancillary_deductible.setCurrentIndex(anc_ded_index)

        QMessageBox.information(
            self,
            "Template Loaded",
            f"Template '{template.template_name}' has been loaded.\n\n"
            f"Review the values and click Calculate Premium to generate a quote."
        )

    def _validate_customer_name(self, text):
        """Validate customer name in real-time."""
        text = text.strip()

        if not text:
            self.customer_name.setStyleSheet("")
            self.customer_name_status.setText("")
            return

        if len(text) < 2:
            self.customer_name.setStyleSheet("border: 1px solid #ef4444;")
            self.customer_name_status.setText("❌ Too short")
            self.customer_name_status.setStyleSheet("color: #ef4444; font-size: 10px;")
        elif len(text) > 200:
            self.customer_name.setStyleSheet("border: 1px solid #ef4444;")
            self.customer_name_status.setText("❌ Too long (max 200)")
            self.customer_name_status.setStyleSheet("color: #ef4444; font-size: 10px;")
        else:
            self.customer_name.setStyleSheet("border: 1px solid #10b981;")
            self.customer_name_status.setText(f"✓ Valid ({len(text)}/200)")
            self.customer_name_status.setStyleSheet("color: #10b981; font-size: 10px;")

    def _validate_agent_name(self, text):
        """Validate agent name in real-time."""
        text = text.strip()

        if not text:
            self.agent_name.setStyleSheet("")
            self.agent_name_status.setText("")
            return

        if len(text) < 2:
            self.agent_name.setStyleSheet("border: 1px solid #f59e0b;")
            self.agent_name_status.setText("⚠ Optional but too short")
            self.agent_name_status.setStyleSheet("color: #f59e0b; font-size: 10px;")
        elif len(text) > 100:
            self.agent_name.setStyleSheet("border: 1px solid #ef4444;")
            self.agent_name_status.setText("❌ Too long (max 100)")
            self.agent_name_status.setStyleSheet("color: #ef4444; font-size: 10px;")
        else:
            self.agent_name.setStyleSheet("border: 1px solid #10b981;")
            self.agent_name_status.setText(f"✓ Valid ({len(text)}/100)")
            self.agent_name_status.setStyleSheet("color: #10b981; font-size: 10px;")
