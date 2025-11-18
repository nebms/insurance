# Input Validation & Security Analysis Report

## Executive Summary
The application has **CRITICAL SQL INJECTION VULNERABILITIES** in the database layer, along with significant validation gaps in user input handling. While parameterized queries are used in most places, two functions directly construct SQL with unsanitized table names, and form validation lacks depth in customer data entry.

---

## 1. Quote Form Validation (`/home/user/insurance/src/ui/quote_form.py`)

### Fields Validated
- **Customer Name** (required, non-empty check)
- **State** (required, dropdown selection)
- **Equipment Age** (range: 0-99 years)
- **Pivot Amount** (required, must be > $0)
- **Ancillary Amount** (must be >= $0)
- **Submersible Pump Amount** (must be >= $0)
- **High Value Warning** (confirmation for total coverage > $1M)

### Validation Rules Implemented
- ✓ Non-empty field checks
- ✓ Numeric range validation (spinboxes constrain input)
- ✓ Positive value validation for amounts
- ✓ Dropdown/combo box constraints for state and deductibles
- ✓ Equipment age dynamically enables/disables corner checkbox

### Validation Gaps & Issues
- **NO LENGTH LIMITS**: Customer name can be extremely long, causing database/UI issues
- **NO SPECIAL CHARACTER VALIDATION**: Customer name accepts any text including quotes, semicolons
- **NO FORMAT VALIDATION**: Agent name has no validation (optional but unrestricted)
- **WEAK CUSTOMER SELECTION**: ComboBox is editable - users can type any name, bypassing customer lookup
- **NO DEDUCTIBLE/TERM VALIDATION**: Dropdowns are pre-populated but not validated (though safe via constraints)

### Risk Level: MEDIUM
```python
# Line 292-299: Customer name validation is too basic
if not self.customer_name.text().strip():
    # Only checks if empty, not length or content
    QMessageBox.warning(...)
    return False
```

---

## 2. Customer Dialog Validation (`/home/user/insurance/src/ui/customer_dialog.py`)

### Customer Input Validation Summary
Only **name field** has any validation (non-empty check). Everything else is unvalidated.

### Email Validation
- **Status**: NONE
- **Current Implementation**: Accepts any text
- **Risk**: Invalid emails stored, potential injection vectors

### Phone Validation
- **Status**: NONE  
- **Current Implementation**: Accepts any text (numbers, letters, special chars)
- **Risk**: No format enforcement, could store malicious content

### Required Field Checks
- **Name**: ✓ Required (non-empty check only)
- **Email**: ✗ No validation
- **Phone**: ✗ No validation
- **Address**: ✗ No validation
- **Notes**: ✗ No validation

### Specific Issues Found
```python
# Line 113-122: Only validates name is non-empty
name = self.name_input.text().strip()
if not name:
    QMessageBox.warning(...)
    return

# Lines 128-139: Everything else is unvalidated!
self.customer.email = self.email_input.text().strip()  # No format check
self.customer.phone = self.phone_input.text().strip()   # No format check
self.customer.address = self.address_input.toPlainText().strip()  # No validation
self.customer.notes = self.notes_input.toPlainText().strip()      # No validation
```

### Validation Gaps
1. **NO EMAIL FORMAT VALIDATION**
   - No regex check for valid email format
   - Accepts: empty string, "invalid", "user@", "@@@@"

2. **NO PHONE FORMAT VALIDATION**
   - No pattern matching for phone numbers
   - Accepts: empty string, random text, special characters

3. **NO LENGTH LIMITS**
   - Name field could be 10,000+ characters
   - Address field could be massive (TextEdit with no height constrain)
   - Notes field similarly unbounded

4. **NO CHARACTER VALIDATION**
   - Email/Phone could contain SQL special characters
   - No sanitization of quotes, semicolons, dashes in database-bound fields

5. **NO REQUIRED FIELD ENFORCEMENT**
   - Email and phone are optional with no validation
   - Address and notes accept any content

### Risk Level: HIGH
These fields are stored directly in the database without validation.

---

## 3. Rate Import Dialog Validation (`/home/user/insurance/src/ui/rate_import_dialog.py`)

### CSV Validation
- **Status**: MINIMAL
- Only checks for presence of 'state_code' column (line 167-168)
- No validation of CSV structure completeness

### Data Format Validation Issues
```python
# Line 175: State code is uppercased but not validated
state_code = row['state_code'].upper()

# Lines 225-240: float() conversion with no validation
float(row.get('standard_500_no_me', 0)),  # Could fail, undefined behavior
float(row.get('standard_500_with_me', 0)),
# ... 15 more columns with same issue

# Missing data silently uses 0 as fallback - BAD DATA!
```

### Specific Validation Gaps
1. **NO REQUIRED COLUMN VALIDATION**
   - Only checks 'state_code' exists
   - Doesn't verify all required rate columns are present
   - Missing columns silently use 0.0 rate (catastrophic for business logic)

