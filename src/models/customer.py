"""
Customer data model and repository.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from database.db_manager import get_db


class Customer:
    """Customer data model."""

    def __init__(self, id: Optional[int] = None, name: str = "",
                 email: str = "", phone: str = "", address: str = "",
                 notes: str = "", created_at: str = "", updated_at: str = ""):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        """Create Customer from dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            notes=data.get('notes', ''),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Customer to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class CustomerRepository:
    """Repository for customer database operations."""

    def __init__(self):
        self.db = get_db()

    def create(self, customer: Customer) -> int:
        """
        Create new customer.

        Args:
            customer: Customer object

        Returns:
            int: New customer ID
        """
        query = """
            INSERT INTO customers (name, email, phone, address, notes)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (customer.name, customer.email, customer.phone,
                  customer.address, customer.notes)
        return self.db.execute_insert(query, params)

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID."""
        query = "SELECT * FROM customers WHERE id = ?"
        results = self.db.execute_query(query, (customer_id,))
        if results:
            return Customer.from_dict(dict(results[0]))
        return None

    def get_all(self) -> List[Customer]:
        """Get all customers."""
        query = "SELECT * FROM customers ORDER BY name"
        results = self.db.execute_query(query)
        return [Customer.from_dict(dict(row)) for row in results]

    def search(self, search_term: str) -> List[Customer]:
        """Search customers by name, email, or phone."""
        query = """
            SELECT * FROM customers
            WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
            ORDER BY name
        """
        term = f"%{search_term}%"
        results = self.db.execute_query(query, (term, term, term))
        return [Customer.from_dict(dict(row)) for row in results]

    def update(self, customer: Customer) -> bool:
        """Update existing customer."""
        query = """
            UPDATE customers
            SET name = ?, email = ?, phone = ?, address = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (customer.name, customer.email, customer.phone,
                  customer.address, customer.notes, customer.id)
        rows = self.db.execute_update(query, params)
        return rows > 0

    def delete(self, customer_id: int) -> bool:
        """Delete customer."""
        query = "DELETE FROM customers WHERE id = ?"
        rows = self.db.execute_update(query, (customer_id,))
        return rows > 0

    def count(self) -> int:
        """Get total number of customers."""
        return self.db.get_table_row_count('customers')
