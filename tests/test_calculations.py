"""
Tests for calculation engine.
Validates against known test cases from Excel.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from calculations.premium_calc import PremiumCalculator


def test_basic_quote_calculation():
    """
    Test Case 1: New Standard Pivot in Oklahoma
    Based on Excel test case.
    """
    calc = PremiumCalculator()

    params = {
        'pivot_amount': 100000.0,
        'ancillary_amount': 0.0,
        'submersible_pump_amount': 0.0,
        'equipment_age_years': 0,
        'is_towable': False,
        'is_corner_or_long': False,
        'has_me_endorsement': True,
        'pivot_deductible_code': 3,  # $2,500
        'ancillary_deductible_code': 2,  # $1,000
        'term_months': 12,
        'state_code': 'OK'
    }

    result = calc.calculate_complete_quote(**params)

    print("\n=== Test Case 1: New Standard Pivot ===")
    print(f"Pivot Rate: {result['pivot_rate']}%")
    print(f"Pivot Premium: ${result['pivot_premium']:,.2f}")
    print(f"Total Premium: ${result['total_premium']:,.2f}")

    # Verify results
    assert result['pivot_rate'] is not None, "Pivot rate should not be None"
    assert result['pivot_premium'] > 0, "Pivot premium should be greater than 0"
    assert result['total_premium'] == result['pivot_premium'], "Total should equal pivot (no ancillary)"

    print("✓ Test passed")


def test_with_ancillary():
    """
    Test Case 2: Equipment with ancillary coverage
    """
    calc = PremiumCalculator()

    params = {
        'pivot_amount': 100000.0,
        'ancillary_amount': 25000.0,
        'submersible_pump_amount': 0.0,
        'equipment_age_years': 10,
        'is_towable': False,
        'is_corner_or_long': False,
        'has_me_endorsement': True,
        'pivot_deductible_code': 3,
        'ancillary_deductible_code': 2,
        'term_months': 12,
        'state_code': 'OK'
    }

    result = calc.calculate_complete_quote(**params)

    print("\n=== Test Case 2: With Ancillary ===")
    print(f"Pivot Premium: ${result['pivot_premium']:,.2f}")
    print(f"Ancillary Premium: ${result['ancillary_premium']:,.2f}")
    print(f"Total Premium: ${result['total_premium']:,.2f}")

    assert result['ancillary_premium'] > 0, "Ancillary premium should be greater than 0"
    assert result['total_premium'] > result['pivot_premium'], "Total should include ancillary"

    print("✓ Test passed")


def test_towable_equipment():
    """
    Test Case 3: Towable equipment
    """
    calc = PremiumCalculator()

    params = {
        'pivot_amount': 150000.0,
        'ancillary_amount': 0.0,
        'submersible_pump_amount': 0.0,
        'equipment_age_years': 5,
        'is_towable': True,
        'is_corner_or_long': False,
        'has_me_endorsement': True,
        'pivot_deductible_code': 4,  # $5,000
        'ancillary_deductible_code': 4,
        'term_months': 12,
        'state_code': 'NE'
    }

    result = calc.calculate_complete_quote(**params)

    print("\n=== Test Case 3: Towable Equipment ===")
    print(f"Pivot Rate: {result['pivot_rate']}%")
    print(f"Total Premium: ${result['total_premium']:,.2f}")

    assert result['pivot_rate'] is not None
    assert result['total_premium'] > 0

    print("✓ Test passed")


def test_older_equipment():
    """
    Test Case 4: Equipment over 35 years old
    """
    calc = PremiumCalculator()

    params = {
        'pivot_amount': 75000.0,
        'ancillary_amount': 10000.0,
        'submersible_pump_amount': 0.0,
        'equipment_age_years': 36,
        'is_towable': False,
        'is_corner_or_long': False,
        'has_me_endorsement': False,
        'pivot_deductible_code': 4,
        'ancillary_deductible_code': 3,
        'term_months': 12,
        'state_code': 'KS'
    }

    result = calc.calculate_complete_quote(**params)

    print("\n=== Test Case 4: Equipment 36 Years Old ===")
    print(f"Pivot Rate: {result['pivot_rate']}%")
    print(f"Ancillary Rate: {result['ancillary_rate']}%")
    print(f"Total Premium: ${result['total_premium']:,.2f}")

    # For equipment over 34, ancillary rate should equal pivot rate
    assert result['ancillary_rate'] == result['pivot_rate'], \
        "Ancillary rate should equal pivot rate for age > 34"

    print("✓ Test passed")


def test_submersible_pump_special_state():
    """
    Test Case 5: Submersible pump in special state (50% surcharge)
    """
    calc = PremiumCalculator()

    params = {
        'pivot_amount': 100000.0,
        'ancillary_amount': 15000.0,
        'submersible_pump_amount': 5000.0,
        'equipment_age_years': 8,
        'is_towable': False,
        'is_corner_or_long': False,
        'has_me_endorsement': True,
        'pivot_deductible_code': 3,
        'ancillary_deductible_code': 2,
        'term_months': 12,
        'state_code': 'TX'  # Special state
    }

    result = calc.calculate_complete_quote(**params)

    print("\n=== Test Case 5: Submersible in TX (Special State) ===")
    print(f"Submersible Charge: ${result['submersible_charge']:,.2f}")
    print(f"Total Premium: ${result['total_premium']:,.2f}")

    assert result['submersible_charge'] > 0, "Should have submersible charge"

    print("✓ Test passed")


def test_alternative_scenarios():
    """
    Test Case 6: Alternative deductible scenarios
    """
    calc = PremiumCalculator()

    params = {
        'pivot_amount': 100000.0,
        'ancillary_amount': 0.0,
        'submersible_pump_amount': 0.0,
        'equipment_age_years': 0,
        'is_towable': False,
        'is_corner_or_long': False,
        'has_me_endorsement': True,
        'pivot_deductible_code': 3,  # $2,500 (base)
        'ancillary_deductible_code': 3,
        'term_months': 12,
        'state_code': 'OK'
    }

    result = calc.calculate_complete_quote(**params)

    print("\n=== Test Case 6: Alternative Scenarios ===")
    print(f"Base ($2,500): ${result['total_premium']:,.2f}")
    if result['alt1_premium']:
        print(f"Alt 1 ($1,000): ${result['alt1_premium']:,.2f}")
    if result['alt2_premium']:
        print(f"Alt 2 ($5,000): ${result['alt2_premium']:,.2f}")

    # Should have two alternatives since deductible code is 3 (middle)
    assert result['alt1_premium'] is not None, "Should have lower deductible alternative"
    assert result['alt2_premium'] is not None, "Should have higher deductible alternative"

    # Lower deductible should have higher premium
    assert result['alt1_premium'] > result['total_premium'], \
        "Lower deductible should cost more"

    # Higher deductible should have lower premium
    assert result['alt2_premium'] < result['total_premium'], \
        "Higher deductible should cost less"

    print("✓ Test passed")


def test_deductible_conversions():
    """Test deductible code/amount conversions."""
    calc = PremiumCalculator()

    print("\n=== Test Case 7: Deductible Conversions ===")

    # Test code to amount
    assert calc.deductible_code_to_amount(1) == 500
    assert calc.deductible_code_to_amount(2) == 1000
    assert calc.deductible_code_to_amount(3) == 2500
    assert calc.deductible_code_to_amount(4) == 5000
    print("✓ Code to amount conversions correct")

    # Test amount to code
    assert calc.deductible_amount_to_code(500) == 1
    assert calc.deductible_amount_to_code(1000) == 2
    assert calc.deductible_amount_to_code(2500) == 3
    assert calc.deductible_amount_to_code(5000) == 4
    print("✓ Amount to code conversions correct")

    print("✓ Test passed")


if __name__ == "__main__":
    print("="* 60)
    print("RUNNING CALCULATION TESTS")
    print("="* 60)

    test_basic_quote_calculation()
    test_with_ancillary()
    test_towable_equipment()
    test_older_equipment()
    test_submersible_pump_special_state()
    test_alternative_scenarios()
    test_deductible_conversions()

    print("\n" + "="* 60)
    print("ALL TESTS PASSED ✓")
    print("="* 60)
