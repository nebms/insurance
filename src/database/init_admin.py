"""
Database initialization utility for admin users.
Creates default admin user if no users exist.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.auth_manager import AuthManager, create_default_admin
from database.db_manager import get_db


def check_users_exist() -> bool:
    """
    Check if any users exist in the database.

    Returns:
        True if users exist, False otherwise
    """
    auth_manager = AuthManager()
    users = auth_manager.get_all_users()
    return len(users) > 0


def initialize_default_admin():
    """
    Initialize default admin user if no users exist.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        if check_users_exist():
            return False, "Users already exist. No default admin created."

        user_id = create_default_admin(
            username="admin",
            password="admin123",
            full_name="Administrator"
        )

        if user_id:
            return True, f"✓ Default admin user created (ID: {user_id})\n" \
                        f"  Username: admin\n" \
                        f"  Password: admin123\n" \
                        f"  ⚠ CHANGE THIS PASSWORD IMMEDIATELY!"
        else:
            return False, "Failed to create default admin user"

    except Exception as e:
        return False, f"Error initializing admin: {str(e)}"


def create_admin_user(username: str, password: str, full_name: str, email: str = None):
    """
    Create a new admin user.

    Args:
        username: Username
        password: Password
        full_name: Full name
        email: Email address (optional)

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        auth_manager = AuthManager()

        user_id = auth_manager.create_user(
            username=username,
            password=password,
            full_name=full_name,
            role='admin',
            email=email
        )

        return True, f"✓ Admin user created (ID: {user_id})\n" \
                    f"  Username: {username}\n" \
                    f"  Full Name: {full_name}"

    except ValueError as e:
        return False, f"Validation error: {str(e)}"
    except Exception as e:
        return False, f"Error creating admin: {str(e)}"


def create_agent_user(username: str, password: str, full_name: str, email: str = None):
    """
    Create a new agent user.

    Args:
        username: Username
        password: Password
        full_name: Full name
        email: Email address (optional)

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        auth_manager = AuthManager()

        user_id = auth_manager.create_user(
            username=username,
            password=password,
            full_name=full_name,
            role='agent',
            email=email
        )

        return True, f"✓ Agent user created (ID: {user_id})\n" \
                    f"  Username: {username}\n" \
                    f"  Full Name: {full_name}"

    except ValueError as e:
        return False, f"Validation error: {str(e)}"
    except Exception as e:
        return False, f"Error creating agent: {str(e)}"


def list_all_users():
    """
    List all users in the system.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        auth_manager = AuthManager()
        users = auth_manager.get_all_users()

        if not users:
            return True, "No users found in database."

        message = f"Found {len(users)} user(s):\n\n"

        for user in users:
            active_status = "ACTIVE" if user.is_active else "INACTIVE"
            last_login = user.last_login or "Never"

            message += f"  [{user.role.upper()}] {user.username}\n"
            message += f"    Name: {user.full_name}\n"
            message += f"    Email: {user.email or 'N/A'}\n"
            message += f"    Status: {active_status}\n"
            message += f"    Created: {user.created_at}\n"
            message += f"    Last Login: {last_login}\n\n"

        return True, message

    except Exception as e:
        return False, f"Error listing users: {str(e)}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database user management utility")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check if users exist')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize default admin user')

    # Create admin command
    create_admin_parser = subparsers.add_parser('create-admin', help='Create new admin user')
    create_admin_parser.add_argument('username', help='Username')
    create_admin_parser.add_argument('password', help='Password')
    create_admin_parser.add_argument('fullname', help='Full name')
    create_admin_parser.add_argument('--email', help='Email address', default=None)

    # Create agent command
    create_agent_parser = subparsers.add_parser('create-agent', help='Create new agent user')
    create_agent_parser.add_argument('username', help='Username')
    create_agent_parser.add_argument('password', help='Password')
    create_agent_parser.add_argument('fullname', help='Full name')
    create_agent_parser.add_argument('--email', help='Email address', default=None)

    # List command
    list_parser = subparsers.add_parser('list', help='List all users')

    args = parser.parse_args()

    # Initialize database
    db = get_db()

    if args.command == 'check':
        if check_users_exist():
            print("✓ Users exist in database")
        else:
            print("⚠ No users found in database")
            print("Run 'python init_admin.py init' to create default admin user")

    elif args.command == 'init':
        success, message = initialize_default_admin()
        print(message)
        sys.exit(0 if success else 1)

    elif args.command == 'create-admin':
        success, message = create_admin_user(
            args.username,
            args.password,
            args.fullname,
            args.email
        )
        print(message)
        sys.exit(0 if success else 1)

    elif args.command == 'create-agent':
        success, message = create_agent_user(
            args.username,
            args.password,
            args.fullname,
            args.email
        )
        print(message)
        sys.exit(0 if success else 1)

    elif args.command == 'list':
        success, message = list_all_users()
        print(message)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)
