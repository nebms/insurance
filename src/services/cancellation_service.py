"""
Cancellation Service.
Handles policy cancellation workflow, premium calculations, and validation.
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime, date
from models.quote import Quote, QuoteRepository


class CancellationService:
    """Service for handling policy cancellations."""

    # Cancellation reasons
    CANCELLATION_REASONS = [
        "Insured Request",
        "Non-payment of Premium",
        "Underwriting Reasons",
        "Material Misrepresentation",
        "Equipment Sold",
        "Duplicate Coverage",
        "Policy Not Taken",
        "Other"
    ]

    # Cancellation types
    CANCELLATION_TYPES = [
        "Flat",          # No loss, full refund
        "Pro-rata",      # Proportional refund
        "Short-rate"     # Penalty cancellation (90% of pro-rata)
    ]

    def __init__(self):
        self.quote_repo = QuoteRepository()

    def cancel_policy(self, quote_id: int, cancellation_info: Dict[str, Any],
                     current_user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Cancel a bound policy.

        Args:
            quote_id: ID of the quote/policy to cancel
            cancellation_info: Dictionary with cancellation details
                - effective_date: When coverage ends (required)
                - reason: Cancellation reason (required)
                - cancellation_type: Flat/Pro-rata/Short-rate (required)
                - notes: Additional notes (optional)
            current_user_id: ID of user performing cancellation

        Returns:
            Tuple of (success, message)
        """
        # Get quote
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            return False, "Quote not found"

        # Validate cancellation requirements
        try:
            self._validate_cancellation_requirements(quote, cancellation_info)
        except ValueError as e:
            return False, str(e)

        # Calculate return premium
        return_premium = self._calculate_return_premium(
            quote,
            cancellation_info['effective_date'],
            cancellation_info['cancellation_type']
        )

        # Prepare cancellation data
        cancellation_date = datetime.now().strftime("%Y-%m-%d")

        update_data = {
            'is_cancelled': 1,
            'cancellation_date': cancellation_date,
            'cancellation_effective_date': cancellation_info['effective_date'],
            'cancellation_reason': cancellation_info['reason'],
            'cancellation_type': cancellation_info['cancellation_type'],
            'return_premium': return_premium,
            'cancelled_by_user_id': current_user_id,
            'cancellation_notes': cancellation_info.get('notes', ''),
            'status': 'cancelled'
        }

        # Update quote with cancellation info
        success = self.quote_repo.update_fields(quote_id, update_data)

        if success:
            return True, f"Policy cancelled successfully. Return premium: ${return_premium:,.2f}"
        else:
            return False, "Failed to update policy cancellation"

    def _validate_cancellation_requirements(self, quote: Quote,
                                          cancellation_info: Dict[str, Any]):
        """Validate that all requirements for cancellation are met."""

        # Must be a bound policy
        if not quote.is_bound:
            raise ValueError("Cannot cancel unbound quote. Only bound policies can be cancelled.")

        # Cannot cancel already cancelled policy
        if quote.is_cancelled:
            raise ValueError("Policy is already cancelled")

        # Required fields
        if not cancellation_info.get('effective_date'):
            raise ValueError("Cancellation effective date is required")

        if not cancellation_info.get('reason'):
            raise ValueError("Cancellation reason is required")

        if not cancellation_info.get('cancellation_type'):
            raise ValueError("Cancellation type is required")

        # Validate reason
        if cancellation_info['reason'] not in self.CANCELLATION_REASONS:
            raise ValueError(f"Invalid cancellation reason: {cancellation_info['reason']}")

        # Validate type
        if cancellation_info['cancellation_type'] not in self.CANCELLATION_TYPES:
            raise ValueError(f"Invalid cancellation type: {cancellation_info['cancellation_type']}")

        # Validate effective date
        try:
            effective_date = datetime.strptime(cancellation_info['effective_date'], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid effective date format")

        # Effective date must be >= policy effective date
        if quote.effective_date:
            policy_effective = datetime.strptime(quote.effective_date, "%Y-%m-%d").date()
            if effective_date < policy_effective:
                raise ValueError("Cancellation effective date cannot be before policy effective date")

        # Effective date should not be in the far future (warn but allow)
        today = date.today()
        if (effective_date - today).days > 60:
            # Could add a warning here, but allow it
            pass

    def _calculate_return_premium(self, quote: Quote, effective_date_str: str,
                                 cancellation_type: str) -> float:
        """
        Calculate return premium based on cancellation type.

        Args:
            quote: Quote/policy being cancelled
            effective_date_str: Cancellation effective date (YYYY-MM-DD)
            cancellation_type: Flat, Pro-rata, or Short-rate

        Returns:
            Return premium amount
        """
        if cancellation_type == "Flat":
            # Flat cancellation - full refund
            return quote.total_premium

        # For Pro-rata and Short-rate, calculate based on unused days
        if not quote.effective_date or not quote.expiration_date:
            # If we don't have dates, can't calculate pro-rata
            return 0.0

        try:
            policy_start = datetime.strptime(quote.effective_date, "%Y-%m-%d").date()
            policy_end = datetime.strptime(quote.expiration_date, "%Y-%m-%d").date()
            cancel_effective = datetime.strptime(effective_date_str, "%Y-%m-%d").date()
        except ValueError:
            return 0.0

        # Total policy days
        total_days = (policy_end - policy_start).days
        if total_days <= 0:
            return 0.0

        # Used days
        used_days = (cancel_effective - policy_start).days
        if used_days < 0:
            used_days = 0

        # Unused days
        unused_days = total_days - used_days
        if unused_days < 0:
            unused_days = 0

        # Calculate pro-rata refund
        pro_rata_refund = (unused_days / total_days) * quote.total_premium

        if cancellation_type == "Pro-rata":
            return round(pro_rata_refund, 2)
        elif cancellation_type == "Short-rate":
            # Short-rate is typically 90% of pro-rata (10% penalty)
            short_rate_refund = pro_rata_refund * 0.90
            return round(short_rate_refund, 2)

        return 0.0

    def reinstate_policy(self, quote_id: int, reinstatement_notes: str = "",
                        current_user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Reinstate a cancelled policy.

        Args:
            quote_id: ID of the cancelled quote/policy
            reinstatement_notes: Notes about reinstatement
            current_user_id: ID of user performing reinstatement

        Returns:
            Tuple of (success, message)
        """
        # Get quote
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            return False, "Quote not found"

        # Must be cancelled
        if not quote.is_cancelled:
            return False, "Policy is not cancelled"

        # Must still be bound
        if not quote.is_bound:
            return False, "Cannot reinstate unbound quote"

        # Clear cancellation data
        update_data = {
            'is_cancelled': 0,
            'cancellation_date': None,
            'cancellation_effective_date': None,
            'cancellation_reason': None,
            'cancellation_type': None,
            'return_premium': 0.0,
            'cancelled_by_user_id': None,
            'cancellation_notes': reinstatement_notes,
            'status': 'bound'
        }

        success = self.quote_repo.update_fields(quote_id, update_data)

        if success:
            return True, "Policy reinstated successfully"
        else:
            return False, "Failed to reinstate policy"

    def get_cancellation_summary(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cancellation summary for a policy.

        Returns:
            Dictionary with cancellation details or None if not found
        """
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            return None

        summary = {
            'quote': quote,
            'is_cancelled': bool(quote.is_cancelled),
            'cancellation_date': quote.cancellation_date,
            'cancellation_effective_date': quote.cancellation_effective_date,
            'cancellation_reason': quote.cancellation_reason,
            'cancellation_type': quote.cancellation_type,
            'return_premium': quote.return_premium or 0.0,
            'cancellation_notes': quote.cancellation_notes or '',
            'cancelled_by': None,
            'can_reinstate': bool(quote.is_cancelled and quote.is_bound)
        }

        # Include user ID who cancelled if available
        if quote.cancelled_by_user_id:
            summary['cancelled_by'] = f"User ID: {quote.cancelled_by_user_id}"

        # Calculate days from effective to cancellation
        if quote.effective_date and quote.cancellation_effective_date:
            try:
                effective = datetime.strptime(quote.effective_date, "%Y-%m-%d").date()
                cancel_eff = datetime.strptime(quote.cancellation_effective_date, "%Y-%m-%d").date()
                summary['days_in_force'] = (cancel_eff - effective).days
            except ValueError:
                summary['days_in_force'] = None

        return summary

    def get_cancelled_policies(self) -> list:
        """Get all cancelled policies."""
        from database.db_manager import get_db
        db = get_db()

        query = """
            SELECT * FROM quotes
            WHERE is_cancelled = 1 AND is_bound = 1
            ORDER BY cancellation_date DESC
        """

        results = db.execute_query(query)
        quotes = [Quote.from_dict(dict(row)) for row in results]

        # Load line items for each quote
        for quote in quotes:
            quote.line_items = self.quote_repo.line_item_repo.get_by_quote(quote.id)
            if quote.line_items:
                quote.populate_from_first_line_item()

        return quotes