2. **NO NUMERIC VALIDATION**
   - `float()` conversion will fail on non-numeric data
   - No try-catch around line 225-314 conversions
   - Could cause import to fail mid-process

3. **NO DATA RANGE VALIDATION**
   - Accepts negative rates
   - Accepts rates > 100%
   - No validation that rates are sensible

4. **NO STATE CODE VALIDATION**
   - Doesn't verify state code matches loaded states
   - Could import rates for invalid states
   - No check for 2-letter format

5. **NO COLUMN NAME VALIDATION**
   - Dynamically looks up columns that may not exist
   - `row.get('standard_500_no_me', 0)` is forgiving but dangerous
   - Bad CSV header causes silent data loss with 0 values

6. **ERROR HANDLING TOO BROAD**
   - Lines 198-204: Catches all exceptions, shows generic error
   - Doesn't indicate which row or field failed
   - No rollback mechanism if import partially fails

### Code Examples of Issues
```python
# Line 174-187: No validation of rate values
for i, row in enumerate(rows):
    state_code = row['state_code'].upper()  # No format check!
    
    if table_type == 0:
        self._import_pivot_under_20(db, state_code, effective_date, row)
    # ... if any float() conversion fails, exception is caught at line 198
```

```python
# Line 225-240: Dangerous - missing data becomes 0.0 rate!
float(row.get('standard_500_no_me', 0)),      # If key missing: 0.0
float(row.get('standard_500_with_me', 0)),    # If key missing: 0.0
# ... 15 more columns
```

### Risk Level: CRITICAL
Bad CSV data can silently corrupt rate tables with zero values, making quotes unprofitable.

---

## 4. SQL Injection Vulnerabilities (`/home/user/insurance/src/database/db_manager.py`)

### CRITICAL: Unsafe SQL Construction Found

#### Vulnerability #1: get_table_row_count() - Line 152
```python
def get_table_row_count(self, table_name: str) -> int:
    """Get number of rows in table."""
    query = f"SELECT COUNT(*) as count FROM {table_name}"  # SQL INJECTION!
    result = self.execute_query(query)
    return result[0]['count'] if result else 0
```

**Issue**: Table name is directly interpolated into SQL using f-string
**Attack**: `get_table_row_count("customers; DROP TABLE customers; --")`
**Impact**: Database manipulation, data loss

#### Vulnerability #2: clear_table() - Line 158
```python
def clear_table(self, table_name: str):
    """Delete all rows from table."""
    query = f"DELETE FROM {table_name}"  # SQL INJECTION!
    self.execute_update(query)
```

**Issue**: Table name directly in f-string, no parameterization
**Attack**: `clear_table("customers WHERE id=0; DROP TABLE customers; --")`
**Impact**: Unintended data deletion, database structure compromise

### How These Are Called
- Line 123 in `/home/user/insurance/src/models/customer.py`:
  ```python
  def count(self) -> int:
      """Get total number of customers."""
      return self.db.get_table_row_count('customers')
  ```
- Line 77 in `/home/user/insurance/src/database/data_loader.py`:
  ```python
  count = db.get_table_row_count('states')
  ```

### Why Table Names Can't Be Parameterized
SQLite does NOT allow parameterized queries for identifiers (table/column names). Only VALUES can be parameterized with `?`.

### CORRECT SOLUTION
Validate table names against a whitelist:
```python
ALLOWED_TABLES = ['customers', 'quotes', 'states', 'pivot_rates_under_20', ...]

def get_table_row_count(self, table_name: str) -> int:
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table: {table_name}")
    query = f"SELECT COUNT(*) as count FROM {table_name}"
    ...
```

### Good Practices Found
- ✓ `execute_query()`, `execute_insert()`, `execute_update()` all use parameterized queries with `?`
- ✓ CustomerRepository uses parameterized queries (line 70-75)
- ✓ QuoteRepository uses parameterized queries (line 74-102)
- ✓ All user input in SELECT/WHERE clauses uses `?` placeholders

### Risk Level: CRITICAL

---

## 5. Rate Engine SQL (`/home/user/insurance/src/calculations/rate_engine.py`)

### Issue: Dynamic Column Names in Queries
```python
# Line 49: Column name is dynamically constructed
column = f"{equipment_type}_{deductible}_{me_suffix}"
# Then used in query (lines 52-58):
query = f"""
    SELECT {column} as rate
    FROM pivot_rates_under_20
    WHERE state_code = ?
```

### Risk Analysis
- **Severity**: MEDIUM (not user-controlled input)
- **Source of Column Names**: Application logic only
  - `equipment_type`: "towable" or "standard" (line 47, controlled)
  - `deductible`: "500", "1000", "2500", "5000" (line 44, from safe map)
  - `me_suffix`: "with_me" or "no_me" (line 48, controlled)
  
- **State Parameter**: IS PARAMETERIZED with `?` (line 60)
- **State Validation**: NONE - accepts any string

- **Vulnerability**: If `state` parameter is not validated, could cause query errors
  - Example: `state = "'; DROP TABLE--"` won't work (quoted in WHERE), but could expose database structure

