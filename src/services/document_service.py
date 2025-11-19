"""
Document Service for handling policy document uploads and management.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

from models.policy_document import PolicyDocument, PolicyDocumentRepository
from models.quote import QuoteRepository


class DocumentService:
    """Service for managing policy documents."""

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.pdf', '.PDF',
        '.doc', '.docx', '.DOC', '.DOCX',
        '.jpg', '.jpeg', '.JPG', '.JPEG',
        '.png', '.PNG',
        '.tif', '.tiff', '.TIF', '.TIFF'
    }

    # Maximum file size (20MB)
    MAX_FILE_SIZE = 20 * 1024 * 1024

    # Documents directory
    DOCUMENTS_DIR = Path("data/policy_documents")

    def __init__(self):
        self.document_repo = PolicyDocumentRepository()
        self.quote_repo = QuoteRepository()
        self._ensure_documents_directory()

    def _ensure_documents_directory(self):
        """Ensure documents directory exists."""
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    def upload_document(self, source_path: str, quote_id: int,
                       document_type: str, received_from: str,
                       notes: str = '', uploaded_by_user_id: Optional[int] = None) -> Tuple[bool, str, Optional[PolicyDocument]]:
        """
        Upload a document for a quote/policy.

        Args:
            source_path: Path to the source file
            quote_id: Quote/Policy ID
            document_type: Type of document (binder, policy, certificate, etc.)
            received_from: Where document came from (carrier, customer, agent)
            notes: Optional notes about the document
            uploaded_by_user_id: User ID who uploaded (optional)

        Returns:
            Tuple of (success, message, document)
        """
        # Check if quote/policy is cancelled
        quote = self.quote_repo.get_by_id(quote_id)
        if not quote:
            return False, "Quote/Policy not found", None

        if quote.is_cancelled:
            return False, "Cannot upload documents to cancelled policy. Reinstate the policy first if needed.", None

        # Validate source file exists
        source_file = Path(source_path)
        if not source_file.exists():
            return False, "Source file does not exist", None

        if not source_file.is_file():
            return False, "Source path is not a file", None

        # Validate file extension
        if source_file.suffix not in self.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(self.ALLOWED_EXTENSIONS))
            return False, f"File type not allowed. Allowed types: {allowed}", None

        # Validate file size
        file_size = source_file.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"File too large ({actual_mb:.1f}MB). Maximum size: {max_mb:.0f}MB", None

        if file_size == 0:
            return False, "File is empty (0 bytes)", None

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = source_file.name
        safe_name = self._sanitize_filename(original_name)
        unique_filename = f"quote_{quote_id}_{timestamp}_{safe_name}"

        # Destination path
        dest_path = self.DOCUMENTS_DIR / unique_filename

        try:
            # Copy file to documents directory
            shutil.copy2(source_path, dest_path)

            # Create document record
            document = PolicyDocument(
                quote_id=quote_id,
                document_type=document_type,
                document_name=original_name,
                file_path=str(dest_path),
                uploaded_by_user_id=uploaded_by_user_id,
                received_from=received_from,
                notes=notes
            )

            # Save to database
            document_id = self.document_repo.create(document)
            document.id = document_id

            return True, f"Document uploaded successfully: {original_name}", document

        except Exception as e:
            # Clean up if database insert failed
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except:
                    pass
            return False, f"Upload failed: {str(e)}", None

    def delete_document(self, document_id: int, delete_file: bool = True) -> Tuple[bool, str]:
        """
        Delete a document.

        Args:
            document_id: Document ID
            delete_file: Whether to delete the physical file (default: True)

        Returns:
            Tuple of (success, message)
        """
        # Get document
        document = self.document_repo.get_by_id(document_id)
        if not document:
            return False, "Document not found"

        # Delete physical file if requested
        if delete_file and document.file_path:
            try:
                file_path = Path(document.file_path)
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                return False, f"Failed to delete file: {str(e)}"

        # Delete database record
        success = self.document_repo.delete(document_id)
        if success:
            return True, "Document deleted successfully"
        else:
            return False, "Failed to delete document record"

    def get_document_path(self, document_id: int) -> Optional[Path]:
        """
        Get the file path for a document.

        Args:
            document_id: Document ID

        Returns:
            Path object or None
        """
        document = self.document_repo.get_by_id(document_id)
        if document and document.file_path:
            path = Path(document.file_path)
            if path.exists():
                return path
        return None

    def get_documents_for_quote(self, quote_id: int) -> List[PolicyDocument]:
        """
        Get all documents for a quote.

        Args:
            quote_id: Quote ID

        Returns:
            List of PolicyDocument instances
        """
        return self.document_repo.get_by_quote(quote_id)

    def get_document_statistics(self, quote_id: int) -> dict:
        """
        Get document statistics for a quote.

        Args:
            quote_id: Quote ID

        Returns:
            Dictionary with document stats
        """
        documents = self.get_documents_for_quote(quote_id)

        stats = {
            'total_count': len(documents),
            'by_type': {},
            'total_size_bytes': 0,
            'latest_upload': None
        }

        for doc in documents:
            # Count by type
            doc_type = doc.document_type
            stats['by_type'][doc_type] = stats['by_type'].get(doc_type, 0) + 1

            # Calculate total size
            if doc.file_path:
                try:
                    size = Path(doc.file_path).stat().st_size
                    stats['total_size_bytes'] += size
                except:
                    pass

            # Track latest upload
            if doc.uploaded_date:
                if not stats['latest_upload'] or doc.uploaded_date > stats['latest_upload']:
                    stats['latest_upload'] = doc.uploaded_date

        # Convert bytes to MB for display
        stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024)

        return stats

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove problematic characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace problematic characters
        unsafe_chars = '<>:"|?*\\/\0'
        safe_name = filename

        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')

        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip('. ')

        # Limit length
        if len(safe_name) > 200:
            # Keep extension
            name_part = Path(safe_name).stem[:190]
            ext_part = Path(safe_name).suffix
            safe_name = name_part + ext_part

        return safe_name

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate a file before upload.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (valid, error_message)
        """
        source_file = Path(file_path)

        if not source_file.exists():
            return False, "File does not exist"

        if not source_file.is_file():
            return False, "Path is not a file"

        if source_file.suffix not in self.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed: {source_file.suffix}"

        file_size = source_file.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"File too large: {actual_mb:.1f}MB (max: {max_mb:.0f}MB)"

        if file_size == 0:
            return False, "File is empty"

        return True, ""

    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file info
        """
        path = Path(file_path)

        if not path.exists():
            return {'exists': False}

        stat = path.stat()

        return {
            'exists': True,
            'name': path.name,
            'extension': path.suffix,
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'size_display': self._format_file_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size for display.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
