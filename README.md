# CSI Pivot Quote - Insurance Quote Calculator

A desktop application for generating insurance quotes for center pivot irrigation equipment.

## Features

- **Quote Calculation Engine**: Complex rate lookups based on equipment age, type, location, and coverage options
- **Customer Management**: Track customer information and quote history
- **PDF Generation**: Professional quote PDFs ready for client delivery
- **Database**: SQLite database for quotes and rate tables
- **User-Friendly GUI**: PyQt6-based desktop interface

## Technology Stack

- **Python 3.11+**
- **PyQt6**: Desktop GUI framework
- **SQLite**: Database
- **ReportLab**: PDF generation
- **PyInstaller**: EXE packaging

## Project Structure

```
insurance/
├── src/
│   ├── database/         # Database layer
│   ├── models/           # Data models
│   ├── calculations/     # Rate lookup and premium calculation
│   ├── ui/               # PyQt6 GUI components
│   ├── reports/          # PDF generation
│   ├── config.py         # Configuration
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── data/                 # Database and PDFs
├── requirements.txt      # Python dependencies
├── build_exe.py          # EXE build script
└── create_distribution.py # Distribution packager
```

## Installation for Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd insurance
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**:
   ```bash
   python -m src.database.data_loader
   ```

5. **Run application**:
   ```bash
   python src/main.py
   ```

## Running Tests

```bash
pytest tests/ -v
```

## Building Windows EXE

**Note**: Building Windows EXE requires running on Windows

```bash
python build_exe.py
```

The executable will be created in `dist/CSI_Pivot_Quote.exe`

## Creating Distribution Package

```bash
python create_distribution.py
```

This creates a ZIP file with:
- Standalone EXE
- Data directory structure
- Installation instructions

## Important Notes

### Sample Rates
The application includes **sample rates for testing only**. Before production use:
1. Export actual rate tables from your source system to CSV
2. Import CSV files using the Tools menu
3. Verify calculations against known test cases

### Database Backup
- Database location: `data/csi_quotes.db`
- Backup regularly by copying the entire `data/` folder
- Consider implementing automated backups

### Future Web Migration
The codebase is designed for easy migration to a web application:
- Business logic in `calculations/` can be reused
- Database models in `models/` are portable
- See documentation for migration guide

## Development

### Code Organization
- **Database Layer**: All database operations in `src/database/`
- **Business Logic**: Rate calculations in `src/calculations/`
- **Data Access**: Repository pattern in `src/models/`
- **User Interface**: PyQt6 widgets in `src/ui/`

### Key Files
- `src/calculations/rate_engine.py`: Rate table lookup logic
- `src/calculations/premium_calc.py`: Premium calculation
- `src/ui/quote_form.py`: Main quote entry form
- `src/reports/pdf_generator.py`: PDF quote generation

## Configuration

Edit `src/config.py` to customize:
- Company information
- Database paths
- PDF settings
- Special state lists

## Support

**Company**: Western Valley Irrigation Sales and Service, Inc.
**Location**: Alliance, Nebraska
**Industry**: Agricultural Equipment Insurance

## License

Copyright © 2025 Western Valley Irrigation Sales and Service, Inc.

## Version History

**v1.0.0** (2025-11-18)
- Initial release
- Desktop application with PyQt6 GUI
- SQLite database
- PDF quote generation
- Sample rate tables

## Future Enhancements

- [ ] CSV rate import functionality
- [ ] Email quote delivery
- [ ] Advanced reporting
- [ ] Web application version
- [ ] Multi-user support with authentication
- [ ] Cloud hosting
