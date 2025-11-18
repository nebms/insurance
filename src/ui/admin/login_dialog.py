"""
Unified login dialog for both admin and agent users.
Routes users to appropriate interface based on role.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.auth_manager import AuthManager, User


class LoginDialog(QDialog):
    """Unified login dialog for admin and agent users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CSI Pivot Quote - Login")
        self.setModal(True)
        self.setFixedSize(400, 300)

        self.auth_manager = AuthManager()
        self.authenticated_user: Optional[User] = None
        self.login_attempts = 0
        self.max_attempts = 3

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Title
        title_layout = QVBoxLayout()
        title = QLabel("CSI Pivot Quote")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Irrigation Equipment Insurance")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)

        # Login form
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(10)

        # Username
        username_label = QLabel("Username:")
        username_label_font = QFont()
        username_label_font.setBold(True)
        username_label.setFont(username_label_font)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.returnPressed.connect(self._on_login)

        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_input, 0, 1)

        # Password
        password_label = QLabel("Password:")
        password_label_font = QFont()
        password_label_font.setBold(True)
        password_label.setFont(password_label_font)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.returnPressed.connect(self._on_login)

        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.password_input, 1, 1)

        layout.addLayout(form_layout)

        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Exit")
        cancel_btn.clicked.connect(self.reject)

        self.login_btn = QPushButton("Login")
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self._on_login)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.login_btn)

        layout.addLayout(button_layout)

        # Info message
        info_label = QLabel("Default credentials: admin / admin123")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label_font = QFont()
        info_label_font.setPointSize(8)
        info_label_font.setItalic(True)
        info_label.setFont(info_label_font)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

        layout.addStretch()
        self.setLayout(layout)

        # Focus on username field
        self.username_input.setFocus()

    def _on_login(self):
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validate inputs
        if not username:
            self.status_label.setText("Please enter your username")
            self.username_input.setFocus()
            return

        if not password:
            self.status_label.setText("Please enter your password")
            self.password_input.setFocus()
            return

        # Clear status
        self.status_label.setText("")

        # Attempt authentication
        user = self.auth_manager.authenticate(username, password)

        if user:
            self.authenticated_user = user
            self.accept()
        else:
            self.login_attempts += 1
            remaining = self.max_attempts - self.login_attempts

            if remaining > 0:
                self.status_label.setText(
                    f"Invalid username or password. {remaining} attempt(s) remaining."
                )
                self.password_input.clear()
                self.password_input.setFocus()
            else:
                QMessageBox.critical(
                    self,
                    "Login Failed",
                    "Maximum login attempts exceeded.\n\n"
                    "The application will now close."
                )
                self.reject()

    def get_authenticated_user(self) -> Optional[User]:
        """
        Get authenticated user after successful login.

        Returns:
            User object if authenticated, None otherwise
        """
        return self.authenticated_user

    def is_admin(self) -> bool:
        """
        Check if authenticated user is admin.

        Returns:
            True if user is admin
        """
        return (self.authenticated_user is not None and
                self.authenticated_user.role == 'admin')

    def is_agent(self) -> bool:
        """
        Check if authenticated user is agent.

        Returns:
            True if user is agent
        """
        return (self.authenticated_user is not None and
                self.authenticated_user.role == 'agent')


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = LoginDialog()
    if dialog.exec():
        user = dialog.get_authenticated_user()
        if user:
            print(f"✓ Login successful!")
            print(f"  User: {user.username}")
            print(f"  Name: {user.full_name}")
            print(f"  Role: {user.role}")

            if dialog.is_admin():
                print("  → Redirecting to Admin Portal...")
            elif dialog.is_agent():
                print("  → Redirecting to Agent Portal...")
        else:
            print("✗ Login failed")
    else:
        print("Login cancelled")
