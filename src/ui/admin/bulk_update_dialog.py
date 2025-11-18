"""
Bulk rate update dialog for applying changes to multiple states.
Allows percentage adjustments with preview and confirmation.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QMessageBox, QRadioButton, QButtonGroup,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QDoubleSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from typing import List, Dict, Any, Optional
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import get_db
from database.auth_manager import User
from database.audit_manager import AuditManager


class BulkUpdateDialog(QDialog):
    """Dialog for bulk updating rates across multiple states."""

    def __init__(self, table_name: str, table_display_name: str,
                 selected_states: List[str], all_states: List[str],
                 user: User, parent=None):
        """
        Initialize bulk update dialog.

        Args:
            table_name: Database table name
            table_display_name: Display name for UI
            selected_states: List of selected state codes
            all_states: List of all available state codes
            user: Authenticated user
            parent: Parent widget
        """
        super().__init__(parent)
        self.table_name = table_name
        self.table_display_name = table_display_name
        self.selected_states = selected_states if selected_states else []
        self.all_states = all_states
        self.user = user

        self.db = get_db()
        self.audit_manager = AuditManager()

        self.preview_data: List[Dict[str, Any]] = []

        self.setWindowTitle(f"Bulk Rate Update - {table_display_name}")
        self.setModal(True)
        self.resize(700, 600)

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Bulk Rate Update - {self.table_display_name}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Scope selection
        scope_group = QGroupBox("Apply to:")
        scope_layout = QVBoxLayout()

        self.scope_group = QButtonGroup()

        self.selected_radio = QRadioButton(
            f"Selected states ({len(self.selected_states)} selected)"
        )
        self.all_radio = QRadioButton(
            f"All states ({len(self.all_states)} states)"
        )

        self.scope_group.addButton(self.selected_radio)
        self.scope_group.addButton(self.all_radio)

        # Default selection
        if self.selected_states:
            self.selected_radio.setChecked(True)
        else:
            self.all_radio.setChecked(True)
            self.selected_radio.setEnabled(False)

        scope_layout.addWidget(self.selected_radio)
        scope_layout.addWidget(self.all_radio)
        scope_group.setLayout(scope_layout)

        layout.addWidget(scope_group)

        # Adjustment type
        adj_group = QGroupBox("Adjustment Type:")
        adj_layout = QVBoxLayout()

        self.adj_type_group = QButtonGroup()

        self.percentage_radio = QRadioButton("Percentage increase/decrease")
        self.fixed_radio = QRadioButton("Set fixed rate")

        self.adj_type_group.addButton(self.percentage_radio)
        self.adj_type_group.addButton(self.fixed_radio)

        self.percentage_radio.setChecked(True)

        adj_layout.addWidget(self.percentage_radio)
        adj_layout.addWidget(self.fixed_radio)
        adj_group.setLayout(adj_layout)

        layout.addWidget(adj_group)

        # Adjustment value
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Adjustment Value:"))

        self.percentage_input = QDoubleSpinBox()
        self.percentage_input.setRange(-100.0, 100.0)
        self.percentage_input.setSingleStep(0.1)
        self.percentage_input.setDecimals(2)
        self.percentage_input.setSuffix(" %")
        self.percentage_input.setValue(0.0)

        self.fixed_input = QDoubleSpinBox()
        self.fixed_input.setRange(0.0, 100.0)
        self.fixed_input.setSingleStep(0.1)
        self.fixed_input.setDecimals(2)
        self.fixed_input.setSuffix(" %")
        self.fixed_input.setValue(0.0)
        self.fixed_input.setEnabled(False)

        value_layout.addWidget(self.percentage_input)
        value_layout.addWidget(self.fixed_input)
        value_layout.addStretch()

        # Connect radio buttons to enable/disable inputs
        self.percentage_radio.toggled.connect(
            lambda checked: self.percentage_input.setEnabled(checked)
        )
        self.fixed_radio.toggled.connect(
            lambda checked: self.fixed_input.setEnabled(checked)
        )

        layout.addLayout(value_layout)

        # Preview button
        preview_btn = QPushButton("Preview Changes")
        preview_btn.clicked.connect(self._preview_changes)
        layout.addWidget(preview_btn)

        # Preview table
        preview_label = QLabel("Preview Changes:")
        preview_label_font = QFont()
        preview_label_font.setBold(True)
        preview_label.setFont(preview_label_font)
        layout.addWidget(preview_label)

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels([
            "State", "Column", "Current", "New", "Change"
        ])
        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.preview_table.setMaximumHeight(200)

        layout.addWidget(self.preview_table)

        # Notes
        notes_label = QLabel("Notes (required for bulk updates):")
        notes_label_font = QFont()
        notes_label_font.setBold(True)
        notes_label.setFont(notes_label_font)
        layout.addWidget(notes_label)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(
            "Enter reason for bulk rate update (e.g., 'Annual rate adjustment for 2025')..."
        )
        self.notes_input.setMaximumHeight(80)
        layout.addWidget(self.notes_input)

        # Warning label
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: orange;")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_changes)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _preview_changes(self):
        """Preview bulk update changes."""
        # Clear previous preview
        self.preview_table.setRowCount(0)
        self.preview_data = []
        self.warning_label.setText("")

        # Get target states
        if self.selected_radio.isChecked():
            target_states = self.selected_states
        else:
            target_states = self.all_states

        if not target_states:
            QMessageBox.warning(
                self,
                "No States Selected",
                "Please select at least one state to update."
            )
            return

        # Get adjustment value
        if self.percentage_radio.isChecked():
            adjustment = self.percentage_input.value()
            if adjustment == 0:
                QMessageBox.warning(
                    self,
                    "No Adjustment",
                    "Please enter a non-zero percentage adjustment."
                )
                return
        else:
            fixed_rate = self.fixed_input.value()

        # Get current rates for all states and columns
        query = f"SELECT * FROM {self.table_name} WHERE state_code IN ({','.join('?' * len(target_states))})"
        rates = self.db.execute_query(query, tuple(target_states))

        # Get column names (exclude id, state_code, effective_date, created_at)
        if rates:
            all_columns = list(rates[0].keys())
            rate_columns = [
                col for col in all_columns
                if col not in ('id', 'state_code', 'effective_date', 'created_at')
            ]

            # Calculate changes
            for rate_row in rates:
                state_code = rate_row['state_code']

                for column in rate_columns:
                    current_value = rate_row[column]
                    if current_value is None:
                        continue

                    # Calculate new value
                    if self.percentage_radio.isChecked():
                        new_value = current_value * (1 + adjustment / 100)
                    else:
                        new_value = fixed_rate

                    # Validate range
                    new_value = max(0.0, min(100.0, new_value))

                    # Only include if value changes
                    if abs(new_value - current_value) >= 0.01:
                        change_pct = ((new_value - current_value) / current_value * 100) if current_value > 0 else 0

                        self.preview_data.append({
                            'state_code': state_code,
                            'column_name': column,
                            'old_value': current_value,
                            'new_value': new_value,
                            'change_pct': change_pct
                        })

        # Display preview
        if not self.preview_data:
            QMessageBox.information(
                self,
                "No Changes",
                "The adjustment would not result in any rate changes."
            )
            return

        self.preview_table.setRowCount(len(self.preview_data))

        for row, change in enumerate(self.preview_data):
            self.preview_table.setItem(
                row, 0, QTableWidgetItem(change['state_code'])
            )
            self.preview_table.setItem(
                row, 1, QTableWidgetItem(change['column_name'].replace('_', ' ').title())
            )
            self.preview_table.setItem(
                row, 2, QTableWidgetItem(f"{change['old_value']:.2f}%")
            )
            self.preview_table.setItem(
                row, 3, QTableWidgetItem(f"{change['new_value']:.2f}%")
            )

            change_str = f"{change['change_pct']:+.2f}%"
            change_item = QTableWidgetItem(change_str)

            # Color code changes
            if change['change_pct'] > 0:
                change_item.setForeground(QColor(0, 150, 0))  # Green for increase
            else:
                change_item.setForeground(QColor(200, 0, 0))  # Red for decrease

            self.preview_table.setItem(row, 4, change_item)

        # Update warning
        self.warning_label.setText(
            f"⚠ This will update {len(self.preview_data)} rate values"
        )

        # Enable apply button
        self.apply_btn.setEnabled(True)

    def _apply_changes(self):
        """Apply bulk update changes."""
        # Validate notes
        notes = self.notes_input.toPlainText().strip()
        if not notes:
            QMessageBox.warning(
                self,
                "Notes Required",
                "Please enter notes explaining the reason for this bulk update.\n\n"
                "Notes are required for audit trail compliance."
            )
            self.notes_input.setFocus()
            return

        if not self.preview_data:
            QMessageBox.warning(
                self,
                "No Preview",
                "Please preview changes before applying."
            )
            return

        # Confirm changes
        confirm_msg = f"You are about to update {len(self.preview_data)} rate values.\n\n"
        confirm_msg += f"Notes: {notes}\n\n"
        confirm_msg += "This action cannot be undone (but will be logged in the audit trail).\n\n"
        confirm_msg += "Proceed with bulk update?"

        reply = QMessageBox.question(
            self,
            "Confirm Bulk Update",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Apply all changes
                for change in self.preview_data:
                    # Update database
                    query = f"""
                        UPDATE {self.table_name}
                        SET {change['column_name']} = ?
                        WHERE state_code = ?
                    """
                    self.db.execute_update(
                        query,
                        (change['new_value'], change['state_code'])
                    )

                # Log to audit trail (bulk operation)
                self.audit_manager.log_bulk_changes(
                    user_id=self.user.id,
                    user_name=self.user.full_name,
                    changes=[
                        {
                            'table_name': self.table_name,
                            'state_code': change['state_code'],
                            'column_name': change['column_name'],
                            'old_value': change['old_value'],
                            'new_value': change['new_value']
                        }
                        for change in self.preview_data
                    ],
                    change_type='bulk_update',
                    notes=notes
                )

                QMessageBox.information(
                    self,
                    "Bulk Update Complete",
                    f"Successfully updated {len(self.preview_data)} rate values.\n\n"
                    f"All changes have been logged to the audit trail."
                )

                self.accept()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Bulk Update Failed",
                    f"Error applying bulk update:\n{str(e)}\n\n"
                    "Changes may have been partially applied."
                )


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

    dialog = BulkUpdateDialog(
        table_name='pivot_rates_under_20',
        table_display_name='Pivot Rates Under 20',
        selected_states=['NE', 'TX', 'OK'],
        all_states=['NE', 'TX', 'OK', 'KS', 'CO'],
        user=test_user
    )

    if dialog.exec():
        print("✓ Bulk update applied")
    else:
        print("✗ Bulk update cancelled")
