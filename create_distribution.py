"""
Create distribution package with EXE and required files.
"""

import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Directories
root_dir = Path(__file__).parent
dist_dir = root_dir / "dist"
package_dir = root_dir / "distribution"

# Clean previous distribution
if package_dir.exists():
    shutil.rmtree(package_dir)

# Create distribution directory
package_dir.mkdir()

print("Creating distribution package...")

# Copy EXE
exe_path = dist_dir / "CSI_Pivot_Quote.exe"
if exe_path.exists():
    shutil.copy(exe_path, package_dir / "CSI_Pivot_Quote.exe")
    print("✓ Copied EXE")
else:
    print("✗ EXE not found. Run build_exe.py first.")
    exit(1)

# Create data directory in package
data_pkg_dir = package_dir / "data"
data_pkg_dir.mkdir()

# Copy sample database (empty)
# Note: Don't include actual quotes database
print("✓ Created data directory")

# Create README
readme_content = """# CSI Pivot Quote - Installation Instructions

## System Requirements
- Windows 10 or later
- No other software required (all dependencies included)

## Installation
1. Extract this ZIP file to a folder on your computer
2. Run CSI_Pivot_Quote.exe

## First Run
On first run, the application will:
- Create a database file (data/csi_quotes.db)
- Load state data
- Load sample rate tables

## Important Notes
- **REPLACE SAMPLE RATES**: The application includes sample rates for testing.
  You must load your actual rate tables before creating real quotes.

- **Database Location**: The database file is created in the same folder as the EXE.
  To backup your quotes, copy the entire 'data' folder.

- **Rate Tables**: Use the Tools > Load Rate Tables menu option to import
  your rate tables from CSV files.

## Support
For assistance, contact:
Western Valley Irrigation Sales and Service, Inc.
Alliance, Nebraska

## Version
Version 1.0.0
Built: {build_date}
"""

with open(package_dir / "README.txt", "w") as f:
    f.write(readme_content.format(build_date=datetime.now().strftime("%Y-%m-%d")))
print("✓ Created README")

# Create ZIP file
zip_filename = f"CSI_Pivot_Quote_v1.0_{datetime.now().strftime('%Y%m%d')}.zip"
zip_path = root_dir / zip_filename

print(f"\nCreating ZIP file: {zip_filename}")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file_path in package_dir.rglob('*'):
        if file_path.is_file():
            arcname = file_path.relative_to(package_dir)
            zipf.write(file_path, arcname)
            print(f"  Added: {arcname}")

print(f"\n✓ Distribution package created: {zip_path}")
print(f"✓ Package size: {zip_path.stat().st_size / (1024*1024):.1f} MB")
print("\nThe ZIP file contains:")
print("  - CSI_Pivot_Quote.exe (standalone application)")
print("  - data/ (directory for database and PDFs)")
print("  - README.txt (installation instructions)")
