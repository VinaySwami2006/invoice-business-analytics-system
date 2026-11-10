import sqlite3
from contextlib import closing
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Store the database inside the data folder
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "business.db"


def get_connection():
    """Create a database connection."""
    return sqlite3.connect(DB_PATH)


def initialize_database():
    """Create all application tables if they do not already exist."""

    with closing(get_connection()) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                city TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                category TEXT,
                unit_price REAL NOT NULL DEFAULT 0
                    CHECK (unit_price >= 0),
                stock_quantity INTEGER NOT NULL DEFAULT 0
                    CHECK (stock_quantity >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                invoice_date TEXT NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                tax_amount REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                line_total REAL NOT NULL,
                FOREIGN KEY (invoice_id)
                    REFERENCES invoices(invoice_id),
                FOREIGN KEY (product_id)
                    REFERENCES products(product_id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS packing_lists (
                packing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL UNIQUE,
                packing_status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK (
                        packing_status IN (
                            'Pending',
                            'Packed',
                            'Dispatched'
                        )
                    ),
                packing_date TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id)
                    REFERENCES invoices(invoice_id)
            )
        """)
        connection.commit()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")
    print(f"Database location: {DB_PATH}")