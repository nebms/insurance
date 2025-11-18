"""
Rate editor dialog for detailed rate editing with validation.
Provides a focused interface for editing individual rates.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QDoubleValidator
from typing import Optional
from datetime import date, datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import get_db
from database.auth_manager import User
from database.audit_manager import AuditManager


class RateEditorDialog(QDialog):
    """Dialog for editing individual rate values."""

    def __init__(self, table_name: str, state_code: str, column_name: str,
                 current_value: Optional[float], user: User, parent=None):
        """
        Initialize rate editor dialog.

        Args:
            table_name: Database table name
            state_code: State code
            column_name: Column name being edited
            current_value: Current rate value
            user: Authenticated user
            parent: Parent widget
        """
        super().__init__(parent)
        self.table_name = table_name
        self.state_code = state_code
        self.column_name = column_name
        self.current_value = current_value
        self.user = user

        self.db = get_db()
        self.audit_manager = AuditManager()

        self.setWindowTitle(f"Edit Rate - {self._format_table_name(table_name)}")
        self.setModal(True)
        self.setFixedSize(450, 400)

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Edit Rate - {self._format_table_name(self.table_name)}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Separator
        layout.addSpacing(10)

        # Form layout
        form_layout = QGridLayout()
        form_layout.setColumnStretch(1, 1)
        row = 0

        # State
        state_label = QLabel("State:")
        state_label_font = QFont()
        state_label_font.setBold(True)
        state_label.setFont(state_label_font)
        state_value = QLabel(self.state_code)

        form_layout.addWidget(state_label, row, 0)
        form_layout.addWidget(state_value, row, 1)
        row += 1

        # Column
        column_label = QLabel("Rate Column:")
        column_label_font = QFont()
        column_label_font.setBold(True)
        column_label.setFont(column_label_font)
        column_value = QLabel(self._format_column_name(self.column_name))

        form_layout.addWidget(column_label, row, 0)
        form_layout.addWidget(column_value, row, 1)
        row += 1

        # Current rate
        current_label = QLabel("Current Rate:")
        current_label_font = QFont()
        current_label_font.setBold(True)
        current_label.setFont(current_label_font)
        current_display = f"{self.current_value:.2f}%" if self.current_value is not None else "Not Set"
        current_value_label = QLabel(current_display)

        form_layout.addWidget(current_label, row, 0)
        form_layout.addWidget(current_value_label, row, 1)
        row += 1

        # New rate input
        new_rate_label = QLabel("New Rate (%):")
        new_rate_label_font = QFont()
        new_rate_label_font.setBold(True)
        new_rate_label.setFont(new_rate_label_font)

        self.new_rate_input = QLineEdit()
        if self.current_value is not None:
            self.new_rate_input.setText(f"{self.current_value:.2f}")
        self.new_rate_input.setPlaceholderText("Enter rate (0-100)")

        # Add validator for decimal input
        validator = QDoubleValidator(0.0, 100.0, 2)
        self.new_rate_input.setValidator(validator)

        rate_layout = QHBoxLayout()
        rate_layout.addWidget(self.new_rate_input)
        rate_layout.addWidget(QLabel("%"))

        form_layout.addWidget(new_rate_label, row, 0)
        form_layout.addLayout(rate_layout, row, 1)
        row += 1

        # Effective date
        effective_label = QLabel("Effective Date:")
        effective_label_font = QFont()
        effective_label_font.setBold(True)
        effective_label.setFont(effective_label_font)

        self.effective_date = QDateEdit()
        self.effective_date.setDate(QDate.currentDate())
        self.effective_date.setCalendarPopup(True)
        self.effective_date.setDisplayFormat("yyyy-MM-dd")

        form_layout.addWidget(effective_label, row, 0)
        form_layout.addWidget(self.effective_date, row, 1)
        row += 1

        layout.addLayout(form_layout)
        layout.addSpacing(10)

        # Notes
        notes_label = QLabel("Notes:")
        notes_label_font = QFont()
        notes_label_font.setBold(True)
        notes_label.setFont(notes_label_font)
        layout.addWidget(notes_label)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional: Enter reason for rate change...")
        self.notes_input.setMaximumHeight(100)
        layout.addWidget(self.notes_input)

        # Validation message
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red;")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Change")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_change)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Focus on rate input
        self.new_rate_input.setFocus()
        self.new_rate_input.selectAll()

    def _format_table_name(self, table_name: str) -> str:
        """Format table name for display."""
        name_map = {
            'pivot_rates_under_20': 'Pivot Rates Under 20',
            'pivot_rates_20_to_34': 'Pivot Rates 20-34',
            'pivot_rates_35_plus': 'Pivot Rates 35+',
            'ancillary_rates': 'Ancillary Rates'
        }
        return name_map.get(table_name, table_name)

    def _format_column_name(self, column_name: str) -> str:
        """Format column name for display."""
        return column_name.replace('_', ' ').title()

    def _save_change(self):
        """Validate and save rate change."""
        # Clear previous validation message
        self.validation_label.setText("")

        # Get new rate value
        new_rate_str = self.new_rate_input.text().strip()

        if not new_rate_str:
            self.validation_label.setText("Please enter a rate value")
            self.new_rate_input.setFocus()
            return

        try:
            new_rate = float(new_rate_str)

            # Validate range
            if new_rate < 0 or new_rate > 100:
                self.validation_label.setText("Rate must be between 0 and 100%")
                self.new_rate_input.setFocus()
                return

            # Check if value actually changed
            if self.current_value is not None and abs(new_rate - self.current_value) < 0.01:
                reply = QMessageBox.question(
                    self,
                    "No Change",
                    "The new rate is the same as the current rate.\n\n"
                    "Do you want to proceed anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # Get notes
            notes = self.notes_input.toPlainText().strip()
            if not notes:
                notes = f"Rate changed from {self.current_value:.2f}% to {new_rate:.2f}%"

            # Confirm change
            change_summary = f"State: {self.state_code}\n"
            change_summary += f"Column: {self._format_column_name(self.column_name)}\n"
            change_summary += f"Current: {self.current_value:.2f}%" if self.current_value is not None else "Not Set"
            change_summary += f"\nNew: {new_rate:.2f}%\n"
            change_summary += f"Effective: {self.effective_date.date().toString('yyyy-MM-dd')}\n\n"
            change_summary += "Proceed with this change?"

            reply = QMessageBox.question(
                self,
                "Confirm Rate Change",
                change_summary,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Update database
                query = f"""
                    UPDATE {self.table_name}
                    SET {self.column_name} = ?
                    WHERE state_code = ?
                """
                self.db.execute_update(query, (new_rate, self.state_code))

                # Log to audit trail
                self.audit_manager.log_rate_change(
                    user_id=self.user.id,
                    user_name=self.user.full_name,
                    table_name=self.table_name,
                    state_code=self.state_code,
                    column_name=self.column_name,
                    old_value=self.current_value,
                    new_value=new_rate,
                    change_type='update',
                    notes=notes
                )

                QMessageBox.information(
                    self,
                    "Rate Updated",
                    f"Rate successfully updated for {self.state_code}.\n\n"
                    f"The change has been logged to the audit trail."
                )

                self.accept()

        except ValueError:
            self.validation_label.setText("Invalid rate value. Please enter a valid number.")
            self.new_rate_input.setFocus()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from database.auth_manager import User

    app = QApplication(sys.argv)

    # Test user
    test_user = User(
        id=1,
        username="admin",
        full_name="Administrator",
        email=None,
        role="admin",
        is_active=True,
        created_at="2025-01-01",
        last_login=None
    )

    dialog = RateEditorDialog(
        table_name='pivot_rates_under_20',
        state_code='NE',
        column_name='standard_500_no_me',
        current_value=2.50,
        user=test_user
    )

    if dialog.exec():
        print("✓ Rate updated")
    else:
        print("✗ Rate update cancelled")
