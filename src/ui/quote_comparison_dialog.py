"""
Quote comparison dialog for side-by-side quote analysis.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QScrollArea, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import List

from models.quote import Quote


class QuoteComparisonDialog(QDialog):
    """Dialog for comparing multiple quotes side-by-side."""

    def __init__(self, quotes: List[Quote], parent=None):
        """
        Initialize quote comparison dialog.

        Args:
            quotes: List of Quote objects to compare (2-4 quotes)
            parent: Parent widget
        """
        super().__init__(parent)
        self.quotes = quotes

        self.setWindowTitle(f"Quote Comparison ({len(quotes)} quotes)")
        self.setModal(True)
        self.resize(1000, 700)

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Comparing {len(self.quotes)} Quotes")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Scroll area for comparison table
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Comparison widget
        comparison_widget = self._create_comparison_widget()
        scroll.setWidget(comparison_widget)

        layout.addWidget(scroll)

        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_comparison_widget(self) -> QWidget:
        """Create the comparison table widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Basic Information Group
        basic_group = self._create_comparison_group("Basic Information", [
            ("Quote Number", lambda q: q.quote_number),
            ("Quote Date", lambda q: q.quote_date),
            ("Agent", lambda q: q.agent_name or "N/A"),
            ("Status", lambda q: q.status),
            ("State", lambda q: q.state_code),
            ("Term", lambda q: f"{q.term_months} months"),
        ])
        layout.addWidget(basic_group)

        # Equipment Details Group
        equipment_fields = [
            ("Quote Type", lambda q: "Multi-Pivot" if q.has_multiple_items() else "Single Pivot"),
        ]

        # For single pivot quotes, show equipment details
        if all(not q.has_multiple_items() for q in self.quotes):
            equipment_fields.extend([
                ("Pivot Amount", lambda q: f"${q.pivot_amount:,.0f}"),
                ("Equipment Age", lambda q: f"{q.equipment_age_years} years"),
                ("Equipment Type", lambda q: "Towable" if q.is_towable else "Standard"),
                ("Corner/Long", lambda q: "Yes" if q.is_corner_or_long else "No"),
                ("M&E Endorsement", lambda q: "Yes" if q.has_me_endorsement else "No"),
                ("Pivot Deductible", lambda q: self._format_deductible(q.pivot_deductible_code)),
                ("Ancillary Amount", lambda q: f"${q.ancillary_amount:,.0f}" if q.ancillary_amount else "$0"),
                ("Ancillary Deductible", lambda q: self._format_deductible(q.ancillary_deductible_code) if q.ancillary_amount else "N/A"),
                ("Submersible Pump", lambda q: f"${q.submersible_pump_amount:,.0f}" if q.submersible_pump_amount else "$0"),
            ])
        else:
            # For multi-pivot or mixed, just show item count
            equipment_fields.append(
                ("Equipment Items", lambda q: f"{len(q.line_items)} items" if q.has_multiple_items() else "1 item")
            )

        equipment_group = self._create_comparison_group("Equipment Details", equipment_fields)
        layout.addWidget(equipment_group)

        # Premium Details Group (only for single pivot quotes)
        if all(not q.has_multiple_items() for q in self.quotes):
            premium_group = self._create_comparison_group("Premium Breakdown", [
                ("Pivot Premium", lambda q: f"${q.pivot_premium:,.2f}" if q.pivot_premium else "$0.00"),
                ("Ancillary Premium", lambda q: f"${q.ancillary_premium:,.2f}" if q.ancillary_premium else "$0.00"),
                ("Submersible Charge", lambda q: f"${q.submersible_charge:,.2f}" if q.submersible_charge else "$0.00"),
            ])
            layout.addWidget(premium_group)

        # Total Premium Group (always shown)
        total_group = self._create_comparison_group("Total Premium", [
            ("TOTAL PREMIUM", lambda q: f"${q.total_premium:,.2f}"),
        ], highlight_total=True)
        layout.addWidget(total_group)

        # Highlight differences
        self._highlight_differences()

        widget.setLayout(layout)
        return widget

    def _create_comparison_group(self, title: str, fields: List[tuple], highlight_total: bool = False) -> QGroupBox:
        """
        Create a comparison group with fields.

        Args:
            title: Group title
            fields: List of (label, value_func) tuples
            highlight_total: Whether to highlight as total row

        Returns:
            QGroupBox with comparison grid
        """
        group = QGroupBox(title)
        grid = QGridLayout()

        # Header row with quote numbers
        grid.addWidget(QLabel(""), 0, 0)  # Empty cell for field labels
        for col, quote in enumerate(self.quotes):
            header = QLabel(quote.quote_number)
            header_font = QFont()
            header_font.setBold(True)
            header.setFont(header_font)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(header, 0, col + 1)

        # Field rows
        for row, (label, value_func) in enumerate(fields, start=1):
            # Field label
            label_widget = QLabel(label + ":")
            label_font = QFont()
            if highlight_total:
                label_font.setBold(True)
                label_font.setPointSize(11)
            label_widget.setFont(label_font)
            grid.addWidget(label_widget, row, 0)

            # Values for each quote
            for col, quote in enumerate(self.quotes):
                try:
                    value = value_func(quote)
                except:
                    value = "N/A"

                value_widget = QLabel(str(value))
                value_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

                if highlight_total:
                    value_font = QFont()
                    value_font.setBold(True)
                    value_font.setPointSize(11)
                    value_widget.setFont(value_font)
                    value_widget.setStyleSheet("background-color: #e8f4f8; padding: 5px;")

                grid.addWidget(value_widget, row, col + 1)

        group.setLayout(grid)
        return group

    def _highlight_differences(self):
        """Highlight fields that differ between quotes."""
        # This is a visual enhancement - could highlight cells with different values
        # For now, the side-by-side layout makes differences obvious
        pass

    def _format_deductible(self, code: int) -> str:
        """Format deductible code to display value."""
        deductible_map = {
            1: "$500",
            2: "$1,000",
            3: "$2,500",
            4: "$5,000"
        }
        return deductible_map.get(code, "Unknown")