### Better Practice
While the column construction is application-controlled, should add state code validation:
```python
# Should validate state code format (2 uppercase letters)
if not re.match(r'^[A-Z]{2}$', state):
    raise ValueError(f"Invalid state code: {state}")
```

### Risk Level: LOW (but could be improved)

---

## 6. Summary of Vulnerabilities by Severity

### CRITICAL
| File | Issue | Lines | Impact |
|------|-------|-------|--------|
| db_manager.py | SQL Injection in `get_table_row_count()` | 152 | Drop tables, corrupt database |
| db_manager.py | SQL Injection in `clear_table()` | 158 | Delete all table data |
| rate_import_dialog.py | No validation of rate values | 225-314 | Corrupt rate tables with 0% rates |

### HIGH
| File | Issue | Lines | Impact |
|------|-------|-------|--------|
| customer_dialog.py | No email format validation | 128-139 | Invalid data in database |
| customer_dialog.py | No phone format validation | 128-139 | Invalid data in database |
| customer_dialog.py | No length limits on fields | All | UI/Database issues, potential DOS |

### MEDIUM
| File | Issue | Lines | Impact |
|------|-------|-------|--------|
| quote_form.py | No length limit on customer_name | 292-299 | Database constraints, UI overflow |
| quote_form.py | No special character validation | 292-299 | Potential display/parsing issues |
| rate_import_dialog.py | No CSV structure validation | 167-168 | Silent data loss with missing columns |
| rate_import_dialog.py | Missing column defaults to 0.0 | 225-314 | Invalid rates for missing fields |
| rate_engine.py | No state code format validation | 60, 83, 100, 140 | Query errors, database exposure |

### LOW
| File | Issue | Lines | Impact |
|------|-------|-------|--------|
| quote_form.py | Editable ComboBox for customer selection | 77 | Users bypass customer lookup |

---

## 7. Recommended Fixes (Priority Order)

### Priority 1 (Fix Immediately - Security Critical)
1. **db_manager.py line 152-159**: Add whitelist validation for table names
   ```python
   ALLOWED_TABLES = {...}
   if table_name not in ALLOWED_TABLES:
       raise ValueError(...)
   ```

2. **rate_import_dialog.py**: Add proper error handling for float conversions
   ```python
   try:
       value = float(row.get('standard_500_no_me', ''))
   except (ValueError, TypeError):
       raise ValueError(f"Invalid rate value at row {i}: ...")
   ```

3. **rate_import_dialog.py**: Validate all required columns exist before processing
   ```python
   required_columns = ['standard_500_no_me', 'standard_500_with_me', ...]
   for col in required_columns:
       if col not in row:
           raise ValueError(f"Missing required column: {col}")
   ```

### Priority 2 (Fix Soon - High Impact)
4. **customer_dialog.py**: Add email validation
   ```python
   import re
   if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
       raise ValueError("Invalid email format")
   ```

5. **customer_dialog.py**: Add phone validation
   ```python
   if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
       raise ValueError("Invalid phone format")
   ```

6. **customer_dialog.py**: Add length limits
   ```python
   if len(name) > 255:
       raise ValueError("Name too long (max 255 characters)")
   ```

### Priority 3 (Improve Robustness)
7. **rate_engine.py**: Add state code validation
   ```python
   if not re.match(r'^[A-Z]{2}$', state):
       raise ValueError(f"Invalid state code: {state}")
   ```

8. **quote_form.py**: Add customer name length limit
   ```python
   if len(customer_name) > 255:
       raise ValueError("Customer name too long")
   ```

9. **rate_import_dialog.py**: Validate rate ranges
   ```python
   if not (0 <= rate <= 100):
       raise ValueError(f"Rate must be between 0 and 100, got {rate}")
   ```

---

## 8. Testing Recommendations

### SQL Injection Tests
```
Test table name with: "customers; DROP TABLE customers; --"
Test clearing table with: "customers WHERE id=0; DROP TABLE--"
```

### Input Validation Tests
```
Customer name: 10000 character string
Email: "'; DROP TABLE--", "not-an-email", "", "user@"
Phone: "'; DROP TABLE--", "abc", "", "1"
State code: "XX", "XYZ", "", "12", "null"
Rate values: "-1", "101", "abc", "", "null"
```

### CSV Import Tests
```
Missing 'state_code' column
Missing rate columns (should fail with clear error)
Non-numeric rate values
Negative rates
Rates > 100%
Empty CSV file
Malformed CSV (quotes, newlines)
```

---

## Conclusion

The application has **3 CRITICAL vulnerabilities** that should be fixed immediately:
1. SQL injection in database utility functions
2. Unvalidated CSV data that corrupts rate tables
3. Complete lack of input format validation in customer data

The good news: Most database queries use parameterized queries correctly. The vulnerabilities are concentrated in specific functions and can be fixed with targeted changes.

**Estimated fix time**: 2-3 hours for all critical and high issues
