"""
Renewal data model and repository.
Tracks policy renewals, reminders, and renewal quote generation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from database.db_manager import get_db


class Renewal:
    """Renewal data model."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.original_quote_id = kwargs.get('original_quote_id')
        self.renewal_quote_id = kwargs.get('renewal_quote_id')

        # Renewal timeline
        self.policy_end_date = kwargs.get('policy_end_date', '')
        self.renewal_due_date = kwargs.get('renewal_due_date', '')

        # Renewal status
        self.status = kwargs.get('status', 'pending')

        # Reminder tracking
        self.reminder_90_days_sent = kwargs.get('reminder_90_days_sent', 0)
        self.reminder_90_days_date = kwargs.get('reminder_90_days_date')
        self.reminder_60_days_sent = kwargs.get('reminder_60_days_sent', 0)
        self.reminder_60_days_date = kwargs.get('reminder_60_days_date')
        self.reminder_30_days_sent = kwargs.get('reminder_30_days_sent', 0)
        self.reminder_30_days_date = kwargs.get('reminder_30_days_date')
        self.reminder_final_sent = kwargs.get('reminder_final_sent', 0)
        self.reminder_final_date = kwargs.get('reminder_final_date')

        # Renewal quote details
        self.renewal_generated_date = kwargs.get('renewal_generated_date')
        self.renewal_sent_date = kwargs.get('renewal_sent_date')
        self.renewal_premium = kwargs.get('renewal_premium')
        self.premium_change_percent = kwargs.get('premium_change_percent')

        # Outcome tracking
        self.outcome_date = kwargs.get('outcome_date')
        self.outcome_notes = kwargs.get('outcome_notes', '')
        self.declined_reason = kwargs.get('declined_reason', '')

        # Metadata
        self.created_at = kwargs.get('created_at', '')
        self.updated_at = kwargs.get('updated_at', '')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Renewal':
        """Create Renewal from dictionary."""
        return cls(**{k: v for k, v in data.items() if v is not None})

    def to_dict(self) -> Dict[str, Any]:
        """Convert Renewal to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def calculate_days_until_expiration(self) -> int:
        """Calculate days until policy expiration."""
        if not self.policy_end_date:
            return -1

        try:
            end_date = datetime.strptime(self.policy_end_date, '%Y-%m-%d').date()
            today = date.today()
            return (end_date - today).days
        except:
            return -1

    def is_reminder_due(self, days_before: int) -> bool:
        """Check if a reminder at specified days before expiration is due."""
        days_until = self.calculate_days_until_expiration()

        # Reminder is due if we're at or past the reminder date
        return days_until <= days_before and days_until > 0

    def get_next_reminder_due(self) -> Optional[tuple]:
        """
        Get the next reminder that needs to be sent.

        Returns:
            Tuple of (days_before, reminder_type) or None
        """
        days_until = self.calculate_days_until_expiration()

        if days_until <= 0:
            return None

        # Check reminders in order from furthest to closest
        if days_until <= 90 and not self.reminder_90_days_sent:
            return (90, '90_days')
        elif days_until <= 60 and not self.reminder_60_days_sent:
            return (60, '60_days')
        elif days_until <= 30 and not self.reminder_30_days_sent:
            return (30, '30_days')
        elif days_until <= 7 and not self.reminder_final_sent:
            return (7, 'final')

        return None


class RenewalRepository:
    """Repository for renewal database operations."""

    def __init__(self):
        self.db = get_db()

    def create(self, renewal: Renewal) -> int:
        """
        Create new renewal tracking record.

        Args:
            renewal: Renewal instance

        Returns:
            Renewal ID
        """
        query = """
        INSERT INTO renewals (
            original_quote_id, renewal_quote_id,
            policy_end_date, renewal_due_date,
            status,
            reminder_90_days_sent, reminder_90_days_date,
            reminder_60_days_sent, reminder_60_days_date,
            reminder_30_days_sent, reminder_30_days_date,
            reminder_final_sent, reminder_final_date,
            renewal_generated_date, renewal_sent_date,
            renewal_premium, premium_change_percent,
            outcome_date, outcome_notes, declined_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            renewal.original_quote_id,
            renewal.renewal_quote_id,
            renewal.policy_end_date,
            renewal.renewal_due_date,
            renewal.status,
            renewal.reminder_90_days_sent,
            renewal.reminder_90_days_date,
            renewal.reminder_60_days_sent,
            renewal.reminder_60_days_date,
            renewal.reminder_30_days_sent,
            renewal.reminder_30_days_date,
            renewal.reminder_final_sent,
            renewal.reminder_final_date,
            renewal.renewal_generated_date,
            renewal.renewal_sent_date,
            renewal.renewal_premium,
            renewal.premium_change_percent,
            renewal.outcome_date,
            renewal.outcome_notes,
            renewal.declined_reason
        )

        return self.db.execute_insert(query, params)

    def get_by_id(self, renewal_id: int) -> Optional[Renewal]:
        """
        Get renewal by ID.

        Args:
            renewal_id: Renewal ID

        Returns:
            Renewal instance or None
        """
        query = "SELECT * FROM renewals WHERE id = ?"
        results = self.db.execute_query(query, (renewal_id,))

        if results:
            return Renewal.from_dict(dict(results[0]))
        return None

    def get_by_original_quote(self, quote_id: int) -> Optional[Renewal]:
        """
        Get renewal by original quote ID.

        Args:
            quote_id: Original quote ID

        Returns:
            Renewal instance or None
        """
        query = "SELECT * FROM renewals WHERE original_quote_id = ? ORDER BY created_at DESC LIMIT 1"
        results = self.db.execute_query(query, (quote_id,))

        if results:
            return Renewal.from_dict(dict(results[0]))
        return None

    def get_all(self, status: Optional[str] = None, limit: int = 100) -> List[Renewal]:
        """
        Get all renewals, optionally filtered by status.
        Excludes renewals for cancelled policies.

        Args:
            status: Optional status filter
            limit: Maximum number of results

        Returns:
            List of Renewal instances
        """
        if status:
            query = """
            SELECT r.* FROM renewals r
            JOIN quotes q ON r.original_quote_id = q.id
            WHERE r.status = ?
            AND (q.is_cancelled IS NULL OR q.is_cancelled = 0)
            ORDER BY r.policy_end_date ASC
            LIMIT ?
            """
            results = self.db.execute_query(query, (status, limit))
        else:
            query = """
            SELECT r.* FROM renewals r
            JOIN quotes q ON r.original_quote_id = q.id
            WHERE (q.is_cancelled IS NULL OR q.is_cancelled = 0)
            ORDER BY r.policy_end_date ASC
            LIMIT ?
            """
            results = self.db.execute_query(query, (limit,))

        return [Renewal.from_dict(dict(row)) for row in results]

    def get_upcoming_renewals(self, days_ahead: int = 90) -> List[Renewal]:
        """
        Get renewals due within specified days.
        Excludes renewals for cancelled policies.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of Renewal instances
        """
        target_date = (date.today() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        today = date.today().strftime('%Y-%m-%d')

        query = """
        SELECT r.* FROM renewals r
        JOIN quotes q ON r.original_quote_id = q.id
        WHERE r.policy_end_date BETWEEN ? AND ?
        AND r.status IN ('pending', 'generated', 'sent')
        AND (q.is_cancelled IS NULL OR q.is_cancelled = 0)
        ORDER BY r.policy_end_date ASC
        """

        results = self.db.execute_query(query, (today, target_date))
        return [Renewal.from_dict(dict(row)) for row in results]

    def get_reminders_due(self) -> List[Renewal]:
        """
        Get renewals that need reminders sent today.

        Returns:
            List of Renewal instances needing reminders
        """
        # Get all pending/generated renewals
        renewals = self.get_all(status='pending')
        renewals.extend(self.get_all(status='generated'))
        renewals.extend(self.get_all(status='sent'))

        # Filter to those needing reminders
        reminders_due = []
        for renewal in renewals:
            if renewal.get_next_reminder_due():
                reminders_due.append(renewal)

        return reminders_due

    def update(self, renewal: Renewal) -> bool:
        """
        Update existing renewal.

        Args:
            renewal: Renewal instance with updated data

        Returns:
            True if successful
        """
        query = """
        UPDATE renewals SET
            renewal_quote_id = ?,
            policy_end_date = ?,
            renewal_due_date = ?,
            status = ?,
            reminder_90_days_sent = ?,
            reminder_90_days_date = ?,
            reminder_60_days_sent = ?,
            reminder_60_days_date = ?,
            reminder_30_days_sent = ?,
            reminder_30_days_date = ?,
            reminder_final_sent = ?,
            reminder_final_date = ?,
            renewal_generated_date = ?,
            renewal_sent_date = ?,
            renewal_premium = ?,
            premium_change_percent = ?,
            outcome_date = ?,
            outcome_notes = ?,
            declined_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        params = (
            renewal.renewal_quote_id,
            renewal.policy_end_date,
            renewal.renewal_due_date,
            renewal.status,
            renewal.reminder_90_days_sent,
            renewal.reminder_90_days_date,
            renewal.reminder_60_days_sent,
            renewal.reminder_60_days_date,
            renewal.reminder_30_days_sent,
            renewal.reminder_30_days_date,
            renewal.reminder_final_sent,
            renewal.reminder_final_date,
            renewal.renewal_generated_date,
            renewal.renewal_sent_date,
            renewal.renewal_premium,
            renewal.premium_change_percent,
            renewal.outcome_date,
            renewal.outcome_notes,
            renewal.declined_reason,
            renewal.id
        )

        rows = self.db.execute_update(query, params)
        return rows > 0

    def mark_reminder_sent(self, renewal_id: int, reminder_type: str) -> bool:
        """
        Mark a specific reminder as sent.

        Args:
            renewal_id: Renewal ID
            reminder_type: '90_days', '60_days', '30_days', or 'final'

        Returns:
            True if successful
        """
        today = date.today().strftime('%Y-%m-%d')

        field_map = {
            '90_days': ('reminder_90_days_sent', 'reminder_90_days_date'),
            '60_days': ('reminder_60_days_sent', 'reminder_60_days_date'),
            '30_days': ('reminder_30_days_sent', 'reminder_30_days_date'),
            'final': ('reminder_final_sent', 'reminder_final_date')
        }

        if reminder_type not in field_map:
            return False

        sent_field, date_field = field_map[reminder_type]

        query = f"""
        UPDATE renewals
        SET {sent_field} = 1,
            {date_field} = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        rows = self.db.execute_update(query, (today, renewal_id))
        return rows > 0

    def update_status(self, renewal_id: int, status: str, outcome_notes: str = '') -> bool:
        """
        Update renewal status.

        Args:
            renewal_id: Renewal ID
            status: New status ('pending', 'generated', 'sent', 'bound', 'declined', 'lapsed')
            outcome_notes: Optional notes about the outcome

        Returns:
            True if successful
        """
        today = date.today().strftime('%Y-%m-%d')

        query = """
        UPDATE renewals
        SET status = ?,
            outcome_date = ?,
            outcome_notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        rows = self.db.execute_update(query, (status, today, outcome_notes, renewal_id))
        return rows > 0

    def delete(self, renewal_id: int) -> bool:
        """
        Delete renewal.

        Args:
            renewal_id: Renewal ID

        Returns:
            True if successful
        """
        query = "DELETE FROM renewals WHERE id = ?"
        rows = self.db.execute_update(query, (renewal_id,))
        return rows > 0

    def get_renewal_statistics(self) -> Dict[str, Any]:
        """
        Get renewal statistics.

        Returns:
            Dictionary with renewal metrics
        """
        stats = {}

        # Total renewals by status
        query = """
        SELECT status, COUNT(*) as count
        FROM renewals
        GROUP BY status
        """
        results = self.db.execute_query(query)
        stats['by_status'] = {row['status']: row['count'] for row in results}

        # Renewals due in next 30 days
        target_date = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        today = date.today().strftime('%Y-%m-%d')

        query = """
        SELECT COUNT(*) as count
        FROM renewals
        WHERE policy_end_date BETWEEN ? AND ?
        AND status IN ('pending', 'generated', 'sent')
        """
        results = self.db.execute_query(query, (today, target_date))
        stats['due_30_days'] = results[0]['count'] if results else 0

        # Renewals due in next 90 days
        target_date_90 = (date.today() + timedelta(days=90)).strftime('%Y-%m-%d')

        query = """
        SELECT COUNT(*) as count
        FROM renewals
        WHERE policy_end_date BETWEEN ? AND ?
        AND status IN ('pending', 'generated', 'sent')
        """
        results = self.db.execute_query(query, (today, target_date_90))
        stats['due_90_days'] = results[0]['count'] if results else 0

        # Average premium change
        query = """
        SELECT AVG(premium_change_percent) as avg_change
        FROM renewals
        WHERE renewal_premium IS NOT NULL
        """
        results = self.db.execute_query(query)
        stats['avg_premium_change'] = results[0]['avg_change'] if results and results[0]['avg_change'] else 0

        return stats
