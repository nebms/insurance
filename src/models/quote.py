"""
Quote data model and repository.
Updated to support multiple pivot equipment items via line items.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from database.db_manager import get_db
from models.quote_line_item import QuoteLineItem, QuoteLineItemRepository


class Quote:
    """Quote data model (header-level information)."""

    def __init__(self, **kwargs):
        # Required fields
        self.id = kwargs.get('id')
        self.quote_number = kwargs.get('quote_number', '')
        self.state_code = kwargs.get('state_code', '')
        self.term_months = kwargs.get('term_months', 12)

        # Optional fields
        self.customer_id = kwargs.get('customer_id')
        self.agent_name = kwargs.get('agent_name', '')
        self.quote_date = kwargs.get('quote_date', str(date.today()))

        # Totals (aggregated from line items)
        self.total_premium = kwargs.get('total_premium', 0.0)

        # Metadata
        self.status = kwargs.get('status', 'draft')
        self.notes = kwargs.get('notes', '')
        self.created_at = kwargs.get('created_at', '')
        self.updated_at = kwargs.get('updated_at', '')

        # Line items (not stored in quotes table, loaded separately)
        self.line_items: List[QuoteLineItem] = []

        # Legacy fields for backward compatibility (single pivot quotes)
        # These will be populated from the first line item if it exists
        self.pivot_amount = kwargs.get('pivot_amount', 0.0)
        self.equipment_age_years = kwargs.get('equipment_age_years', 0)
        self.pivot_deductible_code = kwargs.get('pivot_deductible_code', 3)
        self.ancillary_deductible_code = kwargs.get('ancillary_deductible_code', 2)
        self.ancillary_amount = kwargs.get('ancillary_amount', 0.0)
        self.submersible_pump_amount = kwargs.get('submersible_pump_amount', 0.0)
        self.is_towable = kwargs.get('is_towable', 0)
        self.is_corner_or_long = kwargs.get('is_corner_or_long', 0)
        self.has_me_endorsement = kwargs.get('has_me_endorsement', 1)
        self.pivot_rate = kwargs.get('pivot_rate')
        self.ancillary_rate = kwargs.get('ancillary_rate')
        self.pivot_premium = kwargs.get('pivot_premium')
        self.ancillary_premium = kwargs.get('ancillary_premium')
        self.submersible_charge = kwargs.get('submersible_charge')
        self.alt1_deductible = kwargs.get('alt1_deductible')
        self.alt1_rate = kwargs.get('alt1_rate')
        self.alt1_premium = kwargs.get('alt1_premium')
        self.alt2_deductible = kwargs.get('alt2_deductible')
        self.alt2_rate = kwargs.get('alt2_rate')
        self.alt2_premium = kwargs.get('alt2_premium')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quote':
        """Create Quote from dictionary."""
        return cls(**{k: v for k, v in data.items() if v is not None})

    def to_dict(self) -> Dict[str, Any]:
        """Convert Quote to dictionary."""
        return {k: v for k, v in self.__dict__.items()
                if v is not None and k != 'line_items'}

    def has_multiple_items(self) -> bool:
        """Check if quote has multiple pivot items."""
        return len(self.line_items) > 1

    def populate_from_first_line_item(self):
        """Populate legacy fields from first line item for backward compatibility."""
        if self.line_items:
            first_item = self.line_items[0]
            self.pivot_amount = first_item.pivot_amount
            self.equipment_age_years = first_item.equipment_age_years
            self.pivot_deductible_code = first_item.pivot_deductible_code
            self.ancillary_deductible_code = first_item.ancillary_deductible_code
            self.ancillary_amount = first_item.ancillary_amount
            self.submersible_pump_amount = first_item.submersible_pump_amount
            self.is_towable = first_item.is_towable
            self.is_corner_or_long = first_item.is_corner_or_long
            self.has_me_endorsement = first_item.has_me_endorsement
            self.pivot_rate = first_item.pivot_rate
            self.ancillary_rate = first_item.ancillary_rate
            self.pivot_premium = first_item.pivot_premium
            self.ancillary_premium = first_item.ancillary_premium
            self.submersible_charge = first_item.submersible_charge
            self.alt1_deductible = first_item.alt1_deductible
            self.alt1_rate = first_item.alt1_rate
            self.alt1_premium = first_item.alt1_premium
            self.alt2_deductible = first_item.alt2_deductible
            self.alt2_rate = first_item.alt2_rate
            self.alt2_premium = first_item.alt2_premium


class QuoteRepository:
    """Repository for quote database operations."""

    def __init__(self):
        self.db = get_db()
        self.line_item_repo = QuoteLineItemRepository()

    def create(self, quote: Quote, line_items: Optional[List[QuoteLineItem]] = None) -> int:
        """
        Create new quote with line items.

        Args:
            quote: Quote header information
            line_items: List of line items (if None, creates single line item from quote fields)

        Returns:
            Quote ID
        """
        # Create quote header
        query = """
            INSERT INTO quotes (
                quote_number, customer_id, agent_name, quote_date,
                state_code, term_months, total_premium, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            quote.quote_number, quote.customer_id, quote.agent_name,
            quote.quote_date, quote.state_code, quote.term_months,
            quote.total_premium, quote.status, quote.notes
        )
        quote_id = self.db.execute_insert(query, params)

        # Create line items
        if line_items is None:
            # Backward compatibility: create single line item from quote fields
            line_item = QuoteLineItem(
                quote_id=quote_id,
                line_number=1,
                pivot_amount=quote.pivot_amount,
                ancillary_amount=quote.ancillary_amount,
                submersible_pump_amount=quote.submersible_pump_amount,
                equipment_age_years=quote.equipment_age_years,
                is_towable=quote.is_towable,
                is_corner_or_long=quote.is_corner_or_long,
                has_me_endorsement=quote.has_me_endorsement,
                pivot_deductible_code=quote.pivot_deductible_code,
                ancillary_deductible_code=quote.ancillary_deductible_code,
                pivot_rate=quote.pivot_rate,
                ancillary_rate=quote.ancillary_rate,
                pivot_premium=quote.pivot_premium,
                ancillary_premium=quote.ancillary_premium,
                submersible_charge=quote.submersible_charge,
                line_total_premium=quote.total_premium,
                alt1_deductible=quote.alt1_deductible,
                alt1_rate=quote.alt1_rate,
                alt1_premium=quote.alt1_premium,
                alt2_deductible=quote.alt2_deductible,
                alt2_rate=quote.alt2_rate,
                alt2_premium=quote.alt2_premium
            )
            self.line_item_repo.create(line_item)
        else:
            # Set quote_id for all line items
            for item in line_items:
                item.quote_id = quote_id
            self.line_item_repo.create_bulk(line_items)

        return quote_id

    def get_by_id(self, quote_id: int, load_line_items: bool = True) -> Optional[Quote]:
        """
        Get quote by ID.

        Args:
            quote_id: Quote ID
            load_line_items: Whether to load line items (default: True)

        Returns:
            Quote object with line items or None
        """
        query = "SELECT * FROM quotes WHERE id = ?"
        results = self.db.execute_query(query, (quote_id,))
        if not results:
            return None

        quote = Quote.from_dict(dict(results[0]))

        if load_line_items:
            quote.line_items = self.line_item_repo.get_by_quote_id(quote_id)
            quote.populate_from_first_line_item()

        return quote

    def get_by_quote_number(self, quote_number: str, load_line_items: bool = True) -> Optional[Quote]:
        """Get quote by quote number."""
        query = "SELECT * FROM quotes WHERE quote_number = ?"
        results = self.db.execute_query(query, (quote_number,))
        if not results:
            return None

        quote = Quote.from_dict(dict(results[0]))

        if load_line_items:
            quote.line_items = self.line_item_repo.get_by_quote_id(quote.id)
            quote.populate_from_first_line_item()

        return quote

    def get_all(self, limit: int = 100, load_line_items: bool = False) -> List[Quote]:
        """
        Get all quotes.

        Args:
            limit: Maximum number of quotes to return
            load_line_items: Whether to load line items (default: False for performance)

        Returns:
            List of Quote objects
        """
        query = "SELECT * FROM quotes ORDER BY quote_date DESC LIMIT ?"
        results = self.db.execute_query(query, (limit,))
        quotes = [Quote.from_dict(dict(row)) for row in results]

        if load_line_items:
            for quote in quotes:
                quote.line_items = self.line_item_repo.get_by_quote_id(quote.id)
                quote.populate_from_first_line_item()

        return quotes

    def get_by_customer(self, customer_id: int, load_line_items: bool = False) -> List[Quote]:
        """Get all quotes for a customer."""
        query = """
            SELECT * FROM quotes
            WHERE customer_id = ?
            ORDER BY quote_date DESC
        """
        results = self.db.execute_query(query, (customer_id,))
        quotes = [Quote.from_dict(dict(row)) for row in results]

        if load_line_items:
            for quote in quotes:
                quote.line_items = self.line_item_repo.get_by_quote_id(quote.id)
                quote.populate_from_first_line_item()

        return quotes

    def update(self, quote: Quote, update_line_items: bool = False) -> bool:
        """
        Update existing quote.

        Args:
            quote: Quote object to update
            update_line_items: Whether to also update line items

        Returns:
            True if successful
        """
        query = """
            UPDATE quotes SET
                customer_id = ?, agent_name = ?, quote_date = ?,
                state_code = ?, term_months = ?, total_premium = ?,
                status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (
            quote.customer_id, quote.agent_name, quote.quote_date,
            quote.state_code, quote.term_months, quote.total_premium,
            quote.status, quote.notes, quote.id
        )
        rows = self.db.execute_update(query, params)

        if update_line_items and quote.line_items:
            for line_item in quote.line_items:
                if line_item.id:
                    self.line_item_repo.update(line_item)
                else:
                    self.line_item_repo.create(line_item)

        return rows > 0

    def delete(self, quote_id: int) -> bool:
        """Delete quote (line items will be cascade deleted)."""
        query = "DELETE FROM quotes WHERE id = ?"
        rows = self.db.execute_update(query, (quote_id,))
        return rows > 0

    def recalculate_total(self, quote_id: int) -> float:
        """Recalculate and update quote total from line items."""
        total = self.line_item_repo.get_total_premium(quote_id)

        query = "UPDATE quotes SET total_premium = ? WHERE id = ?"
        self.db.execute_update(query, (total, quote_id))

        return total

    def generate_quote_number(self) -> str:
        """Generate unique quote number."""
        query = "SELECT MAX(id) as max_id FROM quotes"
        result = self.db.execute_query(query)
        max_id = result[0]['max_id'] if result[0]['max_id'] else 0
        next_id = max_id + 1
        return f"Q-{next_id:05d}"
