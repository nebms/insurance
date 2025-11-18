"""
Quote Line Item data model and repository.
Supports multiple pivot equipment items per quote.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from database.db_manager import get_db


class QuoteLineItem:
    """Quote line item data model for individual equipment."""

    def __init__(self, **kwargs):
        # Required fields
        self.id = kwargs.get('id')
        self.quote_id = kwargs.get('quote_id')
        self.line_number = kwargs.get('line_number', 1)

        # Equipment details
        self.pivot_amount = kwargs.get('pivot_amount', 0.0)
        self.equipment_age_years = kwargs.get('equipment_age_years', 0)
        self.pivot_deductible_code = kwargs.get('pivot_deductible_code', 3)
        self.ancillary_deductible_code = kwargs.get('ancillary_deductible_code', 2)

        # Optional fields
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
        self.line_total_premium = kwargs.get('line_total_premium')

        # Alternative scenarios
        self.alt1_deductible = kwargs.get('alt1_deductible')
        self.alt1_rate = kwargs.get('alt1_rate')
        self.alt1_premium = kwargs.get('alt1_premium')
        self.alt2_deductible = kwargs.get('alt2_deductible')
        self.alt2_rate = kwargs.get('alt2_rate')
        self.alt2_premium = kwargs.get('alt2_premium')

        # Metadata
        self.created_at = kwargs.get('created_at', '')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuoteLineItem':
        """Create QuoteLineItem from dictionary."""
        return cls(**{k: v for k, v in data.items() if v is not None})

    def to_dict(self) -> Dict[str, Any]:
        """Convert QuoteLineItem to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class QuoteLineItemRepository:
    """Repository for quote line item database operations."""

    def __init__(self):
        self.db = get_db()

    def create(self, line_item: QuoteLineItem) -> int:
        """Create new quote line item."""
        query = """
            INSERT INTO quote_line_items (
                quote_id, line_number, pivot_amount, ancillary_amount,
                submersible_pump_amount, equipment_age_years,
                is_towable, is_corner_or_long, has_me_endorsement,
                pivot_deductible_code, ancillary_deductible_code,
                pivot_rate, ancillary_rate, pivot_premium,
                ancillary_premium, submersible_charge, line_total_premium,
                alt1_deductible, alt1_rate, alt1_premium,
                alt2_deductible, alt2_rate, alt2_premium
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            line_item.quote_id, line_item.line_number,
            line_item.pivot_amount, line_item.ancillary_amount,
            line_item.submersible_pump_amount, line_item.equipment_age_years,
            line_item.is_towable, line_item.is_corner_or_long,
            line_item.has_me_endorsement, line_item.pivot_deductible_code,
            line_item.ancillary_deductible_code, line_item.pivot_rate,
            line_item.ancillary_rate, line_item.pivot_premium,
            line_item.ancillary_premium, line_item.submersible_charge,
            line_item.line_total_premium, line_item.alt1_deductible,
            line_item.alt1_rate, line_item.alt1_premium,
            line_item.alt2_deductible, line_item.alt2_rate, line_item.alt2_premium
        )
        return self.db.execute_insert(query, params)

    def create_bulk(self, line_items: List[QuoteLineItem]) -> List[int]:
        """Create multiple line items at once."""
        item_ids = []
        for line_item in line_items:
            item_id = self.create(line_item)
            item_ids.append(item_id)
        return item_ids

    def get_by_quote_id(self, quote_id: int) -> List[QuoteLineItem]:
        """Get all line items for a quote."""
        query = """
            SELECT * FROM quote_line_items
            WHERE quote_id = ?
            ORDER BY line_number
        """
        results = self.db.execute_query(query, (quote_id,))
        return [QuoteLineItem.from_dict(dict(row)) for row in results]

    def get_by_id(self, item_id: int) -> Optional[QuoteLineItem]:
        """Get line item by ID."""
        query = "SELECT * FROM quote_line_items WHERE id = ?"
        results = self.db.execute_query(query, (item_id,))
        if results:
            return QuoteLineItem.from_dict(dict(results[0]))
        return None

    def update(self, line_item: QuoteLineItem) -> bool:
        """Update existing line item."""
        query = """
            UPDATE quote_line_items SET
                line_number = ?, pivot_amount = ?, ancillary_amount = ?,
                submersible_pump_amount = ?, equipment_age_years = ?,
                is_towable = ?, is_corner_or_long = ?, has_me_endorsement = ?,
                pivot_deductible_code = ?, ancillary_deductible_code = ?,
                pivot_rate = ?, ancillary_rate = ?, pivot_premium = ?,
                ancillary_premium = ?, submersible_charge = ?,
                line_total_premium = ?, alt1_deductible = ?, alt1_rate = ?,
                alt1_premium = ?, alt2_deductible = ?, alt2_rate = ?, alt2_premium = ?
            WHERE id = ?
        """
        params = (
            line_item.line_number, line_item.pivot_amount,
            line_item.ancillary_amount, line_item.submersible_pump_amount,
            line_item.equipment_age_years, line_item.is_towable,
            line_item.is_corner_or_long, line_item.has_me_endorsement,
            line_item.pivot_deductible_code, line_item.ancillary_deductible_code,
            line_item.pivot_rate, line_item.ancillary_rate,
            line_item.pivot_premium, line_item.ancillary_premium,
            line_item.submersible_charge, line_item.line_total_premium,
            line_item.alt1_deductible, line_item.alt1_rate, line_item.alt1_premium,
            line_item.alt2_deductible, line_item.alt2_rate, line_item.alt2_premium,
            line_item.id
        )
        rows = self.db.execute_update(query, params)
        return rows > 0

    def delete(self, item_id: int) -> bool:
        """Delete line item."""
        query = "DELETE FROM quote_line_items WHERE id = ?"
        rows = self.db.execute_update(query, (item_id,))
        return rows > 0

    def delete_by_quote_id(self, quote_id: int) -> int:
        """Delete all line items for a quote."""
        query = "DELETE FROM quote_line_items WHERE quote_id = ?"
        return self.db.execute_update(query, (quote_id,))

    def get_line_count(self, quote_id: int) -> int:
        """Get count of line items for a quote."""
        query = "SELECT COUNT(*) as count FROM quote_line_items WHERE quote_id = ?"
        result = self.db.execute_query(query, (quote_id,))
        return result[0]['count'] if result else 0

    def get_total_premium(self, quote_id: int) -> float:
        """Calculate total premium for all line items in a quote."""
        query = """
            SELECT SUM(line_total_premium) as total
            FROM quote_line_items
            WHERE quote_id = ?
        """
        result = self.db.execute_query(query, (quote_id,))
        return result[0]['total'] if result and result[0]['total'] else 0.0
