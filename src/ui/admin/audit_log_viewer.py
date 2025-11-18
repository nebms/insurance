"""
Audit log viewer for viewing rate change history.
Provides filtering, pagination, and CSV export capabilities.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDateEdit, QMessageBox,
    QSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from typing import Optional
from datetime import date, datetime
import csv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import get_db
from database.audit_manager import AuditManager
from database.auth_manager import AuthManager, User


class AuditLogViewer(QDialog):
    """Dialog for viewing and filtering rate change audit log."""

    def __init__(self, user: User, parent=None):
        """
        Initialize audit log viewer.

        Args:
            user: Authenticated user
            parent: Parent widget
        """
        super().__init__(parent)
        self.user = user
        self.db = get_db()
        self.audit_manager = AuditManager()
        self.auth_manager = AuthManager()

        self.current_page = 0
        self.page_size = 100

        self.setWindowTitle("Rate Change History - Audit Log")
        self.setModal(True)
        self.resize(1000, 700)

        self._init_ui()
        self._load_audit_log()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Rate Change History - Audit Log")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Filters
        filter_group_label = QLabel("Filters:")
        filter_group_label_font = QFont()
        filter_group_label_font.setBold(True)
        filter_group_label.setFont(filter_group_label_font)
        layout.addWidget(filter_group_label)

        filter_layout = QGridLayout()
        row = 0

        # Date range filter
        filter_layout.addWidget(QLabel("Date Range:"), row, 0)

        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")

        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("to"))
        date_layout.addWidget(self.end_date)
        date_layout.addStretch()

        filter_layout.addLayout(date_layout, row, 1, 1, 3)
        row += 1

        # State filter
        filter_layout.addWidget(QLabel("State:"), row, 0)
        self.state_filter = QComboBox()
        self.state_filter.addItem("All States", None)
        self._load_states()
        filter_layout.addWidget(self.state_filter, row, 1)

        # Table filter
        filter_layout.addWidget(QLabel("Table:"), row, 2)
        self.table_filter = QComboBox()
        self.table_filter.addItem("All Tables", None)
        self.table_filter.addItem("Pivot Rates Under 20", "pivot_rates_under_20")
        self.table_filter.addItem("Pivot Rates 20-34", "pivot_rates_20_to_34")
        self.table_filter.addItem("Pivot Rates 35+", "pivot_rates_35_plus")
        self.table_filter.addItem("Ancillary Rates", "ancillary_rates")
        filter_layout.addWidget(self.table_filter, row, 3)
        row += 1

        # Filter buttons
        filter_btn_layout = QHBoxLayout()

        apply_filter_btn = QPushButton("Apply Filter")
        apply_filter_btn.clicked.connect(self._apply_filter)

        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.clicked.connect(self._clear_filter)

        filter_btn_layout.addWidget(apply_filter_btn)
        filter_btn_layout.addWidget(clear_filter_btn)
        filter_btn_layout.addStretch()

        filter_layout.addLayout(filter_btn_layout, row, 0, 1, 4)

        layout.addLayout(filter_layout)

        # Audit log table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Table", "State", "Column",
            "Old Value", "New Value", "Type", "Notes"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        # Pagination
        pagination_layout = QHBoxLayout()

        self.status_label = QLabel("Loading...")
        pagination_layout.addWidget(self.status_label)
        pagination_layout.addStretch()

        self.prev_btn = QPushButton("< Previous")
        self.prev_btn.clicked.connect(self._previous_page)

        self.page_label = QLabel("Page 1")

        self.next_btn = QPushButton("Next >")
        self.next_btn.clicked.connect(self._next_page)

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)

        layout.addLayout(pagination_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self._export_to_csv)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

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

    def _load_audit_log(self):
        """Load audit log entries."""
        # Get filter values
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        state_code = self.state_filter.currentData()
        table_name = self.table_filter.currentData()

        # Get total count
        total_count = self.audit_manager.get_change_count(
            start_date=start_date,
            end_date=end_date,
            state_code=state_code,
            table_name=table_name
        )

        # Get changes for current page
        changes = self.audit_manager.get_changes(
            start_date=start_date,
            end_date=end_date,
            state_code=state_code,
            table_name=table_name,
            limit=self.page_size,
            offset=self.current_page * self.page_size
        )

        # Update table
        self.table.setRowCount(len(changes))

        for row, change in enumerate(changes):
            # Timestamp
            timestamp = datetime.fromisoformat(change.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            self.table.setItem(row, 0, QTableWidgetItem(timestamp))

            # User
            self.table.setItem(row, 1, QTableWidgetItem(change.user_name))

            # Table
            table_display = self._format_table_name(change.table_name)
            self.table.setItem(row, 2, QTableWidgetItem(table_display))

            # State
            self.table.setItem(row, 3, QTableWidgetItem(change.state_code))

            # Column
            column_display = change.column_name.replace('_', ' ').title()
            self.table.setItem(row, 4, QTableWidgetItem(column_display))

            # Old value
            old_value_str = f"{change.old_value:.2f}%" if change.old_value is not None else "N/A"
            self.table.setItem(row, 5, QTableWidgetItem(old_value_str))

            # New value
            new_value_str = f"{change.new_value:.2f}%" if change.new_value is not None else "N/A"
            self.table.setItem(row, 6, QTableWidgetItem(new_value_str))

            # Type
            self.table.setItem(row, 7, QTableWidgetItem(change.change_type or ""))

            # Notes
            self.table.setItem(row, 8, QTableWidgetItem(change.notes or ""))

        # Update status and pagination
        total_pages = (total_count + self.page_size - 1) // self.page_size
        current_page_display = self.current_page + 1

        self.status_label.setText(
            f"Showing {len(changes)} of {total_count} changes"
        )

        self.page_label.setText(f"Page {current_page_display} of {total_pages}")

        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(current_page_display < total_pages)

    def _format_table_name(self, table_name: str) -> str:
        """Format table name for display."""
        name_map = {
            'pivot_rates_under_20': 'Pivot <20',
            'pivot_rates_20_to_34': 'Pivot 20-34',
            'pivot_rates_35_plus': 'Pivot 35+',
            'ancillary_rates': 'Ancillary'
        }
        return name_map.get(table_name, table_name)

    def _apply_filter(self):
        """Apply filters and reload."""
        self.current_page = 0
        self._load_audit_log()

    def _clear_filter(self):
        """Clear all filters."""
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date.setDate(QDate.currentDate())
        self.state_filter.setCurrentIndex(0)
        self.table_filter.setCurrentIndex(0)
        self.current_page = 0
        self._load_audit_log()

    def _previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_audit_log()

    def _next_page(self):
        """Go to next page."""
        self.current_page += 1
        self._load_audit_log()

    def _export_to_csv(self):
        """Export current audit log view to CSV."""
        # Get filter values
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        state_code = self.state_filter.currentData()
        table_name = self.table_filter.currentData()

        # Get ALL changes (no pagination for export)
        changes = self.audit_manager.get_changes(
            start_date=start_date,
            end_date=end_date,
            state_code=state_code,
            table_name=table_name,
            limit=10000,  # Large limit for export
            offset=0
        )

        if not changes:
            QMessageBox.information(
                self,
                "No Data",
                "No audit log entries to export."
            )
            return

        # Prompt for file location
        default_filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Audit Log to CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Export to CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow([
                    'Timestamp', 'User', 'Table', 'State', 'Column',
                    'Old Value', 'New Value', 'Type', 'Notes'
                ])

                # Write data
                for change in changes:
                    timestamp = datetime.fromisoformat(change.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    table_display = self._format_table_name(change.table_name)
                    column_display = change.column_name.replace('_', ' ').title()
                    old_value_str = f"{change.old_value:.2f}%" if change.old_value is not None else "N/A"
                    new_value_str = f"{change.new_value:.2f}%" if change.new_value is not None else "N/A"

                    writer.writerow([
                        timestamp,
                        change.user_name,
                        table_display,
                        change.state_code,
                        column_display,
                        old_value_str,
                        new_value_str,
                        change.change_type or '',
                        change.notes or ''
                    ])

            QMessageBox.information(
                self,
                "Export Successful",
                f"Audit log exported successfully!\n\n"
                f"File: {file_path}\n"
                f"Records: {len(changes)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export audit log:\n{str(e)}"
            )


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

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

    dialog = AuditLogViewer(test_user)
    dialog.exec()
