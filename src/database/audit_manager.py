"""
Audit manager for tracking rate changes.
All rate modifications are logged for compliance and troubleshooting.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .db_manager import get_db


@dataclass
class RateChange:
    """Rate change audit record."""
    id: int
    timestamp: str
    user_id: int
    user_name: str
    table_name: str
    state_code: str
    column_name: str
    old_value: Optional[float]
    new_value: Optional[float]
    change_type: str
    notes: Optional[str]


class AuditManager:
    """Manages audit trail for rate changes."""

    def __init__(self):
        self.db = get_db()

    def log_rate_change(self, user_id: int, user_name: str,
                       table_name: str, state_code: str,
                       column_name: str, old_value: Optional[float],
                       new_value: Optional[float], change_type: str,
                       notes: Optional[str] = None) -> int:
        """
        Log a rate change to the audit trail.

        Args:
            user_id: ID of user making the change
            user_name: Name of user making the change
            table_name: Name of rate table being modified
            state_code: State code
            column_name: Column/rate being changed
            old_value: Previous rate value
            new_value: New rate value
            change_type: Type of change ('update', 'import', 'bulk_update')
            notes: Optional notes about the change

        Returns:
            Audit log entry ID
        """
        query = """
            INSERT INTO rate_change_log (
                user_id, user_name, table_name, state_code,
                column_name, old_value, new_value, change_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        log_id = self.db.execute_insert(
            query,
            (user_id, user_name, table_name, state_code,
             column_name, old_value, new_value, change_type, notes)
        )

        return log_id

    def log_bulk_changes(self, user_id: int, user_name: str,
                        changes: List[Dict[str, Any]],
                        change_type: str = 'bulk_update',
                        notes: Optional[str] = None):
        """
        Log multiple rate changes at once (bulk operation).

        Args:
            user_id: ID of user making the changes
            user_name: Name of user making the changes
            changes: List of change dictionaries with keys:
                    - table_name
                    - state_code
                    - column_name
                    - old_value
                    - new_value
            change_type: Type of change (default: 'bulk_update')
            notes: Optional notes about the bulk change
        """
        for change in changes:
            self.log_rate_change(
                user_id=user_id,
                user_name=user_name,
                table_name=change['table_name'],
                state_code=change['state_code'],
                column_name=change['column_name'],
                old_value=change.get('old_value'),
                new_value=change.get('new_value'),
                change_type=change_type,
                notes=notes
            )

    def get_changes(self, start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   state_code: Optional[str] = None,
                   table_name: Optional[str] = None,
                   user_id: Optional[int] = None,
                   limit: int = 100,
                   offset: int = 0) -> List[RateChange]:
        """
        Get rate changes with optional filters.

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            state_code: State code filter
            table_name: Table name filter
            user_id: User ID filter
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)

        Returns:
            List of RateChange objects
        """
        query = """
            SELECT id, timestamp, user_id, user_name, table_name,
                   state_code, column_name, old_value, new_value,
                   change_type, notes
            FROM rate_change_log
            WHERE 1=1
        """

        params = []

        # Apply filters
        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date)

        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date)

        if state_code:
            query += " AND state_code = ?"
            params.append(state_code)

        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        # Order by most recent first
        query += " ORDER BY timestamp DESC"

        # Add pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        result = self.db.execute_query(query, tuple(params))

        return [
            RateChange(
                id=row['id'],
                timestamp=row['timestamp'],
                user_id=row['user_id'],
                user_name=row['user_name'],
                table_name=row['table_name'],
                state_code=row['state_code'],
                column_name=row['column_name'],
                old_value=row['old_value'],
                new_value=row['new_value'],
                change_type=row['change_type'],
                notes=row['notes']
            )
            for row in result
        ]

    def get_change_count(self, start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        state_code: Optional[str] = None,
                        table_name: Optional[str] = None,
                        user_id: Optional[int] = None) -> int:
        """
        Get total count of changes matching filters.

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            state_code: State code filter
            table_name: Table name filter
            user_id: User ID filter

        Returns:
            Total count of matching records
        """
        query = "SELECT COUNT(*) as count FROM rate_change_log WHERE 1=1"
        params = []

        # Apply filters (same as get_changes)
        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date)

        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date)

        if state_code:
            query += " AND state_code = ?"
            params.append(state_code)

        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        result = self.db.execute_query(query, tuple(params))
        return result[0]['count']

    def get_state_change_history(self, state_code: str,
                                 table_name: str,
                                 column_name: str,
                                 limit: int = 50) -> List[RateChange]:
        """
        Get change history for a specific state/table/column.

        Args:
            state_code: State code
            table_name: Table name
            column_name: Column name
            limit: Maximum number of records

        Returns:
            List of RateChange objects
        """
        query = """
            SELECT id, timestamp, user_id, user_name, table_name,
                   state_code, column_name, old_value, new_value,
                   change_type, notes
            FROM rate_change_log
            WHERE state_code = ? AND table_name = ? AND column_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """

        result = self.db.execute_query(
            query,
            (state_code, table_name, column_name, limit)
        )

        return [
            RateChange(
                id=row['id'],
                timestamp=row['timestamp'],
                user_id=row['user_id'],
                user_name=row['user_name'],
                table_name=row['table_name'],
                state_code=row['state_code'],
                column_name=row['column_name'],
                old_value=row['old_value'],
                new_value=row['new_value'],
                change_type=row['change_type'],
                notes=row['notes']
            )
            for row in result
        ]

    def get_recent_changes(self, limit: int = 20) -> List[RateChange]:
        """
        Get most recent rate changes.

        Args:
            limit: Number of recent changes to retrieve

        Returns:
            List of RateChange objects
        """
        return self.get_changes(limit=limit, offset=0)

    def get_user_changes(self, user_id: int,
                        limit: int = 100) -> List[RateChange]:
        """
        Get all changes made by a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of records

        Returns:
            List of RateChange objects
        """
        return self.get_changes(user_id=user_id, limit=limit)

    def export_to_dict(self, changes: List[RateChange]) -> List[Dict[str, Any]]:
        """
        Export changes to dictionary format for CSV export.

        Args:
            changes: List of RateChange objects

        Returns:
            List of dictionaries suitable for CSV export
        """
        return [
            {
                'Timestamp': change.timestamp,
                'User': change.user_name,
                'Table': change.table_name,
                'State': change.state_code,
                'Column': change.column_name,
                'Old Value': f"{change.old_value:.2f}%" if change.old_value is not None else "N/A",
                'New Value': f"{change.new_value:.2f}%" if change.new_value is not None else "N/A",
                'Change Type': change.change_type,
                'Notes': change.notes or ''
            }
            for change in changes
        ]

    def delete_old_changes(self, days: int = 365) -> int:
        """
        Delete audit records older than specified days.

        Args:
            days: Number of days to retain (default: 365)

        Returns:
            Number of records deleted

        Note: This should only be called as part of a data retention policy
        """
        query = """
            DELETE FROM rate_change_log
            WHERE DATE(timestamp) < DATE('now', ?)
        """

        # SQLite uses negative days for date subtraction
        cursor = self.db.get_connection().cursor()
        cursor.execute(query, (f'-{days} days',))
        deleted = cursor.rowcount
        self.db.get_connection().commit()

        return deleted
