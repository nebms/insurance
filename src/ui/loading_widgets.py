"""
Loading indicator widget for long-running operations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
    QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QMovie
import os


class LoadingOverlay(QWidget):
    """Semi-transparent loading overlay widget."""

    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.message = message

        # Make it fill the parent
        if parent:
            self.setGeometry(parent.rect())

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        # Semi-transparent background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 200);
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Loading message
        message_label = QLabel(self.message)
        message_font = QFont()
        message_font.setPointSize(14)
        message_font.setBold(True)
        message_label.setFont(message_font)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #333; background-color: transparent;")

        # Progress bar (indeterminate)
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(0)  # Indeterminate mode
        progress.setTextVisible(False)
        progress.setFixedWidth(300)
        progress.setFixedHeight(10)
        progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3b82f6;
                border-radius: 5px;
                background-color: #e0e7ff;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
            }
        """)

        layout.addWidget(message_label)
        layout.addSpacing(20)
        layout.addWidget(progress, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def update_message(self, message):
        """Update the loading message."""
        self.message = message
        # Find and update the label
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setText(message)
                break


class LoadingSpinner(QLabel):
    """Simple loading spinner label."""

    def __init__(self, parent=None, size=32):
        super().__init__(parent)
        self.size = size

        # Create a simple spinner using text
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_index = 0

        # Set up the label
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color: #3b82f6;")

        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_spinner)

    def start(self):
        """Start the spinner animation."""
        self.timer.start(100)  # Update every 100ms
        self.show()

    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
        self.hide()

    def _update_spinner(self):
        """Update the spinner character."""
        self.setText(self.spinner_chars[self.current_index])
        self.current_index = (self.current_index + 1) % len(self.spinner_chars)


class ProgressDialog(QDialog):
    """Dialog showing progress for multi-step operations."""

    def __init__(self, parent=None, title="Processing", message="Please wait..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)

        self._init_ui(message)

    def _init_ui(self, message):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title_label = QLabel(message)
        title_font = QFont()
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        self.title_label = title_label

        layout.addSpacing(20)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3b82f6;
                border-radius: 5px;
                background-color: #e0e7ff;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def set_progress(self, value, message=""):
        """
        Update progress.

        Args:
            value: Progress value (0-100)
            message: Optional status message
        """
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def set_message(self, message):
        """Update the main message."""
        self.title_label.setText(message)

    def set_indeterminate(self):
        """Set progress bar to indeterminate mode."""
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
