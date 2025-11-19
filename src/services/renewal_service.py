"""
Renewal processing service.
Handles renewal quote generation, reminders, and renewal workflow.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, date, timedelta
from models.renewal import Renewal, RenewalRepository
from models.quote import Quote, QuoteRepository
from models.customer import CustomerRepository
from calculations.premium_calc import PremiumCalculator


class RenewalService:
    """Service for processing renewals and generating renewal quotes."""

    def __init__(self):
        self.renewal_repo = RenewalRepository()
        self.quote_repo = QuoteRepository()
        self.customer_repo = CustomerRepository()
        self.calculator = PremiumCalculator()

    def create_renewal_from_quote(self, quote_id: int) -> Optional[Renewal]:
        """
        Create a renewal record from a bound quote.

        Args:
            quote_id: Original quote ID

        Returns:
            Renewal instance or None
        """
        # Get the original quote
        quote = self.quote_repo.get_by_id(quote_id, load_line_items=True)
        if not quote:
            return None

        # Check if quote is bound
        if not quote.is_bound or not quote.policy_end_date:
            raise ValueError("Quote must be bound with a policy end date to create renewal")

        # Check if quote is cancelled
        if quote.is_cancelled:
            raise ValueError("Cannot create renewal for cancelled policy")

        # Check if renewal already exists
        existing = self.renewal_repo.get_by_original_quote(quote_id)
        if existing:
            return existing

        # Calculate renewal due date (90 days before expiration)
        try:
            policy_end = datetime.strptime(quote.policy_end_date, '%Y-%m-%d').date()
            renewal_due = (policy_end - timedelta(days=90)).strftime('%Y-%m-%d')
        except:
            raise ValueError("Invalid policy end date format")

        # Create renewal record
        renewal = Renewal(
            original_quote_id=quote_id,
            policy_end_date=quote.policy_end_date,
            renewal_due_date=renewal_due,
            status='pending'
        )

        renewal_id = self.renewal_repo.create(renewal)
        renewal.id = renewal_id

        return renewal

    def generate_renewal_quote(self, renewal_id: int, apply_rate_updates: bool = True) -> Optional[Quote]:
        """
        Generate a renewal quote from a renewal record.

        Args:
            renewal_id: Renewal ID
            apply_rate_updates: Whether to apply current rate tables (default: True)

        Returns:
            New Quote instance or None
        """
        # Get renewal record
        renewal = self.renewal_repo.get_by_id(renewal_id)
        if not renewal:
            return None

        # Get original quote with line items
        original_quote = self.quote_repo.get_by_id(renewal.original_quote_id, load_line_items=True)
        if not original_quote:
            return None

        # Generate new quote number
        new_quote_number = self.quote_repo.generate_quote_number()

        # Create renewal quote based on original
        renewal_quote = Quote(
            quote_number=new_quote_number,
            customer_id=original_quote.customer_id,
            agent_name=original_quote.agent_name,
            quote_date=date.today().strftime('%Y-%m-%d'),
            state_code=original_quote.state_code,
            term_months=original_quote.term_months,
            status='renewal',
            notes=f"Renewal of {original_quote.quote_number}",
            original_quote_id=original_quote.id
        )

        # Copy line items from original quote
        renewal_line_items = []
        for original_item in original_quote.line_items:
            # Create copy of line item
            renewal_item = type(original_item)(
                line_number=original_item.line_number,
                pivot_amount=original_item.pivot_amount,
                ancillary_amount=original_item.ancillary_amount,
                submersible_pump_amount=original_item.submersible_pump_amount,
                equipment_age_years=original_item.equipment_age_years + 1,  # Age equipment by 1 year
                is_towable=original_item.is_towable,
                is_corner_or_long=original_item.is_corner_or_long,
                has_me_endorsement=original_item.has_me_endorsement,
                pivot_deductible_code=original_item.pivot_deductible_code,
                ancillary_deductible_code=original_item.ancillary_deductible_code
            )

            if apply_rate_updates:
                # Recalculate with current rates
                result = self.calculator.calculate_complete_quote(
                    state_code=renewal_quote.state_code,
                    pivot_amount=renewal_item.pivot_amount,
                    equipment_age_years=renewal_item.equipment_age_years,
                    term_months=renewal_quote.term_months,
                    pivot_deductible_code=renewal_item.pivot_deductible_code,
                    ancillary_deductible_code=renewal_item.ancillary_deductible_code,
                    ancillary_amount=renewal_item.ancillary_amount,
                    submersible_pump_amount=renewal_item.submersible_pump_amount,
                    is_towable=renewal_item.is_towable,
                    is_corner_or_long=renewal_item.is_corner_or_long,
                    has_me_endorsement=renewal_item.has_me_endorsement
                )

                # Update with new calculations
                renewal_item.pivot_rate = result['pivot_rate']
                renewal_item.ancillary_rate = result.get('ancillary_rate')
                renewal_item.pivot_premium = result['pivot_premium']
                renewal_item.ancillary_premium = result.get('ancillary_premium', 0)
                renewal_item.submersible_charge = result.get('submersible_charge', 0)
                renewal_item.line_total_premium = result['total_premium']
                renewal_item.alt1_deductible = result.get('alt1_deductible')
                renewal_item.alt1_rate = result.get('alt1_rate')
                renewal_item.alt1_premium = result.get('alt1_premium')
                renewal_item.alt2_deductible = result.get('alt2_deductible')
                renewal_item.alt2_rate = result.get('alt2_rate')
                renewal_item.alt2_premium = result.get('alt2_premium')
            else:
                # Keep original rates (just age the equipment)
                renewal_item.pivot_rate = original_item.pivot_rate
                renewal_item.ancillary_rate = original_item.ancillary_rate
                renewal_item.pivot_premium = original_item.pivot_premium
                renewal_item.ancillary_premium = original_item.ancillary_premium
                renewal_item.submersible_charge = original_item.submersible_charge
                renewal_item.line_total_premium = original_item.line_total_premium

            renewal_line_items.append(renewal_item)

        # Calculate total premium
        total_premium = sum(item.line_total_premium or 0 for item in renewal_line_items)
        renewal_quote.total_premium = total_premium

        # Save renewal quote
        renewal_quote_id = self.quote_repo.create(renewal_quote, line_items=renewal_line_items)

        # Update renewal record
        renewal.renewal_quote_id = renewal_quote_id
        renewal.renewal_generated_date = date.today().strftime('%Y-%m-%d')
        renewal.renewal_premium = total_premium
        renewal.status = 'generated'

        # Calculate premium change percentage
        if original_quote.total_premium > 0:
            premium_change = ((total_premium - original_quote.total_premium) /
                            original_quote.total_premium) * 100
            renewal.premium_change_percent = round(premium_change, 2)

        self.renewal_repo.update(renewal)

        # Reload quote with line items
        return self.quote_repo.get_by_id(renewal_quote_id, load_line_items=True)

    def mark_quote_as_bound(self, quote_id: int, policy_start_date: str,
                           term_months: Optional[int] = None) -> Tuple[bool, Optional[Renewal]]:
        """
        Mark a quote as bound and create renewal tracking.

        Args:
            quote_id: Quote ID to bind
            policy_start_date: Policy start date (YYYY-MM-DD)
            term_months: Optional term override (uses quote term if not provided)

        Returns:
            Tuple of (success, renewal)
        """
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            return False, None

        # Parse dates
        try:
            start_date = datetime.strptime(policy_start_date, '%Y-%m-%d').date()
            months = term_months or quote.term_months
            end_date = start_date + timedelta(days=months * 30)  # Approximate
            end_date_str = end_date.strftime('%Y-%m-%d')
        except:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

        # Update quote
        quote.is_bound = 1
        quote.status = 'bound'
        quote.policy_start_date = policy_start_date
        quote.policy_end_date = end_date_str

        self.quote_repo.update(quote)

        # Create renewal record
        renewal = self.create_renewal_from_quote(quote_id)

        return True, renewal

    def process_upcoming_renewals(self, days_ahead: int = 90) -> List[Dict[str, Any]]:
        """
        Process renewals due within specified days.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of renewal processing results
        """
        results = []

        # Get upcoming renewals
        renewals = self.renewal_repo.get_upcoming_renewals(days_ahead)

        for renewal in renewals:
            result = {
                'renewal_id': renewal.id,
                'original_quote_id': renewal.original_quote_id,
                'policy_end_date': renewal.policy_end_date,
                'days_until_expiration': renewal.calculate_days_until_expiration(),
                'status': renewal.status,
                'actions_needed': []
            }

            # Check what actions are needed
            if renewal.status == 'pending' and not renewal.renewal_quote_id:
                result['actions_needed'].append('generate_renewal_quote')

            # Check for reminders
            next_reminder = renewal.get_next_reminder_due()
            if next_reminder:
                days_before, reminder_type = next_reminder
                result['actions_needed'].append(f'send_{reminder_type}_reminder')

            results.append(result)

        return results

    def send_renewal_reminder(self, renewal_id: int, reminder_type: str) -> bool:
        """
        Send renewal reminder and mark as sent.

        Args:
            renewal_id: Renewal ID
            reminder_type: '90_days', '60_days', '30_days', or 'final'

        Returns:
            True if successful

        Note:
            This is a placeholder. In production, integrate with email/notification system.
        """
        renewal = self.renewal_repo.get_by_id(renewal_id)
        if not renewal:
            return False

        # Get quote and customer info for reminder
        quote = self.quote_repo.get_by_id(renewal.original_quote_id)
        if not quote:
            return False

        customer = None
        if quote.customer_id:
            customer = self.customer_repo.get_by_id(quote.customer_id)

        # TODO: Integrate with email/notification system
        # For now, just log the reminder
        print(f"=== RENEWAL REMINDER ===")
        print(f"Type: {reminder_type}")
        print(f"Quote: {quote.quote_number}")
        if customer:
            print(f"Customer: {customer.name}")
            print(f"Email: {customer.email}")
        print(f"Policy Expires: {renewal.policy_end_date}")
        print(f"Days Until Expiration: {renewal.calculate_days_until_expiration()}")
        print("========================")

        # Mark reminder as sent
        return self.renewal_repo.mark_reminder_sent(renewal_id, reminder_type)

    def process_daily_renewals(self) -> Dict[str, Any]:
        """
        Daily renewal processing job.
        - Send due reminders
        - Auto-generate renewal quotes for policies expiring in 90 days
        - Update lapsed renewals

        Returns:
            Processing summary
        """
        summary = {
            'reminders_sent': 0,
            'quotes_generated': 0,
            'renewals_lapsed': 0,
            'errors': []
        }

        # Send reminders
        reminders_due = self.renewal_repo.get_reminders_due()
        for renewal in reminders_due:
            next_reminder = renewal.get_next_reminder_due()
            if next_reminder:
                _, reminder_type = next_reminder
                try:
                    if self.send_renewal_reminder(renewal.id, reminder_type):
                        summary['reminders_sent'] += 1
                except Exception as e:
                    summary['errors'].append(f"Reminder error for renewal {renewal.id}: {str(e)}")

        # Auto-generate renewal quotes for pending renewals
        pending_renewals = self.renewal_repo.get_all(status='pending')
        for renewal in pending_renewals:
            days_until = renewal.calculate_days_until_expiration()
            if 0 < days_until <= 90 and not renewal.renewal_quote_id:
                try:
                    self.generate_renewal_quote(renewal.id)
                    summary['quotes_generated'] += 1
                except Exception as e:
                    summary['errors'].append(f"Quote generation error for renewal {renewal.id}: {str(e)}")

        # Mark lapsed renewals
        all_renewals = self.renewal_repo.get_all()
        for renewal in all_renewals:
            if renewal.calculate_days_until_expiration() < 0 and renewal.status not in ['bound', 'declined', 'lapsed']:
                try:
                    self.renewal_repo.update_status(renewal.id, 'lapsed', 'Policy expired without renewal')
                    summary['renewals_lapsed'] += 1
                except Exception as e:
                    summary['errors'].append(f"Lapse error for renewal {renewal.id}: {str(e)}")

        return summary

    def get_renewal_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for renewal dashboard.

        Returns:
            Dashboard data dictionary
        """
        stats = self.renewal_repo.get_renewal_statistics()

        # Get renewals by urgency
        upcoming_30 = self.renewal_repo.get_upcoming_renewals(days_ahead=30)
        upcoming_60 = self.renewal_repo.get_upcoming_renewals(days_ahead=60)
        upcoming_90 = self.renewal_repo.get_upcoming_renewals(days_ahead=90)

        # Get reminders due
        reminders_due = self.renewal_repo.get_reminders_due()

        # Build dashboard data
        dashboard = {
            'statistics': stats,
            'urgent_renewals': len(upcoming_30),
            'upcoming_renewals_30': len(upcoming_30),
            'upcoming_renewals_60': len(upcoming_60),
            'upcoming_renewals_90': len(upcoming_90),
            'reminders_pending': len(reminders_due),
            'recent_renewals': upcoming_30[:10] if upcoming_30 else []
        }

        return dashboard
