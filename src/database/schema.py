"""
Database schema definitions for CSI Pivot Quote application.
Compatible with SQLite (current) and PostgreSQL (future).
"""

# States table
CREATE_STATES_TABLE = """
CREATE TABLE IF NOT EXISTS states (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_special_state INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# Customers table
CREATE_CUSTOMERS_TABLE = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# Quotes table
CREATE_QUOTES_TABLE = """
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    agent_name TEXT,
    quote_date TEXT DEFAULT CURRENT_DATE,

    -- Location and term (common across all line items)
    state_code TEXT NOT NULL,
    term_months INTEGER NOT NULL,

    -- Totals (aggregated from line items)
    total_premium REAL DEFAULT 0,

    -- Metadata
    status TEXT DEFAULT 'draft',
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (state_code) REFERENCES states(code)
);
"""

# Quote line items table (for multi-pivot support)
CREATE_QUOTE_LINE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS quote_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,

    -- Equipment details
    pivot_amount REAL NOT NULL,
    ancillary_amount REAL DEFAULT 0,
    submersible_pump_amount REAL DEFAULT 0,
    equipment_age_years INTEGER NOT NULL,

    -- Equipment configuration
    is_towable INTEGER DEFAULT 0,
    is_corner_or_long INTEGER DEFAULT 0,
    has_me_endorsement INTEGER DEFAULT 1,

    -- Coverage options
    pivot_deductible_code INTEGER NOT NULL,
    ancillary_deductible_code INTEGER NOT NULL,

    -- Calculated results
    pivot_rate REAL,
    ancillary_rate REAL,
    pivot_premium REAL,
    ancillary_premium REAL,
    submersible_charge REAL,
    line_total_premium REAL,

    -- Alternative scenarios
    alt1_deductible INTEGER,
    alt1_rate REAL,
    alt1_premium REAL,
    alt2_deductible INTEGER,
    alt2_rate REAL,
    alt2_premium REAL,

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
    UNIQUE(quote_id, line_number)
);
"""

# Pivot rates for equipment under 20 years
CREATE_PIVOT_RATES_UNDER_20_TABLE = """
CREATE TABLE IF NOT EXISTS pivot_rates_under_20 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT NOT NULL,
    effective_date TEXT NOT NULL,

    -- Standard Equipment rates
    standard_500_no_me REAL,
    standard_500_with_me REAL,
    standard_1000_no_me REAL,
    standard_1000_with_me REAL,
    standard_2500_no_me REAL,
    standard_2500_with_me REAL,
    standard_5000_no_me REAL,
    standard_5000_with_me REAL,

    -- Towable Equipment rates
    towable_500_no_me REAL,
    towable_500_with_me REAL,
    towable_1000_no_me REAL,
    towable_1000_with_me REAL,
    towable_2500_no_me REAL,
    towable_2500_with_me REAL,
    towable_5000_no_me REAL,
    towable_5000_with_me REAL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (state_code) REFERENCES states(code),
    UNIQUE(state_code, effective_date)
);
"""

# Pivot rates for equipment 20-34 years
CREATE_PIVOT_RATES_20_TO_34_TABLE = """
CREATE TABLE IF NOT EXISTS pivot_rates_20_to_34 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT NOT NULL,
    effective_date TEXT NOT NULL,

    standard_500_no_me REAL,
    standard_500_with_me REAL,
    standard_1000_no_me REAL,
    standard_1000_with_me REAL,
    standard_2500_no_me REAL,
    standard_2500_with_me REAL,
    standard_5000_no_me REAL,
    standard_5000_with_me REAL,

    towable_500_no_me REAL,
    towable_500_with_me REAL,
    towable_1000_no_me REAL,
    towable_1000_with_me REAL,
    towable_2500_no_me REAL,
    towable_2500_with_me REAL,
    towable_5000_no_me REAL,
    towable_5000_with_me REAL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (state_code) REFERENCES states(code),
    UNIQUE(state_code, effective_date)
);
"""

