"""
Binding Service for converting quotes to policies.
Handles policy binding, policy number management, and renewal integration.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, date, timedelta
from models.quote import Quote, QuoteRepository
from models.renewal import Renewal, RenewalRepository
from models.policy_document import PolicyDocument, PolicyDocumentRepository


class BindingService:
    """Service for binding quotes to active policies."""

    def __init__(self):
        self.quote_repo = QuoteRepository()
        self.renewal_repo = RenewalRepository()
        self.document_repo = PolicyDocumentRepository()

    def bind_quote(self, quote_id: int, binding_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Bind a quote to create an active policy.

        Args:
            quote_id: Quote ID to bind
            binding_info: Dictionary with binding information:
                - effective_date: Policy effective date (YYYY-MM-DD) [REQUIRED]
                - carrier_name: Insurance carrier name [REQUIRED]
                - policy_number: Policy number (optional, can be added later)
                - payment_status: Payment status (pending, paid, financed)
                - payment_method: Payment method (check, wire, etc.)
                - bound_by_user_id: User ID who bound the policy
                - notes: Additional notes

        Returns:
            Tuple of (success, message)
        """
        # Get quote
        quote = self.quote_repo.get_by_id(quote_id, load_line_items=True)
        if not quote:
            return False, "Quote not found"

        # Validate binding requirements
        valid, error_msg = self._validate_binding_requirements(quote, binding_info)
        if not valid:
            return False, error_msg

        # Check if already bound
        if quote.is_bound:
            return False, f"Quote is already bound (Policy #: {quote.policy_number or 'N/A'})"

        # Check if cancelled
        if quote.is_cancelled:
            return False, "Cannot bind a cancelled quote. Reinstate the policy first."

        # Extract binding information
        effective_date_str = binding_info.get('effective_date')
        carrier_name = binding_info.get('carrier_name', '')
        policy_number = binding_info.get('policy_number')  # Optional
        payment_status = binding_info.get('payment_status', 'pending')
        payment_method = binding_info.get('payment_method', '')
        bound_by_user_id = binding_info.get('bound_by_user_id')
        notes = binding_info.get('notes', '')

        # Calculate expiration date
        try:
            effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
            # Calculate expiration based on term months
            expiration_date = effective_date + timedelta(days=quote.term_months * 30)
            expiration_date_str = expiration_date.strftime('%Y-%m-%d')
        except:
            return False, "Invalid effective date format"

        # Update quote with policy information
        quote.is_bound = 1
        quote.status = 'bound'
        quote.bound_date = date.today().strftime('%Y-%m-%d')
        quote.bound_by_user_id = bound_by_user_id
        quote.effective_date = effective_date_str
        quote.expiration_date = expiration_date_str
        quote.carrier_name = carrier_name
        quote.policy_number = policy_number  # May be None
        quote.payment_status = payment_status
        quote.payment_method = payment_method

        # Also set legacy renewal fields for backward compatibility
        quote.policy_start_date = effective_date_str
        quote.policy_end_date = expiration_date_str

        # Add notes if provided
        if notes:
            existing_notes = quote.notes or ""
            quote.notes = f"{existing_notes}\n[Bound {date.today()}] {notes}".strip()

        # Save quote
        success = self.quote_repo.update(quote)
        if not success:
            return False, "Failed to update quote"

        # Create renewal tracking
        try:
            renewal = self._create_renewal_tracking(quote)
        except Exception as e:
            # Log error but don't fail binding
            print(f"Warning: Failed to create renewal tracking: {e}")

        return True, "Quote successfully bound to policy"

    def update_policy_info(self, quote_id: int, policy_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update policy information (for adding policy number later, etc.).

        Args:
            quote_id: Quote ID
            policy_info: Dictionary with policy information:
                - policy_number: Policy number (optional)
                - carrier_name: Carrier name (optional)
                - payment_status: Payment status (optional)
                - payment_method: Payment method (optional)
                - policy_received_date: Date policy # was received (optional)
                - notes: Additional notes (optional)

        Returns:
            Tuple of (success, message)
        """
        # Get quote
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            return False, "Quote not found"

        if not quote.is_bound:
            return False, "Quote is not bound. Bind it first before updating policy info."

        if quote.is_cancelled:
            return False, "Cannot update cancelled policy. Reinstate it first."

        # Update fields if provided
        if 'policy_number' in policy_info and policy_info['policy_number']:
            quote.policy_number = policy_info['policy_number']
            if not quote.policy_received_date:
                quote.policy_received_date = date.today().strftime('%Y-%m-%d')

        if 'carrier_name' in policy_info:
            quote.carrier_name = policy_info['carrier_name']

        if 'payment_status' in policy_info:
            quote.payment_status = policy_info['payment_status']

        if 'payment_method' in policy_info:
            quote.payment_method = policy_info['payment_method']

        if 'policy_received_date' in policy_info:
            quote.policy_received_date = policy_info['policy_received_date']

        if 'notes' in policy_info and policy_info['notes']:
            existing_notes = quote.notes or ""
            quote.notes = f"{existing_notes}\n[Updated {date.today()}] {policy_info['notes']}".strip()

        # Save changes
        success = self.quote_repo.update(quote)
        if success:
            return True, "Policy information updated successfully"
        else:
            return False, "Failed to update policy information"

    def unbind_quote(self, quote_id: int, reason: str = '') -> Tuple[bool, str]:
        """
        Unbind a policy (revert to quote).

        Args:
            quote_id: Quote ID
            reason: Reason for unbinding

        Returns:
            Tuple of (success, message)
        """
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            return False, "Quote not found"

        if not quote.is_bound:
            return False, "Quote is not bound"

        if quote.is_cancelled:
            return False, "Cannot unbind a cancelled policy. Reinstate it first if needed."

        # Clear binding information
        quote.is_bound = 0
        quote.status = 'unbound'
        quote.bound_date = None
        quote.policy_received_date = None

        # Add note about unbinding
        existing_notes = quote.notes or ""
        quote.notes = f"{existing_notes}\n[Unbound {date.today()}] {reason}".strip()

        # Delete renewal tracking
        renewal = self.renewal_repo.get_by_original_quote(quote_id)
        if renewal:
            self.renewal_repo.delete(renewal.id)

        # Save changes
        success = self.quote_repo.update(quote)
        if success:
            return True, "Policy successfully unbound"
        else:
            return False, "Failed to unbind policy"

    def _validate_binding_requirements(self, quote: Quote, binding_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that quote meets binding requirements.

        Args:
            quote: Quote to validate
            binding_info: Binding information

        Returns:
            Tuple of (valid, error_message)
        """
        # Check required quote fields
        if not quote.customer_id:
            return False, "Quote must have a customer assigned"

        if not quote.total_premium or quote.total_premium <= 0:
            return False, "Quote must have a valid premium amount"

        if not quote.state_code:
            return False, "Quote must have a state code"

        # Check required binding fields
        if not binding_info.get('effective_date'):
            return False, "Effective date is required"

        if not binding_info.get('carrier_name'):
            return False, "Carrier name is required"

        # Validate effective date
        try:
            effective_date = datetime.strptime(binding_info['effective_date'], '%Y-%m-%d').date()

            # Check if effective date is too far in the past (more than 30 days)
            days_ago = (date.today() - effective_date).days
            if days_ago > 30:
                return False, f"Effective date is {days_ago} days in the past. Please verify."

            # Check if effective date is too far in the future (more than 60 days)
            days_ahead = (effective_date - date.today()).days
            if days_ahead > 60:
                return False, f"Effective date is {days_ahead} days in the future. Please verify."

        except ValueError:
            return False, "Invalid effective date format. Use YYYY-MM-DD."

        return True, ""

    def _create_renewal_tracking(self, quote: Quote) -> Optional[Renewal]:
        """
        Create renewal tracking for a bound quote.

        Args:
            quote: Bound quote

        Returns:
            Renewal instance or None
        """
        if not quote.expiration_date:
            return None

        # Don't create renewal for cancelled policies
        if quote.is_cancelled:
            return None

        # Check if renewal already exists
        existing = self.renewal_repo.get_by_original_quote(quote.id)
        if existing:
            return existing

        # Calculate renewal due date (90 days before expiration)
        try:
            expiration = datetime.strptime(quote.expiration_date, '%Y-%m-%d').date()
            renewal_due = (expiration - timedelta(days=90)).strftime('%Y-%m-%d')
        except:
            return None

        # Create renewal record
        renewal = Renewal(
            original_quote_id=quote.id,
            policy_end_date=quote.expiration_date,
            renewal_due_date=renewal_due,
            status='pending'
        )

        renewal_id = self.renewal_repo.create(renewal)
        renewal.id = renewal_id

        return renewal

    def get_policy_summary(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive policy summary.

        Args:
            quote_id: Quote/Policy ID

        Returns:
            Dictionary with policy information
        """
        quote = self.quote_repo.get_by_id(quote_id, load_line_items=True)
        if not quote:
            return None

        # Get documents
        documents = self.document_repo.get_by_quote(quote_id)

        # Get renewal info
        renewal = self.renewal_repo.get_by_original_quote(quote_id)

        # Calculate days until expiration
        days_until_expiration = None
        if quote.expiration_date:
            try:
                exp_date = datetime.strptime(quote.expiration_date, '%Y-%m-%d').date()
                days_until_expiration = (exp_date - date.today()).days
            except:
                pass

        return {
            'quote': quote,
            'is_bound': quote.is_bound == 1,
            'policy_number': quote.policy_number,
            'carrier': quote.carrier_name,
            'effective_date': quote.effective_date,
            'expiration_date': quote.expiration_date,
            'days_until_expiration': days_until_expiration,
            'payment_status': quote.payment_status,
            'payment_method': quote.payment_method,
            'documents': documents,
            'document_count': len(documents),
            'renewal': renewal,
            'has_renewal_tracking': renewal is not None
        }

    def get_active_policies(self, limit: int = 100) -> List[Quote]:
        """
        Get all active (bound) policies.

        Args:
            limit: Maximum number of policies to return

        Returns:
            List of Quote objects representing active policies
        """
        # This would be more efficient with a custom query, but using existing methods
        all_quotes = self.quote_repo.get_all(limit=limit * 2, load_line_items=False)
        active_policies = [q for q in all_quotes if q.is_bound == 1]
        return active_policies[:limit]

    def get_policies_by_carrier(self, carrier_name: str) -> List[Quote]:
        """
        Get all policies for a specific carrier.

        Args:
            carrier_name: Carrier name

        Returns:
            List of Quote objects
        """
        all_quotes = self.quote_repo.get_all(limit=1000, load_line_items=False)
        return [q for q in all_quotes if q.is_bound == 1 and q.carrier_name == carrier_name]

    def get_policies_expiring_soon(self, days: int = 30) -> List[Quote]:
        """
        Get policies expiring within specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of Quote objects
        """
        target_date = (date.today() + timedelta(days=days)).strftime('%Y-%m-%d')
        today = date.today().strftime('%Y-%m-%d')

        all_quotes = self.quote_repo.get_all(limit=1000, load_line_items=False)
        expiring = []

        for quote in all_quotes:
            if quote.is_bound == 1 and quote.expiration_date:
                if today <= quote.expiration_date <= target_date:
                    expiring.append(quote)

        # Sort by expiration date
        expiring.sort(key=lambda q: q.expiration_date)
        return expiring
