"""
Application configuration settings.
"""

import os
from pathlib import Path

# Application info
APP_NAME = "CSI Pivot Quote"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Western Valley Irrigation Sales and Service, Inc."

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
DB_PATH = DATA_DIR / "csi_quotes.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

# Database settings
DB_TYPE = "sqlite"  # Will be "postgresql" for web version

# PDF settings
PDF_COMPANY_NAME = COMPANY_NAME
PDF_QUOTE_VALIDITY_DAYS = 30

# Special states (50% submersible surcharge)
SPECIAL_STATES = ['TX', 'OK', 'GA', 'KS', 'MN', 'NE']

# Deductible options
DEDUCTIBLE_OPTIONS = {
    1: 500,
    2: 1000,
    3: 2500,
    4: 5000
}

# Term options (in months)
TERM_OPTIONS = [12, 24, 36, 48, 60, 72, 84, 96]
