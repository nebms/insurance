"""
Policy Document data model and repository.
Handles document attachments for policies (binders, policies, certificates, etc.).
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from database.db_manager import get_db


class PolicyDocument:
    """Policy Document data model."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.quote_id = kwargs.get('quote_id')
        self.document_type = kwargs.get('document_type', '')
        self.document_name = kwargs.get('document_name', '')
        self.file_path = kwargs.get('file_path', '')
        self.uploaded_date = kwargs.get('uploaded_date', '')
        self.uploaded_by_user_id = kwargs.get('uploaded_by_user_id')
        self.received_from = kwargs.get('received_from', '')
        self.notes = kwargs.get('notes', '')
        self.created_at = kwargs.get('created_at', '')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyDocument':
        """Create PolicyDocument from dictionary."""
        return cls(**{k: v for k, v in data.items() if v is not None})

    def to_dict(self) -> Dict[str, Any]:
        """Convert PolicyDocument to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class PolicyDocumentRepository:
    """Repository for policy document database operations."""

    def __init__(self):
        self.db = get_db()

    def create(self, document: PolicyDocument) -> int:
        """
        Create new policy document record.

        Args:
            document: PolicyDocument instance

        Returns:
            Document ID
        """
        query = """
            INSERT INTO policy_documents (
                quote_id, document_type, document_name, file_path,
                uploaded_by_user_id, received_from, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            document.quote_id,
            document.document_type,
            document.document_name,
            document.file_path,
            document.uploaded_by_user_id,
            document.received_from,
            document.notes
        )

        return self.db.execute_insert(query, params)

    def get_by_id(self, document_id: int) -> Optional[PolicyDocument]:
        """
        Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            PolicyDocument instance or None
        """
        query = "SELECT * FROM policy_documents WHERE id = ?"
        results = self.db.execute_query(query, (document_id,))

        if results:
            return PolicyDocument.from_dict(dict(results[0]))
        return None

    def get_by_quote(self, quote_id: int) -> List[PolicyDocument]:
        """
        Get all documents for a quote.

        Args:
            quote_id: Quote ID

        Returns:
            List of PolicyDocument instances
        """
        query = """
            SELECT * FROM policy_documents
            WHERE quote_id = ?
            ORDER BY uploaded_date DESC
        """
        results = self.db.execute_query(query, (quote_id,))
        return [PolicyDocument.from_dict(dict(row)) for row in results]

    def get_by_type(self, quote_id: int, document_type: str) -> List[PolicyDocument]:
        """
        Get documents by type for a quote.

        Args:
            quote_id: Quote ID
            document_type: Document type (binder, policy, certificate, etc.)

        Returns:
            List of PolicyDocument instances
        """
        query = """
            SELECT * FROM policy_documents
            WHERE quote_id = ? AND document_type = ?
            ORDER BY uploaded_date DESC
        """
        results = self.db.execute_query(query, (quote_id, document_type))
        return [PolicyDocument.from_dict(dict(row)) for row in results]

    def update(self, document: PolicyDocument) -> bool:
        """
        Update existing document.

        Args:
            document: PolicyDocument instance with updated data

        Returns:
            True if successful
        """
        query = """
            UPDATE policy_documents SET
                document_type = ?,
                document_name = ?,
                file_path = ?,
                received_from = ?,
                notes = ?
            WHERE id = ?
        """
        params = (
            document.document_type,
            document.document_name,
            document.file_path,
            document.received_from,
            document.notes,
            document.id
        )
        rows = self.db.execute_update(query, params)
        return rows > 0

    def delete(self, document_id: int) -> bool:
        """
        Delete document record (does not delete actual file).

        Args:
            document_id: Document ID

        Returns:
            True if successful
        """
        query = "DELETE FROM policy_documents WHERE id = ?"
        rows = self.db.execute_update(query, (document_id,))
        return rows > 0

    def count_by_quote(self, quote_id: int) -> int:
        """
        Get document count for a quote.

        Args:
            quote_id: Quote ID

        Returns:
            Number of documents
        """
        query = "SELECT COUNT(*) as count FROM policy_documents WHERE quote_id = ?"
        result = self.db.execute_query(query, (quote_id,))
        return result[0]['count'] if result else 0

    def get_all(self, limit: int = 100) -> List[PolicyDocument]:
        """
        Get all documents.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List of PolicyDocument instances
        """
        query = """
            SELECT * FROM policy_documents
            ORDER BY uploaded_date DESC
            LIMIT ?
        """
        results = self.db.execute_query(query, (limit,))
        return [PolicyDocument.from_dict(dict(row)) for row in results]
