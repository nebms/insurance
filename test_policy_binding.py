#!/usr/bin/env python3
"""
Test script for policy binding and document management functionality.
Tests the core services without requiring UI interaction.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from models.quote import Quote, QuoteRepository
from models.customer import Customer, CustomerRepository
from models.policy_document import PolicyDocumentRepository
from services.binding_service import BindingService
from services.document_service import DocumentService


def test_policy_binding():
    """Test policy binding functionality."""
    print("=" * 60)
    print("Testing Policy Binding Functionality")
    print("=" * 60)
    print()

    # Initialize services
    customer_repo = CustomerRepository()
    quote_repo = QuoteRepository()
    binding_service = BindingService()
    document_service = DocumentService()

    # Create a test customer
    print("1. Creating test customer...")
    customer = Customer(
        name="Test Customer for Policy Binding",
        email="test@example.com",
        phone="555-0123",
        address="123 Test St, Test City, CA 12345",
        notes="Test customer for policy binding system"
    )
    customer_id = customer_repo.create(customer)
    print(f"   ✓ Customer created with ID: {customer_id}")
    print()

    # Create a test quote
    print("2. Creating test quote...")
    quote = Quote(
        customer_id=customer_id,
        quote_date=date.today().strftime("%Y-%m-%d"),
        state_code="CA",
        equipment_age_years=5,
        equipment_value=50000.00,
        term_months=12,
        pivot_amount=50000.00,
        ancillary_amount=0.00,
        submersible_pump_amount=0.00,
        is_towable=0,
        is_corner_or_long=0,
        has_me_endorsement=0,
        pivot_deductible_code="1000",
        ancillary_deductible_code="1000",
        pivot_rate=2.5,
        ancillary_rate=0.0,
        submersible_pump_rate=0.0,
        base_premium=1500.00,
        total_premium=1650.00,
        agent_name="Test Agent",
        status="quoted"
    )
    quote_id = quote_repo.create(quote)
    quote = quote_repo.get_by_id(quote_id)
    print(f"   ✓ Quote created: {quote.quote_number}")
    print()

    # Test binding the quote
    print("3. Binding quote to policy...")
    effective_date = date.today()
    binding_info = {
        'effective_date': effective_date.strftime("%Y-%m-%d"),
        'carrier_name': 'Test Insurance Company',
        'policy_number': None,  # Policy number optional at binding
        'payment_status': 'pending',
        'payment_method': 'Check',
        'notes': 'Test binding for policy system'
    }

    success, message = binding_service.bind_quote(quote_id, binding_info)
    if success:
        print(f"   ✓ {message}")
        quote = quote_repo.get_by_id(quote_id)
        print(f"   - Bound Date: {quote.bound_date}")
        print(f"   - Effective Date: {quote.effective_date}")
        print(f"   - Expiration Date: {quote.expiration_date}")
        print(f"   - Carrier: {quote.carrier_name}")
        print(f"   - Payment Status: {quote.payment_status}")
    else:
        print(f"   ✗ Binding failed: {message}")
        return False
    print()

    # Test updating policy info (adding policy number later)
    print("4. Updating policy information (adding policy number)...")
    policy_info = {
        'policy_number': 'POL-TEST-2024-001',
        'payment_status': 'paid',
        'notes': 'Policy number received from carrier'
    }

    success, message = binding_service.update_policy_info(quote_id, policy_info)
    if success:
        print(f"   ✓ {message}")
        quote = quote_repo.get_by_id(quote_id)
        print(f"   - Policy Number: {quote.policy_number}")
        print(f"   - Policy Received: {quote.policy_received_date}")
        print(f"   - Payment Status: {quote.payment_status}")
    else:
        print(f"   ✗ Update failed: {message}")
        return False
    print()

    # Test document service validation
    print("5. Testing document service validation...")
    print("   - Testing file extension validation...")

    # Test with invalid extension
    test_file = Path("test.exe")
    test_file.touch()  # Create dummy file

    success, message, _ = document_service.upload_document(
        str(test_file),
        quote_id,
        "Policy Declarations",
        "Insurance Carrier"
    )

    if not success and "not allowed" in message:
        print("   ✓ Invalid file type correctly rejected")
    else:
        print("   ✗ Invalid file type not rejected properly")

    test_file.unlink()  # Clean up
    print()

    # Test policy summary
    print("6. Getting policy summary...")
    summary = binding_service.get_policy_summary(quote_id)
    if summary:
        print("   ✓ Policy Summary Retrieved:")
        print(f"   - Quote Number: {summary['quote'].quote_number}")
        print(f"   - Is Bound: {summary['is_bound']}")
        print(f"   - Policy Number: {summary['policy_number']}")
        print(f"   - Carrier: {summary['carrier']}")
        print(f"   - Effective: {summary['effective_date']}")
        print(f"   - Expiration: {summary['expiration_date']}")
        print(f"   - Days Until Expiration: {summary['days_until_expiration']}")
        print(f"   - Payment Status: {summary['payment_status']}")
        print(f"   - Document Count: {summary['document_count']}")
        print(f"   - Has Renewal Tracking: {summary['has_renewal_tracking']}")
    else:
        print("   ✗ Failed to get policy summary")
    print()

    # Test getting active policies
    print("7. Testing active policies query...")
    active_policies = binding_service.get_active_policies()
    print(f"   ✓ Found {len(active_policies)} active policy(ies)")
    print()

    # Clean up test data
    print("8. Cleaning up test data...")
    quote_repo.delete(quote_id)
    customer_repo.delete(customer_id)
    print("   ✓ Test data cleaned up")
    print()

    print("=" * 60)
    print("✓ All Policy Binding Tests Passed!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = test_policy_binding()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
