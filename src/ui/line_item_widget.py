"""
Line Item Widget for managing multiple equipment items in a quote.
Allows adding, editing, and removing pivot equipment from a quote.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import List, Optional

from models.quote_line_item import QuoteLineItem


class LineItemWidget(QWidget):
    """Widget for managing quote line items."""

    # Signal emitted when line items change
    items_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_items: List[QuoteLineItem] = []
        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Equipment Items")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)

        self.count_label = QLabel("0 items")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)

        layout.addLayout(header_layout)

        # Line items table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "#", "Pivot Amount", "Age", "Type", "Deductible",
            "Ancillary", "M&E", "Premium", "Actions", ""
        ])

        # Set column widths
        self.table.setColumnWidth(0, 40)   # Line number
        self.table.setColumnWidth(1, 120)  # Pivot amount
        self.table.setColumnWidth(2, 60)   # Age
        self.table.setColumnWidth(3, 100)  # Type
        self.table.setColumnWidth(4, 100)  # Deductible
        self.table.setColumnWidth(5, 100)  # Ancillary
        self.table.setColumnWidth(6, 60)   # M&E
        self.table.setColumnWidth(7, 100)  # Premium
        self.table.setColumnWidth(8, 120)  # Actions

        self.table.horizontalHeader().setSectionResizeMode(
            9, QHeaderView.ResizeMode.Stretch
        )

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("+ Add Equipment")
        self.add_btn.clicked.connect(self._add_item)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_all)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Total display
        total_layout = QHBoxLayout()
        total_layout.addStretch()

        total_label = QLabel("Total Premium:")
        total_label_font = QFont()
        total_label_font.setBold(True)
        total_label.setFont(total_label_font)

        self.total_display = QLabel("$0.00")
        total_display_font = QFont()
        total_display_font.setPointSize(12)
        total_display_font.setBold(True)
        self.total_display.setFont(total_display_font)

        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_display)

        layout.addLayout(total_layout)

        self.setLayout(layout)

    def set_line_items(self, items: List[QuoteLineItem]):
        """Set line items and refresh display."""
        self.line_items = items
        self._refresh_table()

    def get_line_items(self) -> List[QuoteLineItem]:
        """Get current line items."""
        return self.line_items

    def add_line_item(self, item: QuoteLineItem):
        """Add a new line item."""
        # Set line number
        item.line_number = len(self.line_items) + 1
        self.line_items.append(item)
        self._refresh_table()
        self.items_changed.emit()

    def _add_item(self):
        """Add new equipment item (opens dialog in parent)."""
        # Signal to parent to open add dialog
        # Parent should call add_line_item() after dialog
        if self.parent():
            self.parent()._open_line_item_dialog()

    def _edit_item(self, index: int):
        """Edit existing line item."""
        if 0 <= index < len(self.line_items):
            if self.parent():
                self.parent()._open_line_item_dialog(self.line_items[index], index)

    def _delete_item(self, index: int):
        """Delete line item."""
        if 0 <= index < len(self.line_items):
            item = self.line_items[index]

            reply = QMessageBox.question(
                self,
                "Delete Equipment",
                f"Delete equipment item #{item.line_number}?\n\n"
                f"Pivot Amount: ${item.pivot_amount:,.2f}\n"
                f"Age: {item.equipment_age_years} years",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.line_items.pop(index)
                # Renumber remaining items
                for i, item in enumerate(self.line_items):
                    item.line_number = i + 1
                self._refresh_table()
                self.items_changed.emit()

    def _clear_all(self):
        """Clear all line items."""
        if not self.line_items:
            return

        reply = QMessageBox.question(
            self,
            "Clear All Equipment",
            f"Remove all {len(self.line_items)} equipment item(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.line_items.clear()
            self._refresh_table()
            self.items_changed.emit()

    def _refresh_table(self):
        """Refresh table display."""
        self.table.setRowCount(len(self.line_items))

        deductible_map = {
            1: "$500",
            2: "$1,000",
            3: "$2,500",
            4: "$5,000"
        }

        for row, item in enumerate(self.line_items):
            # Line number
            line_num = QTableWidgetItem(str(item.line_number))
            line_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, line_num)

            # Pivot amount
            pivot_amt = QTableWidgetItem(f"${item.pivot_amount:,.2f}")
            pivot_amt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, pivot_amt)

            # Age
            age = QTableWidgetItem(f"{item.equipment_age_years} yrs")
            age.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, age)

            # Type
            type_parts = []
            if item.is_towable:
                type_parts.append("Towable")
            else:
                type_parts.append("Standard")
            if item.is_corner_or_long:
                type_parts.append("Corner/Long")
            type_str = ", ".join(type_parts)
            self.table.setItem(row, 3, QTableWidgetItem(type_str))

            # Deductible
            ded = deductible_map.get(item.pivot_deductible_code, "N/A")
            self.table.setItem(row, 4, QTableWidgetItem(ded))

            # Ancillary
            if item.ancillary_amount > 0:
                anc = QTableWidgetItem(f"${item.ancillary_amount:,.2f}")
                anc.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                anc = QTableWidgetItem("None")
                anc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, anc)

            # M&E
            me = QTableWidgetItem("Yes" if item.has_me_endorsement else "No")
            me.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, me)

            # Premium
            if item.line_total_premium:
                prem = QTableWidgetItem(f"${item.line_total_premium:,.2f}")
                prem.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                prem_font = QFont()
                prem_font.setBold(True)
                prem.setFont(prem_font)
                self.table.setItem(row, 7, prem)
            else:
                self.table.setItem(row, 7, QTableWidgetItem("Not calculated"))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, r=row: self._edit_item(r))

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self._delete_item(r))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 8, actions_widget)

        # Update count and total
        self.count_label.setText(f"{len(self.line_items)} item(s)")

        total = sum(item.line_total_premium or 0 for item in self.line_items)
        self.total_display.setText(f"${total:,.2f}")

        # Enable/disable buttons
        self.clear_btn.setEnabled(len(self.line_items) > 0)

    def update_item(self, index: int, item: QuoteLineItem):
        """Update existing line item."""
        if 0 <= index < len(self.line_items):
            item.line_number = self.line_items[index].line_number
            self.line_items[index] = item
            self._refresh_table()
            self.items_changed.emit()

    def has_items(self) -> bool:
        """Check if there are any line items."""
        return len(self.line_items) > 0

    def get_total_premium(self) -> float:
        """Get total premium across all line items."""
        return sum(item.line_total_premium or 0 for item in self.line_items)
