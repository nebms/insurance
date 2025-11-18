# Authentication Guide

## Overview

The CSI Pivot Quote application now includes a unified authentication system with role-based access control.

## User Roles

### Agent
- Access to quote application only
- Can create quotes, manage customers, view quote history
- Default interface after login

### Admin
- Access to both quote application AND admin portal
- Can manage rate tables, view audit logs
- Has "Admin" menu with additional options

## Default Credentials

**Username:** `admin`
**Password:** `admin123`

⚠️ **IMPORTANT:** Change this password immediately after first login!

## First Run

On first run, the application will automatically:
1. Initialize the database
2. Load default states and sample rates
3. Create the default admin user (if no users exist)

## User Management

### Creating New Users

Use the command-line utility to manage users:

```bash
# List all users
python src/database/init_admin.py list

# Create new admin user
python src/database/init_admin.py create-admin username password "Full Name" --email email@example.com

# Create new agent user
python src/database/init_admin.py create-agent username password "Full Name" --email email@example.com

# Check if users exist
python src/database/init_admin.py check

# Initialize default admin (only if no users exist)
python src/database/init_admin.py init
```

### Examples

```bash
# Create an admin user
python src/database/init_admin.py create-admin jsmith "secure123" "John Smith" --email john@example.com

# Create an agent user
python src/database/init_admin.py create-agent mjones "pass456" "Mary Jones" --email mary@example.com
```

## Login Flow

1. Application starts
2. Login dialog appears
3. Enter username and password
4. Click "Login"

### For Agents:
- Main quote application window opens
- Can create quotes, manage customers, view history

### For Admins:
- Main quote application window opens
- Additional "Admin" menu appears with:
  - **Admin Portal** - Access rate management
  - **Switch User** - Logout and login as different user

## Admin Portal Features

Admins can access the admin portal from the "Admin" menu:

### Current Features (Phase 2):
- Tabbed interface for all rate tables
- Import rates from CSV
- View change history (placeholder)

### Coming Features:
- **Phase 3:** Rate viewer and editor
- **Phase 4:** Bulk update operations
- **Phase 5:** Export and audit log viewer
- **Phase 6:** Full integration and testing

## Security Features

### Password Security
- Passwords hashed using SHA-256
- No plain text password storage
- Session tracking with last login timestamps

### Login Protection
- Maximum 3 login attempts
- Account lockout after failed attempts
- Active/inactive user status

### Audit Trail
- All rate changes logged
- User ID and username tracked
- Timestamp and change details recorded
- Cannot delete audit records

## Troubleshooting

### "No users found"
Run the initialization command:
```bash
python src/database/init_admin.py init
```

### "Invalid username or password"
- Check credentials are correct
- Verify user account is active
- Contact admin to reset password

### "Maximum login attempts exceeded"
- Application will close after 3 failed attempts
- Restart application to try again
- Verify credentials with admin

## Password Management

### Changing Passwords

Currently, passwords must be changed via database directly or by recreating the user.

**Future Enhancement:** Add password change functionality in the UI.

## Session Management

- Users remain logged in until they logout or close the application
- Admins can switch users without closing the application
- Last login timestamp tracked for all users

## Best Practices

1. **Change default admin password immediately**
2. **Create individual accounts for each user**
3. **Don't share passwords**
4. **Use strong passwords** (8+ characters, mix of letters/numbers)
5. **Review audit logs regularly** (admin feature)
6. **Deactivate user accounts** when employees leave

## Database Location

User data stored in: `data/csi_quotes.db`

**Tables:**
- `users` - User accounts and authentication
- `rate_change_log` - Audit trail for rate changes

## Support

For issues or questions:
1. Check this guide
2. Review audit logs (admins)
3. Contact system administrator
