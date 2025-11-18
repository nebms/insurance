"""
CSV rate table import dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import csv
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import get_db


class RateImportDialog(QDialog):
    """Dialog for importing rate tables from CSV files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Rate Tables from CSV")
        self.setModal(True)
        self.resize(700, 500)
        self.csv_file = None

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Import Insurance Rate Tables")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "<b>Instructions:</b><br>"
            "1. Select the rate table type to import<br>"
            "2. Choose a CSV file with the rate data<br>"
            "3. Preview the data to verify correctness<br>"
            "4. Click Import to load rates into database<br><br>"
            "<b>CSV Format Requirements:</b><br>"
            "• First row must contain column headers<br>"
            "• Must include 'state_code' column<br>"
            "• Rate values should be in percentage format (e.g., 2.50 for 2.50%)"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Rate table type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Rate Table Type:"))
        self.table_type = QComboBox()
        self.table_type.addItems([
            "Pivot Rates (Under 20 years)",
            "Pivot Rates (20-34 years)",
            "Pivot Rates (35+ years)",
            "Ancillary Rates"
        ])
        type_layout.addWidget(self.table_type)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        # Preview area
        layout.addWidget(QLabel("Preview (first 10 rows):"))
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        layout.addWidget(self.preview_text)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        self.import_btn = QPushButton("Import Rates")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._import_rates)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.import_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _browse_file(self):
        """Browse for CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV Rate Table",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.csv_file = file_path
            self.file_label.setText(Path(file_path).name)
            self._preview_file()
            self.import_btn.setEnabled(True)

    def _preview_file(self):
        """Preview the CSV file."""
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.reader(f)
                preview_lines = []
                for i, row in enumerate(reader):
                    if i >= 10:
                        break
                    preview_lines.append(", ".join(row))

                self.preview_text.setPlainText("\n".join(preview_lines))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Preview Error",
                f"Error reading CSV file:\n{str(e)}"
            )
            self.import_btn.setEnabled(False)

    def _import_rates(self):
        """Import rates from CSV into database."""
        table_type = self.table_type.currentIndex()

        try:
            self.progress.setVisible(True)
            self.progress.setValue(0)

            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    raise ValueError("CSV file is empty")

                # Verify required columns
                if 'state_code' not in rows[0]:
                    raise ValueError("CSV must contain 'state_code' column")

                db = get_db()
                effective_date = str(date.today())
                imported = 0

                for i, row in enumerate(rows):
                    state_code = row['state_code'].upper()

                    if table_type == 0:  # Pivot Under 20
                        self._import_pivot_under_20(db, state_code, effective_date, row)
                    elif table_type == 1:  # Pivot 20-34
                        self._import_pivot_20_to_34(db, state_code, effective_date, row)
                    elif table_type == 2:  # Pivot 35+
                        self._import_pivot_35_plus(db, state_code, effective_date, row)
                    elif table_type == 3:  # Ancillary
                        self._import_ancillary(db, state_code, effective_date, row)

                    imported += 1
                    self.progress.setValue(int((i + 1) / len(rows) * 100))

                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Successfully imported {imported} rate records!\n\n"
                    f"Rates are now available for quote calculations."
                )

                self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing rates:\n{str(e)}\n\n"
                "Please verify CSV format and try again."
            )
        finally:
            self.progress.setVisible(False)

    def _validate_rate_value(self, value_str: str, column_name: str, state: str) -> float:
        """
        Validate and convert rate value.

        Args:
            value_str: String value from CSV
            column_name: Name of the column for error messages
            state: State code for error messages

        Returns:
            float: Validated rate value

        Raises:
            ValueError: If value is invalid
        """
        if not value_str or value_str.strip() == '':
            raise ValueError(
                f"Missing required rate value for state '{state}', column '{column_name}'\n\n"
                f"All rate columns must have values."
            )

        try:
            rate = float(value_str)
        except ValueError:
            raise ValueError(
                f"Invalid rate value for state '{state}', column '{column_name}': '{value_str}'\n\n"
                f"Rate must be a valid number."
            )

        # Validate rate range (0-100%)
        if rate < 0:
            raise ValueError(
                f"Negative rate for state '{state}', column '{column_name}': {rate}\n\n"
                f"Rates cannot be negative."
            )

        if rate > 100:
            raise ValueError(
                f"Invalid rate for state '{state}', column '{column_name}': {rate}%\n\n"
                f"Rates cannot exceed 100%.\n"
                f"Note: Enter rates as percentages (e.g., 2.50 for 2.50%)."
            )

        return rate

    def _import_pivot_under_20(self, db, state, date, row):
        """Import pivot under 20 rate."""
        # Required columns for this table
        required_columns = [
            'standard_500_no_me', 'standard_500_with_me',
            'standard_1000_no_me', 'standard_1000_with_me',
            'standard_2500_no_me', 'standard_2500_with_me',
            'standard_5000_no_me', 'standard_5000_with_me',
            'towable_500_no_me', 'towable_500_with_me',
            'towable_1000_no_me', 'towable_1000_with_me',
            'towable_2500_no_me', 'towable_2500_with_me',
            'towable_5000_no_me', 'towable_5000_with_me'
        ]

        # Validate all columns exist and have valid values
        validated_rates = []
        for col in required_columns:
            if col not in row:
                raise ValueError(
                    f"Missing required column '{col}' in CSV file\n\n"
                    f"For Pivot Rates (Under 20 years), all 16 rate columns must be present."
                )
            validated_rates.append(self._validate_rate_value(row[col], col, state))

        query = """
            INSERT OR REPLACE INTO pivot_rates_under_20 (
                state_code, effective_date,
                standard_500_no_me, standard_500_with_me,
                standard_1000_no_me, standard_1000_with_me,
                standard_2500_no_me, standard_2500_with_me,
                standard_5000_no_me, standard_5000_with_me,
                towable_500_no_me, towable_500_with_me,
                towable_1000_no_me, towable_1000_with_me,
                towable_2500_no_me, towable_2500_with_me,
                towable_5000_no_me, towable_5000_with_me
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (state, date, *validated_rates)
        db.execute_insert(query, params)

    def _import_pivot_20_to_34(self, db, state, date, row):
        """Import pivot 20-34 rate."""
        # Required columns for this table
        required_columns = [
            'standard_500_no_me', 'standard_500_with_me',
            'standard_1000_no_me', 'standard_1000_with_me',
            'standard_2500_no_me', 'standard_2500_with_me',
            'standard_5000_no_me', 'standard_5000_with_me',
            'towable_500_no_me', 'towable_500_with_me',
            'towable_1000_no_me', 'towable_1000_with_me',
            'towable_2500_no_me', 'towable_2500_with_me',
            'towable_5000_no_me', 'towable_5000_with_me'
        ]

        # Validate all columns exist and have valid values
        validated_rates = []
        for col in required_columns:
            if col not in row:
                raise ValueError(
                    f"Missing required column '{col}' in CSV file\n\n"
                    f"For Pivot Rates (20-34 years), all 16 rate columns must be present."
                )
            validated_rates.append(self._validate_rate_value(row[col], col, state))

        query = """
            INSERT OR REPLACE INTO pivot_rates_20_to_34 (
                state_code, effective_date,
                standard_500_no_me, standard_500_with_me,
                standard_1000_no_me, standard_1000_with_me,
                standard_2500_no_me, standard_2500_with_me,
                standard_5000_no_me, standard_5000_with_me,
                towable_500_no_me, towable_500_with_me,
                towable_1000_no_me, towable_1000_with_me,
                towable_2500_no_me, towable_2500_with_me,
                towable_5000_no_me, towable_5000_with_me
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (state, date, *validated_rates)
        db.execute_insert(query, params)

    def _import_pivot_35_plus(self, db, state, date, row):
        """Import pivot 35+ rate."""
        # Required columns for this table
        required_columns = ['standard_rate', 'corner_rate']

        # Validate all columns exist and have valid values
        validated_rates = []
        for col in required_columns:
            if col not in row:
                raise ValueError(
                    f"Missing required column '{col}' in CSV file\n\n"
                    f"For Pivot Rates (35+ years), both 'standard_rate' and 'corner_rate' columns must be present."
                )
            validated_rates.append(self._validate_rate_value(row[col], col, state))

        query = """
            INSERT OR REPLACE INTO pivot_rates_35_plus (
                state_code, effective_date, standard_rate, corner_rate
            ) VALUES (?, ?, ?, ?)
        """
        params = (state, date, *validated_rates)
        db.execute_insert(query, params)

    def _import_ancillary(self, db, state, date, row):
        """Import ancillary rate."""
        # Required columns for this table
        required_columns = [
            'standard_500', 'standard_1000', 'standard_2500', 'standard_5000',
            'corner_500', 'corner_1000', 'corner_2500', 'corner_5000'
        ]

        # Validate all columns exist and have valid values
        validated_rates = []
        for col in required_columns:
            if col not in row:
                raise ValueError(
                    f"Missing required column '{col}' in CSV file\n\n"
                    f"For Ancillary Rates, all 8 rate columns must be present."
                )
            validated_rates.append(self._validate_rate_value(row[col], col, state))

        query = """
            INSERT OR REPLACE INTO ancillary_rates (
                state_code, effective_date,
                standard_500, standard_1000, standard_2500, standard_5000,
                corner_500, corner_1000, corner_2500, corner_5000
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (state, date, *validated_rates)
        db.execute_insert(query, params)
