"""
Premium calculation logic for insurance quotes.
"""

from typing import Dict, Tuple, Optional
from .rate_engine import RateEngine


class PremiumCalculator:
    """Calculates insurance premiums based on rates and amounts."""

    def __init__(self):
        self.rate_engine = RateEngine()

    def calculate_premium(self, pivot_amount: float, rate: float,
                         term_months: int) -> float:
        """
        Calculate premium using the formula from Excel:
        Premium = (Amount / 100) × Rate × (Term / 12)

        Args:
            pivot_amount: Insured amount
            rate: Rate as percentage (e.g., 2.33 for 2.33%)
            term_months: Term in months

        Returns:
            Premium amount
        """
        if rate is None:
            return 0.0
        return (pivot_amount / 100.0) * rate * (term_months / 12.0)

    def calculate_submersible_charge(self, pump_amount: float,
                                     ancillary_rate: float,
                                     term_months: int,
                                     is_special_state: bool) -> float:
        """
        Calculate submersible pump surcharge.

        Args:
            pump_amount: Submersible pump insured amount
            ancillary_rate: Ancillary rate
            term_months: Term in months
            is_special_state: True if TX, OK, GA, KS, MN, NE

        Returns:
            Surcharge amount
        """
        if pump_amount == 0 or ancillary_rate is None:
            return 0.0

        # 50% surcharge for special states, 25% for others
        surcharge_rate = 0.50 if is_special_state else 0.25

        return (pump_amount / 100.0) * ancillary_rate * surcharge_rate * (term_months / 12.0)

    def calculate_complete_quote(self, **kwargs) -> Dict[str, float]:
        """
        Calculate complete quote with all scenarios.

        Required kwargs:
            - pivot_amount: float
            - ancillary_amount: float
            - submersible_pump_amount: float
            - equipment_age_years: int
            - is_towable: bool
            - is_corner_or_long: bool
            - has_me_endorsement: bool
            - pivot_deductible_code: int
            - ancillary_deductible_code: int
            - term_months: int
            - state_code: str

        Returns:
            Dictionary with all calculated values
        """
        # Extract parameters
        pivot_amount = kwargs['pivot_amount']
        ancillary_amount = kwargs['ancillary_amount']
        submersible_pump_amount = kwargs['submersible_pump_amount']
        age = kwargs['equipment_age_years']
        is_towable = kwargs['is_towable']
        is_corner = kwargs['is_corner_or_long']
        has_me = kwargs['has_me_endorsement']
        pivot_ded = kwargs['pivot_deductible_code']
        anc_ded = kwargs['ancillary_deductible_code']
        term = kwargs['term_months']
        state = kwargs['state_code']

        # Get rates
        pivot_rate = self.rate_engine.get_pivot_rate(
            age, state, is_towable, has_me, pivot_ded
        )

        ancillary_rate = self.rate_engine.get_ancillary_rate(
            age, state, anc_ded, pivot_rate or 0, is_corner
        )

        # Calculate premiums
        pivot_premium = self.calculate_premium(pivot_amount, pivot_rate or 0, term)
        ancillary_premium = self.calculate_premium(ancillary_amount, ancillary_rate or 0, term)

        # Calculate submersible charge
        is_special = self.rate_engine.is_special_state(state)
        submersible_charge = self.calculate_submersible_charge(
            submersible_pump_amount, ancillary_rate or 0, term, is_special
        )

        total_premium = pivot_premium + ancillary_premium + submersible_charge

        # Calculate alternative scenarios (different deductibles)
        alt1_rate, alt1_premium = None, None
        alt2_rate, alt2_premium = None, None
        alt1_deductible, alt2_deductible = None, None

        # Alternative 1: Lower deductible (if possible)
        if pivot_ded > 1:
            alt1_deductible = pivot_ded - 1
            alt1_rate = self.rate_engine.get_pivot_rate(
                age, state, is_towable, has_me, alt1_deductible
            )
            if alt1_rate:
                alt1_premium = self.calculate_premium(pivot_amount, alt1_rate, term)
                if ancillary_amount > 0:
                    alt1_anc_rate = self.rate_engine.get_ancillary_rate(
                        age, state, alt1_deductible, alt1_rate, is_corner
                    )
                    alt1_premium += self.calculate_premium(ancillary_amount, alt1_anc_rate or 0, term)
                if submersible_pump_amount > 0:
                    alt1_anc_rate = self.rate_engine.get_ancillary_rate(
                        age, state, alt1_deductible, alt1_rate, is_corner
                    )
                    alt1_premium += self.calculate_submersible_charge(
                        submersible_pump_amount, alt1_anc_rate or 0, term, is_special
                    )

        # Alternative 2: Higher deductible (if possible)
        if pivot_ded < 4:
            alt2_deductible = pivot_ded + 1
            alt2_rate = self.rate_engine.get_pivot_rate(
                age, state, is_towable, has_me, alt2_deductible
            )
            if alt2_rate:
                alt2_premium = self.calculate_premium(pivot_amount, alt2_rate, term)
                if ancillary_amount > 0:
                    alt2_anc_rate = self.rate_engine.get_ancillary_rate(
                        age, state, alt2_deductible, alt2_rate, is_corner
                    )
                    alt2_premium += self.calculate_premium(ancillary_amount, alt2_anc_rate or 0, term)
                if submersible_pump_amount > 0:
                    alt2_anc_rate = self.rate_engine.get_ancillary_rate(
                        age, state, alt2_deductible, alt2_rate, is_corner
                    )
                    alt2_premium += self.calculate_submersible_charge(
                        submersible_pump_amount, alt2_anc_rate or 0, term, is_special
                    )

        return {
            'pivot_rate': pivot_rate,
            'ancillary_rate': ancillary_rate,
            'pivot_premium': round(pivot_premium, 2),
            'ancillary_premium': round(ancillary_premium, 2),
            'submersible_charge': round(submersible_charge, 2),
            'total_premium': round(total_premium, 2),
            'alt1_deductible': alt1_deductible,
            'alt1_rate': alt1_rate,
            'alt1_premium': round(alt1_premium, 2) if alt1_premium else None,
            'alt2_deductible': alt2_deductible,
            'alt2_rate': alt2_rate,
            'alt2_premium': round(alt2_premium, 2) if alt2_premium else None,
        }

    @staticmethod
    def deductible_code_to_amount(code: int) -> int:
        """Convert deductible code to dollar amount."""
        mapping = {1: 500, 2: 1000, 3: 2500, 4: 5000}
        return mapping.get(code, 2500)

    @staticmethod
    def deductible_amount_to_code(amount: int) -> int:
        """Convert deductible amount to code."""
        mapping = {500: 1, 1000: 2, 2500: 3, 5000: 4}
        return mapping.get(amount, 3)
