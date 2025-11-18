"""
Rate lookup engine for insurance quotes.
Implements complex rate table lookup logic from Excel analysis.
"""

from typing import Optional, Dict, Tuple
from database.db_manager import get_db


class RateEngine:
    """Handles rate lookups based on equipment configuration."""

    def __init__(self):
        self.db = get_db()

    def get_pivot_rate(self, age: int, state: str, is_towable: bool,
                       has_me: bool, deductible_code: int) -> Optional[float]:
        """
        Get pivot equipment rate based on configuration.

        Args:
            age: Equipment age in years
            state: Two-letter state code
            is_towable: True if towable equipment
            has_me: True if M&E endorsement
            deductible_code: Deductible code (1-5)

        Returns:
            Rate as percentage (e.g., 2.33 for 2.33%)
        """
        # Determine age bracket
        if age < 20:
            return self._get_rate_under_20(state, is_towable, has_me, deductible_code)
        elif age <= 34:
            return self._get_rate_20_to_34(state, is_towable, has_me, deductible_code)
        else:  # 35+
            return self._get_rate_35_plus(state, is_corner=False)

    def _get_rate_under_20(self, state: str, is_towable: bool,
                           has_me: bool, deductible_code: int) -> Optional[float]:
        """Get rate for equipment under 20 years."""
        # Map deductible code to column name
        deduct_map = {1: "500", 2: "1000", 3: "2500", 4: "5000"}
        deductible = deduct_map.get(deductible_code, "2500")

        # Build column name
        equipment_type = "towable" if is_towable else "standard"
        me_suffix = "with_me" if has_me else "no_me"
        column = f"{equipment_type}_{deductible}_{me_suffix}"

        # Query database
        query = f"""
            SELECT {column} as rate
            FROM pivot_rates_under_20
            WHERE state_code = ?
            ORDER BY effective_date DESC
            LIMIT 1
        """

        results = self.db.execute_query(query, (state,))
        if results and results[0]['rate'] is not None:
            return float(results[0]['rate'])
        return None

    def _get_rate_20_to_34(self, state: str, is_towable: bool,
                           has_me: bool, deductible_code: int) -> Optional[float]:
        """Get rate for equipment 20-34 years."""
        deduct_map = {1: "500", 2: "1000", 3: "2500", 4: "5000"}
        deductible = deduct_map.get(deductible_code, "2500")

        equipment_type = "towable" if is_towable else "standard"
        me_suffix = "with_me" if has_me else "no_me"
        column = f"{equipment_type}_{deductible}_{me_suffix}"

        query = f"""
            SELECT {column} as rate
            FROM pivot_rates_20_to_34
            WHERE state_code = ?
            ORDER BY effective_date DESC
            LIMIT 1
        """

        results = self.db.execute_query(query, (state,))
        if results and results[0]['rate'] is not None:
            return float(results[0]['rate'])
        return None

    def _get_rate_35_plus(self, state: str, is_corner: bool) -> Optional[float]:
        """Get rate for equipment 35+ years."""
        column = "corner_rate" if is_corner else "standard_rate"

        query = f"""
            SELECT {column} as rate
            FROM pivot_rates_35_plus
            WHERE state_code = ?
            ORDER BY effective_date DESC
            LIMIT 1
        """

        results = self.db.execute_query(query, (state,))
        if results and results[0]['rate'] is not None:
            return float(results[0]['rate'])
        return None

    def get_ancillary_rate(self, age: int, state: str,
                           deductible_code: int, pivot_rate: float,
                           is_corner: bool = False) -> Optional[float]:
        """
        Get ancillary equipment rate.

        Args:
            age: Equipment age
            state: State code
            deductible_code: Deductible code (1-5)
            pivot_rate: Pivot rate (used if age > 34)
            is_corner: True if corner equipment

        Returns:
            Rate as percentage
        """
        # If age > 34, use pivot rate
        if age > 34:
            return pivot_rate

        # Otherwise lookup ancillary rate
        deduct_map = {1: "500", 2: "1000", 3: "2500", 4: "5000"}
        deductible = deduct_map.get(deductible_code, "1000")

        equipment_type = "corner" if is_corner else "standard"
        column = f"{equipment_type}_{deductible}"

        query = f"""
            SELECT {column} as rate
            FROM ancillary_rates
            WHERE state_code = ?
            ORDER BY effective_date DESC
            LIMIT 1
        """

        results = self.db.execute_query(query, (state,))
        if results and results[0]['rate'] is not None:
            return float(results[0]['rate'])
        return None

    def is_special_state(self, state: str) -> bool:
        """Check if state requires special surcharge (50% vs 25%)."""
        query = "SELECT is_special_state FROM states WHERE code = ?"
        results = self.db.execute_query(query, (state,))
        if results:
            return bool(results[0]['is_special_state'])
        return False
