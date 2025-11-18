# Vulnerable Code Examples with Line Numbers

## Critical Issue #1: SQL Injection in db_manager.py

### Location: src/database/db_manager.py - Lines 150-160

**VULNERABLE CODE:**
```python
150: def get_table_row_count(self, table_name: str) -> int:
151:     """Get number of rows in table."""
152:     query = f"SELECT COUNT(*) as count FROM {table_name}"  # ⚠️ SQL INJECTION!
153:     result = self.execute_query(query)
154:     return result[0]['count'] if result else 0
155:
156: def clear_table(self, table_name: str):
157:     """Delete all rows from table."""
158:     query = f"DELETE FROM {table_name}"  # ⚠️ SQL INJECTION!
159:     self.execute_update(query)
160:     print(f"✓ Cleared table: {table_name}")
```

**HOW TO EXPLOIT:**
```python
# Attacker calls:
db.get_table_row_count("customers; DROP TABLE customers; --")
# Results in SQL execution:
# SELECT COUNT(*) as count FROM customers; DROP TABLE customers; --

# Or:
db.clear_table("customers WHERE id=999; DROP TABLE quotes; --")
# Results in SQL execution:
# DELETE FROM customers WHERE id=999; DROP TABLE quotes; --
```

**CORRECT FIX:**
```python
ALLOWED_TABLES = [
    'customers', 'quotes', 'states',
    'pivot_rates_under_20', 'pivot_rates_20_to_34',
    'pivot_rates_35_plus', 'ancillary_rates'
]

def get_table_row_count(self, table_name: str) -> int:
    """Get number of rows in table."""
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")
    query = f"SELECT COUNT(*) as count FROM {table_name}"
    result = self.execute_query(query)
    return result[0]['count'] if result else 0

def clear_table(self, table_name: str):
    """Delete all rows from table."""
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")
    query = f"DELETE FROM {table_name}"
    self.execute_update(query)
    print(f"✓ Cleared table: {table_name}")
```

---

## Critical Issue #2: Unvalidated CSV Rate Data in rate_import_dialog.py

### Location: src/ui/rate_import_dialog.py - Lines 208-242

**VULNERABLE CODE:**
```python
208: def _import_pivot_under_20(self, db, state, date, row):
209:     """Import pivot under 20 rate."""
210:     query = """
211:         INSERT OR REPLACE INTO pivot_rates_under_20 (
212:             state_code, effective_date,
213:             standard_500_no_me, standard_500_with_me,
...
221:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
222:     """
223:     params = (
224:         state, date,
225:         float(row.get('standard_500_no_me', 0)),     # ⚠️ NO VALIDATION!
226:         float(row.get('standard_500_with_me', 0)),   # ⚠️ Missing column = 0.0
227:         float(row.get('standard_1000_no_me', 0)),    # ⚠️ Negative values OK
228:         float(row.get('standard_1000_with_me', 0)),  # ⚠️ > 100% rates OK
...
240:         float(row.get('towable_5000_with_me', 0))
241:     )
242:     db.execute_insert(query, params)
```

**PROBLEMS:**
1. Missing columns silently become 0.0 (line 225-240 use `row.get(..., 0)`)
2. No validation that columns exist before import
3. No try-catch around float() conversion
4. No validation that rates are between 0-100%
5. No validation that state_code is valid
6. `float()` with invalid data crashes silently

**EXAMPLE OF BAD DATA:**
```csv
state_code,standard_500_no_me,standard_500_with_me,standard_1000_no_me,...
OK,-5.5,2.33,1.89,2.14,...  # NEGATIVE RATE!
TX,250,275,200,225,...       # RATES > 100%!
CA,abc,2.33,1.89,2.14,...    # NON-NUMERIC!
NV,,2.33,1.89,2.14,...       # MISSING VALUE - becomes 0.0!
```

