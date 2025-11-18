"""
Rate table viewer with inline editing capabilities.
Displays rates for a specific table type with filtering and validation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QMessageBox, QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import csv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import get_db
from database.auth_manager import User
from database.audit_manager import AuditManager
from ui.admin.rate_editor_dialog import RateEditorDialog
from ui.admin.bulk_update_dialog import BulkUpdateDialog


class RateViewer(QWidget):
    """Rate table viewer with editing capabilities."""

    def __init__(self, table_name: str, table_display_name: str,
                 user: User, parent=None):
        """
        Initialize rate viewer.

        Args:
            table_name: Database table name
            table_display_name: Display name for UI
            user: Authenticated user
            parent: Parent widget
        """
        super().__init__(parent)
        self.table_name = table_name
        self.table_display_name = table_display_name
        self.user = user
        self.parent = parent

        self.db = get_db()
        self.audit_manager = AuditManager()

        # Column mapping for different table types
        self.column_maps = {
            'pivot_rates_under_20': [
                'state_code', 'effective_date',
                'standard_500_no_me', 'standard_500_with_me',
                'standard_1000_no_me', 'standard_1000_with_me',
                'standard_2500_no_me', 'standard_2500_with_me',
                'standard_5000_no_me', 'standard_5000_with_me',
                'towable_500_no_me', 'towable_500_with_me',
                'towable_1000_no_me', 'towable_1000_with_me',
                'towable_2500_no_me', 'towable_2500_with_me',
                'towable_5000_no_me', 'towable_5000_with_me'
            ],
            'pivot_rates_20_to_34': [
                'state_code', 'effective_date',
                'standard_500_no_me', 'standard_500_with_me',
                'standard_1000_no_me', 'standard_1000_with_me',
                'standard_2500_no_me', 'standard_2500_with_me',
                'standard_5000_no_me', 'standard_5000_with_me',
                'towable_500_no_me', 'towable_500_with_me',
                'towable_1000_no_me', 'towable_1000_with_me',
                'towable_2500_no_me', 'towable_2500_with_me',
                'towable_5000_no_me', 'towable_5000_with_me'
            ],
            'pivot_rates_35_plus': [
                'state_code', 'effective_date',
                'standard_rate', 'corner_rate'
            ],
            'ancillary_rates': [
                'state_code', 'effective_date',
                'standard_500', 'standard_1000', 'standard_2500', 'standard_5000',
                'corner_500', 'corner_1000', 'corner_2500', 'corner_5000'
            ]
        }

        self._init_ui()
        self._load_rates()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Header with filters
        header_layout = QHBoxLayout()

        title = QLabel(f"{self.table_display_name}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)

        header_layout.addWidget(title)
        header_layout.addStretch()

        # State filter
        header_layout.addWidget(QLabel("Filter by State:"))
        self.state_filter = QComboBox()
        self.state_filter.addItem("All States", None)
        self._load_states()
        self.state_filter.currentIndexChanged.connect(self._apply_filter)
        header_layout.addWidget(self.state_filter)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_rates)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Rates table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        layout.addWidget(self.table)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.row_count_label = QLabel("")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.row_count_label)

        layout.addLayout(status_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self._export_to_csv)

        bulk_update_btn = QPushButton("Bulk Update")
        bulk_update_btn.clicked.connect(self._bulk_update)

        button_layout.addWidget(export_btn)
        button_layout.addWidget(bulk_update_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_states(self):
        """Load states for filter dropdown."""
        query = "SELECT code, name FROM states WHERE is_active = 1 ORDER BY code"
        states = self.db.execute_query(query)

        for state in states:
            self.state_filter.addItem(
                f"{state['code']} - {state['name']}",
                state['code']
            )

    def _load_rates(self):
        """Load rates from database into table."""
        # Block signals during load to prevent change events
        self.table.blockSignals(True)

        # Get column configuration
        columns = self.column_maps.get(self.table_name, [])
        if not columns:
            QMessageBox.warning(
                self,
                "Configuration Error",
                f"No column mapping for table: {self.table_name}"
            )
            return

        # Set up table structure
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([
            col.replace('_', ' ').title() for col in columns
        ])

        # Load data
        query = f"SELECT * FROM {self.table_name} ORDER BY state_code"
        rates = self.db.execute_query(query)

        self.table.setRowCount(len(rates))

        for row_idx, rate in enumerate(rates):
            for col_idx, col_name in enumerate(columns):
                value = rate[col_name]

                # Format value
                if col_name in ('state_code', 'effective_date'):
                    # Non-editable columns
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(QColor(240, 240, 240))
                else:
                    # Editable rate columns
                    display_value = f"{value:.2f}" if value is not None else ""
                    item = QTableWidgetItem(display_value)
                    item.setData(Qt.ItemDataRole.UserRole, value)  # Store original value

                self.table.setItem(row_idx, col_idx, item)

        # Resize columns
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Update status
        self.row_count_label.setText(f"{len(rates)} rows")
        self.status_label.setText("Rates loaded successfully")

        # Re-enable signals
        self.table.blockSignals(False)

    def _apply_filter(self):
        """Apply state filter to table."""
        selected_state = self.state_filter.currentData()

        if selected_state is None:
            # Show all rows
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
        else:
            # Hide rows that don't match filter
            for row in range(self.table.rowCount()):
                state_item = self.table.item(row, 0)  # State code is first column
                if state_item:
                    self.table.setRowHidden(
                        row,
                        state_item.text() != selected_state
                    )

        # Update row count
        visible_rows = sum(
            1 for row in range(self.table.rowCount())
            if not self.table.isRowHidden(row)
        )
        self.row_count_label.setText(f"{visible_rows} rows (filtered)")

    def _on_item_changed(self, item: QTableWidgetItem):
        """Handle item change (inline editing)."""
        # Get column name
        col_idx = item.column()
        columns = self.column_maps.get(self.table_name, [])
        if col_idx >= len(columns):
            return

        column_name = columns[col_idx]

        # Skip non-editable columns
        if column_name in ('state_code', 'effective_date'):
            return

        # Validate new value
        new_value_str = item.text().strip()

        try:
            new_value = float(new_value_str) if new_value_str else None

            if new_value is not None:
                # Validate range (0-100%)
                if new_value < 0 or new_value > 100:
                    raise ValueError(f"Rate must be between 0 and 100%")

            # Get old value
            old_value = item.data(Qt.ItemDataRole.UserRole)

            # Only update if value changed
            if old_value != new_value:
                # Get state code
                state_item = self.table.item(item.row(), 0)
                state_code = state_item.text()

                # Update database
                self._update_rate(state_code, column_name, old_value, new_value)

                # Store new value
                item.setData(Qt.ItemDataRole.UserRole, new_value)

                # Update display
                if new_value is not None:
                    item.setText(f"{new_value:.2f}")

                self.status_label.setText(f"Updated {state_code} - {column_name}")

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid Value",
                f"Invalid rate value:\n{str(e)}\n\nRate must be a number between 0 and 100%."
            )
            # Restore old value
            old_value = item.data(Qt.ItemDataRole.UserRole)
            if old_value is not None:
                item.setText(f"{old_value:.2f}")
            else:
                item.setText("")

    def _on_cell_double_clicked(self, row: int, column: int):
        """Handle cell double-click for detailed editing."""
        # Get column name
        columns = self.column_maps.get(self.table_name, [])
        if column >= len(columns):
            return

        column_name = columns[column]

        # Skip non-editable columns
        if column_name in ('state_code', 'effective_date'):
            return

        # Get state code and current value
        state_item = self.table.item(row, 0)
        state_code = state_item.text()

        value_item = self.table.item(row, column)
        current_value = value_item.data(Qt.ItemDataRole.UserRole)

        # Open detailed editor dialog
        dialog = RateEditorDialog(
            table_name=self.table_name,
            state_code=state_code,
            column_name=column_name,
            current_value=current_value,
            user=self.user,
            parent=self
        )

        if dialog.exec():
            # Reload rates to reflect changes
            self._load_rates()
            self.status_label.setText(f"Rate updated for {state_code} - {column_name}")

    def _update_rate(self, state_code: str, column_name: str,
                    old_value: Optional[float], new_value: Optional[float]):
        """
        Update rate in database and log to audit trail.

        Args:
            state_code: State code
            column_name: Column being updated
            old_value: Previous value
            new_value: New value
        """
        # Update database
        query = f"""
            UPDATE {self.table_name}
            SET {column_name} = ?
            WHERE state_code = ?
        """
        self.db.execute_update(query, (new_value, state_code))

        # Log to audit trail
        self.audit_manager.log_rate_change(
            user_id=self.user.id,
            user_name=self.user.full_name,
            table_name=self.table_name,
            state_code=state_code,
            column_name=column_name,
            old_value=old_value,
            new_value=new_value,
            change_type='update',
            notes=f"Inline edit by {self.user.username}"
        )

    def _export_to_csv(self):
        """Export current rates to CSV file."""
        # Get current rates from database
        query = f"SELECT * FROM {self.table_name} ORDER BY state_code"
        rates = self.db.execute_query(query)

        if not rates:
            QMessageBox.information(
                self,
                "No Data",
                "No rates to export."
            )
            return

        # Prompt for file location
        default_filename = f"{self.table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Rates to CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Get column names
            columns = self.column_maps.get(self.table_name, [])

            # Export to CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header (formatted column names)
                header = [col.replace('_', ' ').title() for col in columns]
                writer.writerow(header)

                # Write data
                for rate in rates:
                    row = []
                    for col in columns:
                        value = rate[col]
                        if col in ('state_code', 'effective_date'):
                            row.append(value)
                        else:
                            # Format rate values
                            row.append(f"{value:.2f}" if value is not None else "")
                    writer.writerow(row)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Rates exported successfully!\n\n"
                f"File: {file_path}\n"
                f"Records: {len(rates)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export rates:\n{str(e)}"
            )

    def _bulk_update(self):
        """Open bulk update dialog."""
        # Get selected states (from selected rows)
        selected_rows = self.table.selectionModel().selectedRows()
        selected_states = []

        for row_index in selected_rows:
            row = row_index.row()
            state_item = self.table.item(row, 0)
            if state_item:
                selected_states.append(state_item.text())

        # Get all available states
        query = "SELECT code FROM states WHERE is_active = 1 ORDER BY code"
        all_states_result = self.db.execute_query(query)
        all_states = [row['code'] for row in all_states_result]

        # Open bulk update dialog
        dialog = BulkUpdateDialog(
            table_name=self.table_name,
            table_display_name=self.table_display_name,
            selected_states=selected_states,
            all_states=all_states,
            user=self.user,
            parent=self
        )

        if dialog.exec():
            # Reload rates to reflect changes
            self._load_rates()
            self.status_label.setText("Bulk update completed successfully")
