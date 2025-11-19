#!/usr/bin/env python3
"""
Test script for policy cancellation functionality.
Tests the core cancellation services without requiring UI interaction.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.cancellation_service import CancellationService


def test_cancellation_imports():
    """Test that all cancellation-related modules can be imported."""
    print("Testing cancellation imports...")

    try:
        from services.cancellation_service import CancellationService
        print("✓ CancellationService imported successfully")

        from models.quote import Quote
        print("✓ Quote model imported successfully")

        # Check that Quote has cancellation fields
        q = Quote()
        assert hasattr(q, 'is_cancelled'), "Quote missing is_cancelled field"
        assert hasattr(q, 'cancellation_date'), "Quote missing cancellation_date field"
        assert hasattr(q, 'cancellation_reason'), "Quote missing cancellation_reason field"
        assert hasattr(q, 'cancellation_type'), "Quote missing cancellation_type field"
        assert hasattr(q, 'return_premium'), "Quote missing return_premium field"
        print("✓ Quote model has all cancellation fields")

        print("\n✓ All imports successful!")
        return True

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cancellation_service():
    """Test cancellation service initialization and constants."""
    print("\nTesting cancellation service...")

    try:
        service = CancellationService()
        print("✓ CancellationService initialized")

        # Check cancellation reasons
        print(f"\n  Cancellation Reasons ({len(service.CANCELLATION_REASONS)}):")
        for reason in service.CANCELLATION_REASONS:
            print(f"    - {reason}")

        # Check cancellation types
        print(f"\n  Cancellation Types ({len(service.CANCELLATION_TYPES)}):")
        for ctype in service.CANCELLATION_TYPES:
            print(f"    - {ctype}")

        # Test premium calculation logic
        print("\n  Testing premium calculation methods:")

        # Create a mock quote for testing calculations
        from models.quote import Quote
        test_quote = Quote(
            id=999,
            quote_number="TEST-001",
            total_premium=1200.00,
            effective_date="2024-01-01",
            expiration_date="2024-12-31",
            is_bound=1
        )

        # Test flat cancellation
        flat_refund = service._calculate_return_premium(
            test_quote,
            "2024-06-01",  # Cancel halfway through
            "Flat"
        )
        print(f"    Flat cancellation: ${flat_refund:,.2f} (expected: $1,200.00)")
        assert flat_refund == 1200.00, f"Flat refund should be $1,200.00, got ${flat_refund}"

        # Test pro-rata cancellation (halfway through = ~50% refund)
        prorata_refund = service._calculate_return_premium(
            test_quote,
            "2024-07-01",  # Cancel halfway through (6 months)
            "Pro-rata"
        )
        print(f"    Pro-rata cancellation (6 months in): ${prorata_refund:,.2f}")
        # Should be around $600 (50% of premium)
        assert 550 <= prorata_refund <= 650, f"Pro-rata refund should be ~$600, got ${prorata_refund}"

        # Test short-rate (90% of pro-rata)
        shortrate_refund = service._calculate_return_premium(
            test_quote,
            "2024-07-01",
            "Short-rate"
        )
        print(f"    Short-rate cancellation (6 months in): ${shortrate_refund:,.2f}")
        expected_shortrate = round(prorata_refund * 0.90, 2)
        assert abs(shortrate_refund - expected_shortrate) < 0.01, f"Short-rate should be ~90% of pro-rata (${expected_shortrate:.2f})"

        print("\n✓ Cancellation service tests passed!")
        return True

    except Exception as e:
        print(f"\n✗ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_schema():
    """Test that database has cancellation fields."""
    print("\nTesting database schema...")

    try:
        from database.db_manager import get_db
        db = get_db()

        # Check if cancellation fields exist in quotes table
        results = db.execute_query("PRAGMA table_info(quotes)")
        columns = {row['name'] for row in results}

        required_fields = [
            'is_cancelled',
            'cancellation_date',
            'cancellation_effective_date',
            'cancellation_reason',
            'cancellation_type',
            'return_premium',
            'cancelled_by_user_id',
            'cancellation_notes'
        ]

        print("  Checking for cancellation fields in quotes table:")
        all_present = True
        for field in required_fields:
            if field in columns:
                print(f"    ✓ {field}")
            else:
                print(f"    ✗ {field} MISSING!")
                all_present = False

        if all_present:
            print("\n✓ All cancellation fields present in database!")
            return True
        else:
            print("\n✗ Some fields are missing. Run migrate_cancellation.py")
            return False

    except Exception as e:
        print(f"\n✗ Database schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Policy Cancellation System Tests")
    print("=" * 60)
    print()

    success = True
    success = test_cancellation_imports() and success
    success = test_cancellation_service() and success
    success = test_database_schema() and success

    print()
    print("=" * 60)
    if success:
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nCancellation system is ready to use!")
        print("\nKey Features:")
        print("  • Cancel bound policies with reason and effective date")
        print("  • Three cancellation types: Flat, Pro-rata, Short-rate")
        print("  • Automatic return premium calculation")
        print("  • Reinstate cancelled policies")
        print("  • Renewal system skips cancelled policies")
        print("  • Visual indicators in Quote History")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
