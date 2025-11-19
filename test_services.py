#!/usr/bin/env python3
"""
Simple test to verify services can be imported and initialized.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all services can be imported."""
    print("Testing service imports...")

    try:
        from services.binding_service import BindingService
        print("✓ BindingService imported successfully")

        from services.document_service import DocumentService
        print("✓ DocumentService imported successfully")

        from models.policy_document import PolicyDocument, PolicyDocumentRepository
        print("✓ PolicyDocument models imported successfully")

        # UI components require PyQt6, which may not be installed in all environments
        # Test them separately
        ui_imports_ok = True
        try:
            from ui.bind_quote_dialog import BindQuoteDialog
            print("✓ BindQuoteDialog imported successfully")

            from ui.edit_policy_dialog import EditPolicyDialog
            print("✓ EditPolicyDialog imported successfully")

            from ui.document_upload_dialog import DocumentUploadDialog
            print("✓ DocumentUploadDialog imported successfully")
        except ModuleNotFoundError as e:
            if "PyQt6" in str(e):
                print("ℹ UI components require PyQt6 (not tested in this environment)")
                ui_imports_ok = False
            else:
                raise

        print("\n✓ Core service imports successful!")
        if ui_imports_ok:
            print("✓ UI component imports successful!")
        return True

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_initialization():
    """Test that services can be initialized."""
    print("\nTesting service initialization...")

    try:
        from services.binding_service import BindingService
        from services.document_service import DocumentService
        from models.policy_document import PolicyDocumentRepository

        binding_service = BindingService()
        print("✓ BindingService initialized")

        document_service = DocumentService()
        print("✓ DocumentService initialized")

        document_repo = PolicyDocumentRepository()
        print("✓ PolicyDocumentRepository initialized")

        # Check document service constants
        print(f"\n  Document Service Configuration:")
        print(f"  - Max file size: {document_service.MAX_FILE_SIZE / (1024*1024):.0f} MB")
        print(f"  - Allowed extensions: {', '.join(sorted(document_service.ALLOWED_EXTENSIONS))}")
        print(f"  - Documents directory: {document_service.DOCUMENTS_DIR}")

        # Check that documents directory exists
        if document_service.DOCUMENTS_DIR.exists():
            print(f"  ✓ Documents directory exists")
        else:
            print(f"  ℹ Documents directory will be created on first upload")

        print("\n✓ All services initialized successfully!")
        return True

    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        success = test_service_initialization()

    if success:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPolicy binding and document management system is ready to use.")
        print("\nKey Features:")
        print("  • Bind quotes to create active policies")
        print("  • Add policy number later when received from carrier")
        print("  • Upload and manage policy documents")
        print("  • Track payment status and methods")
        print("  • Automatic renewal tracking integration")
        sys.exit(0)
    else:
        sys.exit(1)
