"""
Build script to create Windows EXE using PyInstaller.
"""

import PyInstaller.__main__
import sys
from pathlib import Path

# Get project root
root_dir = Path(__file__).parent

# PyInstaller arguments
args = [
    'src/main.py',  # Main script
    '--name=CSI_Pivot_Quote',  # EXE name
    '--windowed',  # No console window
    '--onefile',  # Single EXE file
    f'--distpath={root_dir}/dist',  # Output directory
    f'--workpath={root_dir}/build',  # Build directory
    f'--specpath={root_dir}',  # Spec file location
    '--clean',  # Clean cache

    # Add data files
    '--add-data=data;data',  # Include data directory

    # Hidden imports (packages not auto-detected)
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=reportlab',
    '--hidden-import=sqlite3',

    # Exclude unnecessary modules
    '--exclude-module=matplotlib',
    '--exclude-module=numpy',
    '--exclude-module=PIL',
]

# Add icon if exists
icon_path = root_dir / 'data' / 'app_icon.ico'
if icon_path.exists():
    args.append(f'--icon={icon_path}')

print("Building Windows executable...")
print("This may take a few minutes...")
print()

# Run PyInstaller
PyInstaller.__main__.run(args)

print()
print("✓ Build complete!")
print(f"✓ Executable location: {root_dir}/dist/CSI_Pivot_Quote.exe")
print()
print("To run the application:")
print("  cd dist")
print("  ./CSI_Pivot_Quote.exe")