**CORRECT FIX:**
```python
def _import_pivot_under_20(self, db, state, date, row):
    """Import pivot under 20 rate."""
    
    # Define required columns
    required_columns = [
        'standard_500_no_me', 'standard_500_with_me',
        'standard_1000_no_me', 'standard_1000_with_me',
        'standard_2500_no_me', 'standard_2500_with_me',
        'standard_5000_no_me', 'standard_5000_with_me',
        'towable_500_no_me', 'towable_500_with_me',
        'towable_1000_no_me', 'towable_1000_with_me',
        'towable_2500_no_me', 'towable_2500_with_me',
        'towable_5000_no_me', 'towable_5000_with_me'
    ]
    
    # Validate all required columns exist
    for col in required_columns:
        if col not in row:
            raise ValueError(f"Missing required column: {col}")
    
    # Validate and convert rates
    rates = []
    for col in required_columns:
        try:
            rate = float(row[col])  # NOT row.get() - we verified it exists
        except (ValueError, TypeError):
            raise ValueError(f"Invalid rate value in {col}: {row[col]}")
        
        # Validate rate is in valid range
        if not (0 <= rate <= 100):
            raise ValueError(f"Rate {col}={rate} must be between 0-100%")
        
        rates.append(rate)
    
    # Validate state code format
    if not (len(state) == 2 and state.isupper()):
        raise ValueError(f"Invalid state code: {state}")
    
    query = """
        INSERT OR REPLACE INTO pivot_rates_under_20 (
            state_code, effective_date,
            standard_500_no_me, standard_500_with_me,
            ...
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (state, date) + tuple(rates)
    db.execute_insert(query, params)
```

---

## Critical Issue #3: No Email/Phone Validation in customer_dialog.py

### Location: src/ui/customer_dialog.py - Lines 111-142

**VULNERABLE CODE:**
```python
111: def _save(self):
112:     """Validate and save customer."""
113:     name = self.name_input.text().strip()
114:
115:     if not name:
116:         QMessageBox.warning(self, "Validation Error", "Customer name is required.")
117:         self.name_input.setFocus()
118:         return
119:
120:     # Create customer object
121:     if self.customer:
122:         # Editing existing
123:         self.customer.name = name
124:         self.customer.email = self.email_input.text().strip()  # ⚠️ NO VALIDATION!
125:         self.customer.phone = self.phone_input.text().strip()  # ⚠️ NO VALIDATION!
126:         self.customer.address = self.address_input.toPlainText().strip()
127:         self.customer.notes = self.notes_input.toPlainText().strip()
128:     else:
129:         # Creating new
130:         self.customer = Customer(
131:             name=name,
132:             email=self.email_input.text().strip(),         # ⚠️ NO VALIDATION!
133:             phone=self.phone_input.text().strip(),         # ⚠️ NO VALIDATION!
134:             address=self.address_input.toPlainText().strip(),
135:             notes=self.notes_input.toPlainText().strip()
136:         )
137:
138:     self.accept()
```

**WHAT GETS ACCEPTED:**
```python
# Email examples that PASS (but shouldn't):
email = ""                  # Empty is OK
email = "not-an-email"      # No @ symbol
email = "user@"             # No domain
email = "@domain.com"       # No username
email = "'; DROP TABLE--"   # SQL injection attempt (stored as string)
email = "user@domain"       # No TLD

# Phone examples that PASS (but shouldn't):
phone = ""                  # Empty is OK
phone = "abc"               # Letters only
phone = "555"               # Only 3 digits
phone = "'; DROP TABLE--"   # SQL injection attempt
phone = "1-800-FLOWERS"     # Text mixed with numbers
```

