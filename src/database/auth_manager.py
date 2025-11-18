"""
Authentication manager for user login and authorization.
Supports both admin and agent users with role-based access.
"""

import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .db_manager import get_db


@dataclass
class User:
    """User data class."""
    id: int
    username: str
    full_name: str
    email: Optional[str]
    role: str  # 'admin' or 'agent'
    is_active: bool
    created_at: str
    last_login: Optional[str]


class AuthManager:
    """Manages user authentication and authorization."""

    def __init__(self):
        self.db = get_db()

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using SHA-256.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        password_hash = self.hash_password(password)

        query = """
            SELECT id, username, full_name, email, role, is_active,
                   created_at, last_login
            FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """

        result = self.db.execute_query(query, (username, password_hash))

        if not result:
            return None

        user_data = result[0]

        # Update last login timestamp
        self._update_last_login(user_data['id'])

        return User(
            id=user_data['id'],
            username=user_data['username'],
            full_name=user_data['full_name'],
            email=user_data['email'],
            role=user_data['role'],
            is_active=bool(user_data['is_active']),
            created_at=user_data['created_at'],
            last_login=user_data['last_login']
        )

    def _update_last_login(self, user_id: int):
        """Update user's last login timestamp."""
        query = """
            UPDATE users
            SET last_login = ?
            WHERE id = ?
        """
        self.db.execute_update(query, (datetime.now().isoformat(), user_id))

    def create_user(self, username: str, password: str, full_name: str,
                   role: str, email: Optional[str] = None) -> int:
        """
        Create a new user.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            full_name: Full name
            role: User role ('admin' or 'agent')
            email: Email address (optional)

        Returns:
            User ID

        Raises:
            ValueError: If username already exists or role is invalid
        """
        # Validate role
        if role not in ('admin', 'agent'):
            raise ValueError(f"Invalid role: {role}. Must be 'admin' or 'agent'")

        # Check if username already exists
        if self.user_exists(username):
            raise ValueError(f"Username '{username}' already exists")

        password_hash = self.hash_password(password)

        query = """
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
        """

        user_id = self.db.execute_insert(
            query,
            (username, password_hash, full_name, email, role)
        )

        return user_id

    def user_exists(self, username: str) -> bool:
        """
        Check if username exists.

        Args:
            username: Username to check

        Returns:
            True if username exists
        """
        query = "SELECT COUNT(*) as count FROM users WHERE username = ?"
        result = self.db.execute_query(query, (username,))
        return result[0]['count'] > 0

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        query = """
            SELECT id, username, full_name, email, role, is_active,
                   created_at, last_login
            FROM users
            WHERE id = ?
        """

        result = self.db.execute_query(query, (user_id,))

        if not result:
            return None

        user_data = result[0]
        return User(
            id=user_data['id'],
            username=user_data['username'],
            full_name=user_data['full_name'],
            email=user_data['email'],
            role=user_data['role'],
            is_active=bool(user_data['is_active']),
            created_at=user_data['created_at'],
            last_login=user_data['last_login']
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User object or None
        """
        query = """
            SELECT id, username, full_name, email, role, is_active,
                   created_at, last_login
            FROM users
            WHERE username = ?
        """

        result = self.db.execute_query(query, (username,))

        if not result:
            return None

        user_data = result[0]
        return User(
            id=user_data['id'],
            username=user_data['username'],
            full_name=user_data['full_name'],
            email=user_data['email'],
            role=user_data['role'],
            is_active=bool(user_data['is_active']),
            created_at=user_data['created_at'],
            last_login=user_data['last_login']
        )

    def update_password(self, user_id: int, new_password: str):
        """
        Update user password.

        Args:
            user_id: User ID
            new_password: New plain text password (will be hashed)
        """
        password_hash = self.hash_password(new_password)

        query = "UPDATE users SET password_hash = ? WHERE id = ?"
        self.db.execute_update(query, (password_hash, user_id))

    def deactivate_user(self, user_id: int):
        """
        Deactivate user account.

        Args:
            user_id: User ID
        """
        query = "UPDATE users SET is_active = 0 WHERE id = ?"
        self.db.execute_update(query, (user_id,))

    def activate_user(self, user_id: int):
        """
        Activate user account.

        Args:
            user_id: User ID
        """
        query = "UPDATE users SET is_active = 1 WHERE id = ?"
        self.db.execute_update(query, (user_id,))

    def get_all_users(self, role: Optional[str] = None) -> list[User]:
        """
        Get all users, optionally filtered by role.

        Args:
            role: Optional role filter ('admin' or 'agent')

        Returns:
            List of User objects
        """
        if role:
            if role not in ('admin', 'agent'):
                raise ValueError(f"Invalid role: {role}")
            query = """
                SELECT id, username, full_name, email, role, is_active,
                       created_at, last_login
                FROM users
                WHERE role = ?
                ORDER BY username
            """
            result = self.db.execute_query(query, (role,))
        else:
            query = """
                SELECT id, username, full_name, email, role, is_active,
                       created_at, last_login
                FROM users
                ORDER BY username
            """
            result = self.db.execute_query(query)

        return [
            User(
                id=row['id'],
                username=row['username'],
                full_name=row['full_name'],
                email=row['email'],
                role=row['role'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                last_login=row['last_login']
            )
            for row in result
        ]

    def is_admin(self, user: User) -> bool:
        """
        Check if user is an admin.

        Args:
            user: User object

        Returns:
            True if user is admin
        """
        return user.role == 'admin'

    def is_agent(self, user: User) -> bool:
        """
        Check if user is an agent.

        Args:
            user: User object

        Returns:
            True if user is agent
        """
        return user.role == 'agent'


def create_default_admin(username: str = "admin", password: str = "admin123",
                        full_name: str = "Administrator"):
    """
    Create default admin user if no users exist.

    Args:
        username: Admin username (default: 'admin')
        password: Admin password (default: 'admin123')
        full_name: Admin full name

    Returns:
        User ID if created, None if users already exist
    """
    auth_manager = AuthManager()

    # Check if any users exist
    users = auth_manager.get_all_users()
    if users:
        return None

    # Create default admin
    user_id = auth_manager.create_user(
        username=username,
        password=password,
        full_name=full_name,
        role='admin',
        email=None
    )

    return user_id
