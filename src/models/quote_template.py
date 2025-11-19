"""
Quote template data model and repository.
Allows users to save and reuse common quote configurations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from database.db_manager import get_db


class QuoteTemplate:
    """Quote template data model."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.template_name = kwargs.get('template_name', '')
        self.description = kwargs.get('description', '')

        # Location and term
        self.state_code = kwargs.get('state_code', '')
        self.term_months = kwargs.get('term_months', 12)

        # Equipment configuration
        self.pivot_amount = kwargs.get('pivot_amount', 0.0)
        self.equipment_age_years = kwargs.get('equipment_age_years', 0)
        self.pivot_deductible_code = kwargs.get('pivot_deductible_code', 3)
        self.ancillary_deductible_code = kwargs.get('ancillary_deductible_code', 2)
        self.ancillary_amount = kwargs.get('ancillary_amount', 0.0)
        self.submersible_pump_amount = kwargs.get('submersible_pump_amount', 0.0)
        self.is_towable = kwargs.get('is_towable', 0)
        self.is_corner_or_long = kwargs.get('is_corner_or_long', 0)
        self.has_me_endorsement = kwargs.get('has_me_endorsement', 1)

        # Metadata
        self.created_at = kwargs.get('created_at', '')
        self.updated_at = kwargs.get('updated_at', '')


class QuoteTemplateRepository:
    """Repository for quote template database operations."""

    def __init__(self):
        self.db = get_db()

    def create(self, template: QuoteTemplate) -> int:
        """
        Create new quote template.

        Args:
            template: QuoteTemplate instance

        Returns:
            Template ID of created template
        """
        query = """
        INSERT INTO quote_templates (
            template_name, description,
            state_code, term_months,
            pivot_amount, equipment_age_years,
            pivot_deductible_code, ancillary_deductible_code,
            ancillary_amount, submersible_pump_amount,
            is_towable, is_corner_or_long, has_me_endorsement
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            template.template_name,
            template.description,
            template.state_code,
            template.term_months,
            template.pivot_amount,
            template.equipment_age_years,
            template.pivot_deductible_code,
            template.ancillary_deductible_code,
            template.ancillary_amount,
            template.submersible_pump_amount,
            template.is_towable,
            template.is_corner_or_long,
            template.has_me_endorsement
        )

        return self.db.execute_insert(query, params)

    def get_by_id(self, template_id: int) -> Optional[QuoteTemplate]:
        """
        Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            QuoteTemplate instance or None
        """
        query = "SELECT * FROM quote_templates WHERE id = ?"
        results = self.db.execute_query(query, (template_id,))

        if results:
            return QuoteTemplate(**results[0])
        return None

    def get_by_name(self, template_name: str) -> Optional[QuoteTemplate]:
        """
        Get template by name.

        Args:
            template_name: Template name

        Returns:
            QuoteTemplate instance or None
        """
        query = "SELECT * FROM quote_templates WHERE template_name = ?"
        results = self.db.execute_query(query, (template_name,))

        if results:
            return QuoteTemplate(**results[0])
        return None

    def get_all(self, state_code: Optional[str] = None) -> List[QuoteTemplate]:
        """
        Get all templates, optionally filtered by state.

        Args:
            state_code: Optional state code filter

        Returns:
            List of QuoteTemplate instances
        """
        if state_code:
            query = """
            SELECT * FROM quote_templates
            WHERE state_code = ?
            ORDER BY template_name
            """
            results = self.db.execute_query(query, (state_code,))
        else:
            query = """
            SELECT * FROM quote_templates
            ORDER BY template_name
            """
            results = self.db.execute_query(query)

        return [QuoteTemplate(**row) for row in results]

    def update(self, template: QuoteTemplate) -> bool:
        """
        Update existing template.

        Args:
            template: QuoteTemplate instance with updated data

        Returns:
            True if successful, False otherwise
        """
        query = """
        UPDATE quote_templates SET
            template_name = ?,
            description = ?,
            state_code = ?,
            term_months = ?,
            pivot_amount = ?,
            equipment_age_years = ?,
            pivot_deductible_code = ?,
            ancillary_deductible_code = ?,
            ancillary_amount = ?,
            submersible_pump_amount = ?,
            is_towable = ?,
            is_corner_or_long = ?,
            has_me_endorsement = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        params = (
            template.template_name,
            template.description,
            template.state_code,
            template.term_months,
            template.pivot_amount,
            template.equipment_age_years,
            template.pivot_deductible_code,
            template.ancillary_deductible_code,
            template.ancillary_amount,
            template.submersible_pump_amount,
            template.is_towable,
            template.is_corner_or_long,
            template.has_me_endorsement,
            template.id
        )

        return self.db.execute_update(query, params)

    def delete(self, template_id: int) -> bool:
        """
        Delete template.

        Args:
            template_id: Template ID

        Returns:
            True if successful, False otherwise
        """
        query = "DELETE FROM quote_templates WHERE id = ?"
        return self.db.execute_delete(query, (template_id,))

    def exists(self, template_name: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if template name already exists.

        Args:
            template_name: Template name to check
            exclude_id: Optional template ID to exclude (for updates)

        Returns:
            True if exists, False otherwise
        """
        if exclude_id:
            query = """
            SELECT COUNT(*) as count
            FROM quote_templates
            WHERE template_name = ? AND id != ?
            """
            results = self.db.execute_query(query, (template_name, exclude_id))
        else:
            query = """
            SELECT COUNT(*) as count
            FROM quote_templates
            WHERE template_name = ?
            """
            results = self.db.execute_query(query, (template_name,))

        return results[0]['count'] > 0 if results else False
