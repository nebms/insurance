"""
Data loading utilities for initial database population.
"""

from typing import List, Dict
from .db_manager import get_db


# All 50 US states
US_STATES = [
    ('AL', 'Alabama', 0),
    ('AK', 'Alaska', 0),
    ('AZ', 'Arizona', 0),
    ('AR', 'Arkansas', 0),
    ('CA', 'California', 0),
    ('CO', 'Colorado', 0),
    ('CT', 'Connecticut', 0),
    ('DE', 'Delaware', 0),
    ('FL', 'Florida', 0),
    ('GA', 'Georgia', 1),  # Special state
    ('HI', 'Hawaii', 0),
    ('ID', 'Idaho', 0),
    ('IL', 'Illinois', 0),
    ('IN', 'Indiana', 0),
    ('IA', 'Iowa', 0),
    ('KS', 'Kansas', 1),  # Special state
    ('KY', 'Kentucky', 0),
    ('LA', 'Louisiana', 0),
    ('ME', 'Maine', 0),
    ('MD', 'Maryland', 0),
    ('MA', 'Massachusetts', 0),
    ('MI', 'Michigan', 0),
    ('MN', 'Minnesota', 1),  # Special state
    ('MS', 'Mississippi', 0),
    ('MO', 'Missouri', 0),
    ('MT', 'Montana', 0),
    ('NE', 'Nebraska', 1),  # Special state
    ('NV', 'Nevada', 0),
    ('NH', 'New Hampshire', 0),
    ('NJ', 'New Jersey', 0),
    ('NM', 'New Mexico', 0),
    ('NY', 'New York', 0),
    ('NC', 'North Carolina', 0),
    ('ND', 'North Dakota', 0),
    ('OH', 'Ohio', 0),
    ('OK', 'Oklahoma', 1),  # Special state
    ('OR', 'Oregon', 0),
    ('PA', 'Pennsylvania', 0),
    ('RI', 'Rhode Island', 0),
    ('SC', 'South Carolina', 0),
    ('SD', 'South Dakota', 0),
    ('TN', 'Tennessee', 0),
    ('TX', 'Texas', 1),  # Special state
    ('UT', 'Utah', 0),
    ('VT', 'Vermont', 0),
    ('VA', 'Virginia', 0),
    ('WA', 'Washington', 0),
    ('WV', 'West Virginia', 0),
    ('WI', 'Wisconsin', 0),
    ('WY', 'Wyoming', 0),
]


def load_states():
    """Load all US states into database."""
    db = get_db()

    # Clear existing states
    db.execute_update("DELETE FROM states")

    # Insert all states
    query = "INSERT INTO states (code, name, is_special_state) VALUES (?, ?, ?)"

    for code, name, is_special in US_STATES:
        db.execute_insert(query, (code, name, is_special))

    count = db.get_table_row_count('states')
    print(f"✓ Loaded {count} states")

    # List special states
    special = [s[1] for s in US_STATES if s[2] == 1]
    print(f"✓ Special states (50% surcharge): {', '.join(special)}")


def load_sample_rates():
    """
    Load sample rate data for testing.
    IMPORTANT: This uses placeholder rates.
    Replace with actual rates from CSV files.
    """
    db = get_db()
    effective_date = "2025-01-01"

    # Sample rate for Oklahoma (for testing)
    # These are example rates - replace with actual data
    sample_states = ['OK', 'NE', 'TX', 'KS']

    for state in sample_states:
        # Pivot rates under 20
        query = """
            INSERT OR REPLACE INTO pivot_rates_under_20 (
                state_code, effective_date,
                standard_500_no_me, standard_500_with_me,
                standard_1000_no_me, standard_1000_with_me,
                standard_2500_no_me, standard_2500_with_me,
                standard_5000_no_me, standard_5000_with_me,
                towable_500_no_me, towable_500_with_me,
                towable_1000_no_me, towable_1000_with_me,
                towable_2500_no_me, towable_2500_with_me,
                towable_5000_no_me, towable_5000_with_me
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Sample rates (replace with actual)
        params = (
            state, effective_date,
            2.08, 2.33,  # standard 500
            1.89, 2.14,  # standard 1000
            1.58, 1.95,  # standard 2500
            1.41, 1.74,  # standard 5000
            2.41, 2.66,  # towable 500
            2.22, 2.47,  # towable 1000
            1.91, 2.28,  # towable 2500
            1.74, 2.07,  # towable 5000
        )
        db.execute_insert(query, params)

        # Pivot rates 20-34 (slightly higher)
        query = """
            INSERT OR REPLACE INTO pivot_rates_20_to_34 (
                state_code, effective_date,
                standard_500_no_me, standard_500_with_me,
                standard_1000_no_me, standard_1000_with_me,
                standard_2500_no_me, standard_2500_with_me,
                standard_5000_no_me, standard_5000_with_me,
                towable_500_no_me, towable_500_with_me,
                towable_1000_no_me, towable_1000_with_me,
                towable_2500_no_me, towable_2500_with_me,
                towable_5000_no_me, towable_5000_with_me
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            state, effective_date,
            2.28, 2.53,  # standard 500
            2.09, 2.34,  # standard 1000
            1.78, 2.15,  # standard 2500
            1.61, 1.94,  # standard 5000
            2.61, 2.86,  # towable 500
            2.42, 2.67,  # towable 1000
            2.11, 2.48,  # towable 2500
            1.94, 2.27,  # towable 5000
        )
        db.execute_insert(query, params)

        # Pivot rates 35+
        query = """
            INSERT OR REPLACE INTO pivot_rates_35_plus (
                state_code, effective_date, standard_rate, corner_rate
            ) VALUES (?, ?, ?, ?)
        """
        params = (state, effective_date, 2.50, 2.75)
        db.execute_insert(query, params)

        # Ancillary rates
        query = """
            INSERT OR REPLACE INTO ancillary_rates (
                state_code, effective_date,
                standard_500, standard_1000, standard_2500, standard_5000,
                corner_500, corner_1000, corner_2500, corner_5000
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            state, effective_date,
            3.85, 3.63, 3.02, 2.70,  # standard
            4.58, 4.36, 3.75, 3.43,  # corner
        )
        db.execute_insert(query, params)

    print(f"✓ Loaded sample rates for {len(sample_states)} states")
    print(f"⚠️  IMPORTANT: Replace sample rates with actual CSV data!")


if __name__ == "__main__":
    print("Loading initial data...")
    load_states()
    load_sample_rates()
    print("✓ Data loading complete")