# Pivot rates for equipment 35+ years
CREATE_PIVOT_RATES_35_PLUS_TABLE = """
CREATE TABLE IF NOT EXISTS pivot_rates_35_plus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT NOT NULL,
    effective_date TEXT NOT NULL,

    standard_rate REAL,
    corner_rate REAL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (state_code) REFERENCES states(code),
    UNIQUE(state_code, effective_date)
);
"""

# Ancillary equipment rates
CREATE_ANCILLARY_RATES_TABLE = """
CREATE TABLE IF NOT EXISTS ancillary_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT NOT NULL,
    effective_date TEXT NOT NULL,

    standard_500 REAL,
    standard_1000 REAL,
    standard_2500 REAL,
    standard_5000 REAL,

    corner_500 REAL,
    corner_1000 REAL,
    corner_2500 REAL,
    corner_5000 REAL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (state_code) REFERENCES states(code),
    UNIQUE(state_code, effective_date)
);
"""

# Users table (unified for both agents and admins)
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL CHECK(role IN ('admin', 'agent')),
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);
"""

# Quote templates table
CREATE_QUOTE_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS quote_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT UNIQUE NOT NULL,
    description TEXT,

    -- Location and term
    state_code TEXT NOT NULL,
    term_months INTEGER NOT NULL,

    -- Equipment configuration (single pivot template)
    pivot_amount REAL NOT NULL,
    equipment_age_years INTEGER NOT NULL,
    pivot_deductible_code INTEGER NOT NULL,
    ancillary_deductible_code INTEGER NOT NULL,
    ancillary_amount REAL DEFAULT 0,
    submersible_pump_amount REAL DEFAULT 0,
    is_towable INTEGER DEFAULT 0,
    is_corner_or_long INTEGER DEFAULT 0,
    has_me_endorsement INTEGER DEFAULT 1,

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (state_code) REFERENCES states(code)
);
"""

# Rate change audit log
CREATE_RATE_CHANGE_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS rate_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    state_code TEXT NOT NULL,
    column_name TEXT NOT NULL,
    old_value REAL,
    new_value REAL,
    change_type TEXT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

# Performance indexes
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_quotes_customer ON quotes(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_quotes_date ON quotes(quote_date);",
    "CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);",
    "CREATE INDEX IF NOT EXISTS idx_quotes_state ON quotes(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_line_items_quote ON quote_line_items(quote_id);",
    "CREATE INDEX IF NOT EXISTS idx_line_items_line_num ON quote_line_items(quote_id, line_number);",
    "CREATE INDEX IF NOT EXISTS idx_templates_state ON quote_templates(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_templates_name ON quote_templates(template_name);",
    "CREATE INDEX IF NOT EXISTS idx_pivot_under20_state ON pivot_rates_under_20(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_pivot_20to34_state ON pivot_rates_20_to_34(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_pivot_35plus_state ON pivot_rates_35_plus(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_ancillary_state ON ancillary_rates(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
    "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
    "CREATE INDEX IF NOT EXISTS idx_rate_changes_timestamp ON rate_change_log(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_rate_changes_user ON rate_change_log(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_rate_changes_state ON rate_change_log(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_rate_changes_table ON rate_change_log(table_name);",
]

# All tables in creation order
ALL_TABLES = [
    CREATE_STATES_TABLE,
    CREATE_CUSTOMERS_TABLE,
    CREATE_USERS_TABLE,
    CREATE_QUOTES_TABLE,
    CREATE_QUOTE_LINE_ITEMS_TABLE,
    CREATE_QUOTE_TEMPLATES_TABLE,
    CREATE_PIVOT_RATES_UNDER_20_TABLE,
    CREATE_PIVOT_RATES_20_TO_34_TABLE,
    CREATE_PIVOT_RATES_35_PLUS_TABLE,
    CREATE_ANCILLARY_RATES_TABLE,
    CREATE_RATE_CHANGE_LOG_TABLE,
]
