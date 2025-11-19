#!/usr/bin/env python3
"""
Daily renewal processing job.
Run this script daily (via cron or task scheduler) to:
- Send renewal reminders
- Generate renewal quotes automatically
- Update lapsed renewals
- Send notifications

Usage:
    python run_renewal_job.py [--dry-run] [--verbose]

Options:
    --dry-run    Run without sending actual notifications
    --verbose    Show detailed output
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.renewal_service import RenewalService
from services.notification_service import get_notification_service
from models.renewal import RenewalRepository
from models.quote import QuoteRepository
from models.customer import CustomerRepository


def main():
    """Main entry point for renewal job."""
    parser = argparse.ArgumentParser(description='Daily renewal processing job')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without sending notifications')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')
    args = parser.parse_args()

    print("="*70)
    print(f"CSI Pivot Quote - Daily Renewal Processing Job")
    print(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dry_run:
        print("MODE: DRY RUN (no notifications will be sent)")
    print("="*70)
    print()

    # Initialize services
    renewal_service = RenewalService()
    notification_service = get_notification_service()
    renewal_repo = RenewalRepository()
    quote_repo = QuoteRepository()
    customer_repo = CustomerRepository()

    try:
        # Step 1: Process daily renewals
        print("Step 1: Processing daily renewals...")
        summary = renewal_service.process_daily_renewals()

        print(f"  ✓ Reminders sent: {summary['reminders_sent']}")
        print(f"  ✓ Quotes generated: {summary['quotes_generated']}")
        print(f"  ✓ Renewals lapsed: {summary['renewals_lapsed']}")

        if summary['errors']:
            print(f"  ⚠ Errors encountered: {len(summary['errors'])}")
            if args.verbose:
                for error in summary['errors']:
                    print(f"    - {error}")

        print()

        # Step 2: Send renewal quote notifications
        print("Step 2: Sending renewal quote notifications...")
        newly_generated = renewal_repo.get_all(status='generated')
        notifications_sent = 0

        for renewal in newly_generated:
            # Only send if generated today
            if renewal.renewal_generated_date == datetime.now().strftime('%Y-%m-%d'):
                quote = quote_repo.get_by_id(renewal.original_quote_id)
                renewal_quote = quote_repo.get_by_id(renewal.renewal_quote_id)
                customer = None
                if quote and quote.customer_id:
                    customer = customer_repo.get_by_id(quote.customer_id)

                if renewal_quote and customer and customer.email:
                    if not args.dry_run:
                        notification_service.send_renewal_quote_notification(
                            renewal, renewal_quote, customer
                        )
                        # Update status to 'sent'
                        renewal_repo.update_status(renewal.id, 'sent')
                    notifications_sent += 1

                    if args.verbose:
                        print(f"    - Sent renewal quote to {customer.name} ({customer.email})")

        print(f"  ✓ Renewal quote notifications sent: {notifications_sent}")
        print()

        # Step 3: Get renewal dashboard summary
        print("Step 3: Renewal Dashboard Summary")
        dashboard = renewal_service.get_renewal_dashboard_data()

        print(f"  Urgent renewals (< 30 days): {dashboard['urgent_renewals']}")
        print(f"  Upcoming renewals (< 60 days): {dashboard['upcoming_renewals_60']}")
        print(f"  Upcoming renewals (< 90 days): {dashboard['upcoming_renewals_90']}")
        print(f"  Pending reminders: {dashboard['reminders_pending']}")

        if dashboard['statistics'].get('by_status'):
            print("\n  Renewals by status:")
            for status, count in dashboard['statistics']['by_status'].items():
                print(f"    - {status}: {count}")

        if dashboard['statistics'].get('avg_premium_change'):
            avg_change = dashboard['statistics']['avg_premium_change']
            print(f"\n  Average premium change: {avg_change:+.2f}%")

        print()

        # Step 4: Show upcoming critical renewals
        if args.verbose:
            print("Step 4: Upcoming Critical Renewals (next 30 days)")
            upcoming = renewal_repo.get_upcoming_renewals(days_ahead=30)

            if upcoming:
                print(f"  {len(upcoming)} renewal(s) due in next 30 days:")
                for renewal in upcoming[:10]:  # Show first 10
                    quote = quote_repo.get_by_id(renewal.original_quote_id)
                    if quote:
                        days = renewal.calculate_days_until_expiration()
                        print(f"    - Quote {quote.quote_number}: {days} days " +
                              f"(expires {renewal.policy_end_date}) - Status: {renewal.status}")
            else:
                print("  No critical renewals in next 30 days")
            print()

        # Final summary
        print("="*70)
        print("Job completed successfully!")
        print(f"Total reminders sent: {summary['reminders_sent']}")
        print(f"Total quotes generated: {summary['quotes_generated']}")
        print(f"Total notifications sent: {notifications_sent}")
        print("="*70)

        return 0

    except Exception as e:
        print(f"\n✗ Job failed with error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
