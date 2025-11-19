"""
Template management dialogs for quote templates.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox, QListWidget, QListWidgetItem, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.quote_template import QuoteTemplate, QuoteTemplateRepository


class SaveTemplateDialog(QDialog):
    """Dialog for saving current quote configuration as a template."""

    def __init__(self, quote_data: dict, parent=None):
        """
        Initialize save template dialog.

        Args:
            quote_data: Dictionary containing quote configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.quote_data = quote_data
        self.template_repo = QuoteTemplateRepository()
        self.saved_template = None

        self.setWindowTitle("Save Quote Template")
        self.setModal(True)
        self.setFixedSize(500, 350)

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Save Quote as Template")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Info label
        info = QLabel(
            "Save this quote configuration as a reusable template.\n"
            "Templates allow you to quickly create quotes with common settings."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Form
        form_layout = QGridLayout()
        row = 0

        # Template Name
        form_layout.addWidget(QLabel("Template Name:"), row, 0)
        self.template_name = QLineEdit()
        self.template_name.setPlaceholderText("e.g., Standard Nebraska 5-Year")
        form_layout.addWidget(self.template_name, row, 1)
        row += 1

        # Description
        form_layout.addWidget(QLabel("Description:"), row, 0, Qt.AlignmentFlag.AlignTop)
        self.description = QTextEdit()
        self.description.setPlaceholderText(
            "Optional: Describe when to use this template"
        )
        self.description.setMaximumHeight(100)
        form_layout.addWidget(self.description, row, 1)
        row += 1

        layout.addLayout(form_layout)

        # Configuration summary
        summary = QLabel("Configuration:")
        summary_font = QFont()
        summary_font.setBold(True)
        summary.setFont(summary_font)
        layout.addWidget(summary)

        summary_text = self._build_summary()
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Template")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_template)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _build_summary(self) -> str:
        """Build configuration summary text."""
        parts = []
        parts.append(f"State: {self.quote_data.get('state_code', 'N/A')}")
        parts.append(f"Term: {self.quote_data.get('term_months', 12)} months")
        parts.append(f"Pivot Amount: ${self.quote_data.get('pivot_amount', 0):,.0f}")
        parts.append(f"Equipment Age: {self.quote_data.get('equipment_age_years', 0)} years")

        if self.quote_data.get('is_towable'):
            parts.append("Type: Towable")
        else:
            parts.append("Type: Standard")

        return " | ".join(parts)

    def _save_template(self):
        """Save template to database."""
        # Validate
        template_name = self.template_name.text().strip()
        if not template_name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a template name."
            )
            self.template_name.setFocus()
            return

        # Check if name already exists
        if self.template_repo.exists(template_name):
            reply = QMessageBox.question(
                self,
                "Template Exists",
                f"A template named '{template_name}' already exists.\n\n"
                f"Do you want to overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Delete existing template
            existing = self.template_repo.get_by_name(template_name)
            if existing:
                self.template_repo.delete(existing.id)

        # Create template
        template = QuoteTemplate(
            template_name=template_name,
            description=self.description.toPlainText().strip(),
            state_code=self.quote_data.get('state_code'),
            term_months=self.quote_data.get('term_months'),
            pivot_amount=self.quote_data.get('pivot_amount'),
            equipment_age_years=self.quote_data.get('equipment_age_years'),
            pivot_deductible_code=self.quote_data.get('pivot_deductible_code'),
            ancillary_deductible_code=self.quote_data.get('ancillary_deductible_code'),
            ancillary_amount=self.quote_data.get('ancillary_amount', 0),
            submersible_pump_amount=self.quote_data.get('submersible_pump_amount', 0),
            is_towable=self.quote_data.get('is_towable', 0),
            is_corner_or_long=self.quote_data.get('is_corner_or_long', 0),
            has_me_endorsement=self.quote_data.get('has_me_endorsement', 1)
        )

        try:
            template_id = self.template_repo.create(template)

            if template_id:
                template.id = template_id
                self.saved_template = template

                QMessageBox.information(
                    self,
                    "Template Saved",
                    f"Template '{template_name}' has been saved successfully!"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Save Failed",
                    "Could not save template. Please try again."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Error saving template:\n{str(e)}"
            )

    def get_template(self) -> QuoteTemplate:
        """Get the saved template."""
        return self.saved_template


class TemplateManagerDialog(QDialog):
    """Dialog for managing quote templates."""

    def __init__(self, state_code: str = None, parent=None):
        """
        Initialize template manager dialog.

        Args:
            state_code: Optional state code to filter templates
            parent: Parent widget
        """
        super().__init__(parent)
        self.state_code = state_code
        self.template_repo = QuoteTemplateRepository()
        self.selected_template = None

        self.setWindowTitle("Manage Quote Templates")
        self.setModal(True)
        self.resize(700, 500)

        self._init_ui()
        self._load_templates()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Quote Templates")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Filter info
        if self.state_code:
            filter_label = QLabel(f"Showing templates for: {self.state_code}")
            filter_label.setStyleSheet("color: #666;")
            layout.addWidget(filter_label)

        # Templates list
        self.template_list = QListWidget()
        self.template_list.itemDoubleClicked.connect(self._load_template)
        self.template_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.template_list)

        # Template details
        details_label = QLabel("Template Details:")
        details_label_font = QFont()
        details_label_font.setBold(True)
        details_label.setFont(details_label_font)
        layout.addWidget(details_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        layout.addWidget(self.details_text)

        # Buttons
        button_layout = QHBoxLayout()

        self.load_btn = QPushButton("Load Template")
        self.load_btn.clicked.connect(self._load_template)
        self.load_btn.setEnabled(False)

        self.delete_btn = QPushButton("Delete Template")
        self.delete_btn.clicked.connect(self._delete_template)
        self.delete_btn.setEnabled(False)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_templates)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_templates(self):
        """Load templates from database."""
        self.template_list.clear()
        self.details_text.clear()

        templates = self.template_repo.get_all(self.state_code)

        if not templates:
            item = QListWidgetItem("No templates found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.template_list.addItem(item)
            return

        for template in templates:
            display_text = f"{template.template_name} ({template.state_code})"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

    def _on_selection_changed(self):
        """Handle template selection change."""
        items = self.template_list.selectedItems()

        if not items:
            self.details_text.clear()
            self.load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        template = items[0].data(Qt.ItemDataRole.UserRole)
        if not template:
            return

        # Enable buttons
        self.load_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        # Show details
        details = []
        details.append(f"Name: {template.template_name}")
        details.append(f"State: {template.state_code}")
        details.append(f"Term: {template.term_months} months")
        details.append("")
        details.append(f"Pivot Amount: ${template.pivot_amount:,.0f}")
        details.append(f"Equipment Age: {template.equipment_age_years} years")
        details.append(f"Type: {'Towable' if template.is_towable else 'Standard'}")
        details.append(f"Corner/Long: {'Yes' if template.is_corner_or_long else 'No'}")
        details.append(f"M&E Endorsement: {'Yes' if template.has_me_endorsement else 'No'}")
        details.append("")
        details.append(f"Pivot Deductible Code: {template.pivot_deductible_code}")
        details.append(f"Ancillary Amount: ${template.ancillary_amount:,.0f}")
        details.append(f"Submersible Pump: ${template.submersible_pump_amount:,.0f}")

        if template.description:
            details.append("")
            details.append(f"Description: {template.description}")

        details.append("")
        details.append(f"Created: {template.created_at}")

        self.details_text.setPlainText("\n".join(details))

    def _load_template(self):
        """Load selected template."""
        items = self.template_list.selectedItems()
        if not items:
            return

        template = items[0].data(Qt.ItemDataRole.UserRole)
        if not template:
            return

        self.selected_template = template
        self.accept()

    def _delete_template(self):
        """Delete selected template."""
        items = self.template_list.selectedItems()
        if not items:
            return

        template = items[0].data(Qt.ItemDataRole.UserRole)
        if not template:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete template '{template.template_name}'?\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.template_repo.delete(template.id):
                    QMessageBox.information(
                        self,
                        "Template Deleted",
                        f"Template '{template.template_name}' has been deleted."
                    )
                    self._load_templates()
                else:
                    QMessageBox.warning(
                        self,
                        "Delete Failed",
                        f"Could not delete template '{template.template_name}'."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Error",
                    f"Error deleting template:\n{str(e)}"
                )

    def get_selected_template(self) -> QuoteTemplate:
        """Get the selected template."""
        return self.selected_template
