"""
Quote data model and repository.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from database.db_manager import get_db


class Quote:
    """Quote data model."""

    def __init__(self, **kwargs):
        # Required fields
        self.id = kwargs.get('id')
        self.quote_number = kwargs.get('quote_number', '')
        self.pivot_amount = kwargs.get('pivot_amount', 0.0)
        self.equipment_age_years = kwargs.get('equipment_age_years', 0)
        self.pivot_deductible_code = kwargs.get('pivot_deductible_code', 3)
        self.ancillary_deductible_code = kwargs.get('ancillary_deductible_code', 2)
        self.term_months = kwargs.get('term_months', 12)
        self.state_code = kwargs.get('state_code', '')

        # Optional fields
        self.customer_id = kwargs.get('customer_id')
        self.agent_name = kwargs.get('agent_name', '')
        self.quote_date = kwargs.get('quote_date', str(date.today()))
        self.ancillary_amount = kwargs.get('ancillary_amount', 0.0)
        self.submersible_pump_amount = kwargs.get('submersible_pump_amount', 0.0)
        self.is_towable = kwargs.get('is_towable', 0)
        self.is_corner_or_long = kwargs.get('is_corner_or_long', 0)
        self.has_me_endorsement = kwargs.get('has_me_endorsement', 1)

        # Calculated fields
        self.pivot_rate = kwargs.get('pivot_rate')
        self.ancillary_rate = kwargs.get('ancillary_rate')
        self.pivot_premium = kwargs.get('pivot_premium')
        self.ancillary_premium = kwargs.get('ancillary_premium')
        self.submersible_charge = kwargs.get('submersible_charge')
        self.total_premium = kwargs.get('total_premium')

        # Alternative scenarios
        self.alt1_deductible = kwargs.get('alt1_deductible')
        self.alt1_rate = kwargs.get('alt1_rate')
        self.alt1_premium = kwargs.get('alt1_premium')
        self.alt2_deductible = kwargs.get('alt2_deductible')
        self.alt2_rate = kwargs.get('alt2_rate')
        self.alt2_premium = kwargs.get('alt2_premium')

        # Metadata
        self.status = kwargs.get('status', 'draft')
        self.notes = kwargs.get('notes', '')
        self.created_at = kwargs.get('created_at', '')
        self.updated_at = kwargs.get('updated_at', '')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quote':
        """Create Quote from dictionary."""
        return cls(**{k: v for k, v in data.items() if v is not None})

    def to_dict(self) -> Dict[str, Any]:
        """Convert Quote to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class QuoteRepository:
    """Repository for quote database operations."""

    def __init__(self):
        self.db = get_db()

    def create(self, quote: Quote) -> int:
        """Create new quote."""
        query = """
            INSERT INTO quotes (
                quote_number, customer_id, agent_name, quote_date,
                pivot_amount, ancillary_amount, submersible_pump_amount,
                equipment_age_years, is_towable, is_corner_or_long,
                has_me_endorsement, pivot_deductible_code,
                ancillary_deductible_code, term_months, state_code,
                pivot_rate, ancillary_rate, pivot_premium,
                ancillary_premium, submersible_charge, total_premium,
                alt1_deductible, alt1_rate, alt1_premium,
                alt2_deductible, alt2_rate, alt2_premium,
                status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            quote.quote_number, quote.customer_id, quote.agent_name,
            quote.quote_date, quote.pivot_amount, quote.ancillary_amount,
            quote.submersible_pump_amount, quote.equipment_age_years,
            quote.is_towable, quote.is_corner_or_long, quote.has_me_endorsement,
            quote.pivot_deductible_code, quote.ancillary_deductible_code,
            quote.term_months, quote.state_code, quote.pivot_rate,
            quote.ancillary_rate, quote.pivot_premium, quote.ancillary_premium,
            quote.submersible_charge, quote.total_premium,
            quote.alt1_deductible, quote.alt1_rate, quote.alt1_premium,
            quote.alt2_deductible, quote.alt2_rate, quote.alt2_premium,
            quote.status, quote.notes
        )
        return self.db.execute_insert(query, params)

    def get_by_id(self, quote_id: int) -> Optional[Quote]:
        """Get quote by ID."""
        query = "SELECT * FROM quotes WHERE id = ?"
        results = self.db.execute_query(query, (quote_id,))
        if results:
            return Quote.from_dict(dict(results[0]))
        return None

    def get_by_quote_number(self, quote_number: str) -> Optional[Quote]:
        """Get quote by quote number."""
        query = "SELECT * FROM quotes WHERE quote_number = ?"
        results = self.db.execute_query(query, (quote_number,))
        if results:
            return Quote.from_dict(dict(results[0]))
        return None

    def get_all(self, limit: int = 100) -> List[Quote]:
        """Get all quotes."""
        query = "SELECT * FROM quotes ORDER BY quote_date DESC LIMIT ?"
        results = self.db.execute_query(query, (limit,))
        return [Quote.from_dict(dict(row)) for row in results]

    def get_by_customer(self, customer_id: int) -> List[Quote]:
        """Get all quotes for a customer."""
        query = """
            SELECT * FROM quotes
            WHERE customer_id = ?
            ORDER BY quote_date DESC
        """
        results = self.db.execute_query(query, (customer_id,))
        return [Quote.from_dict(dict(row)) for row in results]

    def update(self, quote: Quote) -> bool:
        """Update existing quote."""
        query = """
            UPDATE quotes SET
                customer_id = ?, agent_name = ?, quote_date = ?,
                pivot_amount = ?, ancillary_amount = ?,
                submersible_pump_amount = ?, equipment_age_years = ?,
                is_towable = ?, is_corner_or_long = ?,
                has_me_endorsement = ?, pivot_deductible_code = ?,
                ancillary_deductible_code = ?, term_months = ?,
                state_code = ?, pivot_rate = ?, ancillary_rate = ?,
                pivot_premium = ?, ancillary_premium = ?,
                submersible_charge = ?, total_premium = ?,
                alt1_deductible = ?, alt1_rate = ?, alt1_premium = ?,
                alt2_deductible = ?, alt2_rate = ?, alt2_premium = ?,
                status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (
            quote.customer_id, quote.agent_name, quote.quote_date,
            quote.pivot_amount, quote.ancillary_amount,
            quote.submersible_pump_amount, quote.equipment_age_years,
            quote.is_towable, quote.is_corner_or_long,
            quote.has_me_endorsement, quote.pivot_deductible_code,
            quote.ancillary_deductible_code, quote.term_months,
            quote.state_code, quote.pivot_rate, quote.ancillary_rate,
            quote.pivot_premium, quote.ancillary_premium,
            quote.submersible_charge, quote.total_premium,
            quote.alt1_deductible, quote.alt1_rate, quote.alt1_premium,
            quote.alt2_deductible, quote.alt2_rate, quote.alt2_premium,
            quote.status, quote.notes, quote.id
        )
        rows = self.db.execute_update(query, params)
        return rows > 0

    def delete(self, quote_id: int) -> bool:
        """Delete quote."""
        query = "DELETE FROM quotes WHERE id = ?"
        rows = self.db.execute_update(query, (quote_id,))
        return rows > 0

    def generate_quote_number(self) -> str:
        """Generate unique quote number."""
        query = "SELECT MAX(id) as max_id FROM quotes"
        result = self.db.execute_query(query)
        max_id = result[0]['max_id'] if result[0]['max_id'] else 0
        next_id = max_id + 1
        return f"Q-{next_id:05d}"