**CORRECT FIX:**
```python
import re

def _validate_email(self, email: str) -> bool:
    """Validate email format."""
    if not email:  # Empty is OK (optional field)
        return True
    
    # Basic email regex
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    if not re.match(pattern, email):
        QMessageBox.warning(
            self,
            "Validation Error",
            f"Invalid email format: {email}\n\nExpected: user@domain.com"
        )
        return False
    
    if len(email) > 255:
        QMessageBox.warning(
            self,
            "Validation Error",
            "Email address is too long (max 255 characters)"
        )
        return False
    
    return True

def _validate_phone(self, phone: str) -> bool:
    """Validate phone format."""
    if not phone:  # Empty is OK (optional field)
        return True
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
    
    # Check for 10-15 digits with optional leading +1
    if cleaned.startswith('+1'):
        cleaned = cleaned[2:]
    
    if not re.match(r'^\d{10,15}$', cleaned):
        QMessageBox.warning(
            self,
            "Validation Error",
            f"Invalid phone format: {phone}\n\n"
            "Expected: 10-15 digits (optional +1 prefix and formatting)"
        )
        return False
    
    if len(phone) > 20:  # Store original with formatting
        QMessageBox.warning(
            self,
            "Validation Error",
            "Phone number is too long (max 20 characters)"
        )
        return False
    
    return True

def _validate_name(self, name: str) -> bool:
    """Validate customer name."""
    name = name.strip()
    
    if not name:
        QMessageBox.warning(
            self,
            "Validation Error",
            "Customer name is required."
        )
        return False
    
    if len(name) > 255:
        QMessageBox.warning(
            self,
            "Validation Error",
            "Customer name is too long (max 255 characters)"
        )
        return False
    
    if len(name) < 2:
        QMessageBox.warning(
            self,
            "Validation Error",
            "Customer name must be at least 2 characters"
        )
        return False
    
    return True

def _save(self):
    """Validate and save customer."""
    name = self.name_input.text().strip()
    email = self.email_input.text().strip()
    phone = self.phone_input.text().strip()
    address = self.address_input.toPlainText().strip()
    notes = self.notes_input.toPlainText().strip()
    
    # Validate all fields
    if not self._validate_name(name):
        self.name_input.setFocus()
        return
    
    if not self._validate_email(email):
        self.email_input.setFocus()
        return
    
    if not self._validate_phone(phone):
        self.phone_input.setFocus()
        return
    
    if len(address) > 500:
        QMessageBox.warning(
            self,
            "Validation Error",
            "Address is too long (max 500 characters)"
        )
        return
    
    if len(notes) > 1000:
        QMessageBox.warning(
            self,
            "Validation Error",
            "Notes are too long (max 1000 characters)"
        )
        return
    
    # Create customer object
    if self.customer:
        self.customer.name = name
        self.customer.email = email
        self.customer.phone = phone
        self.customer.address = address
        self.customer.notes = notes
    else:
        self.customer = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address,
            notes=notes
        )
    
    self.accept()
```

---

## High Severity Issues

### Issue #4: No Customer Name Length Validation in quote_form.py

**Location:** src/ui/quote_form.py - Lines 289-300

```python
289: def _validate_form(self):
290:     """Validate form inputs."""
291:     # Customer name validation
292:     if not self.customer_name.text().strip():  # ⚠️ Only checks if empty
293:         QMessageBox.warning(
294:             self,
295:             "Validation Error",
296:             "Customer name is required."
297:         )
298:         self.customer_name.setFocus()
299:         return False
300:
```

**FIX:** Add length check
```python
def _validate_form(self):
    """Validate form inputs."""
    customer_name = self.customer_name.text().strip()
    
    if not customer_name:
        QMessageBox.warning(
            self,
            "Validation Error",
            "Customer name is required."
        )
        self.customer_name.setFocus()
        return False
    
    if len(customer_name) > 255:  # Add this check
        QMessageBox.warning(
            self,
            "Validation Error",
            "Customer name is too long (max 255 characters)"
        )
        self.customer_name.setFocus()
        return False
```

---

## Summary of All Vulnerable Code

| File | Lines | Issue | Severity |
|------|-------|-------|----------|
| db_manager.py | 152, 158 | SQL injection with f-strings | CRITICAL |
| rate_import_dialog.py | 225-314 | No validation of rate values | CRITICAL |
| customer_dialog.py | 124-135 | No email/phone validation | CRITICAL |
| customer_dialog.py | 124-135 | No length limits | HIGH |
| quote_form.py | 292-299 | No customer name length limit | MEDIUM |
| rate_engine.py | 60, 83, 100, 140 | No state code format validation | MEDIUM |
| quote_form.py | 77 | Editable customer ComboBox | LOW |

