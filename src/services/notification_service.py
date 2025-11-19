"""
Notification service for sending emails and alerts.
Placeholder implementation that can be integrated with actual email services.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from models.renewal import Renewal
from models.quote import Quote
from models.customer import Customer


class NotificationService:
    """Service for sending notifications and emails."""

    def __init__(self):
        """Initialize notification service."""
        self.notification_log = []  # In-memory log for testing

    def send_renewal_reminder(self, renewal: Renewal, quote: Quote,
                             customer: Optional[Customer], reminder_type: str) -> bool:
        """
        Send renewal reminder email.

        Args:
            renewal: Renewal record
            quote: Original quote
            customer: Customer record
            reminder_type: '90_days', '60_days', '30_days', or 'final'

        Returns:
            True if successful
        """
        # Build reminder message
        days_until = renewal.calculate_days_until_expiration()

        subject = self._get_reminder_subject(reminder_type, days_until)
        body = self._build_renewal_email_body(renewal, quote, customer, reminder_type, days_until)

        # Log notification (placeholder for actual email sending)
        notification = {
            'timestamp': datetime.now().isoformat(),
            'type': 'renewal_reminder',
            'reminder_type': reminder_type,
            'quote_number': quote.quote_number,
            'customer': customer.name if customer else 'N/A',
            'email': customer.email if customer else None,
            'subject': subject,
            'body': body,
            'sent': True
        }

        self.notification_log.append(notification)

        # TODO: Integrate with actual email service
        # Example integrations:
        # - SMTP (smtplib)
        # - SendGrid
        # - Amazon SES
        # - Mailgun
        print(f"\n{'='*60}")
        print(f"RENEWAL REMINDER EMAIL")
        print(f"{'='*60}")
        print(f"To: {customer.email if customer else 'N/A'}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{'='*60}\n")

        return True

    def send_renewal_quote_notification(self, renewal: Renewal, renewal_quote: Quote,
                                       customer: Optional[Customer]) -> bool:
        """
        Send notification that renewal quote is ready.

        Args:
            renewal: Renewal record
            renewal_quote: Generated renewal quote
            customer: Customer record

        Returns:
            True if successful
        """
        subject = f"Your Renewal Quote is Ready - {renewal_quote.quote_number}"

        body = f"""
Dear {customer.name if customer else 'Valued Customer'},

Your insurance renewal quote is now ready for review.

Quote Details:
- Quote Number: {renewal_quote.quote_number}
- Original Policy: Quote #{renewal.original_quote_id}
- Policy Expiration: {renewal.policy_end_date}
- Renewal Premium: ${renewal_quote.total_premium:,.2f}

"""

        if renewal.premium_change_percent:
            if renewal.premium_change_percent > 0:
                body += f"Premium Change: +{renewal.premium_change_percent}% increase\n"
            else:
                body += f"Premium Change: {abs(renewal.premium_change_percent)}% decrease\n"

        body += """
Please review your renewal quote and contact us if you have any questions.

To accept this renewal, please contact your agent or reply to this email.

Thank you for your continued business!

Best regards,
CSI Pivot Quote Team
"""

        # Log notification
        notification = {
            'timestamp': datetime.now().isoformat(),
            'type': 'renewal_quote_ready',
            'quote_number': renewal_quote.quote_number,
            'customer': customer.name if customer else 'N/A',
            'email': customer.email if customer else None,
            'subject': subject,
            'body': body,
            'sent': True
        }

        self.notification_log.append(notification)

        print(f"\n{'='*60}")
        print(f"RENEWAL QUOTE EMAIL")
        print(f"{'='*60}")
        print(f"To: {customer.email if customer else 'N/A'}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{'='*60}\n")

        return True

    def send_renewal_bound_confirmation(self, renewal: Renewal, renewal_quote: Quote,
                                       customer: Optional[Customer]) -> bool:
        """
        Send confirmation that renewal has been bound.

        Args:
            renewal: Renewal record
            renewal_quote: Bound renewal quote
            customer: Customer record

        Returns:
            True if successful
        """
        subject = f"Renewal Confirmed - {renewal_quote.quote_number}"

        body = f"""
