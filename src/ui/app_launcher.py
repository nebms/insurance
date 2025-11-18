"""
Application launcher with authentication.
Routes users to appropriate interface based on role.
"""

from PyQt6.QtWidgets import QApplication, QMessageBox
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.auth_manager import User
from database.init_admin import check_users_exist, initialize_default_admin
from ui.admin.login_dialog import LoginDialog
from ui.main_window import MainWindow
from ui.admin.admin_portal import AdminPortal


class Application:
    """Main application controller with authentication."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.current_user: Optional[User] = None
        self.main_window: Optional[MainWindow] = None
        self.admin_portal: Optional[AdminPortal] = None

    def run(self) -> int:
        """
        Run application with authentication.

        Returns:
            Exit code
        """
        # Check if users exist, create default admin if needed
        if not check_users_exist():
            success, message = initialize_default_admin()
            if not success:
                QMessageBox.critical(
                    None,
                    "Initialization Error",
                    f"Failed to initialize default admin user:\n{message}"
                )
                return 1

        # Show login dialog
        if not self.show_login():
            return 0  # User cancelled login

        # Route based on user role
        if self.current_user.role == 'admin':
            # Admins see main window with admin menu
            self.show_main_window_with_admin_access()
        else:
            # Agents see main window only
            self.show_main_window()

        return self.app.exec()

    def show_login(self) -> bool:
        """
        Show login dialog.

        Returns:
            True if login successful, False if cancelled
        """
        login_dialog = LoginDialog()

        if login_dialog.exec():
            self.current_user = login_dialog.get_authenticated_user()
            return self.current_user is not None

        return False

    def show_main_window(self):
        """Show main application window (quote application)."""
        self.main_window = MainWindow()
        self.main_window.current_user = self.current_user
        self.main_window.app_launcher = self

        # Update window title with user info
        self.main_window.setWindowTitle(
            f"CSI Pivot Quote - {self.current_user.full_name}"
        )

        self.main_window.show()

    def show_main_window_with_admin_access(self):
        """Show main application window with admin menu."""
        self.show_main_window()

        # Add Admin menu
        admin_menu = self.main_window.menuBar().addMenu("&Admin")

        from PyQt6.QtGui import QAction

        admin_portal_action = QAction("&Admin Portal", self.main_window)
        admin_portal_action.triggered.connect(self.show_admin_portal)
        admin_menu.addAction(admin_portal_action)

        admin_menu.addSeparator()

        switch_user_action = QAction("&Switch User", self.main_window)
        switch_user_action.triggered.connect(self.switch_user)
        admin_menu.addAction(switch_user_action)

    def show_admin_portal(self):
        """Show admin portal window."""
        if self.current_user.role != 'admin':
            QMessageBox.warning(
                self.main_window,
                "Access Denied",
                "Admin portal is only accessible to administrators."
            )
            return

        # Create or show admin portal
        if self.admin_portal is None:
            self.admin_portal = AdminPortal(self.current_user)
            self.admin_portal.setWindowTitle("CSI Pivot Quote - Admin Portal")
            self.admin_portal.resize(900, 600)
            self.admin_portal.parent = self

        self.admin_portal.show()
        self.admin_portal.raise_()
        self.admin_portal.activateWindow()

    def switch_user(self):
        """Switch to different user (re-login)."""
        reply = QMessageBox.question(
            self.main_window,
            "Switch User",
            "Are you sure you want to switch users?\n\n"
            "This will close all open windows and return to the login screen.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Close all windows
            if self.admin_portal:
                self.admin_portal.close()
                self.admin_portal = None

            if self.main_window:
                self.main_window.close()
                self.main_window = None

            # Show login again
            if self.show_login():
                if self.current_user.role == 'admin':
                    self.show_main_window_with_admin_access()
                else:
                    self.show_main_window()
            else:
                # User cancelled, exit application
                self.app.quit()


def main():
    """Main entry point."""
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
