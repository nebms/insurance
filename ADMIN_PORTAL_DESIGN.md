# Admin Rate Management Portal - Design Document

**Project:** CSI Pivot Quote Insurance Application
**Feature:** Admin Portal for Rate Management
**Priority:** P1 - HIGH (User Requirement #1)
**Estimated Time:** 8-12 hours
**Status:** Design Phase

---

## Overview

The Admin Portal provides a secure interface for authorized users to:
- View current insurance rates across all states
- Edit individual rates or bulk update
- Import rates from CSV files (already implemented)
- View rate change history and audit trail
- Export rates to CSV for backup/review

---

## User Stories

### US-1: View Current Rates
**As an** admin user
**I want to** view all current insurance rates in a searchable table
**So that** I can verify rates are correct and up-to-date

**Acceptance Criteria:**
- Display all 4 rate table types in separate tabs
- Show state code, effective date, and all rate columns
- Support filtering by state
- Support sorting by any column
- Display row count and last updated timestamp

### US-2: Edit Individual Rates
**As an** admin user
**I want to** edit individual rate values
**So that** I can correct errors or update specific rates

**Acceptance Criteria:**
- Double-click cell to edit rate value
- Validate rate is 0-100%
- Show confirmation before saving
- Log change to audit trail
- Show success/error message

### US-3: Bulk Update Rates
**As an** admin user
**I want to** apply percentage increases/decreases to multiple rates
**So that** I can efficiently update rates across states

**Acceptance Criteria:**
- Select multiple rows or "all states"
- Enter percentage adjustment (+/- X%)
- Preview changes before applying
- Confirm bulk update
- Log all changes to audit trail

### US-4: Import Rates from CSV
**As an** admin user
**I want to** import rates from CSV files
**So that** I can update rates from external systems

**Status:** ✅ Already implemented (rate_import_dialog.py)
**Integration:** Link from admin portal

### US-5: Export Rates to CSV
**As an** admin user
**I want to** export current rates to CSV
**So that** I can backup rates or review in Excel

**Acceptance Criteria:**
- Export button for each rate table type
- Generate CSV with all columns
- Include header row with column names
- Save to data/exports/ directory
- Show success message with file path

### US-6: View Rate Change History
**As an** admin user
**I want to** see when rates were changed and by whom
**So that** I can track rate adjustments and troubleshoot issues

**Acceptance Criteria:**
- Display change log with: timestamp, user, table, state, old value, new value
- Filter by date range, state, or table type
- Export audit log to CSV
- Paginated results (100 per page)

---

## Architecture

### Database Changes

**New Table: `rate_change_log`**
```sql
CREATE TABLE IF NOT EXISTS rate_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    user_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    state_code TEXT NOT NULL,
    column_name TEXT NOT NULL,
    old_value REAL,
    new_value REAL,
    change_type TEXT,  -- 'update', 'import', 'bulk_update'
    notes TEXT
);

CREATE INDEX idx_rate_changes_timestamp ON rate_change_log(timestamp);
CREATE INDEX idx_rate_changes_state ON rate_change_log(state_code);
CREATE INDEX idx_rate_changes_table ON rate_change_log(table_name);
```

### File Structure

```
src/
├── ui/
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── admin_portal.py          # Main admin portal widget
│   │   ├── rate_viewer.py           # Rate table viewer/editor
│   │   ├── rate_editor_dialog.py    # Edit single rate dialog
│   │   ├── bulk_update_dialog.py    # Bulk update dialog
│   │   ├── audit_log_viewer.py      # Change history viewer
│   │   └── auth_dialog.py           # Admin login dialog
│   ├── main_window.py                # Add "Admin" menu
│   └── ...
├── database/
│   ├── schema.py                     # Add rate_change_log table
│   └── audit_manager.py              # NEW: Audit trail operations
└── ...
```

---

## UI Components

### 1. Main Admin Portal (admin_portal.py)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Admin Portal - Rate Management               🔒 Admin Mode  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ [Pivot <20] [Pivot 20-34] [Pivot 35+] [Ancillary]    │   │
│ ├───────────────────────────────────────────────────────┤   │
│ │                                                         │   │
│ │  Filter by State: [________v]    [Search] [Clear]     │   │
│ │                                                         │   │
│ │  ┌──────────────────────────────────────────────────┐ │   │
│ │  │ State │ Date       │ Rate 1 │ Rate 2 │ ... │     │ │   │
│ │  ├──────────────────────────────────────────────────┤ │   │
│ │  │ NE    │ 2025-01-01 │  2.50% │  2.75% │ ... │     │ │   │
│ │  │ TX    │ 2025-01-01 │  2.60% │  2.80% │ ... │     │ │   │
│ │  │ ...                                              │ │   │
│ │  └──────────────────────────────────────────────────┘ │   │
│ │                                                         │   │
│ │  [Edit Selected] [Bulk Update] [Import CSV] [Export]  │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ [View Change History] [Close]                                │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Tab interface for 4 rate table types
- Searchable/filterable table
- Editable cells (double-click to edit)
- Action buttons for bulk operations
- Status bar showing row count and last update

### 2. Edit Rate Dialog (rate_editor_dialog.py)

**Layout:**
```
┌─────────────────────────────────────┐
│ Edit Rate - Pivot Rates Under 20    │
├─────────────────────────────────────┤
│                                     │
│ State:           NE                 │
│ Column:          standard_500_no_me │
│ Current Rate:    2.50%              │
│                                     │
│ New Rate:        [2.75___] %        │
│                                     │
│ Effective Date:  [2025-01-01_]      │
│                                     │
│ Notes:                              │
│ ┌─────────────────────────────────┐ │
│ │ Rate increase for 2025         │ │
│ └─────────────────────────────────┘ │
│                                     │
│         [Cancel] [Save Change]      │
└─────────────────────────────────────┘
```

**Validation:**
- Rate must be 0-100%
- Effective date cannot be in past
- Notes optional but recommended
- Confirm significant changes (>20% difference)

### 3. Bulk Update Dialog (bulk_update_dialog.py)

**Layout:**
```
┌─────────────────────────────────────────────┐
│ Bulk Rate Update                            │
├─────────────────────────────────────────────┤
│                                             │
│ Apply to:                                   │
│ ○ Selected states (3 selected)              │
│ ● All states (50 states)                    │
│                                             │
│ Adjustment Type:                            │
│ ● Percentage increase/decrease              │
│ ○ Set fixed rate                            │
│                                             │
│ Percentage: [+5.0___] %                     │
│                                             │
│ Effective Date: [2025-01-01_]               │
│                                             │
│ Preview Changes:                            │
│ ┌─────────────────────────────────────────┐ │
│ │ NE: 2.50% → 2.63% (+0.13%)             │ │
│ │ TX: 2.60% → 2.73% (+0.13%)             │ │
│ │ ... (47 more)                          │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Notes:                                      │
│ ┌─────────────────────────────────────────┐ │
│ │ Annual rate adjustment for 2025        │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ⚠ This will update 50 rate values          │
│                                             │
│         [Cancel] [Apply Changes]            │
└─────────────────────────────────────────────┘
```

**Features:**
- Preview all changes before applying
- Warning for large number of changes
- Validation for reasonable adjustments
- Required notes for bulk updates

### 4. Audit Log Viewer (audit_log_viewer.py)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Rate Change History                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Filters:                                                     │
│ Date Range: [2025-01-01_] to [2025-12-31_]                 │
│ State:      [All States  v]                                 │
│ Table:      [All Tables  v]                                 │
│             [Apply Filter] [Clear]                          │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Time       │ User  │ Table  │ State │ Change │ Notes  │  │
│ ├────────────────────────────────────────────────────────┤  │
│ │ 2025-01-15 │ Admin │ Pivot  │ NE    │ 2.50→  │ Annual │  │
│ │ 14:30:25   │       │ <20    │       │ 2.63%  │ adj.   │  │
│ ├────────────────────────────────────────────────────────┤  │
│ │ 2025-01-10 │ Admin │ Anc.   │ TX    │ 3.00→  │ Import │  │
│ │ 09:15:42   │       │        │       │ 3.10%  │ from   │  │
│ │            │       │        │       │        │ CSV    │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Showing 1-100 of 523 changes                                │
│ [< Previous] [1] [2] [3] [4] [5] [Next >]                  │
│                                                              │
│ [Export to CSV] [Close]                                     │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Filterable by date, state, table
- Paginated results
- Export to CSV
- Show change details

### 5. Admin Login Dialog (auth_dialog.py)

**Layout:**
```
┌─────────────────────────────────┐
│ Admin Access Required           │
├─────────────────────────────────┤
│                                 │
│ The admin portal is protected.  │
│ Please enter admin password:    │
│                                 │
│ Password: [**********_]         │
│                                 │
│ [Cancel] [Login]                │
└─────────────────────────────────┘
```

**Security:**
- Password stored as hash in config file
- Max 3 login attempts
- Lock out for 5 minutes after failed attempts
- Optional: Username + password

---

## Configuration

**New File: `config/admin_config.json`**
```json
{
  "admin_password_hash": "sha256_hash_here",
  "session_timeout_minutes": 30,
  "max_login_attempts": 3,
  "lockout_duration_minutes": 5,
  "audit_retention_days": 365,
  "export_directory": "data/exports"
}
```

---

## Implementation Plan

### Phase 1: Database & Core (2 hours)
1. Create `rate_change_log` table in schema.py
2. Create `audit_manager.py` for audit operations
3. Add configuration file support
4. Implement password hashing/verification

### Phase 2: Admin Portal Shell (2 hours)
5. Create `admin_portal.py` with tab interface
6. Add "Admin" menu to main_window.py
7. Create `auth_dialog.py` for login
8. Wire up authentication

### Phase 3: Rate Viewer/Editor (3 hours)
9. Create `rate_viewer.py` with editable table
10. Implement cell editing with validation
11. Create `rate_editor_dialog.py` for detailed editing
12. Integrate audit logging

### Phase 4: Bulk Operations (2 hours)
13. Create `bulk_update_dialog.py`
14. Implement percentage adjustments
15. Add preview functionality
16. Integrate audit logging

### Phase 5: Export & Audit (1.5 hours)
17. Implement CSV export for each table type
18. Create `audit_log_viewer.py`
19. Add filtering and pagination
20. Implement audit log CSV export

### Phase 6: Integration & Testing (1.5 hours)
21. Connect all components
22. Test authentication flow
23. Test rate editing and validation
24. Test bulk updates
25. Test audit trail
26. Documentation

**Total Estimated Time: 12 hours**

---

## Security Considerations

1. **Password Protection:**
   - Use SHA-256 hashing
   - No plaintext passwords
   - Session timeout after 30 minutes

2. **Audit Trail:**
   - Log ALL rate changes
   - Cannot delete audit records
   - Include timestamp and user

3. **Validation:**
   - All rate changes validated (0-100%)
   - Confirmation for bulk changes
   - Preview before applying

4. **Access Control:**
   - Admin portal separate from main app
   - Login required
   - Lockout after failed attempts

---

## Future Enhancements (Out of Scope)

- Multi-user support with different permission levels
- Email notifications for rate changes
- Rate approval workflow
- Scheduled rate updates
- Database backup/restore from admin portal
- Rate comparison across time periods
- Graphical rate trends

---

## Testing Checklist

- [ ] Admin login with correct password succeeds
- [ ] Admin login with wrong password fails
- [ ] Lockout after 3 failed attempts works
- [ ] Session timeout after 30 minutes
- [ ] Can view all 4 rate table types
- [ ] Can edit individual rate
- [ ] Rate validation (0-100%) works
- [ ] Bulk update previews correctly
- [ ] Bulk update applies to all selected states
- [ ] Changes logged to audit trail
- [ ] Can export rates to CSV
- [ ] Can view audit log with filters
- [ ] Can export audit log to CSV
- [ ] Integration with existing rate import works

---

## Questions for User

1. **Password Setup:** Should I use a simple password (stored in config) or username + password?
2. **User Tracking:** For audit log "user_name" - should this be a fixed "Admin" or allow multiple admin users?
3. **Effective Dates:** When editing rates, should changes be immediate or support future effective dates?
4. **Confirmation:** Should significant rate changes (e.g., >20% increase) require additional confirmation?
5. **Priority:** Would you like me to start implementing this now, or review the design first?

---

**Next Step:** Awaiting your approval to proceed with implementation.