Dear {customer.name if customer else 'Valued Customer'},

Thank you for renewing your insurance policy with us!

Your renewal has been confirmed:
- New Quote Number: {renewal_quote.quote_number}
- Policy Start Date: {renewal_quote.policy_start_date}
- Policy End Date: {renewal_quote.policy_end_date}
- Annual Premium: ${renewal_quote.total_premium:,.2f}

Your policy documents will be sent to you shortly.

Thank you for your continued trust in our service!

Best regards,
CSI Pivot Quote Team
"""

        # Log notification
        notification = {
            'timestamp': datetime.now().isoformat(),
            'type': 'renewal_bound',
            'quote_number': renewal_quote.quote_number,
            'customer': customer.name if customer else 'N/A',
            'email': customer.email if customer else None,
            'subject': subject,
            'body': body,
            'sent': True
        }

        self.notification_log.append(notification)

        print(f"\n{'='*60}")
        print(f"RENEWAL CONFIRMATION EMAIL")
        print(f"{'='*60}")
        print(f"To: {customer.email if customer else 'N/A'}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{'='*60}\n")

        return True

    def _get_reminder_subject(self, reminder_type: str, days_until: int) -> str:
        """Get email subject for reminder type."""
        if reminder_type == '90_days':
            return f"Your Insurance Policy Renews in {days_until} Days"
        elif reminder_type == '60_days':
            return f"Renewal Reminder: {days_until} Days Until Policy Expiration"
        elif reminder_type == '30_days':
            return f"Important: Policy Expires in {days_until} Days"
        elif reminder_type == 'final':
            return f"URGENT: Policy Expires in {days_until} Days - Action Required"
        else:
            return "Policy Renewal Reminder"

    def _build_renewal_email_body(self, renewal: Renewal, quote: Quote,
                                  customer: Optional[Customer], reminder_type: str,
                                  days_until: int) -> str:
        """Build renewal reminder email body."""
        urgency = "soon" if days_until > 30 else "SOON"
        if days_until <= 7:
            urgency = "VERY SOON"

        body = f"""
Dear {customer.name if customer else 'Valued Customer'},

This is a friendly reminder that your insurance policy is set to expire {urgency}.

Policy Details:
- Current Quote Number: {quote.quote_number}
- Expiration Date: {renewal.policy_end_date}
- Days Until Expiration: {days_until} days
"""

        if renewal.renewal_quote_id:
            body += f"""
Good News! Your renewal quote has already been prepared:
- Renewal Quote Number: {renewal.renewal_quote_id}
- Renewal Premium: ${renewal.renewal_premium:,.2f}
"""
            if renewal.premium_change_percent:
                if renewal.premium_change_percent > 0:
                    body += f"- Premium Change: +{renewal.premium_change_percent}% from previous year\n"
                else:
                    body += f"- Premium Change: {abs(renewal.premium_change_percent)}% savings from previous year\n"

            body += "\nPlease review your renewal quote and contact us to proceed with renewal.\n"
        else:
            body += """
To ensure continuous coverage, please contact us to:
1. Review your current coverage
2. Receive your renewal quote
3. Make any necessary updates to your policy

We're working on preparing your renewal quote and will send it to you shortly.
"""

        if days_until <= 30:
            body += f"""
⚠️ IMPORTANT: You have only {days_until} days remaining before your policy expires.
To avoid any lapse in coverage, please contact us as soon as possible.
"""

        body += """
If you have any questions or would like to discuss your renewal, please don't hesitate to contact us.

Thank you for your continued business!

Best regards,
CSI Pivot Quote Team
"""

        return body

    def get_notification_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent notifications sent.

        Args:
            limit: Maximum number of notifications to return

        Returns:
            List of notification records
        """
        return self.notification_log[-limit:] if self.notification_log else []

    def clear_notification_log(self):
        """Clear notification log (for testing)."""
        self.notification_log = []


# Singleton instance
_notification_service = None


def get_notification_service() -> NotificationService:
    """Get notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
